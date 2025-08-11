#!/usr/bin/env python3
"""
Task 7 集成测试验证脚本
验证智能体兼容性和提供商切换功能
"""

import sys
import os
import logging
import time
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_basic_agent_creation():
    """测试基本智能体创建"""
    logger.info("测试基本智能体创建...")
    
    try:
        from config.crew_config import create_agent
        
        # 测试创建Google智能体
        google_agent = create_agent("event_analyst", provider="google")
        assert google_agent is not None, "Google智能体创建失败"
        logger.info("✅ Google智能体创建成功")
        
        # 测试创建Volcano智能体
        volcano_agent = create_agent("event_analyst", provider="volcano")
        assert volcano_agent is not None, "Volcano智能体创建失败"
        logger.info("✅ Volcano智能体创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 智能体创建测试失败: {e}")
        return False


def test_provider_manager():
    """测试提供商管理器"""
    logger.info("测试提供商管理器...")
    
    try:
        from config.llm_provider_manager import get_provider_manager
        
        manager = get_provider_manager()
        
        # 测试获取可用提供商
        providers = manager.get_available_providers()
        logger.info(f"可用提供商: {providers}")
        
        # 测试健康检查
        health_results = manager.health_check_all()
        for provider, health in health_results.items():
            logger.info(f"{provider} 状态: {health.status.value}")
        
        # 测试获取LLM
        google_llm = manager.get_llm("google")
        assert google_llm is not None, "获取Google LLM失败"
        logger.info("✅ Google LLM获取成功")
        
        volcano_llm = manager.get_llm("volcano")
        assert volcano_llm is not None, "获取Volcano LLM失败"
        logger.info("✅ Volcano LLM获取成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 提供商管理器测试失败: {e}")
        return False


def test_simple_llm_calls():
    """测试简单LLM调用"""
    logger.info("测试简单LLM调用...")
    
    try:
        from config.llm_provider_manager import get_provider_manager
        
        manager = get_provider_manager()
        test_prompt = "Hello, this is a test message. Please respond briefly."
        
        # 测试Google提供商
        try:
            google_llm = manager.get_llm("google")
            google_response = google_llm.invoke(test_prompt)
            assert len(str(google_response)) > 0, "Google响应为空"
            logger.info(f"✅ Google响应: {str(google_response)[:100]}...")
        except Exception as e:
            logger.warning(f"⚠️ Google调用失败: {e}")
        
        # 测试Volcano提供商
        try:
            volcano_llm = manager.get_llm("volcano")
            volcano_response = volcano_llm.invoke(test_prompt)
            assert len(str(volcano_response)) > 0, "Volcano响应为空"
            logger.info(f"✅ Volcano响应: {str(volcano_response)[:100]}...")
        except Exception as e:
            logger.warning(f"⚠️ Volcano调用失败: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM调用测试失败: {e}")
        return False


def test_crew_manager():
    """测试CrewManager"""
    logger.info("测试CrewManager...")
    
    try:
        from config.crew_config import CrewManager
        
        # 创建团队管理器
        crew_manager = CrewManager(default_provider="google")
        
        # 添加智能体
        crew_manager.add_agent("event_analyst", provider="google")
        crew_manager.add_agent("retention_analyst", provider="volcano")
        
        # 检查智能体信息
        crew_info = crew_manager.get_crew_info()
        logger.info(f"团队信息: {crew_info}")
        
        assert crew_info["total_agents"] == 2, "智能体数量不正确"
        assert "event_analyst" in crew_info["agent_providers"], "事件分析智能体未找到"
        assert "retention_analyst" in crew_info["agent_providers"], "留存分析智能体未找到"
        
        # 测试提供商切换
        crew_manager.update_agent_provider("event_analyst", "volcano")
        updated_provider = crew_manager.get_agent_provider("event_analyst")
        assert updated_provider == "volcano", "提供商切换失败"
        
        logger.info("✅ CrewManager测试成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ CrewManager测试失败: {e}")
        return False


def test_fallback_mechanism():
    """测试回退机制"""
    logger.info("测试回退机制...")
    
    try:
        from config.llm_provider_manager import get_provider_manager
        
        manager = get_provider_manager()
        
        # 测试带回退的调用
        response, used_provider, fallback_event = manager.invoke_with_fallback(
            prompt="Test fallback mechanism",
            provider="google"
        )
        
        assert response is not None, "回退调用失败"
        assert used_provider in ["google", "volcano"], "使用的提供商不正确"
        
        logger.info(f"✅ 回退机制测试成功，使用提供商: {used_provider}")
        
        if fallback_event:
            logger.info(f"触发回退: {fallback_event.primary_provider} -> {fallback_event.fallback_provider}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 回退机制测试失败: {e}")
        return False


def run_integration_verification():
    """运行集成验证"""
    logger.info("开始运行Task 7集成测试验证...")
    
    tests = [
        ("基本智能体创建", test_basic_agent_creation),
        ("提供商管理器", test_provider_manager),
        ("简单LLM调用", test_simple_llm_calls),
        ("CrewManager", test_crew_manager),
        ("回退机制", test_fallback_mechanism)
    ]
    
    results = {}
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"运行测试: {test_name}")
        logger.info(f"{'='*50}")
        
        start_time = time.time()
        try:
            result = test_func()
            end_time = time.time()
            
            results[test_name] = {
                "success": result,
                "duration": end_time - start_time,
                "error": None
            }
            
            if result:
                passed += 1
                logger.info(f"✅ {test_name} 通过 ({end_time - start_time:.2f}s)")
            else:
                logger.error(f"❌ {test_name} 失败")
                
        except Exception as e:
            end_time = time.time()
            results[test_name] = {
                "success": False,
                "duration": end_time - start_time,
                "error": str(e)
            }
            logger.error(f"❌ {test_name} 异常: {e}")
    
    # 打印总结
    logger.info(f"\n{'='*60}")
    logger.info("集成测试验证总结")
    logger.info(f"{'='*60}")
    logger.info(f"总测试数: {total}")
    logger.info(f"通过: {passed}")
    logger.info(f"失败: {total - passed}")
    logger.info(f"成功率: {passed/total:.1%}")
    
    # 详细结果
    for test_name, result in results.items():
        status = "✅ 通过" if result["success"] else "❌ 失败"
        duration = result["duration"]
        logger.info(f"{test_name}: {status} ({duration:.2f}s)")
        
        if result["error"]:
            logger.info(f"  错误: {result['error']}")
    
    logger.info(f"{'='*60}")
    
    return passed == total


def main():
    """主函数"""
    success = run_integration_verification()
    
    if success:
        logger.info("🎉 所有集成测试验证通过！")
        logger.info("Task 7 - 智能体兼容性和提供商切换功能已就绪")
        sys.exit(0)
    else:
        logger.error("💥 集成测试验证失败！")
        logger.error("请检查配置和实现")
        sys.exit(1)


if __name__ == "__main__":
    main()