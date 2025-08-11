"""
留存分析引擎测试模块

测试用户队列构建和留存率计算功能。
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.retention_analysis_engine import (
    RetentionAnalysisEngine,
    CohortData,
    RetentionAnalysisResult,
    UserRetentionProfile
)
from tools.data_storage_manager import DataStorageManager


class TestRetentionAnalysisEngine:
    """留存分析引擎测试类"""
    
    @pytest.fixture
    def sample_events_data(self):
        """创建示例事件数据"""
        np.random.seed(42)
        
        events = []
        users = [f'user_{i}' for i in range(50)]
        
        # 创建60天的数据，模拟真实的用户留存模式
        start_date = datetime.now() - timedelta(days=60)
        
        for user_id in users:
            # 每个用户的首次活动时间
            first_activity = start_date + timedelta(days=np.random.randint(0, 30))
            
            # 模拟用户留存模式：有些用户很活跃，有些逐渐流失
            user_retention_prob = np.random.beta(2, 5)  # 大多数用户留存率较低
            
            current_date = first_activity
            day_offset = 0
            
            while current_date <= datetime.now() and day_offset < 45:
                # 决定用户是否在这一天活跃
                if np.random.random() < user_retention_prob:
                    # 用户活跃，生成1-5个事件
                    daily_events = np.random.randint(1, 6)
                    
                    for _ in range(daily_events):
                        event_time = current_date + timedelta(
                            hours=np.random.randint(0, 24),
                            minutes=np.random.randint(0, 60)
                        )
                        
                        event = {
                            'user_pseudo_id': user_id,
                            'event_name': np.random.choice(['page_view', 'login', 'purchase']),
                            'event_timestamp': int(event_time.timestamp() * 1000000),
                            'event_datetime': event_time,
                            'event_date': current_date.strftime('%Y%m%d'),
                            'platform': 'web'
                        }
                        events.append(event)
                
                # 用户留存概率随时间递减
                user_retention_prob *= 0.95
                current_date += timedelta(days=1)
                day_offset += 1
                
        return pd.DataFrame(events)
        
    @pytest.fixture
    def sample_users_data(self):
        """创建示例用户数据"""
        users = []
        for i in range(50):
            user = {
                'user_pseudo_id': f'user_{i}',
                'platform': 'web',
                'device_category': 'desktop',
                'geo_country': 'US',
                'first_seen': datetime.now() - timedelta(days=np.random.randint(1, 60)),
                'last_seen': datetime.now() - timedelta(days=np.random.randint(0, 10)),
                'total_events': np.random.randint(1, 100)
            }
            users.append(user)
            
        return pd.DataFrame(users)
        
    @pytest.fixture
    def storage_manager(self, sample_events_data, sample_users_data):
        """创建配置好的存储管理器"""
        manager = DataStorageManager()
        manager.store_events(sample_events_data)
        manager.store_users(sample_users_data)
        return manager
        
    @pytest.fixture
    def engine(self, storage_manager):
        """创建留存分析引擎实例"""
        return RetentionAnalysisEngine(storage_manager)
        
    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = RetentionAnalysisEngine()
        assert engine.storage_manager is None
        
    def test_engine_initialization_with_storage(self, storage_manager):
        """测试带存储管理器的引擎初始化"""
        engine = RetentionAnalysisEngine(storage_manager)
        assert engine.storage_manager is not None
        
    def test_build_user_cohorts_monthly(self, engine, sample_events_data):
        """测试构建月度用户队列"""
        cohorts = engine.build_user_cohorts(
            sample_events_data, 
            cohort_period='monthly',
            min_cohort_size=5
        )
        
        assert isinstance(cohorts, dict)
        assert len(cohorts) > 0
        
        # 检查队列格式
        for cohort_period, user_ids in cohorts.items():
            assert isinstance(cohort_period, str)
            assert isinstance(user_ids, list)
            assert len(user_ids) >= 5  # 满足最小队列大小
            
    def test_build_user_cohorts_weekly(self, engine, sample_events_data):
        """测试构建周度用户队列"""
        cohorts = engine.build_user_cohorts(
            sample_events_data,
            cohort_period='weekly',
            min_cohort_size=3
        )
        
        assert isinstance(cohorts, dict)
        assert len(cohorts) > 0
        
    def test_build_user_cohorts_daily(self, engine, sample_events_data):
        """测试构建日度用户队列"""
        cohorts = engine.build_user_cohorts(
            sample_events_data,
            cohort_period='daily',
            min_cohort_size=1
        )
        
        assert isinstance(cohorts, dict)
        assert len(cohorts) > 0
        
    def test_get_cohort_key(self, engine):
        """测试队列键值生成"""
        test_date = datetime(2024, 3, 15)  # 2024年3月15日，周五
        
        # 测试日度键值
        daily_key = engine._get_cohort_key(test_date, 'daily')
        assert daily_key == '2024-03-15'
        
        # 测试周度键值
        weekly_key = engine._get_cohort_key(test_date, 'weekly')
        assert weekly_key.startswith('2024-W')
        
        # 测试月度键值
        monthly_key = engine._get_cohort_key(test_date, 'monthly')
        assert monthly_key == '2024-03'
        
    def test_get_cohort_key_invalid_period(self, engine):
        """测试无效队列周期"""
        test_date = datetime(2024, 3, 15)
        
        with pytest.raises(ValueError):
            engine._get_cohort_key(test_date, 'invalid_period')
            
    def test_calculate_retention_rates_monthly(self, engine, sample_events_data):
        """测试计算月度留存率"""
        result = engine.calculate_retention_rates(
            sample_events_data,
            analysis_type='monthly',
            max_periods=6
        )
        
        assert isinstance(result, RetentionAnalysisResult)
        assert result.analysis_type == 'monthly'
        assert isinstance(result.cohorts, list)
        assert isinstance(result.overall_retention_rates, dict)
        assert isinstance(result.retention_matrix, pd.DataFrame)
        assert isinstance(result.summary_stats, dict)
        
        # 检查队列数据
        for cohort in result.cohorts:
            assert isinstance(cohort, CohortData)
            assert cohort.cohort_size > 0
            assert len(cohort.retention_rates) <= 6
            assert len(cohort.retention_counts) <= 6
            assert cohort.retention_rates[0] == 1.0  # 第0期应该是100%
            
    def test_calculate_retention_rates_weekly(self, engine, sample_events_data):
        """测试计算周度留存率"""
        result = engine.calculate_retention_rates(
            sample_events_data,
            analysis_type='weekly',
            max_periods=8
        )
        
        assert isinstance(result, RetentionAnalysisResult)
        assert result.analysis_type == 'weekly'
        
    def test_calculate_retention_rates_daily(self, engine, sample_events_data):
        """测试计算日度留存率"""
        result = engine.calculate_retention_rates(
            sample_events_data,
            analysis_type='daily',
            max_periods=14
        )
        
        assert isinstance(result, RetentionAnalysisResult)
        assert result.analysis_type == 'daily'
        
    def test_calculate_retention_rates_empty_data(self, engine):
        """测试空数据的留存率计算"""
        empty_df = pd.DataFrame()
        result = engine.calculate_retention_rates(empty_df)
        
        assert isinstance(result, RetentionAnalysisResult)
        assert len(result.cohorts) == 0
        assert len(result.overall_retention_rates) == 0
        
    def test_analyze_daily_retention(self, engine, sample_events_data):
        """测试日留存分析"""
        result = engine.analyze_daily_retention(sample_events_data, max_days=14)
        
        assert isinstance(result, RetentionAnalysisResult)
        assert result.analysis_type == 'daily'
        
    def test_analyze_weekly_retention(self, engine, sample_events_data):
        """测试周留存分析"""
        result = engine.analyze_weekly_retention(sample_events_data, max_weeks=8)
        
        assert isinstance(result, RetentionAnalysisResult)
        assert result.analysis_type == 'weekly'
        
    def test_analyze_monthly_retention(self, engine, sample_events_data):
        """测试月留存分析"""
        result = engine.analyze_monthly_retention(sample_events_data, max_months=6)
        
        assert isinstance(result, RetentionAnalysisResult)
        assert result.analysis_type == 'monthly'
        
    def test_create_user_retention_profiles(self, engine, sample_events_data, sample_users_data):
        """测试创建用户留存档案"""
        profiles = engine.create_user_retention_profiles(sample_events_data, sample_users_data)
        
        assert isinstance(profiles, list)
        assert len(profiles) > 0
        
        # 检查档案结构
        for profile in profiles:
            assert isinstance(profile, UserRetentionProfile)
            assert isinstance(profile.user_id, str)
            assert isinstance(profile.first_activity_date, datetime)
            assert isinstance(profile.last_activity_date, datetime)
            assert isinstance(profile.total_active_days, int)
            assert isinstance(profile.retention_periods, list)
            assert isinstance(profile.activity_pattern, dict)
            assert isinstance(profile.churn_risk_score, float)
            assert 0 <= profile.churn_risk_score <= 100
            
    def test_calculate_user_active_days(self, engine):
        """测试计算用户活跃天数"""
        # 创建测试数据：用户在3天内有活动
        user_events = pd.DataFrame([
            {'event_datetime': datetime(2024, 1, 1, 10, 0)},
            {'event_datetime': datetime(2024, 1, 1, 15, 0)},  # 同一天
            {'event_datetime': datetime(2024, 1, 2, 12, 0)},  # 第二天
            {'event_datetime': datetime(2024, 1, 4, 9, 0)},   # 第四天
        ])
        
        active_days = engine._calculate_user_active_days(user_events)
        assert active_days == 3  # 1月1日、1月2日、1月4日
        
    def test_calculate_user_retention_periods(self, engine):
        """测试计算用户留存周期"""
        first_activity = datetime(2024, 1, 1)
        user_events = pd.DataFrame([
            {'event_datetime': datetime(2024, 1, 1)},   # 第0周
            {'event_datetime': datetime(2024, 1, 8)},   # 第1周
            {'event_datetime': datetime(2024, 1, 15)},  # 第2周
            {'event_datetime': datetime(2024, 1, 30)},  # 第4周
        ])
        
        periods = engine._calculate_user_retention_periods(user_events, first_activity)
        assert isinstance(periods, list)
        assert 0 in periods  # 第0周
        assert 1 in periods  # 第1周
        assert 2 in periods  # 第2周
        assert 4 in periods  # 第4周
        
    def test_analyze_user_activity_pattern(self, engine):
        """测试分析用户活动模式"""
        # 创建7天的用户活动数据
        user_events = pd.DataFrame([
            {
                'event_datetime': datetime(2024, 1, 1) + timedelta(days=i, hours=np.random.randint(0, 24)),
                'event_name': 'page_view'
            }
            for i in range(7)
        ])
        
        pattern = engine._analyze_user_activity_pattern(user_events)
        
        assert isinstance(pattern, dict)
        assert 'activity_frequency' in pattern
        assert 'events_per_day' in pattern
        assert 'activity_regularity' in pattern
        assert 'recent_activity_trend' in pattern
        assert 'event_diversity' in pattern
        assert 'total_events' in pattern
        assert 'unique_event_types' in pattern
        
        assert 0 <= pattern['activity_frequency'] <= 1
        assert pattern['events_per_day'] >= 0
        assert pattern['total_events'] == 7
        
    def test_calculate_recent_activity_trend(self, engine):
        """测试计算最近活动趋势"""
        # 测试上升趋势
        increasing_events = pd.DataFrame([
            {'event_datetime': datetime.now() - timedelta(days=6-i)}
            for i in range(7)
            for _ in range(i+1)  # 每天事件数递增
        ])
        trend = engine._calculate_recent_activity_trend(increasing_events)
        assert trend in ['increasing', 'decreasing', 'stable']
        
        # 测试稳定趋势
        stable_events = pd.DataFrame([
            {'event_datetime': datetime.now() - timedelta(days=6-i)}
            for i in range(7)
            for _ in range(3)  # 每天3个事件
        ])
        trend = engine._calculate_recent_activity_trend(stable_events)
        assert trend in ['increasing', 'decreasing', 'stable']
        
    def test_calculate_churn_risk_score(self, engine):
        """测试计算流失风险得分"""
        # 创建高风险用户：很久没活动
        high_risk_events = pd.DataFrame([
            {'event_datetime': datetime.now() - timedelta(days=45)}
        ])
        last_activity = datetime.now() - timedelta(days=45)
        activity_pattern = {
            'activity_frequency': 0.05,
            'events_per_day': 0.5,
            'recent_activity_trend': 'decreasing'
        }
        
        risk_score = engine._calculate_churn_risk_score(
            high_risk_events, last_activity, activity_pattern
        )
        
        assert isinstance(risk_score, float)
        assert 0 <= risk_score <= 100
        assert risk_score > 50  # 应该是高风险
        
        # 创建低风险用户：最近很活跃
        low_risk_events = pd.DataFrame([
            {'event_datetime': datetime.now() - timedelta(hours=1)}
        ])
        last_activity = datetime.now() - timedelta(hours=1)
        activity_pattern = {
            'activity_frequency': 0.8,
            'events_per_day': 10,
            'recent_activity_trend': 'increasing'
        }
        
        risk_score = engine._calculate_churn_risk_score(
            low_risk_events, last_activity, activity_pattern
        )
        
        assert risk_score < 30  # 应该是低风险
        
    def test_get_retention_insights(self, engine, sample_events_data):
        """测试获取留存分析洞察"""
        retention_result = engine.calculate_retention_rates(sample_events_data)
        insights = engine.get_retention_insights(retention_result)
        
        assert isinstance(insights, dict)
        assert 'key_metrics' in insights
        assert 'trends' in insights
        assert 'recommendations' in insights
        assert 'risk_factors' in insights
        
        # 检查关键指标
        key_metrics = insights['key_metrics']
        if key_metrics:
            for metric_name, metric_value in key_metrics.items():
                assert isinstance(metric_value, (int, float))
                
        # 检查建议和风险因素
        assert isinstance(insights['recommendations'], list)
        assert isinstance(insights['risk_factors'], list)
        
    def test_analyze_retention_trends(self, engine):
        """测试分析留存趋势"""
        # 创建模拟的留存分析结果
        cohort1 = CohortData(
            cohort_period='2024-01',
            cohort_size=100,
            first_activity_date=datetime(2024, 1, 1),
            retention_periods=[0, 1, 2, 3],
            retention_rates=[1.0, 0.5, 0.3, 0.2],
            retention_counts=[100, 50, 30, 20]
        )
        
        cohort2 = CohortData(
            cohort_period='2024-02',
            cohort_size=120,
            first_activity_date=datetime(2024, 2, 1),
            retention_periods=[0, 1, 2, 3],
            retention_rates=[1.0, 0.6, 0.4, 0.3],
            retention_counts=[120, 72, 48, 36]
        )
        
        retention_result = RetentionAnalysisResult(
            analysis_type='monthly',
            cohorts=[cohort1, cohort2],
            overall_retention_rates={0: 1.0, 1: 0.55, 2: 0.35, 3: 0.25},
            retention_matrix=pd.DataFrame(),
            summary_stats={}
        )
        
        trends = engine._analyze_retention_trends(retention_result)
        
        assert isinstance(trends, dict)
        if 'cohort_trend' in trends:
            assert trends['cohort_trend'] in ['improving', 'declining', 'stable']
        if 'curve_shape' in trends:
            assert trends['curve_shape'] in ['steep_drop', 'moderate_drop', 'gradual_drop']
            
    def test_generate_retention_recommendations(self, engine):
        """测试生成留存改进建议"""
        # 创建低留存率的模拟结果
        retention_result = RetentionAnalysisResult(
            analysis_type='monthly',
            cohorts=[],
            overall_retention_rates={0: 1.0, 1: 0.1, 2: 0.05, 3: 0.02},
            retention_matrix=pd.DataFrame(),
            summary_stats={'avg_cohort_size': 30}
        )
        
        recommendations = engine._generate_retention_recommendations(retention_result)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
        
    def test_identify_retention_risk_factors(self, engine):
        """测试识别留存风险因素"""
        # 创建有风险的模拟结果
        retention_result = RetentionAnalysisResult(
            analysis_type='monthly',
            cohorts=[],
            overall_retention_rates={0: 1.0, 1: 0.5, 2: 0.1, 3: 0.05},  # 急剧下降
            retention_matrix=pd.DataFrame(),
            summary_stats={'avg_retention_rate': 0.05}
        )
        
        risk_factors = engine._identify_retention_risk_factors(retention_result)
        
        assert isinstance(risk_factors, list)
        assert len(risk_factors) > 0
        assert all(isinstance(factor, str) for factor in risk_factors)
        
    def test_get_analysis_summary(self, engine):
        """测试获取分析摘要"""
        summary = engine.get_analysis_summary()
        
        assert isinstance(summary, dict)
        assert 'total_events' in summary
        assert 'unique_users' in summary
        assert 'date_range' in summary
        assert 'estimated_cohorts' in summary
        assert 'analysis_capabilities' in summary
        
        # 检查估算的队列数
        estimated_cohorts = summary['estimated_cohorts']
        assert 'daily' in estimated_cohorts
        assert 'weekly' in estimated_cohorts
        assert 'monthly' in estimated_cohorts
        
    def test_get_analysis_summary_no_storage(self):
        """测试无存储管理器时的分析摘要"""
        engine = RetentionAnalysisEngine()
        summary = engine.get_analysis_summary()
        
        assert 'error' in summary
        
    def test_calculate_user_activity_periods(self, engine):
        """测试计算用户活动周期"""
        # 创建测试事件数据
        events = pd.DataFrame([
            {'user_pseudo_id': 'user_1', 'event_datetime': datetime(2024, 1, 1)},   # 第0天
            {'user_pseudo_id': 'user_1', 'event_datetime': datetime(2024, 1, 2)},   # 第1天
            {'user_pseudo_id': 'user_1', 'event_datetime': datetime(2024, 1, 8)},   # 第7天
            {'user_pseudo_id': 'user_2', 'event_datetime': datetime(2024, 1, 1)},   # 第0天
            {'user_pseudo_id': 'user_2', 'event_datetime': datetime(2024, 1, 15)},  # 第14天
        ])
        
        cohort_start = datetime(2024, 1, 1)
        
        # 测试日度分析
        daily_periods = engine._calculate_user_activity_periods(
            events, cohort_start, 'daily', 30
        )
        
        assert isinstance(daily_periods, dict)
        assert 'user_1' in daily_periods
        assert 'user_2' in daily_periods
        assert 0 in daily_periods['user_1']  # 第0天
        assert 1 in daily_periods['user_1']  # 第1天
        assert 7 in daily_periods['user_1']  # 第7天
        
        # 测试周度分析
        weekly_periods = engine._calculate_user_activity_periods(
            events, cohort_start, 'weekly', 10
        )
        
        assert 0 in weekly_periods['user_1']  # 第0周
        assert 1 in weekly_periods['user_1']  # 第1周
        assert 2 in weekly_periods['user_2']  # 第2周
        
    def test_calculate_overall_retention_rates(self, engine):
        """测试计算整体留存率"""
        # 创建测试队列数据
        cohort1 = CohortData(
            cohort_period='2024-01',
            cohort_size=100,
            first_activity_date=datetime(2024, 1, 1),
            retention_periods=[0, 1, 2],
            retention_rates=[1.0, 0.5, 0.3],
            retention_counts=[100, 50, 30]
        )
        
        cohort2 = CohortData(
            cohort_period='2024-02',
            cohort_size=200,
            first_activity_date=datetime(2024, 2, 1),
            retention_periods=[0, 1, 2],
            retention_rates=[1.0, 0.6, 0.4],
            retention_counts=[200, 120, 80]
        )
        
        overall_rates = engine._calculate_overall_retention_rates([cohort1, cohort2])
        
        assert isinstance(overall_rates, dict)
        assert 0 in overall_rates
        assert 1 in overall_rates
        assert 2 in overall_rates
        
        # 验证计算正确性
        # 第1期：(50 + 120) / (100 + 200) = 170 / 300 = 0.567
        assert abs(overall_rates[1] - 0.5667) < 0.001
        
        # 第2期：(30 + 80) / (100 + 200) = 110 / 300 = 0.367
        assert abs(overall_rates[2] - 0.3667) < 0.001
        
    def test_calculate_retention_summary_stats(self, engine):
        """测试计算留存摘要统计"""
        # 创建测试队列数据
        cohorts = [
            CohortData(
                cohort_period='2024-01',
                cohort_size=100,
                first_activity_date=datetime(2024, 1, 1),
                retention_periods=[0, 1, 2],
                retention_rates=[1.0, 0.5, 0.3],
                retention_counts=[100, 50, 30]
            ),
            CohortData(
                cohort_period='2024-02',
                cohort_size=150,
                first_activity_date=datetime(2024, 2, 1),
                retention_periods=[0, 1, 2],
                retention_rates=[1.0, 0.6, 0.4],
                retention_counts=[150, 90, 60]
            )
        ]
        
        stats = engine._calculate_retention_summary_stats(cohorts)
        
        assert isinstance(stats, dict)
        assert stats['total_cohorts'] == 2
        assert stats['total_users'] == 250
        assert stats['avg_cohort_size'] == 125
        assert stats['min_cohort_size'] == 100
        assert stats['max_cohort_size'] == 150
        
        # 检查留存率统计
        assert 'avg_retention_rate' in stats
        assert 'median_retention_rate' in stats
        assert 'min_retention_rate' in stats
        assert 'max_retention_rate' in stats
        
    def test_edge_case_empty_cohorts(self, engine):
        """测试空队列的边界情况"""
        empty_result = RetentionAnalysisResult(
            analysis_type='monthly',
            cohorts=[],
            overall_retention_rates={},
            retention_matrix=pd.DataFrame(),
            summary_stats={}
        )
        
        insights = engine.get_retention_insights(empty_result)
        
        assert isinstance(insights, dict)
        assert 'recommendations' in insights
        assert len(insights['recommendations']) > 0
        
    def test_edge_case_single_user_cohort(self, engine):
        """测试单用户队列的边界情况"""
        single_user_events = pd.DataFrame([
            {
                'user_pseudo_id': 'user_1',
                'event_datetime': datetime.now() - timedelta(days=i),
                'event_timestamp': int((datetime.now() - timedelta(days=i)).timestamp() * 1000000),
                'event_name': 'page_view'
            }
            for i in range(5)
        ])
        
        result = engine.calculate_retention_rates(single_user_events, max_periods=5)
        
        assert isinstance(result, RetentionAnalysisResult)
        # 单用户队列可能不满足最小队列大小要求
        
    @pytest.mark.parametrize("analysis_type", ['daily', 'weekly', 'monthly'])
    def test_different_analysis_types(self, engine, sample_events_data, analysis_type):
        """测试不同分析类型"""
        max_periods = {'daily': 14, 'weekly': 8, 'monthly': 6}[analysis_type]
        
        result = engine.calculate_retention_rates(
            sample_events_data,
            analysis_type=analysis_type,
            max_periods=max_periods
        )
        
        assert isinstance(result, RetentionAnalysisResult)
        assert result.analysis_type == analysis_type
        
    def test_performance_large_dataset(self, engine):
        """测试大数据集性能"""
        # 创建较大的数据集
        large_events = []
        for user_id in range(500):
            for day in range(30):
                if np.random.random() < 0.3:  # 30%概率用户在这天活跃
                    event_time = datetime.now() - timedelta(days=29-day) + timedelta(
                        hours=np.random.randint(0, 24)
                    )
                    
                    large_events.append({
                        'user_pseudo_id': f'user_{user_id}',
                        'event_datetime': event_time,
                        'event_timestamp': int(event_time.timestamp() * 1000000),
                        'event_name': 'page_view'
                    })
                    
        large_df = pd.DataFrame(large_events)
        
        # 测试性能
        import time
        start_time = time.time()
        result = engine.calculate_retention_rates(large_df, analysis_type='weekly', max_periods=4)
        end_time = time.time()
        
        assert isinstance(result, RetentionAnalysisResult)
        # 确保在合理时间内完成（15秒内）
        assert end_time - start_time < 15


if __name__ == '__main__':
    pytest.main([__file__, '-v'])