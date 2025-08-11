"""
路径分析智能体独立版本测试

测试PathAnalysisAgent独立版本的基本功能
"""

import sys
import os
import pandas as pd
from datetime import datetime
from unittest.mock import Mock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from agents.path_analysis_agent_standalone import PathAnalysisAgent
from tools.data_storage_manager import DataStorageManager


def create_mock_storage_manager():
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


def test_agent_initialization():
    """测试智能体初始化"""
    print("测试智能体初始化...")
    
    storage_manager = create_mock_storage_manager()
    agent = PathAnalysisAgent(storage_manager=storage_manager)
    
    assert agent.storage_manager == storage_manager
    assert agent.engine is not None
    
    print("✓ 智能体初始化成功")


def test_session_reconstruction():
    """测试会话重构"""
    print("测试会话重构...")
    
    storage_manager = create_mock_storage_manager()
    agent = PathAnalysisAgent(storage_manager=storage_manager)
    
    result = agent.reconstruct_sessions()
    
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
    
    print(f"✓ 成功重构了{len(sessions)}个会话")


def test_path_mining():
    """测试路径挖掘"""
    print("测试路径挖掘...")
    
    storage_manager = create_mock_storage_manager()
    agent = PathAnalysisAgent(storage_manager=storage_manager)
    
    # 先重构会话
    session_result = agent.reconstruct_sessions()
    assert session_result['status'] == 'success'
    
    # 然后进行路径挖掘
    mining_result = agent.mine_path_patterns(
        sessions=session_result['sessions'],
        min_length=2,
        max_length=5,
        min_pattern_frequency=1
    )
    
    assert mining_result['status'] == 'success'
    assert mining_result['analysis_type'] == 'path_mining'
    assert 'analysis_result' in mining_result
    assert 'insights' in mining_result
    
    # 验证分析结果结构
    analysis_result = mining_result['analysis_result']
    assert 'total_sessions' in analysis_result
    assert 'common_patterns' in analysis_result
    assert 'conversion_paths' in analysis_result
    assert 'path_flow_graph' in analysis_result
    
    print("✓ 路径挖掘分析成功")


def test_user_flow_analysis():
    """测试用户流程分析"""
    print("测试用户流程分析...")
    
    storage_manager = create_mock_storage_manager()
    agent = PathAnalysisAgent(storage_manager=storage_manager)
    
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
    
    result = agent.analyze_user_flow(mock_analysis_result)
    
    assert result['status'] == 'success'
    assert result['analysis_type'] == 'user_flow_analysis'
    assert 'ux_recommendations' in result
    assert 'flow_bottlenecks' in result
    assert 'flow_optimizations' in result
    assert 'insights' in result
    
    print("✓ 用户流程分析成功")


def test_comprehensive_analysis():
    """测试综合路径分析"""
    print("测试综合路径分析...")
    
    storage_manager = create_mock_storage_manager()
    agent = PathAnalysisAgent(storage_manager=storage_manager)
    
    result = agent.comprehensive_path_analysis()
    
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
    
    print("✓ 综合路径分析成功")


def main():
    """运行所有测试"""
    print("开始路径分析智能体独立版本测试...\n")
    
    try:
        test_agent_initialization()
        test_session_reconstruction()
        test_path_mining()
        test_user_flow_analysis()
        test_comprehensive_analysis()
        
        print("\n🎉 所有测试通过！路径分析智能体独立版本工作正常。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)