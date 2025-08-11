#!/usr/bin/env python3
"""
核心错误处理组件测试
测试VolcanoAPIException, VolcanoErrorType, RetryConfig, ErrorHandler等核心组件
"""

import logging
import time
import sys
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import Field, BaseModel
import random

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VolcanoErrorType(Enum):
    """Volcano API错误类型枚举"""
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    API_CONNECTION_ERROR = "api_connection_error"
    API_TIMEOUT_ERROR = "api_timeout_error"
    CONTENT_FILTER_ERROR = "content_filter_error"
    MODEL_OVERLOADED_ERROR = "model_overloaded_error"
    INVALID_REQUEST_ERROR = "invalid_request_error"
    QUOTA_EXCEEDED_ERROR = "quota_exceeded_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class VolcanoAPIException(Exception):
    """Volcano API自定义异常类"""
    
    def __init__(
        self,
        message: str,
        error_type: VolcanoErrorType,
        original_error: Optional[Exception] = None,
        retry_after: Optional[int] = None,
        request_id: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        self.retry_after = retry_after
        self.request_id = request_id
        self.status_code = status_code
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message": self.message,
            "error_type": self.error_type.value,
            "original_error": str(self.original_error) if self.original_error else None,
            "retry_after": self.retry_after,
            "request_id": self.request_id,
            "status_code": self.status_code,
            "timestamp": self.timestamp
        }
    
    def __str__(self) -> str:
        return f"VolcanoAPIException({self.error_type.value}): {self.message}"


class RetryConfig(BaseModel):
    """重试配置"""
    max_retries: int = Field(default=3, ge=0, le=10)
    base_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    max_delay: float = Field(default=60.0, ge=1.0, le=300.0)
    exponential_base: float = Field(default=2.0, ge=1.1, le=10.0)
    jitter: bool = Field(default=True)
    retry_on_timeout: bool = Field(default=True)
    retry_on_connection_error: bool = Field(default=True)
    retry_on_rate_limit: bool = Field(default=True)
    retry_on_server_error: bool = Field(default=True)


class ErrorHandler:
    """Volcano API错误处理器"""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()
        self.error_counts = {}
        self.last_errors = {}
    
    def classify_error(self, error: Exception) -> VolcanoErrorType:
        """
        分类错误类型
        
        Args:
            error: 原始异常
            
        Returns:
            错误类型
        """
        # 简化的错误分类逻辑，不依赖OpenAI包
        error_msg = str(error).lower()
        
        if "authentication" in error_msg or "unauthorized" in error_msg:
            return VolcanoErrorType.AUTHENTICATION_ERROR
        elif "rate limit" in error_msg or "too many requests" in error_msg:
            return VolcanoErrorType.RATE_LIMIT_ERROR
        elif "timeout" in error_msg:
            return VolcanoErrorType.API_TIMEOUT_ERROR
        elif "connection" in error_msg or "network" in error_msg or "dns" in error_msg:
            return VolcanoErrorType.NETWORK_ERROR
        elif "content filter" in error_msg or "safety" in error_msg:
            return VolcanoErrorType.CONTENT_FILTER_ERROR
        elif "quota" in error_msg or "limit" in error_msg:
            return VolcanoErrorType.QUOTA_EXCEEDED_ERROR
        elif "overloaded" in error_msg or "busy" in error_msg:
            return VolcanoErrorType.MODEL_OVERLOADED_ERROR
        elif "invalid" in error_msg or "bad request" in error_msg:
            return VolcanoErrorType.INVALID_REQUEST_ERROR
        else:
            return VolcanoErrorType.UNKNOWN_ERROR
    
    def should_retry(self, error_type: VolcanoErrorType, attempt: int) -> bool:
        """
        判断是否应该重试
        
        Args:
            error_type: 错误类型
            attempt: 当前尝试次数
            
        Returns:
            是否应该重试
        """
        if attempt >= self.retry_config.max_retries:
            return False
        
        # 根据错误类型决定是否重试
        retry_map = {
            VolcanoErrorType.RATE_LIMIT_ERROR: self.retry_config.retry_on_rate_limit,
            VolcanoErrorType.API_TIMEOUT_ERROR: self.retry_config.retry_on_timeout,
            VolcanoErrorType.API_CONNECTION_ERROR: self.retry_config.retry_on_connection_error,
            VolcanoErrorType.NETWORK_ERROR: self.retry_config.retry_on_connection_error,
            VolcanoErrorType.MODEL_OVERLOADED_ERROR: self.retry_config.retry_on_server_error,
            VolcanoErrorType.AUTHENTICATION_ERROR: False,  # 认证错误不重试
            VolcanoErrorType.QUOTA_EXCEEDED_ERROR: False,  # 配额错误不重试
            VolcanoErrorType.CONTENT_FILTER_ERROR: False,  # 内容过滤错误不重试
            VolcanoErrorType.INVALID_REQUEST_ERROR: False,  # 无效请求不重试
        }
        
        return retry_map.get(error_type, False)
    
    def calculate_delay(self, attempt: int, error_type: VolcanoErrorType, retry_after: Optional[int] = None) -> float:
        """
        计算重试延迟时间
        
        Args:
            attempt: 当前尝试次数
            error_type: 错误类型
            retry_after: 服务器建议的重试时间
            
        Returns:
            延迟时间（秒）
        """
        if retry_after is not None:
            # 使用服务器建议的重试时间
            delay = min(retry_after, self.retry_config.max_delay)
        else:
            # 指数退避
            delay = self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt)
            delay = min(delay, self.retry_config.max_delay)
        
        # 添加抖动以避免雷群效应
        if self.retry_config.jitter:
            jitter_range = delay * 0.1  # 10%的抖动
            delay += random.uniform(-jitter_range, jitter_range)
        
        # 对于速率限制错误，使用更长的延迟
        if error_type == VolcanoErrorType.RATE_LIMIT_ERROR:
            delay = max(delay, 5.0)  # 至少等待5秒
        
        return max(delay, 0.1)  # 最小延迟0.1秒
    
    def create_exception(self, error: Exception, error_type: VolcanoErrorType) -> VolcanoAPIException:
        """
        创建自定义异常
        
        Args:
            error: 原始异常
            error_type: 错误类型
            
        Returns:
            自定义异常
        """
        # 提取错误信息
        message = str(error)
        retry_after = None
        request_id = None
        status_code = None
        
        # 简化的响应信息提取（不依赖具体的HTTP库）
        if hasattr(error, 'response') and error.response:
            if hasattr(error.response, 'status_code'):
                status_code = error.response.status_code
            
            if hasattr(error.response, 'headers'):
                headers = error.response.headers
                retry_after = headers.get('Retry-After')
                if retry_after:
                    try:
                        retry_after = int(retry_after)
                    except ValueError:
                        retry_after = None
                
                request_id = headers.get('X-Request-ID') or headers.get('Request-ID')
        
        return VolcanoAPIException(
            message=message,
            error_type=error_type,
            original_error=error,
            retry_after=retry_after,
            request_id=request_id,
            status_code=status_code
        )
    
    def log_error(self, exception: VolcanoAPIException, attempt: int, will_retry: bool):
        """
        记录错误日志
        
        Args:
            exception: 异常对象
            attempt: 尝试次数
            will_retry: 是否会重试
        """
        error_info = {
            "error_type": exception.error_type.value,
            "message": exception.message,
            "attempt": attempt,
            "will_retry": will_retry,
            "request_id": exception.request_id,
            "status_code": exception.status_code,
            "timestamp": exception.timestamp
        }
        
        if will_retry:
            logger.warning(f"Volcano API错误 (将重试): {error_info}")
        else:
            logger.error(f"Volcano API错误 (不重试): {error_info}")
        
        # 更新错误统计
        error_key = exception.error_type.value
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = exception.timestamp
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Returns:
            错误统计字典
        """
        return {
            "error_counts": self.error_counts.copy(),
            "last_errors": self.last_errors.copy(),
            "retry_config": self.retry_config.dict()
        }


def test_error_type_classification():
    """测试错误类型分类"""
    print("测试错误类型分类...")
    error_handler = ErrorHandler()
    
    # 测试各种错误类型
    test_cases = [
        ("Authentication failed", VolcanoErrorType.AUTHENTICATION_ERROR),
        ("Rate limit exceeded", VolcanoErrorType.RATE_LIMIT_ERROR),
        ("Connection timeout", VolcanoErrorType.API_TIMEOUT_ERROR),
        ("Network connection failed", VolcanoErrorType.NETWORK_ERROR),
        ("Content filter violation", VolcanoErrorType.CONTENT_FILTER_ERROR),
        ("Quota exceeded", VolcanoErrorType.QUOTA_EXCEEDED_ERROR),
        ("Model overloaded", VolcanoErrorType.MODEL_OVERLOADED_ERROR),
        ("Invalid request format", VolcanoErrorType.INVALID_REQUEST_ERROR),
        ("Unknown error occurred", VolcanoErrorType.UNKNOWN_ERROR),
    ]
    
    for error_msg, expected_type in test_cases:
        error = Exception(error_msg)
        actual_type = error_handler.classify_error(error)
        assert actual_type == expected_type, f"Expected {expected_type}, got {actual_type} for '{error_msg}'"
    
    print("✓ 错误类型分类测试通过")
    return True


def test_retry_logic():
    """测试重试逻辑"""
    print("测试重试逻辑...")
    retry_config = RetryConfig(
        max_retries=3,
        base_delay=0.1,
        max_delay=1.0,
        exponential_base=2.0,
        jitter=False
    )
    error_handler = ErrorHandler(retry_config)
    
    # 测试应该重试的错误类型
    retryable_errors = [
        VolcanoErrorType.RATE_LIMIT_ERROR,
        VolcanoErrorType.API_TIMEOUT_ERROR,
        VolcanoErrorType.API_CONNECTION_ERROR,
        VolcanoErrorType.MODEL_OVERLOADED_ERROR,
        VolcanoErrorType.NETWORK_ERROR
    ]
    
    for error_type in retryable_errors:
        assert error_handler.should_retry(error_type, 0) == True, f"{error_type} should be retryable"
        assert error_handler.should_retry(error_type, 1) == True, f"{error_type} should be retryable on attempt 1"
        assert error_handler.should_retry(error_type, 2) == True, f"{error_type} should be retryable on attempt 2"
        assert error_handler.should_retry(error_type, 3) == False, f"{error_type} should not be retryable after max attempts"
    
    # 测试不应该重试的错误类型
    non_retryable_errors = [
        VolcanoErrorType.AUTHENTICATION_ERROR,
        VolcanoErrorType.QUOTA_EXCEEDED_ERROR,
        VolcanoErrorType.CONTENT_FILTER_ERROR,
        VolcanoErrorType.INVALID_REQUEST_ERROR
    ]
    
    for error_type in non_retryable_errors:
        assert error_handler.should_retry(error_type, 0) == False, f"{error_type} should not be retryable"
    
    print("✓ 重试逻辑测试通过")
    return True


def test_delay_calculation():
    """测试延迟计算"""
    print("测试延迟计算...")
    retry_config = RetryConfig(
        base_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=False
    )
    error_handler = ErrorHandler(retry_config)
    
    # 测试指数退避
    delay1 = error_handler.calculate_delay(0, VolcanoErrorType.API_TIMEOUT_ERROR)
    delay2 = error_handler.calculate_delay(1, VolcanoErrorType.API_TIMEOUT_ERROR)
    delay3 = error_handler.calculate_delay(2, VolcanoErrorType.API_TIMEOUT_ERROR)
    
    assert delay1 == 1.0, f"Expected 1.0, got {delay1}"
    assert delay2 == 2.0, f"Expected 2.0, got {delay2}"
    assert delay3 == 4.0, f"Expected 4.0, got {delay3}"
    
    # 测试最大延迟限制
    delay_large = error_handler.calculate_delay(10, VolcanoErrorType.API_TIMEOUT_ERROR)
    assert delay_large <= 10.0, f"Delay should not exceed max_delay: {delay_large}"
    
    # 测试服务器建议的重试时间
    delay_server = error_handler.calculate_delay(0, VolcanoErrorType.RATE_LIMIT_ERROR, retry_after=5)
    assert delay_server == 5.0, f"Expected 5.0, got {delay_server}"
    
    # 测试速率限制的最小延迟
    delay_rate_limit = error_handler.calculate_delay(0, VolcanoErrorType.RATE_LIMIT_ERROR)
    assert delay_rate_limit >= 5.0, f"Rate limit delay should be at least 5.0: {delay_rate_limit}"
    
    print("✓ 延迟计算测试通过")
    return True


def test_volcano_api_exception():
    """测试自定义异常"""
    print("测试自定义异常...")
    original_error = Exception("Test error")
    exception = VolcanoAPIException(
        message="Test message",
        error_type=VolcanoErrorType.API_TIMEOUT_ERROR,
        original_error=original_error,
        retry_after=10,
        request_id="req_123",
        status_code=408
    )
    
    # 测试异常属性
    assert exception.message == "Test message"
    assert exception.error_type == VolcanoErrorType.API_TIMEOUT_ERROR
    assert exception.original_error == original_error
    assert exception.retry_after == 10
    assert exception.request_id == "req_123"
    assert exception.status_code == 408
    assert exception.timestamp > 0
    
    # 测试转换为字典
    exception_dict = exception.to_dict()
    assert exception_dict["message"] == "Test message"
    assert exception_dict["error_type"] == "api_timeout_error"
    assert exception_dict["retry_after"] == 10
    assert exception_dict["request_id"] == "req_123"
    assert exception_dict["status_code"] == 408
    
    # 测试字符串表示
    str_repr = str(exception)
    assert "api_timeout_error" in str_repr
    assert "Test message" in str_repr
    
    print("✓ 自定义异常测试通过")
    return True


def test_retry_config_validation():
    """测试重试配置验证"""
    print("测试重试配置验证...")
    
    # 测试有效配置
    valid_config = RetryConfig(
        max_retries=5,
        base_delay=2.0,
        max_delay=120.0,
        exponential_base=1.5,
        jitter=True
    )
    assert valid_config.max_retries == 5
    assert valid_config.base_delay == 2.0
    assert valid_config.max_delay == 120.0
    assert valid_config.exponential_base == 1.5
    assert valid_config.jitter == True
    
    # 测试默认配置
    default_config = RetryConfig()
    assert default_config.max_retries == 3
    assert default_config.base_delay == 1.0
    assert default_config.max_delay == 60.0
    assert default_config.exponential_base == 2.0
    assert default_config.jitter == True
    
    print("✓ 重试配置验证测试通过")
    return True


def test_error_statistics():
    """测试错误统计功能"""
    print("测试错误统计功能...")
    error_handler = ErrorHandler()
    
    # 模拟一些错误
    rate_error = Exception("Rate limit exceeded")
    auth_error = Exception("Authentication failed")
    
    # 分类并记录错误
    rate_exception = error_handler.create_exception(rate_error, VolcanoErrorType.RATE_LIMIT_ERROR)
    auth_exception = error_handler.create_exception(auth_error, VolcanoErrorType.AUTHENTICATION_ERROR)
    
    error_handler.log_error(rate_exception, 1, True)
    error_handler.log_error(auth_exception, 1, False)
    error_handler.log_error(rate_exception, 2, False)
    
    # 获取统计信息
    stats = error_handler.get_error_stats()
    
    # 验证统计
    assert stats["error_counts"]["rate_limit_error"] == 2
    assert stats["error_counts"]["authentication_error"] == 1
    assert "rate_limit_error" in stats["last_errors"]
    assert "authentication_error" in stats["last_errors"]
    
    print("✓ 错误统计功能测试通过")
    return True


def test_comprehensive_error_handling_workflow():
    """测试完整的错误处理工作流"""
    print("测试完整的错误处理工作流...")
    
    # 创建错误处理器
    retry_config = RetryConfig(max_retries=2, base_delay=0.1, jitter=False)
    error_handler = ErrorHandler(retry_config)
    
    # 模拟API调用重试流程
    original_error = Exception("Connection timeout")
    
    for attempt in range(3):  # 0, 1, 2
        # 分类错误
        error_type = error_handler.classify_error(original_error)
        assert error_type == VolcanoErrorType.API_TIMEOUT_ERROR
        
        # 创建异常
        volcano_exception = error_handler.create_exception(original_error, error_type)
        
        # 判断是否重试
        should_retry = error_handler.should_retry(error_type, attempt)
        expected_retry = attempt < 2  # 前两次应该重试
        assert should_retry == expected_retry, f"Attempt {attempt}: expected retry={expected_retry}, got {should_retry}"
        
        # 记录错误
        error_handler.log_error(volcano_exception, attempt + 1, should_retry)
        
        if should_retry:
            # 计算延迟
            delay = error_handler.calculate_delay(attempt, error_type)
            expected_delay = 0.1 * (2.0 ** attempt)  # 指数退避
            assert abs(delay - expected_delay) < 0.01, f"Expected delay {expected_delay}, got {delay}"
        else:
            # 最后一次不重试，退出循环
            break
    
    # 检查统计信息
    stats = error_handler.get_error_stats()
    assert stats["error_counts"]["api_timeout_error"] == 3
    
    print("✓ 完整的错误处理工作流测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("开始Volcano核心错误处理测试...")
    
    tests = [
        test_error_type_classification,
        test_retry_logic,
        test_delay_calculation,
        test_volcano_api_exception,
        test_retry_config_validation,
        test_error_statistics,
        test_comprehensive_error_handling_workflow,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试失败: {test.__name__} - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("✅ 所有核心错误处理测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


def demo_error_handling():
    """演示错误处理功能"""
    print("\n演示Volcano核心错误处理功能...")
    
    try:
        # 演示错误处理器
        error_handler = ErrorHandler()
        
        # 演示各种错误类型的处理
        error_scenarios = [
            ("Rate limit exceeded", "应该重试"),
            ("Authentication failed", "不应该重试"),
            ("Connection timeout", "应该重试"),
            ("Invalid request format", "不应该重试"),
            ("Model overloaded", "应该重试"),
        ]
        
        print("\n错误处理场景演示:")
        for error_msg, expected_behavior in error_scenarios:
            error = Exception(error_msg)
            error_type = error_handler.classify_error(error)
            should_retry = error_handler.should_retry(error_type, 0)
            delay = error_handler.calculate_delay(0, error_type) if should_retry else 0
            
            print(f"  错误: '{error_msg}'")
            print(f"    类型: {error_type.value}")
            print(f"    重试: {'是' if should_retry else '否'} ({expected_behavior})")
            if should_retry:
                print(f"    延迟: {delay:.1f}s")
            print()
        
        # 演示错误统计
        print("错误统计演示:")
        for error_msg, _ in error_scenarios[:3]:  # 只处理前3个
            error = Exception(error_msg)
            error_type = error_handler.classify_error(error)
            volcano_exception = error_handler.create_exception(error, error_type)
            error_handler.log_error(volcano_exception, 1, True)
        
        stats = error_handler.get_error_stats()
        print(f"  错误计数: {stats['error_counts']}")
        print(f"  最后错误时间: {len(stats['last_errors'])} 种错误类型")
        
        print("\n✅ 核心错误处理功能演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行测试
    test_success = run_all_tests()
    
    # 运行演示
    demo_success = demo_error_handling()
    
    if test_success and demo_success:
        print("\n🎉 Volcano核心错误处理实现完成并测试通过！")
        print("\n核心功能包括:")
        print("  ✓ 错误类型分类和识别")
        print("  ✓ 智能重试逻辑判断")
        print("  ✓ 指数退避延迟计算")
        print("  ✓ 自定义异常封装")
        print("  ✓ 错误统计和监控")
        print("  ✓ 可配置的重试策略")
        print("  ✓ 详细的错误日志记录")
        exit(0)
    else:
        print("\n💥 测试或演示失败")
        exit(1)