"""
事件分析智能体测试模块

测试EventAnalysisAgent的功能，包括事件频次分析、趋势分析、关联性分析和关键事件识别。
"""

import pytest
import pandas as pd
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from agents.event_analysis_agent import (
    EventAnalysisAgent,
    EventFrequencyAnalysisTool,
    EventTrendAnalysisTool,
    EventCorrelationAnalysisTool,
    KeyEventIdentificationTool
)
from tools.data_storage_manager import DataStorageManager


class TestEventFrequencyAnalysisTool:
    """测试事件频次分析工具"""
    
    def setup_method(self):
        """测试前准备"""
        self.storage_manager = DataStorageManager()
        self.tool = EventFrequencyAnalysisTool(self.storage_manager)
        
    def create_test_events_data(self):
        """创建测试事件数据"""
        base_time = datetime(2024, 1, 1)
        events_data = []
        
        # 创建不同用户的不同事件
        for user_id in ['user1', 'user2', 'user3']:
            for i in range(5):  # 每个用户5个page_view事件
                events_data.append({
                    'user_pseudo_id': user_id,
                    'event_name': 'page_view',
                    'event_timestamp': int((base_time + timedelta(hours=i)).timestamp() * 1000000),
                    'event_datetime': base_time + timedelta(hours=i),
                    'event_date': '20240101'
                })
                
            # 每个用户1个purchase事件
            events_data.append({
                'user_pseudo_id': user_id,
                'event_name': 'purchase',
                'event_timestamp': int((base_time + timedelta(hours=6)).timestamp() * 1000000),
                'event_datetime': base_time + timedelta(hours=6),
                'event_date': '20240101'
            })
            
        return pd.DataFrame(events_data)
        
    def test_frequency_analysis_success(self):
        """测试成功的频次分析"""
        # 准备测试数据
        test_data = self.create_test_events_data()
        self.storage_manager.store_events(test_data)
        
        # 执行分析
        result = self.tool._run()
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'event_frequency'
        assert 'results' in result
        assert 'summary' in result
        assert 'insights' in result
        
        # 验证具体结果
        results = result['results']
        assert 'page_view' in results
        assert 'purchase' in results
        
        page_view_result = results['page_view']
        assert page_view_result['total_count'] == 15  # 3用户 * 5事件
        assert page_view_result['unique_users'] == 3
        assert page_view_result['avg_per_user'] == 5.0
        
        purchase_result = results['purchase']
        assert purchase_result['total_count'] == 3  # 3用户 * 1事件
        assert purchase_result['unique_users'] == 3
        assert purchase_result['avg_per_user'] == 1.0
        
    def test_frequency_analysis_with_filters(self):
        """测试带过滤条件的频次分析"""
        # 准备测试数据
        test_data = self.create_test_events_data()
        self.storage_manager.store_events(test_data)
        
        # 执行分析（只分析page_view事件）
        result = self.tool._run(event_types=['page_view'])
        
        # 验证结果
        assert result['status'] == 'success'
        results = result['results']
        assert 'page_view' in results
        assert 'purchase' not in results
        
    def test_frequency_analysis_empty_data(self):
        """测试空数据的频次分析"""
        # 不存储任何数据
        result = self.tool._run()
        
        # 应该返回成功但结果为空
        assert result['status'] == 'success'
        assert result['results'] == {}


class TestEventTrendAnalysisTool:
    """测试事件趋势分析工具"""
    
    def setup_method(self):
        """测试前准备"""
        self.storage_manager = DataStorageManager()
        self.tool = EventTrendAnalysisTool(self.storage_manager)
        
    def create_test_trend_data(self):
        """创建测试趋势数据"""
        base_time = datetime(2024, 1, 1)
        events_data = []
        
        # 创建7天的数据，每天递增的事件数量
        for day in range(7):
            current_date = base_time + timedelta(days=day)
            event_count = (day + 1) * 2  # 递增的事件数量
            
            for i in range(event_count):
                events_data.append({
                    'user_pseudo_id': f'user{i % 3}',  # 3个用户循环
                    'event_name': 'page_view',
                    'event_timestamp': int((current_date + timedelta(hours=i)).timestamp() * 1000000),
                    'event_datetime': current_date + timedelta(hours=i),
                    'event_date': current_date.strftime('%Y%m%d')
                })
                
        return pd.DataFrame(events_data)
        
    def test_trend_analysis_success(self):
        """测试成功的趋势分析"""
        # 准备测试数据
        test_data = self.create_test_trend_data()
        self.storage_manager.store_events(test_data)
        
        # 执行分析
        result = self.tool._run()
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'event_trend'
        assert 'results' in result
        assert 'summary' in result
        assert 'insights' in result
        
        # 验证具体结果
        results = result['results']
        assert 'page_view' in results
        
        trend_result = results['page_view']
        assert trend_result['event_name'] == 'page_view'
        assert trend_result['trend_direction'] in ['increasing', 'decreasing', 'stable']
        assert 'growth_rate' in trend_result
        assert 'trend_data' in trend_result
        
    def test_trend_analysis_different_granularity(self):
        """测试不同时间粒度的趋势分析"""
        # 准备测试数据
        test_data = self.create_test_trend_data()
        self.storage_manager.store_events(test_data)
        
        # 测试周粒度
        result = self.tool._run(time_granularity='weekly')
        assert result['status'] == 'success'
        
        # 测试月粒度
        result = self.tool._run(time_granularity='monthly')
        assert result['status'] == 'success'


class TestEventCorrelationAnalysisTool:
    """测试事件关联性分析工具"""
    
    def setup_method(self):
        """测试前准备"""
        self.storage_manager = DataStorageManager()
        self.tool = EventCorrelationAnalysisTool(self.storage_manager)
        
    def create_test_correlation_data(self):
        """创建测试关联性数据"""
        base_time = datetime(2024, 1, 1)
        events_data = []
        
        # 创建有关联性的事件数据
        for user_id in [f'user{i}' for i in range(20)]:  # 20个用户
            # 每个用户都有page_view事件
            events_data.append({
                'user_pseudo_id': user_id,
                'event_name': 'page_view',
                'event_timestamp': int(base_time.timestamp() * 1000000),
                'event_datetime': base_time,
                'event_date': '20240101'
            })
            
            # 80%的用户在page_view后有view_item事件
            if int(user_id.replace('user', '')) < 16:
                events_data.append({
                    'user_pseudo_id': user_id,
                    'event_name': 'view_item',
                    'event_timestamp': int((base_time + timedelta(minutes=5)).timestamp() * 1000000),
                    'event_datetime': base_time + timedelta(minutes=5),
                    'event_date': '20240101'
                })
                
            # 50%的用户有purchase事件
            if int(user_id.replace('user', '')) < 10:
                events_data.append({
                    'user_pseudo_id': user_id,
                    'event_name': 'purchase',
                    'event_timestamp': int((base_time + timedelta(minutes=10)).timestamp() * 1000000),
                    'event_datetime': base_time + timedelta(minutes=10),
                    'event_date': '20240101'
                })
                
        return pd.DataFrame(events_data)
        
    def test_correlation_analysis_success(self):
        """测试成功的关联性分析"""
        # 准备测试数据
        test_data = self.create_test_correlation_data()
        self.storage_manager.store_events(test_data)
        
        # 执行分析
        result = self.tool._run(min_co_occurrence=5)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'event_correlation'
        assert 'results' in result
        assert 'summary' in result
        assert 'insights' in result
        
        # 验证具体结果
        results = result['results']
        assert len(results) > 0  # 应该有关联性结果
        
        # 检查结果结构
        for correlation in results:
            assert 'event_pair' in correlation
            assert 'correlation_coefficient' in correlation
            assert 'significance_level' in correlation
            assert 'co_occurrence_rate' in correlation
            
    def test_correlation_analysis_insufficient_data(self):
        """测试数据不足的关联性分析"""
        # 创建很少的数据
        test_data = pd.DataFrame([
            {
                'user_pseudo_id': 'user1',
                'event_name': 'page_view',
                'event_timestamp': int(datetime.now().timestamp() * 1000000),
                'event_datetime': datetime.now(),
                'event_date': '20240101'
            }
        ])
        self.storage_manager.store_events(test_data)
        
        # 执行分析
        result = self.tool._run(min_co_occurrence=10)
        
        # 应该返回成功但结果为空
        assert result['status'] == 'success'
        assert result['results'] == []


class TestKeyEventIdentificationTool:
    """测试关键事件识别工具"""
    
    def setup_method(self):
        """测试前准备"""
        self.storage_manager = DataStorageManager()
        self.tool = KeyEventIdentificationTool(self.storage_manager)
        
    def create_test_key_event_data(self):
        """创建测试关键事件数据"""
        base_time = datetime(2024, 1, 1)
        events_data = []
        
        # 创建不同重要性的事件
        event_types = ['page_view', 'view_item', 'add_to_cart', 'purchase', 'sign_up']
        user_counts = [50, 30, 20, 10, 15]  # 不同事件的用户数量
        
        for i, (event_type, user_count) in enumerate(zip(event_types, user_counts)):
            for user_id in range(user_count):
                events_data.append({
                    'user_pseudo_id': f'user{user_id}',
                    'event_name': event_type,
                    'event_timestamp': int((base_time + timedelta(hours=i)).timestamp() * 1000000),
                    'event_datetime': base_time + timedelta(hours=i),
                    'event_date': '20240101'
                })
                
        return pd.DataFrame(events_data)
        
    @patch('engines.event_analysis_engine.EventAnalysisEngine.identify_key_events')
    def test_key_event_identification_success(self, mock_identify):
        """测试成功的关键事件识别"""
        # 模拟引擎返回结果
        from engines.event_analysis_engine import KeyEventResult
        mock_results = [
            KeyEventResult(
                event_name='purchase',
                importance_score=95.0,
                user_engagement_impact=80.0,
                conversion_impact=100.0,
                retention_impact=90.0,
                reasons=['高转化价值', '强用户留存影响']
            ),
            KeyEventResult(
                event_name='sign_up',
                importance_score=85.0,
                user_engagement_impact=70.0,
                conversion_impact=90.0,
                retention_impact=80.0,
                reasons=['关键转化节点', '用户获取指标']
            )
        ]
        mock_identify.return_value = mock_results
        
        # 执行分析
        result = self.tool._run(top_k=5)
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'key_event_identification'
        assert 'results' in result
        assert 'summary' in result
        assert 'insights' in result
        
        # 验证具体结果
        results = result['results']
        assert len(results) == 2
        
        # 检查第一个结果
        first_result = results[0]
        assert first_result['event_name'] == 'purchase'
        assert first_result['importance_score'] == 95.0
        assert 'reasons' in first_result


class TestEventAnalysisAgent:
    """测试事件分析智能体"""
    
    def setup_method(self):
        """测试前准备"""
        self.storage_manager = DataStorageManager()
        self.agent = EventAnalysisAgent(self.storage_manager)
        
    def test_agent_initialization(self):
        """测试智能体初始化"""
        assert self.agent.agent is not None
        assert len(self.agent.tools) == 4
        assert self.agent.agent.role == "事件分析专家"
        
    def test_get_agent(self):
        """测试获取智能体实例"""
        agent = self.agent.get_agent()
        assert agent is not None
        assert agent.role == "事件分析专家"
        
    def test_get_tools(self):
        """测试获取工具列表"""
        tools = self.agent.get_tools()
        assert len(tools) == 4
        
        tool_names = [tool.name for tool in tools]
        assert "event_frequency_analysis" in tool_names
        assert "event_trend_analysis" in tool_names
        assert "event_correlation_analysis" in tool_names
        assert "key_event_identification" in tool_names
        
    @patch.object(EventFrequencyAnalysisTool, '_run')
    def test_analyze_event_frequency(self, mock_run):
        """测试事件频次分析方法"""
        # 模拟工具返回结果
        mock_run.return_value = {
            'status': 'success',
            'analysis_type': 'event_frequency',
            'results': {},
            'summary': {},
            'insights': []
        }
        
        result = self.agent.analyze_event_frequency(['page_view'])
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'event_frequency'
        mock_run.assert_called_once_with(['page_view'], None)
        
    @patch.object(EventTrendAnalysisTool, '_run')
    def test_analyze_event_trends(self, mock_run):
        """测试事件趋势分析方法"""
        # 模拟工具返回结果
        mock_run.return_value = {
            'status': 'success',
            'analysis_type': 'event_trend',
            'results': {},
            'summary': {},
            'insights': []
        }
        
        result = self.agent.analyze_event_trends(['page_view'], 'daily')
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'event_trend'
        mock_run.assert_called_once_with(['page_view'], 'daily')
        
    @patch.object(EventCorrelationAnalysisTool, '_run')
    def test_analyze_event_correlations(self, mock_run):
        """测试事件关联性分析方法"""
        # 模拟工具返回结果
        mock_run.return_value = {
            'status': 'success',
            'analysis_type': 'event_correlation',
            'results': [],
            'summary': {},
            'insights': []
        }
        
        result = self.agent.analyze_event_correlations(['page_view', 'purchase'], 10)
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'event_correlation'
        mock_run.assert_called_once_with(['page_view', 'purchase'], 10)
        
    @patch.object(KeyEventIdentificationTool, '_run')
    def test_identify_key_events(self, mock_run):
        """测试关键事件识别方法"""
        # 模拟工具返回结果
        mock_run.return_value = {
            'status': 'success',
            'analysis_type': 'key_event_identification',
            'results': [],
            'summary': {},
            'insights': []
        }
        
        result = self.agent.identify_key_events(5)
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'key_event_identification'
        mock_run.assert_called_once_with(5)
        
    def test_comprehensive_event_analysis(self):
        """测试综合事件分析"""
        # 创建测试数据
        test_data = pd.DataFrame([
            {
                'user_pseudo_id': 'user1',
                'event_name': 'page_view',
                'event_timestamp': int(datetime.now().timestamp() * 1000000),
                'event_datetime': datetime.now(),
                'event_date': '20240101'
            }
        ])
        self.storage_manager.store_events(test_data)
        
        # 执行综合分析
        result = self.agent.comprehensive_event_analysis(['page_view'])
        
        # 验证结果
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'comprehensive_event_analysis'
        assert 'frequency_analysis' in result
        assert 'trend_analysis' in result
        assert 'correlation_analysis' in result
        assert 'key_event_analysis' in result
        assert 'summary' in result


if __name__ == '__main__':
    pytest.main([__file__])