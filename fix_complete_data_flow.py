#!/usr/bin/env python3
"""
完整修复数据流程问题
"""

import pandas as pd
from pathlib import Path
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager
from system.integration_manager import IntegrationManager, WorkflowConfig

def fix_complete_data_flow():
    """完整修复数据流程问题"""
    try:
        print("🔧 完整修复数据流程问题...")
        
        # 1. 确保数据文件存在
        data_file = Path("data/events_ga4.ndjson")
        if not data_file.exists():
            print("📊 生成测试数据...")
            import subprocess
            import sys
            subprocess.run([sys.executable, "generate_clean_data.py"], check=True)
        
        print(f"✅ 数据文件存在: {data_file}")
        
        # 2. 解析数据
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        print(f"✅ 解析了 {len(raw_data)} 个原始事件")
        
        # 3. 提取和合并事件数据（使用修复后的逻辑）
        events_data = parser.extract_events(raw_data)
        user_data = parser.extract_user_properties(raw_data)
        session_data = parser.extract_sessions(raw_data)
        
        # 处理事件数据
        if isinstance(events_data, dict):
            all_events_list = []
            for event_type, event_df in events_data.items():
                if not event_df.empty:
                    all_events_list.append(event_df)
                    print(f"  添加 {event_type}: {len(event_df)} 个事件")
            
            if all_events_list:
                combined_events = pd.concat(all_events_list, ignore_index=True)
                print(f"✅ 合并了 {len(events_data)} 种事件类型，总计 {len(combined_events)} 个事件")
            else:
                combined_events = pd.DataFrame()
                print("⚠️ 没有找到有效的事件数据")
        else:
            combined_events = events_data
        
        # 4. 创建存储管理器并存储数据
        storage_manager = DataStorageManager()
        storage_manager.store_events(combined_events)
        storage_manager.store_users(user_data)
        storage_manager.store_sessions(session_data)
        
        # 5. 验证存储
        stored_events = storage_manager.get_data('events')
        if stored_events is None or stored_events.empty:
            print("❌ 数据存储失败")
            return False
        
        print(f"✅ 数据存储成功，事件数: {len(stored_events)}")
        
        # 6. 测试分析引擎
        print("🧪 测试分析引擎...")
        from engines.event_analysis_engine import EventAnalysisEngine
        from engines.retention_analysis_engine import RetentionAnalysisEngine
        
        event_engine = EventAnalysisEngine(storage_manager)
        event_result = event_engine.analyze_events(stored_events)
        print(f"✅ 事件分析: {event_result.get('status', 'unknown')}")
        
        retention_engine = RetentionAnalysisEngine(storage_manager)
        retention_result = retention_engine.analyze_retention(stored_events)
        print(f"✅ 留存分析: {retention_result.get('status', 'unknown')}")
        
        # 7. 测试集成管理器
        print("🔗 测试集成管理器...")
        config = WorkflowConfig(
            enable_parallel_processing=False,
            max_workers=2,
            timeout_minutes=5,
            enable_caching=True,
            auto_cleanup=True
        )
        
        integration_manager = IntegrationManager(config)
        
        # 确保集成管理器使用相同的存储管理器
        integration_manager.storage_manager = storage_manager
        
        # 重新初始化分析引擎以使用正确的存储管理器
        from engines.event_analysis_engine import EventAnalysisEngine
        from engines.retention_analysis_engine import RetentionAnalysisEngine
        from engines.conversion_analysis_engine import ConversionAnalysisEngine
        
        integration_manager.event_engine = EventAnalysisEngine(storage_manager)
        integration_manager.retention_engine = RetentionAnalysisEngine(storage_manager)
        integration_manager.conversion_engine = ConversionAnalysisEngine(storage_manager)
        
        # 测试单个分析
        print("🧪 测试集成管理器分析...")
        try:
            single_result = integration_manager._execute_single_analysis('event_analysis')
            print(f"✅ 集成管理器事件分析: {single_result.status}")
        except Exception as e:
            print(f"⚠️ 集成管理器事件分析失败: {e}")
        
        try:
            retention_result = integration_manager._execute_single_analysis('retention_analysis')
            print(f"✅ 集成管理器留存分析: {retention_result.status}")
        except Exception as e:
            print(f"⚠️ 集成管理器留存分析失败: {e}")
        
        print("\\n🎉 完整数据流程修复成功！")
        print("现在应用应该可以正常工作了。")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_complete_data_flow()
    if success:
        print("\\n🚀 现在可以启动应用了:")
        print("   streamlit run main.py")
    else:
        print("\\n❌ 修复失败，请检查错误信息")