"""
事件分析引擎模块

提供事件频次统计、趋势分析和关联性分析功能。
支持关键事件识别和事件模式分析。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
import itertools
from scipy import stats
from scipy.stats import chi2_contingency
import warnings

# Import internationalization support
from utils.i18n import t
from utils.i18n_enhanced import LocalizedInsightGenerator

# 忽略统计计算中的警告
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


@dataclass
class EventFrequencyResult:
    """事件频次分析结果"""
    event_name: str
    total_count: int
    unique_users: int
    avg_per_user: float
    frequency_distribution: Dict[str, int]
    percentiles: Dict[str, float]


@dataclass
class EventTrendResult:
    """事件趋势分析结果"""
    event_name: str
    trend_data: Any  # Changed from pd.DataFrame to Any to avoid Pydantic issues
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    growth_rate: float
    seasonal_pattern: Optional[Dict[str, float]]
    anomalies: List[Dict[str, Any]]


@dataclass
class EventCorrelationResult:
    """事件关联性分析结果"""
    event_pair: Tuple[str, str]
    correlation_coefficient: float
    significance_level: float
    co_occurrence_rate: float
    temporal_pattern: Dict[str, Any]


@dataclass
class KeyEventResult:
    """关键事件识别结果"""
    event_name: str
    importance_score: float
    user_engagement_impact: float
    conversion_impact: float
    retention_impact: float
    reasons: List[str]


class EventAnalysisEngine:
    """事件分析引擎类"""
    
    def __init__(self, storage_manager=None):
        """
        初始化事件分析引擎
        
        Args:
            storage_manager: 数据存储管理器实例
        """
        self.storage_manager = storage_manager
        self.conversion_events = {
            'sign_up', 'login', 'purchase', 'begin_checkout', 
            'add_to_cart', 'add_payment_info'
        }
        self.engagement_events = {
            'page_view', 'view_item', 'search', 'view_item_list',
            'select_item', 'view_cart'
        }
        
        logger.info("事件分析引擎初始化完成")
        
    def calculate_event_frequency(self, 
                                events: Optional[pd.DataFrame] = None,
                                event_types: Optional[List[str]] = None,
                                date_range: Optional[Tuple[str, str]] = None) -> Dict[str, EventFrequencyResult]:
        """
        计算事件频次统计
        
        Args:
            events: 事件数据DataFrame，如果为None则从存储管理器获取
            event_types: 要分析的事件类型列表
            date_range: 分析的日期范围
            
        Returns:
            事件频次分析结果字典
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("Event data not provided and storage manager not initialized")
                    
                filters = {}
                if event_types:
                    filters['event_name'] = event_types
                if date_range:
                    filters['event_date'] = {'gte': date_range[0], 'lte': date_range[1]}
                    
                events = self.storage_manager.get_data('events', filters)
                
            if events.empty:
                logger.warning("Event data is empty, cannot perform frequency analysis")
                return {}
                
            results = {}
            
            # 按事件类型分析
            for event_type in events['event_name'].unique():
                event_data = events[events['event_name'] == event_type]
                
                # 基础统计
                total_count = len(event_data)
                unique_users = event_data['user_pseudo_id'].nunique()
                avg_per_user = total_count / unique_users if unique_users > 0 else 0
                
                # 用户事件频次分布
                user_event_counts = event_data['user_pseudo_id'].value_counts()
                frequency_distribution = self._calculate_frequency_distribution(user_event_counts)
                
                # 计算百分位数
                percentiles = {
                    'p25': float(user_event_counts.quantile(0.25)),
                    'p50': float(user_event_counts.quantile(0.50)),
                    'p75': float(user_event_counts.quantile(0.75)),
                    'p90': float(user_event_counts.quantile(0.90)),
                    'p95': float(user_event_counts.quantile(0.95))
                }
                
                results[event_type] = EventFrequencyResult(
                    event_name=event_type,
                    total_count=total_count,
                    unique_users=unique_users,
                    avg_per_user=avg_per_user,
                    frequency_distribution=frequency_distribution,
                    percentiles=percentiles
                )
                
            logger.info(f"完成{len(results)}种事件类型的频次分析")
            return results
            
        except Exception as e:
            logger.error(f"事件频次分析失败: {e}")
            raise
            
    def _calculate_frequency_distribution(self, user_counts: pd.Series) -> Dict[str, int]:
        """
        计算频次分布
        
        Args:
            user_counts: 用户事件计数Series
            
        Returns:
            频次分布字典
        """
        try:
            # 定义频次区间
            bins = [1, 2, 3, 5, 10, 20, 50, float('inf')]
            labels = ['1', '2', '3-4', '5-9', '10-19', '20-49', '50+']
            
            # 计算分布
            distribution = pd.cut(user_counts, bins=bins, labels=labels, right=False)
            freq_dist = distribution.value_counts().to_dict()
            
            # 确保所有标签都存在
            for label in labels:
                if label not in freq_dist:
                    freq_dist[label] = 0
                    
            return freq_dist
            
        except Exception as e:
            logger.warning(f"计算频次分布失败: {e}")
            return {}
            
    def analyze_event_trends(self,
                           events: Optional[pd.DataFrame] = None,
                           event_types: Optional[List[str]] = None,
                           time_granularity: str = 'daily',
                           min_data_points: int = 7,
                           date_range: Optional[Tuple[str, str]] = None) -> Dict[str, EventTrendResult]:
        """
        分析事件趋势
        
        Args:
            events: 事件数据DataFrame
            event_types: 要分析的事件类型列表
            time_granularity: 时间粒度 ('daily', 'weekly', 'monthly')
            min_data_points: 最少数据点数量
            
        Returns:
            事件趋势分析结果字典
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("Event data not provided and storage manager not initialized")
                    
                filters = {}
                if event_types:
                    filters['event_name'] = event_types
                    
                events = self.storage_manager.get_data('events', filters)
                
            if events.empty:
                logger.warning("Event data is empty, cannot perform trend analysis")
                return {}
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("Missing time field")
                    
            results = {}
            
            # 按事件类型分析趋势
            for event_type in events['event_name'].unique():
                event_data = events[events['event_name'] == event_type]
                
                # 按时间粒度聚合
                trend_data = self._aggregate_by_time(event_data, time_granularity)
                
                if len(trend_data) < min_data_points:
                    logger.warning(f"事件 {event_type} 数据点不足，跳过趋势分析")
                    continue
                    
                # 计算趋势方向和增长率
                trend_direction, growth_rate = self._calculate_trend_direction(trend_data)
                
                # 检测季节性模式
                seasonal_pattern = self._detect_seasonal_pattern(trend_data, time_granularity)
                
                # 检测异常点
                anomalies = self._detect_anomalies(trend_data)
                
                results[event_type] = EventTrendResult(
                    event_name=event_type,
                    trend_data=trend_data,
                    trend_direction=trend_direction,
                    growth_rate=growth_rate,
                    seasonal_pattern=seasonal_pattern,
                    anomalies=anomalies
                )
                
            logger.info(f"完成{len(results)}种事件类型的趋势分析")
            return results
            
        except Exception as e:
            logger.error(f"事件趋势分析失败: {e}")
            raise
            
    def _aggregate_by_time(self, events: pd.DataFrame, granularity: str) -> pd.DataFrame:
        """
        按时间粒度聚合事件数据
        
        Args:
            events: 事件数据
            granularity: 时间粒度
            
        Returns:
            聚合后的时间序列数据
        """
        try:
            # 设置时间索引 - 处理时间戳转换
            events_with_time = events.copy()

            # 如果没有event_datetime列，从event_timestamp创建
            if 'event_datetime' not in events_with_time.columns and 'event_timestamp' in events_with_time.columns:
                # 将微秒时间戳转换为datetime
                events_with_time['event_datetime'] = pd.to_datetime(events_with_time['event_timestamp'], unit='us')
            elif 'event_datetime' not in events_with_time.columns:
                raise ValueError("Missing time information in data: event_datetime or event_timestamp column required")

            events_with_time['date'] = events_with_time['event_datetime'].dt.date
            
            # 支持中英文时间粒度
            granularity_mapping = {
                '日': 'daily',
                '周': 'weekly',
                '月': 'monthly',
                'day': 'daily',
                'week': 'weekly',
                'month': 'monthly'
            }

            normalized_granularity = granularity_mapping.get(granularity, granularity)

            if normalized_granularity == 'daily':
                time_col = events_with_time['event_datetime'].dt.date
            elif normalized_granularity == 'weekly':
                time_col = events_with_time['event_datetime'].dt.to_period('W').dt.start_time.dt.date
            elif normalized_granularity == 'monthly':
                time_col = events_with_time['event_datetime'].dt.to_period('M').dt.start_time.dt.date
            else:
                raise ValueError(f"Unsupported time granularity: {granularity} (支持的格式: daily/日, weekly/周, monthly/月)")
                
            # 聚合数据
            agg_data = events_with_time.groupby(time_col).agg({
                'user_pseudo_id': ['count', 'nunique'],
                'event_name': 'count'
            }).reset_index()
            
            # 重命名列
            agg_data.columns = ['date', 'event_count', 'unique_users', 'total_events']
            agg_data['date'] = pd.to_datetime(agg_data['date'])
            
            # 填充缺失日期
            date_range = pd.date_range(
                start=agg_data['date'].min(),
                end=agg_data['date'].max(),
                freq='D' if normalized_granularity == 'daily' else 'W' if normalized_granularity == 'weekly' else 'M'
            )
            
            full_data = pd.DataFrame({'date': date_range})
            result = full_data.merge(agg_data, on='date', how='left').fillna(0)
            
            return result
            
        except Exception as e:
            logger.error(f"时间聚合失败: {e}")
            raise
            
    def _calculate_trend_direction(self, trend_data: pd.DataFrame) -> Tuple[str, float]:
        """
        计算趋势方向和增长率
        
        Args:
            trend_data: 趋势数据
            
        Returns:
            (趋势方向, 增长率)
        """
        try:
            if len(trend_data) < 2:
                return 'stable', 0.0
                
            # 使用线性回归计算趋势
            x = np.arange(len(trend_data))
            y = trend_data['event_count'].values
            
            # 计算斜率
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # 计算增长率（相对于平均值的百分比）
            mean_value = np.mean(y)
            if mean_value > 0:
                growth_rate = (slope * len(trend_data)) / mean_value * 100
            else:
                growth_rate = 0.0
                
            # 判断趋势方向
            if abs(growth_rate) < 5:  # 5%以内认为是稳定
                direction = 'stable'
            elif growth_rate > 0:
                direction = 'increasing'
            else:
                direction = 'decreasing'
                
            return direction, float(growth_rate)
            
        except Exception as e:
            logger.warning(f"计算趋势方向失败: {e}")
            return 'stable', 0.0
            
    def _detect_seasonal_pattern(self, trend_data: pd.DataFrame, granularity: str) -> Optional[Dict[str, float]]:
        """
        检测季节性模式
        
        Args:
            trend_data: 趋势数据
            granularity: 时间粒度
            
        Returns:
            季节性模式字典
        """
        try:
            if len(trend_data) < 14:  # 需要足够的数据点
                return None
                
            # 根据粒度检测不同的季节性 - 支持中英文
            granularity_mapping = {
                '日': 'daily',
                '周': 'weekly',
                '月': 'monthly',
                'day': 'daily',
                'week': 'weekly',
                'month': 'monthly'
            }

            normalized_granularity = granularity_mapping.get(granularity, granularity)

            if normalized_granularity == 'daily':
                # 检测周模式
                trend_data['weekday'] = trend_data['date'].dt.dayofweek
                pattern = trend_data.groupby('weekday')['event_count'].mean().to_dict()

                # 转换为星期名称
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                seasonal_pattern = {weekday_names[k]: v for k, v in pattern.items()}

            elif normalized_granularity == 'weekly':
                # 检测月模式
                trend_data['week_of_month'] = trend_data['date'].dt.day // 7 + 1
                seasonal_pattern = trend_data.groupby('week_of_month')['event_count'].mean().to_dict()
                
            else:
                # 月度数据检测年度模式
                trend_data['month'] = trend_data['date'].dt.month
                pattern = trend_data.groupby('month')['event_count'].mean().to_dict()
                
                # 转换为月份名称
                month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                seasonal_pattern = {month_names[k-1]: v for k, v in pattern.items()}
                
            return seasonal_pattern
            
        except Exception as e:
            logger.warning(f"季节性模式检测失败: {e}")
            return None
            
    def _detect_anomalies(self, trend_data: pd.DataFrame, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        检测异常点
        
        Args:
            trend_data: 趋势数据
            threshold: 异常检测阈值（标准差倍数）
            
        Returns:
            异常点列表
        """
        try:
            if len(trend_data) < 5:
                return []
                
            values = trend_data['event_count'].values
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val == 0:
                return []
                
            anomalies = []
            
            for idx, value in enumerate(values):
                z_score = abs(value - mean_val) / std_val
                
                if z_score > threshold:
                    anomalies.append({
                        'date': trend_data.iloc[idx]['date'].strftime('%Y-%m-%d'),
                        'value': float(value),
                        'z_score': float(z_score),
                        'type': 'high' if value > mean_val else 'low'
                    })
                    
            return anomalies
            
        except Exception as e:
            logger.warning(f"异常检测失败: {e}")
            return []   
         
    def analyze_event_correlation(self,
                                events: Optional[pd.DataFrame] = None,
                                event_types: Optional[List[str]] = None,
                                date_range: Optional[Tuple[str, str]] = None,
                                 min_co_occurrence: int = 10) -> List[EventCorrelationResult]:
        """
        分析事件关联性
        
        Args:
            events: 事件数据DataFrame
            event_types: 要分析的事件类型列表
            min_co_occurrence: 最小共现次数
            
        Returns:
            事件关联性分析结果列表
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("Event data not provided and storage manager not initialized")
                    
                filters = {}
                if event_types:
                    filters['event_name'] = event_types
                    
                events = self.storage_manager.get_data('events', filters)
                
            if events.empty:
                logger.warning("Event data is empty, cannot perform correlation analysis")
                return []
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("Missing time field")
                    
            results = []
            unique_events = events['event_name'].unique()
            
            # 分析所有事件对的关联性
            for event1, event2 in itertools.combinations(unique_events, 2):
                correlation_result = self._analyze_event_pair_correlation(
                    events, event1, event2, min_co_occurrence
                )
                
                if correlation_result:
                    results.append(correlation_result)
                    
            # 按关联强度排序
            results.sort(key=lambda x: abs(x.correlation_coefficient), reverse=True)
            
            logger.info(f"完成{len(results)}个事件对的关联性分析")
            return results
            
        except Exception as e:
            logger.error(f"事件关联性分析失败: {e}")
            raise
            
    def _analyze_event_pair_correlation(self,
                                      events: pd.DataFrame,
                                      event1: str,
                                      event2: str,
                                      min_co_occurrence: int) -> Optional[EventCorrelationResult]:
        """
        分析单个事件对的关联性
        
        Args:
            events: 事件数据
            event1: 第一个事件
            event2: 第二个事件
            min_co_occurrence: 最小共现次数
            
        Returns:
            事件关联性结果
        """
        try:
            # 获取两个事件的数据
            event1_data = events[events['event_name'] == event1]
            event2_data = events[events['event_name'] == event2]
            
            if event1_data.empty or event2_data.empty:
                return None
                
            # 按用户分组分析共现
            event1_users = set(event1_data['user_pseudo_id'].unique())
            event2_users = set(event2_data['user_pseudo_id'].unique())
            
            # 计算共现用户
            co_occurrence_users = event1_users.intersection(event2_users)
            
            if len(co_occurrence_users) < min_co_occurrence:
                return None
                
            # 计算共现率
            total_users = len(event1_users.union(event2_users))
            co_occurrence_rate = len(co_occurrence_users) / total_users if total_users > 0 else 0
            
            # 计算相关系数（使用卡方检验）
            correlation_coefficient, significance_level = self._calculate_chi_square_correlation(
                events, event1, event2
            )
            
            # 分析时间模式
            temporal_pattern = self._analyze_temporal_pattern(
                events, event1, event2, co_occurrence_users
            )
            
            return EventCorrelationResult(
                event_pair=(event1, event2),
                correlation_coefficient=correlation_coefficient,
                significance_level=significance_level,
                co_occurrence_rate=co_occurrence_rate,
                temporal_pattern=temporal_pattern
            )
            
        except Exception as e:
            logger.warning(f"分析事件对 {event1}-{event2} 关联性失败: {e}")
            return None
            
    def _calculate_chi_square_correlation(self,
                                        events: pd.DataFrame,
                                        event1: str,
                                        event2: str) -> Tuple[float, float]:
        """
        使用卡方检验计算事件相关性
        
        Args:
            events: 事件数据
            event1: 第一个事件
            event2: 第二个事件
            
        Returns:
            (相关系数, 显著性水平)
        """
        try:
            # 创建用户-事件矩阵
            user_events = events.groupby('user_pseudo_id')['event_name'].apply(list).to_dict()
            
            # 构建列联表
            has_event1_and_event2 = 0
            has_event1_not_event2 = 0
            not_event1_has_event2 = 0
            not_event1_not_event2 = 0
            
            for user_id, user_event_list in user_events.items():
                has_event1 = event1 in user_event_list
                has_event2 = event2 in user_event_list
                
                if has_event1 and has_event2:
                    has_event1_and_event2 += 1
                elif has_event1 and not has_event2:
                    has_event1_not_event2 += 1
                elif not has_event1 and has_event2:
                    not_event1_has_event2 += 1
                else:
                    not_event1_not_event2 += 1
                    
            # 构建列联表
            contingency_table = np.array([
                [has_event1_and_event2, has_event1_not_event2],
                [not_event1_has_event2, not_event1_not_event2]
            ])
            
            # 执行卡方检验
            if (contingency_table.sum() > 0 and 
                np.all(contingency_table >= 0) and 
                np.all(contingency_table.sum(axis=0) > 0) and 
                np.all(contingency_table.sum(axis=1) > 0)):
                
                try:
                    chi2, p_value, dof, expected = chi2_contingency(contingency_table)
                    
                    # 检查期望频数是否都大于0
                    if np.all(expected > 0):
                        # 计算Cramér's V作为相关系数
                        n = contingency_table.sum()
                        cramers_v = np.sqrt(chi2 / (n * (min(contingency_table.shape) - 1)))
                        return float(cramers_v), float(p_value)
                    else:
                        return 0.0, 1.0
                except ValueError as ve:
                    logger.warning(f"卡方检验计算错误: {ve}")
                    return 0.0, 1.0
            else:
                return 0.0, 1.0
                
        except Exception as e:
            logger.warning(f"计算卡方相关性失败: {e}")
            return 0.0, 1.0
            
    def _analyze_temporal_pattern(self,
                                events: pd.DataFrame,
                                event1: str,
                                event2: str,
                                co_occurrence_users: set) -> Dict[str, Any]:
        """
        分析事件的时间模式
        
        Args:
            events: 事件数据
            event1: 第一个事件
            event2: 第二个事件
            co_occurrence_users: 共现用户集合
            
        Returns:
            时间模式分析结果
        """
        try:
            # 筛选共现用户的事件
            user_events = events[events['user_pseudo_id'].isin(co_occurrence_users)]
            
            # 分析事件顺序
            sequence_patterns = {'event1_first': 0, 'event2_first': 0, 'simultaneous': 0}
            time_gaps = []
            
            for user_id in co_occurrence_users:
                user_data = user_events[user_events['user_pseudo_id'] == user_id]
                
                event1_times = user_data[user_data['event_name'] == event1]['event_datetime']
                event2_times = user_data[user_data['event_name'] == event2]['event_datetime']
                
                if not event1_times.empty and not event2_times.empty:
                    first_event1 = event1_times.min()
                    first_event2 = event2_times.min()
                    
                    time_diff = (first_event2 - first_event1).total_seconds()
                    
                    if abs(time_diff) < 60:  # 1分钟内认为是同时发生
                        sequence_patterns['simultaneous'] += 1
                    elif time_diff > 0:
                        sequence_patterns['event1_first'] += 1
                        time_gaps.append(time_diff)
                    else:
                        sequence_patterns['event2_first'] += 1
                        time_gaps.append(abs(time_diff))
                        
            # 计算平均时间间隔
            avg_time_gap = np.mean(time_gaps) if time_gaps else 0
            
            return {
                'sequence_patterns': sequence_patterns,
                'avg_time_gap_seconds': float(avg_time_gap),
                'median_time_gap_seconds': float(np.median(time_gaps)) if time_gaps else 0
            }
            
        except Exception as e:
            logger.warning(f"时间模式分析失败: {e}")
            return {}
            
    def identify_key_events(self,
                          events: Optional[pd.DataFrame] = None,
                          users: Optional[pd.DataFrame] = None,
                          sessions: Optional[pd.DataFrame] = None,
                          top_k: int = 10) -> List[KeyEventResult]:
        """
        识别关键事件
        
        Args:
            events: 事件数据DataFrame
            users: 用户数据DataFrame
            sessions: 会话数据DataFrame
            top_k: 返回前K个关键事件
            
        Returns:
            关键事件识别结果列表
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("Event data not provided and storage manager not initialized")
                events = self.storage_manager.get_data('events')
                
            if users is None and self.storage_manager:
                users = self.storage_manager.get_data('users')
                
            if sessions is None and self.storage_manager:
                sessions = self.storage_manager.get_data('sessions')
                
            if events.empty:
                logger.warning("Event data is empty, cannot identify key events")
                return []
                
            results = []
            
            # 分析每个事件类型
            for event_type in events['event_name'].unique():
                key_event_result = self._analyze_event_importance(
                    events, users, sessions, event_type
                )
                
                if key_event_result:
                    results.append(key_event_result)
                    
            # 按重要性得分排序
            results.sort(key=lambda x: x.importance_score, reverse=True)
            
            logger.info(f"完成{len(results)}个事件的重要性分析")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"关键事件识别失败: {e}")
            raise
            
    def _analyze_event_importance(self,
                                events: pd.DataFrame,
                                users: Optional[pd.DataFrame],
                                sessions: Optional[pd.DataFrame],
                                event_type: str) -> Optional[KeyEventResult]:
        """
        分析单个事件的重要性
        
        Args:
            events: 事件数据
            users: 用户数据
            sessions: 会话数据
            event_type: 事件类型
            
        Returns:
            关键事件结果
        """
        try:
            event_data = events[events['event_name'] == event_type]
            
            if event_data.empty:
                return None
                
            # 计算用户参与度影响
            user_engagement_impact = self._calculate_user_engagement_impact(
                events, event_data, event_type
            )
            
            # 计算转化影响
            conversion_impact = self._calculate_conversion_impact(
                events, sessions, event_type
            )
            
            # 计算留存影响
            retention_impact = self._calculate_retention_impact(
                events, users, event_type
            )
            
            # 计算综合重要性得分
            importance_score = (
                user_engagement_impact * 0.4 +
                conversion_impact * 0.4 +
                retention_impact * 0.2
            )
            
            # 生成重要性原因
            reasons = self._generate_importance_reasons(
                user_engagement_impact, conversion_impact, retention_impact, event_type
            )
            
            return KeyEventResult(
                event_name=event_type,
                importance_score=importance_score,
                user_engagement_impact=user_engagement_impact,
                conversion_impact=conversion_impact,
                retention_impact=retention_impact,
                reasons=reasons
            )
            
        except Exception as e:
            logger.warning(f"分析事件 {event_type} 重要性失败: {e}")
            return None
            
    def _calculate_user_engagement_impact(self,
                                        all_events: pd.DataFrame,
                                        event_data: pd.DataFrame,
                                        event_type: str) -> float:
        """
        计算用户参与度影响
        
        Args:
            all_events: 所有事件数据
            event_data: 特定事件数据
            event_type: 事件类型
            
        Returns:
            参与度影响得分 (0-100)
        """
        try:
            # 计算事件频次得分
            total_events = len(all_events)
            event_count = len(event_data)
            frequency_score = (event_count / total_events * 100) if total_events > 0 else 0
            
            # 计算用户覆盖率得分
            total_users = all_events['user_pseudo_id'].nunique()
            event_users = event_data['user_pseudo_id'].nunique()
            coverage_score = (event_users / total_users * 100) if total_users > 0 else 0
            
            # 计算用户粘性得分（平均每用户事件数）
            if event_users > 0:
                avg_events_per_user = event_count / event_users
                # 标准化到0-100范围
                stickiness_score = min(avg_events_per_user * 10, 100)
            else:
                stickiness_score = 0
                
            # 综合得分
            engagement_impact = (frequency_score * 0.3 + coverage_score * 0.4 + stickiness_score * 0.3)
            
            return min(engagement_impact, 100.0)
            
        except Exception as e:
            logger.warning(f"计算用户参与度影响失败: {e}")
            return 0.0
            
    def _calculate_conversion_impact(self,
                                   all_events: pd.DataFrame,
                                   sessions: Optional[pd.DataFrame],
                                   event_type: str) -> float:
        """
        计算转化影响
        
        Args:
            all_events: 所有事件数据
            sessions: 会话数据
            event_type: 事件类型
            
        Returns:
            转化影响得分 (0-100)
        """
        try:
            # 如果是转化事件，直接给高分
            if event_type in self.conversion_events:
                return 90.0
                
            # 分析事件与转化的关联性
            event_users = set(all_events[all_events['event_name'] == event_type]['user_pseudo_id'])
            
            conversion_impact_score = 0.0
            
            # 计算与转化事件的关联度
            for conv_event in self.conversion_events:
                conv_users = set(all_events[all_events['event_name'] == conv_event]['user_pseudo_id'])
                
                if conv_users:
                    # 计算重叠用户比例
                    overlap_users = event_users.intersection(conv_users)
                    overlap_rate = len(overlap_users) / len(conv_users) if conv_users else 0
                    
                    # 累加关联度得分
                    conversion_impact_score += overlap_rate * 20  # 每个转化事件最多贡献20分
                    
            # 使用会话数据分析转化影响
            if sessions is not None and not sessions.empty and 'conversions' in sessions.columns:
                # 分析有该事件的会话的转化率
                event_sessions = sessions[sessions['user_pseudo_id'].isin(event_users)]
                if not event_sessions.empty:
                    event_conversion_rate = (event_sessions['conversions'] > 0).mean()
                    
                    # 与整体转化率比较
                    overall_conversion_rate = (sessions['conversions'] > 0).mean()
                    
                    if overall_conversion_rate > 0:
                        conversion_lift = event_conversion_rate / overall_conversion_rate
                        conversion_impact_score += min(conversion_lift * 30, 30)  # 最多贡献30分
                        
            return min(conversion_impact_score, 100.0)
            
        except Exception as e:
            logger.warning(f"计算转化影响失败: {e}")
            return 0.0
            
    def _calculate_retention_impact(self,
                                  all_events: pd.DataFrame,
                                  users: Optional[pd.DataFrame],
                                  event_type: str) -> float:
        """
        计算留存影响
        
        Args:
            all_events: 所有事件数据
            users: 用户数据
            event_type: 事件类型
            
        Returns:
            留存影响得分 (0-100)
        """
        try:
            if 'event_datetime' not in all_events.columns:
                if 'event_timestamp' in all_events.columns:
                    all_events['event_datetime'] = pd.to_datetime(all_events['event_timestamp'], unit='us')
                else:
                    return 0.0
                    
            # 分析有该事件的用户的留存情况
            event_users = set(all_events[all_events['event_name'] == event_type]['user_pseudo_id'])
            
            if not event_users:
                return 0.0
                
            # 计算用户的活跃天数
            user_activity = all_events.groupby('user_pseudo_id')['event_datetime'].agg(['min', 'max'])
            user_activity['active_days'] = (user_activity['max'] - user_activity['min']).dt.days + 1
            
            # 比较有该事件的用户与整体用户的活跃天数
            event_user_activity = user_activity[user_activity.index.isin(event_users)]['active_days']
            overall_user_activity = user_activity['active_days']
            
            if len(event_user_activity) > 0 and len(overall_user_activity) > 0:
                event_avg_active_days = event_user_activity.mean()
                overall_avg_active_days = overall_user_activity.mean()
                
                if overall_avg_active_days > 0:
                    retention_lift = event_avg_active_days / overall_avg_active_days
                    retention_impact = min(retention_lift * 50, 100)  # 标准化到0-100
                else:
                    retention_impact = 0.0
            else:
                retention_impact = 0.0
                
            return retention_impact
            
        except Exception as e:
            logger.warning(f"计算留存影响失败: {e}")
            return 0.0
            
    def _generate_importance_reasons(self,
                                   user_engagement_impact: float,
                                   conversion_impact: float,
                                   retention_impact: float,
                                   event_type: str) -> List[str]:
        """
        生成重要性原因
        
        Args:
            user_engagement_impact: 用户参与度影响
            conversion_impact: 转化影响
            retention_impact: 留存影响
            event_type: 事件类型
            
        Returns:
            重要性原因列表
        """
        reasons = []
        
        if user_engagement_impact > 70:
            reasons.append(LocalizedInsightGenerator.format_event_reason('very_high_engagement'))
        elif user_engagement_impact > 50:
            reasons.append(LocalizedInsightGenerator.format_event_reason('high_engagement'))
            
        if conversion_impact > 70:
            reasons.append(LocalizedInsightGenerator.format_event_reason('high_conversion_impact'))
        elif conversion_impact > 50:
            reasons.append(LocalizedInsightGenerator.format_event_reason('moderate_conversion_impact'))
            
        if retention_impact > 70:
            reasons.append(LocalizedInsightGenerator.format_event_reason('high_retention_impact'))
        elif retention_impact > 50:
            reasons.append(LocalizedInsightGenerator.format_event_reason('moderate_retention_impact'))
            
        if event_type in self.conversion_events:
            reasons.append(LocalizedInsightGenerator.format_event_reason('conversion_event'))
            
        if event_type in self.engagement_events:
            reasons.append(LocalizedInsightGenerator.format_event_reason('engagement_event'))
            
        if not reasons:
            reasons.append(LocalizedInsightGenerator.format_event_reason('basic_event'))
            
        return reasons
        
    def analyze_events(self, events: pd.DataFrame) -> Dict[str, Any]:
        """
        执行事件分析（集成管理器接口）
        
        Args:
            events: 事件数据DataFrame
            
        Returns:
            事件分析结果字典
        """
        try:
            if events.empty:
                return {
                    'status': 'error',
                    'message': '事件数据为空',
                    'insights': [],
                    'recommendations': []
                }
            
            # 获取事件类型
            event_types = events['event_name'].unique().tolist() if 'event_name' in events.columns else []
            
            # 执行各种分析
            frequency_results = self.calculate_event_frequency(events, event_types)
            trend_results = self.analyze_event_trends(events, event_types)
            correlation_results = self.analyze_event_correlation(events, event_types)
            key_events = self.identify_key_events(events)
            
            # 生成洞察和建议
            insights = []
            recommendations = []
            
            # 基于频次分析生成洞察
            if frequency_results:
                top_events = sorted(frequency_results.items(), key=lambda x: x[1].total_count if hasattr(x[1], 'total_count') else 0, reverse=True)[:3]
                event_types = [event for event, _ in top_events]
                insights.append(LocalizedInsightGenerator.format_event_activity_insight(event_types))
                
                if len(frequency_results) > 5:
                    recommendations.append(LocalizedInsightGenerator.format_high_frequency_recommendation())
            
            # 基于趋势分析生成洞察
            if trend_results:
                increasing_trends = [event for event, data in trend_results.items() 
                                   if (hasattr(data, 'trend_direction') and data.trend_direction == 'increasing') or 
                                      (isinstance(data, dict) and data.get('trend_direction') == 'increasing')]
                if increasing_trends:
                    insights.append(LocalizedInsightGenerator.format_trend_insight(increasing_trends))
                    recommendations.append(LocalizedInsightGenerator.format_trend_recommendation())
            
            # 基于关联性分析生成洞察
            if correlation_results:
                strong_correlations = []
                if isinstance(correlation_results, dict):
                    for pair, corr in correlation_results.items():
                        corr_coeff = 0
                        if hasattr(corr, 'correlation_coefficient'):
                            corr_coeff = corr.correlation_coefficient
                        elif isinstance(corr, dict):
                            corr_coeff = corr.get('correlation_coefficient', 0)
                        
                        if abs(corr_coeff) > 0.5:
                            if isinstance(pair, tuple) and len(pair) == 2:
                                strong_correlations.append(f"{pair[0]}-{pair[1]}")
                
                if strong_correlations:
                    insights.append(LocalizedInsightGenerator.format_correlation_insight(strong_correlations))
                    recommendations.append(LocalizedInsightGenerator.format_correlation_recommendation())
            
            # 基于关键事件生成洞察
            if key_events:
                insights.append(LocalizedInsightGenerator.format_key_events_insight(len(key_events)))
                recommendations.append(LocalizedInsightGenerator.format_key_events_recommendation())
            
            return {
                'status': 'success',
                'analysis_type': 'event_analysis',
                'data_size': len(events),
                'event_types_count': len(event_types),
                'insights': insights,
                'recommendations': recommendations,
                'detailed_results': {
                    'frequency_analysis': frequency_results,
                    'trend_analysis': trend_results,
                    'correlation_analysis': correlation_results,
                    'key_events': key_events
                },
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"事件分析执行失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'insights': [],
                'recommendations': []
            }
        
    def analyze_event_frequency(self, events: Optional[pd.DataFrame] = None, event_types: Optional[List[str]] = None, date_range: Optional[Tuple[str, str]] = None) -> Dict[str, EventFrequencyResult]:
        """
        分析事件频次（代理方法）
        
        Args:
            events: 事件数据
            event_types: 事件类型列表
            date_range: 日期范围
            
        Returns:
            事件频次分析结果
        """
        return self.calculate_event_frequency(events=events, event_types=event_types, date_range=date_range)

    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        获取分析摘要
        
        Returns:
            分析摘要字典
        """
        try:
            if self.storage_manager is None:
                return {"error": "Storage manager not initialized"}
                
            events = self.storage_manager.get_data('events')
            
            if events.empty:
                return {"error": "无事件数据"}
                
            # 基础统计
            total_events = len(events)
            unique_users = events['user_pseudo_id'].nunique()
            unique_event_types = events['event_name'].nunique()
            
            # 热门事件
            top_events = events['event_name'].value_counts().head(5).to_dict()
            
            # 时间范围
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                    
            if 'event_datetime' in events.columns:
                date_range = {
                    'start': events['event_datetime'].min().strftime('%Y-%m-%d'),
                    'end': events['event_datetime'].max().strftime('%Y-%m-%d')
                }
            else:
                date_range = {'start': 'N/A', 'end': 'N/A'}
                
            return {
                'total_events': total_events,
                'unique_users': unique_users,
                'unique_event_types': unique_event_types,
                'top_events': top_events,
                'date_range': date_range,
                'analysis_capabilities': [
                    'event_frequency_analysis',
                    'event_trend_analysis', 
                    'event_correlation_analysis',
                    'key_event_identification'
                ]
            }
            
        except Exception as e:
            logger.error(f"获取分析摘要失败: {e}")
            return {"error": str(e)}