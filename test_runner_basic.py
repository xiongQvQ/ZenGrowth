#!/usr/bin/env python3
"""
基础测试运行器 - 验证测试文件的基本功能
"""

import sys
import os
sys.path.append('.')

def test_volcano_client_basic():
    """测试Volcano客户端基础功能"""
    print("=== 测试Volcano客户端基础功能 ===")
    
    try:
        from config.volcano_llm_client import VolcanoLLMClient, VolcanoAPIException, VolcanoErrorType
        print("✓ 成功导入Volcano客户端类")
        
        # 测试异常类
        exception = VolcanoAPIException(
            message="Test error",
            error_type=VolcanoErrorType.API_CONNECTION_ERROR
        )
        assert exception.error_type == VolcanoErrorType.API_CONNECTION_ERROR
        print("✓ 异常类工作正常")
        
        # 测试客户端创建（使用测试密钥）
        os.environ["ARK_API_KEY"] = "test-key-for-validation"
        try:
            client = VolcanoLLMClient(api_key="test-key")
            print("✓ 客户端创建成功")
            
            # 测试基本属性
            assert client.supports_multimodal == True
            print("✓ 多模态支持检测正常")
            
        except Exception as e:
            print(f"⚠ 客户端创建失败（预期的，因为没有真实API密钥）: {e}")
        
    except Exception as e:
        print(f"❌ 基础测试失败: {e}")
        return False
    
    return True

def test_multimodal_handler_basic():
    """测试多模态处理器基础功能"""
    print("\n=== 测试多模态处理器基础功能 ===")
    
    try:
        from config.multimodal_content_handler import (
            MultiModalContentHandler,
            TextContent,
            ImageContent,
            create_text_content,
            create_image_content
        )
        print("✓ 成功导入多模态处理器类")
        
        # 测试内容创建
        text_content = create_text_content("测试文本")
        assert text_content.type == "text"
        assert text_content.text == "测试文本"
        print("✓ 文本内容创建正常")
        
        image_content = create_image_content("https://example.com/test.png")
        assert image_content.type == "image_url"
        assert image_content.image_url.url == "https://example.com/test.png"
        print("✓ 图片内容创建正常")
        
        # 测试处理器
        handler = MultiModalContentHandler()
        
        # 测试URL验证
        valid_url = "https://example.com/image.png"
        assert handler.validate_image_url(valid_url) == True
        print("✓ 有效URL验证正常")
        
        invalid_url = "not-a-url"
        assert handler.validate_image_url(invalid_url) == False
        print("✓ 无效URL验证正常")
        
        # 测试内容准备
        content = handler.prepare_content("测试文本")
        assert len(content) == 1
        assert content[0]["type"] == "text"
        print("✓ 内容准备功能正常")
        
    except Exception as e:
        print(f"❌ 多模态处理器测试失败: {e}")
        return False
    
    return True

def test_provider_manager_basic():
    """测试提供商管理器基础功能"""
    print("\n=== 测试提供商管理器基础功能 ===")
    
    try:
        from config.llm_provider_manager import (
            ProviderStatus,
            HealthCheckResult,
            ProviderMetrics
        )
        print("✓ 成功导入提供商管理器类")
        
        # 测试健康检查结果
        health_result = HealthCheckResult(
            provider="test",
            status=ProviderStatus.AVAILABLE,
            response_time=0.5
        )
        assert health_result.provider == "test"
        assert health_result.status == "available"
        print("✓ 健康检查结果创建正常")
        
        # 测试指标
        metrics = ProviderMetrics()
        metrics.record_success(0.5)
        assert metrics.success_rate == 1.0
        print("✓ 提供商指标功能正常")
        
        # 尝试创建管理器（可能失败）
        try:
            from config.llm_provider_manager import LLMProviderManager
            manager = LLMProviderManager()
            print("✓ 提供商管理器创建正常")
        except Exception as e:
            print(f"⚠ 提供商管理器创建失败（可能需要配置）: {e}")
        
    except Exception as e:
        print(f"❌ 提供商管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """运行所有基础测试"""
    print("开始运行基础测试...")
    
    tests = [
        test_volcano_client_basic,
        test_multimodal_handler_basic,
        test_provider_manager_basic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print(f"\n{'='*50}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有基础测试通过！")
        return True
    else:
        print("⚠ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)