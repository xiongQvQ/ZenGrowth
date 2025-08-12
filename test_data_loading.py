#!/usr/bin/env python3
"""
测试数据加载功能
"""

import pandas as pd
from pathlib import Path
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager

def test_data_loading():
    """测试数据加载"""
    try:
        print("🔍 测试数据加载...")
        
        # 1. 检查数据文件
        data_file = Path("data/events_ga4.ndjson")
        if not data_file.exists():
            print("❌ 数据文件不存在")
            return False
        
        print(f"✅ 数据文件存在: {data_file}")
        
        # 2. 解析数据
        print("📊 解析数据...")
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        
        print(f"✅ 解析成功，事件数: {len(raw_data)}")
        print(f"数据类型: {type(raw_data)}")
        print(f"列名: {list(raw_data.columns)}")
        
        # 3. 检查数据内容
        print("\n📋 数据样本:")
        print(raw_data.head(2))
        
        # 4. 测试存储管理器
        print("\n💾 测试存储管理器...")
        storage_manager = DataStorageManager()
        storage_manager.store_events(raw_data)
        
        # 5. 从存储管理器获取数据
        print("📤 从存储管理器获取数据...")
        stored_events = storage_manager.get_data('events')
        
        if stored_events is not None and not stored_events.empty:
            print(f"✅ 存储成功，存储的事件数: {len(stored_events)}")
            print(f"存储数据类型: {type(stored_events)}")
        else:
            print("❌ 存储的数据为空")
            return False
        
        # 6. 检查用户数据
        unique_users = raw_data['user_pseudo_id'].nunique()
        print(f"👥 独立用户数: {unique_users}")
        
        # 7. 检查事件类型
        event_types = raw_data['event_name'].value_counts()
        print(f"🎯 事件类型分布:")
        print(event_types.head())
        
        print("\n🎉 数据加载测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 数据加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_data_loading()