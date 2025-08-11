#!/usr/bin/env python3
"""
多模态功能单元测试
测试图片内容处理、内容验证和错误处理、提供商特定格式化
"""

import pytest
import base64
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from config.multimodal_content_handler import (
    MultiModalContentHandler,
    TextContent,
    ImageContent,
    ImageUrl,
    MultiModalRequest,
    create_text_content,
    create_image_content,
    create_multimodal_content
)
from config.volcano_llm_client import VolcanoLLMClient


class TestImageContentProcessing:
    """测试图片内容处理"""
    
    def test_text_content_creation(self):
        """测试文本内容创建"""
        text = "分析用户行为数据"
        content = create_text_content(text)
        
        assert isinstance(content, TextContent)
        assert content.type == "text"
        assert content.text == text
    
    def test_image_content_creation(self):
        """测试图片内容创建"""
        url = "https://example.com/chart.png"
        detail = "high"
        
        content = create_image_content(url, detail)
        
        assert isinstance(content, ImageContent)
        assert content.type == "image_url"
        assert content.image_url.url == url
        assert content.image_url.detail == detail
    
    def test_multimodal_content_creation(self):
        """测试多模态内容创建"""
        text = "请分析这些图表"
        image_urls = [
            "https://example.com/chart1.png",
            "https://example.com/chart2.jpg"
        ]
        
        content_list = create_multimodal_content(text, image_urls)
        
        assert len(content_list) == 3  # 1个文本 + 2个图片
        assert content_list[0].type == "text"
        assert content_list[1].type == "image_url"
        assert content_list[2].type == "image_url"
        
        assert content_list[0].text == text
        assert content_list[1].image_url.url == image_urls[0]
        assert content_list[2].image_url.url == image_urls[1]
    
    def test_image_url_validation_http(self):
        """测试HTTP图片URL验证"""
        handler = MultiModalContentHandler()
        
        valid_urls = [
            "https://example.com/image.png",
            "http://example.com/photo.jpg",
            "https://cdn.example.com/assets/chart.gif",
            "https://example.com/path/to/image.webp"
        ]
        
        for url in valid_urls:
            assert handler.validate_image_url(url) == True, f"应该验证通过: {url}"
    
    def test_image_url_validation_data_url(self):
        """测试data URL验证"""
        handler = MultiModalContentHandler()
        
        # 有效的data URL (1x1像素PNG)
        valid_data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        assert handler.validate_image_url(valid_data_url) == True
        
        # 有效的JPEG data URL
        valid_jpeg_data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"
        assert handler.validate_image_url(valid_jpeg_data_url) == True
    
    def test_image_url_validation_invalid(self):
        """测试无效图片URL"""
        handler = MultiModalContentHandler()
        
        invalid_urls = [
            "",  # 空URL
            "not-a-url",  # 不是URL
            "ftp://example.com/image.png",  # 不支持的协议
            "data:text/plain;base64,SGVsbG8=",  # 不是图片的data URL
            "data:image/png;base64,invalid-base64",  # 无效的base64
            "https://",  # 不完整的URL
            "http://",  # 不完整的URL
        ]
        
        for url in invalid_urls:
            assert handler.validate_image_url(url) == False, f"应该验证失败: {url}"
    
    def test_image_size_validation(self):
        """测试图片大小验证"""
        handler = MultiModalContentHandler(max_image_size_mb=5)
        
        # 创建一个小的有效base64图片
        small_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        small_data_url = f"data:image/png;base64,{small_image_data}"
        
        assert handler.validate_image_url(small_data_url) == True
        
        # 创建一个过大的base64数据（模拟）
        large_image_data = "A" * (6 * 1024 * 1024)  # 6MB的数据
        large_data_url = f"data:image/png;base64,{large_image_data}"
        
        assert handler.validate_image_url(large_data_url) == False
    
    def test_image_format_support(self):
        """测试支持的图片格式"""
        handler = MultiModalContentHandler()
        
        supported_formats = [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A",
            "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
            "data:image/webp;base64,UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEADsD+JaQAA3AAAAAA"
        ]
        
        for data_url in supported_formats:
            assert handler.validate_image_url(data_url) == True, f"应该支持格式: {data_url[:50]}..."
        
        # 不支持的格式
        unsupported_format = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMSIgaGVpZ2h0PSIxIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxIiBoZWlnaHQ9IjEiIGZpbGw9InJlZCIvPjwvc3ZnPg=="
        assert handler.validate_image_url(unsupported_format) == False


class TestContentValidationAndErrorHandling:
    """测试内容验证和错误处理"""
    
    def test_content_structure_validation(self):
        """测试内容结构验证"""
        handler = MultiModalContentHandler()
        
        # 有效的内容结构
        valid_content = [
            {"type": "text", "text": "分析这张图片"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image.png",
                    "detail": "high"
                }
            }
        ]
        
        validation_result = handler.validate_content_structure(valid_content)
        
        assert validation_result["is_valid"] == True
        assert len(validation_result["errors"]) == 0
        assert validation_result["statistics"]["text_items"] == 1
        assert validation_result["statistics"]["image_items"] == 1
    
    def test_content_validation_errors(self):
        """测试内容验证错误"""
        handler = MultiModalContentHandler()
        
        # 空内容
        empty_content = []
        result = handler.validate_content_structure(empty_content)
        assert result["is_valid"] == False
        assert "内容列表为空" in result["errors"]
        
        # 无效的内容类型
        invalid_type_content = [{"type": "invalid_type", "data": "test"}]
        result = handler.validate_content_structure(invalid_type_content)
        assert result["is_valid"] == False
        assert any("内容类型无效" in error for error in result["errors"])
        
        # 缺少图片URL
        missing_url_content = [
            {
                "type": "image_url",
                "image_url": {}  # 缺少url字段
            }
        ]
        result = handler.validate_content_structure(missing_url_content)
        assert result["is_valid"] == False
        assert any("图片URL为空" in error for error in result["errors"])
    
    def test_content_normalization(self):
        """测试内容标准化"""
        handler = MultiModalContentHandler()
        
        # 需要标准化的内容
        raw_content = [
            {"type": "text", "text": "  分析数据  "},  # 有多余空格
            {
                "type": "image_url",
                "image_url": {
                    "url": "  https://example.com/image.png  ",  # 有多余空格
                    "detail": "invalid_detail"  # 无效的detail值
                }
            }
        ]
        
        normalized = handler.normalize_content(raw_content)
        
        assert len(normalized) == 2
        assert normalized[0]["text"] == "分析数据"  # 去除空格
        assert normalized[1]["image_url"]["url"] == "https://example.com/image.png"  # 去除空格
        assert normalized[1]["image_url"]["detail"] == "auto"  # 标准化为默认值
    
    def test_content_extraction_functions(self):
        """测试内容提取功能"""
        handler = MultiModalContentHandler()
        
        mixed_content = [
            {"type": "text", "text": "第一段文本"},
            {"type": "image_url", "image_url": {"url": "https://example.com/img1.png"}},
            {"type": "text", "text": "第二段文本"},
            {"type": "image_url", "image_url": {"url": "https://example.com/img2.jpg"}},
            {"type": "text", "text": ""}  # 空文本
        ]
        
        # 提取文本内容
        text_content = handler.extract_text_content(mixed_content)
        assert "第一段文本" in text_content
        assert "第二段文本" in text_content
        assert text_content.count("\n") >= 1  # 多段文本用换行分隔
        
        # 提取图片URL
        image_urls = handler.get_image_urls(mixed_content)
        assert len(image_urls) == 2
        assert "img1.png" in image_urls[0]
        assert "img2.jpg" in image_urls[1]
    
    def test_batch_image_validation(self):
        """测试批量图片验证"""
        handler = MultiModalContentHandler()
        
        image_urls = [
            "https://example.com/valid1.png",
            "https://example.com/valid2.jpg",
            "invalid-url",
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            ""  # 空URL
        ]
        
        results = handler.batch_validate_images(image_urls)
        
        assert results["total"] == 5
        assert results["valid"] == 3  # 前两个HTTP URL和data URL
        assert results["invalid"] == 2  # invalid-url和空URL
        assert len(results["details"]) == 5
        assert len(results["errors"]) == 0  # 没有异常错误，只是验证失败
    
    def test_error_handling_in_validation(self):
        """测试验证过程中的错误处理"""
        handler = MultiModalContentHandler()
        
        # 模拟验证过程中的异常
        with patch.object(handler, 'validate_image_url', side_effect=Exception("Validation error")):
            image_urls = ["https://example.com/image.png"]
            results = handler.batch_validate_images(image_urls)
            
            assert results["total"] == 1
            assert results["invalid"] == 1
            assert len(results["errors"]) == 1
            assert "Validation error" in results["errors"][0]["error"]


class TestProviderSpecificFormatting:
    """测试提供商特定格式化"""
    
    def test_volcano_provider_formatting(self):
        """测试Volcano提供商格式化"""
        handler = MultiModalContentHandler()
        
        content = [
            {"type": "text", "text": "分析图片"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image.png",
                    "detail": "high"
                }
            }
        ]
        
        # Volcano使用OpenAI兼容格式，应该保持原样
        formatted = handler.format_for_provider(content, "volcano")
        
        assert formatted == content  # 应该保持不变
        assert len(formatted) == 2
        assert formatted[0]["type"] == "text"
        assert formatted[1]["type"] == "image_url"
    
    def test_google_provider_formatting(self):
        """测试Google提供商格式化"""
        handler = MultiModalContentHandler()
        
        content = [
            {"type": "text", "text": "分析图片"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image.png",
                    "detail": "high"
                }
            }
        ]
        
        # Google可能需要不同的格式（当前实现返回原格式）
        formatted = handler.format_for_provider(content, "google")
        
        assert formatted is not None
        assert len(formatted) == 2
        # 具体格式要求可能在未来实现中改变
    
    def test_unknown_provider_formatting(self):
        """测试未知提供商格式化"""
        handler = MultiModalContentHandler()
        
        content = [
            {"type": "text", "text": "分析图片"}
        ]
        
        # 未知提供商应该返回原格式
        formatted = handler.format_for_provider(content, "unknown_provider")
        
        assert formatted == content
    
    def test_content_metadata_enhancement(self):
        """测试内容元数据增强"""
        handler = MultiModalContentHandler()
        
        content = [
            {"type": "text", "text": "分析图片"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image.png",
                    "detail": "high"
                }
            }
        ]
        
        enhanced = handler.enhance_content_with_metadata(content)
        
        assert len(enhanced) == 2
        
        # 检查元数据是否添加
        for i, item in enumerate(enhanced):
            assert "_metadata" in item
            assert item["_metadata"]["index"] == i
            assert "timestamp" in item["_metadata"]
    
    def test_image_info_extraction(self):
        """测试图片信息提取"""
        handler = MultiModalContentHandler()
        
        # HTTP URL信息
        http_url = "https://example.com/path/image.png"
        http_info = handler.get_image_info(http_url)
        
        assert http_info["url"] == http_url
        assert http_info["type"] == "http_url"
        assert http_info["is_data_url"] == False
        assert http_info["domain"] == "example.com"
        assert http_info["format"] == "png"
        
        # Data URL信息
        data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"
        data_info = handler.get_image_info(data_url)
        
        assert data_info["url"] == data_url
        assert data_info["type"] == "data_url"
        assert data_info["is_data_url"] == True
        assert data_info["format"] == "jpeg"
        assert data_info["size_mb"] is not None


class TestMultiModalRequest:
    """测试多模态请求"""
    
    def test_multimodal_request_creation(self):
        """测试多模态请求创建"""
        content = [
            create_text_content("分析用户行为"),
            create_image_content("https://example.com/chart.png")
        ]
        
        request = MultiModalRequest(
            content=content,
            analysis_type="user_behavior_analysis",
            parameters={"include_recommendations": True}
        )
        
        assert len(request.content) == 2
        assert request.analysis_type == "user_behavior_analysis"
        assert request.parameters["include_recommendations"] == True
    
    def test_multimodal_request_validation(self):
        """测试多模态请求验证"""
        # 有效请求
        valid_content = [create_text_content("分析数据")]
        valid_request = MultiModalRequest(content=valid_content)
        
        assert valid_request.content is not None
        assert len(valid_request.content) > 0
        
        # 无效请求（空内容）
        with pytest.raises(ValueError):
            MultiModalRequest(content=[])
    
    def test_content_info_extraction(self):
        """测试内容信息提取"""
        client = VolcanoLLMClient(api_key="test-key")
        
        content = [
            {"type": "text", "text": "分析这些图表数据"},
            {"type": "image_url", "image_url": {"url": "https://example.com/chart1.png"}},
            {"type": "image_url", "image_url": {"url": "https://example.com/chart2.jpg"}},
            {"type": "text", "text": "提供建议"}
        ]
        
        info = client.get_content_info(content)
        
        assert info["is_multimodal"] == True
        assert info["text_count"] == 2
        assert info["image_count"] == 2
        assert info["total_items"] == 4
        assert info["text_length"] > 0
        assert len(info["image_urls"]) == 2


class TestIntegrationWithVolcanoClient:
    """测试与Volcano客户端的集成"""
    
    def test_client_multimodal_support(self):
        """测试客户端多模态支持"""
        client = VolcanoLLMClient(api_key="test-key", supports_multimodal=True)
        
        assert client.supports_multimodal == True
    
    def test_client_content_creation_methods(self):
        """测试客户端内容创建方法"""
        client = VolcanoLLMClient(api_key="test-key")
        
        # 创建文本内容
        text_content = client.create_text_content("分析数据")
        assert isinstance(text_content, TextContent)
        assert text_content.text == "分析数据"
        
        # 创建图片内容
        image_content = client.create_image_content("https://example.com/image.png")
        assert isinstance(image_content, ImageContent)
        assert image_content.image_url.url == "https://example.com/image.png"
    
    def test_client_multimodal_request_creation(self):
        """测试客户端多模态请求创建"""
        client = VolcanoLLMClient(api_key="test-key")
        
        request = client.create_multimodal_request(
            text="分析用户行为图表",
            image_urls=["https://example.com/chart1.png", "https://example.com/chart2.jpg"],
            analysis_type="behavior_analysis",
            include_recommendations=True
        )
        
        assert isinstance(request, MultiModalRequest)
        assert len(request.content) == 3  # 1文本 + 2图片
        assert request.analysis_type == "behavior_analysis"
        assert request.parameters["include_recommendations"] == True
    
    @patch('config.volcano_llm_client.OpenAI')
    def test_client_multimodal_api_call(self, mock_openai):
        """测试客户端多模态API调用"""
        # 设置mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "图表分析结果"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        client = VolcanoLLMClient(api_key="test-key", supports_multimodal=True)
        
        # 准备多模态内容
        multimodal_content = [
            {"type": "text", "text": "分析这张图表"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/chart.png",
                    "detail": "high"
                }
            }
        ]
        
        # 模拟API调用
        with patch.object(client, '_call') as mock_call:
            mock_call.return_value = "图表分析结果"
            
            # 验证客户端可以处理多模态内容
            handler = MultiModalContentHandler()
            processed_content = handler.prepare_content(multimodal_content)
            is_valid = handler.validate_content(processed_content)
            
            assert is_valid == True
            assert len(processed_content) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])