#!/usr/bin/env python3
"""
仅测试可视化修复

跳过完整的系统初始化，直接测试可视化数据转换功能
"""

import sys
import os
import pandas as pd
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置日志级别
logging.basicConfig(level=logging.WARNING)

def test_visualization_fixes():
    """测试可视化修复"""
    print("测试可视化修复...")
    
    try:
        # 直接导入和测试数据转换方法
        from system.integration_manager import IntegrationManager
        
        # 创建一个简单的配置来避免完整初始化
        class SimpleConfig:
            def __init__(self):
                self.enable_monitoring = False
                self.enable_caching = False
                self.parallel_execution = False
                self.max_workers = 1
        
        # 尝试创建集成管理器但跳过组件初始化
        manager = IntegrationManager.__new__(IntegrationManager)
        
        # 手动设置必要的属性
        manager.logger = logging.getLogger(__name__)
        
        # 测试留存数据转换
        print("测试留存数据转换...")
        retention_result = {
            'success': True,
            'analyses': {
                'cohort_analysis': {
                    'success': True,
                    'cohorts': [
                        {
                            'cohort_period': '2024-01',
                            'retention_rates': [1.0, 0.7, 0.5, 0.3]
                        },
                        {
                            'cohort_period': '2024-02', 
                            'retention_rates': [1.0, 0.8, 0.6, 0.4]
                        }
                    ]
                }
            }
        }
        
        retention_viz_data = manager._transform_retention_data_for_visualization(retention_result)
        print(f"留存数据转换结果: {retention_viz_data.shape}")
        print(f"列名: {list(retention_viz_data.columns)}")
        
        # 验证必要的列存在
        required_columns = ['cohort_group', 'period_number', 'retention_rate']
        missing_columns = [col for col in required_columns if col not in retention_viz_data.columns]
        
        if missing_columns:
            print(f"❌ 留存数据转换失败: 缺少列 {missing_columns}")
            return False
        else:
            print("✅ 留存数据转换成功")
        
        # 测试转化数据转换
        print("\n测试转化数据转换...")
        conversion_result = {
            'status': 'success',
            'funnel_analyses': {
                'purchase_funnel': {
                    'status': 'success',
                    'funnel': {
                        'steps': [
                            {'step_name': '访问首页', 'total_users': 10000, 'step_order': 0, 'conversion_rate': 1.0},
                            {'step_name': '浏览产品', 'total_users': 7500, 'step_order': 1, 'conversion_rate': 0.75},
                            {'step_name': '添加购物车', 'total_users': 3000, 'step_order': 2, 'conversion_rate': 0.3},
                            {'step_name': '完成购买', 'total_users': 1200, 'step_order': 3, 'conversion_rate': 0.12}
                        ]
                    }
                }
            }
        }
        
        conversion_viz_data = manager._transform_conversion_data_for_visualization(conversion_result)
        print(f"转化数据转换结果: {conversion_viz_data.shape}")
        print(f"列名: {list(conversion_viz_data.columns)}")
        
        # 验证必要的列存在
        required_columns = ['step_name', 'user_count']
        missing_columns = [col for col in required_columns if col not in conversion_viz_data.columns]
        
        if missing_columns:
            print(f"❌ 转化数据转换失败: 缺少列 {missing_columns}")
            return False
        else:
            print("✅ 转化数据转换成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chi_square_fix():
    """测试卡方检验修复"""
    print("\n测试卡方检验修复...")
    
    try:
        from engines.event_analysis_engine import EventAnalysisEngine
        from tools.data_storage_manager import DataStorageManager
        
        # 创建测试数据
        import pandas as pd
        import numpy as np
        
        # 创建模拟事件数据
        events_data = pd.DataFrame({
            'user_pseudo_id': ['user1', 'user2', 'user3', 'user1', 'user2'],
            'event_name': ['page_view', 'page_view', 'purchase', 'purchase', 'page_view'],
            'event_timestamp': [1640995200000000, 1640995300000000, 1640995400000000, 1640995500000000, 1640995600000000]
        })
        
        # 创建存储管理器并存储数据
        storage_manager = DataStorageManager()
        storage_manager.store_events(events_data)
        
        # 创建事件分析引擎
        engine = EventAnalysisEngine(storage_manager)
        
        # 测试卡方相关性计算（这个之前会失败）
        correlation, p_value = engine._calculate_chi_square_correlation(
            events_data, 'page_view', 'purchase'
        )
        
        print(f"卡方相关性计算结果: correlation={correlation:.4f}, p_value={p_value:.4f}")
        print("✅ 卡方检验修复成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 卡方检验测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试可视化修复（跳过完整系统初始化）...")
    
    tests = [
        test_visualization_fixes,
        test_chi_square_fix
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
        print("🎉 所有可视化修复测试通过！")
        print("\n修复总结:")
        print("1. ✅ 留存分析可视化数据转换正常")
        print("2. ✅ 转化分析可视化数据转换正常")
        print("3. ✅ 卡方检验错误已修复")
        print("\n原始错误应该已经解决:")
        print("- 缺少必要的列: ['cohort_group', 'period_number', 'retention_rate']")
        print("- 缺少必要的列: ['step_name', 'user_count']")
        print("- 计算卡方相关性失败: The internally computed table of expected frequencies has a zero element")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)