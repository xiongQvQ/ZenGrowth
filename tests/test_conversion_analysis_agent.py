"""
转化分析智能体测试模块

测试ConversionAnalysisAgent类的各项功能，包括漏斗分析、转化率计算和瓶颈识别。
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from agents.conversion_analysis_agent import (
    ConversionAnalysisAgent,
    FunnelAnalysisTool,
    ConversionRateAnalysisTool,
    BottleneckIdentificationTool,
    ConversionPathAnalysisTool
)
from tools.data_storage_manager import DataStorageManager


class TestConversionAnalysisAgent:
    """转化分析智能体测试类"""
    
    @pytest.fixture
    def sample_events_data(self):
        """创建示例事件数据"""
        np.random.seed(42)
        
        # 创建用户ID
        user_ids = [f"user_{i}" for i in range(100)]
        
        events = []
        base_time = datetime.now() - timedelta(days=7)
        
        for user_id in user_ids:
            user_events = []
            current_time = base_time + timedelta(hours=np.random.randint(0, 168))
            
            # 模拟转化漏斗：page_view -> view_item -> add_to_cart -> begin_checkout -> purchase
            funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
            
            # 每个用户都有page_view
            user_events.append({
                'user_pseudo_id': user_id,
                'event_name': 'page_view',
                'event_datetime': current_time,
                'event_timestamp': int(current_time.timestamp() * 1000000)
            })
            current_time += timedelta(minutes=np.random.randint(1, 30))
            
            # 80%的用户会view_item
            if np.random.random() < 0.8:
                user_events.append({
                    'user_pseudo_id': user_id,
                    'event_name': 'view_item',
                    'event_datetime': current_time,
                    'event_timestamp': int(current_time.timestamp() * 1000000)
                })
                current_time += timedelta(minutes=np.random.randint(1, 60))
                
                # 50%的view_item用户会add_to_cart
                if np.random.random() < 0.5:
                    user_events.append({
                        'user_pseudo_id': user_id,
                        'event_name': 'add_to_cart',
                        'event_datetime': current_time,
                        'event_timestamp': int(current_time.timestamp() * 1000000)
                    })
                    current_time += timedelta(minutes=np.random.randint(1, 120))
                    
                    # 60%的add_to_cart用户会begin_checkout
                    if np.random.random() < 0.6:
                        user_events.append({
                            'user_pseudo_id': user_id,
                            'event_name': 'begin_checkout',
                            'event_datetime': current_time,
                            'event_timestamp': int(current_time.timestamp() * 1000000)
                        })
                        current_time += timedelta(minutes=np.random.randint(1, 30))
                        
                        # 70%的begin_checkout用户会purchase
                        if np.random.random() < 0.7:
                            user_events.append({
                                'user_pseudo_id': user_id,
                                'event_name': 'purchase',
                                'event_datetime': current_time,
                                'event_timestamp': int(current_time.timestamp() * 1000000)
                            })
            
            events.extend(user_events)
        
        return pd.DataFrame(events)
    
    @pytest.fixture
    def mock_storage_manager(self, sample_events_data):
        """创建模拟存储管理器"""
        storage_manager = Mock(spec=DataStorageManager)
        storage_manager.get_data.return_value = sample_events_data
        return storage_manager
    
    @pytest.fixture
    def conversion_agent(self, mock_storage_manager):
        """创建转化分析智能体实例"""
        return ConversionAnalysisAgent(mock_storage_manager)
    
    def test_agent_initialization(self, conversion_agent):
        """测试智能体初始化"""
        assert conversion_agent.storage_manager is not None
        assert len(conversion_agent.tools) == 4
        assert conversion_agent.agent is not None
        
        # 检查工具类型
        tool_names = [tool.name for tool in conversion_agent.tools]
        expected_tools = ['funnel_analysis', 'conversion_rate_analysis', 'bottleneck_identification', 'conversion_path_analysis']
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    def test_funnel_analysis(self, conversion_agent):
        """测试漏斗分析功能"""
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
        
        result = conversion_agent.analyze_funnel(
            funnel_steps=funnel_steps,
            funnel_name="test_funnel",
            time_window_hours=24
        )
        
        # 验证结果结构
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'funnel_analysis'
        assert 'funnel' in result
        assert 'summary' in result
        assert 'insights' in result
        
        # 验证漏斗数据
        funnel = result['funnel']
        assert funnel['funnel_name'] == 'test_funnel'
        assert 'overall_conversion_rate' in funnel
        assert 'total_users_entered' in funnel
        assert 'total_users_converted' in funnel
        assert 'steps' in funnel
        
        # 验证步骤数据
        steps = funnel['steps']
        assert len(steps) == len(funnel_steps)
        
        for i, step in enumerate(steps):
            assert step['step_name'] == funnel_steps[i]
            assert step['step_order'] == i
            assert 'total_users' in step
            assert 'conversion_rate' in step
            assert 'drop_off_rate' in step
    
    def test_conversion_rate_analysis(self, conversion_agent):
        """测试转化率分析功能"""
        funnel_definitions = {
            'purchase_funnel': ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase'],
            'engagement_funnel': ['page_view', 'view_item']
        }
        
        result = conversion_agent.analyze_conversion_rates(funnel_definitions)
        
        # 验证结果结构
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'conversion_rate_analysis'
        assert 'results' in result
        assert 'summary' in result
        assert 'insights' in result
        
        # 验证分析结果
        results = result['results']
        assert 'funnels' in results
        assert 'conversion_metrics' in results
        assert 'bottleneck_analysis' in results
        
        # 验证漏斗数据
        funnels = results['funnels']
        assert len(funnels) >= 1  # 至少有一个有效漏斗
        
        for funnel in funnels:
            assert 'funnel_name' in funnel
            assert 'overall_conversion_rate' in funnel
            assert 'steps' in funnel
    
    def test_bottleneck_identification(self, conversion_agent):
        """测试瓶颈识别功能"""
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
        
        result = conversion_agent.identify_bottlenecks(funnel_steps)
        
        # 验证结果结构
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'bottleneck_identification'
        assert 'drop_off_analysis' in result
        assert 'summary' in result
        assert 'insights' in result
        assert 'recommendations' in result
        
        # 验证分析结果
        drop_off_analysis = result['drop_off_analysis']
        assert 'funnel_steps' in drop_off_analysis
        assert 'major_drop_off_points' in drop_off_analysis
        assert 'drop_off_insights' in drop_off_analysis
        
        # 验证建议
        recommendations = result['recommendations']
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_conversion_path_analysis(self, conversion_agent):
        """测试转化路径分析功能"""
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'purchase']
        
        result = conversion_agent.analyze_conversion_paths(
            funnel_steps=funnel_steps,
            time_window_hours=24
        )
        
        # 验证结果结构
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'conversion_path_analysis'
        assert 'path_analysis' in result
        assert 'insights' in result
        
        # 验证路径分析
        path_analysis = result['path_analysis']
        assert 'optimal_path' in path_analysis
        assert 'path_variations' in path_analysis
        assert 'common_exit_points' in path_analysis
    
    def test_comprehensive_conversion_analysis(self, conversion_agent):
        """测试综合转化分析功能"""
        result = conversion_agent.comprehensive_conversion_analysis()
        
        # 验证结果结构
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'comprehensive_conversion_analysis'
        assert 'conversion_rates_analysis' in result
        assert 'funnel_analyses' in result
        assert 'bottleneck_analyses' in result
        assert 'summary' in result
        
        # 验证各项分析结果
        assert result['conversion_rates_analysis']['status'] == 'success'
        
        funnel_analyses = result['funnel_analyses']
        assert len(funnel_analyses) >= 1
        
        bottleneck_analyses = result['bottleneck_analyses']
        assert len(bottleneck_analyses) >= 1
    
    def test_error_handling_no_data(self, conversion_agent):
        """测试无数据情况的错误处理"""
        # 模拟空数据
        conversion_agent.storage_manager.get_data.return_value = pd.DataFrame()
        
        result = conversion_agent.analyze_funnel(['page_view', 'purchase'])
        
        # 应该返回成功但数据为空的结果
        assert result['status'] == 'success'
        assert result['funnel']['total_users_entered'] == 0
        assert result['funnel']['overall_conversion_rate'] == 0.0
    
    def test_error_handling_invalid_steps(self, conversion_agent):
        """测试无效步骤的错误处理"""
        # 测试空步骤列表
        with pytest.raises(Exception):
            conversion_agent.analyze_funnel([])
    
    def test_custom_funnel_definitions(self, conversion_agent):
        """测试自定义漏斗定义"""
        custom_funnels = {
            'simple_funnel': ['page_view', 'purchase'],
            'complex_funnel': ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
        }
        
        result = conversion_agent.analyze_conversion_rates(custom_funnels)
        
        assert result['status'] == 'success'
        
        # 验证使用了自定义漏斗
        funnels = result['results']['funnels']
        funnel_names = [f['funnel_name'] for f in funnels]
        
        for custom_name in custom_funnels.keys():
            # 至少有一个自定义漏斗被成功分析
            assert any(custom_name in name for name in funnel_names)


class TestFunnelAnalysisTool:
    """漏斗分析工具测试类"""
    
    @pytest.fixture
    def sample_events_data(self):
        """创建示例事件数据"""
        events = []
        base_time = datetime.now()
        
        # 创建简单的转化路径数据
        for i in range(10):
            user_id = f"user_{i}"
            current_time = base_time + timedelta(minutes=i*10)
            
            # 每个用户都有page_view
            events.append({
                'user_pseudo_id': user_id,
                'event_name': 'page_view',
                'event_datetime': current_time,
                'event_timestamp': int(current_time.timestamp() * 1000000)
            })
            
            # 一半用户有purchase
            if i < 5:
                events.append({
                    'user_pseudo_id': user_id,
                    'event_name': 'purchase',
                    'event_datetime': current_time + timedelta(minutes=5),
                    'event_timestamp': int((current_time + timedelta(minutes=5)).timestamp() * 1000000)
                })
        
        return pd.DataFrame(events)
    
    @pytest.fixture
    def mock_storage_manager(self, sample_events_data):
        """创建模拟存储管理器"""
        storage_manager = Mock(spec=DataStorageManager)
        storage_manager.get_data.return_value = sample_events_data
        return storage_manager
    
    @pytest.fixture
    def funnel_tool(self, mock_storage_manager):
        """创建漏斗分析工具实例"""
        return FunnelAnalysisTool(mock_storage_manager)
    
    def test_funnel_tool_basic_analysis(self, funnel_tool):
        """测试漏斗工具基本分析功能"""
        result = funnel_tool._run(
            funnel_steps=['page_view', 'purchase'],
            funnel_name='test_funnel'
        )
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'funnel_analysis'
        
        funnel = result['funnel']
        assert funnel['funnel_name'] == 'test_funnel'
        assert funnel['total_users_entered'] == 10
        assert funnel['total_users_converted'] == 5
        assert funnel['overall_conversion_rate'] == 0.5
    
    def test_funnel_tool_insights_generation(self, funnel_tool):
        """测试漏斗工具洞察生成"""
        result = funnel_tool._run(
            funnel_steps=['page_view', 'purchase'],
            funnel_name='test_funnel'
        )
        
        insights = result['insights']
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # 检查是否包含转化率相关洞察
        insight_text = ' '.join(insights)
        assert '转化率' in insight_text or 'conversion' in insight_text.lower()


class TestConversionRateAnalysisTool:
    """转化率分析工具测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟转化分析引擎"""
        engine = Mock()
        
        # 模拟转化分析结果
        mock_result = Mock()
        mock_result.funnels = []
        mock_result.conversion_metrics = {'overall_conversion_rate': 0.15}
        mock_result.bottleneck_analysis = {'common_bottlenecks': []}
        mock_result.time_analysis = {}
        mock_result.segment_analysis = {}
        
        engine.calculate_conversion_rates.return_value = mock_result
        return engine
    
    @pytest.fixture
    def conversion_tool(self, mock_engine):
        """创建转化率分析工具实例"""
        tool = ConversionRateAnalysisTool()
        tool.engine = mock_engine
        return tool
    
    def test_conversion_rate_tool_basic_analysis(self, conversion_tool):
        """测试转化率工具基本分析功能"""
        result = conversion_tool._run()
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'conversion_rate_analysis'
        assert 'results' in result
        assert 'summary' in result
        assert 'insights' in result


class TestBottleneckIdentificationTool:
    """瓶颈识别工具测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟转化分析引擎"""
        engine = Mock()
        
        # 模拟流失点分析结果
        mock_analysis = {
            'funnel_steps': [
                {'step_name': 'page_view', 'drop_off_rate': 0.0, 'users_lost': 0},
                {'step_name': 'purchase', 'drop_off_rate': 0.5, 'users_lost': 50}
            ],
            'major_drop_off_points': [
                {'step_name': 'purchase', 'drop_off_rate': 0.5}
            ],
            'drop_off_insights': ['购买步骤流失率较高']
        }
        
        engine.identify_drop_off_points.return_value = mock_analysis
        return engine
    
    @pytest.fixture
    def bottleneck_tool(self, mock_engine):
        """创建瓶颈识别工具实例"""
        tool = BottleneckIdentificationTool()
        tool.engine = mock_engine
        return tool
    
    def test_bottleneck_tool_basic_analysis(self, bottleneck_tool):
        """测试瓶颈识别工具基本分析功能"""
        result = bottleneck_tool._run(['page_view', 'purchase'])
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'bottleneck_identification'
        assert 'drop_off_analysis' in result
        assert 'recommendations' in result
        
        # 验证建议生成
        recommendations = result['recommendations']
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0


class TestConversionPathAnalysisTool:
    """转化路径分析工具测试类"""
    
    @pytest.fixture
    def mock_engine(self):
        """创建模拟转化分析引擎"""
        engine = Mock()
        
        # 模拟漏斗结果
        mock_funnel = Mock()
        mock_funnel.steps = [Mock(step_name='page_view'), Mock(step_name='purchase')]
        mock_funnel.overall_conversion_rate = 0.3
        mock_funnel.avg_completion_time = 1800  # 30分钟
        mock_funnel.bottleneck_step = 'purchase'
        
        engine.build_conversion_funnel.return_value = mock_funnel
        return engine
    
    @pytest.fixture
    def path_tool(self, mock_engine):
        """创建转化路径分析工具实例"""
        tool = ConversionPathAnalysisTool()
        tool.engine = mock_engine
        return tool
    
    def test_path_tool_basic_analysis(self, path_tool):
        """测试转化路径分析工具基本分析功能"""
        result = path_tool._run(['page_view', 'purchase'])
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'conversion_path_analysis'
        assert 'path_analysis' in result
        assert 'insights' in result
        
        # 验证路径分析结构
        path_analysis = result['path_analysis']
        assert 'optimal_path' in path_analysis
        assert 'path_variations' in path_analysis
        assert 'common_exit_points' in path_analysis


if __name__ == '__main__':
    pytest.main([__file__, '-v'])