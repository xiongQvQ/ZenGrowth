#!/usr/bin/env python3
"""
多模态内容处理器测试
测试MultiModalContentHandler的各项功能
"""

import sys
import os
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


def test_multimodal_content_handler_initialization():
    """测试多模态内容处理器初始化"""
    print("=== 测试多模态内容处理器初始化 ===")
    
    # 默认初始化
    handler = MultiModalContentHandler()
    assert handler.max_image_size_mb == 10
    assert handler.max_images_per_request == 10
    assert len(handler.supported_image_formats) > 0
    print("✓ 默认初始化成功")
    
    # 自定义参数初始化
    handler_custom = MultiModalContentHandler(max_image_size_mb=20)
    assert handler_custom.max_image_size_mb == 20
    print("✓ 自定义参数初始化成功")


def test_prepare_content():
    """测试内容准备功能"""
    print("\n=== 测试内容准备功能 ===")
    
    handler = MultiModalContentHandler()
    
    # 测试1: 纯文本内容
    print("\n1. 测试纯文本内容")
    text_input = "这是一段测试文本"
    processed = handler.prepare_content(text_input)
    expected = [{"type": "text", "text": "这是一段测试文本"}]
    assert processed == expected
    print(f"输入: {text_input}")
    print(f"处理后: {processed}")
    print("✓ 纯文本内容处理成功")
    
    # 测试2: 字典格式的多模态内容
    print("\n2. 测试字典格式的多模态内容")
    dict_input = [
        {"type": "text", "text": "请分析这张图片"},
        {
            "type": "image_url",
            "image_url": {
                "url": "https://example.com/image.jpg",
                "detail": "high"
            }
        }
    ]
    processed = handler.prepare_content(dict_input)
    assert len(processed) == 2
    assert processed[0]["type"] == "text"
    assert processed[1]["type"] == "image_url"
    print(f"输入: {dict_input}")
    print(f"处理后: {processed}")
    print("✓ 字典格式多模态内容处理成功")
    
    # 测试3: Pydantic模型内容
    print("\n3. 测试Pydantic模型内容")
    model_input = [
        create_text_content("分析图片内容"),
        create_image_content("https://example.com/test.png", "auto")
    ]
    processed = handler.prepare_content(model_input)
    assert len(processed) == 2
    assert processed[0]["type"] == "text"
    assert processed[1]["type"] == "image_url"
    print(f"输入: {model_input}")
    print(f"处理后: {processed}")
    print("✓ Pydantic模型内容处理成功")


def test_image_url_validation():
    """测试图片URL验证"""
    print("\n=== 测试图片URL验证 ===")
    
    handler = MultiModalContentHandler()
    
    # 有效的HTTP/HTTPS URL
    valid_urls = [
        "https://example.com/image.jpg",
        "http://test.com/photo.png",
        "https://cdn.example.com/assets/image.jpeg",
        "https://example.com/path/to/image.webp"
    ]
    
    # 无效的URL
    invalid_urls = [
        "",  # 空URL
        "not-a-url",  # 不是URL格式
        "ftp://example.com/image.jpg",  # 不支持的协议
        "https://",  # 不完整的URL
        "data:text/plain;base64,SGVsbG8="  # 非图片data URL
    ]
    
    print("\n测试有效URL:")
    for url in valid_urls:
        result = handler.validate_image_url(url)
        print(f"  {url}: {'✓' if result else '✗'}")
        assert result, f"应该验证通过: {url}"
    
    print("\n测试无效URL:")
    for url in invalid_urls:
        result = handler.validate_image_url(url)
        print(f"  {url}: {'✓' if not result else '✗'}")
        assert not result, f"应该验证失败: {url}"
    
    print("✓ 图片URL验证测试通过")


def test_data_url_validation():
    """测试Data URL验证"""
    print("\n=== 测试Data URL验证 ===")
    
    handler = MultiModalContentHandler()
    
    # 有效的Data URL (使用简单的base64数据)
    valid_data_urls = [
        "data:image/jpeg;base64,SGVsbG8gV29ybGQ=",  # "Hello World" 作为测试数据
        "data:image/png;base64,VGVzdCBEYXRh"  # "Test Data" 作为测试数据
    ]
    
    # 无效的Data URL
    invalid_data_urls = [
        "data:image/jpeg;base64,invalid_base64",  # 无效base64
        "data:text/plain;base64,SGVsbG8=",  # 非图片类型
        "data:image/unsupported;base64,SGVsbG8=",  # 不支持的图片格式
        "data:image/jpeg;base64,"  # 空base64数据
    ]
    
    print("\n测试有效Data URL:")
    for url in valid_data_urls:
        result = handler.validate_image_url(url)
        print(f"  {url[:50]}...: {'✓' if result else '✗'}")
        assert result, f"应该验证通过: {url[:50]}..."
    
    print("\n测试无效Data URL:")
    for url in invalid_data_urls:
        result = handler.validate_image_url(url)
        print(f"  {url[:50]}...: {'✓' if not result else '✗'}")
        assert not result, f"应该验证失败: {url[:50]}..."
    
    print("✓ Data URL验证测试通过")


def test_content_validation():
    """测试内容验证"""
    print("\n=== 测试内容验证 ===")
    
    handler = MultiModalContentHandler()
    
    # 有效内容
    valid_content = [
        {"type": "text", "text": "分析这张图片"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ]
    
    assert handler.validate_content(valid_content)
    print("✓ 有效内容验证通过")
    
    # 空内容
    empty_content = []
    assert not handler.validate_content(empty_content)
    print("✓ 空内容验证失败（符合预期）")
    
    # 无效图片URL的内容
    invalid_url_content = [
        {"type": "text", "text": "分析图片"},
        {"type": "image_url", "image_url": {"url": "invalid-url"}}
    ]
    
    assert not handler.validate_content(invalid_url_content)
    print("✓ 无效图片URL内容验证失败（符合预期）")
    
    # 不支持的内容类型
    unsupported_content = [
        {"type": "unsupported", "data": "some data"}
    ]
    
    assert not handler.validate_content(unsupported_content)
    print("✓ 不支持的内容类型验证失败（符合预期）")


def test_provider_formatting():
    """测试提供商格式化"""
    print("\n=== 测试提供商格式化 ===")
    
    handler = MultiModalContentHandler()
    
    content = [
        {"type": "text", "text": "测试文本"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg", "detail": "high"}}
    ]
    
    # 测试Volcano格式化
    volcano_formatted = handler.format_for_provider(content, "volcano")
    assert volcano_formatted == content  # Volcano使用标准格式
    print("✓ Volcano格式化测试通过")
    
    # 测试Google格式化
    google_formatted = handler.format_for_provider(content, "google")
    assert len(google_formatted) == 2
    assert google_formatted[0]["type"] == "text"
    assert google_formatted[1]["type"] == "image_url"
    print("✓ Google格式化测试通过")
    
    # 测试未知提供商
    unknown_formatted = handler.format_for_provider(content, "unknown")
    assert unknown_formatted == content  # 返回原格式
    print("✓ 未知提供商格式化测试通过")


def test_content_type_detection():
    """测试内容类型检测"""
    print("\n=== 测试内容类型检测 ===")
    
    handler = MultiModalContentHandler()
    
    # 纯文本
    text_only = "这是纯文本"
    assert handler.detect_content_type(text_only) == "text_only"
    print("✓ 纯文本类型检测正确")
    
    # 仅图片
    image_only = [
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ]
    assert handler.detect_content_type(image_only) == "image_only"
    print("✓ 仅图片类型检测正确")
    
    # 多模态
    multimodal = [
        {"type": "text", "text": "分析图片"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ]
    assert handler.detect_content_type(multimodal) == "multimodal"
    print("✓ 多模态类型检测正确")


def test_content_extraction():
    """测试内容提取"""
    print("\n=== 测试内容提取 ===")
    
    handler = MultiModalContentHandler()
    
    mixed_content = [
        {"type": "text", "text": "第一段文本"},
        {"type": "image_url", "image_url": {"url": "https://example.com/img1.png"}},
        {"type": "text", "text": "第二段文本"},
        {"type": "image_url", "image_url": {"url": "https://example.com/img2.jpg"}}
    ]
    
    # 提取文本内容
    text_content = handler.extract_text_content(mixed_content)
    expected_text = "第一段文本\n第二段文本"
    assert text_content == expected_text
    print(f"提取的文本: {text_content}")
    print("✓ 文本内容提取正确")
    
    # 提取图片URL
    image_urls = handler.get_image_urls(mixed_content)
    expected_urls = ["https://example.com/img1.png", "https://example.com/img2.jpg"]
    assert image_urls == expected_urls
    print(f"提取的图片URL: {image_urls}")
    print("✓ 图片URL提取正确")


def test_content_statistics():
    """测试内容统计"""
    print("\n=== 测试内容统计 ===")
    
    handler = MultiModalContentHandler()
    
    content = [
        {"type": "text", "text": "这是测试文本"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image1.jpg"}},
        {"type": "image_url", "image_url": {"url": "https://example.com/image2.png"}}
    ]
    
    stats = handler.get_content_statistics(content)
    
    assert stats["total_items"] == 3
    assert stats["text_items"] == 1
    assert stats["image_items"] == 2
    assert stats["has_multimodal"] == True
    assert len(stats["image_urls"]) == 2
    assert stats["estimated_tokens"] > 0
    
    print(f"统计信息: {stats}")
    print("✓ 内容统计测试通过")


def test_content_structure_validation():
    """测试内容结构验证"""
    print("\n=== 测试内容结构验证 ===")
    
    handler = MultiModalContentHandler()
    
    # 有效结构
    valid_structure = [
        {"type": "text", "text": "有效文本"},
        {"type": "image_url", "image_url": {"url": "https://example.com/valid.jpg"}}
    ]
    
    validation_result = handler.validate_content_structure(valid_structure)
    assert validation_result["is_valid"] == True
    assert len(validation_result["errors"]) == 0
    print("✓ 有效结构验证通过")
    
    # 无效结构
    invalid_structure = [
        {"type": "text", "text": ""},  # 空文本
        {"type": "image_url", "image_url": {"url": ""}}  # 空URL
    ]
    
    validation_result = handler.validate_content_structure(invalid_structure)
    assert validation_result["is_valid"] == False
    assert len(validation_result["errors"]) > 0
    print(f"无效结构验证结果: {validation_result}")
    print("✓ 无效结构验证失败（符合预期）")


def test_content_normalization():
    """测试内容标准化"""
    print("\n=== 测试内容标准化 ===")
    
    handler = MultiModalContentHandler()
    
    # 需要标准化的内容
    raw_content = [
        {"type": "text", "text": "  带空格的文本  "},
        {"type": "image_url", "image_url": {"url": "  https://example.com/image.jpg  ", "detail": "invalid_detail"}}
    ]
    
    normalized = handler.normalize_content(raw_content)
    
    assert normalized[0]["text"] == "带空格的文本"  # 去除空格
    assert normalized[1]["image_url"]["url"] == "https://example.com/image.jpg"  # 去除空格
    assert normalized[1]["image_url"]["detail"] == "auto"  # 修正无效detail
    
    print(f"原始内容: {raw_content}")
    print(f"标准化后: {normalized}")
    print("✓ 内容标准化测试通过")


def test_multimodal_request_creation():
    """测试多模态请求创建"""
    print("\n=== 测试多模态请求创建 ===")
    
    handler = MultiModalContentHandler()
    
    # 创建多模态请求
    request = handler.create_multimodal_request(
        text="请分析这些图片",
        image_urls=["https://example.com/img1.jpg", "https://example.com/img2.png"],
        analysis_type="visual_analysis",
        provider="volcano",
        include_details=True
    )
    
    assert isinstance(request, MultiModalRequest)
    assert len(request.content) == 3  # 1个文本 + 2个图片
    assert request.analysis_type == "visual_analysis"
    assert request.provider == "volcano"
    assert request.parameters["include_details"] == True
    
    print(f"创建的请求: {request}")
    print("✓ 多模态请求创建测试通过")


def test_convenience_functions():
    """测试便利函数"""
    print("\n=== 测试便利函数 ===")
    
    # 测试create_text_content
    text_content = create_text_content("测试文本")
    assert isinstance(text_content, TextContent)
    assert text_content.type == "text"
    assert text_content.text == "测试文本"
    print("✓ create_text_content测试通过")
    
    # 测试create_image_content
    image_content = create_image_content("https://example.com/image.jpg", "high")
    assert isinstance(image_content, ImageContent)
    assert image_content.type == "image_url"
    assert image_content.image_url.url == "https://example.com/image.jpg"
    assert image_content.image_url.detail == "high"
    print("✓ create_image_content测试通过")
    
    # 测试create_multimodal_content
    multimodal_content = create_multimodal_content(
        "分析图片",
        ["https://example.com/img1.jpg", "https://example.com/img2.png"]
    )
    assert len(multimodal_content) == 3  # 1个文本 + 2个图片
    assert isinstance(multimodal_content[0], TextContent)
    assert isinstance(multimodal_content[1], ImageContent)
    assert isinstance(multimodal_content[2], ImageContent)
    print("✓ create_multimodal_content测试通过")


def run_all_tests():
    """运行所有测试"""
    print("开始运行多模态内容处理器测试...")
    
    try:
        test_multimodal_content_handler_initialization()
        test_prepare_content()
        test_image_url_validation()
        test_data_url_validation()
        test_content_validation()
        test_provider_formatting()
        test_content_type_detection()
        test_content_extraction()
        test_content_statistics()
        test_content_structure_validation()
        test_content_normalization()
        test_multimodal_request_creation()
        test_convenience_functions()
        
        print("\n" + "="*50)
        print("🎉 所有测试通过！多模态内容处理器功能正常")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)