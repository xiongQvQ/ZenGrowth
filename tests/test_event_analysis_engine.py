"""
事件分析引擎测试模块

测试事件频次统计、趋势分析、关联性分析和关键事件识别功能。
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

from engines.event_analysis_engine import (
    EventAnalysisEngine,
    EventFrequencyResult,
    EventTrendResult,
    EventCorrelationResult,
    KeyEventResult
)
from tools.data_storage_manager import DataStorageManager


class TestEventAnalysisEngine:
    """事件分析引擎测试类"""
    
    @pytest.fixture
    def sample_events_data(self):
        """创建示例事件数据"""
        np.random.seed(42)
        
        # 创建30天的事件数据
        start_date = datetime.now() - timedelta(days=30)
        events = []
        
        event_types = ['page_view', 'sign_up', 'login', 'purchase', 'add_to_cart']
        users = [f'user_{i}' for i in range(100)]
        
        for day in range(30):
            current_date = start_date + timedelta(days=day)
            
            # 每天生成不同数量的事件
            daily_events = np.random.poisson(50)
            
            for _ in range(daily_events):
                event = {
                    'user_pseudo_id': np.random.choice(users),
                    'event_name': np.random.choice(event_types, p=[0.5, 0.1, 0.2, 0.05, 0.15]),
                    'event_timestamp': int((current_date + timedelta(
                        hours=np.random.randint(0, 24),
                        minutes=np.random.randint(0, 60)
                    )).timestamp() * 1000000),
                    'event_datetime': current_date + timedelta(
                        hours=np.random.randint(0, 24),
                        minutes=np.random.randint(0, 60)
                    ),
                    'event_date': current_date.strftime('%Y%m%d'),
                    'platform': np.random.choice(['web', 'mobile']),
                    'device': {'category': np.random.choice(['desktop', 'mobile', 'tablet'])},
                    'geo': {'country': np.random.choice(['US', 'UK', 'CA'])}
                }
                events.append(event)
                
        return pd.DataFrame(events)
        
    @pytest.fixture
    def sample_users_data(self):
        """创建示例用户数据"""
        users = []
        for i in range(100):
            user = {
                'user_pseudo_id': f'user_{i}',
                'platform': np.random.choice(['web', 'mobile']),
                'device_category': np.random.choice(['desktop', 'mobile', 'tablet']),
                'geo_country': np.random.choice(['US', 'UK', 'CA']),
                'first_seen': datetime.now() - timedelta(days=np.random.randint(1, 30)),
                'last_seen': datetime.now() - timedelta(days=np.random.randint(0, 5)),
                'total_events': np.random.randint(1, 50)
            }
            users.append(user)
            
        return pd.DataFrame(users)
        
    @pytest.fixture
    def sample_sessions_data(self):
        """创建示例会话数据"""
        sessions = []
        for i in range(200):
            session = {
                'session_id': f'session_{i}',
                'user_pseudo_id': f'user_{np.random.randint(0, 100)}',
                'duration_seconds': np.random.randint(30, 3600),
                'event_count': np.random.randint(1, 20),
                'conversions': np.random.choice([0, 1], p=[0.8, 0.2]),
                'start_time': datetime.now() - timedelta(days=np.random.randint(0, 30))
            }
            sessions.append(session)
            
        return pd.DataFrame(sessions)
        
    @pytest.fixture
    def storage_manager(self, sample_events_data, sample_users_data, sample_sessions_data):
        """创建配置好的存储管理器"""
        manager = DataStorageManager()
        manager.store_events(sample_events_data)
        manager.store_users(sample_users_data)
        manager.store_sessions(sample_sessions_data)
        return manager
        
    @pytest.fixture
    def engine(self, storage_manager):
        """创建事件分析引擎实例"""
        return EventAnalysisEngine(storage_manager)
        
    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = EventAnalysisEngine()
        assert engine.storage_manager is None
        assert 'sign_up' in engine.conversion_events
        assert 'page_view' in engine.engagement_events
        
    def test_engine_initialization_with_storage(self, storage_manager):
        """测试带存储管理器的引擎初始化"""
        engine = EventAnalysisEngine(storage_manager)
        assert engine.storage_manager is not None
        
    def test_calculate_event_frequency_basic(self, engine, sample_events_data):
        """测试基础事件频次计算"""
        results = engine.calculate_event_frequency(sample_events_data)
        
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # 检查结果结构
        for event_type, result in results.items():
            assert isinstance(result, EventFrequencyResult)
            assert result.event_name == event_type
            assert result.total_count > 0
            assert result.unique_users > 0
            assert result.avg_per_user >= 0
            assert isinstance(result.frequency_distribution, dict)
            assert isinstance(result.percentiles, dict)
            
    def test_calculate_event_frequency_with_filters(self, engine):
        """测试带过滤条件的事件频次计算"""
        results = engine.calculate_event_frequency(
            event_types=['page_view', 'sign_up']
        )
        
        assert isinstance(results, dict)
        # 应该只包含指定的事件类型
        for event_type in results.keys():
            assert event_type in ['page_view', 'sign_up']
            
    def test_calculate_event_frequency_empty_data(self, engine):
        """测试空数据的事件频次计算"""
        empty_df = pd.DataFrame()
        results = engine.calculate_event_frequency(empty_df)
        
        assert results == {}
        
    def test_analyze_event_trends_basic(self, engine, sample_events_data):
        """测试基础事件趋势分析"""
        results = engine.analyze_event_trends(sample_events_data)
        
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # 检查结果结构
        for event_type, result in results.items():
            assert isinstance(result, EventTrendResult)
            assert result.event_name == event_type
            assert isinstance(result.trend_data, pd.DataFrame)
            assert result.trend_direction in ['increasing', 'decreasing', 'stable']
            assert isinstance(result.growth_rate, float)
            
    def test_analyze_event_trends_different_granularity(self, engine, sample_events_data):
        """测试不同时间粒度的趋势分析"""
        # 测试周粒度
        results_weekly = engine.analyze_event_trends(
            sample_events_data, 
            time_granularity='weekly'
        )
        assert isinstance(results_weekly, dict)
        
        # 测试月粒度
        results_monthly = engine.analyze_event_trends(
            sample_events_data,
            time_granularity='monthly'
        )
        assert isinstance(results_monthly, dict)
        
    def test_analyze_event_trends_insufficient_data(self, engine):
        """测试数据不足的趋势分析"""
        # 创建只有少量数据的DataFrame
        small_data = pd.DataFrame([
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'page_view',
                'event_timestamp': int(datetime.now().timestamp() * 1000000),
                'event_datetime': datetime.now()
            }
        ])
        
        results = engine.analyze_event_trends(small_data, min_data_points=7)
        
        # 应该返回空结果，因为数据点不足
        assert len(results) == 0
        
    def test_analyze_event_correlations_basic(self, engine, sample_events_data):
        """测试基础事件关联性分析"""
        results = engine.analyze_event_correlations(sample_events_data)
        
        assert isinstance(results, list)
        
        # 检查结果结构
        for result in results:
            assert isinstance(result, EventCorrelationResult)
            assert isinstance(result.event_pair, tuple)
            assert len(result.event_pair) == 2
            assert isinstance(result.correlation_coefficient, float)
            assert isinstance(result.significance_level, float)
            assert isinstance(result.co_occurrence_rate, float)
            assert isinstance(result.temporal_pattern, dict)
            
    def test_analyze_event_correlations_specific_events(self, engine, sample_events_data):
        """测试特定事件的关联性分析"""
        results = engine.analyze_event_correlations(
            sample_events_data,
            event_types=['page_view', 'sign_up', 'purchase']
        )
        
        assert isinstance(results, list)
        
        # 检查只包含指定事件的关联性
        for result in results:
            event1, event2 = result.event_pair
            assert event1 in ['page_view', 'sign_up', 'purchase']
            assert event2 in ['page_view', 'sign_up', 'purchase']
            
    def test_identify_key_events_basic(self, engine, sample_events_data, sample_users_data, sample_sessions_data):
        """测试基础关键事件识别"""
        results = engine.identify_key_events(
            sample_events_data, 
            sample_users_data, 
            sample_sessions_data
        )
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 检查结果结构
        for result in results:
            assert isinstance(result, KeyEventResult)
            assert isinstance(result.event_name, str)
            assert isinstance(result.importance_score, float)
            assert isinstance(result.user_engagement_impact, float)
            assert isinstance(result.conversion_impact, float)
            assert isinstance(result.retention_impact, float)
            assert isinstance(result.reasons, list)
            
        # 检查结果按重要性排序
        scores = [result.importance_score for result in results]
        assert scores == sorted(scores, reverse=True)
        
    def test_identify_key_events_top_k(self, engine, sample_events_data):
        """测试限制返回数量的关键事件识别"""
        results = engine.identify_key_events(sample_events_data, top_k=3)
        
        assert len(results) <= 3
        
    def test_frequency_distribution_calculation(self, engine):
        """测试频次分布计算"""
        # 创建测试数据
        user_counts = pd.Series([1, 2, 3, 5, 10, 25, 100])
        
        distribution = engine._calculate_frequency_distribution(user_counts)
        
        assert isinstance(distribution, dict)
        assert '1' in distribution
        assert '2' in distribution
        assert '50+' in distribution
        
    def test_trend_direction_calculation(self, engine):
        """测试趋势方向计算"""
        # 测试上升趋势
        increasing_data = pd.DataFrame({
            'event_count': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        direction, growth_rate = engine._calculate_trend_direction(increasing_data)
        assert direction == 'increasing'
        assert growth_rate > 0
        
        # 测试下降趋势
        decreasing_data = pd.DataFrame({
            'event_count': [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        })
        direction, growth_rate = engine._calculate_trend_direction(decreasing_data)
        assert direction == 'decreasing'
        assert growth_rate < 0
        
        # 测试稳定趋势
        stable_data = pd.DataFrame({
            'event_count': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        })
        direction, growth_rate = engine._calculate_trend_direction(stable_data)
        assert direction == 'stable'
        assert abs(growth_rate) < 5
        
    def test_seasonal_pattern_detection(self, engine):
        """测试季节性模式检测"""
        # 创建有周模式的日数据
        dates = pd.date_range(start='2024-01-01', periods=21, freq='D')
        trend_data = pd.DataFrame({
            'date': dates,
            'event_count': [10 if d.weekday() < 5 else 5 for d in dates]  # 工作日高，周末低
        })
        
        pattern = engine._detect_seasonal_pattern(trend_data, 'daily')
        
        assert isinstance(pattern, dict)
        assert len(pattern) == 7  # 7天
        
    def test_anomaly_detection(self, engine):
        """测试异常检测"""
        # 创建有异常值的数据
        trend_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=10, freq='D'),
            'event_count': [10, 10, 10, 100, 10, 10, 10, 10, 10, 10]  # 第4天是异常值
        })
        
        anomalies = engine._detect_anomalies(trend_data)
        
        assert isinstance(anomalies, list)
        assert len(anomalies) > 0
        
        # 检查异常点结构
        for anomaly in anomalies:
            assert 'date' in anomaly
            assert 'value' in anomaly
            assert 'z_score' in anomaly
            assert 'type' in anomaly
            
    def test_chi_square_correlation(self, engine, sample_events_data):
        """测试卡方相关性计算"""
        correlation, p_value = engine._calculate_chi_square_correlation(
            sample_events_data, 'page_view', 'sign_up'
        )
        
        assert isinstance(correlation, float)
        assert isinstance(p_value, float)
        assert 0 <= correlation <= 1
        assert 0 <= p_value <= 1
        
    def test_temporal_pattern_analysis(self, engine, sample_events_data):
        """测试时间模式分析"""
        # 获取共现用户
        page_view_users = set(sample_events_data[
            sample_events_data['event_name'] == 'page_view'
        ]['user_pseudo_id'])
        sign_up_users = set(sample_events_data[
            sample_events_data['event_name'] == 'sign_up'
        ]['user_pseudo_id'])
        co_occurrence_users = page_view_users.intersection(sign_up_users)
        
        if co_occurrence_users:
            pattern = engine._analyze_temporal_pattern(
                sample_events_data, 'page_view', 'sign_up', co_occurrence_users
            )
            
            assert isinstance(pattern, dict)
            if pattern:  # 如果有结果
                assert 'sequence_patterns' in pattern
                assert 'avg_time_gap_seconds' in pattern
                
    def test_user_engagement_impact_calculation(self, engine, sample_events_data):
        """测试用户参与度影响计算"""
        page_view_data = sample_events_data[sample_events_data['event_name'] == 'page_view']
        
        impact = engine._calculate_user_engagement_impact(
            sample_events_data, page_view_data, 'page_view'
        )
        
        assert isinstance(impact, float)
        assert 0 <= impact <= 100
        
    def test_conversion_impact_calculation(self, engine, sample_events_data, sample_sessions_data):
        """测试转化影响计算"""
        # 测试转化事件
        impact_conversion = engine._calculate_conversion_impact(
            sample_events_data, sample_sessions_data, 'sign_up'
        )
        assert isinstance(impact_conversion, float)
        assert impact_conversion >= 80  # 转化事件应该有高分
        
        # 测试非转化事件
        impact_non_conversion = engine._calculate_conversion_impact(
            sample_events_data, sample_sessions_data, 'page_view'
        )
        assert isinstance(impact_non_conversion, float)
        assert 0 <= impact_non_conversion <= 100
        
    def test_retention_impact_calculation(self, engine, sample_events_data, sample_users_data):
        """测试留存影响计算"""
        impact = engine._calculate_retention_impact(
            sample_events_data, sample_users_data, 'page_view'
        )
        
        assert isinstance(impact, float)
        assert 0 <= impact <= 100
        
    def test_importance_reasons_generation(self, engine):
        """测试重要性原因生成"""
        reasons = engine._generate_importance_reasons(80, 70, 60, 'sign_up')
        
        assert isinstance(reasons, list)
        assert len(reasons) > 0
        assert all(isinstance(reason, str) for reason in reasons)
        
    def test_get_analysis_summary(self, engine):
        """测试获取分析摘要"""
        summary = engine.get_analysis_summary()
        
        assert isinstance(summary, dict)
        assert 'total_events' in summary
        assert 'unique_users' in summary
        assert 'unique_event_types' in summary
        assert 'analysis_capabilities' in summary
        
    def test_get_analysis_summary_no_storage(self):
        """测试无存储管理器时的分析摘要"""
        engine = EventAnalysisEngine()
        summary = engine.get_analysis_summary()
        
        assert 'error' in summary
        
    def test_time_aggregation(self, engine, sample_events_data):
        """测试时间聚合功能"""
        # 测试日聚合
        daily_agg = engine._aggregate_by_time(sample_events_data, 'daily')
        assert isinstance(daily_agg, pd.DataFrame)
        assert 'date' in daily_agg.columns
        assert 'event_count' in daily_agg.columns
        
        # 测试周聚合
        weekly_agg = engine._aggregate_by_time(sample_events_data, 'weekly')
        assert isinstance(weekly_agg, pd.DataFrame)
        
        # 测试月聚合
        monthly_agg = engine._aggregate_by_time(sample_events_data, 'monthly')
        assert isinstance(monthly_agg, pd.DataFrame)
        
    def test_error_handling_invalid_granularity(self, engine, sample_events_data):
        """测试无效时间粒度的错误处理"""
        with pytest.raises(ValueError):
            engine._aggregate_by_time(sample_events_data, 'invalid_granularity')
            
    def test_error_handling_missing_timestamp(self, engine):
        """测试缺少时间戳的错误处理"""
        # 创建没有时间戳的数据
        invalid_data = pd.DataFrame([
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'page_view'
            }
        ])
        
        with pytest.raises(ValueError):
            engine.analyze_event_trends(invalid_data)
            
    def test_edge_case_single_user(self, engine):
        """测试单用户边界情况"""
        single_user_data = pd.DataFrame([
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'page_view',
                'event_timestamp': int(datetime.now().timestamp() * 1000000),
                'event_datetime': datetime.now()
            }
        ])
        
        results = engine.calculate_event_frequency(single_user_data)
        
        assert isinstance(results, dict)
        assert 'page_view' in results
        assert results['page_view'].unique_users == 1
        
    def test_edge_case_single_event_type(self, engine):
        """测试单事件类型边界情况"""
        single_event_data = pd.DataFrame([
            {
                'user_pseudo_id': f'user_{i}',
                'event_name': 'page_view',
                'event_timestamp': int((datetime.now() + timedelta(hours=i)).timestamp() * 1000000),
                'event_datetime': datetime.now() + timedelta(hours=i)
            }
            for i in range(10)
        ])
        
        correlations = engine.analyze_event_correlations(single_event_data)
        
        # 单事件类型不应该有关联性结果
        assert len(correlations) == 0
        
    @pytest.mark.parametrize("threshold", [1.0, 2.0, 3.0])
    def test_anomaly_detection_different_thresholds(self, engine, threshold):
        """测试不同阈值的异常检测"""
        trend_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=10, freq='D'),
            'event_count': [10, 10, 10, 50, 10, 10, 10, 10, 10, 10]
        })
        
        anomalies = engine._detect_anomalies(trend_data, threshold)
        
        assert isinstance(anomalies, list)
        # 更高的阈值应该检测到更少的异常
        
    def test_performance_large_dataset(self, engine):
        """测试大数据集性能"""
        # 创建较大的数据集
        large_data = pd.DataFrame([
            {
                'user_pseudo_id': f'user_{i % 1000}',
                'event_name': f'event_{i % 10}',
                'event_timestamp': int((datetime.now() + timedelta(minutes=i)).timestamp() * 1000000),
                'event_datetime': datetime.now() + timedelta(minutes=i)
            }
            for i in range(10000)
        ])
        
        # 测试频次分析性能
        import time
        start_time = time.time()
        results = engine.calculate_event_frequency(large_data)
        end_time = time.time()
        
        assert isinstance(results, dict)
        assert len(results) > 0
        # 确保在合理时间内完成（10秒内）
        assert end_time - start_time < 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])