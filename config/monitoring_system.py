"""
监控和日志增强系统
提供商特定的指标收集、详细的请求/响应日志记录和性能监控
"""

import logging
import time
import json
import threading
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import statistics
from pathlib import Path

from pydantic import BaseModel, Field
from config.settings import settings

# 设置日志
logger = logging.getLogger(__name__)


class RequestType(Enum):
    """请求类型枚举"""
    TEXT_ONLY = "text_only"
    MULTIMODAL = "multimodal"
    HEALTH_CHECK = "health_check"
    FALLBACK = "fallback"


class ResponseStatus(Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    FALLBACK_SUCCESS = "fallback_success"


@dataclass
class RequestMetrics:
    """单次请求的指标数据"""
    request_id: str
    provider: str
    request_type: RequestType
    timestamp: float
    prompt_length: int
    response_length: Optional[int] = None
    response_time: Optional[float] = None
    status: Optional[ResponseStatus] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_estimate: Optional[float] = None
    model_used: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    image_count: int = 0
    fallback_used: bool = False
    fallback_provider: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 转换枚举值
        if isinstance(data.get('request_type'), RequestType):
            data['request_type'] = data['request_type'].value
        if isinstance(data.get('status'), ResponseStatus):
            data['status'] = data['status'].value
        return data


@dataclass
class ProviderStats:
    """提供商统计数据"""
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    error_count_by_type: Dict[str, int] = field(default_factory=dict)
    request_count_by_type: Dict[str, int] = field(default_factory=dict)
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_request_time: Optional[float] = None
    last_error_time: Optional[float] = None
    last_error_message: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        """平均响应时间"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    @property
    def median_response_time(self) -> float:
        """响应时间中位数"""
        if not self.response_times:
            return 0.0
        return statistics.median(self.response_times)
    
    @property
    def p95_response_time(self) -> float:
        """95分位响应时间"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]
    
    @property
    def average_tokens_per_request(self) -> float:
        """平均每请求token数"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_tokens / self.successful_requests
    
    @property
    def average_cost_per_request(self) -> float:
        """平均每请求成本"""
        if self.successful_requests == 0:
            return 0.0
        return self.total_cost / self.successful_requests


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.request_history: deque = deque(maxlen=max_history_size)
        self.provider_stats: Dict[str, ProviderStats] = {}
        self.lock = threading.RLock()
        
        # 监控配置
        self.enable_detailed_logging = True
        self.enable_performance_tracking = True
        self.enable_cost_tracking = True
        
        # 日志文件配置
        self.setup_monitoring_logs()
    
    def setup_monitoring_logs(self):
        """设置监控日志文件"""
        log_dir = Path("logs/monitoring")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 请求日志记录器
        self.request_logger = logging.getLogger("volcano.requests")
        self.request_logger.setLevel(logging.INFO)
        
        # 移除现有处理器
        for handler in self.request_logger.handlers[:]:
            self.request_logger.removeHandler(handler)
        
        # 添加文件处理器
        request_handler = logging.FileHandler(
            log_dir / "requests.log",
            encoding="utf-8"
        )
        request_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        self.request_logger.addHandler(request_handler)
        
        # 性能日志记录器
        self.performance_logger = logging.getLogger("volcano.performance")
        self.performance_logger.setLevel(logging.INFO)
        
        # 移除现有处理器
        for handler in self.performance_logger.handlers[:]:
            self.performance_logger.removeHandler(handler)
        
        # 添加文件处理器
        performance_handler = logging.FileHandler(
            log_dir / "performance.log",
            encoding="utf-8"
        )
        performance_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        self.performance_logger.addHandler(performance_handler)
        
        # 错误日志记录器
        self.error_logger = logging.getLogger("volcano.errors")
        self.error_logger.setLevel(logging.WARNING)
        
        # 移除现有处理器
        for handler in self.error_logger.handlers[:]:
            self.error_logger.removeHandler(handler)
        
        # 添加文件处理器
        error_handler = logging.FileHandler(
            log_dir / "errors.log",
            encoding="utf-8"
        )
        error_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        self.error_logger.addHandler(error_handler)
    
    def record_request_start(self, 
                           request_id: str,
                           provider: str,
                           prompt: str,
                           request_type: RequestType = RequestType.TEXT_ONLY,
                           image_count: int = 0,
                           **kwargs) -> RequestMetrics:
        """
        记录请求开始
        
        Args:
            request_id: 请求ID
            provider: 提供商名称
            prompt: 提示文本
            request_type: 请求类型
            image_count: 图片数量
            **kwargs: 其他参数
            
        Returns:
            请求指标对象
        """
        with self.lock:
            # 确保提供商统计存在
            if provider not in self.provider_stats:
                self.provider_stats[provider] = ProviderStats(provider=provider)
            
            # 创建请求指标
            metrics = RequestMetrics(
                request_id=request_id,
                provider=provider,
                request_type=request_type,
                timestamp=time.time(),
                prompt_length=len(prompt),
                image_count=image_count,
                model_used=kwargs.get('model'),
                temperature=kwargs.get('temperature'),
                max_tokens=kwargs.get('max_tokens')
            )
            
            # 记录详细日志
            if self.enable_detailed_logging:
                self.request_logger.info(
                    f"REQUEST_START | {request_id} | {provider} | "
                    f"type={request_type.value} | prompt_len={len(prompt)} | "
                    f"images={image_count} | model={kwargs.get('model', 'unknown')}"
                )
            
            return metrics
    
    def record_request_end(self, 
                          metrics: RequestMetrics,
                          response: Optional[str] = None,
                          status: ResponseStatus = ResponseStatus.SUCCESS,
                          error_message: Optional[str] = None,
                          tokens_used: Optional[int] = None,
                          fallback_used: bool = False,
                          fallback_provider: Optional[str] = None,
                          retry_count: int = 0):
        """
        记录请求结束
        
        Args:
            metrics: 请求指标对象
            response: 响应内容
            status: 响应状态
            error_message: 错误消息
            tokens_used: 使用的token数
            fallback_used: 是否使用了回退
            fallback_provider: 回退提供商
            retry_count: 重试次数
        """
        with self.lock:
            # 更新指标
            end_time = time.time()
            metrics.response_time = end_time - metrics.timestamp
            metrics.response_length = len(response) if response else 0
            metrics.status = status
            metrics.error_message = error_message
            metrics.tokens_used = tokens_used
            metrics.fallback_used = fallback_used
            metrics.fallback_provider = fallback_provider
            metrics.retry_count = retry_count
            
            # 估算成本（简化版本）
            if tokens_used:
                metrics.cost_estimate = self._estimate_cost(metrics.provider, tokens_used)
            
            # 添加到历史记录
            self.request_history.append(metrics)
            
            # 更新提供商统计
            self._update_provider_stats(metrics)
            
            # 记录详细日志
            if self.enable_detailed_logging:
                self._log_request_details(metrics)
            
            # 记录性能日志
            if self.enable_performance_tracking:
                self._log_performance_metrics(metrics)
            
            # 记录错误日志
            if status != ResponseStatus.SUCCESS:
                self._log_error_details(metrics)
    
    def _update_provider_stats(self, metrics: RequestMetrics):
        """更新提供商统计数据"""
        provider = metrics.provider
        stats = self.provider_stats[provider]
        
        # 更新基本统计
        stats.total_requests += 1
        stats.last_request_time = metrics.timestamp
        
        # 更新请求类型统计
        request_type = metrics.request_type.value
        stats.request_count_by_type[request_type] = stats.request_count_by_type.get(request_type, 0) + 1
        
        if metrics.status == ResponseStatus.SUCCESS:
            stats.successful_requests += 1
            if metrics.response_time:
                stats.total_response_time += metrics.response_time
                stats.response_times.append(metrics.response_time)
            if metrics.tokens_used:
                stats.total_tokens += metrics.tokens_used
            if metrics.cost_estimate:
                stats.total_cost += metrics.cost_estimate
        else:
            stats.failed_requests += 1
            stats.last_error_time = metrics.timestamp
            stats.last_error_message = metrics.error_message
            
            # 更新错误类型统计
            error_type = metrics.status.value if metrics.status else "unknown"
            stats.error_count_by_type[error_type] = stats.error_count_by_type.get(error_type, 0) + 1
    
    def _log_request_details(self, metrics: RequestMetrics):
        """记录请求详细日志"""
        log_data = {
            "request_id": metrics.request_id,
            "provider": metrics.provider,
            "type": metrics.request_type.value,
            "status": metrics.status.value,
            "response_time": metrics.response_time,
            "prompt_length": metrics.prompt_length,
            "response_length": metrics.response_length,
            "tokens_used": metrics.tokens_used,
            "cost_estimate": metrics.cost_estimate,
            "image_count": metrics.image_count,
            "fallback_used": metrics.fallback_used,
            "retry_count": metrics.retry_count
        }
        
        self.request_logger.info(f"REQUEST_END | {json.dumps(log_data, ensure_ascii=False)}")
    
    def _log_performance_metrics(self, metrics: RequestMetrics):
        """记录性能指标日志"""
        if metrics.response_time is None:
            return
        
        perf_data = {
            "provider": metrics.provider,
            "response_time": metrics.response_time,
            "tokens_per_second": (metrics.tokens_used / metrics.response_time) if metrics.tokens_used and metrics.response_time > 0 else None,
            "request_type": metrics.request_type.value,
            "model": metrics.model_used,
            "success": metrics.status == ResponseStatus.SUCCESS
        }
        
        self.performance_logger.info(f"PERFORMANCE | {json.dumps(perf_data, ensure_ascii=False)}")
    
    def _log_error_details(self, metrics: RequestMetrics):
        """记录错误详细日志"""
        error_data = {
            "request_id": metrics.request_id,
            "provider": metrics.provider,
            "status": metrics.status.value,
            "error_message": metrics.error_message,
            "response_time": metrics.response_time,
            "retry_count": metrics.retry_count,
            "fallback_used": metrics.fallback_used,
            "fallback_provider": metrics.fallback_provider
        }
        
        self.error_logger.error(f"REQUEST_ERROR | {json.dumps(error_data, ensure_ascii=False)}")
    
    def _estimate_cost(self, provider: str, tokens: int) -> float:
        """
        估算请求成本（简化版本）
        
        Args:
            provider: 提供商名称
            tokens: token数量
            
        Returns:
            估算成本（美元）
        """
        # 简化的成本估算，实际应该根据具体的定价模型
        cost_per_1k_tokens = {
            "google": 0.002,  # Gemini Pro估算
            "volcano": 0.001  # Doubao估算
        }
        
        rate = cost_per_1k_tokens.get(provider, 0.002)
        return (tokens / 1000) * rate
    
    def get_provider_stats(self, provider: str) -> Optional[ProviderStats]:
        """获取提供商统计数据"""
        with self.lock:
            return self.provider_stats.get(provider)
    
    def get_all_provider_stats(self) -> Dict[str, ProviderStats]:
        """获取所有提供商统计数据"""
        with self.lock:
            return self.provider_stats.copy()
    
    def get_recent_requests(self, limit: int = 100, provider: Optional[str] = None) -> List[RequestMetrics]:
        """
        获取最近的请求记录
        
        Args:
            limit: 限制数量
            provider: 过滤特定提供商
            
        Returns:
            请求记录列表
        """
        with self.lock:
            requests = list(self.request_history)
            
            if provider:
                requests = [r for r in requests if r.provider == provider]
            
            # 按时间倒序排列
            requests.sort(key=lambda x: x.timestamp, reverse=True)
            
            return requests[:limit]
    
    def get_performance_comparison(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        获取提供商性能比较
        
        Args:
            time_window_hours: 时间窗口（小时）
            
        Returns:
            性能比较数据
        """
        with self.lock:
            cutoff_time = time.time() - (time_window_hours * 3600)
            recent_requests = [r for r in self.request_history if r.timestamp >= cutoff_time]
            
            comparison = {}
            
            for provider in self.provider_stats.keys():
                provider_requests = [r for r in recent_requests if r.provider == provider]
                
                if not provider_requests:
                    comparison[provider] = {
                        "total_requests": 0,
                        "success_rate": 0.0,
                        "average_response_time": 0.0,
                        "median_response_time": 0.0,
                        "p95_response_time": 0.0,
                        "total_tokens": 0,
                        "total_cost": 0.0,
                        "error_distribution": {}
                    }
                    continue
                
                successful_requests = [r for r in provider_requests if r.status == ResponseStatus.SUCCESS]
                response_times = [r.response_time for r in successful_requests if r.response_time is not None]
                
                # 错误分布
                error_distribution = defaultdict(int)
                for r in provider_requests:
                    if r.status != ResponseStatus.SUCCESS:
                        error_distribution[r.status.value] += 1
                
                comparison[provider] = {
                    "total_requests": len(provider_requests),
                    "successful_requests": len(successful_requests),
                    "success_rate": len(successful_requests) / len(provider_requests) if provider_requests else 0.0,
                    "average_response_time": statistics.mean(response_times) if response_times else 0.0,
                    "median_response_time": statistics.median(response_times) if response_times else 0.0,
                    "p95_response_time": (
                        sorted(response_times)[int(0.95 * len(response_times))] 
                        if response_times else 0.0
                    ),
                    "total_tokens": sum(r.tokens_used for r in successful_requests if r.tokens_used),
                    "total_cost": sum(r.cost_estimate for r in successful_requests if r.cost_estimate),
                    "error_distribution": dict(error_distribution),
                    "multimodal_requests": len([r for r in provider_requests if r.request_type == RequestType.MULTIMODAL]),
                    "fallback_usage": len([r for r in provider_requests if r.fallback_used])
                }
            
            return comparison
    
    def get_hourly_stats(self, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取按小时统计的数据
        
        Args:
            hours: 统计小时数
            
        Returns:
            按小时分组的统计数据
        """
        with self.lock:
            cutoff_time = time.time() - (hours * 3600)
            recent_requests = [r for r in self.request_history if r.timestamp >= cutoff_time]
            
            # 按小时分组
            hourly_data = defaultdict(lambda: defaultdict(list))
            
            for request in recent_requests:
                hour_key = int(request.timestamp // 3600) * 3600  # 向下取整到小时
                hourly_data[hour_key][request.provider].append(request)
            
            # 计算每小时统计
            result = {}
            for provider in self.provider_stats.keys():
                result[provider] = []
                
                for hour_timestamp in sorted(hourly_data.keys()):
                    hour_requests = hourly_data[hour_timestamp][provider]
                    
                    successful = [r for r in hour_requests if r.status == ResponseStatus.SUCCESS]
                    response_times = [r.response_time for r in successful if r.response_time is not None]
                    
                    hour_stats = {
                        "timestamp": hour_timestamp,
                        "datetime": datetime.fromtimestamp(hour_timestamp).isoformat(),
                        "total_requests": len(hour_requests),
                        "successful_requests": len(successful),
                        "success_rate": len(successful) / len(hour_requests) if hour_requests else 0.0,
                        "average_response_time": statistics.mean(response_times) if response_times else 0.0,
                        "total_tokens": sum(r.tokens_used for r in successful if r.tokens_used),
                        "total_cost": sum(r.cost_estimate for r in successful if r.cost_estimate)
                    }
                    
                    result[provider].append(hour_stats)
            
            return result
    
    def export_metrics(self, format: str = "json") -> str:
        """
        导出监控指标
        
        Args:
            format: 导出格式 (json, csv)
            
        Returns:
            导出的数据字符串
        """
        with self.lock:
            export_data = {
                "timestamp": time.time(),
                "datetime": datetime.now().isoformat(),
                "provider_stats": {},
                "performance_comparison": self.get_performance_comparison(),
                "recent_requests": [r.to_dict() for r in self.get_recent_requests(100)]
            }
            
            # 添加提供商统计
            for provider, stats in self.provider_stats.items():
                export_data["provider_stats"][provider] = {
                    "total_requests": stats.total_requests,
                    "successful_requests": stats.successful_requests,
                    "failed_requests": stats.failed_requests,
                    "success_rate": stats.success_rate,
                    "average_response_time": stats.average_response_time,
                    "median_response_time": stats.median_response_time,
                    "p95_response_time": stats.p95_response_time,
                    "total_tokens": stats.total_tokens,
                    "total_cost": stats.total_cost,
                    "average_tokens_per_request": stats.average_tokens_per_request,
                    "average_cost_per_request": stats.average_cost_per_request,
                    "error_count_by_type": stats.error_count_by_type,
                    "request_count_by_type": stats.request_count_by_type,
                    "last_request_time": stats.last_request_time,
                    "last_error_time": stats.last_error_time,
                    "last_error_message": stats.last_error_message
                }
            
            if format == "json":
                return json.dumps(export_data, indent=2, ensure_ascii=False)
            else:
                # 简化的CSV导出
                return "CSV format not implemented yet"
    
    def clear_history(self):
        """清除历史记录"""
        with self.lock:
            self.request_history.clear()
            self.provider_stats.clear()
            logger.info("监控历史记录已清除")
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        
        Returns:
            系统健康状态数据
        """
        with self.lock:
            recent_requests = self.get_recent_requests(1000)
            recent_time = time.time() - 3600  # 最近1小时
            recent_requests = [r for r in recent_requests if r.timestamp >= recent_time]
            
            if not recent_requests:
                return {
                    "status": "no_data",
                    "message": "最近1小时内没有请求数据",
                    "providers": {}
                }
            
            provider_health = {}
            overall_success_rate = 0.0
            total_requests = len(recent_requests)
            successful_requests = len([r for r in recent_requests if r.status == ResponseStatus.SUCCESS])
            
            if total_requests > 0:
                overall_success_rate = successful_requests / total_requests
            
            for provider in self.provider_stats.keys():
                provider_requests = [r for r in recent_requests if r.provider == provider]
                
                if not provider_requests:
                    provider_health[provider] = {
                        "status": "no_data",
                        "requests": 0,
                        "success_rate": 0.0
                    }
                    continue
                
                provider_successful = len([r for r in provider_requests if r.status == ResponseStatus.SUCCESS])
                provider_success_rate = provider_successful / len(provider_requests)
                
                # 判断健康状态
                if provider_success_rate >= 0.95:
                    status = "healthy"
                elif provider_success_rate >= 0.8:
                    status = "degraded"
                else:
                    status = "unhealthy"
                
                provider_health[provider] = {
                    "status": status,
                    "requests": len(provider_requests),
                    "success_rate": provider_success_rate,
                    "average_response_time": statistics.mean([
                        r.response_time for r in provider_requests 
                        if r.response_time is not None and r.status == ResponseStatus.SUCCESS
                    ]) if any(r.response_time for r in provider_requests if r.status == ResponseStatus.SUCCESS) else 0.0
                }
            
            # 整体系统状态
            if overall_success_rate >= 0.95:
                system_status = "healthy"
            elif overall_success_rate >= 0.8:
                system_status = "degraded"
            else:
                system_status = "unhealthy"
            
            return {
                "status": system_status,
                "overall_success_rate": overall_success_rate,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "providers": provider_health,
                "timestamp": time.time(),
                "time_window": "1 hour"
            }


# 全局监控实例
_performance_monitor: Optional[PerformanceMonitor] = None
_monitor_lock = threading.RLock()


def get_performance_monitor() -> PerformanceMonitor:
    """
    获取全局性能监控器实例（单例模式）
    
    Returns:
        性能监控器实例
    """
    global _performance_monitor
    
    if _performance_monitor is None:
        with _monitor_lock:
            if _performance_monitor is None:
                _performance_monitor = PerformanceMonitor()
    
    return _performance_monitor


def reset_performance_monitor():
    """重置性能监控器（主要用于测试）"""
    global _performance_monitor
    with _monitor_lock:
        _performance_monitor = None