#!/usr/bin/env python3
"""
测试事件提取功能
"""

from tools.ga4_data_parser import GA4DataParser
from pathlib import Path

def test_extract_events():
    """测试事件提取"""
    try:
        print("🔍 测试事件提取...")
        
        # 1. 解析数据
        data_file = Path("data/events_ga4.ndjson")
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        
        print(f"原始数据: {len(raw_data)} 行")
        
        # 2. 提取事件数据
        print("提取事件数据...")
        events_data = parser.extract_events(raw_data)
        
        print(f"提取结果类型: {type(events_data)}")
        
        if isinstance(events_data, dict):
            print("事件数据是字典:")
            for key, value in events_data.items():
                print(f"  {key}: {type(value)} - {len(value) if hasattr(value, '__len__') else 'N/A'}")
        else:
            print(f"事件数据长度: {len(events_data)}")
        
        return events_data
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_extract_events()