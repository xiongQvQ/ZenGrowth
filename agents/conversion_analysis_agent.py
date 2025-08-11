"""
转化分析智能体模块

该模块实现ConversionAnalysisAgent类，负责转化漏斗分析和转化优化。
智能体集成了转化分析引擎，提供漏斗构建、转化率计算和瓶颈识别功能。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from engines.conversion_analysis_engine import ConversionAnalysisEngine
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


class FunnelAnalysisTool(BaseTool):
    """漏斗分析工具"""
    
    name: str = "funnel_analysis"
    description: str = "构建转化漏斗，分析各步骤转化率和用户流失情况"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        self.engine = ConversionAnalysisEngine(storage_manager)
        
    def _run(self, funnel_steps: List[str], funnel_name: str = "custom_funnel", time_window_hours: int = 24) -> Dict[str, Any]:
        """
        执行漏斗分析
        
        Args:
            funnel_steps: 漏斗步骤列表
            funnel_name: 漏斗名称
            time_window_hours: 时间窗口（小时）
            
        Returns:
            漏斗分析结果
        """
        try:
            logger.info(f"开始漏斗分析，漏斗: {funnel_name}, 步骤: {funnel_steps}")
            
            # 构建转化漏斗
            funnel = self.engine.build_conversion_funnel(
                funnel_steps=funnel_steps,
                funnel_name=funnel_name,
                time_window_hours=time_window_hours
            )
            
            # 转换结果为可序列化格式
            serialized_funnel = {
                'funnel_name': funnel.funnel_name,
                'overall_conversion_rate': funnel.overall_conversion_rate,
                'total_users_entered': funnel.total_users_entered,
                'total_users_converted': funnel.total_users_converted,
                'avg_completion_time': funnel.avg_completion_time,
                'bottleneck_step': funnel.bottleneck_step,
                'steps': []
            }
            
            for step in funnel.steps:
                serialized_funnel['steps'].append({
                    'step_name': step.step_name,
                    'step_order': step.step_order,
                    'total_users': step.total_users,
                    'conversion_rate': step.conversion_rate,
                    'drop_off_rate': step.drop_off_rate,
                    'avg_time_to_next_step': step.avg_time_to_next_step,
                    'median_time_to_next_step': step.median_time_to_next_step
                })
            
            # 生成分析摘要
            summary = self._generate_funnel_summary(serialized_funnel)
            
            result = {
                'status': 'success',
                'analysis_type': 'funnel_analysis',
                'funnel': serialized_funnel,
                'summary': summary,
                'insights': self._generate_funnel_insights(serialized_funnel)
            }
            
            logger.info(f"漏斗分析完成，整体转化率: {funnel.overall_conversion_rate:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"漏斗分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'funnel_analysis'
            }
            
    def _generate_funnel_summary(self, funnel: Dict[str, Any]) -> Dict[str, Any]:
        """生成漏斗分析摘要"""
        steps = funnel.get('steps', [])
        if not steps:
            return {}
            
        # 计算总体统计
        conversion_rates = [step['conversion_rate'] for step in steps[1:]]  # 排除第一步
        drop_off_rates = [step['drop_off_rate'] for step in steps[1:]]
        
        # 找出最大流失步骤
        max_drop_off_step = max(steps[1:], key=lambda x: x['drop_off_rate']) if len(steps) > 1 else None
        
        return {
            'total_steps': len(steps),
            'users_entered': funnel['total_users_entered'],
            'users_converted': funnel['total_users_converted'],
            'overall_conversion_rate': funnel['overall_conversion_rate'],
            'avg_step_conversion_rate': sum(conversion_rates) / len(conversion_rates) if conversion_rates else 0,
            'max_drop_off_step': {
                'step_name': max_drop_off_step['step_name'],
                'drop_off_rate': max_drop_off_step['drop_off_rate']
            } if max_drop_off_step else None,
            'bottleneck_identified': funnel['bottleneck_step'] is not None,
            'avg_completion_time_minutes': funnel['avg_completion_time'] / 60 if funnel['avg_completion_time'] else None
        }
        
    def _generate_funnel_insights(self, funnel: Dict[str, Any]) -> List[str]:
        """生成漏斗分析洞察"""
        insights = []
        steps = funnel.get('steps', [])
        
        if not steps:
            return ["漏斗数据不足，无法生成洞察"]
            
        # 分析整体转化率
        overall_rate = funnel['overall_conversion_rate']
        if overall_rate < 0.1:
            insights.append(f"整体转化率较低({overall_rate:.1%})，需要重点优化")
        elif overall_rate > 0.3:
            insights.append(f"整体转化率良好({overall_rate:.1%})")
            
        # 分析瓶颈步骤
        if funnel['bottleneck_step']:
            insights.append(f"识别到瓶颈步骤: {funnel['bottleneck_step']}，建议重点优化")
            
        # 分析最大流失点
        if len(steps) > 1:
            max_drop_off = max(steps[1:], key=lambda x: x['drop_off_rate'])
            if max_drop_off['drop_off_rate'] > 0.5:
                insights.append(f"步骤'{max_drop_off['step_name']}'流失率过高({max_drop_off['drop_off_rate']:.1%})")
                
        # 分析完成时间
        if funnel['avg_completion_time']:
            completion_hours = funnel['avg_completion_time'] / 3600
            if completion_hours > 24:
                insights.append(f"平均完成时间较长({completion_hours:.1f}小时)，可能影响转化")
            elif completion_hours < 1:
                insights.append(f"用户转化速度较快({completion_hours:.1f}小时)")
                
        return insights


class ConversionRateAnalysisTool(BaseTool):
    """转化率分析工具"""
    
    name: str = "conversion_rate_analysis"
    description: str = "计算各种转化率指标，分析转化趋势和模式"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        self.engine = ConversionAnalysisEngine(storage_manager)
        
    def _run(self, funnel_definitions: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """
        执行转化率分析
        
        Args:
            funnel_definitions: 自定义漏斗定义
            
        Returns:
            转化率分析结果
        """
        try:
            logger.info("开始转化率分析")
            
            # 执行转化率计算
            conversion_result = self.engine.calculate_conversion_rates(
                funnel_definitions=funnel_definitions
            )
            
            # 转换结果为可序列化格式
            serialized_result = {
                'funnels': [],
                'conversion_metrics': conversion_result.conversion_metrics,
                'bottleneck_analysis': conversion_result.bottleneck_analysis,
                'time_analysis': conversion_result.time_analysis,
                'segment_analysis': conversion_result.segment_analysis
            }
            
            # 序列化漏斗数据
            for funnel in conversion_result.funnels:
                serialized_funnel = {
                    'funnel_name': funnel.funnel_name,
                    'overall_conversion_rate': funnel.overall_conversion_rate,
                    'total_users_entered': funnel.total_users_entered,
                    'total_users_converted': funnel.total_users_converted,
                    'avg_completion_time': funnel.avg_completion_time,
                    'bottleneck_step': funnel.bottleneck_step,
                    'steps': []
                }
                
                for step in funnel.steps:
                    serialized_funnel['steps'].append({
                        'step_name': step.step_name,
                        'step_order': step.step_order,
                        'total_users': step.total_users,
                        'conversion_rate': step.conversion_rate,
                        'drop_off_rate': step.drop_off_rate
                    })
                    
                serialized_result['funnels'].append(serialized_funnel)
            
            # 生成分析摘要
            summary = self._generate_conversion_summary(serialized_result)
            
            result = {
                'status': 'success',
                'analysis_type': 'conversion_rate_analysis',
                'results': serialized_result,
                'summary': summary,
                'insights': self._generate_conversion_insights(serialized_result)
            }
            
            logger.info(f"转化率分析完成，分析了{len(serialized_result['funnels'])}个漏斗")
            return result
            
        except Exception as e:
            logger.error(f"转化率分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'conversion_rate_analysis'
            }
            
    def _generate_conversion_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成转化率分析摘要"""
        funnels = results.get('funnels', [])
        metrics = results.get('conversion_metrics', {})
        
        if not funnels:
            return {'total_funnels': 0}
            
        # 计算漏斗统计
        conversion_rates = [f['overall_conversion_rate'] for f in funnels]
        
        return {
            'total_funnels_analyzed': len(funnels),
            'avg_conversion_rate': sum(conversion_rates) / len(conversion_rates),
            'best_performing_funnel': max(funnels, key=lambda x: x['overall_conversion_rate'])['funnel_name'],
            'worst_performing_funnel': min(funnels, key=lambda x: x['overall_conversion_rate'])['funnel_name'],
            'funnels_with_bottlenecks': sum(1 for f in funnels if f['bottleneck_step']),
            'overall_conversion_metrics': metrics
        }
        
    def _generate_conversion_insights(self, results: Dict[str, Any]) -> List[str]:
        """生成转化率分析洞察"""
        insights = []
        funnels = results.get('funnels', [])
        bottleneck_analysis = results.get('bottleneck_analysis', {})
        
        if not funnels:
            return ["没有足够的转化数据进行分析"]
            
        # 分析最佳和最差漏斗
        best_funnel = max(funnels, key=lambda x: x['overall_conversion_rate'])
        worst_funnel = min(funnels, key=lambda x: x['overall_conversion_rate'])
        
        insights.append(f"最佳转化漏斗: {best_funnel['funnel_name']} ({best_funnel['overall_conversion_rate']:.1%})")
        insights.append(f"最差转化漏斗: {worst_funnel['funnel_name']} ({worst_funnel['overall_conversion_rate']:.1%})")
        
        # 分析常见瓶颈
        common_bottlenecks = bottleneck_analysis.get('common_bottlenecks', [])
        if common_bottlenecks:
            top_bottleneck = common_bottlenecks[0]
            insights.append(f"最常见瓶颈步骤: {top_bottleneck['step']} (出现在{top_bottleneck['frequency']}个漏斗中)")
            
        # 分析转化率分布
        conversion_rates = [f['overall_conversion_rate'] for f in funnels]
        avg_rate = sum(conversion_rates) / len(conversion_rates)
        
        high_performing = [f for f in funnels if f['overall_conversion_rate'] > avg_rate * 1.5]
        if high_performing:
            insights.append(f"高性能漏斗({len(high_performing)}个)平均转化率超过整体平均值50%")
            
        return insights


class BottleneckIdentificationTool(BaseTool):
    """瓶颈识别工具"""
    
    name: str = "bottleneck_identification"
    description: str = "识别转化路径中的瓶颈和流失点，提供优化建议"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        self.engine = ConversionAnalysisEngine(storage_manager)
        
    def _run(self, funnel_steps: List[str] = None) -> Dict[str, Any]:
        """
        执行瓶颈识别
        
        Args:
            funnel_steps: 要分析的漏斗步骤
            
        Returns:
            瓶颈识别结果
        """
        try:
            logger.info(f"开始瓶颈识别，分析步骤: {funnel_steps}")
            
            # 执行流失点识别
            drop_off_analysis = self.engine.identify_drop_off_points(
                funnel_steps=funnel_steps
            )
            
            # 生成分析摘要
            summary = self._generate_bottleneck_summary(drop_off_analysis)
            
            result = {
                'status': 'success',
                'analysis_type': 'bottleneck_identification',
                'drop_off_analysis': drop_off_analysis,
                'summary': summary,
                'insights': self._generate_bottleneck_insights(drop_off_analysis),
                'recommendations': self._generate_optimization_recommendations(drop_off_analysis)
            }
            
            logger.info("瓶颈识别完成")
            return result
            
        except Exception as e:
            logger.error(f"瓶颈识别失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'bottleneck_identification'
            }
            
    def _generate_bottleneck_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成瓶颈分析摘要"""
        funnel_steps = analysis.get('funnel_steps', [])
        major_drop_offs = analysis.get('major_drop_off_points', [])
        
        return {
            'total_steps_analyzed': len(funnel_steps),
            'major_drop_off_points': len(major_drop_offs),
            'most_critical_step': major_drop_offs[0]['step_name'] if major_drop_offs else None,
            'total_users_lost': sum(step.get('users_lost', 0) for step in funnel_steps),
            'avg_step_drop_off_rate': sum(step.get('drop_off_rate', 0) for step in funnel_steps) / len(funnel_steps) if funnel_steps else 0
        }
        
    def _generate_bottleneck_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """生成瓶颈分析洞察"""
        insights = []
        major_drop_offs = analysis.get('major_drop_off_points', [])
        drop_off_insights = analysis.get('drop_off_insights', [])
        
        # 添加预定义洞察
        insights.extend(drop_off_insights)
        
        # 分析主要流失点
        if major_drop_offs:
            critical_step = major_drop_offs[0]
            insights.append(f"最关键流失点: {critical_step['step_name']}，流失率{critical_step['drop_off_rate']:.1%}")
            
        # 分析流失模式
        if len(major_drop_offs) > 1:
            insights.append(f"发现{len(major_drop_offs)}个主要流失点，需要系统性优化")
            
        return insights
        
    def _generate_optimization_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        major_drop_offs = analysis.get('major_drop_off_points', [])
        
        for drop_off in major_drop_offs[:3]:  # 针对前3个主要流失点
            step_name = drop_off['step_name']
            drop_off_rate = drop_off['drop_off_rate']
            
            if drop_off_rate > 0.7:
                recommendations.append(f"步骤'{step_name}'流失率极高，建议重新设计用户流程")
            elif drop_off_rate > 0.5:
                recommendations.append(f"步骤'{step_name}'需要优化用户体验，降低操作难度")
            elif drop_off_rate > 0.3:
                recommendations.append(f"步骤'{step_name}'可通过A/B测试优化界面和交互")
                
        if not recommendations:
            recommendations.append("当前转化流程表现良好，建议持续监控和微调")
            
        return recommendations


class ConversionPathAnalysisTool(BaseTool):
    """转化路径分析工具"""
    
    name: str = "conversion_path_analysis"
    description: str = "分析用户转化路径，识别最优转化路径和异常路径"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        self.engine = ConversionAnalysisEngine(storage_manager)
        
    def _run(self, funnel_steps: List[str], time_window_hours: int = 24) -> Dict[str, Any]:
        """
        执行转化路径分析
        
        Args:
            funnel_steps: 漏斗步骤
            time_window_hours: 时间窗口
            
        Returns:
            转化路径分析结果
        """
        try:
            logger.info(f"开始转化路径分析，步骤: {funnel_steps}")
            
            # 构建漏斗获取用户旅程数据
            funnel = self.engine.build_conversion_funnel(
                funnel_steps=funnel_steps,
                time_window_hours=time_window_hours
            )
            
            # 分析路径模式
            path_analysis = self._analyze_conversion_paths(funnel)
            
            result = {
                'status': 'success',
                'analysis_type': 'conversion_path_analysis',
                'path_analysis': path_analysis,
                'insights': self._generate_path_insights(path_analysis)
            }
            
            logger.info("转化路径分析完成")
            return result
            
        except Exception as e:
            logger.error(f"转化路径分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'conversion_path_analysis'
            }
            
    def _analyze_conversion_paths(self, funnel) -> Dict[str, Any]:
        """分析转化路径"""
        return {
            'optimal_path': {
                'steps': [step.step_name for step in funnel.steps],
                'conversion_rate': funnel.overall_conversion_rate,
                'avg_completion_time': funnel.avg_completion_time
            },
            'path_variations': [],
            'common_exit_points': [funnel.bottleneck_step] if funnel.bottleneck_step else []
        }
        
    def _generate_path_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """生成路径分析洞察"""
        insights = []
        optimal_path = analysis.get('optimal_path', {})
        
        if optimal_path:
            insights.append(f"最优转化路径包含{len(optimal_path['steps'])}个步骤")
            if optimal_path['conversion_rate'] < 0.2:
                insights.append("最优路径转化率仍然较低，建议重新设计转化流程")
                
        return insights


class ConversionAnalysisAgent:
    """转化分析智能体类"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """初始化转化分析智能体"""
        self.storage_manager = storage_manager
        self.tools = [
            FunnelAnalysisTool(storage_manager),
            ConversionRateAnalysisTool(storage_manager),
            BottleneckIdentificationTool(storage_manager),
            ConversionPathAnalysisTool(storage_manager)
        ]
        
        if CREWAI_AVAILABLE:
            self.agent = Agent(
                role="转化分析专家",
                goal="构建转化漏斗，识别转化瓶颈和优化机会",
                backstory="""你是一位经验丰富的转化优化专家，专注于提升用户转化率。
                            你擅长构建复杂的转化漏斗，并能准确识别转化路径中的关键问题。
                            你的分析帮助产品团队优化用户转化流程，提升业务指标。""",
                tools=self.tools,
                llm=get_llm(),
                verbose=True,
                allow_delegation=False,
                max_iter=3
            )
        else:
            self.agent = Agent(
                role="转化分析专家",
                goal="构建转化漏斗，识别转化瓶颈和优化机会"
            )
    
    def analyze_funnel(self, funnel_steps: List[str], funnel_name: str = "custom_funnel", time_window_hours: int = 24) -> Dict[str, Any]:
        """
        分析转化漏斗
        
        Args:
            funnel_steps: 漏斗步骤列表
            funnel_name: 漏斗名称
            time_window_hours: 时间窗口
            
        Returns:
            漏斗分析结果
        """
        try:
            funnel_tool = FunnelAnalysisTool(self.storage_manager)
            return funnel_tool._run(funnel_steps, funnel_name, time_window_hours)
        except Exception as e:
            logger.error(f"漏斗分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'funnel_analysis'
            }
    
    def analyze_conversion_rates(self, funnel_definitions: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """
        分析转化率
        
        Args:
            funnel_definitions: 自定义漏斗定义
            
        Returns:
            转化率分析结果
        """
        try:
            conversion_tool = ConversionRateAnalysisTool(self.storage_manager)
            return conversion_tool._run(funnel_definitions)
        except Exception as e:
            logger.error(f"转化率分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'conversion_rate_analysis'
            }
    
    def identify_bottlenecks(self, funnel_steps: List[str] = None) -> Dict[str, Any]:
        """
        识别转化瓶颈
        
        Args:
            funnel_steps: 要分析的漏斗步骤
            
        Returns:
            瓶颈识别结果
        """
        try:
            bottleneck_tool = BottleneckIdentificationTool(self.storage_manager)
            return bottleneck_tool._run(funnel_steps)
        except Exception as e:
            logger.error(f"瓶颈识别失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'bottleneck_identification'
            }
    
    def analyze_conversion_paths(self, funnel_steps: List[str], time_window_hours: int = 24) -> Dict[str, Any]:
        """
        分析转化路径
        
        Args:
            funnel_steps: 漏斗步骤
            time_window_hours: 时间窗口
            
        Returns:
            转化路径分析结果
        """
        try:
            path_tool = ConversionPathAnalysisTool(self.storage_manager)
            return path_tool._run(funnel_steps, time_window_hours)
        except Exception as e:
            logger.error(f"转化路径分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'conversion_path_analysis'
            }
    
    def comprehensive_conversion_analysis(self, funnel_definitions: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """
        综合转化分析
        
        Args:
            funnel_definitions: 漏斗定义
            
        Returns:
            综合分析结果
        """
        try:
            logger.info("开始综合转化分析")
            
            # 使用默认漏斗定义
            if funnel_definitions is None:
                funnel_definitions = {
                    'purchase_funnel': ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase'],
                    'registration_funnel': ['page_view', 'sign_up', 'login']
                }
            
            # 执行各项分析
            conversion_rates_result = self.analyze_conversion_rates(funnel_definitions)
            
            # 对每个漏斗进行详细分析
            funnel_analyses = {}
            bottleneck_analyses = {}
            
            for funnel_name, steps in funnel_definitions.items():
                funnel_analyses[funnel_name] = self.analyze_funnel(steps, funnel_name)
                bottleneck_analyses[funnel_name] = self.identify_bottlenecks(steps)
            
            # 汇总结果
            comprehensive_result = {
                'status': 'success',
                'analysis_type': 'comprehensive_conversion_analysis',
                'conversion_rates_analysis': conversion_rates_result,
                'funnel_analyses': funnel_analyses,
                'bottleneck_analyses': bottleneck_analyses,
                'summary': self._generate_comprehensive_summary([
                    conversion_rates_result, funnel_analyses, bottleneck_analyses
                ])
            }
            
            logger.info("综合转化分析完成")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"综合转化分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'comprehensive_conversion_analysis'
            }
    
    def _generate_comprehensive_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合分析摘要"""
        successful_analyses = [r for r in analysis_results if isinstance(r, dict) and r.get('status') == 'success']
        
        return {
            'total_analyses_performed': len(analysis_results),
            'successful_analyses': len(successful_analyses),
            'key_findings': self._extract_key_findings(successful_analyses)
        }
    
    def _extract_key_findings(self, results: List[Dict[str, Any]]) -> List[str]:
        """提取关键发现"""
        findings = []
        
        for result in results:
            if isinstance(result, dict):
                insights = result.get('insights', [])
                if insights:
                    findings.extend(insights[:2])  # 每个分析取前2个洞察
            elif isinstance(result, dict):  # 处理嵌套字典
                for sub_result in result.values():
                    if isinstance(sub_result, dict):
                        insights = sub_result.get('insights', [])
                        if insights:
                            findings.extend(insights[:1])  # 每个子分析取1个洞察
                
        return findings[:10]  # 总共返回前10个关键发现
    
    def get_agent(self):
        """获取CrewAI智能体实例"""
        return self.agent
    
    def get_tools(self) -> List:
        """获取智能体工具列表"""
        return self.tools