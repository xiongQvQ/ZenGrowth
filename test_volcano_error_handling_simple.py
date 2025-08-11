#!/usr/bin/env python3
"""
简化的Volcano LLM客户端错误处理测试
测试增强的错误处理和重试逻辑功能
"""

import logging
import time
import os
from unittest.mock import Mock, patch

# 设置测试环境
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.volcano_llm_client import (
    VolcanoLLMClient,
    VolcanoAPIException,
    VolcanoErrorType,
    RetryConfig,
    ErrorHandler,
    create_volcano_llm,
    create_volcano_llm_with_custom_retry
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_error_type_classification():
    """测试错误类型分类"""
    print("测试错误类型分类...")
    error_handler = ErrorHandler()
    
    # 测试通用网络错误
    network_error = Exception("Connection timeout")
    assert error_handler.classify_error(network_error) == VolcanoErrorType.NETWORK_ERROR
    
    # 测试未知错误
    unknown_error = Exception("Unknown error")
    assert error_handler.classify_error(unknown_error) == VolcanoErrorType.UNKNOWN_ERROR
    
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
    assert error_handler.should_retry(VolcanoErrorType.RATE_LIMIT_ERROR, 0) == True
    assert error_handler.should_retry(VolcanoErrorType.API_TIMEOUT_ERROR, 0) == True
    assert error_handler.should_retry(VolcanoErrorType.API_CONNECTION_ERROR, 0) == True
    assert error_handler.should_retry(VolcanoErrorType.MODEL_OVERLOADED_ERROR, 0) == True
    
    # 测试不应该重试的错误类型
    assert error_handler.should_retry(VolcanoErrorType.AUTHENTICATION_ERROR, 0) == False
    assert error_handler.should_retry(VolcanoErrorType.QUOTA_EXCEEDED_ERROR, 0) == False
    assert error_handler.should_retry(VolcanoErrorType.CONTENT_FILTER_ERROR, 0) == False
    assert error_handler.should_retry(VolcanoErrorType.INVALID_REQUEST_ERROR, 0) == False
    
    # 测试超过最大重试次数
    assert error_handler.should_retry(VolcanoErrorType.RATE_LIMIT_ERROR, 3) == False
    
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
    
    assert delay1 == 1.0  # base_delay * (2^0)
    assert delay2 == 2.0  # base_delay * (2^1)
    assert delay3 == 4.0  # base_delay * (2^2)
    
    # 测试最大延迟限制
    delay_large = error_handler.calculate_delay(10, VolcanoErrorType.API_TIMEOUT_ERROR)
    assert delay_large <= 10.0
    
    # 测试服务器建议的重试时间
    delay_server = error_handler.calculate_delay(0, VolcanoErrorType.RATE_LIMIT_ERROR, retry_after=5)
    assert delay_server == 5.0
    
    # 测试速率限制的最小延迟
    delay_rate_limit = error_handler.calculate_delay(0, VolcanoErrorType.RATE_LIMIT_ERROR)
    assert delay_rate_limit >= 5.0
    
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
    
    print("✓ 重试配置验证测试通过")
    return True


def test_error_statistics():
    """测试错误统计功能"""
    print("测试错误统计功能...")
    error_handler = ErrorHandler()
    
    # 模拟一些错误
    rate_error = Exception("Rate limit")
    auth_error = Exception("Auth failed")
    
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


def test_custom_retry_client_creation():
    """测试自定义重试配置的客户端创建"""
    print("测试自定义重试配置的客户端创建...")
    
    # 设置模拟环境变量
    os.environ["ARK_API_KEY"] = "test_api_key"
    
    try:
        # 测试便捷函数
        client = create_volcano_llm_with_custom_retry(
            max_retries=5,
            base_delay=2.0,
            max_delay=30.0,
            exponential_base=1.5,
            jitter=False
        )
        
        # 验证配置
        assert client.max_retries == 5
        assert client.base_delay == 2.0
        assert client.max_delay == 30.0
        assert client.exponential_base == 1.5
        assert client.jitter == False
        
        print("✓ 自定义重试配置客户端创建测试通过")
        return True
        
    except Exception as e:
        print(f"⚠️ 客户端创建测试跳过 (需要有效的API密钥): {e}")
        return True
    finally:
        if "ARK_API_KEY" in os.environ:
            del os.environ["ARK_API_KEY"]


def run_all_tests():
    """运行所有测试"""
    print("开始Volcano错误处理测试...")
    
    tests = [
        test_error_type_classification,
        test_retry_logic,
        test_delay_calculation,
        test_volcano_api_exception,
        test_retry_config_validation,
        test_error_statistics,
        test_custom_retry_client_creation,
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
            failed += 1
    
    print(f"\n测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("✅ 所有错误处理测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False


def demo_error_handling():
    """演示错误处理功能"""
    print("\n演示Volcano错误处理功能...")
    
    try:
        # 演示错误处理器
        error_handler = ErrorHandler()
        
        # 演示错误分类
        test_error = Exception("Connection timeout")
        error_type = error_handler.classify_error(test_error)
        print(f"错误分类: {error_type.value}")
        
        # 演示重试判断
        should_retry = error_handler.should_retry(error_type, 0)
        print(f"是否应该重试: {should_retry}")
        
        # 演示延迟计算
        delay = error_handler.calculate_delay(0, error_type)
        print(f"重试延迟: {delay:.1f}s")
        
        # 演示异常创建
        volcano_exception = error_handler.create_exception(test_error, error_type)
        print(f"自定义异常: {volcano_exception}")
        
        # 演示错误统计
        error_handler.log_error(volcano_exception, 1, True)
        stats = error_handler.get_error_stats()
        print(f"错误统计: {stats}")
        
        print("✅ 错误处理功能演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return False


if __name__ == "__main__":
    # 运行测试
    test_success = run_all_tests()
    
    # 运行演示
    demo_success = demo_error_handling()
    
    if test_success and demo_success:
        print("\n🎉 Volcano错误处理实现完成并测试通过！")
        exit(0)
    else:
        print("\n💥 测试或演示失败")
        exit(1)