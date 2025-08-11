#!/usr/bin/env python3
"""
测试crew_config.py的多提供商支持功能
"""

import sys
import os
import logging
from unittest.mock import Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_get_llm_with_provider():
    """测试get_llm函数的提供商选择功能"""
    print("=" * 50)
    print("测试 get_llm 函数的提供商选择功能")
    print("=" * 50)
    
    try:
        from config.crew_config import get_llm
        
        # 测试默认提供商
        print("\n1. 测试默认提供商")
        llm_default = get_llm()
        print(f"默认LLM类型: {type(llm_default).__name__}")
        
        # 测试指定Google提供商
        print("\n2. 测试Google提供商")
        llm_google = get_llm(provider="google")
        print(f"Google LLM类型: {type(llm_google).__name__}")
        
        # 测试指定Volcano提供商（可能失败，这是正常的）
        print("\n3. 测试Volcano提供商")
        try:
            llm_volcano = get_llm(provider="volcano")
            print(f"Volcano LLM类型: {type(llm_volcano).__name__}")
        except Exception as e:
            print(f"Volcano提供商不可用（预期行为）: {e}")
        
        print("\n✅ get_llm函数测试完成")
        return True
        
    except Exception as e:
        print(f"❌ get_llm函数测试失败: {e}")
        return False


def test_create_agent_with_provider():
    """测试create_agent函数的提供商选择功能"""
    print("\n" + "=" * 50)
    print("测试 create_agent 函数的提供商选择功能")
    print("=" * 50)
    
    try:
        from config.crew_config import create_agent, create_google_agent, create_volcano_agent
        
        # 测试默认智能体创建
        print("\n1. 测试默认智能体创建")
        agent_default = create_agent("event_analyst")
        print(f"默认智能体创建成功: {agent_default.role}")
        
        # 测试指定Google提供商的智能体
        print("\n2. 测试Google智能体创建")
        agent_google = create_agent("retention_analyst", provider="google")
        print(f"Google智能体创建成功: {agent_google.role}")
        
        # 测试便利函数
        print("\n3. 测试便利函数")
        agent_google_conv = create_google_agent("conversion_analyst")
        print(f"Google便利函数智能体创建成功: {agent_google_conv.role}")
        
        # 测试Volcano智能体（可能失败）
        print("\n4. 测试Volcano智能体创建")
        try:
            agent_volcano = create_volcano_agent("segmentation_analyst")
            print(f"Volcano智能体创建成功: {agent_volcano.role}")
        except Exception as e:
            print(f"Volcano智能体创建失败（预期行为）: {e}")
        
        print("\n✅ create_agent函数测试完成")
        return True
        
    except Exception as e:
        print(f"❌ create_agent函数测试失败: {e}")
        return False


def test_crew_manager_multi_provider():
    """测试CrewManager的多提供商支持"""
    print("\n" + "=" * 50)
    print("测试 CrewManager 的多提供商支持")
    print("=" * 50)
    
    try:
        from config.crew_config import CrewManager, create_multi_provider_crew
        
        # 测试基本CrewManager
        print("\n1. 测试基本CrewManager")
        crew_manager = CrewManager(default_provider="google")
        
        # 添加智能体
        crew_manager.add_agent("event_analyst", provider="google")
        crew_manager.add_agent("retention_analyst")  # 使用默认提供商
        
        # 获取团队信息
        info = crew_manager.get_crew_info()
        print(f"团队信息: {info}")
        
        # 测试提供商信息获取
        print(f"event_analyst使用的提供商: {crew_manager.get_agent_provider('event_analyst')}")
        print(f"retention_analyst使用的提供商: {crew_manager.get_agent_provider('retention_analyst')}")
        
        # 测试多提供商团队创建
        print("\n2. 测试多提供商团队创建")
        agent_configs = [
            {'type': 'event_analyst', 'provider': 'google'},
            {'type': 'retention_analyst'},  # 使用默认提供商
            {'type': 'conversion_analyst', 'provider': 'google'}
        ]
        
        multi_crew = create_multi_provider_crew(agent_configs, default_provider="google")
        multi_info = multi_crew.get_crew_info()
        print(f"多提供商团队信息: {multi_info}")
        
        print("\n✅ CrewManager多提供商测试完成")
        return True
        
    except Exception as e:
        print(f"❌ CrewManager多提供商测试失败: {e}")
        return False


def test_utility_functions():
    """测试工具函数"""
    print("\n" + "=" * 50)
    print("测试工具函数")
    print("=" * 50)
    
    try:
        from config.crew_config import (
            get_available_providers, 
            check_provider_health, 
            get_provider_info
        )
        
        # 测试获取可用提供商
        print("\n1. 测试获取可用提供商")
        providers = get_available_providers()
        print(f"可用提供商: {providers}")
        
        # 测试健康检查
        print("\n2. 测试提供商健康检查")
        for provider in ["google", "volcano"]:
            health = check_provider_health(provider)
            print(f"{provider}提供商健康状态: {health}")
        
        # 测试获取提供商信息
        print("\n3. 测试获取提供商信息")
        info = get_provider_info()
        print(f"系统信息: {info}")
        
        print("\n✅ 工具函数测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 工具函数测试失败: {e}")
        return False


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "=" * 50)
    print("测试向后兼容性")
    print("=" * 50)
    
    try:
        # 测试原有的get_llm()调用方式
        from config.crew_config import get_llm, create_agent, CrewManager
        
        print("\n1. 测试原有get_llm()调用")
        llm = get_llm()  # 不传参数，应该使用默认提供商
        print(f"向后兼容LLM类型: {type(llm).__name__}")
        
        print("\n2. 测试原有create_agent()调用")
        agent = create_agent("event_analyst")  # 不传provider参数
        print(f"向后兼容智能体创建成功: {agent.role}")
        
        print("\n3. 测试原有CrewManager使用")
        crew_manager = CrewManager()  # 不传default_provider参数
        crew_manager.add_agent("retention_analyst")  # 不传provider参数
        info = crew_manager.get_crew_info()
        print(f"向后兼容团队信息: {info}")
        
        print("\n✅ 向后兼容性测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试crew_config.py的多提供商支持功能")
    print("=" * 80)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("get_llm函数", test_get_llm_with_provider()))
    test_results.append(("create_agent函数", test_create_agent_with_provider()))
    test_results.append(("CrewManager多提供商", test_crew_manager_multi_provider()))
    test_results.append(("工具函数", test_utility_functions()))
    test_results.append(("向后兼容性", test_backward_compatibility()))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！crew_config.py多提供商支持功能正常工作。")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)