#!/usr/bin/env python3
"""
性能瓶颈测试
验证IntegrationManager初始化时间
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_integration_manager_initialization_time():
    """测试IntegrationManager初始化时间"""
    print("🔍 测试IntegrationManager初始化时间...")
    
    try:
        start_time = time.time()
        
        from system.integration_manager import IntegrationManager
        
        init_start = time.time()
        manager = IntegrationManager()
        init_end = time.time()
        
        total_time = init_end - start_time
        init_time = init_end - init_start
        
        print(f"⏱️  导入耗时: {init_start - start_time:.2f}秒")
        print(f"⏱️  初始化耗时: {init_time:.2f}秒")
        print(f"⏱️  总耗时: {total_time:.2f}秒")
        
        if init_time > 5:
            print(f"❌ 初始化耗时过长: {init_time:.2f}秒 > 5秒")
            return False
        elif init_time > 2:
            print(f"⚠️  初始化耗时较长: {init_time:.2f}秒")
        else:
            print(f"✅ 初始化耗时正常: {init_time:.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ IntegrationManager初始化测试失败: {e}")
        return False

def test_multiple_initialization_overhead():
    """测试多次初始化开销"""
    print("\n🔍 测试多次初始化开销...")
    
    try:
        from system.integration_manager import IntegrationManager
        
        times = []
        for i in range(3):
            start = time.time()
            manager = IntegrationManager()
            end = time.time()
            times.append(end - start)
            print(f"第{i+1}次初始化: {times[i]:.2f}秒")
        
        avg_time = sum(times) / len(times)
        print(f"平均初始化时间: {avg_time:.2f}秒")
        
        if avg_time > 3:
            print(f"❌ 平均初始化时间过长: {avg_time:.2f}秒")
            return False
        else:
            print(f"✅ 多次初始化测试完成")
            return True
        
    except Exception as e:
        print(f"❌ 多次初始化测试失败: {e}")
        return False

def test_agent_orchestrator_overhead():
    """测试AgentOrchestrator开销"""
    print("\n🔍 测试AgentOrchestrator开销...")
    
    try:
        start_time = time.time()
        
        from config.agent_orchestrator import AgentOrchestrator
        from tools.data_storage_manager import DataStorageManager
        
        import_time = time.time()
        
        storage_manager = DataStorageManager()
        orchestrator = AgentOrchestrator(storage_manager)
        
        init_time = time.time()
        
        import_duration = import_time - start_time
        init_duration = init_time - import_time
        total_duration = init_time - start_time
        
        print(f"⏱️  导入耗时: {import_duration:.2f}秒")
        print(f"⏱️  初始化耗时: {init_duration:.2f}秒")
        print(f"⏱️  总耗时: {total_duration:.2f}秒")
        
        if init_duration > 3:
            print(f"❌ AgentOrchestrator初始化耗时过长: {init_duration:.2f}秒")
            return False
        else:
            print(f"✅ AgentOrchestrator初始化测试完成")
            return True
        
    except Exception as e:
        print(f"❌ AgentOrchestrator测试失败: {e}")
        return False

def test_page_object_creation_overhead():
    """测试页面对象创建开销"""
    print("\n🔍 测试页面对象创建开销...")
    
    try:
        from ui.pages.event_analysis import EventAnalysisPage
        
        times = []
        for i in range(5):
            start = time.time()
            page = EventAnalysisPage()
            end = time.time()
            times.append(end - start)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"页面对象创建平均时间: {avg_time:.3f}秒")
        print(f"页面对象创建最大时间: {max_time:.3f}秒")
        
        if max_time > 0.1:
            print(f"⚠️  页面对象创建时间较长: {max_time:.3f}秒")
        else:
            print(f"✅ 页面对象创建时间正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 页面对象创建测试失败: {e}")
        return False

def run_performance_tests():
    """运行性能测试"""
    print("🚀 开始性能瓶颈测试...")
    print("=" * 60)
    
    tests = [
        ("IntegrationManager初始化时间", test_integration_manager_initialization_time),
        ("多次初始化开销", test_multiple_initialization_overhead),
        ("AgentOrchestrator开销", test_agent_orchestrator_overhead),
        ("页面对象创建开销", test_page_object_creation_overhead)
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
    
    if passed >= total * 0.5:  # 至少一半通过
        print("🎯 性能测试完成，已识别瓶颈！")
        return True
    else:
        print(f"⚠️  {total - passed} 个测试失败，需要进一步优化")
        return False

if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)