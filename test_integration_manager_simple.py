#!/usr/bin/env python3
"""
简单的集成管理器测试

测试集成管理器是否能正常初始化，不再出现Pydantic错误
"""

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志级别为WARNING以减少输出
logging.basicConfig(level=logging.WARNING)

def test_integration_manager_initialization():
    """测试集成管理器初始化"""
    print("测试集成管理器初始化...")
    
    try:
        from system.integration_manager import IntegrationManager
        
        # 尝试创建集成管理器实例
        manager = IntegrationManager()
        
        print("✅ 集成管理器初始化成功")
        
        # 测试数据转换方法是否存在
        if hasattr(manager, '_transform_retention_data_for_visualization'):
            print("✅ 留存数据转换方法存在")
        else:
            print("❌ 留存数据转换方法不存在")
            return False
            
        if hasattr(manager, '_transform_conversion_data_for_visualization'):
            print("✅ 转化数据转换方法存在")
        else:
            print("❌ 转化数据转换方法不存在")
            return False
        
        # 关闭管理器
        manager.shutdown()
        print("✅ 集成管理器关闭成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成管理器初始化失败: {e}")
        return False

def test_agent_initialization():
    """测试智能体初始化"""
    print("\n测试智能体初始化...")
    
    try:
        from agents.retention_analysis_agent import RetentionAnalysisAgent
        from agents.conversion_analysis_agent import ConversionAnalysisAgent
        from tools.data_storage_manager import DataStorageManager
        
        storage_manager = DataStorageManager()
        
        # 测试留存分析智能体
        retention_agent = RetentionAnalysisAgent(storage_manager)
        print("✅ 留存分析智能体初始化成功")
        
        # 测试转化分析智能体
        conversion_agent = ConversionAnalysisAgent(storage_manager)
        print("✅ 转化分析智能体初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 智能体初始化失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试修复后的系统...")
    
    tests = [
        test_integration_manager_initialization,
        test_agent_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Pydantic错误已修复。")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)