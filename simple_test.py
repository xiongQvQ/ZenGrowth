#!/usr/bin/env python3
"""
简单的提供商测试脚本
"""

import traceback
from config.llm_provider_manager import ProviderStatus, HealthCheckResult

def test_enum():
    """测试枚举"""
    print("=== 测试枚举 ===")
    try:
        status = ProviderStatus.AVAILABLE
        print(f"状态: {status}")
        print(f"状态值: {status.value}")
        print(f"状态类型: {type(status)}")
        
        # 测试 HealthCheckResult
        result = HealthCheckResult(
            provider="test",
            status=ProviderStatus.AVAILABLE
        )
        print(f"结果状态: {result.status}")
        print(f"结果状态值: {result.status.value}")
        
    except Exception as e:
        print(f"枚举测试失败: {e}")
        traceback.print_exc()
    print()

def test_google_llm():
    """测试 Google LLM"""
    print("=== 测试 Google LLM ===")
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from config.settings import settings
        
        llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        print("Google LLM 创建成功")
        
        # 测试调用
        response = llm.invoke("Hello, this is a test.")
        print(f"响应: {str(response)[:100]}...")
        print("Google LLM 调用成功")
        
    except Exception as e:
        print(f"Google LLM 测试失败: {e}")
        traceback.print_exc()
    print()

def test_volcano_llm():
    """测试 Volcano LLM"""
    print("=== 测试 Volcano LLM ===")
    try:
        from config.volcano_llm_client_monitored import MonitoredVolcanoLLMClient
        from config.settings import settings
        
        llm = MonitoredVolcanoLLMClient(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
            model=settings.ark_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        print("Volcano LLM 创建成功")
        
        # 测试调用
        response = llm.invoke("Hello, this is a test.")
        print(f"响应: {str(response)[:100]}...")
        print("Volcano LLM 调用成功")
        
    except Exception as e:
        print(f"Volcano LLM 测试失败: {e}")
        traceback.print_exc()
    print()

def main():
    """主函数"""
    print("简单提供商测试")
    print("=" * 30)
    
    test_enum()
    test_google_llm()
    test_volcano_llm()
    
    print("测试完成")

if __name__ == "__main__":
    main()