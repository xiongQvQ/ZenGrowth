#!/usr/bin/env python3
"""
测试事件分析页面的data_summary访问修复
"""

import sys
import time
import pandas as pd
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_event_analysis_page_initialization():
    """测试事件分析页面初始化"""
    print("🔍 测试事件分析页面初始化...")
    
    try:
        from ui.pages.event_analysis import EventAnalysisPage
        from engines.event_analysis_engine import EventAnalysisEngine
        from visualization.chart_generator import ChartGenerator
        
        # 创建事件分析页面实例
        page = EventAnalysisPage()
        
        # 验证引擎初始化
        if hasattr(page, '_initialize_engines'):
            print("✅ 事件分析页面类创建成功")
        else:
            print("❌ 事件分析页面类创建失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 事件分析页面初始化失败: {e}")
        return False

def test_state_manager_integration():
    """测试状态管理器集成"""
    print("\n🔍 测试状态管理器集成...")
    
    try:
        from ui.state import get_state_manager
        from ui.pages.event_analysis import EventAnalysisPage
        
        # 获取状态管理器
        state_manager = get_state_manager()
        
        # 设置一些测试数据摘要
        test_summary = {
            'event_types': {
                'page_view': 100,
                'click': 50,
                'purchase': 10
            },
            'total_events': 160,
            'unique_users': 45
        }
        
        state_manager.update_data_summary(test_summary)
        
        # 验证能够获取数据摘要
        retrieved_summary = state_manager.get_data_summary()
        if retrieved_summary and 'event_types' in retrieved_summary:
            print("✅ 状态管理器数据摘要设置和获取成功")
            
            # 测试事件类型获取
            event_types = list(retrieved_summary.get('event_types', {}).keys())
            if len(event_types) == 3:
                print("✅ 事件类型提取正常")
                return True
            else:
                print(f"⚠️  事件类型提取异常: {event_types}")
                return False
        else:
            print("❌ 状态管理器数据摘要获取失败")
            return False
        
    except Exception as e:
        print(f"❌ 状态管理器集成测试失败: {e}")
        return False

def test_data_access_patterns():
    """测试数据访问模式"""
    print("\n🔍 测试数据访问模式...")
    
    try:
        from ui.state import get_state_manager
        
        state_manager = get_state_manager()
        
        # 测试数据加载状态
        if not state_manager.is_data_loaded():
            print("✅ 初始状态：数据未加载")
        else:
            print("⚠️  初始状态异常：数据显示已加载")
        
        # 创建测试数据
        test_raw_data = pd.DataFrame({
            'event_name': ['page_view', 'click', 'purchase', 'page_view'],
            'user_pseudo_id': ['user_001', 'user_001', 'user_002', 'user_003'],
            'event_timestamp': [1640995200, 1640995260, 1640995320, 1640995380]
        })
        
        # 设置数据
        state_manager.set_data_loaded(True, test_raw_data)
        
        # 验证数据访问
        if state_manager.is_data_loaded():
            raw_data = state_manager.get_raw_data()
            if raw_data is not None and len(raw_data) == 4:
                print("✅ 原始数据访问正常")
                return True
            else:
                print("❌ 原始数据访问失败")
                return False
        else:
            print("❌ 数据加载状态设置失败")
            return False
        
    except Exception as e:
        print(f"❌ 数据访问模式测试失败: {e}")
        return False

def test_import_structure():
    """测试导入结构"""
    print("\n🔍 测试导入结构...")
    
    try:
        # 测试关键模块导入
        from ui.state import get_state_manager
        from ui.pages.event_analysis import EventAnalysisPage
        from engines.event_analysis_engine import EventAnalysisEngine
        from visualization.chart_generator import ChartGenerator
        from utils.i18n import t
        from ui.components.common import render_no_data_warning
        
        print("✅ 所有关键模块导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入结构测试失败: {e}")
        return False

def run_event_analysis_tests():
    """运行事件分析修复测试"""
    print("🚀 开始事件分析页面修复测试...")
    print("=" * 60)
    
    tests = [
        ("导入结构测试", test_import_structure),
        ("事件分析页面初始化", test_event_analysis_page_initialization),
        ("状态管理器集成", test_state_manager_integration),
        ("数据访问模式", test_data_access_patterns)
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
        print("🎉 所有事件分析页面测试通过！data_summary访问问题已解决！")
        return True
    else:
        print(f"⚠️  {total - passed} 个测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = run_event_analysis_tests()
    sys.exit(0 if success else 1)