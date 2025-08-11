"""
数据存储管理器集成测试

测试DataStorageManager与GA4DataParser的集成使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager
from tools.data_cleaner import DataCleaner

def test_storage_integration():
    """测试存储管理器集成功能"""
    
    print("=== 数据存储管理器集成测试 ===\n")
    
    # 初始化组件
    parser = GA4DataParser()
    storage = DataStorageManager()
    cleaner = DataCleaner()
    
    # 1. 解析和存储事件数据
    print("1. 解析和存储事件数据...")
    try:
        # 解析GA4数据
        raw_data = parser.parse_ndjson('data/events_ga4.ndjson')
        cleaned_data = cleaner.clean_dataframe(raw_data)
        events_by_type = parser.extract_events(cleaned_data)
        
        # 存储事件数据
        storage.store_events(cleaned_data)
        
        print(f"   ✓ 成功存储 {len(cleaned_data)} 条事件数据")
        print(f"   ✓ 事件类型: {storage.get_event_types()}")
        
    except Exception as e:
        print(f"   ✗ 事件数据存储失败: {e}")
        return
    
    # 2. 存储用户数据
    print("\n2. 存储用户数据...")
    try:
        user_data = parser.extract_user_properties(cleaned_data)
        storage.store_users(user_data)
        
        print(f"   ✓ 成功存储 {len(user_data)} 个用户数据")
        
    except Exception as e:
        print(f"   ✗ 用户数据存储失败: {e}")
    
    # 3. 存储会话数据
    print("\n3. 存储会话数据...")
    try:
        session_data = parser.extract_sessions(cleaned_data)
        storage.store_sessions(session_data)
        
        print(f"   ✓ 成功存储 {len(session_data)} 个会话数据")
        
    except Exception as e:
        print(f"   ✗ 会话数据存储失败: {e}")
    
    # 4. 测试数据查询功能
    print("\n4. 测试数据查询功能...")
    try:
        # 查询特定用户的事件
        user_events = storage.query_events(user_ids=['ps_af7ba80a-6830-548c-a986-e50e2bd4bdbf'])
        print(f"   ✓ 特定用户事件: {len(user_events)} 条")
        
        # 查询特定事件类型
        page_views = storage.query_events(event_types=['page_view'])
        print(f"   ✓ 页面浏览事件: {len(page_views)} 条")
        
        # 查询Web平台用户
        web_users = storage.query_users(platforms=['WEB'])
        print(f"   ✓ Web平台用户: {len(web_users)} 个")
        
        # 查询长会话
        long_sessions = storage.query_sessions(min_duration=1000)
        print(f"   ✓ 长会话(>1000秒): {len(long_sessions)} 个")
        
    except Exception as e:
        print(f"   ✗ 数据查询失败: {e}")
    
    # 5. 测试数据过滤功能
    print("\n5. 测试数据过滤功能...")
    try:
        # 复杂过滤条件
        recent_events = storage.get_data('events', {
            'event_timestamp': {'gt': 1750980000000000},
            'platform': 'WEB'
        })
        print(f"   ✓ 最近的Web事件: {len(recent_events)} 条")
        
        # 获取特定事件类型数据
        sign_up_events = storage.get_data('event_type:sign_up')
        print(f"   ✓ 注册事件: {len(sign_up_events)} 条")
        
    except Exception as e:
        print(f"   ✗ 数据过滤失败: {e}")
    
    # 6. 测试数据聚合功能
    print("\n6. 测试数据聚合功能...")
    try:
        # 按事件类型聚合
        event_counts = storage.aggregate_events(
            group_by=['event_name'],
            agg_functions={'user_pseudo_id': 'count'}
        )
        print(f"   ✓ 事件类型聚合: {len(event_counts)} 种事件")
        print(f"   ✓ 热门事件: {event_counts.head(3).to_dict('records')}")
        
        # 按平台聚合
        platform_stats = storage.aggregate_events(
            group_by=['platform'],
            agg_functions={'user_pseudo_id': 'nunique', 'event_name': 'count'}
        )
        print(f"   ✓ 平台统计: {platform_stats.to_dict('records')}")
        
    except Exception as e:
        print(f"   ✗ 数据聚合失败: {e}")
    
    # 7. 获取存储统计信息
    print("\n7. 存储统计信息...")
    try:
        stats = storage.get_statistics()
        print(f"   ✓ 总事件数: {stats.total_events}")
        print(f"   ✓ 总用户数: {stats.total_users}")
        print(f"   ✓ 总会话数: {stats.total_sessions}")
        print(f"   ✓ 内存使用: {stats.memory_usage_mb:.2f} MB")
        print(f"   ✓ 最后更新: {stats.last_updated}")
        
    except Exception as e:
        print(f"   ✗ 获取统计信息失败: {e}")
    
    # 8. 获取数据摘要
    print("\n8. 数据摘要信息...")
    try:
        summary = storage.get_data_summary()
        
        print("   ✓ 事件摘要:")
        events_summary = summary['events']
        print(f"     - 总数: {events_summary['total_count']}")
        print(f"     - 类型: {events_summary['event_types'][:5]}...")
        print(f"     - 热门事件: {list(events_summary['top_events'].keys())[:3]}")
        
        print("   ✓ 用户摘要:")
        users_summary = summary['users']
        print(f"     - 总数: {users_summary['total_count']}")
        print(f"     - 平台分布: {users_summary['platforms']}")
        
        print("   ✓ 会话摘要:")
        sessions_summary = summary['sessions']
        print(f"     - 总数: {sessions_summary['total_count']}")
        print(f"     - 平均时长: {sessions_summary['avg_duration']:.1f} 秒")
        print(f"     - 转化率: {sessions_summary['conversion_rate']:.2%}")
        
    except Exception as e:
        print(f"   ✗ 获取数据摘要失败: {e}")
    
    # 9. 测试数据导出功能
    print("\n9. 测试数据导出功能...")
    try:
        import tempfile
        
        # 导出事件数据
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            storage.export_data('events', tmp_file.name, 'csv')
            print(f"   ✓ 事件数据导出到: {tmp_file.name}")
            
            # 验证文件存在
            if os.path.exists(tmp_file.name):
                file_size = os.path.getsize(tmp_file.name)
                print(f"   ✓ 导出文件大小: {file_size} 字节")
                os.unlink(tmp_file.name)  # 清理临时文件
                
    except Exception as e:
        print(f"   ✗ 数据导出失败: {e}")
    
    print("\n=== 集成测试完成 ===")

if __name__ == '__main__':
    test_storage_integration()