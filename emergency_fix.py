#!/usr/bin/env python3
"""
紧急修复脚本 - 确保数据正确加载到存储管理器
"""

import pandas as pd
from pathlib import Path
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager

def emergency_fix():
    """紧急修复数据加载问题"""
    try:
        print("🚨 紧急修复数据加载问题...")
        
        # 1. 检查数据文件
        data_file = Path("data/events_ga4.ndjson")
        if not data_file.exists():
            print("❌ 数据文件不存在")
            return False
        
        # 2. 解析数据
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        print(f"✅ 解析了 {len(raw_data)} 个原始事件")
        
        # 3. 提取和合并事件数据
        events_data = parser.extract_events(raw_data)
        
        if isinstance(events_data, dict):
            all_events_list = []
            event_counts = {}
            for event_type, event_df in events_data.items():
                if not event_df.empty:
                    all_events_list.append(event_df)
                    event_counts[event_type] = len(event_df)
            
            if all_events_list:
                combined_events = pd.concat(all_events_list, ignore_index=True)
                print(f"✅ 合并了 {len(events_data)} 种事件类型:")
                for event_type, count in event_counts.items():
                    print(f"   - {event_type}: {count} 个事件")
                print(f"   总计: {len(combined_events)} 个事件")
            else:
                combined_events = pd.DataFrame()
                print("❌ 没有找到有效的事件数据")
                return False
        else:
            combined_events = events_data
            print(f"✅ 直接使用事件数据: {len(combined_events)} 个事件")
        
        # 4. 验证数据结构
        if combined_events.empty:
            print("❌ 合并后的事件数据为空")
            return False
        
        required_columns = ['event_name', 'user_pseudo_id', 'event_timestamp']
        missing_columns = [col for col in required_columns if col not in combined_events.columns]
        if missing_columns:
            print(f"⚠️ 缺少必要列: {missing_columns}")
            print(f"可用列: {list(combined_events.columns)}")
        
        # 5. 创建存储管理器并存储数据
        storage_manager = DataStorageManager()
        
        print("💾 存储事件数据...")
        storage_manager.store_events(combined_events)
        
        # 6. 验证存储
        stored_events = storage_manager.get_data('events')
        if stored_events is None or stored_events.empty:
            print("❌ 数据存储失败 - 存储后为空")
            
            # 调试存储管理器状态
            print("🔍 调试存储管理器状态:")
            print(f"   _events_data 类型: {type(storage_manager._events_data)}")
            print(f"   _events_data 形状: {getattr(storage_manager._events_data, 'shape', 'N/A')}")
            print(f"   _events_data 为空: {getattr(storage_manager._events_data, 'empty', 'N/A')}")
            
            return False
        
        print(f"✅ 数据存储成功，验证结果:")
        print(f"   存储的事件数: {len(stored_events)}")
        print(f"   事件类型数: {stored_events['event_name'].nunique() if 'event_name' in stored_events.columns else 'N/A'}")
        print(f"   独立用户数: {stored_events['user_pseudo_id'].nunique() if 'user_pseudo_id' in stored_events.columns else 'N/A'}")
        
        # 7. 测试分析引擎
        print("🧪 测试分析引擎...")
        from engines.event_analysis_engine import EventAnalysisEngine
        
        event_engine = EventAnalysisEngine(storage_manager)
        
        # 直接测试 get_events 方法
        engine_events = event_engine.storage_manager.get_events()
        if engine_events is None or engine_events.empty:
            print("❌ 分析引擎无法获取事件数据")
            return False
        
        print(f"✅ 分析引擎可以获取 {len(engine_events)} 个事件")
        
        # 测试分析方法
        try:
            analysis_result = event_engine.analyze_events(engine_events)
            print(f"✅ 事件分析成功: {analysis_result.get('status', 'unknown')}")
        except Exception as e:
            print(f"❌ 事件分析失败: {e}")
            return False
        
        print("\\n🎉 紧急修复成功！数据已正确加载到存储管理器。")
        return True
        
    except Exception as e:
        print(f"❌ 紧急修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = emergency_fix()
    if success:
        print("\\n✅ 现在可以重新启动应用，数据应该可以正常工作了。")
    else:
        print("\\n❌ 紧急修复失败，需要进一步调试。")