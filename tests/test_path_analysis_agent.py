"""
路径分析智能体测试模块

测试PathAnalysisAgent类的各种功能，包括会话重构、路径挖掘和用户流程分析。
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.path_analysis_agent import PathAnalysisAgent, SessionReconstructionTool, PathMiningTool, UserFlowAnalysisTool
from engines.path_analysis_engine import UserSession, PathPattern, PathAnalysisResult
from tools.data_storage_manager import DataStorageManager


class TestPathAnalysisAgent:
    """路径分析智能体测试类"""
    
    @pytest.fixture
    def mock_storage_manager(self):
        """创建模拟存储管理器"""
        storage_manager = Mock(spec=DataStorageManager)
        
        # 创建测试事件数据
        test_events = pd.DataFrame({
            'user_pseudo_id': ['user1', 'user1', 'user1', 'user2', 'user2', 'user2'],
            'event_name': ['page_view', 'view_item', 'purchase', 'page_view', 'add_to_cart', 'page_view'],
            'event_timestamp': [
                1640995200000000,  # 2022-01-01 00:00:00
                1640995260000000,  # 2022-01-01 00:01:00
                1640995320000000,  # 2022-01-01 00:02:00
                1640995380000000,  # 2022-01-01 00:03:00
                1640995440000000,  # 2022-01-01 00:04:00
                1640995500000000,  # 2022-01-01 00:05:00
            ],
            'event_date': ['2022-01-01'] * 6
        })
        
        # 添加event_datetime列
        test_events['event_datetime'] = pd.to_datetime(test_events['event_timestamp'], unit='us')
        
        storage_manager.get_data.return_value = test_events
        return storage_manager
    
    @pytest.fixture
    def path_analysis_agent(self, mock_storage_manager):
        """创建路径分析智能体实例"""
        return PathAnalysisAgent(storage_manager=mock_storage_manager)
    
    @pytest.fixture
    def sample_sessions(self):
        """创建示例会话数据"""
        return [
            {
                'session_id': 'user1_1',
                'user_id': 'user1',
                'start_time': '2022-01-01T00:00:00',
                'end_time': '2022-01-01T00:02:00',
                'duration_seconds': 120,
                'page_views': 1,
                'conversions': 1,
                'path_sequence': ['page_view', 'view_item', 'purchase'],
                'event_count': 3
            },
            {
                'session_id': 'user2_1',
                'user_id': 'user2',
                'start_time': '2022-01-01T00:03:00',
                'end_time': '2022-01-01T00:05:00',
                'duration_seconds': 120,
                'page_views': 2,
                'conversions': 0,
                'path_sequence': ['page_view', 'add_to_cart', 'page_view'],
                'event_count': 3
            }
        ]
    
    def test_agent_initialization(self, mock_storage_manager):
        """测试智能体初始化"""
        agent = PathAnalysisAgent(storage_manager=mock_storage_manager)
        
        assert agent.storage_manager == mock_storage_manager
        assert len(agent.tools) == 3
        assert isinstance(agent.tools[0], SessionReconstructionTool)
        assert isinstance(agent.tools[1], PathMiningTool)
        assert isinstance(agent.tools[2], UserFlowAnalysisTool)
    
    def test_reconstruct_sessions_success(self, path_analysis_agent):
        """测试成功的会话重构"""
        result = path_analysis_agent.reconstruct_sessions()
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'session_reconstruction'
        assert 'sessions' in result
        assert 'session_statistics' in result
        assert 'insights' in result
        
        # 验证会话数据结构
        sessions = result['sessions']
        assert len(sessions) > 0
        
        session = sessions[0]
        assert 'session_id' in session
        assert 'user_id' in session
        assert 'path_sequence' in session
        assert 'duration_seconds' in session
    
    def test_reconstruct_sessions_with_parameters(self, path_analysis_agent):
        """测试带参数的会话重构"""
        result = path_analysis_agent.reconstruct_sessions(
            user_ids=['user1'],
            date_range=('2022-01-01', '2022-01-02'),
            session_timeout_minutes=60
        )
        
        assert result['status'] == 'success'
        assert 'sessions' in result
    
    def test_mine_path_patterns_success(self, path_analysis_agent, sample_sessions):
        """测试成功的路径模式挖掘"""
        result = path_analysis_agent.mine_path_patterns(
            sessions=sample_sessions,
            min_length=2,
            max_length=5,
            min_pattern_frequency=1
        )
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'path_mining'
        assert 'analysis_result' in result
        assert 'insights' in result
        
        # 验证分析结果结构
        analysis_result = result['analysis_result']
        assert 'total_sessions' in analysis_result
        assert 'common_patterns' in analysis_result
        assert 'conversion_paths' in analysis_result
        assert 'path_flow_graph' in analysis_result
    
    def test_analyze_user_flow_success(self, path_analysis_agent):
        """测试成功的用户流程分析"""
        # 创建模拟的分析结果
        mock_analysis_result = {
            'total_sessions': 2,
            'total_paths': 2,
            'avg_path_length': 3.0,
            'common_patterns': [
                {
                    'pattern_id': 'common_1',
                    'path_sequence': ['page_view', 'view_item'],
                    'frequency': 5,
                    'user_count': 3,
                    'avg_duration': 120.0,
                    'conversion_rate': 0.6,
                    'pattern_type': 'common'
                }
            ],
            'anomalous_patterns': [],
            'conversion_paths': [
                {
                    'pattern_id': 'conversion_1',
                    'path_sequence': ['page_view', 'view_item', 'purchase'],
                    'frequency': 2,
                    'user_count': 2,
                    'avg_duration': 180.0,
                    'conversion_rate': 1.0,
                    'pattern_type': 'conversion'
                }
            ],
            'exit_patterns': [],
            'path_flow_graph': {
                'nodes': [
                    {'id': 'page_view', 'label': 'page_view', 'size': 10, 'type': 'regular'}
                ],
                'edges': [
                    {'from': 'page_view', 'to': 'view_item', 'weight': 5, 'label': '5'}
                ]
            }
        }
        
        result = path_analysis_agent.analyze_user_flow(mock_analysis_result)
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'user_flow_analysis'
        assert 'ux_recommendations' in result
        assert 'flow_bottlenecks' in result
        assert 'flow_optimizations' in result
        assert 'insights' in result
    
    def test_comprehensive_path_analysis_success(self, path_analysis_agent):
        """测试成功的综合路径分析"""
        result = path_analysis_agent.comprehensive_path_analysis()
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'comprehensive_path_analysis'
        assert 'session_reconstruction' in result
        assert 'path_mining' in result
        assert 'user_flow_analysis' in result
        assert 'summary' in result
        
        # 验证摘要信息
        summary = result['summary']
        assert 'total_analyses_performed' in summary
        assert 'successful_analyses' in summary
        assert 'key_findings' in summary
    
    def test_comprehensive_path_analysis_with_parameters(self, path_analysis_agent):
        """测试带参数的综合路径分析"""
        result = path_analysis_agent.comprehensive_path_analysis(
            user_ids=['user1', 'user2'],
            date_range=('2022-01-01', '2022-01-02'),
            session_timeout_minutes=45,
            min_length=2,
            max_length=8,
            min_pattern_frequency=3
        )
        
        assert result['status'] == 'success'
        assert 'session_reconstruction' in result
        assert 'path_mining' in result
        assert 'user_flow_analysis' in result
    
    def test_error_handling_no_data(self, mock_storage_manager):
        """测试无数据时的错误处理"""
        # 设置存储管理器返回空数据
        mock_storage_manager.get_data.return_value = pd.DataFrame()
        
        agent = PathAnalysisAgent(storage_manager=mock_storage_manager)
        result = agent.reconstruct_sessions()
        
        assert result['status'] == 'error'
        assert 'error_message' in result
    
    def test_error_handling_invalid_sessions(self, path_analysis_agent):
        """测试无效会话数据的错误处理"""
        invalid_sessions = [
            {
                'session_id': 'invalid',
                # 缺少必要字段
            }
        ]
        
        result = path_analysis_agent.mine_path_patterns(sessions=invalid_sessions)
        
        # 应该能处理错误并返回错误状态
        assert result['status'] == 'error'
        assert 'error_message' in result
    
    def test_get_agent_method(self, path_analysis_agent):
        """测试获取智能体实例方法"""
        agent_instance = path_analysis_agent.get_agent()
        assert agent_instance is not None
    
    def test_get_tools_method(self, path_analysis_agent):
        """测试获取工具列表方法"""
        tools = path_analysis_agent.get_tools()
        assert len(tools) == 3
        assert all(hasattr(tool, 'name') for tool in tools)
        assert all(hasattr(tool, 'description') for tool in tools)


class TestSessionReconstructionTool:
    """会话重构工具测试类"""
    
    @pytest.fixture
    def mock_storage_manager(self):
        """创建模拟存储管理器"""
        storage_manager = Mock(spec=DataStorageManager)
        
        # 创建测试事件数据
        test_events = pd.DataFrame({
            'user_pseudo_id': ['user1', 'user1', 'user1'],
            'event_name': ['page_view', 'view_item', 'purchase'],
            'event_timestamp': [
                1640995200000000,  # 2022-01-01 00:00:00
                1640995260000000,  # 2022-01-01 00:01:00
                1640995320000000,  # 2022-01-01 00:02:00
            ],
            'event_date': ['2022-01-01'] * 3
        })
        
        test_events['event_datetime'] = pd.to_datetime(test_events['event_timestamp'], unit='us')
        storage_manager.get_data.return_value = test_events
        return storage_manager
    
    @pytest.fixture
    def session_tool(self, mock_storage_manager):
        """创建会话重构工具实例"""
        return SessionReconstructionTool(storage_manager=mock_storage_manager)
    
    def test_tool_initialization(self, mock_storage_manager):
        """测试工具初始化"""
        tool = SessionReconstructionTool(storage_manager=mock_storage_manager)
        
        assert tool.name == "session_reconstruction"
        assert "重构完整的用户会话" in tool.description
        assert tool.engine is not None
    
    def test_session_reconstruction_success(self, session_tool):
        """测试成功的会话重构"""
        result = session_tool._run()
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'session_reconstruction'
        assert 'sessions' in result
        assert 'session_statistics' in result
        assert 'insights' in result
        
        # 验证会话统计
        stats = result['session_statistics']
        assert 'total_sessions' in stats
        assert 'unique_users' in stats
        assert 'duration_stats' in stats
        assert 'conversion_stats' in stats
    
    def test_session_reconstruction_with_parameters(self, session_tool):
        """测试带参数的会话重构"""
        result = session_tool._run(
            user_ids=['user1'],
            date_range=('2022-01-01', '2022-01-02'),
            session_timeout_minutes=60
        )
        
        assert result['status'] == 'success'
        assert 'sessions' in result


class TestPathMiningTool:
    """路径挖掘工具测试类"""
    
    @pytest.fixture
    def mock_storage_manager(self):
        """创建模拟存储管理器"""
        return Mock(spec=DataStorageManager)
    
    @pytest.fixture
    def mining_tool(self, mock_storage_manager):
        """创建路径挖掘工具实例"""
        return PathMiningTool(storage_manager=mock_storage_manager)
    
    @pytest.fixture
    def sample_sessions(self):
        """创建示例会话数据"""
        return [
            {
                'session_id': 'user1_1',
                'user_id': 'user1',
                'start_time': '2022-01-01T00:00:00',
                'end_time': '2022-01-01T00:02:00',
                'duration_seconds': 120,
                'page_views': 1,
                'conversions': 1,
                'path_sequence': ['page_view', 'view_item', 'purchase'],
                'event_count': 3
            }
        ]
    
    def test_tool_initialization(self, mock_storage_manager):
        """测试工具初始化"""
        tool = PathMiningTool(storage_manager=mock_storage_manager)
        
        assert tool.name == "path_mining"
        assert "挖掘常见路径模式" in tool.description
        assert tool.engine is not None
    
    def test_path_mining_success(self, mining_tool, sample_sessions):
        """测试成功的路径挖掘"""
        result = mining_tool._run(
            sessions=sample_sessions,
            min_length=2,
            max_length=5,
            min_pattern_frequency=1
        )
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'path_mining'
        assert 'analysis_result' in result
        assert 'insights' in result


class TestUserFlowAnalysisTool:
    """用户流程分析工具测试类"""
    
    @pytest.fixture
    def mock_storage_manager(self):
        """创建模拟存储管理器"""
        return Mock(spec=DataStorageManager)
    
    @pytest.fixture
    def flow_tool(self, mock_storage_manager):
        """创建用户流程分析工具实例"""
        return UserFlowAnalysisTool(storage_manager=mock_storage_manager)
    
    def test_tool_initialization(self, mock_storage_manager):
        """测试工具初始化"""
        tool = UserFlowAnalysisTool(storage_manager=mock_storage_manager)
        
        assert tool.name == "user_flow_analysis"
        assert "分析用户行为流程" in tool.description
        assert tool.engine is not None
    
    def test_flow_analysis_success(self, flow_tool):
        """测试成功的流程分析"""
        # 创建模拟分析结果
        mock_analysis_result = {
            'total_sessions': 2,
            'total_paths': 2,
            'avg_path_length': 3.0,
            'common_patterns': [],
            'anomalous_patterns': [],
            'conversion_paths': [],
            'exit_patterns': [],
            'path_flow_graph': {'nodes': [], 'edges': []}
        }
        
        result = flow_tool._run(mock_analysis_result)
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'user_flow_analysis'
        assert 'ux_recommendations' in result
        assert 'flow_bottlenecks' in result
        assert 'flow_optimizations' in result
        assert 'insights' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])