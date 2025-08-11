"""
路径分析智能体独立模块

该模块实现PathAnalysisAgent类的独立版本，不依赖CrewAI框架。
提供用户行为路径分析和流程优化功能。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from engines.path_analysis_engine import PathAnalysisEngine, UserSession, PathPattern, PathAnalysisResult
from tools.data_storage_manager import DataStorageManager

logger = logging.getLogger(__name__)


class PathAnalysisAgent:
    """路径分析智能体类（独立版本）"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """初始化路径分析智能体"""
        self.storage_manager = storage_manager
        self.engine = PathAnalysisEngine(storage_manager)
        
        logger.info("路径分析智能体初始化完成（独立模式）")
    
    def reconstruct_sessions(self, user_ids: Optional[List[str]] = None,
                           date_range: Optional[Tuple[str, str]] = None,
                           session_timeout_minutes: int = 30) -> Dict[str, Any]:
        """
        重构用户会话
        
        Args:
            user_ids: 要分析的用户ID列表
            date_range: 分析的日期范围
            session_timeout_minutes: 会话超时时间
            
        Returns:
            会话重构结果
        """
        try:
            logger.info("开始用户会话重构")
            
            # 设置会话超时时间
            self.engine.session_timeout_minutes = session_timeout_minutes
            
            # 重构用户会话
            sessions = self.engine.reconstruct_user_sessions(
                user_ids=user_ids,
                date_range=date_range
            )
            
            if not sessions:
                return {
                    'status': 'error',
                    'error_message': '没有可用的事件数据进行会话重构',
                    'analysis_type': 'session_reconstruction'
                }
            
            # 转换为可序列化格式
            serialized_sessions = []
            for session in sessions:
                serialized_sessions.append({
                    'session_id': session.session_id,
                    'user_id': session.user_id,
                    'start_time': session.start_time.isoformat(),
                    'end_time': session.end_time.isoformat(),
                    'duration_seconds': session.duration_seconds,
                    'page_views': session.page_views,
                    'conversions': session.conversions,
                    'path_sequence': session.path_sequence,
                    'event_count': len(session.events)
                })
            
            # 生成会话统计
            session_stats = self._generate_session_statistics(sessions)
            
            result = {
                'status': 'success',
                'analysis_type': 'session_reconstruction',
                'sessions': serialized_sessions,
                'session_statistics': session_stats,
                'insights': self._generate_session_insights(sessions)
            }
            
            logger.info(f"会话重构完成，生成了{len(sessions)}个用户会话")
            return result
            
        except Exception as e:
            logger.error(f"会话重构失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'session_reconstruction'
            }
    
    def mine_path_patterns(self, sessions: Optional[List[Dict]] = None,
                          min_length: int = 2, max_length: int = 10,
                          min_pattern_frequency: int = 5) -> Dict[str, Any]:
        """
        挖掘路径模式
        
        Args:
            sessions: 用户会话数据
            min_length: 最小路径长度
            max_length: 最大路径长度
            min_pattern_frequency: 最小模式频次
            
        Returns:
            路径挖掘结果
        """
        try:
            logger.info("开始路径挖掘分析")
            
            # 设置最小模式频次
            self.engine.min_pattern_frequency = min_pattern_frequency
            
            # 转换会话数据
            session_objects = None
            if sessions:
                session_objects = []
                for session_data in sessions:
                    from datetime import datetime
                    session_obj = UserSession(
                        session_id=session_data['session_id'],
                        user_id=session_data['user_id'],
                        start_time=datetime.fromisoformat(session_data['start_time']),
                        end_time=datetime.fromisoformat(session_data['end_time']),
                        events=[],  # 简化处理
                        duration_seconds=session_data['duration_seconds'],
                        page_views=session_data['page_views'],
                        conversions=session_data['conversions'],
                        path_sequence=session_data['path_sequence']
                    )
                    session_objects.append(session_obj)
            
            # 执行路径模式识别
            analysis_result = self.engine.identify_path_patterns(
                sessions=session_objects,
                min_length=min_length,
                max_length=max_length
            )
            
            # 转换为可序列化格式
            serialized_result = self._serialize_analysis_result(analysis_result)
            
            result = {
                'status': 'success',
                'analysis_type': 'path_mining',
                'analysis_result': serialized_result,
                'insights': analysis_result.insights
            }
            
            logger.info("路径挖掘分析完成")
            return result
            
        except Exception as e:
            logger.error(f"路径挖掘分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'path_mining'
            }
    
    def analyze_user_flow(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析用户流程
        
        Args:
            analysis_result: 路径分析结果
            
        Returns:
            用户流程分析结果
        """
        try:
            logger.info("开始用户流程分析")
            
            # 重构PathAnalysisResult对象
            path_result = self._reconstruct_analysis_result(analysis_result)
            
            # 生成UX优化建议
            ux_recommendations = self.engine.generate_ux_recommendations(path_result)
            
            # 分析流程瓶颈
            bottlenecks = self._identify_flow_bottlenecks(analysis_result)
            
            # 生成流程优化建议
            flow_optimizations = self._generate_flow_optimizations(analysis_result, bottlenecks)
            
            result = {
                'status': 'success',
                'analysis_type': 'user_flow_analysis',
                'ux_recommendations': ux_recommendations,
                'flow_bottlenecks': bottlenecks,
                'flow_optimizations': flow_optimizations,
                'path_flow_graph': analysis_result.get('path_flow_graph', {}),
                'insights': self._generate_flow_insights(analysis_result, bottlenecks)
            }
            
            logger.info("用户流程分析完成")
            return result
            
        except Exception as e:
            logger.error(f"用户流程分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'user_flow_analysis'
            }
    
    def comprehensive_path_analysis(self, user_ids: Optional[List[str]] = None,
                                  date_range: Optional[Tuple[str, str]] = None,
                                  **kwargs) -> Dict[str, Any]:
        """
        综合路径分析
        
        Args:
            user_ids: 要分析的用户ID列表
            date_range: 分析的日期范围
            **kwargs: 其他参数
            
        Returns:
            综合路径分析结果
        """
        try:
            logger.info("开始综合路径分析")
            
            # 1. 重构用户会话
            session_result = self.reconstruct_sessions(
                user_ids=user_ids,
                date_range=date_range,
                session_timeout_minutes=kwargs.get('session_timeout_minutes', 30)
            )
            if session_result.get('status') != 'success':
                return session_result
            
            # 2. 挖掘路径模式
            mining_result = self.mine_path_patterns(
                sessions=session_result.get('sessions'),
                min_length=kwargs.get('min_length', 2),
                max_length=kwargs.get('max_length', 10),
                min_pattern_frequency=kwargs.get('min_pattern_frequency', 5)
            )
            if mining_result.get('status') != 'success':
                return mining_result
            
            # 3. 分析用户流程
            flow_result = self.analyze_user_flow(
                mining_result.get('analysis_result', {})
            )
            
            # 4. 汇总结果
            comprehensive_result = {
                'status': 'success',
                'analysis_type': 'comprehensive_path_analysis',
                'session_reconstruction': session_result,
                'path_mining': mining_result,
                'user_flow_analysis': flow_result,
                'summary': self._generate_comprehensive_summary([
                    session_result, mining_result, flow_result
                ])
            }
            
            logger.info("综合路径分析完成")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"综合路径分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'comprehensive_path_analysis'
            }
    
    def _generate_session_statistics(self, sessions: List[UserSession]) -> Dict[str, Any]:
        """生成会话统计信息"""
        if not sessions:
            return {}
        
        import numpy as np
        
        durations = [s.duration_seconds for s in sessions]
        path_lengths = [len(s.path_sequence) for s in sessions]
        page_views = [s.page_views for s in sessions]
        conversions = [s.conversions for s in sessions]
        
        stats = {
            'total_sessions': len(sessions),
            'unique_users': len(set(s.user_id for s in sessions)),
            'duration_stats': {
                'mean': float(np.mean(durations)),
                'median': float(np.median(durations)),
                'min': int(min(durations)),
                'max': int(max(durations))
            },
            'path_length_stats': {
                'mean': float(np.mean(path_lengths)),
                'median': float(np.median(path_lengths)),
                'min': int(min(path_lengths)),
                'max': int(max(path_lengths))
            },
            'conversion_stats': {
                'total_conversions': sum(conversions),
                'conversion_sessions': sum(1 for c in conversions if c > 0),
                'conversion_rate': sum(1 for c in conversions if c > 0) / len(sessions)
            }
        }
        
        return stats
    
    def _generate_session_insights(self, sessions: List[UserSession]) -> List[str]:
        """生成会话洞察"""
        insights = []
        
        if not sessions:
            return ["没有足够的会话数据生成洞察"]
        
        import numpy as np
        
        total_sessions = len(sessions)
        unique_users = len(set(s.user_id for s in sessions))
        avg_duration = np.mean([s.duration_seconds for s in sessions])
        conversion_sessions = sum(1 for s in sessions if s.conversions > 0)
        
        insights.append(f"成功重构了{total_sessions}个会话，涉及{unique_users}个用户")
        insights.append(f"平均会话时长为{avg_duration/60:.1f}分钟")
        insights.append(f"有{conversion_sessions}个会话产生了转化，转化率为{conversion_sessions/total_sessions:.1%}")
        
        # 分析会话长度分布
        long_sessions = sum(1 for s in sessions if s.duration_seconds > 1800)  # 超过30分钟
        if long_sessions > 0:
            insights.append(f"发现{long_sessions}个长时间会话（超过30分钟），用户参与度较高")
        
        return insights
    
    def _serialize_analysis_result(self, result: PathAnalysisResult) -> Dict[str, Any]:
        """序列化分析结果"""
        def serialize_patterns(patterns: List[PathPattern]) -> List[Dict]:
            return [{
                'pattern_id': p.pattern_id,
                'path_sequence': p.path_sequence,
                'frequency': p.frequency,
                'user_count': p.user_count,
                'avg_duration': p.avg_duration,
                'conversion_rate': p.conversion_rate,
                'pattern_type': p.pattern_type
            } for p in patterns]
        
        return {
            'total_sessions': result.total_sessions,
            'total_paths': result.total_paths,
            'avg_path_length': result.avg_path_length,
            'common_patterns': serialize_patterns(result.common_patterns),
            'anomalous_patterns': serialize_patterns(result.anomalous_patterns),
            'conversion_paths': serialize_patterns(result.conversion_paths),
            'exit_patterns': serialize_patterns(result.exit_patterns),
            'path_flow_graph': result.path_flow_graph
        }
    
    def _reconstruct_analysis_result(self, data: Dict[str, Any]) -> PathAnalysisResult:
        """重构PathAnalysisResult对象"""
        def reconstruct_patterns(pattern_data: List[Dict]) -> List[PathPattern]:
            patterns = []
            for p in pattern_data:
                pattern = PathPattern(
                    pattern_id=p['pattern_id'],
                    path_sequence=p['path_sequence'],
                    frequency=p['frequency'],
                    user_count=p['user_count'],
                    avg_duration=p['avg_duration'],
                    conversion_rate=p['conversion_rate'],
                    pattern_type=p['pattern_type']
                )
                patterns.append(pattern)
            return patterns
        
        return PathAnalysisResult(
            total_sessions=data.get('total_sessions', 0),
            total_paths=data.get('total_paths', 0),
            avg_path_length=data.get('avg_path_length', 0),
            common_patterns=reconstruct_patterns(data.get('common_patterns', [])),
            anomalous_patterns=reconstruct_patterns(data.get('anomalous_patterns', [])),
            conversion_paths=reconstruct_patterns(data.get('conversion_paths', [])),
            exit_patterns=reconstruct_patterns(data.get('exit_patterns', [])),
            path_flow_graph=data.get('path_flow_graph', {}),
            insights=data.get('insights', [])
        )
    
    def _identify_flow_bottlenecks(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别流程瓶颈"""
        bottlenecks = []
        
        # 分析退出模式找出瓶颈
        exit_patterns = analysis_result.get('exit_patterns', [])
        for pattern in exit_patterns:
            if pattern['frequency'] > 10:  # 频繁退出点
                bottlenecks.append({
                    'type': 'exit_bottleneck',
                    'location': pattern['path_sequence'][-1] if pattern['path_sequence'] else 'unknown',
                    'frequency': pattern['frequency'],
                    'description': f"用户经常在'{pattern['path_sequence'][-1]}'步骤退出"
                })
        
        # 分析转化路径找出转化瓶颈
        conversion_paths = analysis_result.get('conversion_paths', [])
        if conversion_paths:
            avg_conversion_length = sum(len(p['path_sequence']) for p in conversion_paths) / len(conversion_paths)
            if avg_conversion_length > 6:
                bottlenecks.append({
                    'type': 'conversion_bottleneck',
                    'location': 'conversion_path',
                    'avg_length': avg_conversion_length,
                    'description': f"转化路径过长，平均需要{avg_conversion_length:.1f}步"
                })
        
        # 分析异常模式找出可用性问题
        anomalous_patterns = analysis_result.get('anomalous_patterns', [])
        if len(anomalous_patterns) > 5:
            bottlenecks.append({
                'type': 'usability_bottleneck',
                'location': 'multiple_points',
                'pattern_count': len(anomalous_patterns),
                'description': f"发现{len(anomalous_patterns)}个异常行为模式，可能存在可用性问题"
            })
        
        return bottlenecks
    
    def _generate_flow_optimizations(self, analysis_result: Dict[str, Any], 
                                   bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """生成流程优化建议"""
        optimizations = []
        
        # 基于瓶颈生成优化建议
        for bottleneck in bottlenecks:
            if bottleneck['type'] == 'exit_bottleneck':
                optimizations.append(f"优化'{bottleneck['location']}'步骤的用户体验，减少用户流失")
            elif bottleneck['type'] == 'conversion_bottleneck':
                optimizations.append("简化转化流程，减少不必要的中间步骤")
            elif bottleneck['type'] == 'usability_bottleneck':
                optimizations.append("进行用户可用性测试，识别和修复界面问题")
        
        # 基于常见模式生成优化建议
        common_patterns = analysis_result.get('common_patterns', [])
        if common_patterns:
            most_common = common_patterns[0]
            if most_common['conversion_rate'] < 0.2:
                optimizations.append(f"优化最常见路径的转化效果，当前转化率仅为{most_common['conversion_rate']:.1%}")
        
        # 基于路径流图生成建议
        flow_graph = analysis_result.get('path_flow_graph', {})
        if flow_graph.get('nodes'):
            high_traffic_nodes = [node for node in flow_graph['nodes'] if node.get('size', 0) > 100]
            if high_traffic_nodes:
                optimizations.append("重点优化高流量页面的性能和用户体验")
        
        if not optimizations:
            optimizations.append("当前用户流程表现良好，继续监控关键指标")
        
        return optimizations
    
    def _generate_flow_insights(self, analysis_result: Dict[str, Any], 
                              bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """生成流程分析洞察"""
        insights = []
        
        # 基本流程统计
        total_sessions = analysis_result.get('total_sessions', 0)
        avg_path_length = analysis_result.get('avg_path_length', 0)
        insights.append(f"分析了{total_sessions}个用户会话的行为流程")
        insights.append(f"用户平均完成{avg_path_length:.1f}个步骤")
        
        # 瓶颈分析洞察
        if bottlenecks:
            insights.append(f"识别出{len(bottlenecks)}个流程瓶颈点需要优化")
        else:
            insights.append("未发现明显的流程瓶颈，用户体验良好")
        
        # 转化路径洞察
        conversion_paths = analysis_result.get('conversion_paths', [])
        if conversion_paths:
            insights.append(f"发现{len(conversion_paths)}种有效的转化路径模式")
        
        return insights
    
    def _generate_comprehensive_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合分析摘要"""
        successful_analyses = [r for r in analysis_results if r.get('status') == 'success']
        
        summary = {
            'total_analyses_performed': len(analysis_results),
            'successful_analyses': len(successful_analyses),
            'key_findings': []
        }
        
        # 提取关键发现
        for result in successful_analyses:
            insights = result.get('insights', [])
            if insights:
                summary['key_findings'].extend(insights[:2])
        
        return summary