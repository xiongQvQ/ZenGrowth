"""
LLM提供商管理系统
实现多提供商支持、健康检查、动态切换和回退机制
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock
import json

from langchain_core.language_models.base import BaseLanguageModel
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from config.settings import settings, get_provider_api_key, validate_provider_config
from config.volcano_llm_client import VolcanoLLMClient, VolcanoAPIException, VolcanoErrorType
from config.volcano_llm_client_monitored import MonitoredVolcanoLLMClient
from config.monitoring_system import get_performance_monitor
from config.fallback_handler import FallbackHandler, FallbackEvent, FallbackReason, get_fallback_handler

# 设置日志
logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """提供商状态枚举"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    DISABLED = "disabled"


class HealthCheckResult(BaseModel):
    """健康检查结果"""
    provider: str
    status: ProviderStatus
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    last_check: float = Field(default_factory=time.time)
    success_rate: Optional[float] = None
    consecutive_failures: int = 0
    
    class Config:
        use_enum_values = True


@dataclass
class ProviderMetrics:
    """提供商指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    last_request_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        """计算平均响应时间"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests
    
    def record_success(self, response_time: float):
        """记录成功请求"""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_response_time += response_time
        self.last_request_time = time.time()
        self.consecutive_failures = 0
        self.consecutive_successes += 1
    
    def record_failure(self, error_message: str):
        """记录失败请求"""
        self.total_requests += 1
        self.failed_requests += 1
        self.last_request_time = time.time()
        self.last_error = error_message
        self.last_error_time = time.time()
        self.consecutive_successes = 0
        self.consecutive_failures += 1


class LLMProviderManager:
    """LLM提供商管理器"""
    
    def __init__(self):
        self._providers: Dict[str, BaseLanguageModel] = {}
        self._provider_configs: Dict[str, Dict[str, Any]] = {}
        self._health_status: Dict[str, HealthCheckResult] = {}
        self._metrics: Dict[str, ProviderMetrics] = {}
        self._lock = Lock()
        
        # 健康检查配置
        self.health_check_interval = 300  # 5分钟
        self.health_check_timeout = 30  # 30秒
        self.max_consecutive_failures = 3  # 最大连续失败次数
        self.degraded_threshold = 0.8  # 成功率低于80%视为降级
        
        # 回退配置
        self.fallback_enabled = settings.enable_fallback
        self.fallback_order = settings.fallback_order.copy()
        
        # 初始化回退处理器
        self._fallback_handler = get_fallback_handler()
        
        # 初始化提供商
        self._initialize_providers()
        
        # 启动健康检查
        self._last_health_check = 0
        
        logger.info(f"LLM提供商管理器初始化完成，支持的提供商: {list(self._providers.keys())}")
    
    def _initialize_providers(self):
        """初始化所有配置的提供商"""
        for provider_name in settings.enabled_providers:
            try:
                if self._initialize_provider(provider_name):
                    logger.info(f"提供商 {provider_name} 初始化成功")
                else:
                    logger.warning(f"提供商 {provider_name} 初始化失败")
            except Exception as e:
                logger.error(f"初始化提供商 {provider_name} 时发生错误: {e}")
    
    def _initialize_provider(self, provider_name: str) -> bool:
        """
        初始化单个提供商
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            是否初始化成功
        """
        try:
            # 验证配置
            if not validate_provider_config(provider_name):
                logger.error(f"提供商 {provider_name} 配置验证失败")
                return False
            
            # 获取配置
            config = self._get_provider_config(provider_name)
            self._provider_configs[provider_name] = config
            
            # 创建提供商实例
            provider_instance = self._create_provider_instance(provider_name, config)
            if provider_instance is None:
                return False
            
            self._providers[provider_name] = provider_instance
            
            # 初始化指标
            self._metrics[provider_name] = ProviderMetrics()
            
            # 初始化健康状态
            self._health_status[provider_name] = HealthCheckResult(
                provider=provider_name,
                status=ProviderStatus.UNKNOWN
            )
            
            return True
            
        except Exception as e:
            logger.error(f"初始化提供商 {provider_name} 失败: {e}")
            return False
    
    def _get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """获取提供商配置"""
        if provider_name == "google":
            return {
                "api_key": settings.google_api_key,
                "model": settings.llm_model,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
                "supports_multimodal": False
            }
        elif provider_name == "volcano":
            return {
                "api_key": settings.ark_api_key,
                "base_url": settings.ark_base_url,
                "model": settings.ark_model,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.llm_max_tokens,
                "supports_multimodal": settings.enable_multimodal
            }
        else:
            raise ValueError(f"不支持的提供商: {provider_name}")
    
    def _create_provider_instance(self, provider_name: str, config: Dict[str, Any]) -> Optional[BaseLanguageModel]:
        """创建提供商实例"""
        try:
            if provider_name == "google":
                return ChatGoogleGenerativeAI(
                    model=config["model"],
                    google_api_key=config["api_key"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"]
                )
            elif provider_name == "volcano":
                # 使用带监控的Volcano客户端
                return MonitoredVolcanoLLMClient(
                    api_key=config["api_key"],
                    base_url=config["base_url"],
                    model=config["model"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"]
                )
            else:
                logger.error(f"不支持的提供商类型: {provider_name}")
                return None
                
        except Exception as e:
            logger.error(f"创建提供商 {provider_name} 实例失败: {e}")
            return None
    
    def get_llm(self, provider: Optional[str] = None, **kwargs) -> BaseLanguageModel:
        """
        获取LLM实例
        
        Args:
            provider: 指定的提供商，如果为None则使用默认提供商
            **kwargs: 额外的配置参数
            
        Returns:
            LLM实例
            
        Raises:
            ValueError: 当提供商不可用时
        """
        with self._lock:
            # 确定要使用的提供商
            target_provider = provider or settings.default_llm_provider
            
            # 检查提供商是否存在
            if target_provider not in self._providers:
                if self.fallback_enabled:
                    target_provider = self._get_fallback_provider(target_provider)
                    if target_provider is None:
                        raise ValueError("没有可用的LLM提供商")
                else:
                    raise ValueError(f"提供商 {target_provider} 不可用")
            
            # 检查提供商健康状态
            if not self._is_provider_healthy(target_provider):
                # 尝试重新检查健康状态
                logger.info(f"提供商 {target_provider} 显示不健康，尝试重新检查...")
                try:
                    health_result = self.health_check(target_provider)
                    if health_result.status in ["available", "degraded"]:
                        logger.info(f"提供商 {target_provider} 重新检查后状态: {health_result.status}")
                    else:
                        # 仍然不健康，尝试回退
                        if self.fallback_enabled:
                            fallback_provider = self._get_fallback_provider(target_provider)
                            if fallback_provider is not None:
                                logger.warning(f"提供商 {target_provider} 不健康，切换到 {fallback_provider}")
                                target_provider = fallback_provider
                            else:
                                logger.warning(f"提供商 {target_provider} 不健康，但没有可用的回退选项")
                except Exception as e:
                    logger.error(f"重新检查提供商 {target_provider} 失败: {e}")
                    if self.fallback_enabled:
                        fallback_provider = self._get_fallback_provider(target_provider)
                        if fallback_provider is not None:
                            logger.warning(f"提供商 {target_provider} 检查失败，切换到 {fallback_provider}")
                            target_provider = fallback_provider
                        else:
                            logger.warning(f"提供商 {target_provider} 检查失败，但没有可用的回退选项")
            
            logger.info(f"使用LLM提供商: {target_provider}")
            return self._providers[target_provider]
    
    def get_available_providers(self) -> List[str]:
        """
        获取可用的提供商列表
        
        Returns:
            可用提供商名称列表
        """
        available = []
        for provider_name in self._providers.keys():
            if self._is_provider_healthy(provider_name):
                available.append(provider_name)
        return available
    
    def set_default_provider(self, provider: str) -> None:
        """
        设置默认提供商
        
        Args:
            provider: 提供商名称
            
        Raises:
            ValueError: 当提供商不存在时
        """
        if provider not in self._providers:
            raise ValueError(f"提供商 {provider} 不存在")
        
        # 这里应该更新配置，但由于settings是只读的，我们只记录日志
        logger.info(f"请求设置默认提供商为: {provider}")
        logger.warning("动态设置默认提供商需要更新配置文件或环境变量")
    
    def health_check(self, provider: str) -> HealthCheckResult:
        """
        执行单个提供商的健康检查
        
        Args:
            provider: 提供商名称
            
        Returns:
            健康检查结果
        """
        if provider not in self._providers:
            return HealthCheckResult(
                provider=provider,
                status=ProviderStatus.UNAVAILABLE,
                error_message="提供商不存在"
            )
        
        start_time = time.time()
        
        try:
            # 执行简单的测试请求
            llm = self._providers[provider]
            test_prompt = "Hello, this is a health check."
            
            # 使用同步调用进行健康检查
            response = llm.invoke(test_prompt)
            
            response_time = time.time() - start_time
            
            # 检查响应是否有效
            if response and len(str(response).strip()) > 0:
                # 更新指标
                self._metrics[provider].record_success(response_time)
                
                # 根据成功率判断状态
                success_rate = self._metrics[provider].success_rate
                if success_rate >= self.degraded_threshold:
                    status = ProviderStatus.AVAILABLE
                else:
                    status = ProviderStatus.DEGRADED
                
                result = HealthCheckResult(
                    provider=provider,
                    status=status,
                    response_time=response_time,
                    success_rate=success_rate,
                    consecutive_failures=self._metrics[provider].consecutive_failures
                )
            else:
                # 响应无效
                error_msg = "健康检查响应无效"
                self._metrics[provider].record_failure(error_msg)
                
                result = HealthCheckResult(
                    provider=provider,
                    status=ProviderStatus.UNAVAILABLE,
                    error_message=error_msg,
                    consecutive_failures=self._metrics[provider].consecutive_failures
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            
            # 更新指标
            self._metrics[provider].record_failure(error_msg)
            
            # 根据连续失败次数判断状态
            consecutive_failures = self._metrics[provider].consecutive_failures
            if consecutive_failures >= self.max_consecutive_failures:
                status = ProviderStatus.UNAVAILABLE
            else:
                status = ProviderStatus.DEGRADED
            
            result = HealthCheckResult(
                provider=provider,
                status=status,
                response_time=response_time,
                error_message=error_msg,
                consecutive_failures=consecutive_failures
            )
        
        # 更新健康状态
        self._health_status[provider] = result
        
        logger.debug(f"提供商 {provider} 健康检查完成: {result.status}")
        
        return result
    
    def health_check_all(self) -> Dict[str, HealthCheckResult]:
        """
        执行所有提供商的健康检查
        
        Returns:
            所有提供商的健康检查结果
        """
        results = {}
        
        for provider_name in self._providers.keys():
            try:
                results[provider_name] = self.health_check(provider_name)
            except Exception as e:
                logger.error(f"提供商 {provider_name} 健康检查失败: {e}")
                results[provider_name] = HealthCheckResult(
                    provider=provider_name,
                    status=ProviderStatus.UNAVAILABLE,
                    error_message=str(e)
                )
        
        self._last_health_check = time.time()
        
        return results
    
    def _is_provider_healthy(self, provider: str) -> bool:
        """
        检查提供商是否健康
        
        Args:
            provider: 提供商名称
            
        Returns:
            是否健康
        """
        if provider not in self._health_status:
            # 如果没有健康状态记录，尝试执行健康检查
            logger.debug(f"提供商 {provider} 没有健康状态记录，执行健康检查")
            try:
                self.health_check(provider)
            except Exception as e:
                logger.error(f"提供商 {provider} 健康检查失败: {e}")
                return False
        
        if provider not in self._health_status:
            return False
        
        status = self._health_status[provider].status
        # 处理字符串和枚举值
        if isinstance(status, str):
            is_healthy = status in ["available", "degraded"]
        else:
            is_healthy = status in [ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED]
        
        logger.debug(f"提供商 {provider} 健康状态: {status}, 是否健康: {is_healthy}")
        return is_healthy
    
    def _get_fallback_provider(self, failed_provider: str) -> Optional[str]:
        """
        获取回退提供商
        
        Args:
            failed_provider: 失败的提供商
            
        Returns:
            回退提供商名称，如果没有可用的则返回None
        """
        if not self.fallback_enabled:
            return None
        
        # 按照回退顺序查找可用的提供商
        for provider in self.fallback_order:
            if provider != failed_provider and provider in self._providers:
                if self._is_provider_healthy(provider):
                    return provider
        
        # 如果回退列表中没有可用的，尝试其他已初始化的提供商
        for provider in self._providers.keys():
            if provider != failed_provider and self._is_provider_healthy(provider):
                return provider
        
        return None
    
    def get_provider_metrics(self, provider: str) -> Optional[ProviderMetrics]:
        """
        获取提供商指标
        
        Args:
            provider: 提供商名称
            
        Returns:
            提供商指标，如果不存在则返回None
        """
        return self._metrics.get(provider)
    
    def get_all_metrics(self) -> Dict[str, ProviderMetrics]:
        """
        获取所有提供商的指标
        
        Returns:
            所有提供商的指标字典
        """
        return self._metrics.copy()
    
    def get_provider_status(self, provider: str) -> Optional[HealthCheckResult]:
        """
        获取提供商状态
        
        Args:
            provider: 提供商名称
            
        Returns:
            健康检查结果，如果不存在则返回None
        """
        return self._health_status.get(provider)
    
    def get_all_status(self) -> Dict[str, HealthCheckResult]:
        """
        获取所有提供商的状态
        
        Returns:
            所有提供商的状态字典
        """
        return self._health_status.copy()
    
    def force_health_check(self) -> Dict[str, HealthCheckResult]:
        """
        强制执行健康检查
        
        Returns:
            健康检查结果
        """
        logger.info("执行强制健康检查")
        return self.health_check_all()
    
    def should_run_health_check(self) -> bool:
        """
        判断是否应该运行健康检查
        
        Returns:
            是否应该运行
        """
        return (time.time() - self._last_health_check) >= self.health_check_interval
    
    def auto_health_check(self) -> Optional[Dict[str, HealthCheckResult]]:
        """
        自动健康检查（如果需要的话）
        
        Returns:
            健康检查结果，如果不需要检查则返回None
        """
        if self.should_run_health_check():
            return self.health_check_all()
        return None
    
    def disable_provider(self, provider: str) -> bool:
        """
        禁用提供商
        
        Args:
            provider: 提供商名称
            
        Returns:
            是否成功禁用
        """
        if provider not in self._providers:
            return False
        
        # 更新状态为禁用
        self._health_status[provider] = HealthCheckResult(
            provider=provider,
            status=ProviderStatus.DISABLED,
            error_message="手动禁用"
        )
        
        logger.info(f"提供商 {provider} 已被禁用")
        return True
    
    def enable_provider(self, provider: str) -> bool:
        """
        启用提供商
        
        Args:
            provider: 提供商名称
            
        Returns:
            是否成功启用
        """
        if provider not in self._providers:
            return False
        
        # 执行健康检查来更新状态
        self.health_check(provider)
        
        logger.info(f"提供商 {provider} 已被启用")
        return True
    
    def get_provider_info(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        获取提供商详细信息
        
        Args:
            provider: 提供商名称
            
        Returns:
            提供商信息字典
        """
        if provider not in self._providers:
            return None
        
        config = self._provider_configs.get(provider, {})
        metrics = self._metrics.get(provider)
        status = self._health_status.get(provider)
        
        # 隐藏敏感信息
        safe_config = config.copy()
        if "api_key" in safe_config:
            api_key = safe_config["api_key"]
            if api_key:
                safe_config["api_key"] = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        
        return {
            "name": provider,
            "config": safe_config,
            "metrics": {
                "total_requests": metrics.total_requests if metrics else 0,
                "success_rate": metrics.success_rate if metrics else 0.0,
                "average_response_time": metrics.average_response_time if metrics else 0.0,
                "consecutive_failures": metrics.consecutive_failures if metrics else 0,
                "last_request_time": metrics.last_request_time if metrics else None,
            } if metrics else {},
            "status": {
                "status": str(status.status) if status else "unknown",
                "last_check": status.last_check if status else None,
                "error_message": status.error_message if status else None,
                "response_time": status.response_time if status else None,
            } if status else {}
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        
        Returns:
            系统信息字典
        """
        providers_info = {}
        for provider in self._providers.keys():
            providers_info[provider] = self.get_provider_info(provider)
        
        return {
            "total_providers": len(self._providers),
            "available_providers": len(self.get_available_providers()),
            "default_provider": settings.default_llm_provider,
            "fallback_enabled": self.fallback_enabled,
            "fallback_order": self.fallback_order,
            "last_health_check": self._last_health_check,
            "health_check_interval": self.health_check_interval,
            "providers": providers_info
        }
    
    def invoke_with_fallback(self, 
                           prompt: str, 
                           provider: Optional[str] = None,
                           **kwargs) -> Tuple[Any, str, Optional[FallbackEvent]]:
        """
        使用回退机制执行LLM调用
        
        Args:
            prompt: 提示文本
            provider: 指定的提供商
            **kwargs: 额外参数
            
        Returns:
            (响应结果, 实际使用的提供商, 回退事件)
        """
        primary_provider = provider or settings.default_llm_provider
        available_providers = self.get_available_providers()
        
        def request_func(provider_name: str, prompt_text: str, **request_kwargs):
            """请求函数"""
            llm = self._providers[provider_name]
            start_time = time.time()
            
            try:
                result = llm.invoke(prompt_text, **request_kwargs)
                response_time = time.time() - start_time
                
                # 记录成功指标
                self._metrics[provider_name].record_success(response_time)
                
                return result
                
            except Exception as e:
                # 记录失败指标
                self._metrics[provider_name].record_failure(str(e))
                raise e
        
        return self._fallback_handler.execute_with_fallback(
            primary_provider=primary_provider,
            request_func=request_func,
            request_args=(prompt,),
            request_kwargs=kwargs,
            available_providers=available_providers
        )
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """
        获取回退统计信息
        
        Returns:
            回退统计信息字典
        """
        fallback_stats = self._fallback_handler.get_fallback_stats()
        return {
            "total_fallbacks": fallback_stats.total_fallbacks,
            "successful_fallbacks": fallback_stats.successful_fallbacks,
            "failed_fallbacks": fallback_stats.failed_fallbacks,
            "fallback_success_rate": fallback_stats.fallback_success_rate,
            "average_fallback_time": fallback_stats.average_fallback_time,
            "last_fallback_time": fallback_stats.last_fallback_time,
            "fallback_by_reason": fallback_stats.fallback_by_reason,
            "fallback_by_provider": fallback_stats.fallback_by_provider
        }
    
    def get_fallback_history(self, limit: Optional[int] = 10) -> List[Dict[str, Any]]:
        """
        获取回退历史记录
        
        Args:
            limit: 限制返回的记录数
            
        Returns:
            回退历史记录列表
        """
        history = self._fallback_handler.get_fallback_history(limit)
        return [event.to_dict() for event in history]
    
    def manual_fallback(self, from_provider: str, to_provider: str, reason: str = "manual_switch") -> bool:
        """
        手动触发回退
        
        Args:
            from_provider: 源提供商
            to_provider: 目标提供商
            reason: 回退原因
            
        Returns:
            是否成功
        """
        try:
            # 验证提供商存在
            if from_provider not in self._providers or to_provider not in self._providers:
                logger.error("指定的提供商不存在")
                return False
            
            # 记录手动回退事件
            self._fallback_handler.manual_fallback(from_provider, to_provider, reason)
            
            logger.info(f"手动回退成功: {from_provider} -> {to_provider}")
            return True
            
        except Exception as e:
            logger.error(f"手动回退失败: {e}")
            return False
    
    def reset_fallback_stats(self):
        """重置回退统计信息"""
        self._fallback_handler.clear_history()
        logger.info("回退统计信息已重置")
    
    def update_fallback_order(self, new_order: List[str]) -> bool:
        """
        更新回退顺序
        
        Args:
            new_order: 新的回退顺序
            
        Returns:
            是否成功更新
        """
        try:
            # 验证所有提供商都存在
            for provider in new_order:
                if provider not in self._providers:
                    logger.error(f"提供商 {provider} 不存在")
                    return False
            
            # 更新本地配置
            self.fallback_order = new_order.copy()
            
            # 更新回退处理器配置
            self._fallback_handler.update_fallback_order(new_order)
            
            logger.info(f"回退顺序已更新: {new_order}")
            return True
            
        except Exception as e:
            logger.error(f"更新回退顺序失败: {e}")
            return False
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取断路器状态
        
        Returns:
            断路器状态字典
        """
        return self._fallback_handler.get_circuit_breaker_status()
    
    def reset_circuit_breakers(self):
        """重置所有断路器"""
        self._fallback_handler.reset_circuit_breaker_all()
        logger.info("所有断路器已重置")
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        获取监控统计信息
        
        Returns:
            监控统计信息字典
        """
        performance_monitor = get_performance_monitor()
        
        return {
            "provider_stats": performance_monitor.get_all_provider_stats(),
            "performance_comparison": performance_monitor.get_performance_comparison(),
            "system_health": performance_monitor.get_system_health(),
            "hourly_stats": performance_monitor.get_hourly_stats(),
            "recent_requests": [r.to_dict() for r in performance_monitor.get_recent_requests(50)]
        }
    
    def get_provider_monitoring_stats(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        获取特定提供商的监控统计
        
        Args:
            provider: 提供商名称
            
        Returns:
            提供商监控统计，如果不存在则返回None
        """
        if provider not in self._providers:
            return None
        
        # 如果是监控增强的客户端，获取其统计信息
        provider_instance = self._providers[provider]
        if hasattr(provider_instance, 'get_monitoring_stats'):
            return provider_instance.get_monitoring_stats()
        
        # 否则从全局监控器获取
        performance_monitor = get_performance_monitor()
        provider_stats = performance_monitor.get_provider_stats(provider)
        
        if not provider_stats:
            return None
        
        return {
            "provider": provider,
            "total_requests": provider_stats.total_requests,
            "successful_requests": provider_stats.successful_requests,
            "failed_requests": provider_stats.failed_requests,
            "success_rate": provider_stats.success_rate,
            "average_response_time": provider_stats.average_response_time,
            "median_response_time": provider_stats.median_response_time,
            "p95_response_time": provider_stats.p95_response_time,
            "total_tokens": provider_stats.total_tokens,
            "total_cost": provider_stats.total_cost,
            "error_count_by_type": provider_stats.error_count_by_type,
            "request_count_by_type": provider_stats.request_count_by_type
        }
    
    def export_monitoring_report(self) -> str:
        """
        导出完整的监控报告
        
        Returns:
            JSON格式的监控报告
        """
        performance_monitor = get_performance_monitor()
        
        report_data = {
            "timestamp": time.time(),
            "system_info": self.get_system_info(),
            "monitoring_stats": self.get_monitoring_stats(),
            "fallback_stats": self.get_fallback_stats(),
            "circuit_breaker_status": self.get_circuit_breaker_status(),
            "detailed_metrics": performance_monitor.export_metrics()
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def export_metrics(self) -> str:
        """
        导出指标为JSON格式
        
        Returns:
            JSON格式的指标数据
        """
        export_data = {
            "timestamp": time.time(),
            "system_info": self.get_system_info(),
            "detailed_metrics": {},
            "fallback_stats": self.get_fallback_stats(),
            "circuit_breaker_status": self.get_circuit_breaker_status()
        }
        
        for provider, metrics in self._metrics.items():
            export_data["detailed_metrics"][provider] = {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.success_rate,
                "average_response_time": metrics.average_response_time,
                "consecutive_failures": metrics.consecutive_failures,
                "consecutive_successes": metrics.consecutive_successes,
                "last_request_time": metrics.last_request_time,
                "last_error": metrics.last_error,
                "last_error_time": metrics.last_error_time
            }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def export_fallback_report(self) -> str:
        """
        导出回退报告
        
        Returns:
            JSON格式的回退报告
        """
        report = self._fallback_handler.export_fallback_report()
        return json.dumps(report, indent=2, ensure_ascii=False)


# 全局提供商管理器实例
_provider_manager: Optional[LLMProviderManager] = None
_manager_lock = Lock()


def get_provider_manager() -> LLMProviderManager:
    """
    获取全局提供商管理器实例（单例模式）
    
    Returns:
        提供商管理器实例
    """
    global _provider_manager
    
    if _provider_manager is None:
        with _manager_lock:
            if _provider_manager is None:
                _provider_manager = LLMProviderManager()
    
    return _provider_manager


def reset_provider_manager():
    """重置提供商管理器（主要用于测试）"""
    global _provider_manager
    with _manager_lock:
        _provider_manager = None