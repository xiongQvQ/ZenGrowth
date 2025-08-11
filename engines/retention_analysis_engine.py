"""
留存分析引擎模块

提供用户队列构建和留存率计算功能。
支持日/周/月留存分析和队列分析。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


@dataclass
class CohortData:
    """队列数据模型"""
    cohort_period: str
    cohort_size: int
    first_activity_date: datetime
    retention_periods: List[int]
    retention_rates: List[float]
    retention_counts: List[int]


@dataclass
class RetentionAnalysisResult:
    """留存分析结果"""
    analysis_type: str  # 'daily', 'weekly', 'monthly'
    cohorts: List[CohortData]
    overall_retention_rates: Dict[int, float]
    retention_matrix: pd.DataFrame
    summary_stats: Dict[str, Any]


@dataclass
class UserRetentionProfile:
    """用户留存档案"""
    user_id: str
    first_activity_date: datetime
    last_activity_date: datetime
    total_active_days: int
    retention_periods: List[int]
    activity_pattern: Dict[str, Any]
    churn_risk_score: float


class RetentionAnalysisEngine:
    """留存分析引擎类"""
    
    def __init__(self, storage_manager=None):
        """
        初始化留存分析引擎
        
        Args:
            storage_manager: 数据存储管理器实例
        """
        self.storage_manager = storage_manager
        
        logger.info("留存分析引擎初始化完成")
        
    def build_user_cohorts(self,
                          events: Optional[pd.DataFrame] = None,
                          cohort_period: str = 'monthly',
                          min_cohort_size: int = 10) -> Dict[str, List[str]]:
        """
        构建用户队列
        
        Args:
            events: 事件数据DataFrame
            cohort_period: 队列周期 ('daily', 'weekly', 'monthly')
            min_cohort_size: 最小队列大小
            
        Returns:
            队列字典 {cohort_period: [user_ids]}
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if events.empty:
                logger.warning("事件数据为空，无法构建用户队列")
                return {}
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("缺少时间字段")
                    
            # 计算每个用户的首次活动时间
            user_first_activity = events.groupby('user_pseudo_id')['event_datetime'].min().reset_index()
            user_first_activity.columns = ['user_id', 'first_activity_date']
            
            # 根据队列周期分组用户
            cohorts = {}
            
            for _, user in user_first_activity.iterrows():
                cohort_key = self._get_cohort_key(user['first_activity_date'], cohort_period)
                
                if cohort_key not in cohorts:
                    cohorts[cohort_key] = []
                    
                cohorts[cohort_key].append(user['user_id'])
                
            # 过滤小队列
            filtered_cohorts = {
                key: users for key, users in cohorts.items() 
                if len(users) >= min_cohort_size
            }
            
            logger.info(f"构建了{len(filtered_cohorts)}个用户队列")
            return filtered_cohorts
            
        except Exception as e:
            logger.error(f"构建用户队列失败: {e}")
            raise
            
    def _get_cohort_key(self, date: datetime, period: str) -> str:
        """
        获取队列键值
        
        Args:
            date: 日期
            period: 周期类型
            
        Returns:
            队列键值字符串
        """
        if period == 'daily':
            return date.strftime('%Y-%m-%d')
        elif period == 'weekly':
            # 获取周的开始日期（周一）
            start_of_week = date - timedelta(days=date.weekday())
            return start_of_week.strftime('%Y-W%U')
        elif period == 'monthly':
            return date.strftime('%Y-%m')
        else:
            raise ValueError(f"不支持的队列周期: {period}")
            
    def calculate_retention_rates(self,
                                events: Optional[pd.DataFrame] = None,
                                analysis_type: str = 'monthly',
                                max_periods: int = 12) -> RetentionAnalysisResult:
        """
        计算留存率
        
        Args:
            events: 事件数据DataFrame
            analysis_type: 分析类型 ('daily', 'weekly', 'monthly')
            max_periods: 最大分析周期数
            
        Returns:
            留存分析结果
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if events.empty:
                logger.warning("事件数据为空，无法计算留存率")
                return RetentionAnalysisResult(
                    analysis_type=analysis_type,
                    cohorts=[],
                    overall_retention_rates={},
                    retention_matrix=pd.DataFrame(),
                    summary_stats={}
                )
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("缺少时间字段")
                    
            # 构建用户队列
            cohorts_dict = self.build_user_cohorts(events, analysis_type)
            
            if not cohorts_dict:
                logger.warning("没有足够的队列数据进行留存分析")
                return RetentionAnalysisResult(
                    analysis_type=analysis_type,
                    cohorts=[],
                    overall_retention_rates={},
                    retention_matrix=pd.DataFrame(),
                    summary_stats={}
                )
                
            # 计算每个队列的留存率
            cohort_results = []
            retention_matrix_data = []
            
            for cohort_period, user_ids in cohorts_dict.items():
                cohort_data = self._calculate_cohort_retention(
                    events, user_ids, cohort_period, analysis_type, max_periods
                )
                
                if cohort_data:
                    cohort_results.append(cohort_data)
                    
                    # 为留存矩阵准备数据
                    matrix_row = {
                        'cohort': cohort_period,
                        'cohort_size': cohort_data.cohort_size
                    }
                    
                    for i, rate in enumerate(cohort_data.retention_rates):
                        matrix_row[f'period_{i}'] = rate
                        
                    retention_matrix_data.append(matrix_row)
                    
            # 创建留存矩阵
            retention_matrix = pd.DataFrame(retention_matrix_data)
            if not retention_matrix.empty:
                retention_matrix = retention_matrix.set_index('cohort')
                
            # 计算整体留存率
            overall_retention_rates = self._calculate_overall_retention_rates(cohort_results)
            
            # 计算摘要统计
            summary_stats = self._calculate_retention_summary_stats(cohort_results)
            
            result = RetentionAnalysisResult(
                analysis_type=analysis_type,
                cohorts=cohort_results,
                overall_retention_rates=overall_retention_rates,
                retention_matrix=retention_matrix,
                summary_stats=summary_stats
            )
            
            logger.info(f"完成{analysis_type}留存分析，包含{len(cohort_results)}个队列")
            return result
            
        except Exception as e:
            logger.error(f"计算留存率失败: {e}")
            raise
            
    def _calculate_cohort_retention(self,
                                  events: pd.DataFrame,
                                  user_ids: List[str],
                                  cohort_period: str,
                                  analysis_type: str,
                                  max_periods: int) -> Optional[CohortData]:
        """
        计算单个队列的留存率
        
        Args:
            events: 事件数据
            user_ids: 队列用户ID列表
            cohort_period: 队列周期
            analysis_type: 分析类型
            max_periods: 最大周期数
            
        Returns:
            队列数据
        """
        try:
            # 筛选队列用户的事件
            cohort_events = events[events['user_pseudo_id'].isin(user_ids)]
            
            if cohort_events.empty:
                return None
                
            # 获取队列的首次活动日期
            first_activity_date = cohort_events['event_datetime'].min()
            
            # 计算每个用户在各个周期的活动情况
            user_activity_periods = self._calculate_user_activity_periods(
                cohort_events, first_activity_date, analysis_type, max_periods
            )
            
            # 计算留存率
            retention_periods = list(range(max_periods))
            retention_counts = []
            retention_rates = []
            
            cohort_size = len(user_ids)
            
            for period in retention_periods:
                active_users = sum(1 for user_periods in user_activity_periods.values() 
                                 if period in user_periods)
                retention_counts.append(active_users)
                retention_rates.append(active_users / cohort_size if cohort_size > 0 else 0)
                
            return CohortData(
                cohort_period=cohort_period,
                cohort_size=cohort_size,
                first_activity_date=first_activity_date,
                retention_periods=retention_periods,
                retention_rates=retention_rates,
                retention_counts=retention_counts
            )
            
        except Exception as e:
            logger.warning(f"计算队列 {cohort_period} 留存率失败: {e}")
            return None
            
    def _calculate_user_activity_periods(self,
                                       events: pd.DataFrame,
                                       cohort_start_date: datetime,
                                       analysis_type: str,
                                       max_periods: int) -> Dict[str, List[int]]:
        """
        计算用户在各个周期的活动情况
        
        Args:
            events: 事件数据
            cohort_start_date: 队列开始日期
            analysis_type: 分析类型
            max_periods: 最大周期数
            
        Returns:
            用户活动周期字典 {user_id: [active_periods]}
        """
        try:
            user_activity_periods = defaultdict(set)
            
            # 计算周期长度
            if analysis_type == 'daily':
                period_delta = timedelta(days=1)
            elif analysis_type == 'weekly':
                period_delta = timedelta(weeks=1)
            elif analysis_type == 'monthly':
                period_delta = timedelta(days=30)  # 简化为30天
            else:
                raise ValueError(f"不支持的分析类型: {analysis_type}")
                
            # 为每个事件计算所属周期
            for _, event in events.iterrows():
                event_date = event['event_datetime']
                user_id = event['user_pseudo_id']
                
                # 计算事件距离队列开始的周期数
                time_diff = event_date - cohort_start_date
                
                if analysis_type == 'daily':
                    period = time_diff.days
                elif analysis_type == 'weekly':
                    period = time_diff.days // 7
                elif analysis_type == 'monthly':
                    period = time_diff.days // 30
                    
                # 只记录在分析范围内的周期
                if 0 <= period < max_periods:
                    user_activity_periods[user_id].add(period)
                    
            # 转换为列表格式
            return {user_id: list(periods) for user_id, periods in user_activity_periods.items()}
            
        except Exception as e:
            logger.warning(f"计算用户活动周期失败: {e}")
            return {}
            
    def _calculate_overall_retention_rates(self, cohorts: List[CohortData]) -> Dict[int, float]:
        """
        计算整体留存率
        
        Args:
            cohorts: 队列数据列表
            
        Returns:
            整体留存率字典 {period: retention_rate}
        """
        try:
            if not cohorts:
                return {}
                
            # 获取最大周期数
            max_periods = max(len(cohort.retention_rates) for cohort in cohorts)
            
            overall_rates = {}
            
            for period in range(max_periods):
                total_users = 0
                active_users = 0
                
                for cohort in cohorts:
                    if period < len(cohort.retention_counts):
                        total_users += cohort.cohort_size
                        active_users += cohort.retention_counts[period]
                        
                overall_rates[period] = active_users / total_users if total_users > 0 else 0
                
            return overall_rates
            
        except Exception as e:
            logger.warning(f"计算整体留存率失败: {e}")
            return {}
            
    def _calculate_retention_summary_stats(self, cohorts: List[CohortData]) -> Dict[str, Any]:
        """
        计算留存摘要统计
        
        Args:
            cohorts: 队列数据列表
            
        Returns:
            摘要统计字典
        """
        try:
            if not cohorts:
                return {}
                
            # 基础统计
            total_cohorts = len(cohorts)
            total_users = sum(cohort.cohort_size for cohort in cohorts)
            avg_cohort_size = total_users / total_cohorts if total_cohorts > 0 else 0
            
            # 留存率统计
            all_retention_rates = []
            for cohort in cohorts:
                all_retention_rates.extend(cohort.retention_rates[1:])  # 排除第0期（100%）
                
            if all_retention_rates:
                avg_retention_rate = np.mean(all_retention_rates)
                median_retention_rate = np.median(all_retention_rates)
                min_retention_rate = np.min(all_retention_rates)
                max_retention_rate = np.max(all_retention_rates)
            else:
                avg_retention_rate = median_retention_rate = min_retention_rate = max_retention_rate = 0
                
            # 队列大小统计
            cohort_sizes = [cohort.cohort_size for cohort in cohorts]
            min_cohort_size = min(cohort_sizes) if cohort_sizes else 0
            max_cohort_size = max(cohort_sizes) if cohort_sizes else 0
            
            return {
                'total_cohorts': total_cohorts,
                'total_users': total_users,
                'avg_cohort_size': avg_cohort_size,
                'min_cohort_size': min_cohort_size,
                'max_cohort_size': max_cohort_size,
                'avg_retention_rate': avg_retention_rate,
                'median_retention_rate': median_retention_rate,
                'min_retention_rate': min_retention_rate,
                'max_retention_rate': max_retention_rate
            }
            
        except Exception as e:
            logger.warning(f"计算留存摘要统计失败: {e}")
            return {}
            
    def analyze_daily_retention(self,
                              events: Optional[pd.DataFrame] = None,
                              max_days: int = 30) -> RetentionAnalysisResult:
        """
        分析日留存
        
        Args:
            events: 事件数据DataFrame
            max_days: 最大分析天数
            
        Returns:
            日留存分析结果
        """
        try:
            return self.calculate_retention_rates(
                events=events,
                analysis_type='daily',
                max_periods=max_days
            )
            
        except Exception as e:
            logger.error(f"日留存分析失败: {e}")
            raise
            
    def analyze_weekly_retention(self,
                               events: Optional[pd.DataFrame] = None,
                               max_weeks: int = 12) -> RetentionAnalysisResult:
        """
        分析周留存
        
        Args:
            events: 事件数据DataFrame
            max_weeks: 最大分析周数
            
        Returns:
            周留存分析结果
        """
        try:
            return self.calculate_retention_rates(
                events=events,
                analysis_type='weekly',
                max_periods=max_weeks
            )
            
        except Exception as e:
            logger.error(f"周留存分析失败: {e}")
            raise
            
    def analyze_monthly_retention(self,
                                events: Optional[pd.DataFrame] = None,
                                max_months: int = 12) -> RetentionAnalysisResult:
        """
        分析月留存
        
        Args:
            events: 事件数据DataFrame
            max_months: 最大分析月数
            
        Returns:
            月留存分析结果
        """
        try:
            return self.calculate_retention_rates(
                events=events,
                analysis_type='monthly',
                max_periods=max_months
            )
            
        except Exception as e:
            logger.error(f"月留存分析失败: {e}")
            raise 
           
    def create_user_retention_profiles(self,
                                     events: Optional[pd.DataFrame] = None,
                                     users: Optional[pd.DataFrame] = None) -> List[UserRetentionProfile]:
        """
        创建用户留存档案
        
        Args:
            events: 事件数据DataFrame
            users: 用户数据DataFrame
            
        Returns:
            用户留存档案列表
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if users is None and self.storage_manager:
                users = self.storage_manager.get_data('users')
                
            if events.empty:
                logger.warning("事件数据为空，无法创建用户留存档案")
                return []
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("缺少时间字段")
                    
            profiles = []
            
            # 按用户分组分析
            for user_id in events['user_pseudo_id'].unique():
                user_events = events[events['user_pseudo_id'] == user_id].sort_values('event_datetime')
                
                if user_events.empty:
                    continue
                    
                # 基础信息
                first_activity = user_events['event_datetime'].min()
                last_activity = user_events['event_datetime'].max()
                
                # 计算活跃天数
                active_days = self._calculate_user_active_days(user_events)
                
                # 计算留存周期
                retention_periods = self._calculate_user_retention_periods(user_events, first_activity)
                
                # 分析活动模式
                activity_pattern = self._analyze_user_activity_pattern(user_events)
                
                # 计算流失风险得分
                churn_risk_score = self._calculate_churn_risk_score(
                    user_events, last_activity, activity_pattern
                )
                
                profile = UserRetentionProfile(
                    user_id=user_id,
                    first_activity_date=first_activity,
                    last_activity_date=last_activity,
                    total_active_days=active_days,
                    retention_periods=retention_periods,
                    activity_pattern=activity_pattern,
                    churn_risk_score=churn_risk_score
                )
                
                profiles.append(profile)
                
            logger.info(f"创建了{len(profiles)}个用户留存档案")
            return profiles
            
        except Exception as e:
            logger.error(f"创建用户留存档案失败: {e}")
            raise
            
    def _calculate_user_active_days(self, user_events: pd.DataFrame) -> int:
        """
        计算用户活跃天数
        
        Args:
            user_events: 用户事件数据
            
        Returns:
            活跃天数
        """
        try:
            # 获取用户活跃的唯一日期
            active_dates = user_events['event_datetime'].dt.date.unique()
            return len(active_dates)
            
        except Exception as e:
            logger.warning(f"计算用户活跃天数失败: {e}")
            return 0
            
    def _calculate_user_retention_periods(self,
                                        user_events: pd.DataFrame,
                                        first_activity: datetime) -> List[int]:
        """
        计算用户留存周期
        
        Args:
            user_events: 用户事件数据
            first_activity: 首次活动时间
            
        Returns:
            留存周期列表
        """
        try:
            retention_periods = set()
            
            for _, event in user_events.iterrows():
                days_since_first = (event['event_datetime'] - first_activity).days
                week_period = days_since_first // 7
                retention_periods.add(week_period)
                
            return sorted(list(retention_periods))
            
        except Exception as e:
            logger.warning(f"计算用户留存周期失败: {e}")
            return []
            
    def _analyze_user_activity_pattern(self, user_events: pd.DataFrame) -> Dict[str, Any]:
        """
        分析用户活动模式
        
        Args:
            user_events: 用户事件数据
            
        Returns:
            活动模式字典
        """
        try:
            # 计算活动频率
            total_days = (user_events['event_datetime'].max() - user_events['event_datetime'].min()).days + 1
            active_days = len(user_events['event_datetime'].dt.date.unique())
            activity_frequency = active_days / total_days if total_days > 0 else 0
            
            # 分析活动强度
            events_per_day = len(user_events) / active_days if active_days > 0 else 0
            
            # 分析活动规律性（计算活动间隔的标准差）
            daily_events = user_events.groupby(user_events['event_datetime'].dt.date).size()
            activity_regularity = 1 / (daily_events.std() + 1) if len(daily_events) > 1 else 1
            
            # 分析最近活动趋势
            recent_activity_trend = self._calculate_recent_activity_trend(user_events)
            
            # 分析事件类型多样性
            event_diversity = len(user_events['event_name'].unique()) / len(user_events['event_name']) if len(user_events) > 0 else 0
            
            return {
                'activity_frequency': activity_frequency,
                'events_per_day': events_per_day,
                'activity_regularity': activity_regularity,
                'recent_activity_trend': recent_activity_trend,
                'event_diversity': event_diversity,
                'total_events': len(user_events),
                'unique_event_types': len(user_events['event_name'].unique())
            }
            
        except Exception as e:
            logger.warning(f"分析用户活动模式失败: {e}")
            return {}
            
    def _calculate_recent_activity_trend(self, user_events: pd.DataFrame, days: int = 7) -> str:
        """
        计算最近活动趋势
        
        Args:
            user_events: 用户事件数据
            days: 分析天数
            
        Returns:
            趋势描述 ('increasing', 'decreasing', 'stable')
        """
        try:
            # 获取最近N天的活动
            cutoff_date = user_events['event_datetime'].max() - timedelta(days=days)
            recent_events = user_events[user_events['event_datetime'] >= cutoff_date]
            
            if len(recent_events) < 2:
                return 'stable'
                
            # 按天分组计算活动量
            daily_activity = recent_events.groupby(recent_events['event_datetime'].dt.date).size()
            
            if len(daily_activity) < 2:
                return 'stable'
                
            # 计算趋势
            x = np.arange(len(daily_activity))
            y = daily_activity.values
            
            # 简单线性回归
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception as e:
            logger.warning(f"计算最近活动趋势失败: {e}")
            return 'stable'
            
    def _calculate_churn_risk_score(self,
                                  user_events: pd.DataFrame,
                                  last_activity: datetime,
                                  activity_pattern: Dict[str, Any]) -> float:
        """
        计算流失风险得分
        
        Args:
            user_events: 用户事件数据
            last_activity: 最后活动时间
            activity_pattern: 活动模式
            
        Returns:
            流失风险得分 (0-100, 越高风险越大)
        """
        try:
            risk_score = 0.0
            
            # 1. 最后活动时间距今天数 (40%权重)
            days_since_last_activity = (datetime.now() - last_activity).days
            if days_since_last_activity > 30:
                risk_score += 40
            elif days_since_last_activity > 14:
                risk_score += 30
            elif days_since_last_activity > 7:
                risk_score += 20
            elif days_since_last_activity > 3:
                risk_score += 10
                
            # 2. 活动频率 (25%权重)
            activity_frequency = activity_pattern.get('activity_frequency', 0)
            if activity_frequency < 0.1:  # 活动频率低于10%
                risk_score += 25
            elif activity_frequency < 0.3:
                risk_score += 15
            elif activity_frequency < 0.5:
                risk_score += 10
                
            # 3. 最近活动趋势 (20%权重)
            recent_trend = activity_pattern.get('recent_activity_trend', 'stable')
            if recent_trend == 'decreasing':
                risk_score += 20
            elif recent_trend == 'stable':
                risk_score += 10
                
            # 4. 活动强度 (15%权重)
            events_per_day = activity_pattern.get('events_per_day', 0)
            if events_per_day < 1:
                risk_score += 15
            elif events_per_day < 3:
                risk_score += 10
            elif events_per_day < 5:
                risk_score += 5
                
            return min(risk_score, 100.0)
            
        except Exception as e:
            logger.warning(f"计算流失风险得分失败: {e}")
            return 50.0  # 默认中等风险
            
    def get_retention_insights(self,
                             retention_result: RetentionAnalysisResult) -> Dict[str, Any]:
        """
        获取留存分析洞察
        
        Args:
            retention_result: 留存分析结果
            
        Returns:
            洞察字典
        """
        try:
            insights = {
                'key_metrics': {},
                'trends': {},
                'recommendations': [],
                'risk_factors': []
            }
            
            if not retention_result.cohorts:
                insights['recommendations'].append("数据不足，建议收集更多用户行为数据")
                return insights
                
            # 关键指标
            overall_rates = retention_result.overall_retention_rates
            if overall_rates:
                # 第1期留存率（通常是次日/次周/次月留存）
                first_period_retention = overall_rates.get(1, 0)
                insights['key_metrics']['first_period_retention'] = first_period_retention
                
                # 长期留存率（最后一期）
                last_period = max(overall_rates.keys())
                long_term_retention = overall_rates.get(last_period, 0)
                insights['key_metrics']['long_term_retention'] = long_term_retention
                
                # 留存衰减率
                if first_period_retention > 0:
                    retention_decay = (first_period_retention - long_term_retention) / first_period_retention
                    insights['key_metrics']['retention_decay'] = retention_decay
                    
            # 趋势分析
            insights['trends'] = self._analyze_retention_trends(retention_result)
            
            # 生成建议
            insights['recommendations'] = self._generate_retention_recommendations(retention_result)
            
            # 识别风险因素
            insights['risk_factors'] = self._identify_retention_risk_factors(retention_result)
            
            return insights
            
        except Exception as e:
            logger.error(f"获取留存分析洞察失败: {e}")
            return {}
            
    def _analyze_retention_trends(self, retention_result: RetentionAnalysisResult) -> Dict[str, Any]:
        """
        分析留存趋势
        
        Args:
            retention_result: 留存分析结果
            
        Returns:
            趋势分析结果
        """
        try:
            trends = {}
            
            # 分析队列间的留存率变化
            if len(retention_result.cohorts) > 1:
                # 比较最新队列和最旧队列的留存率
                cohorts_sorted = sorted(retention_result.cohorts, 
                                      key=lambda x: x.first_activity_date)
                
                oldest_cohort = cohorts_sorted[0]
                newest_cohort = cohorts_sorted[-1]
                
                # 比较第1期留存率
                if len(oldest_cohort.retention_rates) > 1 and len(newest_cohort.retention_rates) > 1:
                    old_retention = oldest_cohort.retention_rates[1]
                    new_retention = newest_cohort.retention_rates[1]
                    
                    if new_retention > old_retention * 1.1:
                        trends['cohort_trend'] = 'improving'
                    elif new_retention < old_retention * 0.9:
                        trends['cohort_trend'] = 'declining'
                    else:
                        trends['cohort_trend'] = 'stable'
                        
                    trends['retention_change'] = (new_retention - old_retention) / old_retention if old_retention > 0 else 0
                    
            # 分析留存曲线形状
            overall_rates = retention_result.overall_retention_rates
            if len(overall_rates) > 2:
                rates_list = [overall_rates[i] for i in sorted(overall_rates.keys())]
                
                # 计算留存曲线的陡峭程度
                initial_drop = rates_list[0] - rates_list[1] if len(rates_list) > 1 else 0
                if initial_drop > 0.5:
                    trends['curve_shape'] = 'steep_drop'
                elif initial_drop > 0.3:
                    trends['curve_shape'] = 'moderate_drop'
                else:
                    trends['curve_shape'] = 'gradual_drop'
                    
            return trends
            
        except Exception as e:
            logger.warning(f"分析留存趋势失败: {e}")
            return {}
            
    def _generate_retention_recommendations(self, retention_result: RetentionAnalysisResult) -> List[str]:
        """
        生成留存改进建议
        
        Args:
            retention_result: 留存分析结果
            
        Returns:
            建议列表
        """
        try:
            recommendations = []
            
            overall_rates = retention_result.overall_retention_rates
            summary_stats = retention_result.summary_stats
            
            # 基于第1期留存率的建议
            if overall_rates and 1 in overall_rates:
                first_period_retention = overall_rates[1]
                
                if first_period_retention < 0.2:
                    recommendations.append("第1期留存率过低，建议优化新用户引导流程和首次体验")
                elif first_period_retention < 0.4:
                    recommendations.append("第1期留存率有待提升，建议加强用户激活策略")
                    
            # 基于长期留存的建议
            if overall_rates:
                last_period = max(overall_rates.keys())
                if last_period > 3:
                    long_term_retention = overall_rates[last_period]
                    if long_term_retention < 0.05:
                        recommendations.append("长期留存率较低，建议建立用户忠诚度计划")
                        
            # 基于队列大小的建议
            avg_cohort_size = summary_stats.get('avg_cohort_size', 0)
            if avg_cohort_size < 50:
                recommendations.append("队列规模较小，建议加大用户获取力度")
                
            # 基于留存率变异的建议
            if summary_stats.get('max_retention_rate', 0) - summary_stats.get('min_retention_rate', 0) > 0.3:
                recommendations.append("不同队列间留存率差异较大，建议分析高留存队列的特征")
                
            if not recommendations:
                recommendations.append("留存表现良好，建议继续保持当前策略")
                
            return recommendations
            
        except Exception as e:
            logger.warning(f"生成留存建议失败: {e}")
            return ["建议进行更详细的留存分析"]
            
    def _identify_retention_risk_factors(self, retention_result: RetentionAnalysisResult) -> List[str]:
        """
        识别留存风险因素
        
        Args:
            retention_result: 留存分析结果
            
        Returns:
            风险因素列表
        """
        try:
            risk_factors = []
            
            overall_rates = retention_result.overall_retention_rates
            summary_stats = retention_result.summary_stats
            
            # 检查急剧下降的留存率
            if overall_rates and len(overall_rates) > 1:
                rates_list = [overall_rates[i] for i in sorted(overall_rates.keys())]
                
                for i in range(1, len(rates_list)):
                    if rates_list[i-1] > 0 and (rates_list[i-1] - rates_list[i]) / rates_list[i-1] > 0.5:
                        risk_factors.append(f"第{i}期留存率急剧下降")
                        break
                        
            # 检查整体低留存率
            avg_retention = summary_stats.get('avg_retention_rate', 0)
            if avg_retention < 0.1:
                risk_factors.append("整体留存率过低")
                
            # 检查留存率下降趋势
            if len(retention_result.cohorts) > 2:
                recent_cohorts = sorted(retention_result.cohorts, 
                                      key=lambda x: x.first_activity_date)[-3:]
                
                if len(recent_cohorts) >= 2:
                    # 比较最近两个队列的留存率
                    if (len(recent_cohorts[-1].retention_rates) > 1 and 
                        len(recent_cohorts[-2].retention_rates) > 1):
                        
                        latest_retention = recent_cohorts[-1].retention_rates[1]
                        previous_retention = recent_cohorts[-2].retention_rates[1]
                        
                        if latest_retention < previous_retention * 0.8:
                            risk_factors.append("最近队列留存率呈下降趋势")
                            
            if not risk_factors:
                risk_factors.append("未发现明显的留存风险因素")
                
            return risk_factors
            
        except Exception as e:
            logger.warning(f"识别留存风险因素失败: {e}")
            return ["风险因素分析失败"]
            
    def analyze_retention(self, events: pd.DataFrame) -> Dict[str, Any]:
        """
        执行留存分析（集成管理器接口）
        
        Args:
            events: 事件数据DataFrame
            
        Returns:
            留存分析结果字典
        """
        try:
            if events.empty:
                return {
                    'status': 'error',
                    'message': '事件数据为空',
                    'insights': [],
                    'recommendations': []
                }
            
            # 执行月度留存分析（默认）
            retention_result = self.analyze_monthly_retention(events)
            
            # 生成洞察和建议
            insights = []
            recommendations = []
            
            if retention_result and retention_result.overall_retention_rates:
                # 分析整体留存率
                retention_rates = retention_result.overall_retention_rates
                
                # 第1个月留存率
                if 1 in retention_rates:
                    month1_retention = retention_rates[1] * 100
                    insights.append(f"第1个月留存率: {month1_retention:.1f}%")
                    
                    if month1_retention < 20:
                        recommendations.append("第1个月留存率较低，需要改善新用户引导体验")
                    elif month1_retention > 40:
                        recommendations.append("第1个月留存率表现良好，可以作为基准优化其他时期")
                
                # 第3个月留存率
                if 3 in retention_rates:
                    month3_retention = retention_rates[3] * 100
                    insights.append(f"第3个月留存率: {month3_retention:.1f}%")
                    
                    if month3_retention < 10:
                        recommendations.append("长期留存率需要提升，考虑增加用户粘性功能")
                
                # 留存趋势分析
                if len(retention_rates) >= 3:
                    rates_list = [retention_rates[i] for i in sorted(retention_rates.keys())[:3]]
                    if rates_list[1] > rates_list[0] * 0.5:
                        insights.append("留存率下降趋势相对平缓")
                        recommendations.append("保持当前用户体验策略，继续监控留存表现")
                    else:
                        insights.append("留存率下降较快")
                        recommendations.append("需要紧急优化用户留存策略")
            
            # 队列分析洞察
            if retention_result and retention_result.cohorts:
                cohort_count = len(retention_result.cohorts)
                insights.append(f"分析了 {cohort_count} 个用户队列")
                
                if cohort_count >= 3:
                    recommendations.append("有足够的队列数据进行趋势分析，建议定期监控队列表现")
                else:
                    recommendations.append("队列数据较少，建议积累更多数据以获得更准确的留存洞察")
            
            return {
                'status': 'success',
                'analysis_type': 'retention_analysis',
                'data_size': len(events),
                'unique_users': events['user_pseudo_id'].nunique() if 'user_pseudo_id' in events.columns else 0,
                'insights': insights,
                'recommendations': recommendations,
                'detailed_results': {
                    'retention_result': retention_result,
                    'cohort_count': len(retention_result.cohorts) if retention_result else 0
                },
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"留存分析执行失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'insights': [],
                'recommendations': []
            }
            
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        获取分析摘要
        
        Returns:
            分析摘要字典
        """
        try:
            if self.storage_manager is None:
                return {"error": "存储管理器未初始化"}
                
            events = self.storage_manager.get_data('events')
            
            if events.empty:
                return {"error": "无事件数据"}
                
            # 基础统计
            total_events = len(events)
            unique_users = events['user_pseudo_id'].nunique()
            
            # 时间范围
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                    
            if 'event_datetime' in events.columns:
                date_range = {
                    'start': events['event_datetime'].min().strftime('%Y-%m-%d'),
                    'end': events['event_datetime'].max().strftime('%Y-%m-%d')
                }
                
                # 计算数据跨度
                data_span_days = (events['event_datetime'].max() - events['event_datetime'].min()).days
            else:
                date_range = {'start': 'N/A', 'end': 'N/A'}
                data_span_days = 0
                
            # 估算可分析的队列数
            if data_span_days > 0:
                estimated_daily_cohorts = min(data_span_days, 30)
                estimated_weekly_cohorts = min(data_span_days // 7, 12)
                estimated_monthly_cohorts = min(data_span_days // 30, 12)
            else:
                estimated_daily_cohorts = estimated_weekly_cohorts = estimated_monthly_cohorts = 0
                
            return {
                'total_events': total_events,
                'unique_users': unique_users,
                'date_range': date_range,
                'data_span_days': data_span_days,
                'estimated_cohorts': {
                    'daily': estimated_daily_cohorts,
                    'weekly': estimated_weekly_cohorts,
                    'monthly': estimated_monthly_cohorts
                },
                'analysis_capabilities': [
                    'daily_retention_analysis',
                    'weekly_retention_analysis',
                    'monthly_retention_analysis',
                    'user_cohort_building',
                    'retention_profile_creation'
                ]
            }
            
        except Exception as e:
            logger.error(f"获取分析摘要失败: {e}")
            return {"error": str(e)}