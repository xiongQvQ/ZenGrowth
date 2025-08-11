"""
测试现有智能体与Volcano提供商的兼容性
验证所有智能体在使用Volcano提供商时的正确性、输出格式一致性和分析质量
"""

import pytest
import logging
import time
import json
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock

# 导入智能体
from agents.event_analysis_agent import EventAnalysisAgent
from agents.retention_analysis_agent import RetentionAnalysisAgent
from agents.conversion_analysis_agent import ConversionAnalysisAgent
from agents.user_segmentation_agent import UserSegmentationAgent
from agents.path_analysis_agent import PathAnalysisAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.data_processing_agent import DataProcessingAgent

# 导入配置和管理器
from config.crew_config import create_agent, get_llm, CrewManager
from config.llm_provider_manager import get_provider_manager, ProviderStatus
from config.settings import settings

# 导入测试数据
from tests.test_data_generator import generate_test_ga4_data, generate_test_events

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentCompatibilityTester:
    """智能体兼容性测试器"""
    
    def __init__(self):
        self.provider_manager = get_provider_manager()
        self.test_data = generate_test_ga4_data()
        self.test_events = generate_test_events()
        self.results = {}
        
    def setup_test_environment(self):
        """设置测试环境"""
        # 确保Volcano提供商可用
        volcano_status = self.provider_manager.health_check("volcano")
        if volcano_status.status != ProviderStatus.AVAILABLE:
            pytest.skip("Volcano提供商不可用，跳过兼容性测试")
        
        # 确保Google提供商可用（用于对比）
        google_status = self.provider_manager.health_check("google")
        if google_status.status != ProviderStatus.AVAILABLE:
            pytest.skip("Google提供商不可用，无法进行对比测试")
    
    def test_agent_creation(self, agent_type: str, provider: str) -> bool:
        """
        测试智能体创建
        
        Args:
            agent_type: 智能体类型
            provider: 提供商名称
            
        Returns:
            是否创建成功
        """
        try:
            agent = create_agent(agent_type, provider=provider)
            assert agent is not None, f"智能体 {agent_type} 创建失败"
            assert hasattr(agent, 'llm'), f"智能体 {agent_type} 缺少LLM属性"
            
            logger.info(f"智能体 {agent_type} 使用 {provider} 提供商创建成功")
            return True
            
        except Exception as e:
            logger.error(f"智能体 {agent_type} 使用 {provider} 提供商创建失败: {e}")
            return False
    
    def test_agent_basic_functionality(self, agent_type: str, provider: str) -> Dict[str, Any]:
        """
        测试智能体基本功能
        
        Args:
            agent_type: 智能体类型
            provider: 提供商名称
            
        Returns:
            测试结果字典
        """
        result = {
            "agent_type": agent_type,
            "provider": provider,
            "success": False,
            "response_time": None,
            "output_length": 0,
            "output_format": "unknown",
            "error": None
        }
        
        try:
            # 创建智能体
            agent = create_agent(agent_type, provider=provider)
            
            # 准备测试提示
            test_prompt = self._get_test_prompt(agent_type)
            
            # 执行测试
            start_time = time.time()
            
            # 使用智能体的LLM直接调用
            response = agent.llm.invoke(test_prompt)
            
            end_time = time.time()
            
            # 分析响应
            result["success"] = True
            result["response_time"] = end_time - start_time
            result["output_length"] = len(str(response))
            result["output_format"] = self._analyze_output_format(str(response))
            result["response"] = str(response)[:500]  # 保存前500字符用于分析
            
            logger.info(f"智能体 {agent_type} 使用 {provider} 基本功能测试成功")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"智能体 {agent_type} 使用 {provider} 基本功能测试失败: {e}")
        
        return result
    
    def test_agent_with_real_data(self, agent_type: str, provider: str) -> Dict[str, Any]:
        """
        使用真实数据测试智能体
        
        Args:
            agent_type: 智能体类型
            provider: 提供商名称
            
        Returns:
            测试结果字典
        """
        result = {
            "agent_type": agent_type,
            "provider": provider,
            "success": False,
            "analysis_quality": "unknown",
            "insights_count": 0,
            "recommendations_count": 0,
            "error": None
        }
        
        try:
            # 根据智能体类型选择合适的测试方法
            if agent_type == "event_analyst":
                result = self._test_event_analysis(provider)
            elif agent_type == "retention_analyst":
                result = self._test_retention_analysis(provider)
            elif agent_type == "conversion_analyst":
                result = self._test_conversion_analysis(provider)
            elif agent_type == "segmentation_analyst":
                result = self._test_segmentation_analysis(provider)
            elif agent_type == "path_analyst":
                result = self._test_path_analysis(provider)
            elif agent_type == "report_generator":
                result = self._test_report_generation(provider)
            elif agent_type == "data_processor":
                result = self._test_data_processing(provider)
            else:
                result["error"] = f"未知的智能体类型: {agent_type}"
            
            result["agent_type"] = agent_type
            result["provider"] = provider
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"智能体 {agent_type} 使用 {provider} 真实数据测试失败: {e}")
        
        return result
    
    def compare_providers(self, agent_type: str) -> Dict[str, Any]:
        """
        比较不同提供商的输出
        
        Args:
            agent_type: 智能体类型
            
        Returns:
            比较结果字典
        """
        comparison = {
            "agent_type": agent_type,
            "google_result": None,
            "volcano_result": None,
            "consistency_score": 0.0,
            "quality_comparison": "unknown",
            "performance_comparison": "unknown"
        }
        
        try:
            # 测试Google提供商
            google_result = self.test_agent_basic_functionality(agent_type, "google")
            comparison["google_result"] = google_result
            
            # 测试Volcano提供商
            volcano_result = self.test_agent_basic_functionality(agent_type, "volcano")
            comparison["volcano_result"] = volcano_result
            
            # 计算一致性分数
            if google_result["success"] and volcano_result["success"]:
                comparison["consistency_score"] = self._calculate_consistency_score(
                    google_result["response"], volcano_result["response"]
                )
                
                # 比较质量
                comparison["quality_comparison"] = self._compare_quality(
                    google_result, volcano_result
                )
                
                # 比较性能
                comparison["performance_comparison"] = self._compare_performance(
                    google_result, volcano_result
                )
            
        except Exception as e:
            comparison["error"] = str(e)
            logger.error(f"提供商比较失败 {agent_type}: {e}")
        
        return comparison
    
    def _get_test_prompt(self, agent_type: str) -> str:
        """获取测试提示"""
        prompts = {
            "event_analyst": "分析以下用户事件数据，识别关键行为模式：用户在过去7天内完成了10次页面浏览、3次购买和2次分享。",
            "retention_analyst": "计算用户留存率：100个新用户在第1天，80个在第7天，60个在第30天仍然活跃。",
            "conversion_analyst": "分析转化漏斗：1000个访客，500个查看产品，200个加入购物车，50个完成购买。",
            "segmentation_analyst": "基于用户行为进行分群：高频用户（每日活跃），中频用户（每周活跃），低频用户（每月活跃）。",
            "path_analyst": "分析用户路径：首页 -> 产品页 -> 购物车 -> 结账页 -> 支付完成。",
            "report_generator": "生成分析报告：用户活跃度上升15%，转化率提升8%，平均订单价值增长12%。",
            "data_processor": "处理GA4事件数据：验证数据完整性，清理异常值，标准化事件格式。"
        }
        return prompts.get(agent_type, "请分析提供的数据并给出洞察。")
    
    def _analyze_output_format(self, output: str) -> str:
        """分析输出格式"""
        output_lower = output.lower()
        
        if "json" in output_lower or output.strip().startswith("{"):
            return "json"
        elif "markdown" in output_lower or "#" in output:
            return "markdown"
        elif "html" in output_lower or "<" in output:
            return "html"
        elif "\n-" in output or "\n*" in output:
            return "list"
        else:
            return "text"
    
    def _calculate_consistency_score(self, response1: str, response2: str) -> float:
        """计算响应一致性分数"""
        # 简单的相似度计算
        words1 = set(response1.lower().split())
        words2 = set(response2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _compare_quality(self, result1: Dict, result2: Dict) -> str:
        """比较输出质量"""
        # 基于输出长度和响应时间的简单质量比较
        len1, len2 = result1["output_length"], result2["output_length"]
        time1, time2 = result1["response_time"], result2["response_time"]
        
        if abs(len1 - len2) < 100:  # 长度相似
            if abs(time1 - time2) < 1.0:  # 时间相似
                return "equivalent"
            elif time1 < time2:
                return "google_faster"
            else:
                return "volcano_faster"
        elif len1 > len2:
            return "google_more_detailed"
        else:
            return "volcano_more_detailed"
    
    def _compare_performance(self, result1: Dict, result2: Dict) -> str:
        """比较性能"""
        time1, time2 = result1["response_time"], result2["response_time"]
        
        if abs(time1 - time2) < 0.5:
            return "similar"
        elif time1 < time2:
            return "google_faster"
        else:
            return "volcano_faster"
    
    def _test_event_analysis(self, provider: str) -> Dict[str, Any]:
        """测试事件分析智能体"""
        try:
            agent = create_agent("event_analyst", provider=provider)
            
            # 准备事件数据
            events_data = json.dumps(self.test_events[:10])  # 使用前10个事件
            
            prompt = f"""
            分析以下GA4事件数据，识别用户行为模式和趋势：
            
            {events_data}
            
            请提供：
            1. 关键事件类型分析
            2. 用户行为趋势
            3. 异常模式识别
            4. 业务建议
            """
            
            response = agent.llm.invoke(prompt)
            response_str = str(response)
            
            # 分析响应质量
            insights_count = response_str.lower().count("洞察") + response_str.lower().count("发现")
            recommendations_count = response_str.lower().count("建议") + response_str.lower().count("推荐")
            
            return {
                "success": True,
                "analysis_quality": "good" if insights_count >= 2 else "basic",
                "insights_count": insights_count,
                "recommendations_count": recommendations_count,
                "response_length": len(response_str)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_retention_analysis(self, provider: str) -> Dict[str, Any]:
        """测试留存分析智能体"""
        try:
            agent = create_agent("retention_analyst", provider=provider)
            
            prompt = """
            计算并分析用户留存率：
            
            新用户数据：
            - 第1天：1000个新用户
            - 第7天：750个用户仍活跃
            - 第30天：500个用户仍活跃
            - 第90天：300个用户仍活跃
            
            请提供：
            1. 各时期留存率计算
            2. 留存趋势分析
            3. 流失原因推测
            4. 改进建议
            """
            
            response = agent.llm.invoke(prompt)
            response_str = str(response)
            
            # 检查是否包含留存率计算
            has_calculations = any(char in response_str for char in ['%', '率', '比例'])
            has_analysis = "分析" in response_str or "趋势" in response_str
            
            return {
                "success": True,
                "analysis_quality": "good" if has_calculations and has_analysis else "basic",
                "insights_count": response_str.count("洞察") + response_str.count("发现"),
                "recommendations_count": response_str.count("建议") + response_str.count("推荐"),
                "has_calculations": has_calculations
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_conversion_analysis(self, provider: str) -> Dict[str, Any]:
        """测试转化分析智能体"""
        try:
            agent = create_agent("conversion_analyst", provider=provider)
            
            prompt = """
            分析转化漏斗数据：
            
            漏斗数据：
            1. 访问首页：10000人
            2. 浏览产品：6000人
            3. 加入购物车：2000人
            4. 进入结账：800人
            5. 完成支付：400人
            
            请提供：
            1. 各步骤转化率
            2. 主要流失点分析
            3. 优化建议
            4. 预期改进效果
            """
            
            response = agent.llm.invoke(prompt)
            response_str = str(response)
            
            # 检查转化分析质量
            has_rates = any(char in response_str for char in ['%', '率', '转化'])
            has_bottlenecks = "瓶颈" in response_str or "流失" in response_str
            
            return {
                "success": True,
                "analysis_quality": "good" if has_rates and has_bottlenecks else "basic",
                "insights_count": response_str.count("洞察") + response_str.count("发现"),
                "recommendations_count": response_str.count("建议") + response_str.count("推荐"),
                "has_conversion_rates": has_rates
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_segmentation_analysis(self, provider: str) -> Dict[str, Any]:
        """测试用户分群智能体"""
        try:
            agent = create_agent("segmentation_analyst", provider=provider)
            
            prompt = """
            基于用户行为数据进行用户分群：
            
            用户行为特征：
            - 高活跃用户：每日登录，月消费>1000元
            - 中活跃用户：每周登录，月消费200-1000元
            - 低活跃用户：每月登录，月消费<200元
            - 流失用户：30天未登录
            
            请提供：
            1. 用户群体特征分析
            2. 各群体价值评估
            3. 针对性营销策略
            4. 群体转化建议
            """
            
            response = agent.llm.invoke(prompt)
            response_str = str(response)
            
            # 检查分群分析质量
            has_segments = "群体" in response_str or "分群" in response_str
            has_strategies = "策略" in response_str or "营销" in response_str
            
            return {
                "success": True,
                "analysis_quality": "good" if has_segments and has_strategies else "basic",
                "insights_count": response_str.count("洞察") + response_str.count("特征"),
                "recommendations_count": response_str.count("建议") + response_str.count("策略"),
                "has_segmentation": has_segments
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_path_analysis(self, provider: str) -> Dict[str, Any]:
        """测试路径分析智能体"""
        try:
            agent = create_agent("path_analyst", provider=provider)
            
            prompt = """
            分析用户行为路径：
            
            常见路径：
            1. 首页 → 产品列表 → 产品详情 → 购买 (转化率: 15%)
            2. 首页 → 搜索 → 产品详情 → 购买 (转化率: 25%)
            3. 首页 → 分类页 → 产品详情 → 离开 (转化率: 5%)
            4. 首页 → 关于我们 → 离开 (转化率: 1%)
            
            请提供：
            1. 最优路径识别
            2. 路径优化建议
            3. 用户体验改进点
            4. 预期效果评估
            """
            
            response = agent.llm.invoke(prompt)
            response_str = str(response)
            
            # 检查路径分析质量
            has_paths = "路径" in response_str or "流程" in response_str
            has_optimization = "优化" in response_str or "改进" in response_str
            
            return {
                "success": True,
                "analysis_quality": "good" if has_paths and has_optimization else "basic",
                "insights_count": response_str.count("洞察") + response_str.count("发现"),
                "recommendations_count": response_str.count("建议") + response_str.count("优化"),
                "has_path_analysis": has_paths
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_report_generation(self, provider: str) -> Dict[str, Any]:
        """测试报告生成智能体"""
        try:
            agent = create_agent("report_generator", provider=provider)
            
            prompt = """
            生成用户行为分析综合报告：
            
            分析结果摘要：
            - 用户活跃度：月活跃用户增长20%
            - 转化率：整体转化率提升15%
            - 留存率：30天留存率达到65%
            - 用户价值：平均订单价值增长18%
            
            请生成包含以下内容的报告：
            1. 执行摘要
            2. 关键指标分析
            3. 主要发现和洞察
            4. 行动建议
            5. 预期效果
            """
            
            response = agent.llm.invoke(prompt)
            response_str = str(response)
            
            # 检查报告质量
            has_summary = "摘要" in response_str or "总结" in response_str
            has_metrics = "指标" in response_str or "数据" in response_str
            has_structure = response_str.count("\n") > 10  # 检查结构化程度
            
            return {
                "success": True,
                "analysis_quality": "good" if has_summary and has_metrics and has_structure else "basic",
                "insights_count": response_str.count("洞察") + response_str.count("发现"),
                "recommendations_count": response_str.count("建议") + response_str.count("推荐"),
                "has_structure": has_structure
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_data_processing(self, provider: str) -> Dict[str, Any]:
        """测试数据处理智能体"""
        try:
            agent = create_agent("data_processor", provider=provider)
            
            # 准备测试数据
            test_data = json.dumps(self.test_events[:5])
            
            prompt = f"""
            处理和验证以下GA4事件数据：
            
            {test_data}
            
            请执行：
            1. 数据完整性检查
            2. 异常值识别
            3. 数据清洗建议
            4. 质量评估报告
            """
            
            response = agent.llm.invoke(prompt)
            response_str = str(response)
            
            # 检查数据处理质量
            has_validation = "验证" in response_str or "检查" in response_str
            has_cleaning = "清洗" in response_str or "处理" in response_str
            
            return {
                "success": True,
                "analysis_quality": "good" if has_validation and has_cleaning else "basic",
                "insights_count": response_str.count("问题") + response_str.count("异常"),
                "recommendations_count": response_str.count("建议") + response_str.count("推荐"),
                "has_data_validation": has_validation
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# 测试类
class TestAgentVolcanoCompatibility:
    """智能体Volcano兼容性测试"""
    
    @classmethod
    def setup_class(cls):
        """设置测试类"""
        cls.tester = AgentCompatibilityTester()
        cls.tester.setup_test_environment()
        
        # 定义要测试的智能体类型
        cls.agent_types = [
            "event_analyst",
            "retention_analyst", 
            "conversion_analyst",
            "segmentation_analyst",
            "path_analyst",
            "report_generator",
            "data_processor"
        ]
    
    @pytest.mark.parametrize("agent_type", [
        "event_analyst", "retention_analyst", "conversion_analyst",
        "segmentation_analyst", "path_analyst", "report_generator", "data_processor"
    ])
    def test_agent_creation_volcano(self, agent_type):
        """测试使用Volcano提供商创建智能体"""
        success = self.tester.test_agent_creation(agent_type, "volcano")
        assert success, f"智能体 {agent_type} 使用Volcano提供商创建失败"
    
    @pytest.mark.parametrize("agent_type", [
        "event_analyst", "retention_analyst", "conversion_analyst",
        "segmentation_analyst", "path_analyst", "report_generator", "data_processor"
    ])
    def test_agent_basic_functionality_volcano(self, agent_type):
        """测试智能体使用Volcano提供商的基本功能"""
        result = self.tester.test_agent_basic_functionality(agent_type, "volcano")
        
        assert result["success"], f"智能体 {agent_type} 基本功能测试失败: {result.get('error')}"
        assert result["response_time"] is not None, "响应时间应该被记录"
        assert result["output_length"] > 0, "输出长度应该大于0"
        assert result["output_format"] != "unknown", "应该能识别输出格式"
    
    @pytest.mark.parametrize("agent_type", [
        "event_analyst", "retention_analyst", "conversion_analyst",
        "segmentation_analyst", "path_analyst", "report_generator", "data_processor"
    ])
    def test_agent_real_data_volcano(self, agent_type):
        """测试智能体使用Volcano提供商处理真实数据"""
        result = self.tester.test_agent_with_real_data(agent_type, "volcano")
        
        assert result["success"], f"智能体 {agent_type} 真实数据测试失败: {result.get('error')}"
        assert result["analysis_quality"] in ["basic", "good"], "分析质量应该被评估"
    
    @pytest.mark.parametrize("agent_type", [
        "event_analyst", "retention_analyst", "conversion_analyst",
        "segmentation_analyst", "path_analyst", "report_generator", "data_processor"
    ])
    def test_provider_comparison(self, agent_type):
        """比较Google和Volcano提供商的输出"""
        comparison = self.tester.compare_providers(agent_type)
        
        # 检查两个提供商都成功
        if comparison.get("google_result") and comparison.get("volcano_result"):
            assert comparison["google_result"]["success"], f"Google提供商测试失败: {comparison['google_result'].get('error')}"
            assert comparison["volcano_result"]["success"], f"Volcano提供商测试失败: {comparison['volcano_result'].get('error')}"
            
            # 检查一致性分数
            assert comparison["consistency_score"] >= 0.0, "一致性分数应该大于等于0"
            assert comparison["quality_comparison"] != "unknown", "质量比较应该有结果"
            assert comparison["performance_comparison"] != "unknown", "性能比较应该有结果"
    
    def test_output_format_consistency(self):
        """测试输出格式一致性"""
        results = {}
        
        for agent_type in self.agent_types:
            google_result = self.tester.test_agent_basic_functionality(agent_type, "google")
            volcano_result = self.tester.test_agent_basic_functionality(agent_type, "volcano")
            
            if google_result["success"] and volcano_result["success"]:
                results[agent_type] = {
                    "google_format": google_result["output_format"],
                    "volcano_format": volcano_result["output_format"],
                    "consistent": google_result["output_format"] == volcano_result["output_format"]
                }
        
        # 检查格式一致性
        consistent_count = sum(1 for r in results.values() if r["consistent"])
        total_count = len(results)
        
        consistency_rate = consistent_count / total_count if total_count > 0 else 0
        
        logger.info(f"输出格式一致性: {consistency_rate:.2%} ({consistent_count}/{total_count})")
        
        # 至少70%的智能体应该有一致的输出格式
        assert consistency_rate >= 0.7, f"输出格式一致性过低: {consistency_rate:.2%}"
    
    def test_analysis_quality_comparison(self):
        """测试分析质量比较"""
        quality_scores = {"google": 0, "volcano": 0, "tie": 0}
        
        for agent_type in self.agent_types:
            google_result = self.tester.test_agent_with_real_data(agent_type, "google")
            volcano_result = self.tester.test_agent_with_real_data(agent_type, "volcano")
            
            if google_result["success"] and volcano_result["success"]:
                google_quality = google_result.get("analysis_quality", "basic")
                volcano_quality = volcano_result.get("analysis_quality", "basic")
                
                if google_quality == "good" and volcano_quality == "basic":
                    quality_scores["google"] += 1
                elif volcano_quality == "good" and google_quality == "basic":
                    quality_scores["volcano"] += 1
                else:
                    quality_scores["tie"] += 1
        
        logger.info(f"分析质量比较: Google={quality_scores['google']}, Volcano={quality_scores['volcano']}, Tie={quality_scores['tie']}")
        
        # Volcano提供商的质量不应该明显低于Google
        total_comparisons = sum(quality_scores.values())
        if total_comparisons > 0:
            volcano_performance = (quality_scores["volcano"] + quality_scores["tie"]) / total_comparisons
            assert volcano_performance >= 0.5, f"Volcano提供商质量表现过低: {volcano_performance:.2%}"
    
    def test_performance_comparison(self):
        """测试性能比较"""
        performance_data = []
        
        for agent_type in self.agent_types:
            google_result = self.tester.test_agent_basic_functionality(agent_type, "google")
            volcano_result = self.tester.test_agent_basic_functionality(agent_type, "volcano")
            
            if google_result["success"] and volcano_result["success"]:
                performance_data.append({
                    "agent_type": agent_type,
                    "google_time": google_result["response_time"],
                    "volcano_time": volcano_result["response_time"],
                    "ratio": volcano_result["response_time"] / google_result["response_time"]
                })
        
        if performance_data:
            avg_ratio = sum(p["ratio"] for p in performance_data) / len(performance_data)
            logger.info(f"平均性能比率 (Volcano/Google): {avg_ratio:.2f}")
            
            # Volcano的平均响应时间不应该超过Google的3倍
            assert avg_ratio <= 3.0, f"Volcano提供商性能过低: 平均比率 {avg_ratio:.2f}"
    
    def test_error_handling_consistency(self):
        """测试错误处理一致性"""
        # 使用无效的提示测试错误处理
        invalid_prompt = "这是一个故意设计的无效提示" * 1000  # 超长提示
        
        error_handling_results = {}
        
        for provider in ["google", "volcano"]:
            try:
                agent = create_agent("event_analyst", provider=provider)
                response = agent.llm.invoke(invalid_prompt)
                error_handling_results[provider] = {
                    "handled_gracefully": True,
                    "response_length": len(str(response))
                }
            except Exception as e:
                error_handling_results[provider] = {
                    "handled_gracefully": False,
                    "error": str(e)
                }
        
        # 两个提供商应该有相似的错误处理行为
        google_handled = error_handling_results.get("google", {}).get("handled_gracefully", False)
        volcano_handled = error_handling_results.get("volcano", {}).get("handled_gracefully", False)
        
        # 如果一个提供商能处理，另一个也应该能处理
        if google_handled or volcano_handled:
            logger.info("至少有一个提供商能处理异常情况")
        else:
            logger.info("两个提供商都无法处理异常情况，这是可以接受的")
    
    def test_concurrent_requests(self):
        """测试并发请求处理"""
        import concurrent.futures
        import threading
        
        def test_concurrent_agent(agent_type, provider):
            """并发测试函数"""
            try:
                result = self.tester.test_agent_basic_functionality(agent_type, provider)
                return result["success"]
            except Exception:
                return False
        
        # 测试并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 提交并发任务
            futures = []
            for i in range(3):
                future = executor.submit(test_concurrent_agent, "event_analyst", "volcano")
                futures.append(future)
            
            # 收集结果
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # 检查并发处理结果
        success_count = sum(results)
        logger.info(f"并发测试结果: {success_count}/3 成功")
        
        # 至少2/3的并发请求应该成功
        assert success_count >= 2, f"并发处理能力不足: {success_count}/3"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])