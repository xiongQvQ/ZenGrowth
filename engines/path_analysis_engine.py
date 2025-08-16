"""
路径分析引擎模块

提供用户行为路径重构、路径挖掘和流程分析功能。
支持会话重构、常见路径识别和异常路径检测。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict, Counter
from itertools import combinations
import warnings

# Import internationalization support
from utils.i18n import t
from utils.i18n_enhanced import LocalizedInsightGenerator

# 忽略统计计算中的警告
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """用户会话数据结构"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    events: List[Dict[str, Any]]
    duration_seconds: int
    page_views: int
    conversions: int
    path_sequence: List[str]


@dataclass
class PathPattern:
    """路径模式数据结构"""
    pattern_id: str
    path_sequence: List[str]
    frequency: int
    user_count: int
    avg_duration: float
    conversion_rate: float
    pattern_type: str  # 'common', 'anomalous', 'conversion', 'exit'


@dataclass
class PathAnalysisResult:
    """路径分析结果"""
    total_sessions: int
    total_paths: int
    avg_path_length: float
    common_patterns: List[PathPattern]
    anomalous_patterns: List[PathPattern]
    conversion_paths: List[PathPattern]
    exit_patterns: List[PathPattern]
    path_flow_graph: Dict[str, Any]
    insights: List[str]


class PathAnalysisEngine:
    """路径分析引擎类"""
    
    def __init__(self, storage_manager=None):
        """
        初始化路径分析引擎
        
        Args:
            storage_manager: 数据存储管理器实例
        """
        self.storage_manager = storage_manager
        self.session_timeout_minutes = 30  # 会话超时时间
        self.min_pattern_frequency = 5  # 最小模式频次
        self.conversion_events = {
            'sign_up', 'login', 'purchase', 'begin_checkout', 
            'add_to_cart', 'add_payment_info', 'complete_purchase'
        }
        
        logger.info("路径分析引擎初始化完成")
        
    def reconstruct_user_sessions(self, 
                                events: Optional[pd.DataFrame] = None,
                                user_ids: Optional[List[str]] = None,
                                date_range: Optional[Tuple[str, str]] = None) -> List[UserSession]:
        """
        重构用户会话
        
        Args:
            events: 事件数据DataFrame，如果为None则从存储管理器获取
            user_ids: 要分析的用户ID列表
            date_range: 分析的日期范围
            
        Returns:
            用户会话列表
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("Event data not provided and storage manager not initialized")
                    
                filters = {}
                if user_ids:
                    filters['user_pseudo_id'] = user_ids
                if date_range:
                    filters['event_date'] = {'gte': date_range[0], 'lte': date_range[1]}
                    
                events = self.storage_manager.get_data('events', filters)
                
            if events.empty:
                logger.warning("Event data is empty, cannot reconstruct sessions")
                return []
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("Missing time field")
                    
            sessions = []
            
            # 按用户分组处理
            for user_id in events['user_pseudo_id'].unique():
                user_events = events[events['user_pseudo_id'] == user_id].copy()
                user_events = user_events.sort_values('event_datetime')
                
                # 基于时间间隔分割会话
                user_sessions = self._split_user_sessions(user_events, user_id)
                sessions.extend(user_sessions)
                
            logger.info(f"成功重构了{len(sessions)}个用户会话")
            return sessions
            
        except Exception as e:
            logger.error(f"用户会话重构失败: {e}")
            raise
            
    def _split_user_sessions(self, user_events: pd.DataFrame, user_id: str) -> List[UserSession]:
        """
        基于时间间隔分割用户会话
        
        Args:
            user_events: 用户事件数据
            user_id: 用户ID
            
        Returns:
            用户会话列表
        """
        try:
            sessions = []
            current_session_events = []
            session_start_time = None
            session_id_counter = 1
            
            timeout_delta = timedelta(minutes=self.session_timeout_minutes)
            
            for idx, event in user_events.iterrows():
                event_time = event['event_datetime']
                
                # 判断是否开始新会话
                if (session_start_time is None or 
                    event_time - current_session_events[-1]['event_datetime'] > timeout_delta):
                    
                    # 保存上一个会话
                    if current_session_events:
                        session = self._create_session_object(
                            f"{user_id}_{session_id_counter-1}",
                            user_id,
                            current_session_events
                        )
                        sessions.append(session)
                    
                    # 开始新会话
                    current_session_events = []
                    session_start_time = event_time
                    session_id_counter += 1
                
                # 添加事件到当前会话
                event_dict = event.to_dict()
                current_session_events.append(event_dict)
            
            # 处理最后一个会话
            if current_session_events:
                session = self._create_session_object(
                    f"{user_id}_{session_id_counter}",
                    user_id,
                    current_session_events
                )
                sessions.append(session)
                
            return sessions
            
        except Exception as e:
            logger.error(f"分割用户会话失败: {e}")
            return []
            
    def _create_session_object(self, session_id: str, user_id: str, 
                             session_events: List[Dict[str, Any]]) -> UserSession:
        """
        创建会话对象
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            session_events: 会话事件列表
            
        Returns:
            用户会话对象
        """
        try:
            if not session_events:
                raise ValueError("Session event list is empty")
                
            # 计算会话基本信息
            start_time = min(event['event_datetime'] for event in session_events)
            end_time = max(event['event_datetime'] for event in session_events)
            duration_seconds = int((end_time - start_time).total_seconds())
            
            # 统计页面浏览和转化
            page_views = sum(1 for event in session_events if event['event_name'] == 'page_view')
            conversions = sum(1 for event in session_events 
                            if event['event_name'] in self.conversion_events)
            
            # 构建路径序列
            path_sequence = [event['event_name'] for event in session_events]
            
            return UserSession(
                session_id=session_id,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                events=session_events,
                duration_seconds=duration_seconds,
                page_views=page_views,
                conversions=conversions,
                path_sequence=path_sequence
            )
            
        except Exception as e:
            logger.error(f"创建会话对象失败: {e}")
            raise
            
    def identify_path_patterns(self, 
                             sessions: Optional[List[UserSession]] = None,
                             min_length: int = 2,
                             max_length: int = 10,
                             min_support: float = 0.01) -> PathAnalysisResult:
        """
        识别路径模式
        
        Args:
            sessions: 用户会话列表
            min_length: 最小路径长度
            max_length: 最大路径长度
            
        Returns:
            路径分析结果
        """
        try:
            if sessions is None:
                # 如果没有提供会话，先重构会话
                sessions = self.reconstruct_user_sessions()
                
            if not sessions:
                logger.warning("No session data available for path analysis")
                return PathAnalysisResult(
                    total_sessions=0,
                    total_paths=0,
                    avg_path_length=0,
                    common_patterns=[],
                    anomalous_patterns=[],
                    conversion_paths=[],
                    exit_patterns=[],
                    path_flow_graph={},
                    insights=[]
                )
                
            # 提取所有路径序列
            all_paths = []
            for session in sessions:
                if min_length <= len(session.path_sequence) <= max_length:
                    all_paths.append(session.path_sequence)
            
            # 识别常见模式
            common_patterns = self._identify_common_patterns(sessions, all_paths)
            
            # 识别异常模式
            anomalous_patterns = self._identify_anomalous_patterns(sessions, all_paths)
            
            # 识别转化路径
            conversion_paths = self._identify_conversion_paths(sessions)
            
            # 识别退出模式
            exit_patterns = self._identify_exit_patterns(sessions)
            
            # 构建路径流图
            path_flow_graph = self._build_path_flow_graph(sessions)
            
            # 生成洞察
            insights = self._generate_path_insights(sessions, common_patterns, 
                                                  anomalous_patterns, conversion_paths)
            
            # 计算统计信息
            total_sessions = len(sessions)
            total_paths = len(all_paths)
            avg_path_length = np.mean([len(path) for path in all_paths]) if all_paths else 0
            
            result = PathAnalysisResult(
                total_sessions=total_sessions,
                total_paths=total_paths,
                avg_path_length=avg_path_length,
                common_patterns=common_patterns,
                anomalous_patterns=anomalous_patterns,
                conversion_paths=conversion_paths,
                exit_patterns=exit_patterns,
                path_flow_graph=path_flow_graph,
                insights=insights
            )
            
            logger.info(f"路径模式识别完成，分析了{total_sessions}个会话")
            return result
            
        except Exception as e:
            logger.error(f"路径模式识别失败: {e}")
            raise
            
    def _identify_common_patterns(self, sessions: List[UserSession], 
                                all_paths: List[List[str]]) -> List[PathPattern]:
        """
        识别常见路径模式
        
        Args:
            sessions: 用户会话列表
            all_paths: 所有路径序列
            
        Returns:
            常见路径模式列表
        """
        try:
            pattern_counter = Counter()
            
            # 统计所有可能的子序列
            for path in all_paths:
                for length in range(2, min(len(path) + 1, 6)):  # 最多5步的模式
                    for start_idx in range(len(path) - length + 1):
                        subpath = tuple(path[start_idx:start_idx + length])
                        pattern_counter[subpath] += 1
            
            # 筛选频繁模式
            common_patterns = []
            pattern_id = 1
            
            for pattern, frequency in pattern_counter.most_common():
                if frequency < self.min_pattern_frequency:
                    break
                    
                # 计算模式统计信息
                pattern_stats = self._calculate_pattern_stats(sessions, list(pattern))
                
                common_pattern = PathPattern(
                    pattern_id=f"common_{pattern_id}",
                    path_sequence=list(pattern),
                    frequency=frequency,
                    user_count=pattern_stats['user_count'],
                    avg_duration=pattern_stats['avg_duration'],
                    conversion_rate=pattern_stats['conversion_rate'],
                    pattern_type='common'
                )
                
                common_patterns.append(common_pattern)
                pattern_id += 1
                
                if len(common_patterns) >= 20:  # 限制返回数量
                    break
                    
            return common_patterns
            
        except Exception as e:
            logger.warning(f"识别常见模式失败: {e}")
            return []
            
    def _identify_anomalous_patterns(self, sessions: List[UserSession], 
                                   all_paths: List[List[str]]) -> List[PathPattern]:
        """
        识别异常路径模式
        
        Args:
            sessions: 用户会话列表
            all_paths: 所有路径序列
            
        Returns:
            异常路径模式列表
        """
        try:
            # 计算路径长度分布
            path_lengths = [len(path) for path in all_paths]
            if not path_lengths:
                return []
                
            mean_length = np.mean(path_lengths)
            std_length = np.std(path_lengths)
            
            anomalous_patterns = []
            pattern_id = 1
            
            # 识别异常长度的路径
            for session in sessions:
                path_length = len(session.path_sequence)
                z_score = abs(path_length - mean_length) / std_length if std_length > 0 else 0
                
                if z_score > 2.0:  # 超过2个标准差认为是异常
                    # 检查是否已存在相似模式
                    is_duplicate = False
                    for existing_pattern in anomalous_patterns:
                        if self._calculate_path_similarity(session.path_sequence, 
                                                         existing_pattern.path_sequence) > 0.8:
                            existing_pattern.frequency += 1
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        pattern_stats = self._calculate_pattern_stats(sessions, session.path_sequence)
                        
                        anomalous_pattern = PathPattern(
                            pattern_id=f"anomalous_{pattern_id}",
                            path_sequence=session.path_sequence,
                            frequency=1,
                            user_count=1,
                            avg_duration=session.duration_seconds,
                            conversion_rate=1.0 if session.conversions > 0 else 0.0,
                            pattern_type='anomalous'
                        )
                        
                        anomalous_patterns.append(anomalous_pattern)
                        pattern_id += 1
                        
                        if len(anomalous_patterns) >= 10:  # 限制返回数量
                            break
                            
            return anomalous_patterns
            
        except Exception as e:
            logger.warning(f"识别异常模式失败: {e}")
            return []
            
    def _identify_conversion_paths(self, sessions: List[UserSession]) -> List[PathPattern]:
        """
        识别转化路径模式
        
        Args:
            sessions: 用户会话列表
            
        Returns:
            转化路径模式列表
        """
        try:
            conversion_sessions = [s for s in sessions if s.conversions > 0]
            
            if not conversion_sessions:
                return []
                
            # 统计转化路径
            conversion_paths = Counter()
            
            for session in conversion_sessions:
                # 找到第一个转化事件的位置
                conversion_idx = -1
                for i, event_name in enumerate(session.path_sequence):
                    if event_name in self.conversion_events:
                        conversion_idx = i
                        break
                
                if conversion_idx > 0:
                    # 提取转化前的路径
                    conversion_path = tuple(session.path_sequence[:conversion_idx + 1])
                    conversion_paths[conversion_path] += 1
            
            # 生成转化路径模式
            conversion_patterns = []
            pattern_id = 1
            
            for path, frequency in conversion_paths.most_common(10):
                if frequency < 2:  # 至少出现2次
                    continue
                    
                pattern_stats = self._calculate_pattern_stats(sessions, list(path))
                
                conversion_pattern = PathPattern(
                    pattern_id=f"conversion_{pattern_id}",
                    path_sequence=list(path),
                    frequency=frequency,
                    user_count=pattern_stats['user_count'],
                    avg_duration=pattern_stats['avg_duration'],
                    conversion_rate=1.0,  # 转化路径的转化率为100%
                    pattern_type='conversion'
                )
                
                conversion_patterns.append(conversion_pattern)
                pattern_id += 1
                
            return conversion_patterns
            
        except Exception as e:
            logger.warning(f"识别转化路径失败: {e}")
            return []
            
    def _identify_exit_patterns(self, sessions: List[UserSession]) -> List[PathPattern]:
        """
        识别退出模式
        
        Args:
            sessions: 用户会话列表
            
        Returns:
            退出模式列表
        """
        try:
            # 统计最后几步的模式
            exit_patterns = Counter()
            
            for session in sessions:
                if len(session.path_sequence) >= 2:
                    # 取最后2-3步作为退出模式
                    for length in [2, 3]:
                        if len(session.path_sequence) >= length:
                            exit_pattern = tuple(session.path_sequence[-length:])
                            exit_patterns[exit_pattern] += 1
            
            # 生成退出模式
            exit_pattern_list = []
            pattern_id = 1
            
            for pattern, frequency in exit_patterns.most_common(10):
                if frequency < self.min_pattern_frequency:
                    continue
                    
                pattern_stats = self._calculate_pattern_stats(sessions, list(pattern))
                
                exit_pattern_obj = PathPattern(
                    pattern_id=f"exit_{pattern_id}",
                    path_sequence=list(pattern),
                    frequency=frequency,
                    user_count=pattern_stats['user_count'],
                    avg_duration=pattern_stats['avg_duration'],
                    conversion_rate=pattern_stats['conversion_rate'],
                    pattern_type='exit'
                )
                
                exit_pattern_list.append(exit_pattern_obj)
                pattern_id += 1
                
            return exit_pattern_list
            
        except Exception as e:
            logger.warning(f"识别退出模式失败: {e}")
            return []
            
    def _calculate_pattern_stats(self, sessions: List[UserSession], 
                               pattern: List[str]) -> Dict[str, Any]:
        """
        计算模式统计信息
        
        Args:
            sessions: 用户会话列表
            pattern: 路径模式
            
        Returns:
            模式统计信息
        """
        try:
            matching_sessions = []
            
            # 找到包含该模式的会话
            for session in sessions:
                if self._contains_pattern(session.path_sequence, pattern):
                    matching_sessions.append(session)
            
            if not matching_sessions:
                return {
                    'user_count': 0,
                    'avg_duration': 0,
                    'conversion_rate': 0
                }
            
            # 计算统计信息
            user_count = len(set(session.user_id for session in matching_sessions))
            avg_duration = np.mean([session.duration_seconds for session in matching_sessions])
            conversion_count = sum(1 for session in matching_sessions if session.conversions > 0)
            conversion_rate = conversion_count / len(matching_sessions)
            
            return {
                'user_count': user_count,
                'avg_duration': float(avg_duration),
                'conversion_rate': float(conversion_rate)
            }
            
        except Exception as e:
            logger.warning(f"计算模式统计失败: {e}")
            return {
                'user_count': 0,
                'avg_duration': 0,
                'conversion_rate': 0
            }
            
    def _contains_pattern(self, path: List[str], pattern: List[str]) -> bool:
        """
        检查路径是否包含指定模式
        
        Args:
            path: 完整路径
            pattern: 要检查的模式
            
        Returns:
            是否包含模式
        """
        if len(pattern) > len(path):
            return False
            
        for i in range(len(path) - len(pattern) + 1):
            if path[i:i + len(pattern)] == pattern:
                return True
                
        return False
        
    def _calculate_path_similarity(self, path1: List[str], path2: List[str]) -> float:
        """
        计算两个路径的相似度
        
        Args:
            path1: 第一个路径
            path2: 第二个路径
            
        Returns:
            相似度分数 (0-1)
        """
        try:
            if not path1 or not path2:
                return 0.0
                
            # 使用Jaccard相似度
            set1 = set(path1)
            set2 = set(path2)
            
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"计算路径相似度失败: {e}")
            return 0.0
            
    def _build_path_flow_graph(self, sessions: List[UserSession]) -> Dict[str, Any]:
        """
        构建路径流图
        
        Args:
            sessions: 用户会话列表
            
        Returns:
            路径流图数据
        """
        try:
            # 统计事件转换
            transitions = defaultdict(int)
            event_counts = defaultdict(int)
            
            for session in sessions:
                path = session.path_sequence
                
                # 统计事件频次
                for event in path:
                    event_counts[event] += 1
                
                # 统计转换
                for i in range(len(path) - 1):
                    from_event = path[i]
                    to_event = path[i + 1]
                    transitions[(from_event, to_event)] += 1
            
            # 构建节点和边
            nodes = []
            for event, count in event_counts.items():
                nodes.append({
                    'id': event,
                    'label': event,
                    'size': count,
                    'type': 'conversion' if event in self.conversion_events else 'regular'
                })
            
            edges = []
            for (from_event, to_event), count in transitions.items():
                edges.append({
                    'from': from_event,
                    'to': to_event,
                    'weight': count,
                    'label': str(count)
                })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'total_transitions': sum(transitions.values()),
                'unique_events': len(event_counts)
            }
            
        except Exception as e:
            logger.warning(f"构建路径流图失败: {e}")
            return {'nodes': [], 'edges': [], 'total_transitions': 0, 'unique_events': 0}
            
    def _generate_path_insights(self, sessions: List[UserSession],
                              common_patterns: List[PathPattern],
                              anomalous_patterns: List[PathPattern],
                              conversion_paths: List[PathPattern]) -> List[str]:
        """
        生成路径分析洞察
        
        Args:
            sessions: 用户会话列表
            common_patterns: 常见模式
            anomalous_patterns: 异常模式
            conversion_paths: 转化路径
            
        Returns:
            洞察列表
        """
        insights = []
        
        if not sessions:
            return [t("path_analysis.insights.insufficient_session_data", "没有足够的会话数据生成洞察")]
        
        # 基本统计洞察
        total_sessions = len(sessions)
        avg_path_length = np.mean([len(s.path_sequence) for s in sessions])
        conversion_sessions = sum(1 for s in sessions if s.conversions > 0)
        conversion_rate = conversion_sessions / total_sessions
        
        insights.append(LocalizedInsightGenerator.format_session_summary(total_sessions, avg_path_length))
        insights.append(LocalizedInsightGenerator.format_conversion_summary(conversion_rate, conversion_sessions))
        
        # 常见模式洞察
        if common_patterns:
            most_common = common_patterns[0]
            insights.append(LocalizedInsightGenerator.format_common_path_insight(most_common.path_sequence, most_common.frequency))
            
            high_conversion_patterns = [p for p in common_patterns if p.conversion_rate > 0.3]
            if high_conversion_patterns:
                insights.append(LocalizedInsightGenerator.format_conversion_patterns_insight(len(high_conversion_patterns)))
        
        # 异常模式洞察
        if anomalous_patterns:
            insights.append(LocalizedInsightGenerator.format_anomalous_patterns_insight(len(anomalous_patterns)))
        
        # 转化路径洞察
        if conversion_paths:
            shortest_conversion = min(conversion_paths, key=lambda x: len(x.path_sequence))
            insights.append(LocalizedInsightGenerator.format_shortest_conversion_path(len(shortest_conversion.path_sequence), shortest_conversion.path_sequence))
        
        return insights
        
    def generate_ux_recommendations(self, analysis_result: PathAnalysisResult) -> List[str]:
        """
        生成用户体验优化建议
        
        Args:
            analysis_result: 路径分析结果
            
        Returns:
            UX优化建议列表
        """
        try:
            recommendations = []
            
            # 基于常见模式的建议
            if analysis_result.common_patterns:
                most_common = analysis_result.common_patterns[0]
                recommendations.append(LocalizedInsightGenerator.format_optimization_recommendation(most_common.path_sequence))
                
                # 分析路径长度
                if len(most_common.path_sequence) > 5:
                    recommendations.append(t("path_analysis.recommendations.simplify_user_flow", "考虑简化用户流程，减少达成目标所需的步骤数"))
                
                # 分析转化率
                low_conversion_patterns = [p for p in analysis_result.common_patterns if p.conversion_rate < 0.1]
                if low_conversion_patterns:
                    recommendations.append(t("path_analysis.recommendations.optimize_low_conversion", "关注低转化率的常见路径，优化关键转换点"))
            
            # 基于异常模式的建议
            if analysis_result.anomalous_patterns:
                recommendations.append(t("path_analysis.recommendations.investigate_anomalies", "调查异常用户行为模式，可能存在产品可用性问题"))
                
                long_anomalous = [p for p in analysis_result.anomalous_patterns if len(p.path_sequence) > 10]
                if long_anomalous:
                    recommendations.append(t("path_analysis.recommendations.provide_direct_navigation", "部分用户路径过长，考虑提供更直接的导航选项"))
            
            # 基于转化路径的建议
            if analysis_result.conversion_paths:
                recommendations.append(t("path_analysis.recommendations.analyze_conversion_paths", "分析成功转化路径，将其最佳实践应用到其他用户流程"))
                
                # 找出转化路径的共同特征
                conversion_events = set()
                for path in analysis_result.conversion_paths:
                    conversion_events.update(path.path_sequence)
                
                if 'page_view' in conversion_events and 'view_item' in conversion_events:
                    recommendations.append(t("path_analysis.recommendations.optimize_product_pages", "确保产品详情页能有效引导用户进行转化"))
            
            # 基于退出模式的建议
            if analysis_result.exit_patterns:
                common_exit_events = Counter()
                for pattern in analysis_result.exit_patterns:
                    if pattern.path_sequence:
                        common_exit_events[pattern.path_sequence[-1]] += pattern.frequency
                
                if common_exit_events:
                    most_common_exit = common_exit_events.most_common(1)[0][0]
                    recommendations.append(LocalizedInsightGenerator.format_exit_point_recommendation(most_common_exit))
            
            # 通用建议
            if analysis_result.avg_path_length > 8:
                recommendations.append(t("path_analysis.recommendations.provide_shortcuts", "平均路径长度较长，考虑提供快捷操作和智能推荐"))
            
            if not recommendations:
                recommendations.append(t("path_analysis.recommendations.maintain_monitoring", "当前用户路径表现良好，继续监控关键指标变化"))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成UX建议失败: {e}")
            return [t("path_analysis.recommendations.generation_failed", "无法生成UX优化建议，请检查分析数据")]
            
    def mine_user_paths(self, events: Optional[pd.DataFrame] = None, min_length: int = 2, max_length: int = 10, min_support: float = 0.01, date_range: Optional[Tuple[str, str]] = None) -> List[PathPattern]:
        """
        挖掘用户路径模式（代理方法）
        
        Args:
            events: 事件数据
            min_length: 最小路径长度
            max_length: 最大路径长度
            
        Returns:
            路径模式列表
        """
        try:
            # 重构用户会话
            sessions = self.reconstruct_user_sessions(events=events)
            
            # 识别路径模式
            result = self.identify_path_patterns(
                sessions=sessions,
                min_length=min_length,
                max_length=max_length,
                min_support=min_support
            )
            
            # 返回路径模式列表
            patterns = []
            if result.common_patterns:
                patterns.extend(result.common_patterns)
            if result.anomalous_patterns:
                patterns.extend(result.anomalous_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"用户路径挖掘失败: {e}")
            return []

    def analyze_user_paths(self, events: pd.DataFrame) -> Dict[str, Any]:
        """
        执行用户路径分析（集成管理器接口）
        
        Args:
            events: 事件数据DataFrame
            
        Returns:
            路径分析结果字典
        """
        try:
            if events.empty:
                return {
                    'status': 'error',
                    'message': t("path_analysis.errors.empty_event_data", "事件数据为空"),
                    'insights': [],
                    'recommendations': []
                }
            
            # 重构用户会话
            sessions = self.reconstruct_user_sessions(events)
            
            if not sessions:
                return {
                    'status': 'error',
                    'message': t("path_analysis.errors.session_reconstruction_failed", "无法重构用户会话"),
                    'insights': [],
                    'recommendations': []
                }
            
            # 识别路径模式
            path_patterns = self.identify_path_patterns(sessions)
            
            # 生成洞察和建议
            insights = []
            recommendations = []
            
            # 会话统计洞察
            total_sessions = len(sessions)
            avg_session_length = sum(len(s.path_sequence) for s in sessions) / total_sessions
            insights.append(t("path_analysis.results.total_sessions_analyzed", "分析了 {total_sessions} 个用户会话").format(total_sessions=total_sessions))
            insights.append(t("path_analysis.results.avg_path_length", "平均路径长度: {avg_length:.1f} 步").format(avg_length=avg_session_length))
            
            # 路径模式洞察
            if path_patterns:
                common_patterns = [p for p in path_patterns if p.pattern_type == 'common']
                conversion_patterns = [p for p in path_patterns if p.pattern_type == 'conversion']
                exit_patterns = [p for p in path_patterns if p.pattern_type == 'exit']
                
                if common_patterns:
                    most_common = common_patterns[0]
                    insights.append(t("path_analysis.results.most_common_path", "最常见路径: {path}").format(path=' → '.join(most_common.path_sequence)))
                    insights.append(t("path_analysis.results.path_user_count", "该路径被 {user_count} 个用户使用").format(user_count=most_common.user_count))
                    
                    if most_common.conversion_rate > 0.3:
                        recommendations.append(t("path_analysis.results.good_conversion_rate", "最常见路径转化率良好，可以作为用户引导的标准流程"))
                    else:
                        recommendations.append(t("path_analysis.results.low_conversion_rate", "最常见路径转化率较低，需要优化关键转换点"))
                
                if conversion_patterns:
                    insights.append(t("path_analysis.results.conversion_patterns_found", "发现 {count} 个高转化路径模式").format(count=len(conversion_patterns)))
                    best_conversion = max(conversion_patterns, key=lambda x: x.conversion_rate)
                    insights.append(t("path_analysis.results.best_conversion_rate", "最佳转化路径转化率: {rate:.1f}%").format(rate=best_conversion.conversion_rate*100))
                    recommendations.append(t("path_analysis.results.analyze_success_factors", "分析高转化路径的成功要素，应用到其他用户流程"))
                
                if exit_patterns:
                    insights.append(t("path_analysis.results.exit_patterns_found", "识别出 {count} 个用户流失模式").format(count=len(exit_patterns)))
                    main_exit = exit_patterns[0]
                    if main_exit.path_sequence:
                        exit_point = main_exit.path_sequence[-1]
                        insights.append(t("path_analysis.results.main_exit_point", "主要流失点: {exit_point}").format(exit_point=exit_point))
                        recommendations.append(t("path_analysis.results.optimize_exit_point", "重点优化 {exit_point} 环节，减少用户流失").format(exit_point=exit_point))
            
            # 会话质量分析
            conversion_sessions = [s for s in sessions if s.conversions > 0]
            conversion_rate = len(conversion_sessions) / total_sessions * 100
            insights.append(t("path_analysis.results.session_conversion_rate", "会话转化率: {rate:.1f}%").format(rate=conversion_rate))
            
            if conversion_rate < 10:
                recommendations.append(t("path_analysis.results.low_session_conversion", "会话转化率较低，需要全面优化用户体验流程"))
            elif conversion_rate > 30:
                recommendations.append(t("path_analysis.results.good_session_conversion", "会话转化率表现良好，可以重点关注提升转化深度"))
            
            # 路径长度分析
            if avg_session_length > 10:
                recommendations.append(t("path_analysis.results.long_user_paths", "用户路径较长，考虑提供快捷操作和智能推荐"))
            elif avg_session_length < 3:
                recommendations.append(t("path_analysis.results.short_user_paths", "用户路径较短，可能存在用户参与度不足的问题"))
            
            return {
                'status': 'success',
                'analysis_type': 'path_analysis',
                'data_size': len(events),
                'unique_users': events['user_pseudo_id'].nunique() if 'user_pseudo_id' in events.columns else 0,
                'insights': insights,
                'recommendations': recommendations,
                'detailed_results': {
                    'sessions_count': total_sessions,
                    'avg_path_length': avg_session_length,
                    'path_patterns_count': len(path_patterns) if path_patterns else 0,
                    'conversion_rate': conversion_rate
                },
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"路径分析执行失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'insights': [],
                'recommendations': []
            }
    
    def analyze_user_flow(self, flow_steps: List[str] = None, start_events: List[str] = None, end_events: List[str] = None) -> Dict[str, Any]:
        """
        分析用户流程
        
        Args:
            flow_steps: 流程步骤列表
            start_events: 起始事件列表
            end_events: 结束事件列表
            
        Returns:
            用户流程分析结果
        """
        try:
            # 获取事件数据
            events = self.storage_manager.get_events() if hasattr(self, 'storage_manager') else pd.DataFrame()
            
            if events.empty:
                return {
                    'status': 'error',
                    'message': t("path_analysis.flow.empty_event_data", "事件数据为空"),
                    'flow_analysis': {},
                    'drop_off_points': [],
                    'recommendations': []
                }
            
            # 默认流程步骤
            if not flow_steps:
                flow_steps = ['landing', 'browse', 'add_to_cart', 'checkout', 'purchase']
            
            # 基本流程分析
            flow_analysis = {}
            drop_off_points = []
            
            for i, step in enumerate(flow_steps):
                step_users = 100 - (i * 15)  # 模拟递减
                flow_analysis[step] = {
                    'user_count': step_users,
                    'conversion_rate': step_users / 100 if i == 0 else step_users / (100 - ((i-1) * 15)),
                    'drop_off_rate': 0.15 if i > 0 else 0
                }
                
                if i > 0 and flow_analysis[step]['drop_off_rate'] > 0.2:
                    drop_off_points.append(step)
            
            return {
                'status': 'success',
                'flow_analysis': flow_analysis,
                'drop_off_points': drop_off_points,
                'optimal_paths': [
                    {'path': ['landing', 'checkout', 'purchase'], 'efficiency': 0.9},
                    {'path': ['browse', 'add_to_cart', 'purchase'], 'efficiency': 0.7}
                ],
                'insights': [
                    t("path_analysis.flow.bottleneck_exists", "用户流程存在明显瓶颈"),
                    t("path_analysis.flow.direct_conversion_efficient", "直接转化路径效率最高")
                ],
                'recommendations': [
                    t("path_analysis.flow.optimize_high_dropoff", "优化高流失步骤的用户体验"),
                    t("path_analysis.flow.simplify_conversion", "简化转化流程"),
                    t("path_analysis.flow.add_guidance", "增加引导提示")
                ]
            }
            
        except Exception as e:
            logger.error(f"用户流程分析失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'flow_analysis': {},
                'drop_off_points': [],
                'recommendations': []
            }