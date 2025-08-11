"""
LLM提供商回退机制处理器
实现自动回退、成功/失败跟踪和详细日志记录
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from threading import Lock

from config.settings import settings

# 设置日志
logger = logging.getLogger(__name__)


class FallbackReason(Enum):
    """回退原因枚举"""
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    HEALTH_CHECK_FAILED = "health_check_failed"
    REQUEST_FAILED = "request_failed"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION_ERROR = "authentication_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    MANUAL_SWITCH = "manual_switch"
    CONFIGURATION_ERROR = "configuration_error"


class FallbackStrategy(Enum):
    """回退策略枚举"""
    IMMEDIATE = "immediate"  # 立即回退
    RETRY_THEN_FALLBACK = "retry_then_fallback"  # 重试后回退
    CIRCUIT_BREAKER = "circuit_breaker"  # 断路器模式
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"  # 加权轮询


@dataclass
class FallbackEvent:
    """回退事件记录"""
    timestamp: float = field(default_factory=time.time)
    from_provider: str = ""
    to_provider: str = ""
    reason: FallbackReason = FallbackReason.PROVIDER_UNAVAILABLE
    success: bool = False
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    response_time: Optional[float] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "timestamp": self.timestamp,
            "from_provider": self.from_provider,
            "to_provider": self.to_provider,
            "reason": self.reason.value,
            "success": self.success,
            "error_message": self.error_message,
            "request_id": self.request_id,
            "response_time": self.response_time,
            "retry_count": self.retry_count
        }


@dataclass
class FallbackStats:
    """回退统计信息"""
    total_fallbacks: int = 0
    successful_fallbacks: int = 0
    failed_fallbacks: int = 0
    fallback_by_reason: Dict[str, int] = field(default_factory=dict)
    fallback_by_provider: Dict[str, int] = field(default_factory=dict)
    average_fallback_time: float = 0.0
    last_fallback_time: Optional[float] = None
    
    @property
    def fallback_success_rate(self) -> float:
        """回退成功率"""
        if self.total_fallbacks == 0:
            return 0.0
        return self.successful_fallbacks / self.total_fallbacks
    
    def record_fallback(self, event: FallbackEvent):
        """记录回退事件"""
        self.total_fallbacks += 1
        self.last_fallback_time = event.timestamp
        
        if event.success:
            self.successful_fallbacks += 1
        else:
            self.failed_fallbacks += 1
        
        # 按原因统计
        reason_key = event.reason.value
        self.fallback_by_reason[reason_key] = self.fallback_by_reason.get(reason_key, 0) + 1
        
        # 按提供商统计
        provider_key = f"{event.from_provider}->{event.to_provider}"
        self.fallback_by_provider[provider_key] = self.fallback_by_provider.get(provider_key, 0) + 1
        
        # 更新平均时间
        if event.response_time is not None:
            total_time = self.average_fallback_time * (self.total_fallbacks - 1) + event.response_time
            self.average_fallback_time = total_time / self.total_fallbacks


class FallbackHandler:
    """回退处理器"""
    
    def __init__(self, 
                 fallback_order: Optional[List[str]] = None,
                 strategy: FallbackStrategy = FallbackStrategy.IMMEDIATE,
                 max_retries: int = 2,
                 retry_delay: float = 1.0):
        """
        初始化回退处理器
        
        Args:
            fallback_order: 回退顺序列表
            strategy: 回退策略
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间
        """
        self.fallback_order = fallback_order or settings.fallback_order.copy()
        self.strategy = strategy
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 回退历史和统计
        self._fallback_history: List[FallbackEvent] = []
        self._fallback_stats = FallbackStats()
        self._lock = Lock()
        
        # 断路器状态
        self._circuit_breaker_state: Dict[str, Dict[str, Any]] = {}
        self._circuit_breaker_threshold = 5  # 连续失败阈值
        self._circuit_breaker_timeout = 300  # 断路器超时时间（秒）
        
        # 配置参数
        self.max_history_size = 1000  # 最大历史记录数
        self.enable_detailed_logging = True
        self.enable_metrics_collection = True
        
        logger.info(f"回退处理器初始化完成，策略: {strategy.value}, 顺序: {self.fallback_order}")
    
    def execute_with_fallback(self, 
                            primary_provider: str,
                            request_func: Callable,
                            request_args: Tuple = (),
                            request_kwargs: Optional[Dict[str, Any]] = None,
                            available_providers: Optional[List[str]] = None) -> Tuple[Any, str, Optional[FallbackEvent]]:
        """
        执行带回退的请求
        
        Args:
            primary_provider: 主要提供商
            request_func: 请求函数
            request_args: 请求参数
            request_kwargs: 请求关键字参数
            available_providers: 可用提供商列表
            
        Returns:
            (响应结果, 实际使用的提供商, 回退事件)
        """
        request_kwargs = request_kwargs or {}
        available_providers = available_providers or self.fallback_order
        
        # 构建尝试顺序
        try_order = self._build_try_order(primary_provider, available_providers)
        
        last_error = None
        fallback_event = None
        
        for i, provider in enumerate(try_order):
            is_fallback = i > 0
            start_time = time.time()
            
            try:
                # 检查断路器状态
                if self._is_circuit_breaker_open(provider):
                    logger.warning(f"提供商 {provider} 断路器开启，跳过")
                    continue
                
                # 执行请求
                logger.debug(f"尝试使用提供商: {provider} (第{i+1}次尝试)")
                result = request_func(provider, *request_args, **request_kwargs)
                
                response_time = time.time() - start_time
                
                # 请求成功
                if is_fallback:
                    fallback_event = FallbackEvent(
                        from_provider=primary_provider,
                        to_provider=provider,
                        reason=self._determine_fallback_reason(last_error),
                        success=True,
                        response_time=response_time,
                        retry_count=i
                    )
                    self._record_fallback_event(fallback_event)
                    logger.info(f"回退成功: {primary_provider} -> {provider}")
                
                # 重置断路器
                self._reset_circuit_breaker(provider)
                
                return result, provider, fallback_event
                
            except Exception as e:
                response_time = time.time() - start_time
                last_error = e
                
                logger.warning(f"提供商 {provider} 请求失败: {e}")
                
                # 更新断路器状态
                self._update_circuit_breaker(provider, False)
                
                # 如果是最后一个提供商，记录失败的回退事件
                if i == len(try_order) - 1 and is_fallback:
                    fallback_event = FallbackEvent(
                        from_provider=primary_provider,
                        to_provider=provider,
                        reason=self._determine_fallback_reason(e),
                        success=False,
                        error_message=str(e),
                        response_time=response_time,
                        retry_count=i
                    )
                    self._record_fallback_event(fallback_event)
        
        # 所有提供商都失败了
        error_msg = f"所有提供商都不可用，最后错误: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def _build_try_order(self, primary_provider: str, available_providers: List[str]) -> List[str]:
        """
        构建尝试顺序
        
        Args:
            primary_provider: 主要提供商
            available_providers: 可用提供商列表
            
        Returns:
            尝试顺序列表
        """
        try_order = [primary_provider]
        
        # 添加回退提供商
        for provider in self.fallback_order:
            if provider != primary_provider and provider in available_providers:
                try_order.append(provider)
        
        # 添加其他可用提供商
        for provider in available_providers:
            if provider not in try_order:
                try_order.append(provider)
        
        return try_order
    
    def _determine_fallback_reason(self, error: Optional[Exception]) -> FallbackReason:
        """
        确定回退原因
        
        Args:
            error: 错误对象
            
        Returns:
            回退原因
        """
        if error is None:
            return FallbackReason.PROVIDER_UNAVAILABLE
        
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return FallbackReason.TIMEOUT
        elif "rate limit" in error_str or "429" in error_str:
            return FallbackReason.RATE_LIMIT
        elif "authentication" in error_str or "401" in error_str:
            return FallbackReason.AUTHENTICATION_ERROR
        elif "quota" in error_str or "403" in error_str:
            return FallbackReason.QUOTA_EXCEEDED
        elif "configuration" in error_str or "config" in error_str:
            return FallbackReason.CONFIGURATION_ERROR
        else:
            return FallbackReason.REQUEST_FAILED
    
    def _record_fallback_event(self, event: FallbackEvent):
        """
        记录回退事件
        
        Args:
            event: 回退事件
        """
        with self._lock:
            # 添加到历史记录
            self._fallback_history.append(event)
            
            # 限制历史记录大小
            if len(self._fallback_history) > self.max_history_size:
                self._fallback_history = self._fallback_history[-self.max_history_size:]
            
            # 更新统计信息
            if self.enable_metrics_collection:
                self._fallback_stats.record_fallback(event)
            
            # 详细日志
            if self.enable_detailed_logging:
                log_data = event.to_dict()
                if event.success:
                    logger.info(f"回退成功: {json.dumps(log_data, ensure_ascii=False)}")
                else:
                    logger.error(f"回退失败: {json.dumps(log_data, ensure_ascii=False)}")
    
    def _is_circuit_breaker_open(self, provider: str) -> bool:
        """
        检查断路器是否开启
        
        Args:
            provider: 提供商名称
            
        Returns:
            断路器是否开启
        """
        if provider not in self._circuit_breaker_state:
            return False
        
        state = self._circuit_breaker_state[provider]
        
        # 检查是否超时
        if time.time() - state.get("last_failure_time", 0) > self._circuit_breaker_timeout:
            # 超时后重置断路器
            self._reset_circuit_breaker(provider)
            return False
        
        return state.get("is_open", False)
    
    def _update_circuit_breaker(self, provider: str, success: bool):
        """
        更新断路器状态
        
        Args:
            provider: 提供商名称
            success: 是否成功
        """
        if provider not in self._circuit_breaker_state:
            self._circuit_breaker_state[provider] = {
                "consecutive_failures": 0,
                "is_open": False,
                "last_failure_time": 0  # 使用0而不是None
            }
        
        state = self._circuit_breaker_state[provider]
        
        if success:
            # 成功时重置计数器
            state["consecutive_failures"] = 0
            state["is_open"] = False
        else:
            # 失败时增加计数器
            state["consecutive_failures"] += 1
            state["last_failure_time"] = time.time()
            
            # 检查是否需要开启断路器
            if state["consecutive_failures"] >= self._circuit_breaker_threshold:
                state["is_open"] = True
                logger.warning(f"提供商 {provider} 断路器开启，连续失败 {state['consecutive_failures']} 次")
    
    def _reset_circuit_breaker(self, provider: str):
        """
        重置断路器
        
        Args:
            provider: 提供商名称
        """
        if provider in self._circuit_breaker_state:
            self._circuit_breaker_state[provider] = {
                "consecutive_failures": 0,
                "is_open": False,
                "last_failure_time": 0  # 使用0而不是None
            }
            logger.debug(f"提供商 {provider} 断路器已重置")
    
    def get_fallback_stats(self) -> FallbackStats:
        """
        获取回退统计信息
        
        Returns:
            回退统计信息
        """
        return self._fallback_stats
    
    def get_fallback_history(self, limit: Optional[int] = None) -> List[FallbackEvent]:
        """
        获取回退历史记录
        
        Args:
            limit: 限制返回的记录数
            
        Returns:
            回退历史记录列表
        """
        with self._lock:
            history = self._fallback_history.copy()
            if limit is not None:
                history = history[-limit:]
            return history
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """
        获取断路器状态
        
        Returns:
            断路器状态字典
        """
        return self._circuit_breaker_state.copy()
    
    def manual_fallback(self, from_provider: str, to_provider: str, reason: str = "manual_switch") -> FallbackEvent:
        """
        手动触发回退
        
        Args:
            from_provider: 源提供商
            to_provider: 目标提供商
            reason: 回退原因
            
        Returns:
            回退事件
        """
        event = FallbackEvent(
            from_provider=from_provider,
            to_provider=to_provider,
            reason=FallbackReason.MANUAL_SWITCH,
            success=True,
            error_message=reason
        )
        
        self._record_fallback_event(event)
        logger.info(f"手动回退: {from_provider} -> {to_provider}, 原因: {reason}")
        
        return event
    
    def reset_circuit_breaker_all(self):
        """重置所有断路器"""
        with self._lock:
            for provider in self._circuit_breaker_state.keys():
                self._reset_circuit_breaker(provider)
        logger.info("所有断路器已重置")
    
    def clear_history(self):
        """清空回退历史"""
        with self._lock:
            self._fallback_history.clear()
            self._fallback_stats = FallbackStats()
        logger.info("回退历史已清空")
    
    def export_fallback_report(self) -> Dict[str, Any]:
        """
        导出回退报告
        
        Returns:
            回退报告字典
        """
        with self._lock:
            return {
                "timestamp": time.time(),
                "configuration": {
                    "fallback_order": self.fallback_order,
                    "strategy": self.strategy.value,
                    "max_retries": self.max_retries,
                    "retry_delay": self.retry_delay,
                    "circuit_breaker_threshold": self._circuit_breaker_threshold,
                    "circuit_breaker_timeout": self._circuit_breaker_timeout
                },
                "statistics": {
                    "total_fallbacks": self._fallback_stats.total_fallbacks,
                    "successful_fallbacks": self._fallback_stats.successful_fallbacks,
                    "failed_fallbacks": self._fallback_stats.failed_fallbacks,
                    "fallback_success_rate": self._fallback_stats.fallback_success_rate,
                    "average_fallback_time": self._fallback_stats.average_fallback_time,
                    "last_fallback_time": self._fallback_stats.last_fallback_time,
                    "fallback_by_reason": self._fallback_stats.fallback_by_reason,
                    "fallback_by_provider": self._fallback_stats.fallback_by_provider
                },
                "circuit_breaker_status": self.get_circuit_breaker_status(),
                "recent_history": [event.to_dict() for event in self._fallback_history[-10:]]
            }
    
    def update_fallback_order(self, new_order: List[str]):
        """
        更新回退顺序
        
        Args:
            new_order: 新的回退顺序
        """
        old_order = self.fallback_order.copy()
        self.fallback_order = new_order.copy()
        logger.info(f"回退顺序已更新: {old_order} -> {new_order}")
    
    def set_circuit_breaker_threshold(self, threshold: int):
        """
        设置断路器阈值
        
        Args:
            threshold: 新的阈值
        """
        old_threshold = self._circuit_breaker_threshold
        self._circuit_breaker_threshold = threshold
        logger.info(f"断路器阈值已更新: {old_threshold} -> {threshold}")
    
    def set_circuit_breaker_timeout(self, timeout: int):
        """
        设置断路器超时时间
        
        Args:
            timeout: 新的超时时间（秒）
        """
        old_timeout = self._circuit_breaker_timeout
        self._circuit_breaker_timeout = timeout
        logger.info(f"断路器超时时间已更新: {old_timeout} -> {timeout}")


# 全局回退处理器实例
_fallback_handler: Optional[FallbackHandler] = None
_handler_lock = Lock()


def get_fallback_handler() -> FallbackHandler:
    """
    获取全局回退处理器实例（单例模式）
    
    Returns:
        回退处理器实例
    """
    global _fallback_handler
    
    if _fallback_handler is None:
        with _handler_lock:
            if _fallback_handler is None:
                _fallback_handler = FallbackHandler()
    
    return _fallback_handler


def reset_fallback_handler():
    """重置回退处理器（主要用于测试）"""
    global _fallback_handler
    with _handler_lock:
        _fallback_handler = None