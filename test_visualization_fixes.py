#!/usr/bin/env python3
"""
测试可视化修复

验证留存分析和转化分析的可视化数据转换是否正常工作
"""

import sys
import os
import pandas as pd
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from system.integration_manager import IntegrationManager
from tools.data_storage_manager import DataStorageManager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_retention_data_transformation():
    """测试留存数据转换"""
    print("测试留存数据转换...")
    
    # 创建模拟的留存分析结果
    mock_result = {
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
    
    # 创建集成管理器
    manager = IntegrationManager()
    
    # 测试数据转换
    viz_data = manager._transform_retention_data_for_visualization(mock_result)
    
    print(f"转换后的数据形状: {viz_data.shape}")
    print(f"列名: {list(viz_data.columns)}")
    print("前几行数据:")
    print(viz_data.head())
    
    # 验证必要的列存在
    required_columns = ['cohort_group', 'period_number', 'retention_rate']
    missing_columns = [col for col in required_columns if col not in viz_data.columns]
    
    if missing_columns:
        print(f"❌ 缺少必要的列: {missing_columns}")
        return False
    else:
        print("✅ 留存数据转换成功")
        return True

def test_conversion_data_transformation():
    """测试转化数据转换"""
    print("\n测试转化数据转换...")
    
    # 创建模拟的转化分析结果
    mock_result = {
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
    
    # 创建集成管理器
    manager = IntegrationManager()
    
    # 测试数据转换
    viz_data = manager._transform_conversion_data_for_visualization(mock_result)
    
    print(f"转换后的数据形状: {viz_data.shape}")
    print(f"列名: {list(viz_data.columns)}")
    print("前几行数据:")
    print(viz_data.head())
    
    # 验证必要的列存在
    required_columns = ['step_name', 'user_count']
    missing_columns = [col for col in required_columns if col not in viz_data.columns]
    
    if missing_columns:
        print(f"❌ 缺少必要的列: {missing_columns}")
        return False
    else:
        print("✅ 转化数据转换成功")
        return True

def test_empty_data_handling():
    """测试空数据处理"""
    print("\n测试空数据处理...")
    
    manager = IntegrationManager()
    
    # 测试空的留存数据
    empty_retention_result = {'success': False}
    retention_data = manager._transform_retention_data_for_visualization(empty_retention_result)
    print(f"空留存数据处理结果: {retention_data.shape}")
    
    # 测试空的转化数据
    empty_conversion_result = {'status': 'error'}
    conversion_data = manager._transform_conversion_data_for_visualization(empty_conversion_result)
    print(f"空转化数据处理结果: {conversion_data.shape}")
    
    # 验证即使是空数据也能返回有效的DataFrame
    if (not retention_data.empty and not conversion_data.empty and
        'cohort_group' in retention_data.columns and 'step_name' in conversion_data.columns):
        print("✅ 空数据处理成功")
        return True
    else:
        print("❌ 空数据处理失败")
        return False

def main():
    """主测试函数"""
    print("开始测试可视化修复...")
    
    tests = [
        test_retention_data_transformation,
        test_conversion_data_transformation,
        test_empty_data_handling
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
        print("🎉 所有测试通过！可视化修复成功。")
        return True
    else:
        print("⚠️  部分测试失败，需要进一步检查。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)