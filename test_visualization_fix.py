#!/usr/bin/env python3
"""
测试可视化图表修复
验证所有分析模块的可视化数据格式是否正确
"""

import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from system.integration_manager import IntegrationManager
from tools.data_storage_manager import DataStorageManager
from utils.logger import setup_logger

logger = setup_logger()


def create_test_data():
    """创建测试数据"""
    print("📊 创建测试数据...")
    
    # 创建事件数据
    events_data = pd.DataFrame({
        'event_date': ['2024-01-01'] * 100,
        'event_timestamp': list(range(100)),
        'event_name': ['page_view', 'sign_up', 'login', 'purchase'] * 25,
        'user_pseudo_id': [f'user_{i % 20}' for i in range(100)],
        'user_id': [f'uid_{i % 20}' for i in range(100)],
        'platform': ['web'] * 50 + ['mobile'] * 50,
        'device_category': ['desktop'] * 30 + ['mobile'] * 40 + ['tablet'] * 30
    })
    
    # 创建用户数据
    users_data = pd.DataFrame({
        'user_id': [f'uid_{i}' for i in range(20)],
        'user_pseudo_id': [f'user_{i}' for i in range(20)],
        'first_seen': ['2024-01-01'] * 20,
        'last_seen': ['2024-01-15'] * 20,
        'total_events': np.random.randint(10, 100, 20),
        'platform': ['web'] * 10 + ['mobile'] * 10
    })
    
    # 创建会话数据
    sessions_data = pd.DataFrame({
        'session_id': [f'session_{i}' for i in range(30)],
        'user_id': [f'uid_{i % 20}' for i in range(30)],
        'user_pseudo_id': [f'user_{i % 20}' for i in range(30)],
        'start_time': pd.date_range('2024-01-01', periods=30, freq='H'),
        'platform': ['web'] * 15 + ['mobile'] * 15,
        'device_category': ['desktop'] * 10 + ['mobile'] * 10 + ['tablet'] * 10,
        'geo_country': ['China'] * 10 + ['USA'] * 10 + ['Japan'] * 10,
        'geo_city': ['Beijing'] * 5 + ['Shanghai'] * 5 + ['New York'] * 5 + ['Tokyo'] * 5 + ['Osaka'] * 5 + ['LA'] * 5
    })
    
    return events_data, users_data, sessions_data


def test_visualization_format():
    """测试可视化数据格式"""
    print("\n🔍 测试可视化数据格式...")
    
    # 初始化存储管理器
    storage_manager = DataStorageManager()
    
    # 创建并存储测试数据
    events_data, users_data, sessions_data = create_test_data()
    storage_manager.store_events(events_data)
    storage_manager.store_users(users_data)
    storage_manager.store_sessions(sessions_data)
    
    # 初始化集成管理器
    integration_manager = IntegrationManager()
    integration_manager.storage_manager = storage_manager
    
    # 测试各个分析模块
    analysis_types = [
        'event_analysis',
        'retention_analysis',
        'conversion_analysis',
        'user_segmentation',
        'path_analysis'
    ]
    
    results = {}
    for analysis_type in analysis_types:
        print(f"\n📈 测试 {analysis_type}...")
        
        try:
            if analysis_type == 'event_analysis':
                result = integration_manager._execute_event_analysis()
            elif analysis_type == 'retention_analysis':
                result = integration_manager._execute_retention_analysis()
            elif analysis_type == 'conversion_analysis':
                result = integration_manager._execute_conversion_analysis()
            elif analysis_type == 'user_segmentation':
                result = integration_manager._execute_segmentation_analysis()
            elif analysis_type == 'path_analysis':
                result = integration_manager._execute_path_analysis()
            
            results[analysis_type] = result
            
            # 检查可视化数据格式
            if 'visualizations' in result and result['visualizations']:
                print(f"  ✅ 找到可视化数据")
                for viz_name, viz_data in result['visualizations'].items():
                    if isinstance(viz_data, dict) and 'chart' in viz_data:
                        print(f"    ✅ {viz_name}: 格式正确 (包含 'chart' 键)")
                        print(f"       - 类型: {viz_data.get('type', 'unknown')}")
                        print(f"       - 标题: {viz_data.get('title', 'unknown')}")
                    else:
                        print(f"    ❌ {viz_name}: 格式错误 (缺少 'chart' 键)")
                        print(f"       - 数据类型: {type(viz_data)}")
            else:
                print(f"  ⚠️ 没有可视化数据")
                
        except Exception as e:
            print(f"  ❌ 测试失败: {str(e)}")
            results[analysis_type] = {'error': str(e)}
    
    return results


def test_workflow_integration():
    """测试完整工作流程中的可视化"""
    print("\n🔄 测试完整工作流程...")
    
    # 初始化集成管理器
    integration_manager = IntegrationManager()
    
    # 创建测试数据文件
    test_file = Path("data/test_events.ndjson")
    test_file.parent.mkdir(exist_ok=True)
    
    # 生成测试NDJSON数据
    test_events = []
    for i in range(50):
        event = {
            'event_date': '20240101',
            'event_timestamp': i * 1000000,
            'event_name': ['page_view', 'sign_up', 'login', 'purchase'][i % 4],
            'user_pseudo_id': f'user_{i % 10}',
            'platform': 'web',
            'device': {'category': 'desktop'},
            'geo': {'country': 'China', 'city': 'Beijing'},
            'traffic_source': {'source': 'google', 'medium': 'organic'},
            'event_params': [],
            'user_properties': []
        }
        test_events.append(json.dumps(event))
    
    with open(test_file, 'w') as f:
        f.write('\n'.join(test_events))
    
    print(f"  📝 创建测试文件: {test_file}")
    
    try:
        # 执行完整工作流程
        result = integration_manager.execute_complete_workflow(
            str(test_file),
            analysis_types=['event_analysis', 'retention_analysis']
        )
        
        # 检查可视化数据
        if 'visualizations' in result:
            print("  ✅ 工作流程包含可视化数据")
            for analysis_type, viz_dict in result['visualizations'].items():
                print(f"\n  📊 {analysis_type}:")
                for viz_name, viz_data in viz_dict.items():
                    if isinstance(viz_data, dict) and 'chart' in viz_data:
                        print(f"    ✅ {viz_name}: 格式正确")
                    else:
                        print(f"    ❌ {viz_name}: 格式错误")
        else:
            print("  ⚠️ 工作流程没有可视化数据")
            
    except Exception as e:
        print(f"  ❌ 工作流程测试失败: {str(e)}")
    
    # 清理测试文件
    if test_file.exists():
        test_file.unlink()
        print(f"  🧹 清理测试文件")


def main():
    """主函数"""
    print("=" * 60)
    print("🎯 可视化图表格式修复测试")
    print("=" * 60)
    
    # 测试单个模块
    module_results = test_visualization_format()
    
    # 测试完整工作流程
    test_workflow_integration()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for analysis_type, result in module_results.items():
        if 'error' in result:
            fail_count += 1
            print(f"  ❌ {analysis_type}: 失败")
        elif 'visualizations' in result and result['visualizations']:
            all_correct = all(
                isinstance(viz, dict) and 'chart' in viz
                for viz in result['visualizations'].values()
            )
            if all_correct:
                success_count += 1
                print(f"  ✅ {analysis_type}: 成功")
            else:
                fail_count += 1
                print(f"  ⚠️ {analysis_type}: 部分成功")
        else:
            print(f"  ⚠️ {analysis_type}: 无可视化数据")
    
    print(f"\n成功: {success_count}, 失败: {fail_count}")
    
    if fail_count == 0:
        print("\n✅ 所有可视化格式修复成功！")
    else:
        print(f"\n⚠️ 还有 {fail_count} 个模块需要修复")


if __name__ == "__main__":
    main()