#!/usr/bin/env python3
"""
测试filtered_data错误修复
验证事件分析页面的防御性检查
"""

import sys
import time
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch
import streamlit as st

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_defensive_checks_implementation():
    """测试防御性检查实现"""
    print("🔍 测试防御性检查实现...")
    
    try:
        from ui.pages.event_analysis import EventAnalysisPage
        
        # 创建事件分析页面实例
        page = EventAnalysisPage()
        
        # 检查关键方法是否存在
        methods_to_check = [
            '_render_key_metrics',
            '_render_timeline_chart', 
            '_render_distribution_charts',
            '_render_detailed_data',
            '_render_analysis_results'
        ]
        
        for method_name in methods_to_check:
            if hasattr(page, method_name):
                print(f"✅ 方法 {method_name} 存在")
            else:
                print(f"❌ 方法 {method_name} 缺失")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 防御性检查实现测试失败: {e}")
        return False

def test_missing_filtered_data_handling():
    """测试缺失filtered_data的处理"""
    print("\n🔍 测试缺失filtered_data处理...")
    
    try:
        from ui.pages.event_analysis import EventAnalysisPage
        from unittest.mock import MagicMock
        
        # 创建模拟的streamlit组件
        with patch('streamlit.error') as mock_error, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.subheader') as mock_subheader:
            
            # 创建页面实例
            page = EventAnalysisPage()
            
            # 测试空结果字典
            empty_results = {}
            
            # 测试_render_key_metrics with empty results
            mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
            page._render_key_metrics(empty_results)
            
            # 验证是否调用了错误显示
            mock_error.assert_called_with("分析结果中缺少过滤数据，请重新执行分析")
            print("✅ _render_key_metrics 缺失数据处理正常")
            
            # 重置mock
            mock_error.reset_mock()
            
            # 测试_render_distribution_charts with empty results
            mock_columns.return_value = [MagicMock(), MagicMock()]
            page._render_distribution_charts(empty_results)
            
            # 验证是否调用了错误显示
            mock_error.assert_called_with("分析结果中缺少过滤数据，无法生成分布图表")
            print("✅ _render_distribution_charts 缺失数据处理正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 缺失filtered_data处理测试失败: {e}")
        return False

def test_valid_filtered_data_handling():
    """测试有效filtered_data的处理"""
    print("\n🔍 测试有效filtered_data处理...")
    
    try:
        from ui.pages.event_analysis import EventAnalysisPage
        from unittest.mock import MagicMock, patch
        
        # 创建测试数据
        test_filtered_data = pd.DataFrame({
            'event_name': ['page_view', 'click', 'purchase', 'page_view'],
            'user_pseudo_id': ['user_001', 'user_001', 'user_002', 'user_003'],
            'event_timestamp': [1640995200, 1640995260, 1640995320, 1640995380]
        })
        
        # 创建有效的结果字典
        valid_results = {
            'filtered_data': test_filtered_data,
            'frequency': {'page_view': 2, 'click': 1, 'purchase': 1},
            'trends': {'daily': [1, 2, 3]},
            'config': {}
        }
        
        with patch('streamlit.metric') as mock_metric, \
             patch('streamlit.columns') as mock_columns:
            
            # 创建页面实例
            page = EventAnalysisPage()
            
            # 模拟4个列
            mock_columns.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
            
            # 测试_render_key_metrics with valid data
            page._render_key_metrics(valid_results)
            
            # 验证是否调用了metric显示
            assert mock_metric.call_count >= 4, "应该显示4个关键指标"
            print("✅ _render_key_metrics 有效数据处理正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 有效filtered_data处理测试失败: {e}")
        return False

def test_analysis_results_structure_validation():
    """测试分析结果结构验证"""
    print("\n🔍 测试分析结果结构验证...")
    
    try:
        from ui.pages.event_analysis import EventAnalysisPage
        from unittest.mock import patch
        
        # 创建页面实例
        page = EventAnalysisPage()
        
        with patch('streamlit.session_state') as mock_session_state, \
             patch('streamlit.warning') as mock_warning, \
             patch('streamlit.error') as mock_error:
            
            # 测试1: 没有event_analysis_results
            mock_session_state.__contains__ = lambda key: False
            page._render_analysis_results()
            mock_warning.assert_called_with("没有找到分析结果，请先执行事件分析")
            print("✅ 缺失分析结果检查正常")
            
            # 重置mock
            mock_warning.reset_mock()
            mock_error.reset_mock()
            
            # 测试2: 有event_analysis_results但格式错误
            mock_session_state.__contains__ = lambda key: True
            mock_session_state.event_analysis_results = "invalid_format"
            mock_session_state.chart_generator = Mock()
            
            page._render_analysis_results()
            mock_error.assert_called_with("分析结果格式错误，请重新执行分析")
            print("✅ 错误格式检查正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析结果结构验证测试失败: {e}")
        return False

def test_integration_with_state_manager():
    """测试与状态管理器的集成"""
    print("\n🔍 测试与状态管理器集成...")
    
    try:
        from ui.pages.event_analysis import EventAnalysisPage
        from ui.state import get_state_manager
        
        # 获取状态管理器
        state_manager = get_state_manager()
        
        # 设置测试数据
        test_data = pd.DataFrame({
            'event_name': ['page_view', 'click'],
            'user_pseudo_id': ['user_001', 'user_002'],
            'event_timestamp': [1640995200, 1640995260]
        })
        
        # 设置数据摘要
        test_summary = {
            'event_types': {
                'page_view': 1,
                'click': 1
            },
            'total_events': 2,
            'unique_users': 2
        }
        
        state_manager.set_data_loaded(True, test_data)
        state_manager.update_data_summary(test_summary)
        
        # 创建页面实例
        page = EventAnalysisPage()
        
        # 验证数据访问
        if state_manager.is_data_loaded():
            raw_data = state_manager.get_raw_data()
            if raw_data is not None and len(raw_data) == 2:
                print("✅ 状态管理器集成正常")
                return True
            else:
                print("❌ 数据访问失败")
                return False
        else:
            print("❌ 数据加载状态错误")
            return False
        
    except Exception as e:
        print(f"❌ 状态管理器集成测试失败: {e}")
        return False

def run_filtered_data_fix_tests():
    """运行filtered_data修复测试"""
    print("🚀 开始filtered_data错误修复测试...")
    print("=" * 60)
    
    tests = [
        ("防御性检查实现", test_defensive_checks_implementation),
        ("缺失filtered_data处理", test_missing_filtered_data_handling),
        ("有效filtered_data处理", test_valid_filtered_data_handling),
        ("分析结果结构验证", test_analysis_results_structure_validation),
        ("状态管理器集成", test_integration_with_state_manager)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 执行测试: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - 测试通过")
            else:
                print(f"❌ {test_name} - 测试失败")
        except Exception as e:
            print(f"❌ {test_name} - 测试异常: {e}")
        
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有filtered_data修复测试通过！Analysis Results页面错误已解决！")
        return True
    else:
        print(f"⚠️  {total - passed} 个测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = run_filtered_data_fix_tests()
    sys.exit(0 if success else 1)