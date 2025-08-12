#!/usr/bin/env python3
"""
修复存储管理器问题
"""

import pandas as pd
from pathlib import Path
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager

def fix_storage_issue():
    """修复存储管理器问题"""
    try:
        print("🔧 修复存储管理器问题...")
        
        # 1. 加载和处理数据
        data_file = Path("data/events_ga4.ndjson")
        if not data_file.exists():
            print("❌ 数据文件不存在")
            return False
        
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        print(f"✅ 解析了 {len(raw_data)} 个事件")
        
        # 2. 提取和合并事件数据
        events_data = parser.extract_events(raw_data)
        
        if isinstance(events_data, dict):
            all_events_list = []
            for event_type, event_df in events_data.items():
                if not event_df.empty:
                    all_events_list.append(event_df)
            
            if all_events_list:
                combined_events = pd.concat(all_events_list, ignore_index=True)
                print(f"✅ 合并了 {len(events_data)} 种事件类型，总计 {len(combined_events)} 个事件")
            else:
                combined_events = pd.DataFrame()
        else:
            combined_events = events_data
        
        # 3. 确保存储管理器有数据
        storage_manager = DataStorageManager()
        storage_manager.store_events(combined_events)
        
        # 4. 验证存储
        stored_events = storage_manager.get_data('events')
        if stored_events is not None and not stored_events.empty:
            print(f"✅ 存储验证成功，事件数: {len(stored_events)}")
            
            # 5. 测试分析引擎接口
            from engines.event_analysis_engine import EventAnalysisEngine
            from engines.retention_analysis_engine import RetentionAnalysisEngine
            
            print("🧪 测试分析引擎...")
            
            # 测试事件分析
            event_engine = EventAnalysisEngine(storage_manager)
            event_result = event_engine.analyze_events(stored_events)
            print(f"✅ 事件分析: {event_result.get('status', 'unknown')}")
            
            # 测试留存分析
            retention_engine = RetentionAnalysisEngine(storage_manager)
            retention_result = retention_engine.analyze_retention(stored_events)
            print(f"✅ 留存分析: {retention_result.get('status', 'unknown')}")
            
            return True
        else:
            print("❌ 存储验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_storage_issue()
    if success:
        print("\n🎉 存储问题修复成功！")
        print("现在可以重新启动应用了。")
    else:
        print("\n❌ 存储问题修复失败")