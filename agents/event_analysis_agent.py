"""
事件分析智能体模块

该模块实现EventAnalysisAgent类，负责事件模式识别和趋势分析。
智能体集成了事件分析引擎，提供事件频次统计、趋势分析和关联性分析功能。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from engines.event_analysis_engine import EventAnalysisEngine
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


class EventFrequencyAnalysisTool(BaseTool):
    """事件频次分析工具"""
    
    name: str = "event_frequency_analysis"
    description: str = "分析事件频次统计，包括事件计数、用户分布和频次分布"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', EventAnalysisEngine(storage_manager))
        
    def _run(self, event_types: Optional[List[str]] = None, date_range: Optional[Tuple[str, str]] = None) -> Dict[str, Any]:
        """
        执行事件频次分析
        
        Args:
            event_types: 要分析的事件类型列表
            date_range: 分析的日期范围
            
        Returns:
            频次分析结果
        """
        try:
            logger.info(f"开始事件频次分析，事件类型: {event_types}, 日期范围: {date_range}")
            
            # 执行频次分析
            frequency_results = self.engine.calculate_event_frequency(
                event_types=event_types,
                date_range=date_range
            )
            
            # 转换结果为可序列化格式
            serialized_results = {}
            for event_type, result in frequency_results.items():
                serialized_results[event_type] = {
                    'event_name': result.event_name,
                    'total_count': result.total_count,
                    'unique_users': result.unique_users,
                    'avg_per_user': result.avg_per_user,
                    'frequency_distribution': result.frequency_distribution,
                    'percentiles': result.percentiles
                }
            
            # 生成分析摘要
            summary = self._generate_frequency_summary(serialized_results)
            
            result = {
                'status': 'success',
                'analysis_type': 'event_frequency',
                'results': serialized_results,
                'summary': summary,
                'insights': self._generate_frequency_insights(serialized_results)
            }
            
            logger.info(f"事件频次分析完成，分析了{len(serialized_results)}种事件类型")
            return result
            
        except Exception as e:
            logger.error(f"事件频次分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'event_frequency'
            }
            
    def _generate_frequency_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成频次分析摘要"""
        if not results:
            return {}
            
        total_events = sum(r['total_count'] for r in results.values())
        total_unique_users = len(set().union(*[
            [r['event_name']] * r['unique_users'] for r in results.values()
        ]))
        
        # 找出最活跃的事件
        most_frequent_event = max(results.items(), key=lambda x: x[1]['total_count'])
        
        # 找出用户参与度最高的事件
        highest_engagement_event = max(results.items(), key=lambda x: x[1]['avg_per_user'])
        
        return {
            'total_events_analyzed': len(results),
            'total_event_count': total_events,
            'estimated_unique_users': total_unique_users,
            'most_frequent_event': {
                'name': most_frequent_event[0],
                'count': most_frequent_event[1]['total_count']
            },
            'highest_engagement_event': {
                'name': highest_engagement_event[0],
                'avg_per_user': highest_engagement_event[1]['avg_per_user']
            }
        }
        
    def _generate_frequency_insights(self, results: Dict[str, Any]) -> List[str]:
        """生成频次分析洞察"""
        insights = []
        
        if not results:
            return ["没有足够的数据进行频次分析"]
            
        # 分析事件分布
        event_counts = [(name, data['total_count']) for name, data in results.items()]
        event_counts.sort(key=lambda x: x[1], reverse=True)
        
        if len(event_counts) > 1:
            top_event = event_counts[0]
            second_event = event_counts[1]
            
            if top_event[1] > second_event[1] * 2:
                insights.append(f"事件'{top_event[0]}'占主导地位，发生次数是第二高事件的{top_event[1]/second_event[1]:.1f}倍")
                
        # 分析用户参与度
        high_engagement_events = [
            name for name, data in results.items() 
            if data['avg_per_user'] > 2.0
        ]
        
        if high_engagement_events:
            insights.append(f"高参与度事件包括: {', '.join(high_engagement_events)}")
            
        # 分析频次分布
        for event_name, data in results.items():
            freq_dist = data['frequency_distribution']
            if freq_dist.get('1', 0) > sum(freq_dist.values()) * 0.7:
                insights.append(f"事件'{event_name}'主要是一次性行为，70%以上用户只触发一次")
            elif freq_dist.get('50+', 0) > 0:
                insights.append(f"事件'{event_name}'有高频用户，部分用户触发超过50次")
                
        return insights


class EventTrendAnalysisTool(BaseTool):
    """事件趋势分析工具"""
    
    name: str = "event_trend_analysis"
    description: str = "分析事件趋势，包括增长趋势、季节性模式和异常检测"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', EventAnalysisEngine(storage_manager))
        
    def _run(self, event_types: Optional[List[str]] = None, time_granularity: str = 'daily') -> Dict[str, Any]:
        """
        执行事件趋势分析
        
        Args:
            event_types: 要分析的事件类型列表
            time_granularity: 时间粒度 ('daily', 'weekly', 'monthly')
            
        Returns:
            趋势分析结果
        """
        try:
            logger.info(f"开始事件趋势分析，事件类型: {event_types}, 时间粒度: {time_granularity}")
            
            # 执行趋势分析
            trend_results = self.engine.analyze_event_trends(
                event_types=event_types,
                time_granularity=time_granularity
            )
            
            # 转换结果为可序列化格式
            serialized_results = {}
            for event_type, result in trend_results.items():
                serialized_results[event_type] = {
                    'event_name': result.event_name,
                    'trend_direction': result.trend_direction,
                    'growth_rate': result.growth_rate,
                    'seasonal_pattern': result.seasonal_pattern,
                    'anomalies': result.anomalies,
                    'trend_data': result.trend_data.to_dict('records') if not result.trend_data.empty else []
                }
            
            # 生成分析摘要
            summary = self._generate_trend_summary(serialized_results)
            
            result = {
                'status': 'success',
                'analysis_type': 'event_trend',
                'results': serialized_results,
                'summary': summary,
                'insights': self._generate_trend_insights(serialized_results)
            }
            
            logger.info(f"事件趋势分析完成，分析了{len(serialized_results)}种事件类型")
            return result
            
        except Exception as e:
            logger.error(f"事件趋势分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'event_trend'
            }
            
    def _generate_trend_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成趋势分析摘要"""
        if not results:
            return {}
            
        trend_directions = [r['trend_direction'] for r in results.values()]
        growth_rates = [r['growth_rate'] for r in results.values()]
        
        return {
            'total_events_analyzed': len(results),
            'trend_distribution': {
                'increasing': trend_directions.count('increasing'),
                'decreasing': trend_directions.count('decreasing'),
                'stable': trend_directions.count('stable')
            },
            'avg_growth_rate': sum(growth_rates) / len(growth_rates) if growth_rates else 0,
            'events_with_anomalies': sum(1 for r in results.values() if r['anomalies']),
            'events_with_seasonality': sum(1 for r in results.values() if r['seasonal_pattern'])
        }
        
    def _generate_trend_insights(self, results: Dict[str, Any]) -> List[str]:
        """生成趋势分析洞察"""
        insights = []
        
        if not results:
            return ["没有足够的数据进行趋势分析"]
            
        # 分析增长趋势
        growing_events = [name for name, data in results.items() if data['trend_direction'] == 'increasing']
        declining_events = [name for name, data in results.items() if data['trend_direction'] == 'decreasing']
        
        if growing_events:
            insights.append(f"增长中的事件: {', '.join(growing_events)}")
        if declining_events:
            insights.append(f"下降中的事件: {', '.join(declining_events)}")
            
        # 分析异常事件
        events_with_anomalies = [name for name, data in results.items() if data['anomalies']]
        if events_with_anomalies:
            insights.append(f"检测到异常的事件: {', '.join(events_with_anomalies)}")
            
        # 分析季节性模式
        seasonal_events = [name for name, data in results.items() if data['seasonal_pattern']]
        if seasonal_events:
            insights.append(f"具有季节性模式的事件: {', '.join(seasonal_events)}")
            
        # 分析高增长率事件
        high_growth_events = [
            name for name, data in results.items() 
            if data['growth_rate'] > 20
        ]
        if high_growth_events:
            insights.append(f"高增长率事件(>20%): {', '.join(high_growth_events)}")
            
        return insights


class EventCorrelationAnalysisTool(BaseTool):
    """事件关联性分析工具"""
    
    name: str = "event_correlation_analysis"
    description: str = "分析事件之间的关联性和共现模式"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', EventAnalysisEngine(storage_manager))
        
    def _run(self, event_types: Optional[List[str]] = None, min_co_occurrence: int = 10) -> Dict[str, Any]:
        """
        执行事件关联性分析
        
        Args:
            event_types: 要分析的事件类型列表
            min_co_occurrence: 最小共现次数
            
        Returns:
            关联性分析结果
        """
        try:
            logger.info(f"开始事件关联性分析，事件类型: {event_types}, 最小共现次数: {min_co_occurrence}")
            
            # 执行关联性分析
            correlation_results = self.engine.analyze_event_correlation(
                event_types=event_types,
                min_co_occurrence=min_co_occurrence
            )
            
            # 转换结果为可序列化格式
            serialized_results = []
            for result in correlation_results:
                serialized_results.append({
                    'event_pair': result.event_pair,
                    'correlation_coefficient': result.correlation_coefficient,
                    'significance_level': result.significance_level,
                    'co_occurrence_rate': result.co_occurrence_rate,
                    'temporal_pattern': result.temporal_pattern
                })
            
            # 生成分析摘要
            summary = self._generate_correlation_summary(serialized_results)
            
            result = {
                'status': 'success',
                'analysis_type': 'event_correlation',
                'results': serialized_results,
                'summary': summary,
                'insights': self._generate_correlation_insights(serialized_results)
            }
            
            logger.info(f"事件关联性分析完成，分析了{len(serialized_results)}个事件对")
            return result
            
        except Exception as e:
            logger.error(f"事件关联性分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'event_correlation'
            }
            
    def _generate_correlation_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成关联性分析摘要"""
        if not results:
            return {}
            
        correlations = [r['correlation_coefficient'] for r in results]
        co_occurrence_rates = [r['co_occurrence_rate'] for r in results]
        
        # 找出最强关联
        strongest_correlation = max(results, key=lambda x: abs(x['correlation_coefficient'])) if results else None
        
        return {
            'total_pairs_analyzed': len(results),
            'avg_correlation': sum(correlations) / len(correlations) if correlations else 0,
            'avg_co_occurrence_rate': sum(co_occurrence_rates) / len(co_occurrence_rates) if co_occurrence_rates else 0,
            'strongest_correlation': {
                'event_pair': strongest_correlation['event_pair'],
                'correlation': strongest_correlation['correlation_coefficient']
            } if strongest_correlation else None,
            'significant_correlations': sum(1 for r in results if r['significance_level'] < 0.05)
        }
        
    def _generate_correlation_insights(self, results: List[Dict[str, Any]]) -> List[str]:
        """生成关联性分析洞察"""
        insights = []
        
        if not results:
            return ["没有足够的数据进行关联性分析"]
            
        # 分析强关联事件对
        strong_correlations = [r for r in results if abs(r['correlation_coefficient']) > 0.3]
        if strong_correlations:
            for corr in strong_correlations[:3]:  # 显示前3个
                event1, event2 = corr['event_pair']
                insights.append(f"事件'{event1}'和'{event2}'存在强关联 (相关系数: {corr['correlation_coefficient']:.3f})")
                
        # 分析高共现率事件对
        high_co_occurrence = [r for r in results if r['co_occurrence_rate'] > 0.5]
        if high_co_occurrence:
            insights.append(f"发现{len(high_co_occurrence)}个高共现率事件对 (共现率>50%)")
            
        # 分析时间模式
        sequential_patterns = [
            r for r in results 
            if r['temporal_pattern'] and 
            r['temporal_pattern'].get('sequence_patterns', {}).get('event1_first', 0) > 
            r['temporal_pattern'].get('sequence_patterns', {}).get('event2_first', 0)
        ]
        
        if sequential_patterns:
            insights.append(f"发现{len(sequential_patterns)}个具有明显时间顺序的事件对")
            
        return insights


class KeyEventIdentificationTool(BaseTool):
    """关键事件识别工具"""
    
    name: str = "key_event_identification"
    description: str = "识别对用户参与度、转化和留存最重要的关键事件"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', EventAnalysisEngine(storage_manager))
        
    def _run(self, top_k: int = 10) -> Dict[str, Any]:
        """
        执行关键事件识别
        
        Args:
            top_k: 返回前K个关键事件
            
        Returns:
            关键事件识别结果
        """
        try:
            logger.info(f"开始关键事件识别，返回前{top_k}个关键事件")
            
            # 执行关键事件识别
            key_event_results = self.engine.identify_key_events(top_k=top_k)
            
            # 转换结果为可序列化格式
            serialized_results = []
            for result in key_event_results:
                serialized_results.append({
                    'event_name': result.event_name,
                    'importance_score': result.importance_score,
                    'user_engagement_impact': result.user_engagement_impact,
                    'conversion_impact': result.conversion_impact,
                    'retention_impact': result.retention_impact,
                    'reasons': result.reasons
                })
            
            # 生成分析摘要
            summary = self._generate_key_event_summary(serialized_results)
            
            result = {
                'status': 'success',
                'analysis_type': 'key_event_identification',
                'results': serialized_results,
                'summary': summary,
                'insights': self._generate_key_event_insights(serialized_results)
            }
            
            logger.info(f"关键事件识别完成，识别了{len(serialized_results)}个关键事件")
            return result
            
        except Exception as e:
            logger.error(f"关键事件识别失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'key_event_identification'
            }
            
    def _generate_key_event_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成关键事件分析摘要"""
        if not results:
            return {}
            
        importance_scores = [r['importance_score'] for r in results]
        
        # 找出最重要的事件
        most_important_event = max(results, key=lambda x: x['importance_score']) if results else None
        
        return {
            'total_events_analyzed': len(results),
            'avg_importance_score': sum(importance_scores) / len(importance_scores) if importance_scores else 0,
            'most_important_event': {
                'name': most_important_event['event_name'],
                'score': most_important_event['importance_score']
            } if most_important_event else None,
            'high_impact_events': sum(1 for r in results if r['importance_score'] > 70)
        }
        
    def _generate_key_event_insights(self, results: List[Dict[str, Any]]) -> List[str]:
        """生成关键事件洞察"""
        insights = []
        
        if not results:
            return ["没有足够的数据进行关键事件识别"]
            
        # 分析最重要的事件
        if results:
            top_event = results[0]
            insights.append(f"最关键的事件是'{top_event['event_name']}'，重要性得分: {top_event['importance_score']:.1f}")
            
        # 分析高影响事件
        high_engagement_events = [r for r in results if r['user_engagement_impact'] > 70]
        high_conversion_events = [r for r in results if r['conversion_impact'] > 70]
        high_retention_events = [r for r in results if r['retention_impact'] > 70]
        
        if high_engagement_events:
            insights.append(f"高用户参与度事件: {', '.join([e['event_name'] for e in high_engagement_events])}")
        if high_conversion_events:
            insights.append(f"高转化影响事件: {', '.join([e['event_name'] for e in high_conversion_events])}")
        if high_retention_events:
            insights.append(f"高留存影响事件: {', '.join([e['event_name'] for e in high_retention_events])}")
            
        # 分析事件重要性原因
        common_reasons = {}
        for result in results:
            for reason in result['reasons']:
                common_reasons[reason] = common_reasons.get(reason, 0) + 1
                
        if common_reasons:
            most_common_reason = max(common_reasons.items(), key=lambda x: x[1])
            insights.append(f"最常见的重要性原因: {most_common_reason[0]}")
            
        return insights


class EventAnalysisAgent:
    """事件分析智能体类"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """初始化事件分析智能体"""
        self.storage_manager = storage_manager
        self.tools = [
            EventFrequencyAnalysisTool(storage_manager),
            EventTrendAnalysisTool(storage_manager),
            EventCorrelationAnalysisTool(storage_manager),
            KeyEventIdentificationTool(storage_manager)
        ]
        
        if CREWAI_AVAILABLE:
            self.agent = Agent(
                role="事件分析专家",
                goal="深入分析用户事件模式，识别关键行为趋势和异常",
                backstory="""你是一位资深的用户行为分析师，擅长从海量事件数据中发现有价值的模式。
                            你能够识别用户行为的关键节点，分析事件趋势和关联性，并提供数据驱动的业务洞察。
                            你的分析帮助产品团队理解用户行为，优化产品功能和用户体验。""",
                tools=self.tools,
                llm=get_llm(),
                verbose=True,
                allow_delegation=False,
                max_iter=3
            )
        else:
            self.agent = Agent(
                role="事件分析专家",
                goal="深入分析用户事件模式，识别关键行为趋势和异常"
            )
        
    def analyze_event_frequency(self, event_types: Optional[List[str]] = None, date_range: Optional[Tuple[str, str]] = None) -> Dict[str, Any]:
        """
        分析事件频次
        
        Args:
            event_types: 要分析的事件类型列表
            date_range: 分析的日期范围
            
        Returns:
            频次分析结果
        """
        try:
            frequency_tool = EventFrequencyAnalysisTool(self.storage_manager)
            return frequency_tool._run(event_types, date_range)
        except Exception as e:
            logger.error(f"事件频次分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'event_frequency'
            }
            
    def analyze_event_trends(self, event_types: Optional[List[str]] = None, time_granularity: str = 'daily') -> Dict[str, Any]:
        """
        分析事件趋势
        
        Args:
            event_types: 要分析的事件类型列表
            time_granularity: 时间粒度
            
        Returns:
            趋势分析结果
        """
        try:
            trend_tool = EventTrendAnalysisTool(self.storage_manager)
            return trend_tool._run(event_types, time_granularity)
        except Exception as e:
            logger.error(f"事件趋势分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'event_trend'
            }
            
    def analyze_event_correlation(self, event_types: Optional[List[str]] = None, min_co_occurrence: int = 10) -> Dict[str, Any]:
        """
        分析事件关联性
        
        Args:
            event_types: 要分析的事件类型列表
            min_co_occurrence: 最小共现次数
            
        Returns:
            关联性分析结果
        """
        try:
            correlation_tool = EventCorrelationAnalysisTool(self.storage_manager)
            return correlation_tool._run(event_types, min_co_occurrence)
        except Exception as e:
            logger.error(f"事件关联性分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'event_correlation'
            }
            
    def identify_key_events(self, top_k: int = 10) -> Dict[str, Any]:
        """
        识别关键事件
        
        Args:
            top_k: 返回前K个关键事件
            
        Returns:
            关键事件识别结果
        """
        try:
            key_event_tool = KeyEventIdentificationTool(self.storage_manager)
            return key_event_tool._run(top_k)
        except Exception as e:
            logger.error(f"关键事件识别失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'key_event_identification'
            }
            
    def comprehensive_event_analysis(self, event_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        综合事件分析
        
        Args:
            event_types: 要分析的事件类型列表
            
        Returns:
            综合分析结果
        """
        try:
            logger.info("开始综合事件分析")
            
            # 执行各项分析
            frequency_result = self.analyze_event_frequency(event_types)
            trend_result = self.analyze_event_trends(event_types)
            correlation_result = self.analyze_event_correlation(event_types)
            key_event_result = self.identify_key_events()
            
            # 汇总结果
            comprehensive_result = {
                'status': 'success',
                'analysis_type': 'comprehensive_event_analysis',
                'frequency_analysis': frequency_result,
                'trend_analysis': trend_result,
                'correlation_analysis': correlation_result,
                'key_event_analysis': key_event_result,
                'summary': self._generate_comprehensive_summary([
                    frequency_result, trend_result, correlation_result, key_event_result
                ])
            }
            
            logger.info("综合事件分析完成")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"综合事件分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'comprehensive_event_analysis'
            }
            
    def _generate_comprehensive_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合分析摘要"""
        successful_analyses = [r for r in analysis_results if r.get('status') == 'success']
        
        return {
            'total_analyses_performed': len(analysis_results),
            'successful_analyses': len(successful_analyses),
            'analysis_types': [r.get('analysis_type') for r in successful_analyses],
            'key_findings': self._extract_key_findings(successful_analyses)
        }
        
    def _extract_key_findings(self, results: List[Dict[str, Any]]) -> List[str]:
        """提取关键发现"""
        findings = []
        
        for result in results:
            insights = result.get('insights', [])
            if insights:
                findings.extend(insights[:2])  # 每个分析取前2个洞察
                
        return findings[:10]  # 总共返回前10个关键发现
        
    def get_agent(self):
        """获取CrewAI智能体实例"""
        return self.agent
        
    def get_tools(self) -> List:
        """获取智能体工具列表"""
        return self.tools