#!/usr/bin/env python3
"""
测试集成管理器修复
"""

import pandas as pd
from pathlib import Path
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager
from system.integration_manager import IntegrationManager, WorkflowConfig

def test_integration_fix():
    """测试集成管理器修复"""
    try:
        print("🧪 测试集成管理器修复...")
        
        # 1. 准备数据
        data_file = Path("data/events_ga4.ndjson")
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        
        # 2. 处理数据
        events_data = parser.extract_events(raw_data)
        if isinstance(events_data, dict):
            all_events_list = []
            for event_type, event_df in events_data.items():
                if not event_df.empty:
                    all_events_list.append(event_df)
            combined_events = pd.concat(all_events_list, ignore_index=True)
        else:
            combined_events = events_data
        
        print(f"✅ 准备了 {len(combined_events)} 个事件")
        
        # 3. 创建存储管理器并存储数据
        storage_manager = DataStorageManager()
        storage_manager.store_events(combined_events)
        
        # 验证存储
        stored_events = storage_manager.get_data('events')
        if stored_events.empty:
            print("❌ 存储管理器中没有数据")
            return False
        
        print(f"✅ 存储管理器有 {len(stored_events)} 个事件")
        
        # 4. 创建集成管理器
        config = WorkflowConfig(
            enable_parallel_processing=False,
            max_workers=2,
            timeout_minutes=5,
            enable_caching=True,
            auto_cleanup=True
        )
        
        integration_manager = IntegrationManager(config)
        
        # 5. 测试初始状态（应该为空）
        initial_events = integration_manager.storage_manager.get_data('events')
        print(f"🔍 集成管理器初始事件数: {len(initial_events)}")
        
        # 6. 刷新存储管理器
        print("🔄 刷新集成管理器的存储管理器...")
        integration_manager.refresh_storage_manager(storage_manager)
        
        # 7. 验证刷新后的状态
        refreshed_events = integration_manager.storage_manager.get_data('events')
        print(f"✅ 刷新后集成管理器事件数: {len(refreshed_events)}")
        
        if refreshed_events.empty:
            print("❌ 刷新后仍然没有数据")
            return False
        
        # 8. 测试分析执行
        print("🧪 测试分析执行...")
        try:
            result = integration_manager._execute_single_analysis('event_analysis')
            print(f"✅ 事件分析状态: {result.status}")
            
            if result.status == 'failed':
                print(f"❌ 分析失败: {result.error_message}")
                return False
                
        except Exception as e:
            print(f"❌ 分析执行异常: {e}")
            return False
        
        print("\\n🎉 集成管理器修复测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration_fix()
    if success:
        print("\\n✅ 修复成功！现在集成管理器应该可以正常工作了。")
    else:
        print("\\n❌ 修复失败，需要进一步调试。")