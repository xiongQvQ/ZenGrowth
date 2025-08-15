"""
漏斗分析智能体模块

该模块实现FunnelAnalysisAgent类，负责用户转化漏斗分析和优化。
智能体集成了漏斗分析引擎，提供漏斗构建、转化率计算、瓶颈识别和优化建议功能。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from engines.funnel_analysis_engine import FunnelAnalysisEngine
from tools.data_storage_manager import DataStorageManager

# Try to import CrewAI components, but handle import errors gracefully
try:
    from crewai import Agent
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field
    from config.crew_config import get_llm
    CREWAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI not available: {e}. Agent will work in standalone mode.")
    CREWAI_AVAILABLE = False
    
    # Create mock classes for compatibility
    class BaseTool:
        def __init__(self):
            self.name = ""
            self.description = ""
            
    class Agent:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)


class FunnelBuilderTool(BaseTool):
    """漏斗构建工具"""
    
    name: str = "funnel_builder"
    description: str = "构建和分析用户转化漏斗，计算各步骤的转化率和流失情况"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', FunnelAnalysisEngine(storage_manager))
    
    def _run(self, funnel_steps: List[str], funnel_name: str = "custom_funnel", 
             time_window: int = 7) -> Dict[str, Any]:
        """
        执行漏斗构建分析
        
        Args:
            funnel_steps: 漏斗步骤列表
            funnel_name: 漏斗名称
            time_window: 分析时间窗口（天）
            
        Returns:
            漏斗分析结果
        """
        try:
            result = self.engine.build_conversion_funnel(
                funnel_steps=funnel_steps,
                funnel_name=funnel_name,
                time_window_days=time_window
            )
            
            return {
                'success': True,
                'funnel_name': result.funnel_name,
                'total_users': result.total_users,
                'conversion_rate': result.overall_conversion_rate,
                'total_conversions': result.total_conversions,
                'avg_time_to_convert': result.avg_time_to_convert,
                'bottleneck_step': result.bottleneck_step,
                'steps': [
                    {
                        'step_name': step.step_name,
                        'step_order': step.step_order,
                        'users_count': step.users_count,
                        'conversion_rate': step.conversion_rate,
                        'drop_off_rate': step.drop_off_rate,
                        'avg_time_to_next': step.avg_time_to_next_step
                    }
                    for step in result.steps
                ],
                'drop_off_analysis': result.drop_off_analysis
            }
            
        except Exception as e:
            logger.error(f"漏斗构建失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'funnel_steps': funnel_steps
            }


class FunnelComparisonTool(BaseTool):
    """漏斗对比工具"""
    
    name: str = "funnel_comparison"
    description: str = "对比不同漏斗的表现，识别最优转化路径"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', FunnelAnalysisEngine(storage_manager))
    
    def _run(self, funnel_definitions: Dict[str, List[str]], 
             comparison_period: int = 30) -> Dict[str, Any]:
        """
        执行漏斗对比分析
        
        Args:
            funnel_definitions: 漏斗定义字典 {funnel_name: [steps...]}
            comparison_period: 对比时间周期（天）
            
        Returns:
            漏斗对比结果
        """
        try:
            results = {}
            
            for funnel_name, steps in funnel_definitions.items():
                result = self.engine.build_conversion_funnel(
                    funnel_steps=steps,
                    funnel_name=funnel_name,
                    time_window_days=comparison_period
                )
                results[funnel_name] = {
                    'conversion_rate': result.overall_conversion_rate,
                    'total_users': result.total_users,
                    'total_conversions': result.total_conversions,
                    'avg_time_to_convert': result.avg_time_to_convert,
                    'bottleneck_step': result.bottleneck_step
                }
            
            # 找出最佳漏斗
            best_funnel = max(results.items(), 
                            key=lambda x: x[1]['conversion_rate'])
            
            return {
                'success': True,
                'comparison_results': results,
                'best_funnel': best_funnel[0],
                'best_conversion_rate': best_funnel[1]['conversion_rate']
            }
            
        except Exception as e:
            logger.error(f"漏斗对比失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class BottleneckAnalyzerTool(BaseTool):
    """瓶颈分析工具"""
    
    name: str = "bottleneck_analyzer"
    description: str = "识别转化漏斗中的关键瓶颈，提供优化建议"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', FunnelAnalysisEngine(storage_manager))
    
    def _run(self, funnel_steps: List[str], 
             threshold: float = 0.2) -> Dict[str, Any]:
        """
        执行瓶颈分析
        
        Args:
            funnel_steps: 漏斗步骤
            threshold: 瓶颈识别阈值（转化率低于此值为瓶颈）
            
        Returns:
            瓶颈分析结果
        """
        try:
            result = self.engine.identify_bottlenecks(
                funnel_steps=funnel_steps,
                drop_off_threshold=threshold
            )
            
            return {
                'success': True,
                'bottlenecks': [
                    {
                        'step_name': bottleneck.step_name,
                        'step_order': bottleneck.step_order,
                        'drop_off_rate': bottleneck.drop_off_rate,
                        'users_lost': bottleneck.users_lost,
                        'impact_score': bottleneck.impact_score,
                        'optimization_priority': bottleneck.optimization_priority
                    }
                    for bottleneck in result.bottlenecks
                ],
                'total_revenue_impact': result.total_revenue_impact,
                'optimization_recommendations': result.recommendations
            }
            
        except Exception as e:
            logger.error(f"瓶颈分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class FunnelOptimizationTool(BaseTool):
    """漏斗优化工具"""
    
    name: str = "funnel_optimization"
    description: str = "基于分析结果提供漏斗优化策略和建议"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', FunnelAnalysisEngine(storage_manager))
    
    def _run(self, current_funnel: List[str], 
             optimization_targets: Dict[str, float]) -> Dict[str, Any]:
        """
        执行漏斗优化分析
        
        Args:
            current_funnel: 当前漏斗步骤
            optimization_targets: 优化目标 {step_name: target_conversion_rate}
            
        Returns:
            优化建议和策略
        """
        try:
            # 分析当前漏斗
            current_result = self.engine.build_conversion_funnel(current_funnel)
            
            # 生成优化建议
            optimization_plan = self.engine.generate_optimization_plan(
                current_result=current_result,
                targets=optimization_targets
            )
            
            return {
                'success': True,
                'current_performance': {
                    'conversion_rate': current_result.overall_conversion_rate,
                    'bottlenecks': current_result.bottleneck_step
                },
                'optimization_plan': {
                    'priority_steps': optimization_plan.priority_steps,
                    'expected_improvements': optimization_plan.expected_improvements,
                    'implementation_phases': optimization_plan.implementation_phases,
                    'estimated_impact': optimization_plan.estimated_impact
                },
                'a_b_test_suggestions': optimization_plan.ab_test_suggestions
            }
            
        except Exception as e:
            logger.error(f"漏斗优化分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class FunnelAnalysisAgent:
    """漏斗分析智能体"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """
        初始化漏斗分析智能体
        
        Args:
            storage_manager: 数据存储管理器
        """
        self.storage_manager = storage_manager
        self.engine = FunnelAnalysisEngine(storage_manager)
        
        # 初始化工具
        self.funnel_builder = FunnelBuilderTool(storage_manager)
        self.funnel_comparator = FunnelComparisonTool(storage_manager)
        self.bottleneck_analyzer = BottleneckAnalyzerTool(storage_manager)
        self.optimization_tool = FunnelOptimizationTool(storage_manager)
        
        # 创建CrewAI智能体
        if CREWAI_AVAILABLE:
            self._create_crewai_agent()
        
        logger.info("漏斗分析智能体初始化完成")
    
    def _create_crewai_agent(self):
        """创建CrewAI智能体"""
        try:
            self.agent = Agent(
                role="漏斗分析专家",
                goal="构建和优化用户转化漏斗，提升整体转化率和用户体验",
                backstory="""
                你是一位资深的转化漏斗分析专家，拥有超过10年的用户行为分析和转化优化经验。
                你精通各种转化漏斗模型的构建和分析，能够准确识别转化路径中的关键瓶颈，
                并提供数据驱动的优化建议。你的分析帮助众多企业显著提升了用户转化率，
                平均转化率提升达到30%以上。你特别擅长电商、SaaS和内容平台的转化优化。
                """,
                tools=[
                    self.funnel_builder,
                    self.funnel_comparator,
                    self.bottleneck_analyzer,
                    self.optimization_tool
                ],
                llm=get_llm(),
                verbose=True,
                allow_delegation=False,
                max_iter=5
            )
        except Exception as e:
            logger.warning(f"CrewAI智能体创建失败: {e}")
            self.agent = None
    
    def analyze_funnel(self, funnel_steps: List[str], funnel_name: str = "custom_funnel",
                      time_window: int = 7) -> Dict[str, Any]:
        """
        分析转化漏斗
        
        Args:
            funnel_steps: 漏斗步骤列表
            funnel_name: 漏斗名称
            time_window: 时间窗口（天）
            
        Returns:
            漏斗分析结果
        """
        logger.info(f"开始分析漏斗: {funnel_name}")
        
        try:
            result = self.engine.build_conversion_funnel(
                funnel_steps=funnel_steps,
                funnel_name=funnel_name,
                time_window_days=time_window
            )
            
            return {
                'success': True,
                'funnel_name': result.funnel_name,
                'total_users': result.total_users,
                'overall_conversion_rate': result.overall_conversion_rate,
                'total_conversions': result.total_conversions,
                'avg_time_to_convert': result.avg_time_to_convert,
                'bottleneck_step': result.bottleneck_step,
                'steps': [
                    {
                        'step_name': step.step_name,
                        'step_order': step.step_order,
                        'users_count': step.users_count,
                        'conversion_rate': step.conversion_rate,
                        'drop_off_rate': step.drop_off_rate,
                        'avg_time_to_next_step': step.avg_time_to_next_step
                    }
                    for step in result.steps
                ],
                'drop_off_analysis': result.drop_off_analysis,
                'optimization_suggestions': result.optimization_suggestions
            }
            
        except Exception as e:
            logger.error(f"漏斗分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'funnel_steps': funnel_steps
            }
    
    def compare_funnels(self, funnel_definitions: Dict[str, List[str]], 
                       comparison_period: int = 30) -> Dict[str, Any]:
        """
        对比多个漏斗
        
        Args:
            funnel_definitions: 漏斗定义
            comparison_period: 对比周期
            
        Returns:
            漏斗对比结果
        """
        logger.info("开始对比多个漏斗")
        
        try:
            comparison_results = {}
            
            for funnel_name, steps in funnel_definitions.items():
                result = self.engine.build_conversion_funnel(
                    funnel_steps=steps,
                    funnel_name=funnel_name,
                    time_window_days=comparison_period
                )
                comparison_results[funnel_name] = {
                    'conversion_rate': result.overall_conversion_rate,
                    'total_users': result.total_users,
                    'total_conversions': result.total_conversions,
                    'avg_time_to_convert': result.avg_time_to_convert,
                    'bottleneck_step': result.bottleneck_step,
                    'performance_rank': 0
                }
            
            # 按转化率排序
            sorted_funnels = sorted(comparison_results.items(), 
                                  key=lambda x: x[1]['conversion_rate'], reverse=True)
            
            # 添加排名
            for rank, (funnel_name, data) in enumerate(sorted_funnels, 1):
                comparison_results[funnel_name]['performance_rank'] = rank
            
            best_funnel = sorted_funnels[0] if sorted_funnels else None
            
            return {
                'success': True,
                'comparison_results': comparison_results,
                'best_funnel': best_funnel[0] if best_funnel else None,
                'best_conversion_rate': best_funnel[1]['conversion_rate'] if best_funnel else 0,
                'recommendations': [
                    f"推荐使用表现最佳的漏斗: {best_funnel[0]}" if best_funnel else "需要更多数据进行分析"
                ]
            }
            
        except Exception as e:
            logger.error(f"漏斗对比失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def identify_bottlenecks(self, funnel_steps: List[str], 
                           threshold: float = 0.2) -> Dict[str, Any]:
        """
        识别转化瓶颈
        
        Args:
            funnel_steps: 漏斗步骤
            threshold: 瓶颈识别阈值
            
        Returns:
            瓶颈分析结果
        """
        logger.info("开始识别转化瓶颈")
        
        try:
            result = self.engine.identify_bottlenecks(
                funnel_steps=funnel_steps,
                drop_off_threshold=threshold
            )
            
            return {
                'success': True,
                'bottlenecks': [
                    {
                        'step_name': bottleneck.step_name,
                        'step_order': bottleneck.step_order,
                        'drop_off_rate': bottleneck.drop_off_rate,
                        'users_lost': bottleneck.users_lost,
                        'impact_score': bottleneck.impact_score,
                        'revenue_impact': bottleneck.revenue_impact,
                        'optimization_priority': bottleneck.optimization_priority
                    }
                    for bottleneck in result.bottlenecks
                ],
                'total_revenue_impact': result.total_revenue_impact,
                'optimization_recommendations': result.recommendations,
                'urgent_fixes': result.urgent_fixes
            }
            
        except Exception as e:
            logger.error(f"瓶颈识别失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def comprehensive_funnel_analysis(self, 
                                    funnel_steps: Optional[List[str]] = None,
                                    include_comparison: bool = False) -> Dict[str, Any]:
        """
        执行综合漏斗分析
        
        Args:
            funnel_steps: 自定义漏斗步骤，如果为None使用默认漏斗
            include_comparison: 是否包含对比分析
            
        Returns:
            综合分析结果
        """
        logger.info("开始执行综合漏斗分析")
        
        try:
            # 使用默认漏斗步骤
            if funnel_steps is None:
                funnel_steps = [
                    'page_view',
                    'view_item',
                    'add_to_cart',
                    'begin_checkout',
                    'purchase'
                ]
            
            # 基础漏斗分析
            funnel_result = self.analyze_funnel(funnel_steps)
            
            # 瓶颈分析
            bottleneck_result = self.identify_bottlenecks(funnel_steps)
            
            # 对比分析（如果需要）
            comparison_result = None
            if include_comparison:
                comparison_definitions = {
                    'standard_funnel': funnel_steps,
                    'simplified_funnel': funnel_steps[:3],
                    'extended_funnel': funnel_steps + ['add_payment_info']
                }
                comparison_result = self.compare_funnels(comparison_definitions)
            
            # 生成综合洞察
            insights = []
            recommendations = []
            
            if funnel_result.get('success'):
                conversion_rate = funnel_result['overall_conversion_rate']
                insights.append(f"整体转化率为 {conversion_rate:.2%}")
                
                if conversion_rate < 0.1:
                    recommendations.append("转化率较低，建议优先优化用户体验")
                elif conversion_rate > 0.3:
                    insights.append("转化率表现良好")
            
            if bottleneck_result.get('success') and bottleneck_result['bottlenecks']:
                worst_bottleneck = bottleneck_result['bottlenecks'][0]
                insights.append(f"主要瓶颈在 {worst_bottleneck['step_name']}，流失率 {worst_bottleneck['drop_off_rate']:.2%}")
                recommendations.append(f"优先优化步骤: {worst_bottleneck['step_name']}")
            
            return {
                'success': True,
                'analysis_type': 'comprehensive_funnel_analysis',
                'funnel_analysis': funnel_result,
                'bottleneck_analysis': bottleneck_result,
                'comparison_analysis': comparison_result,
                'insights': insights,
                'recommendations': recommendations,
                'summary': {
                    'total_steps_analyzed': len(funnel_steps),
                    'analysis_completed': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"综合漏斗分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        获取智能体状态
        
        Returns:
            智能体状态信息
        """
        return {
            'agent_type': 'FunnelAnalysisAgent',
            'crewai_available': CREWAI_AVAILABLE,
            'crewai_agent_created': hasattr(self, 'agent') and self.agent is not None,
            'storage_manager_available': self.storage_manager is not None,
            'engine_available': self.engine is not None,
            'tools_count': 4,
            'tools': ['funnel_builder', 'funnel_comparison', 'bottleneck_analyzer', 'optimization_tool'],
            'supported_analyses': [
                'conversion_funnel_analysis',
                'bottleneck_identification',
                'funnel_comparison',
                'optimization_recommendations'
            ]
        }


# 为了向后兼容，提供一个简单的工厂函数
def create_funnel_analysis_agent(storage_manager: DataStorageManager = None) -> FunnelAnalysisAgent:
    """
    创建漏斗分析智能体实例
    
    Args:
        storage_manager: 数据存储管理器
        
    Returns:
        漏斗分析智能体实例
    """
    return FunnelAnalysisAgent(storage_manager)