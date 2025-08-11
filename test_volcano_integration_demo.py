#!/usr/bin/env python3
"""
Volcano LLM客户端集成演示
演示错误处理和重试逻辑在实际客户端中的集成
"""

import logging
import time
import os
from unittest.mock import Mock, patch

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_error_handling_integration():
    """演示错误处理集成功能"""
    print("演示Volcano LLM客户端错误处理集成...")
    
    try:
        # 设置模拟环境变量
        os.environ["ARK_API_KEY"] = "test_api_key_for_demo"
        
        # 导入客户端（需要在设置环境变量后）
        from config.volcano_llm_client import (
            create_volcano_llm_with_custom_retry,
            VolcanoAPIException,
            VolcanoErrorType
        )
        
        # 创建带有自定义重试配置的客户端
        client = create_volcano_llm_with_custom_retry(
            max_retries=2,
            base_delay=0.1,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )
        
        print("✓ 客户端创建成功")
        print(f"  模型: {client.model}")
        print(f"  最大重试次数: {client.max_retries}")
        print(f"  基础延迟: {client.base_delay}s")
        print(f"  支持多模态: {client.supports_multimodal}")
        
        # 获取模型信息
        model_info = client.get_model_info()
        print(f"\n模型信息:")
        print(f"  提供商: {model_info['provider']}")
        print(f"  模型名称: {model_info['model']}")
        print(f"  多模态功能: {model_info['multimodal_features']}")
        
        # 获取初始错误统计
        initial_stats = client.get_error_statistics()
        print(f"\n初始错误统计: {initial_stats['error_counts']}")
        
        # 演示重试配置更新
        print("\n演示重试配置更新...")
        client.update_retry_config(max_retries=5, base_delay=2.0)
        print("✓ 重试配置更新成功")
        
        # 重置错误统计
        client.reset_error_statistics()
        print("✓ 错误统计重置成功")
        
        # 获取健康状态（这会尝试连接，但由于是测试环境会失败）
        print("\n获取健康状态...")
        health_status = client.get_health_status()
        print(f"  状态: {health_status['status']}")
        print(f"  健康分数: {health_status['health_score']}")
        print(f"  连接测试成功: {health_status['connection_test']['success']}")
        if health_status['recommendations']:
            print(f"  建议: {health_status['recommendations'][:2]}")  # 显示前两个建议
        
        # 获取更新后的错误统计
        final_stats = client.get_error_statistics()
        print(f"\n最终错误统计: {final_stats['error_counts']}")
        
        print("\n✅ 错误处理集成演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理环境变量
        if "ARK_API_KEY" in os.environ:
            del os.environ["ARK_API_KEY"]


def demo_multimodal_content_handling():
    """演示多模态内容处理"""
    print("\n演示多模态内容处理...")
    
    try:
        # 设置模拟环境变量
        os.environ["ARK_API_KEY"] = "test_api_key_for_demo"
        
        from config.volcano_llm_client import (
            create_volcano_llm,
            create_text_content,
            create_image_content,
            create_multimodal_content
        )
        
        # 创建客户端
        client = create_volcano_llm()
        
        # 演示内容创建
        print("创建多模态内容...")
        
        # 创建文本内容
        text_content = create_text_content("分析这张图片中的内容")
        print(f"  文本内容: {text_content.text[:30]}...")
        
        # 创建图片内容（使用示例URL）
        image_url = "https://example.com/image.jpg"
        try:
            image_content = create_image_content(image_url, detail="high")
            print(f"  图片内容: {image_content.image_url.url}")
            print(f"  图片详细程度: {image_content.image_url.detail}")
        except ValueError as e:
            print(f"  图片内容创建失败（预期）: {e}")
        
        # 创建混合内容
        multimodal_content = create_multimodal_content(
            text="请分析这些图片",
            image_urls=["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
        )
        print(f"  混合内容项数: {len(multimodal_content)}")
        
        # 演示内容验证
        print("\n内容验证演示...")
        
        # 验证简单文本
        simple_content = "这是一个简单的文本内容"
        content_info = client.get_content_info(simple_content)
        print(f"  简单文本: {content_info}")
        
        # 验证多模态内容
        complex_content = [
            {"type": "text", "text": "分析图片"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,invalid_base64"}}
        ]
        content_info = client.get_content_info(complex_content)
        print(f"  多模态内容: {content_info}")
        
        # 演示内容验证
        validation_result = client.validate_multimodal_request(complex_content)
        print(f"  验证结果: 有效={validation_result['is_valid']}")
        if not validation_result['is_valid']:
            print(f"  验证错误: {validation_result.get('error', '未知错误')}")
        
        print("\n✅ 多模态内容处理演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理环境变量
        if "ARK_API_KEY" in os.environ:
            del os.environ["ARK_API_KEY"]


def demo_error_scenarios():
    """演示各种错误场景的处理"""
    print("\n演示错误场景处理...")
    
    try:
        from config.volcano_llm_client import (
            ErrorHandler,
            RetryConfig,
            VolcanoErrorType,
            VolcanoAPIException
        )
        
        # 创建错误处理器
        retry_config = RetryConfig(
            max_retries=3,
            base_delay=0.5,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )
        error_handler = ErrorHandler(retry_config)
        
        # 模拟各种错误场景
        error_scenarios = [
            ("API rate limit exceeded", "速率限制"),
            ("Authentication failed: invalid API key", "认证失败"),
            ("Connection timeout after 30 seconds", "连接超时"),
            ("Model is currently overloaded", "模型过载"),
            ("Content filter: inappropriate content detected", "内容过滤"),
            ("Quota exceeded for this month", "配额超限"),
            ("Invalid request: missing required parameter", "无效请求"),
            ("Network connection failed", "网络错误"),
            ("Unknown server error occurred", "未知错误")
        ]
        
        print("错误场景处理演示:")
        for error_msg, description in error_scenarios:
            print(f"\n  场景: {description}")
            print(f"  错误: {error_msg}")
            
            # 创建错误
            error = Exception(error_msg)
            
            # 分类错误
            error_type = error_handler.classify_error(error)
            print(f"  分类: {error_type.value}")
            
            # 判断重试
            should_retry = error_handler.should_retry(error_type, 0)
            print(f"  重试: {'是' if should_retry else '否'}")
            
            if should_retry:
                # 计算延迟
                delay = error_handler.calculate_delay(0, error_type)
                print(f"  延迟: {delay:.1f}s")
                
                # 模拟重试过程
                for attempt in range(retry_config.max_retries):
                    will_retry = error_handler.should_retry(error_type, attempt + 1)
                    if not will_retry:
                        print(f"  最大重试次数: {attempt + 1}")
                        break
            
            # 创建异常
            volcano_exception = error_handler.create_exception(error, error_type)
            
            # 记录错误（不重试，避免日志过多）
            error_handler.log_error(volcano_exception, 1, False)
        
        # 显示最终统计
        stats = error_handler.get_error_stats()
        print(f"\n错误统计汇总:")
        for error_type, count in stats["error_counts"].items():
            print(f"  {error_type}: {count} 次")
        
        print("\n✅ 错误场景处理演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 Volcano LLM客户端错误处理集成演示")
    print("=" * 50)
    
    demos = [
        ("错误处理集成", demo_error_handling_integration),
        ("多模态内容处理", demo_multimodal_content_handling),
        ("错误场景处理", demo_error_scenarios),
    ]
    
    success_count = 0
    
    for name, demo_func in demos:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            if demo_func():
                success_count += 1
                print(f"✅ {name}演示成功")
            else:
                print(f"❌ {name}演示失败")
        except Exception as e:
            print(f"❌ {name}演示异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"演示结果: {success_count}/{len(demos)} 成功")
    
    if success_count == len(demos):
        print("\n🎉 所有演示成功完成！")
        print("\nVolcano LLM客户端错误处理功能包括:")
        print("  ✓ 智能错误分类和识别")
        print("  ✓ 可配置的重试策略")
        print("  ✓ 指数退避延迟算法")
        print("  ✓ 详细的错误日志记录")
        print("  ✓ 错误统计和监控")
        print("  ✓ 健康状态检查")
        print("  ✓ 多模态内容处理")
        print("  ✓ 内容验证和回退机制")
        return True
    else:
        print("\n💥 部分演示失败")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)