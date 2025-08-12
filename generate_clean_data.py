#!/usr/bin/env python3
"""
生成干净的测试数据
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_clean_test_data():
    """生成干净的测试数据"""
    try:
        print("生成干净的测试数据...")
        
        # 确保数据目录存在
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # 生成示例数据
        events = []
        base_date = datetime.now() - timedelta(days=30)
        
        # 生成500个用户，每个用户有多个事件
        for user_id in range(1, 501):
            user_pseudo_id = f"user_{user_id:04d}"
            
            # 每个用户生成3-15个事件
            num_events = random.randint(3, 15)
            
            for event_num in range(num_events):
                # 随机选择日期
                days_offset = random.randint(0, 29)
                event_date = base_date + timedelta(days=days_offset)
                
                # 随机选择事件类型
                event_types = ['page_view', 'sign_up', 'login', 'purchase', 'search', 'add_to_cart', 'view_item', 'select_item']
                event_name = random.choice(event_types)
                
                # 创建完整的事件结构（符合GA4DataParser的要求）
                event = {
                    "event_date": event_date.strftime("%Y%m%d"),
                    "event_timestamp": int(event_date.timestamp() * 1000000),
                    "event_name": event_name,
                    "event_params": [
                        {"key": "ga_session_id", "value": {"string_value": f"session_{user_id}_{event_num}"}},
                        {"key": "page_title", "value": {"string_value": f"Page {random.randint(1, 10)}"}},
                        {"key": "page_location", "value": {"string_value": f"https://example.com/page{random.randint(1, 10)}"}}
                    ],
                    "user_pseudo_id": user_pseudo_id,
                    "user_id": user_pseudo_id,
                    "user_properties": [
                        {"key": "user_type", "value": {"string_value": random.choice(["new", "returning"])}},
                        {"key": "country", "value": {"string_value": random.choice(["US", "CN", "JP", "UK", "DE"])}}
                    ],
                    "device": {
                        "category": random.choice(["desktop", "mobile", "tablet"]),
                        "operating_system": random.choice(["Windows", "macOS", "iOS", "Android"]),
                        "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"])
                    },
                    "geo": {
                        "country": random.choice(["US", "CN", "JP", "UK", "DE"]),
                        "city": f"City_{random.randint(1, 100)}"
                    },
                    "traffic_source": {
                        "source": random.choice(["google", "direct", "facebook", "twitter"]),
                        "medium": random.choice(["organic", "cpc", "social", "referral"])
                    },
                    "platform": random.choice(["web", "mobile", "tablet"]),
                    "stream_id": "123456789",
                    "user_ltv": {
                        "revenue": random.uniform(0, 1000),
                        "currency": "USD"
                    }
                }
                
                events.append(event)
        
        # 保存到文件
        output_file = data_dir / "events_ga4.ndjson"
        with open(output_file, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        print(f"✅ 生成干净数据成功: {output_file}")
        print(f"📊 生成事件数: {len(events)}")
        print(f"👥 用户数: 500")
        print(f"📅 数据天数: 30")
        
        return True
        
    except Exception as e:
        print(f"❌ 生成数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_clean_test_data()