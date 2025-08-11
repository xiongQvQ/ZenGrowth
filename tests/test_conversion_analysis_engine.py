"""
转化分析引擎测试模块

测试转化漏斗构建和转化率计算功能。
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

from engines.conversion_analysis_engine import (
    ConversionAnalysisEngine,
    ConversionFunnel,
    FunnelStep,
    ConversionAnalysisResult,
    UserConversionJourney
)
from tools.data_storage_manager import DataStorageManager


class TestConversionAnalysisEngine:
    """转化分析引擎测试类"""
    
    @pytest.fixture
    def sample_conversion_events_data(self):
        """创建示例转化事件数据"""
        np.random.seed(42)
        
        events = []
        users = [f'user_{i}' for i in range(100)]
        
        # 定义转化漏斗步骤
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
        
        # 模拟转化漏斗，每个步骤都有一定的转化率
        conversion_rates = [1.0, 0.6, 0.4, 0.7, 0.8]  # 相对于上一步的转化率
        
        start_date = datetime.now() - timedelta(days=30)
        
        for user_id in users:
            # 决定用户能走到哪一步
            user_max_step = 0
            for i, rate in enumerate(conversion_rates):
                if np.random.random() < rate:
                    user_max_step = i
                else:
                    break
                    
            # 为用户生成事件
            current_time = start_date + timedelta(
                days=np.random.randint(0, 30),
                hours=np.random.randint(0, 24)
            )
            
            for step_idx in range(user_max_step + 1):
                step_name = funnel_steps[step_idx]
                
                # 在合理的时间间隔内生成事件
                if step_idx > 0:
                    current_time += timedelta(minutes=np.random.randint(1, 60))
                    
                event = {
                    'user_pseudo_id': user_id,
                    'event_name': step_name,
                    'event_timestamp': int(current_time.timestamp() * 1000000),
                    'event_datetime': current_time,
                    'event_date': current_time.strftime('%Y%m%d'),
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
                'total_events': np.random.randint(1, 20)
            }
            users.append(user)
            
        return pd.DataFrame(users)
        
    @pytest.fixture
    def storage_manager(self, sample_conversion_events_data, sample_users_data):
        """创建配置好的存储管理器"""
        manager = DataStorageManager()
        manager.store_events(sample_conversion_events_data)
        manager.store_users(sample_users_data)
        return manager
        
    @pytest.fixture
    def engine(self, storage_manager):
        """创建转化分析引擎实例"""
        return ConversionAnalysisEngine(storage_manager)
        
    def test_engine_initialization(self):
        """测试引擎初始化"""
        engine = ConversionAnalysisEngine()
        assert engine.storage_manager is None
        assert 'purchase_funnel' in engine.predefined_funnels
        assert 'purchase' in engine.conversion_events
        
    def test_engine_initialization_with_storage(self, storage_manager):
        """测试带存储管理器的引擎初始化"""
        engine = ConversionAnalysisEngine(storage_manager)
        assert engine.storage_manager is not None
        
    def test_build_conversion_funnel_basic(self, engine, sample_conversion_events_data):
        """测试基础转化漏斗构建"""
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'purchase']
        
        funnel = engine.build_conversion_funnel(
            sample_conversion_events_data,
            funnel_steps,
            "test_funnel"
        )
        
        assert isinstance(funnel, ConversionFunnel)
        assert funnel.funnel_name == "test_funnel"
        assert len(funnel.steps) == len(funnel_steps)
        assert funnel.total_users_entered > 0
        assert 0 <= funnel.overall_conversion_rate <= 1
        
        # 检查步骤顺序
        for i, step in enumerate(funnel.steps):
            assert isinstance(step, FunnelStep)
            assert step.step_name == funnel_steps[i]
            assert step.step_order == i
            assert step.total_users >= 0
            assert 0 <= step.conversion_rate <= 1
            
    def test_build_conversion_funnel_empty_data(self, engine):
        """测试空数据的漏斗构建"""
        empty_df = pd.DataFrame()
        funnel_steps = ['page_view', 'purchase']
        
        funnel = engine.build_conversion_funnel(empty_df, funnel_steps, "empty_funnel")
        
        assert isinstance(funnel, ConversionFunnel)
        assert len(funnel.steps) == 0
        assert funnel.overall_conversion_rate == 0.0
        assert funnel.total_users_entered == 0
        
    def test_build_conversion_funnel_invalid_steps(self, engine, sample_conversion_events_data):
        """测试无效步骤的漏斗构建"""
        invalid_steps = ['nonexistent_event1', 'nonexistent_event2']
        
        funnel = engine.build_conversion_funnel(
            sample_conversion_events_data,
            invalid_steps,
            "invalid_funnel"
        )
        
        assert isinstance(funnel, ConversionFunnel)
        assert len(funnel.steps) == 0
        
    def test_analyze_user_journeys(self, engine, sample_conversion_events_data):
        """测试用户旅程分析"""
        funnel_steps = ['page_view', 'view_item', 'add_to_cart']
        
        # 筛选相关事件
        funnel_events = sample_conversion_events_data[
            sample_conversion_events_data['event_name'].isin(funnel_steps)
        ]
        
        user_journeys = engine._analyze_user_journeys(
            funnel_events, funnel_steps, 24
        )
        
        assert isinstance(user_journeys, dict)
        assert len(user_journeys) > 0
        
        # 检查旅程结构
        for user_id, journey in user_journeys.items():
            assert isinstance(journey, dict)
            assert 'completed_steps' in journey
            assert 'completed_all_steps' in journey
            assert isinstance(journey['completed_steps'], list)
            assert isinstance(journey['completed_all_steps'], bool)
            
    def test_analyze_single_user_journey(self, engine):
        """测试单用户旅程分析"""
        # 创建单用户事件序列
        base_time = datetime.now()
        user_events = pd.DataFrame([
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'page_view',
                'event_datetime': base_time
            },
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'view_item',
                'event_datetime': base_time + timedelta(minutes=5)
            },
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'add_to_cart',
                'event_datetime': base_time + timedelta(minutes=10)
            }
        ])
        
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'purchase']
        
        journey = engine._analyze_single_user_journey(user_events, funnel_steps, 24)
        
        assert journey is not None
        assert journey['completed_steps'] == ['page_view', 'view_item', 'add_to_cart']
        assert journey['completed_all_steps'] == False
        assert journey['total_time'] == 600  # 10分钟 = 600秒
        
    def test_build_funnel_steps(self, engine):
        """测试漏斗步骤构建"""
        # 创建模拟用户旅程数据
        user_journeys = {
            'user_1': {
                'completed_steps': ['page_view', 'view_item'],
                'completed_all_steps': False,
                'step_durations': {'page_view_to_view_item': 300}
            },
            'user_2': {
                'completed_steps': ['page_view', 'view_item', 'purchase'],
                'completed_all_steps': True,
                'step_durations': {
                    'page_view_to_view_item': 180,
                    'view_item_to_purchase': 600
                }
            },
            'user_3': {
                'completed_steps': ['page_view'],
                'completed_all_steps': False,
                'step_durations': {}
            }
        }
        
        funnel_steps = ['page_view', 'view_item', 'purchase']
        
        steps = engine._build_funnel_steps(user_journeys, funnel_steps)
        
        assert len(steps) == 3
        
        # 检查第一步（page_view）
        assert steps[0].step_name == 'page_view'
        assert steps[0].total_users == 3  # 所有用户都到达了
        assert steps[0].conversion_rate == 1.0  # 第一步转化率是到达率
        
        # 检查第二步（view_item）
        assert steps[1].step_name == 'view_item'
        assert steps[1].total_users == 2  # 2个用户到达
        assert steps[1].conversion_rate == 2/3  # 相对于上一步的转化率
        
        # 检查第三步（purchase）
        assert steps[2].step_name == 'purchase'
        assert steps[2].total_users == 1  # 1个用户到达
        assert steps[2].conversion_rate == 1/2  # 相对于上一步的转化率
        
    def test_identify_bottleneck_step(self, engine):
        """测试瓶颈步骤识别"""
        # 创建测试步骤
        steps = [
            FunnelStep('page_view', 0, 100, 1.0, 0.0, None, None),
            FunnelStep('view_item', 1, 80, 0.8, 0.2, None, None),
            FunnelStep('add_to_cart', 2, 20, 0.25, 0.75, None, None),  # 瓶颈
            FunnelStep('purchase', 3, 15, 0.75, 0.25, None, None)
        ]
        
        bottleneck = engine._identify_bottleneck_step(steps)
        
        assert bottleneck == 'add_to_cart'  # 转化率最低的步骤
        
    def test_calculate_conversion_rates(self, engine, sample_conversion_events_data):
        """测试转化率计算"""
        result = engine.calculate_conversion_rates(sample_conversion_events_data)
        
        assert isinstance(result, ConversionAnalysisResult)
        assert isinstance(result.funnels, list)
        assert isinstance(result.conversion_metrics, dict)
        assert isinstance(result.bottleneck_analysis, dict)
        assert isinstance(result.time_analysis, dict)
        assert isinstance(result.segment_analysis, dict)
        
        # 检查是否有有效的漏斗
        assert len(result.funnels) > 0
        
        # 检查转化指标
        assert 'overall_conversion_user_rate' in result.conversion_metrics
        
    def test_calculate_conversion_metrics(self, engine, sample_conversion_events_data):
        """测试转化指标计算"""
        # 创建测试漏斗
        funnel = ConversionFunnel(
            funnel_name='test',
            steps=[],
            overall_conversion_rate=0.3,
            total_users_entered=100,
            total_users_converted=30,
            avg_completion_time=None,
            bottleneck_step=None
        )
        
        metrics = engine._calculate_conversion_metrics([funnel], sample_conversion_events_data)
        
        assert isinstance(metrics, dict)
        assert 'overall_conversion_user_rate' in metrics
        assert 'avg_funnel_conversion_rate' in metrics
        
    def test_analyze_bottlenecks(self, engine):
        """测试瓶颈分析"""
        # 创建测试漏斗
        steps = [
            FunnelStep('page_view', 0, 100, 1.0, 0.0, None, None),
            FunnelStep('view_item', 1, 50, 0.5, 0.5, None, None),
            FunnelStep('purchase', 2, 10, 0.2, 0.8, None, None)  # 瓶颈
        ]
        
        funnel = ConversionFunnel(
            funnel_name='test_funnel',
            steps=steps,
            overall_conversion_rate=0.1,
            total_users_entered=100,
            total_users_converted=10,
            avg_completion_time=None,
            bottleneck_step='purchase'
        )
        
        bottleneck_analysis = engine._analyze_bottlenecks([funnel])
        
        assert isinstance(bottleneck_analysis, dict)
        assert 'funnel_bottlenecks' in bottleneck_analysis
        assert 'common_bottlenecks' in bottleneck_analysis
        assert 'bottleneck_severity' in bottleneck_analysis
        
    def test_analyze_conversion_times(self, engine):
        """测试转化时间分析"""
        # 创建带时间信息的测试漏斗
        steps = [
            FunnelStep('page_view', 0, 100, 1.0, 0.0, 300, 250),  # 5分钟到下一步
            FunnelStep('purchase', 1, 50, 0.5, 0.5, None, None)
        ]
        
        funnel = ConversionFunnel(
            funnel_name='test_funnel',
            steps=steps,
            overall_conversion_rate=0.5,
            total_users_entered=100,
            total_users_converted=50,
            avg_completion_time=600,  # 10分钟
            bottleneck_step=None
        )
        
        time_analysis = engine._analyze_conversion_times([funnel])
        
        assert isinstance(time_analysis, dict)
        assert 'funnel_completion_times' in time_analysis
        assert 'step_transition_times' in time_analysis
        
    def test_identify_drop_off_points(self, engine, sample_conversion_events_data):
        """测试流失点识别"""
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'purchase']
        
        drop_off_analysis = engine.identify_drop_off_points(
            sample_conversion_events_data,
            funnel_steps
        )
        
        assert isinstance(drop_off_analysis, dict)
        assert 'funnel_steps' in drop_off_analysis
        assert 'major_drop_off_points' in drop_off_analysis
        assert 'drop_off_insights' in drop_off_analysis
        
        # 检查漏斗步骤信息
        funnel_steps_info = drop_off_analysis['funnel_steps']
        assert len(funnel_steps_info) > 0
        
        for step_info in funnel_steps_info:
            assert 'step_name' in step_info
            assert 'users_reached' in step_info
            assert 'conversion_rate' in step_info
            assert 'drop_off_rate' in step_info
            
    def test_create_user_conversion_journeys(self, engine, sample_conversion_events_data):
        """测试用户转化旅程创建"""
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'purchase']
        
        journeys = engine.create_user_conversion_journeys(
            sample_conversion_events_data,
            funnel_steps
        )
        
        assert isinstance(journeys, list)
        assert len(journeys) > 0
        
        # 检查旅程结构
        for journey in journeys:
            assert isinstance(journey, UserConversionJourney)
            assert isinstance(journey.user_id, str)
            assert isinstance(journey.journey_steps, list)
            assert journey.conversion_status in ['converted', 'dropped_off', 'in_progress']
            
    def test_create_single_user_journey(self, engine):
        """测试单用户旅程创建"""
        # 创建用户事件
        user_events = pd.DataFrame([
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'page_view',
                'event_datetime': datetime.now()
            },
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'purchase',
                'event_datetime': datetime.now() + timedelta(minutes=10)
            }
        ])
        
        funnel_steps = ['page_view', 'view_item', 'purchase']
        
        journey = engine._create_single_user_journey(user_events, funnel_steps, 'user_1')
        
        assert journey is not None
        assert journey.user_id == 'user_1'
        assert journey.conversion_status == 'converted'  # 完成了最终步骤
        assert journey.total_journey_time == 600  # 10分钟
        
    def test_analyze_conversion_attribution(self, engine, sample_conversion_events_data):
        """测试转化归因分析"""
        attribution_analysis = engine.analyze_conversion_attribution(
            sample_conversion_events_data,
            attribution_window_days=7
        )
        
        assert isinstance(attribution_analysis, dict)
        assert 'first_touch_attribution' in attribution_analysis
        assert 'last_touch_attribution' in attribution_analysis
        assert 'multi_touch_attribution' in attribution_analysis
        assert 'attribution_insights' in attribution_analysis
        
    def test_get_conversion_insights(self, engine, sample_conversion_events_data):
        """测试转化分析洞察"""
        # 先进行转化分析
        conversion_result = engine.calculate_conversion_rates(sample_conversion_events_data)
        
        insights = engine.get_conversion_insights(conversion_result)
        
        assert isinstance(insights, dict)
        assert 'key_metrics' in insights
        assert 'optimization_opportunities' in insights
        assert 'performance_insights' in insights
        assert 'recommendations' in insights
        
        # 检查关键指标
        key_metrics = insights['key_metrics']
        assert 'avg_conversion_rate' in key_metrics
        assert 'total_funnels_analyzed' in key_metrics
        
    def test_get_analysis_summary(self, engine):
        """测试获取分析摘要"""
        summary = engine.get_analysis_summary()
        
        assert isinstance(summary, dict)
        assert 'total_events' in summary
        assert 'unique_users' in summary
        assert 'conversion_events_count' in summary
        assert 'conversion_users_count' in summary
        assert 'available_funnels' in summary
        assert 'analysis_capabilities' in summary
        
        # 检查可用漏斗
        available_funnels = summary['available_funnels']
        assert 'purchase_funnel' in available_funnels
        assert 'user_registration' in available_funnels
        
    def test_get_analysis_summary_no_storage(self):
        """测试无存储管理器时的分析摘要"""
        engine = ConversionAnalysisEngine()
        summary = engine.get_analysis_summary()
        
        assert 'error' in summary
        
    def test_edge_case_single_step_funnel(self, engine, sample_conversion_events_data):
        """测试单步骤漏斗的边界情况"""
        single_step = ['page_view']
        
        funnel = engine.build_conversion_funnel(
            sample_conversion_events_data,
            single_step,
            "single_step_funnel"
        )
        
        assert isinstance(funnel, ConversionFunnel)
        assert len(funnel.steps) == 1
        assert funnel.steps[0].conversion_rate == 1.0  # 单步骤转化率应该是1.0
        assert funnel.bottleneck_step is None  # 单步骤没有瓶颈
        
    def test_edge_case_no_conversions(self, engine):
        """测试无转化事件的边界情况"""
        # 创建只有浏览事件的数据
        no_conversion_events = pd.DataFrame([
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'page_view',
                'event_datetime': datetime.now(),
                'event_timestamp': int(datetime.now().timestamp() * 1000000)
            }
        ])
        
        result = engine.calculate_conversion_rates(no_conversion_events)
        
        assert isinstance(result, ConversionAnalysisResult)
        # 应该仍然能处理，只是转化率为0
        
    def test_time_window_filtering(self, engine):
        """测试时间窗口过滤"""
        # 创建时间跨度很大的事件
        base_time = datetime.now()
        user_events = pd.DataFrame([
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'page_view',
                'event_datetime': base_time
            },
            {
                'user_pseudo_id': 'user_1',
                'event_name': 'purchase',
                'event_datetime': base_time + timedelta(days=2)  # 超过24小时窗口
            }
        ])
        
        funnel_steps = ['page_view', 'purchase']
        
        journey = engine._analyze_single_user_journey(user_events, funnel_steps, 24)
        
        # 由于超过时间窗口，用户应该只完成第一步
        assert journey['completed_steps'] == ['page_view']
        assert journey['completed_all_steps'] == False
        
    @pytest.mark.parametrize("time_window", [1, 6, 24, 72])
    def test_different_time_windows(self, engine, sample_conversion_events_data, time_window):
        """测试不同时间窗口"""
        funnel_steps = ['page_view', 'view_item', 'purchase']
        
        funnel = engine.build_conversion_funnel(
            sample_conversion_events_data,
            funnel_steps,
            f"funnel_{time_window}h",
            time_window_hours=time_window
        )
        
        assert isinstance(funnel, ConversionFunnel)
        # 时间窗口越短，转化率通常越低
        
    def test_performance_large_dataset(self, engine):
        """测试大数据集性能"""
        # 创建较大的数据集
        large_events = []
        for user_id in range(1000):
            for step in ['page_view', 'view_item', 'add_to_cart']:
                if np.random.random() < 0.5:  # 50%概率完成每个步骤
                    event_time = datetime.now() - timedelta(
                        days=np.random.randint(0, 30),
                        hours=np.random.randint(0, 24)
                    )
                    
                    large_events.append({
                        'user_pseudo_id': f'user_{user_id}',
                        'event_name': step,
                        'event_datetime': event_time,
                        'event_timestamp': int(event_time.timestamp() * 1000000),
                        'platform': 'web'
                    })
                    
        large_df = pd.DataFrame(large_events)
        
        # 测试性能
        import time
        start_time = time.time()
        funnel = engine.build_conversion_funnel(
            large_df,
            ['page_view', 'view_item', 'add_to_cart'],
            'large_funnel'
        )
        end_time = time.time()
        
        assert isinstance(funnel, ConversionFunnel)
        # 确保在合理时间内完成（10秒内）
        assert end_time - start_time < 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])