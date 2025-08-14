#!/usr/bin/env python3
"""
测试重构后的应用基本功能
"""

import requests
import time
import sys
from pathlib import Path

def test_app_health():
    """测试应用健康状态"""
    print("🔍 测试应用健康状态...")
    
    try:
        # 测试主页
        response = requests.get("http://localhost:8502", timeout=10)
        if response.status_code == 200:
            print("✅ 应用主页响应正常 (HTTP 200)")
            return True
        else:
            print(f"❌ 应用主页响应异常 (HTTP {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_healthcheck_endpoint():
    """测试健康检查端点"""
    print("🔍 测试健康检查端点...")
    
    try:
        # 尝试访问健康检查端点
        response = requests.get("http://localhost:8502/health", timeout=10)
        if response.status_code == 200:
            print("✅ 健康检查端点响应正常")
            return True
        else:
            print(f"⚠️  健康检查端点未配置或响应异常 (HTTP {response.status_code})")
            return False
    except requests.exceptions.RequestException:
        print("⚠️  健康检查端点未配置或不可访问")
        return False

def test_module_imports():
    """测试模块导入"""
    print("🔍 测试模块化架构导入...")
    
    try:
        # 测试核心模块
        from ui.state import get_state_manager
        from ui.layouts.sidebar import render_sidebar
        from ui.layouts.main_layout import render_main_layout
        from ui.pages.data_upload import show_data_upload_page
        from ui.pages.intelligent_analysis import show_intelligent_analysis_page
        from ui.components.common import render_no_data_warning
        from ui.components.config_panel import ConfigPanel
        from ui.components.results_display import MetricsCard
        
        print("✅ 所有核心模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 模块导入异常: {e}")
        return False

def test_state_manager():
    """测试状态管理器功能"""
    print("🔍 测试状态管理器功能...")
    
    try:
        from ui.state import get_state_manager
        
        # 创建状态管理器实例
        state_manager = get_state_manager()
        
        # 测试基本方法
        _ = state_manager.is_data_loaded()
        _ = state_manager.get_current_page()
        _ = state_manager.is_initialized()
        
        print("✅ 状态管理器功能正常")
        return True
    except Exception as e:
        print(f"❌ 状态管理器测试失败: {e}")
        return False

def run_tests():
    """运行所有测试"""
    print("🚀 开始测试重构后的应用...")
    print("=" * 50)
    
    tests = [
        ("应用健康状态", test_app_health),
        ("健康检查端点", test_healthcheck_endpoint),
        ("模块导入", test_module_imports),
        ("状态管理器", test_state_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 测试: {test_name}")
        if test_func():
            passed += 1
        time.sleep(0.5)  # 短暂延迟
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！模块化重构成功！")
        return True
    else:
        print(f"⚠️  {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)