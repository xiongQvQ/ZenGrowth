#!/usr/bin/env python3
"""
测试留存分析可视化修复
"""

import sys
import os
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_retention_data_transformation():
    """测试留存数据转换"""
    print("=== 测试留存数据转换 ===\n")
    
    try:
        from system.integration_manager import IntegrationManager
        
        # 创建集成管理器
        manager = IntegrationManager()
        
        # 创建模拟的留存分析结果
        mock_result = {
            'success': True,
            'analyses': {
                'cohort_analysis': {
                    'success': True,
                    'cohorts': [
                        {
                            'cohort_period': '2024-01',
                            'retention_rates': [1.0, 0.8, 0.6, 0.4]
                        },
                        {
                            'cohort_period': '2024-02', 
                            'retention_rates': [1.0, 0.7, 0.5, 0.3]
                        }
                    ]
                }
            }
        }
        
        # 测试数据转换
        viz_data = manager._transform_retention_data_for_visualization(mock_result)
        
        print(f"转换后的数据形状: {viz_data.shape}")
        print(f"数据列: {list(viz_data.columns)}")
        print("\n前几行数据:")
        print(viz_data.head())
        
        # 验证必要的列
        required_columns = ['cohort_group', 'period_number', 'retention_rate']
        missing_columns = [col for col in required_columns if col not in viz_data.columns]
        
        if not missing_columns:
            print("✅ 所有必要的列都存在")
            return True
        else:
            print(f"❌ 缺少列: {missing_columns}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_empty_result_handling():
    """测试空结果处理"""
    print("\n=== 测试空结果处理 ===\n")
    
    try:
        from system.integration_manager import IntegrationManager
        
        manager = IntegrationManager()
        
        # 测试空结果
        empty_result = {'success': False}
        viz_data = manager._transform_retention_data_for_visualization(empty_result)
        
        print(f"空结果转换后的数据形状: {viz_data.shape}")
        print(f"数据列: {list(viz_data.columns)}")
        
        # 验证示例数据
        required_columns = ['cohort_group', 'period_number', 'retention_rate']
        missing_columns = [col for col in required_columns if col not in viz_data.columns]
        
        if not missing_columns and not viz_data.empty:
            print("✅ 空结果正确处理，生成了示例数据")
            return True
        else:
            print(f"❌ 空结果处理失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_visualization_creation():
    """测试可视化创建"""
    print("\n=== 测试可视化创建 ===\n")
    
    try:
        from visualization.advanced_visualizer import AdvancedVisualizer
        
        # 创建测试数据
        test_data = pd.DataFrame([
            {'cohort_group': '2024-01', 'period_number': 0, 'retention_rate': 1.0},
            {'cohort_group': '2024-01', 'period_number': 1, 'retention_rate': 0.7},
            {'cohort_group': '2024-01', 'period_number': 2, 'retention_rate': 0.5},
            {'cohort_group': '2024-02', 'period_number': 0, 'retention_rate': 1.0},
            {'cohort_group': '2024-02', 'period_number': 1, 'retention_rate': 0.8},
            {'cohort_group': '2024-02', 'period_number': 2, 'retention_rate': 0.6}
        ])
        
        visualizer = AdvancedVisualizer()
        
        # 测试热力图创建
        heatmap = visualizer.create_retention_heatmap(test_data)
        print("✅ 留存热力图创建成功")
        
        # 只测试留存热力图，因为队列分析热力图需要不同的数据格式
        print("✅ 留存分析只需要留存热力图")
        
        return True
        
    except Exception as e:
        print(f"❌ 可视化创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试留存分析可视化修复...\n")
    
    # 测试数据转换
    transform_success = test_retention_data_transformation()
    
    # 测试空结果处理
    empty_success = test_empty_result_handling()
    
    # 测试可视化创建
    viz_success = test_visualization_creation()
    
    print(f"\n=== 测试结果 ===")
    print(f"数据转换: {'✅ 通过' if transform_success else '❌ 失败'}")
    print(f"空结果处理: {'✅ 通过' if empty_success else '❌ 失败'}")
    print(f"可视化创建: {'✅ 通过' if viz_success else '❌ 失败'}")
    
    if transform_success and empty_success and viz_success:
        print("\n🎉 留存分析可视化修复成功!")
        return True
    else:
        print("\n❌ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)