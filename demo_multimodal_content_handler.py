#!/usr/bin/env python3
"""
多模态内容处理器演示
展示如何使用MultiModalContentHandler处理文本和图片内容
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.multimodal_content_handler import (
    MultiModalContentHandler,
    create_text_content,
    create_image_content,
    create_multimodal_content
)


def demo_basic_usage():
    """演示基本用法"""
    print("=== 多模态内容处理器基本用法演示 ===")
    
    # 创建处理器实例
    handler = MultiModalContentHandler(max_image_size_mb=10)
    
    # 1. 处理纯文本内容
    print("\n1. 处理纯文本内容")
    text_input = "请分析用户行为数据"
    processed_text = handler.prepare_content(text_input)
    print(f"输入: {text_input}")
    print(f"处理后: {processed_text}")
    
    # 2. 处理多模态内容
    print("\n2. 处理多模态内容")
    multimodal_input = [
        {"type": "text", "text": "请分析这些用户界面截图"},
        {"type": "image_url", "image_url": {"url": "https://example.com/ui_screenshot1.png", "detail": "high"}},
        {"type": "image_url", "image_url": {"url": "https://example.com/ui_screenshot2.png", "detail": "high"}}
    ]
    
    processed_multimodal = handler.prepare_content(multimodal_input)
    print(f"输入项数: {len(multimodal_input)}")
    print(f"处理后项数: {len(processed_multimodal)}")
    
    # 验证内容
    is_valid = handler.validate_content(processed_multimodal)
    print(f"内容验证结果: {'✓ 有效' if is_valid else '✗ 无效'}")


def demo_provider_formatting():
    """演示提供商格式化"""
    print("\n=== 提供商格式化演示 ===")
    
    handler = MultiModalContentHandler()
    
    # 创建标准内容
    content = [
        {"type": "text", "text": "分析用户转化漏斗"},
        {"type": "image_url", "image_url": {"url": "https://example.com/funnel_chart.png", "detail": "high"}}
    ]
    
    # 为不同提供商格式化
    print("\n为Volcano提供商格式化:")
    volcano_content = handler.format_for_provider(content, "volcano")
    print(f"Volcano格式: {volcano_content}")
    
    print("\n为Google提供商格式化:")
    google_content = handler.format_for_provider(content, "google")
    print(f"Google格式: {google_content}")


def demo_content_analysis():
    """演示内容分析功能"""
    print("\n=== 内容分析功能演示 ===")
    
    handler = MultiModalContentHandler()
    
    # 创建混合内容
    mixed_content = [
        {"type": "text", "text": "用户行为分析报告"},
        {"type": "image_url", "image_url": {"url": "https://example.com/chart1.png"}},
        {"type": "text", "text": "关键指标趋势"},
        {"type": "image_url", "image_url": {"url": "https://example.com/chart2.jpg"}},
        {"type": "text", "text": "建议和结论"}
    ]
    
    # 内容类型检测
    content_type = handler.detect_content_type(mixed_content)
    print(f"内容类型: {content_type}")
    
    # 提取文本内容
    text_content = handler.extract_text_content(mixed_content)
    print(f"提取的文本:\n{text_content}")
    
    # 提取图片URL
    image_urls = handler.get_image_urls(mixed_content)
    print(f"提取的图片URL: {image_urls}")
    
    # 获取统计信息
    stats = handler.get_content_statistics(mixed_content)
    print(f"内容统计: {stats}")


def demo_validation_features():
    """演示验证功能"""
    print("\n=== 验证功能演示 ===")
    
    handler = MultiModalContentHandler()
    
    # 测试URL验证
    test_urls = [
        "https://example.com/valid_image.jpg",
        "http://test.com/photo.png",
        "invalid-url",
        "data:image/jpeg;base64,SGVsbG8gV29ybGQ=",
        ""
    ]
    
    print("URL验证结果:")
    for url in test_urls:
        is_valid = handler.validate_image_url(url)
        status = "✓" if is_valid else "✗"
        print(f"  {status} {url if url else '(空URL)'}")
    
    # 测试内容结构验证
    print("\n内容结构验证:")
    test_content = [
        {"type": "text", "text": "有效文本"},
        {"type": "image_url", "image_url": {"url": "https://example.com/valid.jpg"}},
        {"type": "image_url", "image_url": {"url": ""}}  # 无效URL
    ]
    
    validation_result = handler.validate_content_structure(test_content)
    print(f"验证结果: {'✓ 有效' if validation_result['is_valid'] else '✗ 无效'}")
    if validation_result['errors']:
        print(f"错误: {validation_result['errors']}")
    if validation_result['warnings']:
        print(f"警告: {validation_result['warnings']}")


def demo_convenience_functions():
    """演示便利函数"""
    print("\n=== 便利函数演示 ===")
    
    # 创建文本内容
    text_content = create_text_content("分析用户留存率")
    print(f"文本内容: {text_content}")
    
    # 创建图片内容
    image_content = create_image_content("https://example.com/retention_chart.png", "high")
    print(f"图片内容: {image_content}")
    
    # 创建混合内容
    multimodal_content = create_multimodal_content(
        "请分析这些用户行为图表",
        ["https://example.com/chart1.png", "https://example.com/chart2.jpg"]
    )
    print(f"混合内容项数: {len(multimodal_content)}")
    for i, item in enumerate(multimodal_content):
        print(f"  项 {i+1}: {item.type}")


def demo_multimodal_request():
    """演示多模态请求创建"""
    print("\n=== 多模态请求创建演示 ===")
    
    handler = MultiModalContentHandler()
    
    # 创建分析请求
    request = handler.create_multimodal_request(
        text="请分析这些用户界面截图，识别可能的用户体验问题",
        image_urls=[
            "https://example.com/ui_screenshot1.png",
            "https://example.com/ui_screenshot2.png"
        ],
        analysis_type="ux_analysis",
        provider="volcano",
        include_recommendations=True,
        focus_areas=["navigation", "conversion", "accessibility"]
    )
    
    print(f"请求类型: {request.analysis_type}")
    print(f"目标提供商: {request.provider}")
    print(f"内容项数: {len(request.content)}")
    print(f"参数: {request.parameters}")


def main():
    """主函数"""
    print("多模态内容处理器功能演示")
    print("="*50)
    
    try:
        demo_basic_usage()
        demo_provider_formatting()
        demo_content_analysis()
        demo_validation_features()
        demo_convenience_functions()
        demo_multimodal_request()
        
        print("\n" + "="*50)
        print("🎉 演示完成！多模态内容处理器功能正常")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()