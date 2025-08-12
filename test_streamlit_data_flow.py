#!/usr/bin/env python3
"""
测试 Streamlit 数据流程
模拟应用中的数据处理流程
"""

import pandas as pd
from pathlib import Path
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager
from system.integration_manager import IntegrationManager, WorkflowConfig

def test_streamlit_data_flow():
    """测试 Streamlit 数据流程"""
    try:
        print("🔄 测试 Streamlit 数据流程...")
        
        # 1. 模拟文件上传和解析（就像在 main.py 中一样）
        print("1. 模拟文件上传和解析...")
        data_file = Path("data/events_ga4.ndjson")
        
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        print(f"✅ 解析了 {len(raw_data)} 个事件")
        
        # 2. 提取不同类型的数据（就像在 main.py 中一样）
        print("2. 提取数据...")
        events_data = parser.extract_events(raw_data)
        user_data = parser.extract_user_properties(raw_data)
        session_data = parser.extract_sessions(raw_data)
        
        print(f"事件数据类型: {type(events_data)}")
        if isinstance(events_data, dict):
            print(f"事件数据键: {list(events_data.keys())}")
            for key, value in events_data.items():
                print(f"  {key}: {len(value)} 条记录")
        else:
            print(f"事件数据长度: {len(events_data)}")
        
        # 3. 创建存储管理器并存储数据
        print("3. 存储数据...")
        storage_manager = DataStorageManager()
        
        # 这里可能是问题所在 - 检查 extract_events 返回的是什么
        if isinstance(events_data, dict):
            # 如果是字典，可能需要合并或选择主要的事件数据
            if 'all_events' in events_data:
                storage_manager.store_events(events_data['all_events'])
            elif events_data:
                # 取第一个非空的数据集
                for key, df in events_data.items():
                    if not df.empty:
                        print(f"使用 {key} 作为主要事件数据")
                        storage_manager.store_events(df)
                        break
            else:
                print("❌ 事件数据字典为空")
                return False
        else:
            storage_manager.store_events(events_data)
        
        storage_manager.store_users(user_data)
        storage_manager.store_sessions(session_data)
        
        # 4. 验证存储的数据
        print("4. 验证存储的数据...")
        stored_events = storage_manager.get_data('events')
        
        if stored_events is not None and not stored_events.empty:
            print(f"✅ 存储验证成功，事件数: {len(stored_events)}")
        else:
            print("❌ 存储验证失败，数据为空")
            return False
        
        # 5. 测试集成管理器
        print("5. 测试集成管理器...")
        config = WorkflowConfig(
            enable_parallel_processing=True,
            max_workers=2,
            memory_limit_gb=4.0,
            timeout_minutes=10,
            enable_caching=True,
            cache_ttl_hours=24,
            enable_monitoring=True,
            auto_cleanup=True
        )
        
        integration_manager = IntegrationManager(config)
        
        # 6. 测试单个分析
        print("6. 测试事件分析...")
        try:
            result = integration_manager.execute_single_analysis(
                analysis_type='event_analysis',
                data_manager=storage_manager,
                analysis_params={'time_granularity': 'day'}
            )
            
            if result:
                print(f"✅ 事件分析成功，结果类型: {type(result)}")
            else:
                print("❌ 事件分析返回空结果")
                
        except Exception as e:
            print(f"❌ 事件分析失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n🎉 数据流程测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 数据流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_streamlit_data_flow()