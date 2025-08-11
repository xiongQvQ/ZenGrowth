#!/usr/bin/env python3
"""
多模态内容处理器集成示例
展示如何在不同LLM提供商中使用MultiModalContentHandler
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.multimodal_content_handler import MultiModalContentHandler
from config.settings import settings


class MockLLMProvider:
    """模拟LLM提供商基类"""
    
    def __init__(self, provider_name: str, content_handler: MultiModalContentHandler):
        self.provider_name = provider_name
        self.content_handler = content_handler
    
    def process_content(self, content, **kwargs):
        """处理内容的通用方法"""
        # 准备内容
        processed_content = self.content_handler.prepare_content(content)
        
        # 验证内容
        if not self.content_handler.validate_content(processed_content):
            raise ValueError(f"内容验证失败 - {self.provider_name}")
        
        # 为特定提供商格式化
        formatted_content = self.content_handler.format_for_provider(
            processed_content, 
            self.provider_name.lower()
        )
        
        # 模拟API调用
        return self._mock_api_call(formatted_content, **kwargs)
    
    def _mock_api_call(self, content, **kwargs):
        """模拟API调用"""
        content_stats = self.content_handler.get_content_statistics(content)
        
        return {
            "provider": self.provider_name,
            "content_type": self.content_handler.detect_content_type(content),
            "processed_items": len(content),
            "estimated_tokens": content_stats["estimated_tokens"],
            "has_images": content_stats["has_multimodal"],
            "mock_response": f"[{self.provider_name}] 分析完成，发现了有趣的用户行为模式。"
        }


class VolcanoProvider(MockLLMProvider):
    """Volcano提供商实现"""
    
    def __init__(self, content_handler: MultiModalContentHandler):
        super().__init__("Volcano", content_handler)
    
    def _mock_api_call(self, content, **kwargs):
        """Volcano特定的API调用逻辑"""
        result = super()._mock_api_call(content, **kwargs)
        result["supports_multimodal"] = True
        result["model"] = "doubao-seed-1-6-250615"
        return result


class GoogleProvider(MockLLMProvider):
    """Google提供商实现"""
    
    def __init__(self, content_handler: MultiModalContentHandler):
        super().__init__("Google", content_handler)
    
    def _mock_api_call(self, content, **kwargs):
        """Google特定的API调用逻辑"""
        result = super()._mock_api_call(content, **kwargs)
        result["supports_multimodal"] = False  # 假设Google版本不支持多模态
        result["model"] = "gemini-2.5-pro"
        return result


def demo_provider_integration():
    """演示提供商集成"""
    print("=== 多模态内容处理器提供商集成演示 ===")
    
    # 创建共享的内容处理器
    content_handler = MultiModalContentHandler(max_image_size_mb=settings.max_image_size_mb)
    
    # 创建不同的提供商实例
    volcano_provider = VolcanoProvider(content_handler)
    google_provider = GoogleProvider(content_handler)
    
    # 测试内容
    test_content = [
        {"type": "text", "text": "请分析这些用户行为数据图表"},
        {"type": "image_url", "image_url": {"url": "https://example.com/user_behavior_chart.png", "detail": "high"}},
        {"type": "image_url", "image_url": {"url": "https://example.com/conversion_funnel.jpg", "detail": "auto"}}
    ]
    
    print(f"\n测试内容包含 {len(test_content)} 项")
    
    # 使用Volcano提供商处理
    print("\n--- 使用Volcano提供商 ---")
    try:
        volcano_result = volcano_provider.process_content(test_content)
        print(f"提供商: {volcano_result['provider']}")
        print(f"内容类型: {volcano_result['content_type']}")
        print(f"处理项数: {volcano_result['processed_items']}")
        print(f"预估tokens: {volcano_result['estimated_tokens']}")
        print(f"包含图片: {volcano_result['has_images']}")
        print(f"支持多模态: {volcano_result['supports_multimodal']}")
        print(f"模型: {volcano_result['model']}")
        print(f"响应: {volcano_result['mock_response']}")
    except Exception as e:
        print(f"Volcano处理失败: {e}")
    
    # 使用Google提供商处理
    print("\n--- 使用Google提供商 ---")
    try:
        google_result = google_provider.process_content(test_content)
        print(f"提供商: {google_result['provider']}")
        print(f"内容类型: {google_result['content_type']}")
        print(f"处理项数: {google_result['processed_items']}")
        print(f"预估tokens: {google_result['estimated_tokens']}")
        print(f"包含图片: {google_result['has_images']}")
        print(f"支持多模态: {google_result['supports_multimodal']}")
        print(f"模型: {google_result['model']}")
        print(f"响应: {google_result['mock_response']}")
    except Exception as e:
        print(f"Google处理失败: {e}")


def demo_fallback_scenario():
    """演示回退场景"""
    print("\n=== 回退场景演示 ===")
    
    content_handler = MultiModalContentHandler()
    
    # 创建包含无效图片的内容
    invalid_content = [
        {"type": "text", "text": "分析用户数据"},
        {"type": "image_url", "image_url": {"url": "invalid-url", "detail": "high"}}
    ]
    
    print("测试包含无效图片URL的内容...")
    
    # 尝试处理无效内容
    processed_content = content_handler.prepare_content(invalid_content)
    is_valid = content_handler.validate_content(processed_content)
    
    if not is_valid:
        print("❌ 多模态内容验证失败")
        
        # 回退到纯文本模式
        text_content = content_handler.extract_text_content(processed_content)
        if text_content:
            print(f"✓ 回退到纯文本模式: {text_content}")
            
            # 创建纯文本内容
            fallback_content = content_handler.prepare_content(text_content)
            fallback_valid = content_handler.validate_content(fallback_content)
            print(f"纯文本内容验证: {'✓ 有效' if fallback_valid else '✗ 无效'}")
        else:
            print("❌ 无法提取有效的文本内容")


def demo_content_preprocessing():
    """演示内容预处理"""
    print("\n=== 内容预处理演示 ===")
    
    content_handler = MultiModalContentHandler()
    
    # 原始内容（需要清理）
    raw_content = [
        {"type": "text", "text": "  请分析用户转化数据  "},  # 包含多余空格
        {"type": "image_url", "image_url": {"url": "  https://example.com/chart.png  ", "detail": "invalid_detail"}},  # URL有空格，detail无效
        {"type": "text", "text": ""},  # 空文本
    ]
    
    print("原始内容:")
    for i, item in enumerate(raw_content):
        print(f"  {i+1}. {item}")
    
    # 标准化内容
    normalized_content = content_handler.normalize_content(raw_content)
    
    print("\n标准化后:")
    for i, item in enumerate(normalized_content):
        print(f"  {i+1}. {item}")
    
    # 验证标准化后的内容
    validation_result = content_handler.validate_content_structure(normalized_content)
    print(f"\n验证结果: {'✓ 有效' if validation_result['is_valid'] else '✗ 无效'}")
    
    if validation_result['errors']:
        print(f"错误: {validation_result['errors']}")
    if validation_result['warnings']:
        print(f"警告: {validation_result['warnings']}")


def demo_batch_processing():
    """演示批量处理"""
    print("\n=== 批量处理演示 ===")
    
    content_handler = MultiModalContentHandler()
    
    # 批量请求
    batch_requests = [
        {
            "text": "分析用户注册流程",
            "image_urls": ["https://example.com/signup_flow.png"],
            "analysis_type": "ux_analysis"
        },
        {
            "text": "评估转化漏斗效果",
            "image_urls": ["https://example.com/funnel1.jpg", "https://example.com/funnel2.jpg"],
            "analysis_type": "conversion_analysis"
        },
        {
            "text": "用户留存趋势分析",
            "image_urls": [],  # 纯文本请求
            "analysis_type": "retention_analysis"
        }
    ]
    
    print(f"处理 {len(batch_requests)} 个批量请求...")
    
    for i, request in enumerate(batch_requests):
        print(f"\n--- 请求 {i+1} ---")
        try:
            # 创建多模态请求
            multimodal_request = content_handler.create_multimodal_request(
                text=request["text"],
                image_urls=request.get("image_urls", []),
                analysis_type=request["analysis_type"],
                provider="volcano"
            )
            
            print(f"分析类型: {multimodal_request.analysis_type}")
            print(f"内容项数: {len(multimodal_request.content)}")
            
            # 获取内容统计
            content_stats = content_handler.get_content_statistics(
                content_handler.prepare_content(multimodal_request.content)
            )
            print(f"内容类型: {content_stats['content_types']}")
            print(f"预估tokens: {content_stats['estimated_tokens']}")
            
        except Exception as e:
            print(f"请求 {i+1} 处理失败: {e}")


def main():
    """主函数"""
    print("多模态内容处理器集成示例")
    print("="*50)
    
    try:
        demo_provider_integration()
        demo_fallback_scenario()
        demo_content_preprocessing()
        demo_batch_processing()
        
        print("\n" + "="*50)
        print("🎉 集成示例演示完成！")
        print("MultiModalContentHandler 可以成功集成到不同的LLM提供商中")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()