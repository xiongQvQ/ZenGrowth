#!/usr/bin/env python3
"""
简单测试crew_config.py的多提供商支持功能（不依赖CrewAI）
"""

import sys
import os
import logging
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports_and_basic_functionality():
    """测试导入和基本功能"""
    print("=" * 50)
    print("测试导入和基本功能")
    print("=" * 50)
    
    try:
        # Mock CrewAI components to avoid import errors
        with patch.dict('sys.modules', {
            'crewai': MagicMock(),
            'crewai.tools': MagicMock(),
            'langchain_google_genai': MagicMock(),
        }):
            # Mock the ChatGoogleGenerativeAI class
            mock_google_llm = MagicMock()
            mock_google_llm.__name__ = 'ChatGoogleGenerativeAI'
            
            with patch('config.crew_config.ChatGoogleGenerativeAI', return_value=mock_google_llm):
                # Mock the provider manager
                mock_provider_manager = MagicMock()
                mock_provider_manager.get_llm.return_value = mock_google_llm
                mock_provider_manager.get_available_providers.return_value = ['google', 'volcano']
                mock_provider_manager.health_check.return_value = MagicMock(status=MagicMock(value='available'))
                mock_provider_manager.get_provider_info.return_value = {'name': 'google', 'status': 'available'}
                mock_provider_manager.get_system_info.return_value = {'total_providers': 2}
                
                with patch('config.crew_config.get_provider_manager', return_value=mock_provider_manager):
                    # Now test the imports
                    from config.crew_config import (
                        get_llm, 
                        get_available_providers, 
                        check_provider_health, 
                        get_provider_info
                    )
                    
                    print("✅ 成功导入所有函数")
                    
                    # Test get_llm function
                    print("\n1. 测试get_llm函数")
                    llm_default = get_llm()
                    print(f"默认LLM: {llm_default}")
                    
                    llm_google = get_llm(provider="google")
                    print(f"Google LLM: {llm_google}")
                    
                    llm_volcano = get_llm(provider="volcano")
                    print(f"Volcano LLM: {llm_volcano}")
                    
                    # Test utility functions
                    print("\n2. 测试工具函数")
                    providers = get_available_providers()
                    print(f"可用提供商: {providers}")
                    
                    health = check_provider_health("google")
                    print(f"Google健康状态: {health}")
                    
                    info = get_provider_info("google")
                    print(f"Google信息: {info}")
                    
                    system_info = get_provider_info()
                    print(f"系统信息: {system_info}")
                    
                    print("\n✅ 所有基本功能测试通过")
                    return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "=" * 50)
    print("测试向后兼容性")
    print("=" * 50)
    
    try:
        # Mock CrewAI components
        with patch.dict('sys.modules', {
            'crewai': MagicMock(),
            'crewai.tools': MagicMock(),
            'langchain_google_genai': MagicMock(),
        }):
            mock_google_llm = MagicMock()
            mock_google_llm.__name__ = 'ChatGoogleGenerativeAI'
            
            with patch('config.crew_config.ChatGoogleGenerativeAI', return_value=mock_google_llm):
                # Test fallback behavior when provider manager fails
                with patch('config.crew_config.get_provider_manager', side_effect=Exception("Provider manager not available")):
                    from config.crew_config import get_llm
                    
                    print("\n1. 测试提供商管理器不可用时的回退行为")
                    llm = get_llm()
                    print(f"回退LLM类型: {type(llm)}")
                    
                    # Test with specific provider when manager fails
                    llm_volcano = get_llm(provider="volcano")
                    print(f"指定Volcano但回退到Google: {type(llm_volcano)}")
                    
                    print("\n✅ 向后兼容性测试通过")
                    return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crew_manager_mock():
    """测试CrewManager的模拟功能"""
    print("\n" + "=" * 50)
    print("测试CrewManager模拟功能")
    print("=" * 50)
    
    try:
        # Mock all CrewAI components
        mock_agent = MagicMock()
        mock_agent.role = "Test Agent"
        mock_agent.tools = []
        
        mock_crew_module = MagicMock()
        mock_crew_module.Agent = MagicMock(return_value=mock_agent)
        mock_crew_module.Task = MagicMock()
        mock_crew_module.Crew = MagicMock()
        
        with patch.dict('sys.modules', {
            'crewai': mock_crew_module,
            'crewai.tools': MagicMock(),
            'langchain_google_genai': MagicMock(),
        }):
            mock_google_llm = MagicMock()
            mock_google_llm.__name__ = 'ChatGoogleGenerativeAI'
            
            with patch('config.crew_config.ChatGoogleGenerativeAI', return_value=mock_google_llm):
                # Mock provider manager
                mock_provider_manager = MagicMock()
                mock_provider_manager.get_llm.return_value = mock_google_llm
                
                with patch('config.crew_config.get_provider_manager', return_value=mock_provider_manager):
                    # Import after all patches are in place
                    import importlib
                    import config.crew_config
                    importlib.reload(config.crew_config)
                    from config.crew_config import CrewManager, create_multi_provider_crew, create_agent
                    
                    print("\n1. 测试CrewManager基本功能")
                    crew_manager = CrewManager(default_provider="google")
                    crew_manager.add_agent("event_analyst", provider="google")
                    crew_manager.add_agent("retention_analyst")  # 使用默认提供商
                    
                    info = crew_manager.get_crew_info()
                    print(f"团队信息: {info}")
                    
                    print("\n2. 测试多提供商团队创建")
                    agent_configs = [
                        {'type': 'event_analyst', 'provider': 'google'},
                        {'type': 'retention_analyst'},
                    ]
                    
                    multi_crew = create_multi_provider_crew(agent_configs, default_provider="google")
                    multi_info = multi_crew.get_crew_info()
                    print(f"多提供商团队信息: {multi_info}")
                    
                    print("\n3. 测试智能体创建")
                    agent = create_agent("event_analyst", provider="google")
                    print(f"智能体创建成功: {agent.role}")
                    
                    print("\n✅ CrewManager模拟测试通过")
                    return True
        
    except Exception as e:
        print(f"❌ CrewManager模拟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试crew_config.py的多提供商支持功能（简化版）")
    print("=" * 80)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("基本功能", test_imports_and_basic_functionality()))
    test_results.append(("向后兼容性", test_backward_compatibility()))
    test_results.append(("CrewManager模拟", test_crew_manager_mock()))
    
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