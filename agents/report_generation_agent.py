"""
报告生成智能体模块

该模块实现ReportGenerationAgent类，负责汇总所有分析结果并生成综合报告。
智能体集成了结果汇总工具、洞察生成工具和建议生成工具。
"""

import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import json
from datetime import datetime, timedelta
import os

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

from tools.data_storage_manager import DataStorageManager
from engines.event_analysis_engine import EventAnalysisEngine
from engines.conversion_analysis_engine import ConversionAnalysisEngine
from engines.retention_analysis_engine import RetentionAnalysisEngine
from engines.user_segmentation_engine import UserSegmentationEngine
from engines.path_analysis_engine import PathAnalysisEngine

logger = logging.getLogger(__name__)


class ReportCompilerTool(BaseTool):
    """报告编译工具 - 汇总所有分析结果"""
    
    name: str = "report_compiler"
    description: str = "编译和汇总来自各个分析引擎的结果，生成统一的数据结构"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        self.storage_manager = storage_manager or DataStorageManager()
        self.event_engine = EventAnalysisEngine(self.storage_manager)
        self.conversion_engine = ConversionAnalysisEngine(self.storage_manager)
        self.retention_engine = RetentionAnalysisEngine(self.storage_manager)
        self.segmentation_engine = UserSegmentationEngine(self.storage_manager)
        self.path_engine = PathAnalysisEngine(self.storage_manager)
        
    def _run(self, analysis_scope: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        编译综合分析报告
        
        Args:
            analysis_scope: 分析范围配置
            
        Returns:
            编译后的综合报告数据
        """
        try:
            logger.info("开始编译综合分析报告")
            
            # 设置默认分析范围
            if analysis_scope is None:
                analysis_scope = {
                    'date_range': None,
                    'event_types': None,
                    'user_segments': None
                }
            
            compiled_report = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'analysis_scope': analysis_scope,
                    'data_summary': self._get_data_summary()
                },
                'executive_summary': {},
                'detailed_analysis': {},
                'raw_results': {}
            }
            
            # 1. 事件分析结果
            logger.info("编译事件分析结果")
            event_results = self._compile_event_analysis(analysis_scope)
            compiled_report['detailed_analysis']['event_analysis'] = event_results
            compiled_report['raw_results']['event_analysis'] = event_results
            
            # 2. 转化分析结果
            logger.info("编译转化分析结果")
            conversion_results = self._compile_conversion_analysis(analysis_scope)
            compiled_report['detailed_analysis']['conversion_analysis'] = conversion_results
            compiled_report['raw_results']['conversion_analysis'] = conversion_results
            
            # 3. 留存分析结果
            logger.info("编译留存分析结果")
            retention_results = self._compile_retention_analysis(analysis_scope)
            compiled_report['detailed_analysis']['retention_analysis'] = retention_results
            compiled_report['raw_results']['retention_analysis'] = retention_results
            
            # 4. 用户分群结果
            logger.info("编译用户分群结果")
            segmentation_results = self._compile_segmentation_analysis(analysis_scope)
            compiled_report['detailed_analysis']['user_segmentation'] = segmentation_results
            compiled_report['raw_results']['user_segmentation'] = segmentation_results
            
            # 5. 路径分析结果
            logger.info("编译路径分析结果")
            path_results = self._compile_path_analysis(analysis_scope)
            compiled_report['detailed_analysis']['path_analysis'] = path_results
            compiled_report['raw_results']['path_analysis'] = path_results
            
            # 6. 生成执行摘要
            compiled_report['executive_summary'] = self._generate_executive_summary(compiled_report)
            
            logger.info("综合分析报告编译完成")
            return {
                'status': 'success',
                'report': compiled_report,
                'summary': {
                    'total_sections': len(compiled_report['detailed_analysis']),
                    'data_period': analysis_scope.get('date_range', 'All time'),
                    'generated_at': compiled_report['metadata']['generated_at']
                }
            }
            
        except Exception as e:
            logger.error(f"报告编译失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'report': None
            }
    
    def _get_data_summary(self) -> Dict[str, Any]:
        """获取数据概览"""
        try:
            stats = self.storage_manager.get_statistics()
            return {
                'total_events': stats.get('events_count', 0),
                'unique_users': stats.get('users_count', 0),
                'total_sessions': stats.get('sessions_count', 0),
                'date_range': stats.get('date_range', 'Unknown')
            }
        except Exception as e:
            logger.warning(f"获取数据概览失败: {e}")
            return {}
    
    def _compile_event_analysis(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """编译事件分析结果"""
        try:
            # 事件频次分析
            frequency_result = self.event_engine.analyze_event_frequency(
                event_types=scope.get('event_types'),
                date_range=scope.get('date_range')
            )
            
            # 事件趋势分析
            trend_result = self.event_engine.analyze_event_trends(
                event_types=scope.get('event_types'),
                date_range=scope.get('date_range')
            )
            
            # 事件关联分析
            correlation_result = self.event_engine.analyze_event_correlation(
                event_types=scope.get('event_types'),
                date_range=scope.get('date_range')
            )
            
            return {
                'frequency_analysis': frequency_result,
                'trend_analysis': trend_result,
                'correlation_analysis': correlation_result,
                'summary': {
                    'top_events': frequency_result.get('top_events', [])[:5],
                    'trending_events': trend_result.get('trending_events', [])[:3],
                    'key_correlations': correlation_result.get('strong_correlations', [])[:3]
                }
            }
        except Exception as e:
            logger.error(f"事件分析编译失败: {e}")
            return {'error': str(e)}
    
    def _compile_conversion_analysis(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """编译转化分析结果"""
        try:
            # 转化漏斗分析
            funnel_result = self.conversion_engine.analyze_conversion_funnel(
                funnel_steps=scope.get('funnel_steps'),
                date_range=scope.get('date_range')
            )
            
            # 转化路径分析
            path_result = self.conversion_engine.analyze_conversion_paths(
                target_event=scope.get('target_event', 'purchase'),
                date_range=scope.get('date_range')
            )
            
            return {
                'funnel_analysis': funnel_result,
                'path_analysis': path_result,
                'summary': {
                    'overall_conversion_rate': funnel_result.get('overall_conversion_rate', 0),
                    'bottleneck_step': funnel_result.get('bottleneck_step', 'Unknown'),
                    'top_conversion_paths': path_result.get('top_paths', [])[:3]
                }
            }
        except Exception as e:
            logger.error(f"转化分析编译失败: {e}")
            return {'error': str(e)}
    
    def _compile_retention_analysis(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """编译留存分析结果"""
        try:
            # 留存率分析
            retention_result = self.retention_engine.analyze_retention_rate(
                date_range=scope.get('date_range')
            )
            
            # 队列分析
            cohort_result = self.retention_engine.analyze_cohort_retention(
                date_range=scope.get('date_range')
            )
            
            return {
                'retention_analysis': retention_result,
                'cohort_analysis': cohort_result,
                'summary': {
                    'day1_retention': retention_result.get('day1_retention', 0),
                    'day7_retention': retention_result.get('day7_retention', 0),
                    'day30_retention': retention_result.get('day30_retention', 0),
                    'best_cohort': cohort_result.get('best_performing_cohort', 'Unknown')
                }
            }
        except Exception as e:
            logger.error(f"留存分析编译失败: {e}")
            return {'error': str(e)}
    
    def _compile_segmentation_analysis(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """编译用户分群结果"""
        try:
            # 用户分群
            segmentation_result = self.segmentation_engine.segment_users(
                features=scope.get('segmentation_features'),
                n_clusters=scope.get('n_clusters', 5)
            )
            
            # 群体画像
            profile_result = self.segmentation_engine.profile_segments(
                segmentation_result.get('segments', {})
            )
            
            return {
                'segmentation_result': segmentation_result,
                'segment_profiles': profile_result,
                'summary': {
                    'total_segments': len(segmentation_result.get('segments', {})),
                    'largest_segment': profile_result.get('largest_segment', 'Unknown'),
                    'most_valuable_segment': profile_result.get('most_valuable_segment', 'Unknown')
                }
            }
        except Exception as e:
            logger.error(f"用户分群编译失败: {e}")
            return {'error': str(e)}
    
    def _compile_path_analysis(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """编译路径分析结果"""
        try:
            # 路径挖掘
            path_result = self.path_engine.mine_user_paths(
                min_support=scope.get('min_support', 0.01),
                date_range=scope.get('date_range')
            )
            
            # 流程分析
            flow_result = self.path_engine.analyze_user_flow(
                start_events=scope.get('start_events'),
                end_events=scope.get('end_events')
            )
            
            return {
                'path_mining': path_result,
                'flow_analysis': flow_result,
                'summary': {
                    'common_paths_count': len(path_result.get('common_paths', [])),
                    'drop_off_points': flow_result.get('drop_off_points', [])[:3],
                    'optimal_paths': path_result.get('optimal_paths', [])[:3]
                }
            }
        except Exception as e:
            logger.error(f"路径分析编译失败: {e}")
            return {'error': str(e)}
    
    def _generate_executive_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """生成执行摘要"""
        try:
            detailed = report.get('detailed_analysis', {})
            
            # 提取关键指标
            key_metrics = {
                'total_events': report['metadata']['data_summary'].get('total_events', 0),
                'unique_users': report['metadata']['data_summary'].get('unique_users', 0),
                'conversion_rate': detailed.get('conversion_analysis', {}).get('summary', {}).get('overall_conversion_rate', 0),
                'day1_retention': detailed.get('retention_analysis', {}).get('summary', {}).get('day1_retention', 0),
                'user_segments': detailed.get('user_segmentation', {}).get('summary', {}).get('total_segments', 0)
            }
            
            # 识别关键趋势
            key_trends = []
            if 'event_analysis' in detailed:
                trending = detailed['event_analysis'].get('summary', {}).get('trending_events', [])
                if trending:
                    key_trends.append(f"事件趋势: {', '.join([t.get('event_name', 'Unknown') for t in trending[:2]])}")
            
            # 识别关键问题
            key_issues = []
            if 'conversion_analysis' in detailed:
                bottleneck = detailed['conversion_analysis'].get('summary', {}).get('bottleneck_step')
                if bottleneck and bottleneck != 'Unknown':
                    key_issues.append(f"转化瓶颈: {bottleneck}")
            
            if 'path_analysis' in detailed:
                drop_offs = detailed['path_analysis'].get('summary', {}).get('drop_off_points', [])
                if drop_offs:
                    key_issues.append(f"流失点: {', '.join(drop_offs[:2])}")
            
            return {
                'key_metrics': key_metrics,
                'key_trends': key_trends,
                'key_issues': key_issues,
                'data_quality_score': self._calculate_data_quality_score(report),
                'analysis_completeness': self._calculate_analysis_completeness(detailed)
            }
            
        except Exception as e:
            logger.error(f"执行摘要生成失败: {e}")
            return {'error': str(e)}
    
    def _calculate_data_quality_score(self, report: Dict[str, Any]) -> float:
        """计算数据质量评分"""
        try:
            data_summary = report['metadata']['data_summary']
            score = 0.0
            
            # 基于数据完整性评分
            if data_summary.get('total_events', 0) > 0:
                score += 0.3
            if data_summary.get('unique_users', 0) > 0:
                score += 0.3
            if data_summary.get('total_sessions', 0) > 0:
                score += 0.2
            if data_summary.get('date_range') != 'Unknown':
                score += 0.2
                
            return min(score, 1.0)
        except:
            return 0.0
    
    def _calculate_analysis_completeness(self, detailed: Dict[str, Any]) -> float:
        """计算分析完整性评分"""
        try:
            expected_sections = ['event_analysis', 'conversion_analysis', 'retention_analysis', 
                               'user_segmentation', 'path_analysis']
            completed_sections = sum(1 for section in expected_sections if section in detailed and 'error' not in detailed[section])
            return completed_sections / len(expected_sections)
        except:
            return 0.0


class InsightGeneratorTool(BaseTool):
    """洞察生成工具 - 从分析结果中提取业务洞察"""
    
    name: str = "insight_generator"
    description: str = "从编译的分析结果中生成业务洞察和关键发现"
    
    def __init__(self):
        super().__init__()
        
    def _run(self, compiled_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成业务洞察
        
        Args:
            compiled_report: 编译后的分析报告
            
        Returns:
            业务洞察结果
        """
        try:
            logger.info("开始生成业务洞察")
            
            insights = {
                'key_insights': [],
                'performance_insights': [],
                'user_behavior_insights': [],
                'opportunity_insights': [],
                'risk_insights': []
            }
            
            detailed = compiled_report.get('detailed_analysis', {})
            executive = compiled_report.get('executive_summary', {})
            
            # 1. 关键洞察
            insights['key_insights'] = self._generate_key_insights(executive, detailed)
            
            # 2. 性能洞察
            insights['performance_insights'] = self._generate_performance_insights(detailed)
            
            # 3. 用户行为洞察
            insights['user_behavior_insights'] = self._generate_behavior_insights(detailed)
            
            # 4. 机会洞察
            insights['opportunity_insights'] = self._generate_opportunity_insights(detailed)
            
            # 5. 风险洞察
            insights['risk_insights'] = self._generate_risk_insights(detailed)
            
            # 计算洞察质量评分
            quality_score = self._calculate_insight_quality(insights)
            
            logger.info("业务洞察生成完成")
            return {
                'status': 'success',
                'insights': insights,
                'quality_score': quality_score,
                'total_insights': sum(len(category) for category in insights.values())
            }
            
        except Exception as e:
            logger.error(f"业务洞察生成失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'insights': None
            }  
  
    def _generate_key_insights(self, executive: Dict[str, Any], detailed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成关键洞察"""
        insights = []
        
        try:
            key_metrics = executive.get('key_metrics', {})
            
            # 用户规模洞察
            if key_metrics.get('unique_users', 0) > 0:
                insights.append({
                    'type': 'user_scale',
                    'title': '用户规模分析',
                    'description': f"平台共有 {key_metrics['unique_users']:,} 名独立用户，产生了 {key_metrics['total_events']:,} 次事件",
                    'impact': 'high',
                    'confidence': 0.9
                })
            
            # 转化率洞察
            conversion_rate = key_metrics.get('conversion_rate', 0)
            if conversion_rate > 0:
                if conversion_rate > 0.1:
                    insights.append({
                        'type': 'conversion_performance',
                        'title': '转化表现优秀',
                        'description': f"整体转化率达到 {conversion_rate:.1%}，表现良好",
                        'impact': 'high',
                        'confidence': 0.8
                    })
                elif conversion_rate < 0.05:
                    insights.append({
                        'type': 'conversion_concern',
                        'title': '转化率需要关注',
                        'description': f"整体转化率仅为 {conversion_rate:.1%}，存在优化空间",
                        'impact': 'high',
                        'confidence': 0.8
                    })
            
            # 留存率洞察
            day1_retention = key_metrics.get('day1_retention', 0)
            if day1_retention > 0:
                if day1_retention > 0.4:
                    insights.append({
                        'type': 'retention_strength',
                        'title': '用户留存表现强劲',
                        'description': f"次日留存率达到 {day1_retention:.1%}，用户粘性良好",
                        'impact': 'medium',
                        'confidence': 0.7
                    })
                elif day1_retention < 0.2:
                    insights.append({
                        'type': 'retention_weakness',
                        'title': '用户留存需要改善',
                        'description': f"次日留存率仅为 {day1_retention:.1%}，需要提升用户体验",
                        'impact': 'high',
                        'confidence': 0.8
                    })
            
        except Exception as e:
            logger.warning(f"关键洞察生成部分失败: {e}")
        
        return insights
    
    def _generate_performance_insights(self, detailed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成性能洞察"""
        insights = []
        
        try:
            # 事件分析洞察
            if 'event_analysis' in detailed:
                event_summary = detailed['event_analysis'].get('summary', {})
                top_events = event_summary.get('top_events', [])
                
                if top_events:
                    top_event = top_events[0]
                    insights.append({
                        'type': 'top_event',
                        'title': '最活跃事件',
                        'description': f"'{top_event.get('event_name', 'Unknown')}' 是最活跃的事件，占总事件的 {top_event.get('percentage', 0):.1%}",
                        'impact': 'medium',
                        'confidence': 0.9
                    })
            
            # 转化分析洞察
            if 'conversion_analysis' in detailed:
                conv_summary = detailed['conversion_analysis'].get('summary', {})
                bottleneck = conv_summary.get('bottleneck_step')
                
                if bottleneck and bottleneck != 'Unknown':
                    insights.append({
                        'type': 'conversion_bottleneck',
                        'title': '转化瓶颈识别',
                        'description': f"'{bottleneck}' 步骤是主要的转化瓶颈，需要重点优化",
                        'impact': 'high',
                        'confidence': 0.8
                    })
            
        except Exception as e:
            logger.warning(f"性能洞察生成部分失败: {e}")
        
        return insights
    
    def _generate_behavior_insights(self, detailed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成用户行为洞察"""
        insights = []
        
        try:
            # 用户分群洞察
            if 'user_segmentation' in detailed:
                seg_summary = detailed['user_segmentation'].get('summary', {})
                total_segments = seg_summary.get('total_segments', 0)
                
                if total_segments > 0:
                    insights.append({
                        'type': 'user_diversity',
                        'title': '用户群体多样性',
                        'description': f"用户可以分为 {total_segments} 个不同的群体，显示出多样化的行为模式",
                        'impact': 'medium',
                        'confidence': 0.7
                    })
            
            # 路径分析洞察
            if 'path_analysis' in detailed:
                path_summary = detailed['path_analysis'].get('summary', {})
                drop_off_points = path_summary.get('drop_off_points', [])
                
                if drop_off_points:
                    insights.append({
                        'type': 'user_journey',
                        'title': '用户旅程流失点',
                        'description': f"用户在 {', '.join(drop_off_points[:2])} 等环节容易流失",
                        'impact': 'high',
                        'confidence': 0.8
                    })
            
        except Exception as e:
            logger.warning(f"行为洞察生成部分失败: {e}")
        
        return insights
    
    def _generate_opportunity_insights(self, detailed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成机会洞察"""
        insights = []
        
        try:
            # 基于转化分析的机会
            if 'conversion_analysis' in detailed:
                conv_data = detailed['conversion_analysis']
                if 'path_analysis' in conv_data:
                    top_paths = conv_data['path_analysis'].get('top_paths', [])
                    if top_paths:
                        insights.append({
                            'type': 'conversion_opportunity',
                            'title': '转化路径优化机会',
                            'description': f"优化高转化路径可以进一步提升整体转化率",
                            'impact': 'medium',
                            'confidence': 0.6
                        })
            
            # 基于用户分群的机会
            if 'user_segmentation' in detailed:
                seg_data = detailed['user_segmentation']
                if 'segment_profiles' in seg_data:
                    insights.append({
                        'type': 'segmentation_opportunity',
                        'title': '精准营销机会',
                        'description': "基于用户分群结果，可以实施更精准的个性化营销策略",
                        'impact': 'medium',
                        'confidence': 0.7
                    })
            
        except Exception as e:
            logger.warning(f"机会洞察生成部分失败: {e}")
        
        return insights
    
    def _generate_risk_insights(self, detailed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成风险洞察"""
        insights = []
        
        try:
            # 留存风险
            if 'retention_analysis' in detailed:
                ret_summary = detailed['retention_analysis'].get('summary', {})
                day1_retention = ret_summary.get('day1_retention', 0)
                
                if day1_retention < 0.3:
                    insights.append({
                        'type': 'retention_risk',
                        'title': '用户留存风险',
                        'description': f"次日留存率较低 ({day1_retention:.1%})，存在用户流失风险",
                        'impact': 'high',
                        'confidence': 0.8
                    })
            
            # 转化风险
            if 'conversion_analysis' in detailed:
                conv_summary = detailed['conversion_analysis'].get('summary', {})
                conversion_rate = conv_summary.get('overall_conversion_rate', 0)
                
                if conversion_rate < 0.05:
                    insights.append({
                        'type': 'conversion_risk',
                        'title': '转化率风险',
                        'description': f"整体转化率偏低 ({conversion_rate:.1%})，可能影响业务目标达成",
                        'impact': 'high',
                        'confidence': 0.8
                    })
            
        except Exception as e:
            logger.warning(f"风险洞察生成部分失败: {e}")
        
        return insights
    
    def _calculate_insight_quality(self, insights: Dict[str, List]) -> float:
        """计算洞察质量评分"""
        try:
            total_insights = sum(len(category) for category in insights.values())
            if total_insights == 0:
                return 0.0
            
            # 基于洞察数量和分布计算质量
            quality_score = min(total_insights / 10.0, 1.0)  # 最多10个洞察为满分
            
            # 考虑洞察分布的均衡性
            non_empty_categories = sum(1 for category in insights.values() if len(category) > 0)
            balance_score = non_empty_categories / len(insights)
            
            return (quality_score + balance_score) / 2
        except:
            return 0.0


class RecommendationEngineTool(BaseTool):
    """建议生成工具 - 基于洞察生成可执行的业务建议"""
    
    name: str = "recommendation_engine"
    description: str = "基于业务洞察生成具体的行动建议和优化方案"
    
    def __init__(self):
        super().__init__()
        
    def _run(self, insights: Dict[str, Any], compiled_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成业务建议
        
        Args:
            insights: 业务洞察结果
            compiled_report: 编译后的分析报告
            
        Returns:
            业务建议结果
        """
        try:
            logger.info("开始生成业务建议")
            
            recommendations = {
                'immediate_actions': [],      # 立即行动建议
                'short_term_improvements': [], # 短期改进建议
                'long_term_strategies': [],   # 长期策略建议
                'technical_optimizations': [], # 技术优化建议
                'business_opportunities': []   # 业务机会建议
            }
            
            insight_data = insights.get('insights', {})
            
            # 1. 基于关键洞察生成建议
            recommendations['immediate_actions'].extend(
                self._generate_immediate_actions(insight_data.get('key_insights', []))
            )
            
            # 2. 基于性能洞察生成建议
            recommendations['technical_optimizations'].extend(
                self._generate_technical_recommendations(insight_data.get('performance_insights', []))
            )
            
            # 3. 基于用户行为洞察生成建议
            recommendations['short_term_improvements'].extend(
                self._generate_behavior_recommendations(insight_data.get('user_behavior_insights', []))
            )
            
            # 4. 基于机会洞察生成建议
            recommendations['business_opportunities'].extend(
                self._generate_opportunity_recommendations(insight_data.get('opportunity_insights', []))
            )
            
            # 5. 基于风险洞察生成建议
            recommendations['immediate_actions'].extend(
                self._generate_risk_mitigation_recommendations(insight_data.get('risk_insights', []))
            )
            
            # 6. 生成长期策略建议
            recommendations['long_term_strategies'].extend(
                self._generate_strategic_recommendations(compiled_report)
            )
            
            # 计算建议优先级
            prioritized_recommendations = self._prioritize_recommendations(recommendations)
            
            logger.info("业务建议生成完成")
            return {
                'status': 'success',
                'recommendations': recommendations,
                'prioritized_recommendations': prioritized_recommendations,
                'total_recommendations': sum(len(category) for category in recommendations.values())
            }
            
        except Exception as e:
            logger.error(f"业务建议生成失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'recommendations': None
            }
    
    def _generate_immediate_actions(self, key_insights: List[Dict]) -> List[Dict[str, Any]]:
        """生成立即行动建议"""
        actions = []
        
        for insight in key_insights:
            if insight.get('impact') == 'high':
                if insight.get('type') == 'conversion_concern':
                    actions.append({
                        'title': '紧急优化转化流程',
                        'description': '立即检查转化漏斗中的关键步骤，识别并修复明显的用户体验问题',
                        'priority': 'high',
                        'effort': 'medium',
                        'expected_impact': 'high',
                        'timeline': '1-2周'
                    })
                elif insight.get('type') == 'retention_weakness':
                    actions.append({
                        'title': '启动用户留存改善计划',
                        'description': '分析新用户首次体验，优化引导流程和核心功能的可发现性',
                        'priority': 'high',
                        'effort': 'medium',
                        'expected_impact': 'high',
                        'timeline': '2-3周'
                    })
        
        return actions
    
    def _generate_technical_recommendations(self, performance_insights: List[Dict]) -> List[Dict[str, Any]]:
        """生成技术优化建议"""
        recommendations = []
        
        for insight in performance_insights:
            if insight.get('type') == 'conversion_bottleneck':
                recommendations.append({
                    'title': '优化转化瓶颈步骤',
                    'description': f"重点优化 {insight.get('description', '')} 中提到的瓶颈步骤，改善页面加载速度和用户界面",
                    'priority': 'high',
                    'effort': 'medium',
                    'expected_impact': 'high',
                    'timeline': '2-4周'
                })
            elif insight.get('type') == 'top_event':
                recommendations.append({
                    'title': '优化核心事件体验',
                    'description': '针对最活跃的事件进行深度优化，提升用户体验和事件完成率',
                    'priority': 'medium',
                    'effort': 'low',
                    'expected_impact': 'medium',
                    'timeline': '1-2周'
                })
        
        return recommendations
    
    def _generate_behavior_recommendations(self, behavior_insights: List[Dict]) -> List[Dict[str, Any]]:
        """生成行为优化建议"""
        recommendations = []
        
        for insight in behavior_insights:
            if insight.get('type') == 'user_journey':
                recommendations.append({
                    'title': '优化用户旅程流失点',
                    'description': '在识别的流失点添加引导提示、简化操作流程或提供帮助信息',
                    'priority': 'high',
                    'effort': 'medium',
                    'expected_impact': 'high',
                    'timeline': '3-4周'
                })
            elif insight.get('type') == 'user_diversity':
                recommendations.append({
                    'title': '实施个性化体验',
                    'description': '基于用户分群结果，为不同群体提供个性化的内容和功能推荐',
                    'priority': 'medium',
                    'effort': 'high',
                    'expected_impact': 'medium',
                    'timeline': '6-8周'
                })
        
        return recommendations
    
    def _generate_opportunity_recommendations(self, opportunity_insights: List[Dict]) -> List[Dict[str, Any]]:
        """生成机会建议"""
        recommendations = []
        
        for insight in opportunity_insights:
            if insight.get('type') == 'conversion_opportunity':
                recommendations.append({
                    'title': '扩展高转化路径',
                    'description': '分析高转化路径的特征，在其他路径中复制成功要素',
                    'priority': 'medium',
                    'effort': 'medium',
                    'expected_impact': 'medium',
                    'timeline': '4-6周'
                })
            elif insight.get('type') == 'segmentation_opportunity':
                recommendations.append({
                    'title': '启动精准营销计划',
                    'description': '基于用户分群制定差异化的营销策略和内容推送方案',
                    'priority': 'medium',
                    'effort': 'high',
                    'expected_impact': 'high',
                    'timeline': '8-12周'
                })
        
        return recommendations
    
    def _generate_risk_mitigation_recommendations(self, risk_insights: List[Dict]) -> List[Dict[str, Any]]:
        """生成风险缓解建议"""
        recommendations = []
        
        for insight in risk_insights:
            if insight.get('type') == 'retention_risk':
                recommendations.append({
                    'title': '实施留存提升策略',
                    'description': '建立用户激活指标体系，优化新用户引导和核心价值传递',
                    'priority': 'high',
                    'effort': 'high',
                    'expected_impact': 'high',
                    'timeline': '4-6周'
                })
            elif insight.get('type') == 'conversion_risk':
                recommendations.append({
                    'title': '启动转化率提升项目',
                    'description': '全面审查转化流程，实施A/B测试验证优化方案',
                    'priority': 'high',
                    'effort': 'high',
                    'expected_impact': 'high',
                    'timeline': '6-8周'
                })
        
        return recommendations
    
    def _generate_strategic_recommendations(self, compiled_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成长期策略建议"""
        recommendations = []
        
        # 基于整体数据质量和分析完整性生成策略建议
        executive = compiled_report.get('executive_summary', {})
        data_quality = executive.get('data_quality_score', 0)
        analysis_completeness = executive.get('analysis_completeness', 0)
        
        if data_quality < 0.8:
            recommendations.append({
                'title': '建立数据质量管理体系',
                'description': '建立数据收集标准、质量监控和清洗流程，提升数据分析的准确性',
                'priority': 'medium',
                'effort': 'high',
                'expected_impact': 'high',
                'timeline': '3-6个月'
            })
        
        if analysis_completeness < 0.8:
            recommendations.append({
                'title': '完善分析能力建设',
                'description': '补充缺失的分析模块，建立完整的用户行为分析体系',
                'priority': 'medium',
                'effort': 'high',
                'expected_impact': 'medium',
                'timeline': '6-12个月'
            })
        
        # 通用策略建议
        recommendations.append({
            'title': '建立持续优化机制',
            'description': '建立定期的数据分析和优化评估机制，形成数据驱动的产品迭代循环',
            'priority': 'medium',
            'effort': 'medium',
            'expected_impact': 'high',
            'timeline': '3-6个月'
        })
        
        return recommendations
    
    def _prioritize_recommendations(self, recommendations: Dict[str, List]) -> List[Dict[str, Any]]:
        """对建议进行优先级排序"""
        all_recommendations = []
        
        # 收集所有建议并添加类别信息
        for category, recs in recommendations.items():
            for rec in recs:
                rec_copy = rec.copy()
                rec_copy['category'] = category
                all_recommendations.append(rec_copy)
        
        # 计算优先级分数
        def calculate_priority_score(rec):
            priority_weights = {'high': 3, 'medium': 2, 'low': 1}
            impact_weights = {'high': 3, 'medium': 2, 'low': 1}
            effort_weights = {'low': 3, 'medium': 2, 'high': 1}  # 低努力高分
            
            priority_score = priority_weights.get(rec.get('priority', 'medium'), 2)
            impact_score = impact_weights.get(rec.get('expected_impact', 'medium'), 2)
            effort_score = effort_weights.get(rec.get('effort', 'medium'), 2)
            
            return priority_score * 0.4 + impact_score * 0.4 + effort_score * 0.2
        
        # 按优先级分数排序
        all_recommendations.sort(key=calculate_priority_score, reverse=True)
        
        return all_recommendations[:10]  # 返回前10个最高优先级的建议


class ReportGenerationAgent:
    """报告生成智能体类"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """初始化报告生成智能体"""
        self.storage_manager = storage_manager or DataStorageManager()
        
        self.tools = [
            ReportCompilerTool(self.storage_manager),
            InsightGeneratorTool(),
            RecommendationEngineTool()
        ]
        
        if CREWAI_AVAILABLE:
            self.agent = Agent(
                role="业务分析师",
                goal="汇总分析结果并生成综合报告，提供业务洞察和行动建议",
                backstory="""你是一位经验丰富的业务分析师，擅长从复杂的数据分析结果中提取有价值的业务洞察。
                            你能够将技术分析结果转化为清晰的业务语言，为决策者提供可执行的建议。
                            你的专长包括数据解读、趋势分析、风险识别和机会挖掘。
                            你的目标是帮助业务团队基于数据做出明智的决策。""",
                tools=self.tools,
                llm=get_llm(),
                verbose=True,
                allow_delegation=False,
                max_iter=3
            )
        else:
            self.agent = None
    
    def generate_comprehensive_report(self, analysis_scope: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成综合分析报告
        
        Args:
            analysis_scope: 分析范围配置
            
        Returns:
            综合报告结果
        """
        try:
            logger.info("开始生成综合分析报告")
            
            # 1. 编译分析结果
            compiler_tool = ReportCompilerTool(self.storage_manager)
            compiled_result = compiler_tool._run(analysis_scope)
            
            if compiled_result['status'] != 'success':
                return compiled_result
            
            compiled_report = compiled_result['report']
            
            # 2. 生成业务洞察
            insight_tool = InsightGeneratorTool()
            insights_result = insight_tool._run(compiled_report)
            
            if insights_result['status'] != 'success':
                return insights_result
            
            # 3. 生成业务建议
            recommendation_tool = RecommendationEngineTool()
            recommendations_result = recommendation_tool._run(insights_result, compiled_report)
            
            if recommendations_result['status'] != 'success':
                return recommendations_result
            
            # 4. 整合最终报告
            final_report = {
                'metadata': compiled_report['metadata'],
                'executive_summary': compiled_report['executive_summary'],
                'business_insights': insights_result['insights'],
                'recommendations': recommendations_result['recommendations'],
                'prioritized_actions': recommendations_result['prioritized_recommendations'],
                'detailed_analysis': compiled_report['detailed_analysis'],
                'raw_results': compiled_report['raw_results']
            }
            
            # 5. 生成报告摘要
            report_summary = self._generate_report_summary(final_report)
            
            logger.info("综合分析报告生成完成")
            return {
                'status': 'success',
                'report': final_report,
                'summary': report_summary,
                'export_formats': ['json', 'pdf', 'excel']  # 支持的导出格式
            }
            
        except Exception as e:
            logger.error(f"综合分析报告生成失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'report': None
            }
    
    def export_report(self, report: Dict[str, Any], format_type: str = 'json', output_path: str = None) -> Dict[str, Any]:
        """
        导出报告到指定格式
        
        Args:
            report: 报告数据
            format_type: 导出格式 ('json', 'pdf', 'excel')
            output_path: 输出路径
            
        Returns:
            导出结果
        """
        try:
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"reports/comprehensive_report_{timestamp}.{format_type}"
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if format_type.lower() == 'json':
                return self._export_json(report, output_path)
            elif format_type.lower() == 'pdf':
                return self._export_pdf(report, output_path)
            elif format_type.lower() == 'excel':
                return self._export_excel(report, output_path)
            else:
                return {
                    'status': 'error',
                    'error_message': f"不支持的导出格式: {format_type}"
                }
                
        except Exception as e:
            logger.error(f"报告导出失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }
    
    def _generate_report_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告摘要"""
        try:
            metadata = report.get('metadata', {})
            executive = report.get('executive_summary', {})
            insights = report.get('business_insights', {})
            recommendations = report.get('recommendations', {})
            
            return {
                'generated_at': metadata.get('generated_at'),
                'data_period': metadata.get('analysis_scope', {}).get('date_range', 'All time'),
                'total_users': executive.get('key_metrics', {}).get('unique_users', 0),
                'total_events': executive.get('key_metrics', {}).get('total_events', 0),
                'key_metrics': executive.get('key_metrics', {}),
                'total_insights': sum(len(category) for category in insights.values()) if insights else 0,
                'total_recommendations': sum(len(category) for category in recommendations.values()) if recommendations else 0,
                'data_quality_score': executive.get('data_quality_score', 0),
                'analysis_completeness': executive.get('analysis_completeness', 0)
            }
        except Exception as e:
            logger.warning(f"报告摘要生成失败: {e}")
            return {}
    
    def _export_json(self, report: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """导出JSON格式报告"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            return {
                'status': 'success',
                'output_path': output_path,
                'format': 'json'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f"JSON导出失败: {e}"
            }
    
    def _export_pdf(self, report: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """导出PDF格式报告"""
        # 这里可以集成PDF生成库，如reportlab
        # 目前返回占位符实现
        return {
            'status': 'success',
            'output_path': output_path,
            'format': 'pdf',
            'note': 'PDF导出功能需要集成PDF生成库'
        }
    
    def _export_excel(self, report: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """导出Excel格式报告"""
        # 这里可以集成Excel生成库，如openpyxl
        # 目前返回占位符实现
        return {
            'status': 'success',
            'output_path': output_path,
            'format': 'excel',
            'note': 'Excel导出功能需要集成Excel生成库'
        }
    
    def get_agent(self) -> Agent:
        """获取CrewAI智能体实例"""
        return self.agent
        
    def get_tools(self) -> List[BaseTool]:
        """获取智能体工具列表"""
        return self.tools