#!/usr/bin/env python3
"""
Volcano LLM客户端错误处理测试
测试增强的错误处理和重试逻辑功能
"""

import pytest
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# 设置测试环境
import sys
import os
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


class TestVolcanoErrorHandling:
    """Volcano错误处理测试类"""
    
    def setup_method(self):
        """测试前设置"""
        # 模拟环境变量
        os.environ["ARK_API_KEY"] = "test_api_key"
        
    def teardown_method(self):
        """测试后清理"""
        if "ARK_API_KEY" in os.environ:
            del os.environ["ARK_API_KEY"]
    
    def test_error_type_classification(self):
        """测试错误类型分类"""
        error_handler = ErrorHandler()
        
        # 测试认证错误
        from openai import AuthenticationError
        auth_error = AuthenticationError("Invalid API key")
        assert error_handler.classify_error(auth_error) == VolcanoErrorType.AUTHENTICATION_ERROR
        
        # 测试速率限制错误
        from openai import RateLimitError
        rate_error = RateLimitError("Rate limit exceeded")
        assert error_handler.classify_error(rate_error) == VolcanoErrorType.RATE_LIMIT_ERROR
        
        # 测试超时错误
        from openai import APITimeoutError
        timeout_error = APITimeoutError("Request timeout")
        assert error_handler.classify_error(timeout_error) == VolcanoErrorType.API_TIMEOUT_ERROR
        
        # 测试连接错误
        from openai import APIConnectionError
        connection_error = APIConnectionError("Connection failed")
        assert error_handler.classify_error(connection_error) == VolcanoErrorType.API_CONNECTION_ERROR
        
        # 测试通用网络错误
        network_error = Exception("Connection timeout")
        assert error_handler.classify_error(network_error) == VolcanoErrorType.NETWORK_ERROR
        
        logger.info("✓ 错误类型分类测试通过")
    
    def test_retry_logic(self):
        """测试重试逻辑"""
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
        
        logger.info("✓ 重试逻辑测试通过")
    
    def test_delay_calculation(self):
        """测试延迟计算"""
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
        
        logger.info("✓ 延迟计算测试通过")
    
    def test_volcano_api_exception(self):
        """测试自定义异常"""
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
        
        logger.info("✓ 自定义异常测试通过")
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_client_error_handling(self, mock_openai):
        """测试客户端错误处理"""
        # 设置模拟客户端
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # 创建客户端
        client = create_volcano_llm(max_retries=2, base_delay=0.1)
        
        # 模拟API错误
        from openai import RateLimitError
        mock_client.chat.completions.create.side_effect = RateLimitError("Rate limit exceeded")
        
        # 测试错误处理
        with pytest.raises(VolcanoAPIException) as exc_info:
            client._call("Test prompt")
        
        # 验证异常类型
        assert exc_info.value.error_type == VolcanoErrorType.RATE_LIMIT_ERROR
        
        # 验证重试次数（应该调用3次：初始调用 + 2次重试）
        assert mock_client.chat.completions.create.call_count == 3
        
        logger.info("✓ 客户端错误处理测试通过")
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_successful_retry(self, mock_openai):
        """测试成功重试"""
        # 设置模拟客户端
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # 创建客户端
        client = create_volcano_llm(max_retries=2, base_delay=0.1)
        
        # 模拟第一次失败，第二次成功
        from openai import APITimeoutError
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Success response"
        
        mock_client.chat.completions.create.side_effect = [
            APITimeoutError("Timeout"),
            mock_response
        ]
        
        # 测试重试成功
        result = client._call("Test prompt")
        assert result == "Success response"
        
        # 验证调用次数（1次失败 + 1次成功）
        assert mock_client.chat.completions.create.call_count == 2
        
        logger.info("✓ 成功重试测试通过")
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_connection_test(self, mock_openai):
        """测试连接测试功能"""
        # 设置模拟客户端
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # 创建客户端
        client = create_volcano_llm()
        
        # 模拟成功响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello response"
        mock_client.chat.completions.create.return_value = mock_response
        
        # 测试连接
        result = client.test_connection()
        
        # 验证结果
        assert result["success"] == True
        assert result["response_time"] > 0
        assert "Hello response" in result["response_preview"]
        
        logger.info("✓ 连接测试功能测试通过")
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_health_status(self, mock_openai):
        """测试健康状态检查"""
        # 设置模拟客户端
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        # 创建客户端
        client = create_volcano_llm()
        
        # 模拟成功响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Health check response"
        mock_client.chat.completions.create.return_value = mock_response
        
        # 获取健康状态
        health = client.get_health_status()
        
        # 验证健康状态
        assert health["status"] in ["healthy", "degraded", "unhealthy", "critical"]
        assert 0 <= health["health_score"] <= 100
        assert "connection_test" in health
        assert "error_statistics" in health
        assert "recommendations" in health
        
        logger.info("✓ 健康状态检查测试通过")
    
    def test_retry_config_validation(self):
        """测试重试配置验证"""
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
        
        # 测试边界值
        with pytest.raises(Exception):
            RetryConfig(max_retries=-1)  # 负数应该失败
        
        with pytest.raises(Exception):
            RetryConfig(max_retries=15)  # 超过最大值应该失败
        
        with pytest.raises(Exception):
            RetryConfig(base_delay=0.05)  # 小于最小值应该失败
        
        logger.info("✓ 重试配置验证测试通过")
    
    def test_error_statistics(self):
        """测试错误统计功能"""
        error_handler = ErrorHandler()
        
        # 模拟一些错误
        from openai import RateLimitError, AuthenticationError
        
        rate_error = RateLimitError("Rate limit")
        auth_error = AuthenticationError("Auth failed")
        
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
        
        logger.info("✓ 错误统计功能测试通过")
    
    def test_custom_retry_client_creation(self):
        """测试自定义重试配置的客户端创建"""
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
        
        logger.info("✓ 自定义重试配置客户端创建测试通过")


def run_error_handling_tests():
    """运行错误处理测试"""
    logger.info("开始Volcano错误处理测试...")
    
    test_instance = TestVolcanoErrorHandling()
    
    try:
        # 运行所有测试
        test_instance.setup_method()
        test_instance.test_error_type_classification()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_retry_logic()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_delay_calculation()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_volcano_api_exception()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_retry_config_validation()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_error_statistics()
        test_instance.teardown_method()
        
        test_instance.setup_method()
        test_instance.test_custom_retry_client_creation()
        test_instance.teardown_method()
        
        logger.info("✅ 所有错误处理测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False


def demo_error_handling():
    """演示错误处理功能"""
    logger.info("演示Volcano错误处理功能...")
    
    try:
        # 创建带有自定义重试配置的客户端
        client = create_volcano_llm_with_custom_retry(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )
        
        logger.info("✓ 客户端创建成功")
        
        # 获取模型信息
        model_info = client.get_model_info()
        logger.info(f"模型信息: {model_info}")
        
        # 获取错误统计
        error_stats = client.get_error_statistics()
        logger.info(f"错误统计: {error_stats}")
        
        # 演示重试配置更新
        client.update_retry_config(max_retries=5, base_delay=2.0)
        logger.info("✓ 重试配置更新成功")
        
        # 重置错误统计
        client.reset_error_statistics()
        logger.info("✓ 错误统计重置成功")
        
        logger.info("✅ 错误处理功能演示完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 演示失败: {e}")
        return False


if __name__ == "__main__":
    # 运行测试
    test_success = run_error_handling_tests()
    
    # 运行演示
    demo_success = demo_error_handling()
    
    if test_success and demo_success:
        logger.info("🎉 Volcano错误处理实现完成并测试通过！")
        exit(0)
    else:
        logger.error("💥 测试或演示失败")
        exit(1)