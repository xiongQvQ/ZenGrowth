"""
带监控增强的Volcano LLM客户端
集成详细的请求/响应日志记录和性能监控
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Union
from langchain_core.language_models.llms import LLM
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult, Generation
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

from config.volcano_llm_client import VolcanoLLMClient, VolcanoAPIException, VolcanoErrorType
from config.monitoring_system import (
    get_performance_monitor, 
    RequestType, 
    ResponseStatus,
    RequestMetrics
)

# 设置日志
logger = logging.getLogger(__name__)


class MonitoredVolcanoLLMClient(VolcanoLLMClient):
    """
    带监控增强的Volcano LLM客户端
    
    在原有功能基础上添加：
    - 详细的请求/响应日志记录
    - 性能指标收集
    - 提供商特定的监控数据
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 使用对象属性而不是Pydantic字段来避免序列化问题
        object.__setattr__(self, 'performance_monitor', get_performance_monitor())
        object.__setattr__(self, 'provider_name', "volcano")
        
        logger.info("监控增强的Volcano LLM客户端初始化完成")
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        带监控的文本生成调用
        
        Args:
            prompt: 输入提示文本
            stop: 停止词列表
            run_manager: 回调管理器
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 确定请求类型
        request_type = RequestType.TEXT_ONLY
        image_count = 0
        
        # 开始监控记录
        metrics = self.performance_monitor.record_request_start(
            request_id=request_id,
            provider=self.provider_name,
            prompt=prompt,
            request_type=request_type,
            image_count=image_count,
            model=self.model,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens)
        )
        
        if run_manager:
            run_manager.on_llm_start(
                serialized={"name": self._llm_type, "request_id": request_id},
                prompts=[prompt]
            )
        
        try:
            # 调用父类方法
            response = super()._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
            
            # 记录成功结果
            self.performance_monitor.record_request_end(
                metrics=metrics,
                response=response,
                status=ResponseStatus.SUCCESS,
                tokens_used=self._estimate_tokens(prompt, response)
            )
            
            logger.debug(f"请求 {request_id} 成功完成，响应长度: {len(response)}")
            
            return response
            
        except VolcanoAPIException as e:
            # 记录Volcano API异常
            status = self._map_volcano_error_to_status(e.error_type)
            
            self.performance_monitor.record_request_end(
                metrics=metrics,
                status=status,
                error_message=e.message,
                retry_count=getattr(e, 'retry_count', 0)
            )
            
            logger.error(f"请求 {request_id} 失败: {e.error_type.value} - {e.message}")
            raise e
            
        except Exception as e:
            # 记录其他异常
            self.performance_monitor.record_request_end(
                metrics=metrics,
                status=ResponseStatus.ERROR,
                error_message=str(e)
            )
            
            logger.error(f"请求 {request_id} 出现未预期错误: {e}")
            raise e
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        带监控的批量文本生成
        
        Args:
            prompts: 提示文本列表
            stop: 停止词列表
            run_manager: 回调管理器
            **kwargs: 其他参数
            
        Returns:
            LLM生成结果
        """
        batch_id = str(uuid.uuid4())
        logger.info(f"开始批量生成 {batch_id}，包含 {len(prompts)} 个提示")
        
        generations = []
        successful_count = 0
        failed_count = 0
        
        for i, prompt in enumerate(prompts):
            try:
                content = self._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
                generations.append([Generation(text=content)])
                successful_count += 1
                
            except VolcanoAPIException as e:
                generations.append([Generation(
                    text="", 
                    generation_info={
                        "error": e.message,
                        "error_type": e.error_type.value,
                        "request_id": e.request_id,
                        "status_code": e.status_code,
                        "batch_id": batch_id,
                        "prompt_index": i
                    }
                )])
                failed_count += 1
                
            except Exception as e:
                generations.append([Generation(
                    text="", 
                    generation_info={
                        "error": str(e),
                        "error_type": "unknown_error",
                        "batch_id": batch_id,
                        "prompt_index": i
                    }
                )])
                failed_count += 1
        
        logger.info(f"批量生成 {batch_id} 完成: 成功 {successful_count}, 失败 {failed_count}")
        
        return LLMResult(generations=generations)
    
    def generate_multimodal(
        self,
        content: Union[str, List[Dict[str, Any]]],
        **kwargs: Any
    ) -> str:
        """
        带监控的多模态内容生成
        
        Args:
            content: 多模态内容（文本和图片）
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 分析内容类型
        if isinstance(content, str):
            request_type = RequestType.TEXT_ONLY
            image_count = 0
            prompt_text = content
        else:
            # 分析多模态内容
            text_parts = []
            image_count = 0
            
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "image_url":
                        image_count += 1
            
            prompt_text = " ".join(text_parts)
            request_type = RequestType.MULTIMODAL if image_count > 0 else RequestType.TEXT_ONLY
        
        # 开始监控记录
        metrics = self.performance_monitor.record_request_start(
            request_id=request_id,
            provider=self.provider_name,
            prompt=prompt_text,
            request_type=request_type,
            image_count=image_count,
            model=self.model,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens)
        )
        
        try:
            # 准备多模态消息
            if isinstance(content, str):
                messages = [{"role": "user", "content": content}]
            else:
                # 验证和处理多模态内容
                processed_content = self.content_handler.prepare_content(content)
                if not self.content_handler.validate_content(processed_content):
                    raise ValueError("多模态内容验证失败")
                
                messages = [{"role": "user", "content": processed_content}]
            
            # 执行API调用
            response = self._make_api_call(messages, **kwargs)
            response_text = response.choices[0].message.content
            
            # 提取token使用信息
            tokens_used = None
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
            
            # 记录成功结果
            self.performance_monitor.record_request_end(
                metrics=metrics,
                response=response_text,
                status=ResponseStatus.SUCCESS,
                tokens_used=tokens_used or self._estimate_tokens(prompt_text, response_text)
            )
            
            logger.info(f"多模态请求 {request_id} 成功完成")
            
            return response_text
            
        except VolcanoAPIException as e:
            # 记录Volcano API异常
            status = self._map_volcano_error_to_status(e.error_type)
            
            self.performance_monitor.record_request_end(
                metrics=metrics,
                status=status,
                error_message=e.message,
                retry_count=getattr(e, 'retry_count', 0)
            )
            
            logger.error(f"多模态请求 {request_id} 失败: {e.error_type.value} - {e.message}")
            raise e
            
        except Exception as e:
            # 记录其他异常
            self.performance_monitor.record_request_end(
                metrics=metrics,
                status=ResponseStatus.ERROR,
                error_message=str(e)
            )
            
            logger.error(f"多模态请求 {request_id} 出现未预期错误: {e}")
            raise e
    
    def health_check(self) -> Dict[str, Any]:
        """
        带监控的健康检查
        
        Returns:
            健康检查结果
        """
        request_id = str(uuid.uuid4())
        
        # 开始监控记录
        metrics = self.performance_monitor.record_request_start(
            request_id=request_id,
            provider=self.provider_name,
            prompt="Health check",
            request_type=RequestType.HEALTH_CHECK,
            model=self.model
        )
        
        try:
            # 执行简单的健康检查请求
            test_prompt = "Hello, this is a health check."
            response = self._call(test_prompt)
            
            # 记录成功结果
            self.performance_monitor.record_request_end(
                metrics=metrics,
                response=response,
                status=ResponseStatus.SUCCESS,
                tokens_used=self._estimate_tokens(test_prompt, response)
            )
            
            return {
                "status": "healthy",
                "provider": self.provider_name,
                "model": self.model,
                "response_time": metrics.response_time,
                "request_id": request_id,
                "timestamp": time.time()
            }
            
        except Exception as e:
            # 记录失败结果
            status = ResponseStatus.ERROR
            if isinstance(e, VolcanoAPIException):
                status = self._map_volcano_error_to_status(e.error_type)
            
            self.performance_monitor.record_request_end(
                metrics=metrics,
                status=status,
                error_message=str(e)
            )
            
            return {
                "status": "unhealthy",
                "provider": self.provider_name,
                "model": self.model,
                "error": str(e),
                "request_id": request_id,
                "timestamp": time.time()
            }
    
    def _map_volcano_error_to_status(self, error_type: VolcanoErrorType) -> ResponseStatus:
        """
        将Volcano错误类型映射到响应状态
        
        Args:
            error_type: Volcano错误类型
            
        Returns:
            响应状态
        """
        mapping = {
            VolcanoErrorType.RATE_LIMIT_ERROR: ResponseStatus.RATE_LIMITED,
            VolcanoErrorType.API_TIMEOUT_ERROR: ResponseStatus.TIMEOUT,
            VolcanoErrorType.API_CONNECTION_ERROR: ResponseStatus.ERROR,
            VolcanoErrorType.NETWORK_ERROR: ResponseStatus.ERROR,
            VolcanoErrorType.AUTHENTICATION_ERROR: ResponseStatus.ERROR,
            VolcanoErrorType.QUOTA_EXCEEDED_ERROR: ResponseStatus.ERROR,
            VolcanoErrorType.MODEL_OVERLOADED_ERROR: ResponseStatus.ERROR,
            VolcanoErrorType.CONTENT_FILTER_ERROR: ResponseStatus.ERROR,
            VolcanoErrorType.INVALID_REQUEST_ERROR: ResponseStatus.ERROR,
            VolcanoErrorType.UNKNOWN_ERROR: ResponseStatus.ERROR
        }
        
        return mapping.get(error_type, ResponseStatus.ERROR)
    
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """
        估算token使用量（简化版本）
        
        Args:
            prompt: 提示文本
            response: 响应文本
            
        Returns:
            估算的token数量
        """
        # 简化的token估算：大约4个字符 = 1个token
        total_chars = len(prompt) + len(response)
        return max(1, total_chars // 4)
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """
        获取当前客户端的监控统计信息
        
        Returns:
            监控统计数据
        """
        provider_stats = self.performance_monitor.get_provider_stats(self.provider_name)
        
        if not provider_stats:
            return {
                "provider": self.provider_name,
                "status": "no_data",
                "message": "没有可用的统计数据"
            }
        
        return {
            "provider": self.provider_name,
            "model": self.model,
            "total_requests": provider_stats.total_requests,
            "successful_requests": provider_stats.successful_requests,
            "failed_requests": provider_stats.failed_requests,
            "success_rate": provider_stats.success_rate,
            "average_response_time": provider_stats.average_response_time,
            "median_response_time": provider_stats.median_response_time,
            "p95_response_time": provider_stats.p95_response_time,
            "total_tokens": provider_stats.total_tokens,
            "total_cost": provider_stats.total_cost,
            "average_tokens_per_request": provider_stats.average_tokens_per_request,
            "average_cost_per_request": provider_stats.average_cost_per_request,
            "error_count_by_type": provider_stats.error_count_by_type,
            "request_count_by_type": provider_stats.request_count_by_type,
            "last_request_time": provider_stats.last_request_time,
            "last_error_time": provider_stats.last_error_time,
            "last_error_message": provider_stats.last_error_message
        }
    
    def get_recent_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的请求记录
        
        Args:
            limit: 限制数量
            
        Returns:
            最近的请求记录列表
        """
        recent_requests = self.performance_monitor.get_recent_requests(
            limit=limit, 
            provider=self.provider_name
        )
        
        return [request.to_dict() for request in recent_requests]
    
    def export_monitoring_data(self) -> str:
        """
        导出监控数据
        
        Returns:
            JSON格式的监控数据
        """
        return self.performance_monitor.export_metrics()
    
    def reset_monitoring_stats(self):
        """重置监控统计数据"""
        # 注意：这会重置全局监控器的所有数据，包括其他提供商的数据
        logger.warning("重置监控统计数据（影响所有提供商）")
        self.performance_monitor.clear_history()