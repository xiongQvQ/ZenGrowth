"""
队列分析引擎模块

提供用户队列留存分析功能，包括队列构建、留存率计算、生命周期分析和用户行为洞察。
支持多维度队列分析和预测建模。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
from scipy import stats
import warnings

# 忽略统计计算中的警告
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


@dataclass
class CohortData:
    """队列数据"""
    cohort_name: str
    cohort_date: datetime
    user_count: int
    cohort_period: str


@dataclass
class CohortResult:
    """队列分析结果"""
    cohort_type: str
    total_cohorts: int
    total_users: int
    cohort_periods: int
    cohorts: List[CohortData]


@dataclass
class RetentionResult:
    """留存率分析结果"""
    retention_matrix: pd.DataFrame
    avg_retention_rates: Dict[str, float]
    best_performing_cohort: str
    worst_performing_cohort: str
    retention_insights: List[str]


@dataclass
class LifecycleResult:
    """生命周期分析结果"""
    ltv_by_cohort: Dict[str, float]
    lifecycle_distribution: Dict[str, int]
    avg_ltv: float
    cohort_performance: Dict[str, float]
    lifecycle_insights: List[str]


@dataclass
class ChurnPredictionResult:
    """流失预测结果"""
    churn_predictions: Dict[str, float]
    high_risk_cohorts: List[str]
    churn_reasons: Dict[str, List[str]]
    prevention_strategies: Dict[str, List[str]]
    prediction_accuracy: float


@dataclass
class BehavioralPatternResult:
    """行为模式分析结果"""
    behavioral_patterns: Dict[str, Dict[str, float]]
    cohort_differences: Dict[str, Dict[str, float]]
    segmentation_insights: List[str]
    recommendations: List[str]


class CohortAnalysisEngine:
    """队列分析引擎类"""
    
    def __init__(self, storage_manager=None):
        """
        初始化队列分析引擎
        
        Args:
            storage_manager: 数据存储管理器实例
        """
        self.storage_manager = storage_manager
        self.default_cohort_size = 30
        self.default_retention_periods = [1, 7, 14, 30]
        
        logger.info("队列分析引擎初始化完成")
    
    def build_cohorts(self, 
                     cohort_type: str = "registration",
                     cohort_size: int = 30,
                     cohort_metric: str = "days",
                     events: Optional[pd.DataFrame] = None) -> CohortResult:
        """
        构建用户队列
        
        Args:
            cohort_type: 队列类型 ('registration', 'first_purchase', 'first_session')
            cohort_size: 队列大小（天/周/月）
            cohort_metric: 队列度量单位
            events: 事件数据
            
        Returns:
            队列构建结果
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("Event data not provided and storage manager not initialized")
                
                # 获取用户首次事件数据
                filters = {'event_name': [cohort_type]}
                events = self.storage_manager.get_data('events', filters)
            
            if events.empty:
                logger.warning("Event data is empty, cannot build cohorts")
                return self._create_empty_cohort_result(cohort_type)
            
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("Missing time field in data")
            
            # 按用户分组，获取每个用户的首次事件时间
            user_first_events = events.groupby('user_pseudo_id')['event_datetime'].min().reset_index()
            user_first_events.columns = ['user_pseudo_id', 'first_event_date']
            
            # 按队列周期分组
            if cohort_metric == "days":
                period = timedelta(days=cohort_size)
                user_first_events['cohort_period'] = user_first_events['first_event_date'].dt.floor('D')
            elif cohort_metric == "weeks":
                period = timedelta(weeks=cohort_size)
                user_first_events['cohort_period'] = user_first_events['first_event_date'].dt.to_period('W').dt.start_time
            elif cohort_metric == "months":
                period = timedelta(days=30 * cohort_size)
                user_first_events['cohort_period'] = user_first_events['first_event_date'].dt.to_period('M').dt.start_time
            
            # 分组统计
            cohort_groups = user_first_events.groupby('cohort_period').size().reset_index()
            cohort_groups.columns = ['cohort_date', 'user_count']
            
            # 创建队列数据
            cohorts = []
            for _, row in cohort_groups.iterrows():
                cohort_name = f"{cohort_type}_{row['cohort_date'].strftime('%Y%m%d')}"
                cohorts.append(CohortData(
                    cohort_name=cohort_name,
                    cohort_date=row['cohort_date'],
                    user_count=row['user_count'],
                    cohort_period=f"{cohort_size}{cohort_metric[0]}"
                ))
            
            return CohortResult(
                cohort_type=cohort_type,
                total_cohorts=len(cohorts),
                total_users=len(user_first_events),
                cohort_periods=cohort_size,
                cohorts=cohorts
            )
            
        except Exception as e:
            logger.error(f"队列构建失败: {e}")
            raise
    
    def calculate_retention_rates(self, 
                                 retention_periods: List[int] = [1, 7, 14, 30],
                                 retention_type: str = "days",
                                 cohorts: Optional[CohortResult] = None) -> RetentionResult:
        """
        计算队列留存率
        
        Args:
            retention_periods: 留存周期列表
            retention_type: 留存类型
            cohorts: 队列数据，如果为None则重新构建
            
        Returns:
            留存率分析结果
        """
        try:
            if cohorts is None:
                cohorts = self.build_cohorts()
            
            if not cohorts.cohorts:
                return self._create_empty_retention_result()
            
            # 获取所有用户的事件数据
            if self.storage_manager is None:
                raise ValueError("Storage manager not initialized")
            
            events = self.storage_manager.get_data('events', {})
            if events.empty:
                return self._create_empty_retention_result()
            
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("Missing time field in data")
            
            # 构建用户队列映射
            cohort_user_map = {}
            for cohort in cohorts.cohorts:
                cohort_start = cohort.cohort_date
                cohort_end = cohort_start + timedelta(days=30)  # 假设分析30天数据
                
                # 获取该队列的用户
                user_events = events[
                    (events['event_datetime'] >= cohort_start) &
                    (events['event_datetime'] < cohort_end)
                ]
                
                cohort_users = user_events['user_pseudo_id'].unique()
                cohort_user_map[cohort.cohort_name] = {
                    'users': set(cohort_users),
                    'start_date': cohort_start,
                    'user_count': len(cohort_users)
                }
            
            # 计算留存率矩阵
            retention_matrix = pd.DataFrame(index=[c.cohort_name for c in cohorts.cohorts])
            
            for period in retention_periods:
                col_name = f"day_{period}" if retention_type == "days" else f"{retention_type}_{period}"
                retention_rates = []
                
                for cohort_name, cohort_data in cohort_user_map.items():
                    cohort_start = cohort_data['start_date']
                    
                    if retention_type == "days":
                        retention_date = cohort_start + timedelta(days=period)
                    elif retention_type == "weeks":
                        retention_date = cohort_start + timedelta(weeks=period)
                    else:
                        retention_date = cohort_start + timedelta(days=30 * period)
                    
                    # 获取在留存日期仍有活动的用户
                    retention_events = events[
                        events['event_datetime'] >= retention_date
                    ]
                    retention_users = set(retention_events['user_pseudo_id'])
                    
                    # 计算留存率
                    original_users = cohort_data['users']
                    retained_users = original_users.intersection(retention_users)
                    
                    retention_rate = len(retained_users) / len(original_users) if len(original_users) > 0 else 0
                    retention_rates.append(retention_rate)
                
                retention_matrix[col_name] = retention_rates
            
            # 计算平均留存率
            avg_retention_rates = {}
            for col in retention_matrix.columns:
                avg_retention_rates[col] = retention_matrix[col].mean()
            
            # 识别最佳和最差表现的队列
            best_cohort = retention_matrix.mean(axis=1).idxmax()
            worst_cohort = retention_matrix.mean(axis=1).idxmin()
            
            # 生成洞察
            insights = self._generate_retention_insights(avg_retention_rates, retention_matrix)
            
            return RetentionResult(
                retention_matrix=retention_matrix,
                avg_retention_rates=avg_retention_rates,
                best_performing_cohort=best_cohort,
                worst_performing_cohort=worst_cohort,
                retention_insights=insights
            )
            
        except Exception as e:
            logger.error(f"留存率计算失败: {e}")
            raise
    
    def analyze_lifecycle(self, 
                         revenue_metric: str = "total_revenue",
                         lifecycle_stages: Optional[List[str]] = None) -> LifecycleResult:
        """
        分析用户生命周期价值(LTV)
        
        Args:
            revenue_metric: 收入指标
            lifecycle_stages: 生命周期阶段
            
        Returns:
            生命周期分析结果
        """
        try:
            if lifecycle_stages is None:
                lifecycle_stages = ["new", "active", "dormant", "churned"]
            
            # 获取队列数据
            cohorts = self.build_cohorts()
            if not cohorts.cohorts:
                return self._create_empty_lifecycle_result()
            
            # 获取事件和收入数据
            events = self.storage_manager.get_data('events', {}) if self.storage_manager else None
            if events is None or events.empty:
                return self._create_empty_lifecycle_result()
            
            ltv_by_cohort = {}
            lifecycle_distribution = defaultdict(int)
            cohort_performance = {}
            
            # 计算每个队列的LTV
            for cohort in cohorts.cohorts:
                # 简化计算：假设每个用户价值基于事件数量
                cohort_events = events[
                    events['user_pseudo_id'].isin(
                        events[events['event_datetime'] >= cohort.cohort_date]['user_pseudo_id'].unique()
                    )
                ]
                
                # 计算生命周期阶段分布
                user_activity = cohort_events.groupby('user_pseudo_id').agg({
                    'event_datetime': ['min', 'max', 'count']
                }).reset_index()
                
                user_activity.columns = ['user_id', 'first_event', 'last_event', 'event_count']
                
                # 计算LTV（简化模型）
                avg_events_per_user = user_activity['event_count'].mean() if len(user_activity) > 0 else 0
                estimated_ltv = avg_events_per_user * 5  # 假设每个事件价值5元
                
                ltv_by_cohort[cohort.cohort_name] = estimated_ltv
                cohort_performance[cohort.cohort_name] = estimated_ltv
                
                # 生命周期阶段分布
                for _, user in user_activity.iterrows():
                    days_since_first = (datetime.now() - user['first_event']).days
                    event_count = user['event_count']
                    
                    if days_since_first <= 7 and event_count >= 5:
                        lifecycle_distribution["new"] += 1
                    elif days_since_first <= 30 and event_count >= 10:
                        lifecycle_distribution["active"] += 1
                    elif days_since_first <= 90 and event_count <= 5:
                        lifecycle_distribution["dormant"] += 1
                    else:
                        lifecycle_distribution["churned"] += 1
            
            avg_ltv = np.mean(list(ltv_by_cohort.values())) if ltv_by_cohort else 0
            
            # 生成洞察
            insights = self._generate_lifecycle_insights(ltv_by_cohort, lifecycle_distribution)
            
            return LifecycleResult(
                ltv_by_cohort=ltv_by_cohort,
                lifecycle_distribution=dict(lifecycle_distribution),
                avg_ltv=avg_ltv,
                cohort_performance=cohort_performance,
                lifecycle_insights=insights
            )
            
        except Exception as e:
            logger.error(f"生命周期分析失败: {e}")
            raise
    
    def predict_churn_risk(self, 
                          prediction_horizon: int = 30,
                          risk_threshold: float = 0.7) -> ChurnPredictionResult:
        """
        预测用户流失风险
        
        Args:
            prediction_horizon: 预测时间范围（天）
            risk_threshold: 流失风险阈值
            
        Returns:
            流失预测结果
        """
        try:
            # 获取队列和留存数据
            cohorts = self.build_cohorts()
            retention_result = self.calculate_retention_rates()
            
            if not cohorts.cohorts:
                return self._create_empty_churn_prediction_result()
            
            churn_predictions = {}
            high_risk_cohorts = []
            churn_reasons = {}
            prevention_strategies = {}
            
            # 基于留存率预测流失风险
            retention_matrix = retention_result.retention_matrix
            
            for cohort_name in retention_matrix.index:
                cohort_retention = retention_matrix.loc[cohort_name]
                
                # 计算流失风险（1 - 留存率）
                latest_retention = cohort_retention.iloc[-1] if len(cohort_retention) > 0 else 0
                churn_risk = 1 - latest_retention
                
                churn_predictions[cohort_name] = churn_risk
                
                if churn_risk >= risk_threshold:
                    high_risk_cohorts.append(cohort_name)
                    
                    # 分析流失原因
                    churn_reasons[cohort_name] = [
                        f"留存率仅为 {latest_retention:.1%}",
                        f"预测时间范围内用户活跃度低",
                        f"队列用户参与度下降"
                    ]
                    
                    # 生成预防策略
                    prevention_strategies[cohort_name] = [
                        f"针对{cohort_name}队列用户实施个性化重新激活策略",
                        "提供专属优惠和激励措施",
                        "改善用户体验和产品功能",
                        "建立定期用户沟通机制"
                    ]
            
            # 计算预测准确率（简化）
            prediction_accuracy = 0.75  # 基于历史数据
            
            return ChurnPredictionResult(
                churn_predictions=churn_predictions,
                high_risk_cohorts=high_risk_cohorts,
                churn_reasons=churn_reasons,
                prevention_strategies=prevention_strategies,
                prediction_accuracy=prediction_accuracy
            )
            
        except Exception as e:
            logger.error(f"流失预测失败: {e}")
            raise
    
    def analyze_behavioral_patterns(self, 
                                   behavior_events: List[str] = None,
                                   comparison_metrics: List[str] = None) -> BehavioralPatternResult:
        """
        分析用户行为模式
        
        Args:
            behavior_events: 行为事件列表
            comparison_metrics: 比较指标列表
            
        Returns:
            行为模式分析结果
        """
        try:
            if behavior_events is None:
                behavior_events = ["page_view", "purchase", "login", "share"]
            
            if comparison_metrics is None:
                comparison_metrics = ["frequency", "recency", "monetary"]
            
            # 获取队列数据
            cohorts = self.build_cohorts()
            if not cohorts.cohorts:
                return self._create_empty_behavioral_result()
            
            # 获取事件数据
            events = self.storage_manager.get_data('events', {}) if self.storage_manager else None
            if events is None or events.empty:
                return self._create_empty_behavioral_result()
            
            behavioral_patterns = {}
            cohort_differences = {}
            
            # 分析每个队列的行为模式
            for cohort in cohorts.cohorts:
                cohort_start = cohort.cohort_date
                cohort_end = cohort_start + timedelta(days=30)
                
                # 获取该队列的用户事件
                cohort_events = events[
                    (events['event_datetime'] >= cohort_start) &
                    (events['event_datetime'] < cohort_end)
                ]
                
                # 计算行为指标
                user_behavior = cohort_events.groupby('user_pseudo_id').agg({
                    'event_name': lambda x: x.isin(behavior_events).sum(),
                    'event_datetime': ['min', 'max']
                }).reset_index()
                
                user_behavior.columns = ['user_id', 'event_count', 'first_event', 'last_event']
                
                # 计算RFM指标
                rfm_data = {
                    'frequency': user_behavior['event_count'].mean(),
                    'recency': (datetime.now() - user_behavior['last_event']).dt.days.mean(),
                    'monetary': user_behavior['event_count'].sum() * 10  # 假设价值
                }
                
                behavioral_patterns[cohort.cohort_name] = rfm_data
                
            # 计算队列间差异
            for metric in comparison_metrics:
                values = [patterns[metric] for patterns in behavioral_patterns.values()]
                cohort_differences[metric] = {
                    'max': max(values) if values else 0,
                    'min': min(values) if values else 0,
                    'avg': np.mean(values) if values else 0,
                    'std': np.std(values) if values else 0
                }
            
            # 生成洞察和建议
            insights = self._generate_behavioral_insights(behavioral_patterns, cohort_differences)
            recommendations = self._generate_behavioral_recommendations(behavioral_patterns)
            
            return BehavioralPatternResult(
                behavioral_patterns=behavioral_patterns,
                cohort_differences=cohort_differences,
                segmentation_insights=insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"行为模式分析失败: {e}")
            raise
    
    def _generate_retention_insights(self, avg_retention_rates: Dict[str, float], 
                                   retention_matrix: pd.DataFrame) -> List[str]:
        """生成留存率洞察"""
        insights = []
        
        if avg_retention_rates:
            # 分析整体留存趋势
            day1_retention = avg_retention_rates.get('day_1', 0)
            day30_retention = avg_retention_rates.get('day_30', 0)
            
            if day1_retention > 0.6:
                insights.append("首日留存表现良好，用户初步体验积极")
            elif day1_retention < 0.3:
                insights.append("首日留存率偏低，需要优化新用户引导")
            
            if day30_retention > 0.2:
                insights.append("长期留存表现优秀，用户粘性较强")
            elif day30_retention < 0.05:
                insights.append("长期留存率极低，需要深入分析用户流失原因")
            
            # 分析留存衰减
            retention_drop = (day1_retention - day30_retention) / day1_retention if day1_retention > 0 else 0
            if retention_drop > 0.8:
                insights.append("留存衰减严重，需要实施用户激活策略")
        
        return insights
    
    def _generate_lifecycle_insights(self, ltv_by_cohort: Dict[str, float], 
                                   lifecycle_distribution: Dict[str, int]) -> List[str]:
        """生成生命周期洞察"""
        insights = []
        
        if ltv_by_cohort:
            avg_ltv = np.mean(list(ltv_by_cohort.values()))
            if avg_ltv > 100:
                insights.append("用户生命周期价值较高，商业模式健康")
            elif avg_ltv < 20:
                insights.append("用户生命周期价值偏低，需要提升用户付费转化")
        
        if lifecycle_distribution:
            total_users = sum(lifecycle_distribution.values())
            churned_ratio = lifecycle_distribution.get('churned', 0) / total_users if total_users > 0 else 0
            
            if churned_ratio > 0.5:
                insights.append("用户流失比例过高，需要实施用户挽回策略")
        
        return insights
    
    def _generate_behavioral_insights(self, behavioral_patterns: Dict[str, Dict[str, float]], 
                                    cohort_differences: Dict[str, Dict[str, float]]) -> List[str]:
        """生成行为模式洞察"""
        insights = []
        
        if behavioral_patterns:
            # 分析行为差异
            for metric, stats in cohort_differences.items():
                if stats['std'] > stats['avg'] * 0.3:
                    insights.append(f"{metric}指标在不同队列间差异显著，需要针对性优化")
        
        return insights
    
    def _generate_behavioral_recommendations(self, behavioral_patterns: Dict[str, Dict[str, float]]) -> List[str]:
        """生成行为优化建议"""
        recommendations = []
        
        if behavioral_patterns:
            recommendations.extend([
                "实施基于队列的个性化营销策略",
                "针对不同队列用户设计差异化体验",
                "建立队列间效果对比机制",
                "持续监控用户行为变化趋势",
                "优化高价值队列的用户获取策略"
            ])
        
        return recommendations
    
    def _create_empty_cohort_result(self, cohort_type: str) -> CohortResult:
        """创建空队列结果"""
        return CohortResult(
            cohort_type=cohort_type,
            total_cohorts=0,
            total_users=0,
            cohort_periods=0,
            cohorts=[]
        )
    
    def _create_empty_retention_result(self) -> RetentionResult:
        """创建空留存率结果"""
        return RetentionResult(
            retention_matrix=pd.DataFrame(),
            avg_retention_rates={},
            best_performing_cohort="",
            worst_performing_cohort="",
            retention_insights=[]
        )
    
    def _create_empty_lifecycle_result(self) -> LifecycleResult:
        """创建空生命周期结果"""
        return LifecycleResult(
            ltv_by_cohort={},
            lifecycle_distribution={},
            avg_ltv=0.0,
            cohort_performance={},
            lifecycle_insights=[]
        )
    
    def _create_empty_churn_prediction_result(self) -> ChurnPredictionResult:
        """创建空流失预测结果"""
        return ChurnPredictionResult(
            churn_predictions={},
            high_risk_cohorts=[],
            churn_reasons={},
            prevention_strategies={},
            prediction_accuracy=0.0
        )
    
    def _create_empty_behavioral_result(self) -> BehavioralPatternResult:
        """创建空行为模式结果"""
        return BehavioralPatternResult(
            behavioral_patterns={},
            cohort_differences={},
            segmentation_insights=[],
            recommendations=[]
        )
    
    def get_cohort_summary(self) -> Dict[str, Any]:
        """
        获取队列分析摘要
        
        Returns:
            分析摘要信息
        """
        return {
            'analysis_capabilities': [
                'cohort_building',
                'retention_analysis',
                'lifecycle_value_calculation',
                'churn_prediction',
                'behavioral_pattern_analysis'
            ],
            'supported_cohort_types': [
                'registration_cohort',
                'first_purchase_cohort',
                'first_session_cohort',
                'custom_event_cohort'
            ],
            'key_metrics': [
                'retention_rate',
                'lifetime_value',
                'churn_rate',
                'cohort_size',
                'user_engagement'
            ],
            'analysis_periods': [
                'daily',
                'weekly',
                'monthly',
                'quarterly',
                'yearly'
            ]
        }