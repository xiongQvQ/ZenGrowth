"""
测试提供商切换场景
测试动态提供商切换、回退行为和性能影响
"""

import pytest
import logging
import time
import threading
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入配置和管理器
from config.crew_config import CrewManager, create_agent, get_llm
from config.llm_provider_manager import get_provider_manager, ProviderStatus
from config.fallback_handler import FallbackReason, get_fallback_handler
from config.settings import settings

# 导入测试数据
from tests.test_data_generator import generate_test_ga4_data, generate_test_events

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderSwitchingTester:
    """提供商切换测试器"""
    
    def __init__(self):
        self.provider_manager = get_provider_manager()
        self.fallback_handler = get_fallback_handler()
        self.test_data = generate_test_ga4_data()
        self.test_results = {}
        
    def setup_test_environment(self):
        """设置测试环境"""
        # 确保两个提供商都可用
        google_status = self.provider_manager.health_check("google")
        volcano_status = self.provider_manager.health_check("volcano")
        
        if google_status.status != ProviderStatus.AVAILABLE:
            pytest.skip("Google提供商不可用，跳过切换测试")
        
        if volcano_status.status != ProviderStatus.AVAILABLE:
            pytest.skip("Volcano提供商不可用，跳过切换测试")
        
        # 重置回退统计
        self.fallback_handler.clear_history()
        
        logger.info("测试环境设置完成")
    
    def test_dynamic_provider_switching(self, agent_type: str = "event_analyst") -> Dict[str, Any]:
        """
        测试动态提供商切换
        
        Args:
            agent_type: 智能体类型
            
        Returns:
            测试结果字典
        """
        result = {
            "test_name": "dynamic_provider_switching",
            "agent_type": agent_type,
            "switches": [],
            "success": False,
            "total_time": 0,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            # 创建CrewManager
            crew_manager = CrewManager()
            
            # 测试序列：Google -> Volcano -> Google
            switch_sequence = [
                ("google", "使用Google提供商进行初始分析"),
                ("volcano", "切换到Volcano提供商"),
                ("google", "切换回Google提供商")
            ]
            
            for provider, description in switch_sequence:
                switch_start = time.time()
                
                # 添加或更新智能体
                if agent_type in crew_manager.agents:
                    crew_manager.update_agent_provider(agent_type, provider)
                else:
                    crew_manager.add_agent(agent_type, provider=provider)
                
                # 执行测试任务
                test_prompt = f"分析用户行为数据，当前使用{provider}提供商"
                
                agent = crew_manager.agents[agent_type]
                response = agent.llm.invoke(test_prompt)
                
                switch_time = time.time() - switch_start
                
                switch_result = {
                    "provider": provider,
                    "description": description,
                    "response_time": switch_time,
                    "response_length": len(str(response)),
                    "success": True,
                    "actual_provider": crew_manager.get_agent_provider(agent_type)
                }
                
                result["switches"].append(switch_result)
                logger.info(f"切换到 {provider} 成功，耗时 {switch_time:.2f}s")
            
            result["success"] = True
            result["total_time"] = time.time() - start_time
            
        except Exception as e:
            result["error"] = str(e)
            result["total_time"] = time.time() - start_time
            logger.error(f"动态切换测试失败: {e}")
        
        return result
    
    def test_fallback_during_analysis(self) -> Dict[str, Any]:
        """
        测试分析过程中的回退行为
        
        Returns:
            测试结果字典
        """
        result = {
            "test_name": "fallback_during_analysis",
            "fallback_triggered": False,
            "fallback_successful": False,
            "original_provider": None,
            "fallback_provider": None,
            "performance_impact": 0,
            "error": None
        }
        
        try:
            # 模拟主提供商失败的情况
            with patch.object(self.provider_manager, '_providers') as mock_providers:
                # 设置模拟的提供商
                mock_google_llm = Mock()
                mock_volcano_llm = Mock()
                
                # 让Google提供商失败
                mock_google_llm.invoke.side_effect = Exception("模拟的Google API错误")
                mock_volcano_llm.invoke.return_value = "Volcano提供商的分析结果"
                
                mock_providers.__getitem__.side_effect = lambda key: {
                    "google": mock_google_llm,
                    "volcano": mock_volcano_llm
                }[key]
                mock_providers.keys.return_value = ["google", "volcano"]
                
                # 执行带回退的调用
                start_time = time.time()
                
                response, used_provider, fallback_event = self.provider_manager.invoke_with_fallback(
                    prompt="测试回退机制",
                    provider="google"  # 指定使用Google，但会失败并回退
                )
                
                end_time = time.time()
                
                result["fallback_triggered"] = fallback_event is not None
                result["fallback_successful"] = response is not None
                result["original_provider"] = "google"
                result["fallback_provider"] = used_provider
                result["performance_impact"] = end_time - start_time
                
                if fallback_event:
                    logger.info(f"回退成功: {fallback_event.primary_provider} -> {fallback_event.fallback_provider}")
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"回退测试失败: {e}")
        
        return result
    
    def test_concurrent_provider_switching(self) -> Dict[str, Any]:
        """
        测试并发提供商切换
        
        Returns:
            测试结果字典
        """
        result = {
            "test_name": "concurrent_provider_switching",
            "concurrent_tasks": 5,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0,
            "provider_distribution": {},
            "error": None
        }
        
        def concurrent_task(task_id: int) -> Dict[str, Any]:
            """并发任务函数"""
            try:
                # 随机选择提供商
                provider = "google" if task_id % 2 == 0 else "volcano"
                
                # 创建智能体
                agent = create_agent("event_analyst", provider=provider)
                
                start_time = time.time()
                response = agent.llm.invoke(f"任务{task_id}: 分析用户行为数据")
                end_time = time.time()
                
                return {
                    "task_id": task_id,
                    "provider": provider,
                    "success": True,
                    "response_time": end_time - start_time,
                    "response_length": len(str(response))
                }
                
            except Exception as e:
                return {
                    "task_id": task_id,
                    "provider": provider,
                    "success": False,
                    "error": str(e),
                    "response_time": 0
                }
        
        try:
            # 执行并发任务
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(concurrent_task, i) for i in range(5)]
                task_results = [future.result() for future in as_completed(futures)]
            
            # 分析结果
            successful_tasks = [r for r in task_results if r["success"]]
            failed_tasks = [r for r in task_results if not r["success"]]
            
            result["successful_tasks"] = len(successful_tasks)
            result["failed_tasks"] = len(failed_tasks)
            
            if successful_tasks:
                result["avg_response_time"] = sum(r["response_time"] for r in successful_tasks) / len(successful_tasks)
                
                # 统计提供商分布
                for task in successful_tasks:
                    provider = task["provider"]
                    result["provider_distribution"][provider] = result["provider_distribution"].get(provider, 0) + 1
            
            logger.info(f"并发切换测试完成: {result['successful_tasks']}/{result['concurrent_tasks']} 成功")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"并发切换测试失败: {e}")
        
        return result
    
    def test_provider_performance_impact(self) -> Dict[str, Any]:
        """
        测试提供商切换的性能影响
        
        Returns:
            测试结果字典
        """
        result = {
            "test_name": "provider_performance_impact",
            "baseline_performance": {},
            "switching_performance": {},
            "performance_overhead": 0,
            "error": None
        }
        
        try:
            # 基线性能测试（无切换）
            baseline_times = []
            agent = create_agent("event_analyst", provider="google")
            
            for i in range(3):
                start_time = time.time()
                agent.llm.invoke(f"基线测试 {i}: 分析用户数据")
                end_time = time.time()
                baseline_times.append(end_time - start_time)
            
            result["baseline_performance"] = {
                "avg_time": sum(baseline_times) / len(baseline_times),
                "min_time": min(baseline_times),
                "max_time": max(baseline_times)
            }
            
            # 切换性能测试
            switching_times = []
            crew_manager = CrewManager()
            crew_manager.add_agent("event_analyst", provider="google")
            
            providers = ["volcano", "google", "volcano"]  # 切换序列
            
            for i, provider in enumerate(providers):
                start_time = time.time()
                
                # 切换提供商
                crew_manager.update_agent_provider("event_analyst", provider)
                
                # 执行任务
                agent = crew_manager.agents["event_analyst"]
                agent.llm.invoke(f"切换测试 {i}: 分析用户数据")
                
                end_time = time.time()
                switching_times.append(end_time - start_time)
            
            result["switching_performance"] = {
                "avg_time": sum(switching_times) / len(switching_times),
                "min_time": min(switching_times),
                "max_time": max(switching_times)
            }
            
            # 计算性能开销
            baseline_avg = result["baseline_performance"]["avg_time"]
            switching_avg = result["switching_performance"]["avg_time"]
            result["performance_overhead"] = (switching_avg - baseline_avg) / baseline_avg * 100
            
            logger.info(f"性能影响测试完成，开销: {result['performance_overhead']:.1f}%")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"性能影响测试失败: {e}")
        
        return result
    
    def test_fallback_chain_behavior(self) -> Dict[str, Any]:
        """
        测试回退链行为
        
        Returns:
            测试结果字典
        """
        result = {
            "test_name": "fallback_chain_behavior",
            "fallback_chain": [],
            "final_provider": None,
            "total_fallbacks": 0,
            "success": False,
            "error": None
        }
        
        try:
            # 模拟多个提供商失败的情况
            with patch.object(self.provider_manager, '_providers') as mock_providers:
                mock_google_llm = Mock()
                mock_volcano_llm = Mock()
                
                # 设置第一个提供商失败，第二个成功
                mock_google_llm.invoke.side_effect = Exception("Google API失败")
                mock_volcano_llm.invoke.return_value = "Volcano成功响应"
                
                mock_providers.__getitem__.side_effect = lambda key: {
                    "google": mock_google_llm,
                    "volcano": mock_volcano_llm
                }[key]
                mock_providers.keys.return_value = ["google", "volcano"]
                
                # 模拟健康检查
                with patch.object(self.provider_manager, '_is_provider_healthy') as mock_health:
                    mock_health.side_effect = lambda p: p == "volcano"  # 只有volcano健康
                    
                    # 执行回退测试
                    response, used_provider, fallback_event = self.provider_manager.invoke_with_fallback(
                        prompt="测试回退链",
                        provider="google"
                    )
                    
                    result["success"] = response is not None
                    result["final_provider"] = used_provider
                    
                    if fallback_event:
                        result["fallback_chain"].append({
                            "from": fallback_event.primary_provider,
                            "to": fallback_event.fallback_provider,
                            "reason": fallback_event.reason.value
                        })
                        result["total_fallbacks"] = 1
            
            logger.info(f"回退链测试完成，最终使用: {result['final_provider']}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"回退链测试失败: {e}")
        
        return result
    
    def test_provider_switching_with_crew(self) -> Dict[str, Any]:
        """
        测试在CrewAI团队中的提供商切换
        
        Returns:
            测试结果字典
        """
        result = {
            "test_name": "provider_switching_with_crew",
            "crew_agents": [],
            "switching_results": [],
            "crew_performance": {},
            "success": False,
            "error": None
        }
        
        try:
            # 创建多智能体团队
            crew_manager = CrewManager(default_provider="google")
            
            # 添加不同类型的智能体
            agent_configs = [
                {"type": "event_analyst", "provider": "google"},
                {"type": "retention_analyst", "provider": "volcano"},
                {"type": "report_generator", "provider": "google"}
            ]
            
            for config in agent_configs:
                crew_manager.add_agent(config["type"], provider=config["provider"])
                result["crew_agents"].append({
                    "type": config["type"],
                    "initial_provider": config["provider"]
                })
            
            # 测试团队级别的提供商切换
            start_time = time.time()
            
            # 切换所有智能体到volcano
            for agent_type in crew_manager.agents.keys():
                crew_manager.update_agent_provider(agent_type, "volcano")
                
                switch_result = {
                    "agent_type": agent_type,
                    "new_provider": "volcano",
                    "success": True
                }
                result["switching_results"].append(switch_result)
            
            # 测试团队执行
            crew_manager.add_task("分析用户事件数据", "event_analyst")
            crew_manager.add_task("计算用户留存率", "retention_analyst")
            crew_manager.add_task("生成综合报告", "report_generator")
            
            # 执行团队任务（模拟）
            crew_info = crew_manager.get_crew_info()
            
            end_time = time.time()
            
            result["crew_performance"] = {
                "total_agents": crew_info["total_agents"],
                "total_tasks": crew_info["total_tasks"],
                "execution_time": end_time - start_time,
                "final_providers": crew_info["agent_providers"]
            }
            
            result["success"] = True
            
            logger.info(f"团队切换测试完成，{crew_info['total_agents']}个智能体切换成功")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"团队切换测试失败: {e}")
        
        return result
    
    def test_provider_health_monitoring(self) -> Dict[str, Any]:
        """
        测试提供商健康监控和自动切换
        
        Returns:
            测试结果字典
        """
        result = {
            "test_name": "provider_health_monitoring",
            "health_checks": [],
            "auto_switches": [],
            "monitoring_effective": False,
            "error": None
        }
        
        try:
            # 执行健康检查
            health_results = self.provider_manager.health_check_all()
            
            for provider, health in health_results.items():
                result["health_checks"].append({
                    "provider": provider,
                    "status": health.status.value,
                    "response_time": health.response_time,
                    "error": health.error_message
                })
            
            # 模拟提供商健康状态变化
            with patch.object(self.provider_manager, 'health_check') as mock_health_check:
                # 模拟Google提供商变为不可用
                mock_health_check.return_value = Mock(
                    status=ProviderStatus.UNAVAILABLE,
                    error_message="模拟的健康检查失败"
                )
                
                # 测试自动切换
                try:
                    llm = self.provider_manager.get_llm(provider="google")
                    # 如果成功获取到LLM，说明有自动切换或回退机制
                    result["auto_switches"].append({
                        "from": "google",
                        "to": "fallback",
                        "success": True
                    })
                except Exception as e:
                    result["auto_switches"].append({
                        "from": "google", 
                        "to": "none",
                        "success": False,
                        "error": str(e)
                    })
            
            result["monitoring_effective"] = len(result["health_checks"]) > 0
            
            logger.info(f"健康监控测试完成，检查了{len(result['health_checks'])}个提供商")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"健康监控测试失败: {e}")
        
        return result


# 测试类
class TestProviderSwitching:
    """提供商切换测试"""
    
    @classmethod
    def setup_class(cls):
        """设置测试类"""
        cls.tester = ProviderSwitchingTester()
        cls.tester.setup_test_environment()
    
    def test_dynamic_provider_switching(self):
        """测试动态提供商切换"""
        result = self.tester.test_dynamic_provider_switching()
        
        assert result["success"], f"动态切换测试失败: {result.get('error')}"
        assert len(result["switches"]) == 3, "应该执行3次切换"
        
        # 检查每次切换都成功
        for switch in result["switches"]:
            assert switch["success"], f"切换到{switch['provider']}失败"
            assert switch["response_time"] > 0, "响应时间应该大于0"
            assert switch["response_length"] > 0, "响应长度应该大于0"
        
        # 检查切换序列正确
        expected_providers = ["google", "volcano", "google"]
        actual_providers = [s["provider"] for s in result["switches"]]
        assert actual_providers == expected_providers, f"切换序列不正确: {actual_providers}"
    
    def test_fallback_during_analysis(self):
        """测试分析过程中的回退行为"""
        result = self.tester.test_fallback_during_analysis()
        
        # 检查回退是否被触发
        assert result["fallback_triggered"], "回退机制应该被触发"
        assert result["fallback_successful"], "回退应该成功"
        assert result["original_provider"] == "google", "原始提供商应该是google"
        assert result["fallback_provider"] == "volcano", "回退提供商应该是volcano"
        assert result["performance_impact"] > 0, "性能影响应该被记录"
    
    def test_concurrent_provider_switching(self):
        """测试并发提供商切换"""
        result = self.tester.test_concurrent_provider_switching()
        
        assert result["successful_tasks"] >= 3, f"至少3个并发任务应该成功，实际: {result['successful_tasks']}"
        assert result["failed_tasks"] <= 2, f"失败任务不应超过2个，实际: {result['failed_tasks']}"
        
        # 检查提供商分布
        assert len(result["provider_distribution"]) > 0, "应该有提供商分布统计"
        
        # 检查平均响应时间合理
        if result["avg_response_time"] > 0:
            assert result["avg_response_time"] < 30, f"平均响应时间过长: {result['avg_response_time']}s"
    
    def test_provider_performance_impact(self):
        """测试提供商切换的性能影响"""
        result = self.tester.test_provider_performance_impact()
        
        assert "baseline_performance" in result, "应该有基线性能数据"
        assert "switching_performance" in result, "应该有切换性能数据"
        
        baseline_avg = result["baseline_performance"]["avg_time"]
        switching_avg = result["switching_performance"]["avg_time"]
        
        assert baseline_avg > 0, "基线平均时间应该大于0"
        assert switching_avg > 0, "切换平均时间应该大于0"
        
        # 性能开销不应该超过100%
        assert result["performance_overhead"] < 100, f"性能开销过高: {result['performance_overhead']:.1f}%"
    
    def test_fallback_chain_behavior(self):
        """测试回退链行为"""
        result = self.tester.test_fallback_chain_behavior()
        
        assert result["success"], f"回退链测试失败: {result.get('error')}"
        assert result["final_provider"] == "volcano", "最终应该使用volcano提供商"
        assert result["total_fallbacks"] >= 1, "应该至少有一次回退"
        
        # 检查回退链
        if result["fallback_chain"]:
            first_fallback = result["fallback_chain"][0]
            assert first_fallback["from"] == "google", "应该从google开始回退"
            assert first_fallback["to"] == "volcano", "应该回退到volcano"
    
    def test_provider_switching_with_crew(self):
        """测试在CrewAI团队中的提供商切换"""
        result = self.tester.test_provider_switching_with_crew()
        
        assert result["success"], f"团队切换测试失败: {result.get('error')}"
        assert len(result["crew_agents"]) == 3, "应该有3个智能体"
        assert len(result["switching_results"]) == 3, "应该有3次切换结果"
        
        # 检查所有智能体都切换成功
        for switch in result["switching_results"]:
            assert switch["success"], f"智能体{switch['agent_type']}切换失败"
            assert switch["new_provider"] == "volcano", "所有智能体都应该切换到volcano"
        
        # 检查团队性能
        crew_perf = result["crew_performance"]
        assert crew_perf["total_agents"] == 3, "团队应该有3个智能体"
        assert crew_perf["total_tasks"] == 3, "团队应该有3个任务"
        assert crew_perf["execution_time"] > 0, "执行时间应该大于0"
    
    def test_provider_health_monitoring(self):
        """测试提供商健康监控"""
        result = self.tester.test_provider_health_monitoring()
        
        assert result["monitoring_effective"], "健康监控应该有效"
        assert len(result["health_checks"]) >= 2, "应该检查至少2个提供商"
        
        # 检查健康检查结果
        for health_check in result["health_checks"]:
            assert health_check["provider"] in ["google", "volcano"], "提供商名称应该正确"
            assert health_check["status"] in ["available", "unavailable", "degraded", "unknown"], "状态应该有效"
    
    def test_switching_stress_test(self):
        """提供商切换压力测试"""
        stress_results = []
        
        # 执行多次快速切换
        crew_manager = CrewManager()
        crew_manager.add_agent("event_analyst", provider="google")
        
        providers = ["volcano", "google"] * 10  # 20次切换
        
        for i, provider in enumerate(providers):
            try:
                start_time = time.time()
                crew_manager.update_agent_provider("event_analyst", provider)
                
                # 执行简单任务
                agent = crew_manager.agents["event_analyst"]
                agent.llm.invoke(f"压力测试 {i}")
                
                end_time = time.time()
                
                stress_results.append({
                    "switch_id": i,
                    "provider": provider,
                    "success": True,
                    "time": end_time - start_time
                })
                
            except Exception as e:
                stress_results.append({
                    "switch_id": i,
                    "provider": provider,
                    "success": False,
                    "error": str(e)
                })
        
        # 分析压力测试结果
        successful_switches = [r for r in stress_results if r["success"]]
        failed_switches = [r for r in stress_results if not r["success"]]
        
        success_rate = len(successful_switches) / len(stress_results)
        
        logger.info(f"压力测试完成: {len(successful_switches)}/{len(stress_results)} 成功 ({success_rate:.1%})")
        
        # 至少80%的切换应该成功
        assert success_rate >= 0.8, f"压力测试成功率过低: {success_rate:.1%}"
        
        # 检查平均切换时间
        if successful_switches:
            avg_time = sum(r["time"] for r in successful_switches) / len(successful_switches)
            assert avg_time < 10, f"平均切换时间过长: {avg_time:.2f}s"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])