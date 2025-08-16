"""
共享基础工具类

提供通用的分析工具基类，减少代码重复
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod

from tools.data_storage_manager import DataStorageManager

logger = logging.getLogger(__name__)


class BaseAnalysisTool(ABC):
    """分析工具基类"""
    
    def __init__(self, storage_manager: DataStorageManager = None, engine_class=None):
        self.storage_manager = storage_manager
        self.engine = engine_class(storage_manager) if engine_class else None
        self.name = self.__class__.__name__
        self.description = "基础分析工具"
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """执行分析的主方法"""
        pass
    
    def _handle_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """统一错误处理"""
        logger.error(f"{operation}失败: {error}")
        return {
            'status': 'error',
            'error_message': str(error),
            'analysis_type': self.name.lower().replace('tool', '')
        }
    
    def _generate_summary(self, data: Dict[str, Any], summary_type: str) -> Dict[str, Any]:
        """生成通用摘要"""
        return {
            'total_items': len(data) if isinstance(data, dict) else 0,
            'analysis_completed': bool(data),
            'summary_type': summary_type
        }


class BaseAgent(ABC):
    """智能体基类"""
    
    def __init__(self, storage_manager: DataStorageManager = None, tools=None, engine_class=None):
        self.storage_manager = storage_manager
        self.engine = engine_class(storage_manager) if engine_class else None
        self.tools = tools or []
        
        # 智能体配置
        self.role = "分析专家"
        self.goal = "提供数据分析洞察"
        self.backstory = "专业的数据分析师"
    
    def get_tools(self) -> List:
        """获取工具列表"""
        return self.tools
    
    def get_agent_config(self) -> Dict[str, str]:
        """获取智能体配置"""
        return {
            'role': self.role,
            'goal': self.goal,
            'backstory': self.backstory
        }


class FunnelAnalysisMixin:
    """漏斗分析功能混入类"""
    
    def _serialize_funnel(self, funnel) -> Dict[str, Any]:
        """序列化漏斗数据"""
        return {
            'funnel_name': funnel.funnel_name,
            'overall_conversion_rate': funnel.overall_conversion_rate,
            'total_users_entered': funnel.total_users_entered,
            'total_users_converted': funnel.total_users_converted,
            'avg_completion_time': funnel.avg_completion_time,
            'bottleneck_step': funnel.bottleneck_step,
            'steps': [
                {
                    'step_name': step.step_name,
                    'step_order': step.step_order,
                    'total_users': step.total_users,
                    'conversion_rate': step.conversion_rate,
                    'drop_off_rate': step.drop_off_rate,
                    'avg_time_to_next_step': getattr(step, 'avg_time_to_next_step', None),
                    'median_time_to_next_step': getattr(step, 'median_time_to_next_step', None)
                }
                for step in getattr(funnel, 'steps', [])
            ]
        }
    
    def _generate_funnel_summary(self, funnel: Dict[str, Any]) -> Dict[str, Any]:
        """生成漏斗分析摘要"""
        steps = funnel.get('steps', [])
        if not steps:
            return {}
        
        conversion_rates = [step['conversion_rate'] for step in steps[1:]]
        drop_off_rates = [step['drop_off_rate'] for step in steps[1:]]
        
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
            'bottleneck_identified': funnel['bottleneck_step'] is not None
        }
    
    def _generate_funnel_insights(self, funnel: Dict[str, Any]) -> List[str]:
        """生成漏斗分析洞察"""
        insights = []
        steps = funnel.get('steps', [])
        
        if not steps:
            return ["Insufficient funnel data, cannot generate insights"]
        
        overall_rate = funnel['overall_conversion_rate']
        if overall_rate < 0.1:
            insights.append(f"整体转化率较低({overall_rate:.1%})，需要重点优化")
        elif overall_rate > 0.3:
            insights.append(f"整体转化率良好({overall_rate:.1%})")
        
        if funnel['bottleneck_step']:
            insights.append(f"识别到瓶颈步骤: {funnel['bottleneck_step']}，建议重点优化")
        
        return insights


class EventAnalysisMixin:
    """事件分析功能混入类"""
    
    def _serialize_event_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """序列化事件分析结果"""
        serialized = {}
        for event_type, result in results.items():
            serialized[event_type] = {
                'event_name': getattr(result, 'event_name', event_type),
                'total_count': getattr(result, 'total_count', 0),
                'unique_users': getattr(result, 'unique_users', 0),
                'avg_per_user': getattr(result, 'avg_per_user', 0),
                'frequency_distribution': getattr(result, 'frequency_distribution', {}),
                'percentiles': getattr(result, 'percentiles', {}),
                'trend_direction': getattr(result, 'trend_direction', 'unknown'),
                'growth_rate': getattr(result, 'growth_rate', 0),
                'seasonal_pattern': getattr(result, 'seasonal_pattern', None),
                'anomalies': getattr(result, 'anomalies', [])
            }
        return serialized
    
    def _generate_event_summary(self, results: Dict[str, Any], summary_type: str) -> Dict[str, Any]:
        """生成事件分析摘要"""
        if not results:
            return {}
        
        if summary_type == 'frequency':
            total_events = sum(r['total_count'] for r in results.values())
            most_frequent = max(results.items(), key=lambda x: x[1]['total_count'])
            return {
                'total_events_analyzed': len(results),
                'total_event_count': total_events,
                'most_frequent_event': {'name': most_frequent[0], 'count': most_frequent[1]['total_count']}
            }
        
        elif summary_type == 'trend':
            trend_directions = [r['trend_direction'] for r in results.values()]
            return {
                'total_events_analyzed': len(results),
                'trend_distribution': {
                    'increasing': trend_directions.count('increasing'),
                    'decreasing': trend_directions.count('decreasing'),
                    'stable': trend_directions.count('stable')
                }
            }
        
        return {'summary_type': summary_type, 'total_events': len(results)}


class CommonAnalysisMixin:
    """通用分析功能混入类"""
    
    def _extract_key_findings(self, results: List[Dict[str, Any]], max_findings: int = 10) -> List[str]:
        """提取关键发现"""
        findings = []
        
        for result in results:
            if isinstance(result, dict) and result.get('status') == 'success':
                insights = result.get('insights', [])
                if insights:
                    findings.extend(insights[:2])  # 每个分析取前2个洞察
        
        return findings[:max_findings]
    
    def _generate_comprehensive_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合分析摘要"""
        successful_analyses = [r for r in analysis_results if isinstance(r, dict) and r.get('status') == 'success']
        
        return {
            'total_analyses_performed': len(analysis_results),
            'successful_analyses': len(successful_analyses),
            'analysis_types': [r.get('analysis_type') for r in successful_analyses],
            'key_findings': self._extract_key_findings(successful_analyses)
        }