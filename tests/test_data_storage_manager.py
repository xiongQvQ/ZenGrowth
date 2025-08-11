"""
数据存储管理器单元测试

测试DataStorageManager类的所有功能，包括数据存储、检索、查询和过滤。
"""

import unittest
import pandas as pd
import tempfile
import os
from datetime import datetime, timedelta
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.data_storage_manager import DataStorageManager, StorageStats


class TestDataStorageManager(unittest.TestCase):
    """数据存储管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.storage = DataStorageManager()
        
        # 创建测试事件数据
        self.sample_events = pd.DataFrame([
            {
                'user_pseudo_id': 'user_001',
                'event_name': 'page_view',
                'event_timestamp': 1750980893000000,
                'event_date': '20250626',
                'platform': 'WEB',
                'device_category': 'desktop'
            },
            {
                'user_pseudo_id': 'user_001',
                'event_name': 'sign_up',
                'event_timestamp': 1750980894000000,
                'event_date': '20250626',
                'platform': 'WEB',
                'device_category': 'desktop'
            },
            {
                'user_pseudo_id': 'user_002',
                'event_name': 'page_view',
                'event_timestamp': 1750980895000000,
                'event_date': '20250626',
                'platform': 'ANDROID',
                'device_category': 'mobile'
            }
        ])
        
        # 创建测试用户数据
        self.sample_users = pd.DataFrame([
            {
                'user_pseudo_id': 'user_001',
                'platform': 'WEB',
                'device_category': 'desktop',
                'geo_country': 'US',
                'total_events': 2
            },
            {
                'user_pseudo_id': 'user_002',
                'platform': 'ANDROID',
                'device_category': 'mobile',
                'geo_country': 'CN',
                'total_events': 1
            }
        ])
        
        # 创建测试会话数据
        self.sample_sessions = pd.DataFrame([
            {
                'session_id': 'session_001',
                'user_pseudo_id': 'user_001',
                'duration_seconds': 300,
                'event_count': 2,
                'conversions': 1
            },
            {
                'session_id': 'session_002',
                'user_pseudo_id': 'user_002',
                'duration_seconds': 150,
                'event_count': 1,
                'conversions': 0
            }
        ])
        
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.storage._events_data, pd.DataFrame)
        self.assertIsInstance(self.storage._users_data, pd.DataFrame)
        self.assertIsInstance(self.storage._sessions_data, pd.DataFrame)
        self.assertIsInstance(self.storage._events_by_type, dict)
        self.assertTrue(self.storage._events_data.empty)
        
    def test_store_events_success(self):
        """测试成功存储事件数据"""
        self.storage.store_events(self.sample_events)
        
        # 验证数据存储
        self.assertEqual(len(self.storage._events_data), 3)
        self.assertEqual(len(self.storage._events_by_type), 2)  # page_view 和 sign_up
        self.assertIn('page_view', self.storage._events_by_type)
        self.assertIn('sign_up', self.storage._events_by_type)
        
        # 验证按类型分组
        page_view_events = self.storage._events_by_type['page_view']
        self.assertEqual(len(page_view_events), 2)
        
        sign_up_events = self.storage._events_by_type['sign_up']
        self.assertEqual(len(sign_up_events), 1)
        
    def test_store_events_empty_data(self):
        """测试存储空事件数据"""
        empty_df = pd.DataFrame()
        self.storage.store_events(empty_df)
        self.assertTrue(self.storage._events_data.empty)
        
    def test_store_events_missing_columns(self):
        """测试存储缺少必需列的事件数据"""
        invalid_events = pd.DataFrame([{'invalid_column': 'value'}])
        
        with self.assertRaises(ValueError) as context:
            self.storage.store_events(invalid_events)
        self.assertIn('缺少必需列', str(context.exception))
        
    def test_store_users_success(self):
        """测试成功存储用户数据"""
        self.storage.store_users(self.sample_users)
        
        self.assertEqual(len(self.storage._users_data), 2)
        self.assertIn('user_pseudo_id', self.storage._users_data.columns)
        
    def test_store_sessions_success(self):
        """测试成功存储会话数据"""
        self.storage.store_sessions(self.sample_sessions)
        
        self.assertEqual(len(self.storage._sessions_data), 2)
        self.assertIn('session_id', self.storage._sessions_data.columns)
        self.assertIn('user_pseudo_id', self.storage._sessions_data.columns)
        
    def test_get_data_events(self):
        """测试获取事件数据"""
        self.storage.store_events(self.sample_events)
        
        events = self.storage.get_data('events')
        self.assertEqual(len(events), 3)
        self.assertIn('event_name', events.columns)
        
    def test_get_data_users(self):
        """测试获取用户数据"""
        self.storage.store_users(self.sample_users)
        
        users = self.storage.get_data('users')
        self.assertEqual(len(users), 2)
        self.assertIn('user_pseudo_id', users.columns)
        
    def test_get_data_sessions(self):
        """测试获取会话数据"""
        self.storage.store_sessions(self.sample_sessions)
        
        sessions = self.storage.get_data('sessions')
        self.assertEqual(len(sessions), 2)
        self.assertIn('session_id', sessions.columns)
        
    def test_get_data_event_type(self):
        """测试获取特定事件类型数据"""
        self.storage.store_events(self.sample_events)
        
        page_views = self.storage.get_data('event_type:page_view')
        self.assertEqual(len(page_views), 2)
        
        sign_ups = self.storage.get_data('event_type:sign_up')
        self.assertEqual(len(sign_ups), 1)
        
    def test_get_data_with_filters(self):
        """测试带过滤条件获取数据"""
        self.storage.store_events(self.sample_events)
        
        # 测试等值过滤
        web_events = self.storage.get_data('events', {'platform': 'WEB'})
        self.assertEqual(len(web_events), 2)
        
        # 测试IN过滤
        specific_users = self.storage.get_data('events', {'user_pseudo_id': ['user_001']})
        self.assertEqual(len(specific_users), 2)
        
    def test_apply_complex_filter(self):
        """测试复杂过滤条件"""
        self.storage.store_events(self.sample_events)
        
        # 测试大于条件
        recent_events = self.storage.get_data('events', {
            'event_timestamp': {'gt': 1750980893000000}
        })
        self.assertEqual(len(recent_events), 2)
        
        # 测试包含条件
        page_events = self.storage.get_data('events', {
            'event_name': {'contains': 'page'}
        })
        self.assertEqual(len(page_events), 2)
        
    def test_query_events(self):
        """测试查询事件数据"""
        self.storage.store_events(self.sample_events)
        
        # 按用户查询
        user_events = self.storage.query_events(user_ids=['user_001'])
        self.assertEqual(len(user_events), 2)
        
        # 按事件类型查询
        page_views = self.storage.query_events(event_types=['page_view'])
        self.assertEqual(len(page_views), 2)
        
        # 限制返回数量
        limited_events = self.storage.query_events(limit=1)
        self.assertEqual(len(limited_events), 1)
        
    def test_query_users(self):
        """测试查询用户数据"""
        self.storage.store_users(self.sample_users)
        
        # 按平台查询
        web_users = self.storage.query_users(platforms=['WEB'])
        self.assertEqual(len(web_users), 1)
        
        # 按设备类别查询
        mobile_users = self.storage.query_users(device_categories=['mobile'])
        self.assertEqual(len(mobile_users), 1)
        
    def test_query_sessions(self):
        """测试查询会话数据"""
        self.storage.store_sessions(self.sample_sessions)
        
        # 按最小时长查询
        long_sessions = self.storage.query_sessions(min_duration=200)
        self.assertEqual(len(long_sessions), 1)
        
        # 按转化查询
        conversion_sessions = self.storage.query_sessions(has_conversions=True)
        self.assertEqual(len(conversion_sessions), 1)
        
        no_conversion_sessions = self.storage.query_sessions(has_conversions=False)
        self.assertEqual(len(no_conversion_sessions), 1)
        
    def test_get_statistics(self):
        """测试获取统计信息"""
        self.storage.store_events(self.sample_events)
        self.storage.store_users(self.sample_users)
        self.storage.store_sessions(self.sample_sessions)
        
        stats = self.storage.get_statistics()
        
        self.assertIsInstance(stats, StorageStats)
        self.assertEqual(stats.total_events, 3)
        self.assertEqual(stats.total_users, 2)
        self.assertEqual(stats.total_sessions, 2)
        self.assertGreater(stats.memory_usage_mb, 0)
        self.assertIsInstance(stats.last_updated, datetime)
        
    def test_clear_data(self):
        """测试清空数据"""
        self.storage.store_events(self.sample_events)
        self.storage.store_users(self.sample_users)
        
        # 清空特定类型数据
        self.storage.clear_data('events')
        self.assertTrue(self.storage._events_data.empty)
        self.assertFalse(self.storage._users_data.empty)
        
        # 清空所有数据
        self.storage.clear_data('all')
        self.assertTrue(self.storage._events_data.empty)
        self.assertTrue(self.storage._users_data.empty)
        
    def test_export_import_data(self):
        """测试数据导出和导入"""
        self.storage.store_events(self.sample_events)
        
        # 测试CSV导出导入
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            try:
                # 导出
                self.storage.export_data('events', tmp_file.name, 'csv')
                self.assertTrue(os.path.exists(tmp_file.name))
                
                # 清空数据
                self.storage.clear_data('events')
                self.assertTrue(self.storage._events_data.empty)
                
                # 导入
                self.storage.import_data('events', tmp_file.name, 'csv')
                self.assertEqual(len(self.storage._events_data), 3)
                
            finally:
                if os.path.exists(tmp_file.name):
                    os.unlink(tmp_file.name)
                    
    def test_get_event_types(self):
        """测试获取事件类型"""
        self.storage.store_events(self.sample_events)
        
        event_types = self.storage.get_event_types()
        self.assertEqual(len(event_types), 2)
        self.assertIn('page_view', event_types)
        self.assertIn('sign_up', event_types)
        
    def test_get_counts(self):
        """测试获取计数"""
        self.storage.store_events(self.sample_events)
        self.storage.store_users(self.sample_users)
        self.storage.store_sessions(self.sample_sessions)
        
        self.assertEqual(self.storage.get_user_count(), 2)
        self.assertEqual(self.storage.get_event_count(), 3)
        self.assertEqual(self.storage.get_event_count('page_view'), 2)
        self.assertEqual(self.storage.get_session_count(), 2)
        
    def test_aggregate_events(self):
        """测试事件数据聚合"""
        self.storage.store_events(self.sample_events)
        
        # 按事件名称聚合
        agg_result = self.storage.aggregate_events(
            group_by=['event_name'],
            agg_functions={'user_pseudo_id': 'count'}
        )
        
        self.assertEqual(len(agg_result), 2)
        self.assertIn('event_name', agg_result.columns)
        self.assertIn('user_pseudo_id', agg_result.columns)
        
    def test_get_data_summary(self):
        """测试获取数据摘要"""
        self.storage.store_events(self.sample_events)
        self.storage.store_users(self.sample_users)
        self.storage.store_sessions(self.sample_sessions)
        
        summary = self.storage.get_data_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('events', summary)
        self.assertIn('users', summary)
        self.assertIn('sessions', summary)
        self.assertIn('storage', summary)
        
        # 验证事件摘要
        events_summary = summary['events']
        self.assertEqual(events_summary['total_count'], 3)
        self.assertEqual(len(events_summary['event_types']), 2)
        
        # 验证用户摘要
        users_summary = summary['users']
        self.assertEqual(users_summary['total_count'], 2)
        
        # 验证会话摘要
        sessions_summary = summary['sessions']
        self.assertEqual(sessions_summary['total_count'], 2)
        self.assertGreater(sessions_summary['avg_duration'], 0)
        
    def test_invalid_data_type(self):
        """测试无效数据类型"""
        with self.assertRaises(ValueError):
            self.storage.get_data('invalid_type')
            
        with self.assertRaises(ValueError):
            self.storage.clear_data('invalid_type')
            
    def test_thread_safety(self):
        """测试线程安全性"""
        import threading
        import time
        
        def store_data():
            for i in range(10):
                events = self.sample_events.copy()
                events['user_pseudo_id'] = f'user_{i}'
                self.storage.store_events(events)
                time.sleep(0.001)
                
        # 创建多个线程同时存储数据
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=store_data)
            threads.append(thread)
            thread.start()
            
        # 等待所有线程完成
        for thread in threads:
            thread.join()
            
        # 验证数据完整性
        stats = self.storage.get_statistics()
        self.assertGreater(stats.total_events, 0)


if __name__ == '__main__':
    # 创建测试目录
    os.makedirs('tests', exist_ok=True)
    
    # 运行测试
    unittest.main(verbosity=2)