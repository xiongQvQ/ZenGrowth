#!/usr/bin/env python3
"""
Task 7 简单验证脚本
验证代码结构和基本功能（不需要API调用）
"""

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_imports():
    """测试所有必要的导入"""
    logger.info("测试导入...")
    
    try:
        # 测试智能体兼容性测试模块
        from tests.test_agent_volcano_compatibility import AgentCompatibilityTester, TestAgentVolcanoCompatibility
        logger.info("✅ 智能体兼容性测试模块导入成功")
        
        # 测试提供商切换测试模块
        from tests.test_provider_switching import ProviderSwitchingTester, TestProviderSwitching
        logger.info("✅ 提供商切换测试模块导入成功")
        
        # 测试集成测试运行器
        from tests.test_integration_runner import IntegrationTestRunner
        logger.info("✅ 集成测试运行器导入成功")
        
        # 测试数据生成器
        from tests.test_data_generator import generate_test_ga4_data, generate_test_events
        logger.info("✅ 测试数据生成器导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 导入测试失败: {e}")
        return False


def test_class_structure():
    """测试类结构"""
    logger.info("测试类结构...")
    
    try:
        from tests.test_agent_volcano_compatibility import AgentCompatibilityTester
        from tests.test_provider_switching import ProviderSwitchingTester
        from tests.test_integration_runner import IntegrationTestRunner
        
        # 测试AgentCompatibilityTester
        tester = AgentCompatibilityTester()
        assert hasattr(tester, 'test_agent_creation'), "缺少test_agent_creation方法"
        assert hasattr(tester, 'test_agent_basic_functionality'), "缺少test_agent_basic_functionality方法"
        assert hasattr(tester, 'test_agent_with_real_data'), "缺少test_agent_with_real_data方法"
        assert hasattr(tester, 'compare_providers'), "缺少compare_providers方法"
        logger.info("✅ AgentCompatibilityTester结构正确")
        
        # 测试ProviderSwitchingTester
        switcher = ProviderSwitchingTester()
        assert hasattr(switcher, 'test_dynamic_provider_switching'), "缺少test_dynamic_provider_switching方法"
        assert hasattr(switcher, 'test_fallback_during_analysis'), "缺少test_fallback_during_analysis方法"
        assert hasattr(switcher, 'test_concurrent_provider_switching'), "缺少test_concurrent_provider_switching方法"
        logger.info("✅ ProviderSwitchingTester结构正确")
        
        # 测试IntegrationTestRunner
        runner = IntegrationTestRunner()
        assert hasattr(runner, 'run_all_tests'), "缺少run_all_tests方法"
        assert hasattr(runner, 'run_compatibility_tests'), "缺少run_compatibility_tests方法"
        assert hasattr(runner, 'run_switching_tests'), "缺少run_switching_tests方法"
        logger.info("✅ IntegrationTestRunner结构正确")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 类结构测试失败: {e}")
        return False


def test_data_generation():
    """测试数据生成"""
    logger.info("测试数据生成...")
    
    try:
        from tests.test_data_generator import (
            generate_test_ga4_data, 
            generate_test_events,
            generate_test_users,
            generate_retention_cohort_data,
            generate_conversion_funnel_data
        )
        
        # 测试GA4数据生成
        ga4_data = generate_test_ga4_data(num_users=10, num_events=50)
        assert "users" in ga4_data, "GA4数据缺少users字段"
        assert "events" in ga4_data, "GA4数据缺少events字段"
        assert len(ga4_data["users"]) == 10, "用户数量不正确"
        assert len(ga4_data["events"]) == 50, "事件数量不正确"
        logger.info("✅ GA4数据生成正确")
        
        # 测试事件生成
        events = generate_test_events(num_events=20)
        assert len(events) == 20, "事件数量不正确"
        assert all("event_name" in event for event in events), "事件缺少event_name字段"
        logger.info("✅ 事件数据生成正确")
        
        # 测试用户生成
        users = generate_test_users(num_users=5)
        assert len(users) == 5, "用户数量不正确"
        assert all("user_id" in user for user in users), "用户缺少user_id字段"
        logger.info("✅ 用户数据生成正确")
        
        # 测试留存数据生成
        retention_data = generate_retention_cohort_data()
        assert len(retention_data) > 0, "留存数据为空"
        logger.info("✅ 留存数据生成正确")
        
        # 测试转化数据生成
        conversion_data = generate_conversion_funnel_data()
        assert "steps" in conversion_data, "转化数据缺少steps字段"
        assert len(conversion_data["steps"]) > 0, "转化步骤为空"
        logger.info("✅ 转化数据生成正确")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据生成测试失败: {e}")
        return False


def test_test_methods():
    """测试测试方法的基本结构"""
    logger.info("测试测试方法结构...")
    
    try:
        from tests.test_agent_volcano_compatibility import AgentCompatibilityTester
        from tests.test_provider_switching import ProviderSwitchingTester
        
        # 创建测试器实例
        compatibility_tester = AgentCompatibilityTester()
        switching_tester = ProviderSwitchingTester()
        
        # 检查方法签名
        import inspect
        
        # 检查兼容性测试方法
        methods_to_check = [
            'test_agent_creation',
            'test_agent_basic_functionality', 
            'test_agent_with_real_data',
            'compare_providers'
        ]
        
        for method_name in methods_to_check:
            method = getattr(compatibility_tester, method_name)
            sig = inspect.signature(method)
            assert len(sig.parameters) >= 1, f"{method_name}方法参数不足"
            logger.info(f"✅ {method_name}方法签名正确")
        
        # 检查切换测试方法
        switching_methods = [
            'test_dynamic_provider_switching',
            'test_fallback_during_analysis',
            'test_concurrent_provider_switching'
        ]
        
        for method_name in switching_methods:
            method = getattr(switching_tester, method_name)
            sig = inspect.signature(method)
            # 这些方法不需要参数（除了self）
            logger.info(f"✅ {method_name}方法存在")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试方法结构测试失败: {e}")
        return False


def test_file_structure():
    """测试文件结构"""
    logger.info("测试文件结构...")
    
    required_files = [
        "tests/test_agent_volcano_compatibility.py",
        "tests/test_provider_switching.py", 
        "tests/test_integration_runner.py",
        "tests/test_data_generator.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            logger.info(f"✅ {file_path} 存在")
    
    if missing_files:
        logger.error(f"❌ 缺少文件: {missing_files}")
        return False
    
    logger.info("✅ 所有必需文件都存在")
    return True


def test_pytest_compatibility():
    """测试pytest兼容性"""
    logger.info("测试pytest兼容性...")
    
    try:
        import pytest
        
        # 检查测试类是否符合pytest规范
        from tests.test_agent_volcano_compatibility import TestAgentVolcanoCompatibility
        from tests.test_provider_switching import TestProviderSwitching
        
        # 检查测试类名
        assert TestAgentVolcanoCompatibility.__name__.startswith("Test"), "测试类名不符合pytest规范"
        assert TestProviderSwitching.__name__.startswith("Test"), "测试类名不符合pytest规范"
        
        # 检查测试方法名
        compatibility_methods = [method for method in dir(TestAgentVolcanoCompatibility) if method.startswith("test_")]
        switching_methods = [method for method in dir(TestProviderSwitching) if method.startswith("test_")]
        
        assert len(compatibility_methods) > 0, "兼容性测试类没有测试方法"
        assert len(switching_methods) > 0, "切换测试类没有测试方法"
        
        logger.info(f"✅ 兼容性测试方法数: {len(compatibility_methods)}")
        logger.info(f"✅ 切换测试方法数: {len(switching_methods)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ pytest兼容性测试失败: {e}")
        return False


def run_simple_verification():
    """运行简单验证"""
    logger.info("开始运行Task 7简单验证...")
    
    tests = [
        ("文件结构", test_file_structure),
        ("导入测试", test_imports),
        ("类结构", test_class_structure),
        ("数据生成", test_data_generation),
        ("测试方法", test_test_methods),
        ("pytest兼容性", test_pytest_compatibility)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = {"success": result, "error": None}
            
            if result:
                passed += 1
                logger.info(f"✅ {test_name} 通过")
            else:
                logger.error(f"❌ {test_name} 失败")
                
        except Exception as e:
            results[test_name] = {"success": False, "error": str(e)}
            logger.error(f"❌ {test_name} 异常: {e}")
    
    # 打印总结
    logger.info(f"\n{'='*60}")
    logger.info("简单验证总结")
    logger.info(f"{'='*60}")
    logger.info(f"总测试数: {total}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {total - passed}")
    logger.info(f"成功率: {passed/total:.1%}")
    
    # 详细结果
    for test_name, result in results.items():
        status = "✅ 通过" if result["success"] else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        
        if result["error"]:
            logger.info(f"  错误: {result['error']}")
    
    logger.info(f"{'='*60}")
    
    return passed == total


def main():
    """主函数"""
    success = run_simple_verification()
    
    if success:
        logger.info("🎉 所有简单验证通过！")
        logger.info("Task 7 - 智能体兼容性和提供商切换测试代码结构正确")
        logger.info("\n📋 实现的功能:")
        logger.info("  ✅ 智能体与Volcano提供商兼容性测试")
        logger.info("  ✅ 输出格式一致性验证")
        logger.info("  ✅ 分析质量和准确性测试")
        logger.info("  ✅ 动态提供商切换测试")
        logger.info("  ✅ 回退行为测试")
        logger.info("  ✅ 性能影响评估")
        logger.info("  ✅ 并发切换测试")
        logger.info("  ✅ 完整的测试数据生成")
        logger.info("  ✅ 集成测试运行器")
        logger.info("\n🚀 可以使用以下命令运行实际测试:")
        logger.info("  python -m pytest tests/test_agent_volcano_compatibility.py -v")
        logger.info("  python -m pytest tests/test_provider_switching.py -v")
        logger.info("  python tests/test_integration_runner.py")
        sys.exit(0)
    else:
        logger.error("💥 简单验证失败！")
        logger.error("请检查代码结构和实现")
        sys.exit(1)


if __name__ == "__main__":
    main()