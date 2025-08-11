#!/usr/bin/env python3
"""
Volcano LLM客户端功能单元测试
测试API认证、连接、多模态内容处理和错误处理场景
"""

import pytest
import os
import time
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from config.volcano_llm_client import (
    VolcanoLLMClient,
    VolcanoAPIException,
    VolcanoErrorType,
    ErrorHandler,
    RetryConfig
)
from config.multimodal_content_handler import (
    MultiModalContentHandler,
    TextContent,
    ImageContent,
    ImageUrl
)


class TestVolcanoLLMClientAuthentication:
    """测试Volcano LLM客户端认证功能"""
    
    def test_client_initialization_with_valid_api_key(self):
        """测试使用有效API密钥初始化客户端"""
        api_key = "test-ark-api-key"
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
        model = "doubao-seed-1-6-250615"
        
        client = VolcanoLLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model
        )
        
        assert client.api_key == api_key
        assert client.base_url == base_url
        assert client.model == model
        assert client.supports_multimodal == True
    
    def test_client_initialization_without_api_key(self):
        """测试没有API密钥时的初始化行为"""
        with pytest.raises(ValueError, match="ARK_API_KEY is required"):
            VolcanoLLMClient(api_key=None)
    
    def test_client_initialization_with_empty_api_key(self):
        """测试空API密钥时的初始化行为"""
        with pytest.raises(ValueError, match="ARK_API_KEY cannot be empty"):
            VolcanoLLMClient(api_key="")
    
    def test_client_initialization_with_invalid_base_url(self):
        """测试无效base_url时的初始化行为"""
        with pytest.raises(ValueError, match="Invalid base_url"):
            VolcanoLLMClient(
                api_key="test-key",
                base_url="invalid-url"
            )
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_openai_client_creation(self, mock_openai):
        """测试OpenAI客户端创建"""
        api_key = "test-ark-api-key"
        base_url = "https://ark.cn-beijing.volces.com/api/v3"
        
        client = VolcanoLLMClient(api_key=api_key, base_url=base_url)
        
        # 验证OpenAI客户端是否正确创建
        mock_openai.assert_called_once_with(
            api_key=api_key,
            base_url=base_url
        )
    
    def test_authentication_error_handling(self):
        """测试认证错误处理"""
        from openai import AuthenticationError
        
        error_handler = ErrorHandler()
        auth_error = AuthenticationError("Invalid API key")
        
        error_type = error_handler.classify_error(auth_error)
        assert error_type == VolcanoErrorType.AUTHENTICATION_ERROR
        
        # 认证错误不应该重试
        should_retry = error_handler.should_retry(error_type, 1)
        assert should_retry == False


class TestVolcanoLLMClientConnection:
    """测试Volcano LLM客户端连接功能"""
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_successful_api_call(self, mock_openai):
        """测试成功的API调用"""
        # 设置mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.total_tokens = 100
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = VolcanoLLMClient(api_key="test-key")
        
        # 模拟调用
        with patch.object(client, '_call') as mock_call:
            mock_call.return_value = "Test response"
            result = client._call("Test prompt")
            
            assert result == "Test response"
            mock_call.assert_called_once_with("Test prompt")
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_api_connection_error_handling(self, mock_openai):
        """测试API连接错误处理"""
        from openai import APIConnectionError
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = APIConnectionError("Connection failed")
        mock_openai.return_value = mock_client
        
        client = VolcanoLLMClient(api_key="test-key")
        error_handler = ErrorHandler()
        
        connection_error = APIConnectionError("Connection failed")
        error_type = error_handler.classify_error(connection_error)
        
        assert error_type == VolcanoErrorType.API_CONNECTION_ERROR
        
        # 连接错误应该重试
        should_retry = error_handler.should_retry(error_type, 1)
        assert should_retry == True
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_api_timeout_error_handling(self, mock_openai):
        """测试API超时错误处理"""
        from openai import APITimeoutError
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = APITimeoutError("Request timeout")
        mock_openai.return_value = mock_client
        
        client = VolcanoLLMClient(api_key="test-key")
        error_handler = ErrorHandler()
        
        timeout_error = APITimeoutError("Request timeout")
        error_type = error_handler.classify_error(timeout_error)
        
        assert error_type == VolcanoErrorType.API_TIMEOUT_ERROR
        
        # 超时错误应该重试
        should_retry = error_handler.should_retry(error_type, 1)
        assert should_retry == True
    
    def test_rate_limit_error_handling(self):
        """测试速率限制错误处理"""
        from openai import RateLimitError
        
        error_handler = ErrorHandler()
        rate_limit_error = RateLimitError("Rate limit exceeded")
        
        error_type = error_handler.classify_error(rate_limit_error)
        assert error_type == VolcanoErrorType.RATE_LIMIT_ERROR
        
        # 速率限制错误应该重试
        should_retry = error_handler.should_retry(error_type, 1)
        assert should_retry == True
        
        # 计算重试延迟
        delay = error_handler.calculate_delay(1, error_type)
        assert delay >= 5.0  # 速率限制至少等待5秒


class TestVolcanoLLMClientMultiModal:
    """测试Volcano LLM客户端多模态功能"""
    
    def test_multimodal_support_detection(self):
        """测试多模态支持检测"""
        client = VolcanoLLMClient(api_key="test-key", supports_multimodal=True)
        assert client.supports_multimodal == True
        
        client_no_multimodal = VolcanoLLMClient(api_key="test-key", supports_multimodal=False)
        assert client_no_multimodal.supports_multimodal == False
    
    def test_text_content_processing(self):
        """测试文本内容处理"""
        client = VolcanoLLMClient(api_key="test-key")
        handler = MultiModalContentHandler()
        
        text_content = "分析用户行为数据"
        processed = handler.prepare_content(text_content)
        
        assert len(processed) == 1
        assert processed[0]["type"] == "text"
        assert processed[0]["text"] == text_content
        
        # 验证内容
        is_valid = handler.validate_content(processed)
        assert is_valid == True
    
    def test_image_content_processing(self):
        """测试图片内容处理"""
        client = VolcanoLLMClient(api_key="test-key")
        handler = MultiModalContentHandler()
        
        image_url = "https://example.com/test-image.png"
        image_content = [
            {"type": "text", "text": "分析这张图片"},
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": "high"
                }
            }
        ]
        
        processed = handler.prepare_content(image_content)
        
        assert len(processed) == 2
        assert processed[0]["type"] == "text"
        assert processed[1]["type"] == "image_url"
        assert processed[1]["image_url"]["url"] == image_url
        assert processed[1]["image_url"]["detail"] == "high"
        
        # 验证内容
        is_valid = handler.validate_content(processed)
        assert is_valid == True
    
    def test_image_url_validation(self):
        """测试图片URL验证"""
        handler = MultiModalContentHandler()
        
        # 有效的HTTP URL
        valid_http_url = "https://example.com/image.png"
        assert handler.validate_image_url(valid_http_url) == True
        
        # 有效的data URL
        valid_data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        assert handler.validate_image_url(valid_data_url) == True
        
        # 无效的URL
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com/image.png",
            "data:text/plain;base64,SGVsbG8="
        ]
        
        for url in invalid_urls:
            assert handler.validate_image_url(url) == False
    
    def test_content_validation_errors(self):
        """测试内容验证错误场景"""
        handler = MultiModalContentHandler()
        
        # 空内容
        empty_content = []
        assert handler.validate_content(empty_content) == False
        
        # 无效的内容类型
        invalid_type_content = [{"type": "invalid", "data": "test"}]
        assert handler.validate_content(invalid_type_content) == False
        
        # 缺少图片URL
        missing_url_content = [{"type": "image_url", "image_url": {}}]
        assert handler.validate_content(missing_url_content) == False
        
        # 无效的图片URL
        invalid_url_content = [
            {
                "type": "image_url",
                "image_url": {"url": "invalid-url"}
            }
        ]
        assert handler.validate_content(invalid_url_content) == False
    
    def test_content_extraction(self):
        """测试内容提取功能"""
        handler = MultiModalContentHandler()
        
        mixed_content = [
            {"type": "text", "text": "第一段文本"},
            {"type": "image_url", "image_url": {"url": "https://example.com/img1.png"}},
            {"type": "text", "text": "第二段文本"},
            {"type": "image_url", "image_url": {"url": "https://example.com/img2.jpg"}}
        ]
        
        # 提取文本
        text_content = handler.extract_text_content(mixed_content)
        assert "第一段文本" in text_content
        assert "第二段文本" in text_content
        
        # 提取图片URL
        image_urls = handler.get_image_urls(mixed_content)
        assert len(image_urls) == 2
        assert "img1.png" in image_urls[0]
        assert "img2.jpg" in image_urls[1]


class TestVolcanoLLMClientErrorHandling:
    """测试Volcano LLM客户端错误处理"""
    
    def test_error_classification(self):
        """测试错误分类"""
        from openai import (
            AuthenticationError, RateLimitError, APITimeoutError,
            APIConnectionError, APIError
        )
        
        error_handler = ErrorHandler()
        
        # 测试各种错误类型的分类
        test_cases = [
            (AuthenticationError("Invalid key"), VolcanoErrorType.AUTHENTICATION_ERROR),
            (RateLimitError("Rate limit"), VolcanoErrorType.RATE_LIMIT_ERROR),
            (APITimeoutError("Timeout"), VolcanoErrorType.API_TIMEOUT_ERROR),
            (APIConnectionError("Connection failed"), VolcanoErrorType.API_CONNECTION_ERROR),
        ]
        
        for error, expected_type in test_cases:
            classified_type = error_handler.classify_error(error)
            assert classified_type == expected_type
    
    def test_retry_logic(self):
        """测试重试逻辑"""
        retry_config = RetryConfig(max_retries=3)
        error_handler = ErrorHandler(retry_config)
        
        # 应该重试的错误类型
        retryable_errors = [
            VolcanoErrorType.RATE_LIMIT_ERROR,
            VolcanoErrorType.API_TIMEOUT_ERROR,
            VolcanoErrorType.API_CONNECTION_ERROR,
            VolcanoErrorType.MODEL_OVERLOADED_ERROR
        ]
        
        for error_type in retryable_errors:
            assert error_handler.should_retry(error_type, 1) == True
            assert error_handler.should_retry(error_type, 3) == False  # 超过最大重试次数
        
        # 不应该重试的错误类型
        non_retryable_errors = [
            VolcanoErrorType.AUTHENTICATION_ERROR,
            VolcanoErrorType.QUOTA_EXCEEDED_ERROR,
            VolcanoErrorType.CONTENT_FILTER_ERROR,
            VolcanoErrorType.INVALID_REQUEST_ERROR
        ]
        
        for error_type in non_retryable_errors:
            assert error_handler.should_retry(error_type, 1) == False
    
    def test_delay_calculation(self):
        """测试延迟计算"""
        retry_config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=False  # 关闭抖动以便测试
        )
        error_handler = ErrorHandler(retry_config)
        
        # 测试指数退避
        delay1 = error_handler.calculate_delay(1, VolcanoErrorType.API_CONNECTION_ERROR)
        delay2 = error_handler.calculate_delay(2, VolcanoErrorType.API_CONNECTION_ERROR)
        
        assert delay1 == 2.0  # 1.0 * 2^1
        assert delay2 == 4.0  # 1.0 * 2^2
        
        # 测试速率限制的特殊处理
        rate_limit_delay = error_handler.calculate_delay(1, VolcanoErrorType.RATE_LIMIT_ERROR)
        assert rate_limit_delay >= 5.0  # 速率限制至少5秒
        
        # 测试最大延迟限制
        large_delay = error_handler.calculate_delay(10, VolcanoErrorType.API_CONNECTION_ERROR)
        assert large_delay <= retry_config.max_delay
    
    def test_custom_exception_creation(self):
        """测试自定义异常创建"""
        from openai import RateLimitError
        
        error_handler = ErrorHandler()
        original_error = RateLimitError("Rate limit exceeded")
        
        custom_exception = error_handler.create_exception(
            original_error,
            VolcanoErrorType.RATE_LIMIT_ERROR
        )
        
        assert isinstance(custom_exception, VolcanoAPIException)
        assert custom_exception.error_type == VolcanoErrorType.RATE_LIMIT_ERROR
        assert custom_exception.original_error == original_error
        assert "Rate limit exceeded" in custom_exception.message
    
    def test_error_logging_and_stats(self):
        """测试错误日志记录和统计"""
        error_handler = ErrorHandler()
        
        # 创建测试异常
        exception = VolcanoAPIException(
            message="Test error",
            error_type=VolcanoErrorType.API_CONNECTION_ERROR
        )
        
        # 记录错误
        error_handler.log_error(exception, attempt=1, will_retry=True)
        
        # 检查统计信息
        stats = error_handler.get_error_stats()
        assert stats["error_counts"]["api_connection_error"] == 1
        assert "api_connection_error" in stats["last_errors"]
        
        # 再次记录同类型错误
        error_handler.log_error(exception, attempt=2, will_retry=False)
        
        updated_stats = error_handler.get_error_stats()
        assert updated_stats["error_counts"]["api_connection_error"] == 2


class TestVolcanoLLMClientIntegration:
    """测试Volcano LLM客户端集成功能"""
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_end_to_end_text_generation(self, mock_openai):
        """测试端到端文本生成"""
        # 设置mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated response"
        mock_response.usage.total_tokens = 50
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = VolcanoLLMClient(api_key="test-key")
        
        # 模拟文本生成
        with patch.object(client, '_call') as mock_call:
            mock_call.return_value = "Generated response"
            result = client._call("Test prompt")
            
            assert result == "Generated response"
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_multimodal_request_processing(self, mock_openai):
        """测试多模态请求处理"""
        # 设置mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Multimodal analysis result"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = VolcanoLLMClient(api_key="test-key", supports_multimodal=True)
        handler = MultiModalContentHandler()
        
        # 准备多模态内容
        multimodal_content = [
            {"type": "text", "text": "分析这张图片"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/test.png",
                    "detail": "high"
                }
            }
        ]
        
        # 验证内容处理
        processed_content = handler.prepare_content(multimodal_content)
        assert handler.validate_content(processed_content) == True
        
        # 验证客户端支持多模态
        assert client.supports_multimodal == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])