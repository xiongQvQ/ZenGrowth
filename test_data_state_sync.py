#!/usr/bin/env python3
"""
测试数据上传后的状态同步功能
验证数据处理完成后状态是否正确更新
"""

import sys
import time
import pandas as pd
from pathlib import Path
from unittest.mock import Mock

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_state_manager_data_loading():
    """测试状态管理器的数据加载功能"""
    print("🔍 测试状态管理器数据加载功能...")
    
    try:
        from ui.state import get_state_manager
        
        # 获取状态管理器
        state_manager = get_state_manager()
        
        # 测试初始状态
        if not state_manager.is_data_loaded():
            print("✅ 初始状态：数据未加载")
        else:
            print("⚠️  初始状态异常：数据显示已加载")
            return False
        
        # 创建测试数据
        test_data = pd.DataFrame({
            'event_name': ['page_view', 'click', 'purchase'],
            'user_id': ['user_001', 'user_002', 'user_003'],
            'timestamp': [1640995200, 1640995260, 1640995320]
        })
        
        # 测试设置数据加载状态
        state_manager.set_data_loaded(True, test_data)
        
        if state_manager.is_data_loaded():
            print("✅ 数据加载状态设置成功")
        else:
            print("❌ 数据加载状态设置失败")
            return False
        
        # 测试获取数据
        raw_data = state_manager.get_raw_data()
        if raw_data is not None and len(raw_data) == 3:
            print("✅ 原始数据存储和获取成功")
        else:
            print("❌ 原始数据存储或获取失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 状态管理器测试失败: {e}")
        return False

def test_data_upload_page_state_integration():
    """测试数据上传页面与状态管理器的集成"""
    print("\n🔍 测试数据上传页面状态集成...")
    
    try:
        from ui.pages.data_upload import DataUploadPage
        from tools.ga4_data_parser import GA4DataParser
        from tools.data_validator import DataValidator
        
        # 创建测试数据上传页面
        upload_page = DataUploadPage()
        
        # 验证组件初始化
        if hasattr(upload_page, 'parser') and isinstance(upload_page.parser, GA4DataParser):
            print("✅ GA4数据解析器初始化成功")
        else:
            print("❌ GA4数据解析器初始化失败")
            return False
            
        if hasattr(upload_page, 'validator') and isinstance(upload_page.validator, DataValidator):
            print("✅ 数据验证器初始化成功")
        else:
            print("❌ 数据验证器初始化失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 数据上传页面集成测试失败: {e}")
        return False

def test_common_components_state_check():
    """测试通用组件的状态检查功能"""
    print("\n🔍 测试通用组件状态检查...")
    
    try:
        from ui.components.common import render_data_status_check
        from ui.state import get_state_manager
        
        state_manager = get_state_manager()
        
        # 创建一个测试函数
        @render_data_status_check
        def test_function():
            return "数据检查通过"
        
        # 测试无数据状态
        state_manager.set_data_loaded(False)
        result = test_function()
        
        # 如果没有数据，函数应该返回None
        if result is None:
            print("✅ 无数据状态检查正常")
        else:
            print("⚠️  无数据状态检查可能有问题")
        
        # 测试有数据状态
        test_data = pd.DataFrame({'test': [1, 2, 3]})
        state_manager.set_data_loaded(True, test_data)
        result = test_function()
        
        if result == "数据检查通过":
            print("✅ 有数据状态检查正常")
        else:
            print("❌ 有数据状态检查失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 通用组件状态检查测试失败: {e}")
        return False

def test_data_processing_workflow():
    """测试完整的数据处理工作流"""
    print("\n🔍 测试完整数据处理工作流...")
    
    try:
        from tools.ga4_data_parser import GA4DataParser
        from tools.data_validator import DataValidator
        from ui.state import get_state_manager
        
        # 初始化组件
        parser = GA4DataParser()
        validator = DataValidator()
        state_manager = get_state_manager()
        
        # 读取测试数据
        test_file = Path(__file__).parent / "test_data.ndjson"
        if not test_file.exists():
            print("❌ 测试数据文件不存在")
            return False
        
        # 解析数据
        raw_data = parser.parse_ndjson(str(test_file))
        if raw_data is None or raw_data.empty:
            print("❌ 数据解析失败")
            return False
        else:
            print(f"✅ 数据解析成功，共 {len(raw_data)} 行")
        
        # 验证数据
        validation_report = validator.validate_dataframe(raw_data)
        if validation_report:
            print("✅ 数据验证完成")
        else:
            print("❌ 数据验证失败")
            return False
        
        # 通过状态管理器存储数据
        state_manager.set_data_loaded(True, raw_data)
        
        # 验证状态同步
        if state_manager.is_data_loaded():
            stored_data = state_manager.get_raw_data()
            if stored_data is not None and len(stored_data) == len(raw_data):
                print("✅ 数据状态同步成功")
                return True
            else:
                print("❌ 数据状态同步失败")
                return False
        else:
            print("❌ 数据加载状态未正确设置")
            return False
        
    except Exception as e:
        print(f"❌ 数据处理工作流测试失败: {e}")
        return False

def run_comprehensive_state_tests():
    """运行全面的状态测试"""
    print("🚀 开始数据状态同步测试...")
    print("=" * 60)
    
    tests = [
        ("状态管理器数据加载", test_state_manager_data_loading),
        ("数据上传页面状态集成", test_data_upload_page_state_integration),
        ("通用组件状态检查", test_common_components_state_check),
        ("完整数据处理工作流", test_data_processing_workflow)
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
        print("🎉 所有状态同步测试通过！数据上传后状态同步问题已解决！")
        return True
    else:
        print(f"⚠️  {total - passed} 个测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = run_comprehensive_state_tests()
    sys.exit(0 if success else 1)