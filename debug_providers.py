#!/usr/bin/env python3
"""
LLM提供商诊断脚本
用于诊断和修复提供商配置问题
"""

import sys
import traceback
from config.settings import settings, validate_config, get_available_providers
from config.llm_provider_manager import get_provider_manager
from config.crew_config import get_llm, get_available_providers as crew_get_providers

def test_basic_config():
    """测试基础配置"""
    print("=== 基础配置测试 ===")
    print(f"默认提供商: {settings.default_llm_provider}")
    print(f"启用的提供商: {settings.enabled_providers}")
    print(f"回退启用: {settings.enable_fallback}")
    print(f"回退顺序: {settings.fallback_order}")
    print(f"Google API Key: {'已设置' if settings.google_api_key else '未设置'}")
    print(f"Volcano API Key: {'已设置' if settings.ark_api_key else '未设置'}")
    print()

def test_config_validation():
    """测试配置验证"""
    print("=== 配置验证测试 ===")
    try:
        is_valid = validate_config()
        print(f"配置验证结果: {'通过' if is_valid else '失败'}")
        
        available = get_available_providers()
        print(f"可用提供商: {available}")
        
    except Exception as e:
        print(f"配置验证异常: {e}")
        traceback.print_exc()
    print()

def test_provider_manager():
    """测试提供商管理器"""
    print("=== 提供商管理器测试 ===")
    try:
        manager = get_provider_manager()
        print("提供商管理器创建成功")
        
        # 获取系统信息
        system_info = manager.get_system_info()
        print(f"总提供商数: {system_info['total_providers']}")
        print(f"可用提供商数: {system_info['available_providers']}")
        print(f"默认提供商: {system_info['default_provider']}")
        
        # 检查每个提供商的健康状态
        print("\n提供商健康检查:")
        health_results = manager.health_check_all()
        for provider, result in health_results.items():
            status = result.status if isinstance(result.status, str) else result.status.value
            print(f"  {provider}: {status}")
            if result.error_message:
                print(f"    错误: {result.error_message}")
        
    except Exception as e:
        print(f"提供商管理器测试失败: {e}")
        traceback.print_exc()
    print()

def test_crew_config():
    """测试 CrewAI 配置"""
    print("=== CrewAI 配置测试 ===")
    try:
        # 测试获取可用提供商
        providers = crew_get_providers()
        print(f"CrewAI 可用提供商: {providers}")
        
        # 测试获取默认 LLM
        print("测试获取默认 LLM...")
        llm = get_llm()
        print(f"默认 LLM 类型: {type(llm).__name__}")
        
        # 测试 Google LLM
        if "google" in providers:
            print("测试 Google LLM...")
            google_llm = get_llm(provider="google")
            print(f"Google LLM 类型: {type(google_llm).__name__}")
        
        # 测试 Volcano LLM
        if "volcano" in providers:
            print("测试 Volcano LLM...")
            volcano_llm = get_llm(provider="volcano")
            print(f"Volcano LLM 类型: {type(volcano_llm).__name__}")
            
    except Exception as e:
        print(f"CrewAI 配置测试失败: {e}")
        traceback.print_exc()
    print()

def test_llm_invoke():
    """测试 LLM 调用"""
    print("=== LLM 调用测试 ===")
    test_prompt = "Hello, this is a test message. Please respond with 'Test successful'."
    
    try:
        manager = get_provider_manager()
        available_providers = manager.get_available_providers()
        
        if not available_providers:
            print("没有可用的提供商进行测试")
            return
        
        for provider in available_providers:
            print(f"测试提供商: {provider}")
            try:
                llm = get_llm(provider=provider)
                response = llm.invoke(test_prompt)
                print(f"  响应: {str(response)[:100]}...")
                print(f"  状态: 成功")
            except Exception as e:
                print(f"  错误: {e}")
                print(f"  状态: 失败")
            print()
            
    except Exception as e:
        print(f"LLM 调用测试失败: {e}")
        traceback.print_exc()

def main():
    """主函数"""
    print("LLM 提供商诊断工具")
    print("=" * 50)
    
    test_basic_config()
    test_config_validation()
    test_provider_manager()
    test_crew_config()
    test_llm_invoke()
    
    print("诊断完成")

if __name__ == "__main__":
    main()