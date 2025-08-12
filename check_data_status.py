#!/usr/bin/env python3
"""
检查数据状态和留存分析要求
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_sample_data():
    """检查示例数据"""
    try:
        print("=== 检查示例数据状态 ===")
        
        # 检查是否有示例数据文件
        data_files = [
            "data/events_ga4.ndjson",
            "data/uploads/events_ga4.ndjson",
            "data/processed/events_ga4.ndjson"
        ]
        
        found_file = None
        for file_path in data_files:
            if Path(file_path).exists():
                found_file = file_path
                break
        
        if not found_file:
            print("❌ 没有找到数据文件")
            print("可用的数据文件路径:")
            for file_path in data_files:
                print(f"  - {file_path}")
            return create_sample_data()
        
        print(f"✅ 找到数据文件: {found_file}")
        
        # 读取和分析数据
        return analyze_data_file(found_file)
        
    except Exception as e:
        print(f"❌ 检查数据失败: {e}")
        return False

def analyze_data_file(file_path):
    """分析数据文件"""
    try:
        print(f"\n=== 分析数据文件: {file_path} ===")
        
        # 读取NDJSON文件
        events = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except json.JSONDecodeError as e:
                        print(f"警告: 第{line_num}行JSON解析失败: {e}")
                        continue
        
        if not events:
            print("❌ 数据文件为空")
            return False
        
        print(f"📊 总事件数: {len(events)}")
        
        # 分析用户数据
        users = set()
        dates = set()
        event_types = {}
        
        for event in events:
            # 提取用户ID
            user_id = event.get('user_pseudo_id') or event.get('user_id')
            if user_id:
                users.add(user_id)
            
            # 提取日期
            event_date = event.get('event_date')
            if event_date:
                dates.add(event_date)
            
            # 统计事件类型
            event_name = event.get('event_name', 'unknown')
            event_types[event_name] = event_types.get(event_name, 0) + 1
        
        print(f"👥 独立用户数: {len(users)}")
        print(f"📅 数据天数: {len(dates)}")
        print(f"🎯 事件类型数: {len(event_types)}")
        
        # 显示前5个事件类型
        print("\n前5个事件类型:")
        sorted_events = sorted(event_types.items(), key=lambda x: x[1], reverse=True)
        for event_name, count in sorted_events[:5]:
            print(f"  {event_name}: {count}")
        
        # 检查留存分析要求
        print(f"\n=== 留存分析要求检查 ===")
        
        min_users_required = 100  # 最小用户数要求
        min_days_required = 7     # 最小天数要求
        
        print(f"最小用户数要求: {min_users_required}")
        print(f"实际用户数: {len(users)}")
        print(f"用户数检查: {'✅ 通过' if len(users) >= min_users_required else '❌ 不足'}")
        
        print(f"最小天数要求: {min_days_required}")
        print(f"实际天数: {len(dates)}")
        print(f"天数检查: {'✅ 通过' if len(dates) >= min_days_required else '❌ 不足'}")
        
        # 检查数据质量
        print(f"\n=== 数据质量检查 ===")
        
        users_with_multiple_events = 0
        for user_id in users:
            user_events = [e for e in events if e.get('user_pseudo_id') == user_id or e.get('user_id') == user_id]
            if len(user_events) > 1:
                users_with_multiple_events += 1
        
        print(f"有多次事件的用户数: {users_with_multiple_events}")
        print(f"多事件用户比例: {users_with_multiple_events/len(users)*100:.1f}%")
        
        # 建议
        print(f"\n=== 建议 ===")
        if len(users) < min_users_required:
            print("⚠️  用户数不足，建议:")
            print("   1. 增加更多的示例数据")
            print("   2. 降低留存分析的最小队列大小设置")
            print("   3. 使用生成的测试数据")
        
        if len(dates) < min_days_required:
            print("⚠️  数据天数不足，建议:")
            print("   1. 增加更多天的数据")
            print("   2. 生成跨越更长时间的测试数据")
        
        if users_with_multiple_events < len(users) * 0.5:
            print("⚠️  用户行为数据不足，建议:")
            print("   1. 确保用户有多次访问记录")
            print("   2. 生成更丰富的用户行为数据")
        
        return len(users) >= min_users_required and len(dates) >= min_days_required
        
    except Exception as e:
        print(f"❌ 分析数据文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_data():
    """创建示例数据"""
    try:
        print("\n=== 创建示例数据 ===")
        
        # 确保数据目录存在
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # 生成示例数据
        sample_events = []
        
        # 生成30天的数据
        base_date = datetime.now() - timedelta(days=30)
        
        # 生成500个用户
        for user_id in range(1, 501):
            user_pseudo_id = f"user_{user_id:04d}"
            
            # 每个用户生成1-10个事件
            import random
            num_events = random.randint(1, 10)
            
            for event_num in range(num_events):
                # 随机选择日期
                days_offset = random.randint(0, 29)
                event_date = base_date + timedelta(days=days_offset)
                
                # 随机选择事件类型
                event_types = ['page_view', 'sign_up', 'login', 'purchase', 'search', 'add_to_cart']
                event_name = random.choice(event_types)
                
                # 创建事件
                event = {
                    "event_date": event_date.strftime("%Y%m%d"),
                    "event_timestamp": int(event_date.timestamp() * 1000000),
                    "event_name": event_name,
                    "user_pseudo_id": user_pseudo_id,
                    "ga_session_id": f"session_{user_id}_{event_num}",
                    "platform": random.choice(["web", "mobile", "tablet"]),
                    "event_params": {
                        "page_title": f"Page {random.randint(1, 10)}",
                        "page_location": f"https://example.com/page{random.randint(1, 10)}"
                    }
                }
                
                sample_events.append(event)
        
        # 保存到文件
        output_file = data_dir / "events_ga4.ndjson"
        with open(output_file, 'w', encoding='utf-8') as f:
            for event in sample_events:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        print(f"✅ 创建示例数据成功: {output_file}")
        print(f"📊 生成事件数: {len(sample_events)}")
        print(f"👥 用户数: 500")
        print(f"📅 数据天数: 30")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建示例数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("数据状态检查工具")
    print("=" * 50)
    
    # 检查现有数据
    if not check_sample_data():
        print("\n数据检查未通过，请:")
        print("1. 上传有效的GA4数据文件")
        print("2. 或者运行此脚本生成示例数据")
        print("3. 调整留存分析的配置参数")
    else:
        print("\n✅ 数据检查通过，可以进行留存分析")

if __name__ == "__main__":
    main()