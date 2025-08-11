"""
GA4数据解析器单元测试

测试GA4DataParser类的所有功能，包括NDJSON解析、数据提取、验证和清洗。
"""

import unittest
import pandas as pd
import json
import tempfile
import os
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.ga4_data_parser import GA4DataParser, EventData, UserSession


class TestGA4DataParser(unittest.TestCase):
    """GA4数据解析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.parser = GA4DataParser()
        
        # 创建测试数据
        self.sample_event = {
            "event_date": "20250626",
            "event_timestamp": 1750980893000000,
            "event_name": "page_view",
            "user_pseudo_id": "ps_test_user",
            "user_id": "u_0001",
            "platform": "WEB",
            "device": {
                "category": "desktop",
                "operating_system": "windows",
                "browser": "chrome"
            },
            "geo": {
                "country": "US",
                "city": "New York"
            },
            "traffic_source": {
                "name": "organic",
                "medium": "organic",
                "source": "google"
            },
            "event_params": [
                {
                    "key": "page",
                    "value": {"string_value": "home"}
                },
                {
                    "key": "ga_session_id",
                    "value": {"int_value": 123456789}
                }
            ],
            "user_properties": [
                {
                    "key": "channel",
                    "value": {
                        "set_timestamp_micros": 1750710869000000,
                        "string_value": "organic"
                    }
                }
            ]
        }
        
        # 创建临时测试文件
        self.test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False)
        self.test_file.write(json.dumps(self.sample_event) + '\n')
        
        # 添加第二个事件
        second_event = self.sample_event.copy()
        second_event['event_name'] = 'sign_up'
        second_event['event_timestamp'] = 1750980894000000
        self.test_file.write(json.dumps(second_event) + '\n')
        
        self.test_file.close()
        
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
            
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.parser.supported_events, set)
        self.assertIsInstance(self.parser.conversion_events, set)
        self.assertIn('page_view', self.parser.supported_events)
        self.assertIn('sign_up', self.parser.conversion_events)
        
    def test_parse_ndjson_success(self):
        """测试成功解析NDJSON文件"""
        df = self.parser.parse_ndjson(self.test_file.name)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertIn('event_name', df.columns)
        self.assertIn('user_pseudo_id', df.columns)
        self.assertEqual(df.iloc[0]['event_name'], 'page_view')
        self.assertEqual(df.iloc[1]['event_name'], 'sign_up')
        
    def test_parse_ndjson_file_not_found(self):
        """测试文件不存在的情况"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_ndjson('nonexistent_file.ndjson')
            
    def test_parse_ndjson_invalid_json(self):
        """测试无效JSON格式"""
        invalid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False)
        invalid_file.write('invalid json line\n')
        invalid_file.write(json.dumps(self.sample_event) + '\n')
        invalid_file.close()
        
        try:
            df = self.parser.parse_ndjson(invalid_file.name)
            self.assertEqual(len(df), 1)  # 应该只解析成功一行
        finally:
            os.unlink(invalid_file.name)
            
    def test_validate_event_structure_valid(self):
        """测试有效事件结构验证"""
        self.assertTrue(self.parser._validate_event_structure(self.sample_event))
        
    def test_validate_event_structure_invalid(self):
        """测试无效事件结构验证"""
        invalid_event = self.sample_event.copy()
        del invalid_event['event_name']
        self.assertFalse(self.parser._validate_event_structure(invalid_event))
        
        invalid_event2 = self.sample_event.copy()
        invalid_event2['device'] = 'not_a_dict'
        self.assertFalse(self.parser._validate_event_structure(invalid_event2))
        
    def test_extract_param_value(self):
        """测试参数值提取"""
        # 测试字符串值
        string_value = {"string_value": "test"}
        self.assertEqual(self.parser._extract_param_value(string_value), "test")
        
        # 测试整数值
        int_value = {"int_value": 123}
        self.assertEqual(self.parser._extract_param_value(int_value), 123)
        
        # 测试浮点数值
        double_value = {"double_value": 123.45}
        self.assertEqual(self.parser._extract_param_value(double_value), 123.45)
        
        # 测试非字典值
        self.assertEqual(self.parser._extract_param_value("direct_value"), "direct_value")
        
    def test_clean_event_data(self):
        """测试事件数据清洗"""
        df = pd.DataFrame([self.sample_event])
        cleaned_df = self.parser._clean_event_data(df)
        
        self.assertIn('event_datetime', cleaned_df.columns)
        self.assertIn('event_date_parsed', cleaned_df.columns)
        self.assertEqual(cleaned_df.iloc[0]['event_name'], 'page_view')  # 应该保持小写
        
    def test_extract_events(self):
        """测试事件数据提取"""
        df = self.parser.parse_ndjson(self.test_file.name)
        events_by_type = self.parser.extract_events(df)
        
        self.assertIsInstance(events_by_type, dict)
        self.assertIn('page_view', events_by_type)
        self.assertIn('sign_up', events_by_type)
        
        page_view_data = events_by_type['page_view']
        self.assertIn('param_page', page_view_data.columns)
        self.assertIn('param_ga_session_id', page_view_data.columns)
        
    def test_parse_event_params(self):
        """测试事件参数解析"""
        df = pd.DataFrame([self.sample_event])
        parsed_df = self.parser._parse_event_params(df)
        
        self.assertIn('param_page', parsed_df.columns)
        self.assertIn('param_ga_session_id', parsed_df.columns)
        self.assertEqual(parsed_df.iloc[0]['param_page'], 'home')
        self.assertEqual(parsed_df.iloc[0]['param_ga_session_id'], 123456789)
        
    def test_parse_user_properties(self):
        """测试用户属性解析"""
        df = pd.DataFrame([self.sample_event])
        parsed_df = self.parser._parse_user_properties(df)
        
        self.assertIn('user_channel', parsed_df.columns)
        self.assertEqual(parsed_df.iloc[0]['user_channel'], 'organic')
        
    def test_parse_items(self):
        """测试商品信息解析"""
        event_with_items = self.sample_event.copy()
        event_with_items['items'] = [
            {
                "item_id": "SKU-123",
                "item_category": "Electronics",
                "price": 99.99,
                "quantity": 1
            }
        ]
        
        df = pd.DataFrame([event_with_items])
        parsed_df = self.parser._parse_items(df)
        
        self.assertIn('item_ids', parsed_df.columns)
        self.assertIn('item_categories', parsed_df.columns)
        self.assertIn('item_prices', parsed_df.columns)
        self.assertIn('item_quantities', parsed_df.columns)
        
        self.assertEqual(parsed_df.iloc[0]['item_ids'], ['SKU-123'])
        self.assertEqual(parsed_df.iloc[0]['item_categories'], ['Electronics'])
        
    def test_extract_user_properties(self):
        """测试用户属性提取"""
        df = self.parser.parse_ndjson(self.test_file.name)
        df = self.parser._clean_event_data(df)
        df = self.parser._parse_event_params(df)
        
        user_props = self.parser.extract_user_properties(df)
        
        self.assertIsInstance(user_props, pd.DataFrame)
        self.assertIn('user_pseudo_id', user_props.columns)
        self.assertIn('platform', user_props.columns)
        self.assertIn('device_category', user_props.columns)
        self.assertIn('first_seen', user_props.columns)
        self.assertIn('last_seen', user_props.columns)
        
        self.assertEqual(len(user_props), 1)  # 只有一个用户
        self.assertEqual(user_props.iloc[0]['user_pseudo_id'], 'ps_test_user')
        
    def test_extract_sessions(self):
        """测试会话数据提取"""
        df = self.parser.parse_ndjson(self.test_file.name)
        df = self.parser._clean_event_data(df)
        df = self.parser._parse_event_params(df)
        
        sessions = self.parser.extract_sessions(df)
        
        self.assertIsInstance(sessions, pd.DataFrame)
        self.assertIn('session_id', sessions.columns)
        self.assertIn('user_pseudo_id', sessions.columns)
        self.assertIn('start_time', sessions.columns)
        self.assertIn('end_time', sessions.columns)
        self.assertIn('duration_seconds', sessions.columns)
        self.assertIn('event_count', sessions.columns)
        
        self.assertEqual(len(sessions), 1)  # 一个会话
        self.assertEqual(sessions.iloc[0]['event_count'], 2)  # 两个事件
        
    def test_validate_data_quality(self):
        """测试数据质量验证"""
        df = self.parser.parse_ndjson(self.test_file.name)
        df = self.parser._clean_event_data(df)
        
        quality_report = self.parser.validate_data_quality(df)
        
        self.assertIsInstance(quality_report, dict)
        self.assertIn('total_events', quality_report)
        self.assertIn('unique_users', quality_report)
        self.assertIn('date_range', quality_report)
        self.assertIn('event_types', quality_report)
        self.assertIn('data_issues', quality_report)
        
        self.assertEqual(quality_report['total_events'], 2)
        self.assertEqual(quality_report['unique_users'], 1)
        
    def test_clean_and_standardize(self):
        """测试数据清洗和标准化"""
        # 创建包含重复数据的DataFrame
        df = pd.DataFrame([self.sample_event, self.sample_event])  # 重复数据
        df = self.parser._clean_event_data(df)
        
        cleaned_df = self.parser.clean_and_standardize(df)
        
        self.assertEqual(len(cleaned_df), 1)  # 重复数据应该被移除
        self.assertIn('geo_country', cleaned_df.columns)
        self.assertIn('geo_city', cleaned_df.columns)
        self.assertIn('device_category', cleaned_df.columns)
        
        self.assertEqual(cleaned_df.iloc[0]['geo_country'], 'US')
        self.assertEqual(cleaned_df.iloc[0]['geo_city'], 'New York')


class TestEventDataModel(unittest.TestCase):
    """事件数据模型测试"""
    
    def test_event_data_creation(self):
        """测试事件数据模型创建"""
        event_data = EventData(
            event_date="20250626",
            event_timestamp=1750980893000000,
            event_name="page_view",
            user_pseudo_id="ps_test",
            user_id="u_001",
            platform="WEB",
            device={"category": "desktop"},
            geo={"country": "US"},
            traffic_source={"source": "google"},
            event_params=[],
            user_properties=[]
        )
        
        self.assertEqual(event_data.event_name, "page_view")
        self.assertEqual(event_data.user_pseudo_id, "ps_test")
        self.assertIsNone(event_data.items)


class TestUserSessionModel(unittest.TestCase):
    """用户会话模型测试"""
    
    def test_user_session_creation(self):
        """测试用户会话模型创建"""
        session = UserSession(
            session_id="session_123",
            user_id="u_001",
            user_pseudo_id="ps_test",
            start_time=datetime.now(),
            end_time=datetime.now(),
            events=[],
            duration=300,
            page_views=5,
            conversions=1,
            platform="WEB",
            device={"category": "desktop"},
            geo={"country": "US"}
        )
        
        self.assertEqual(session.session_id, "session_123")
        self.assertEqual(session.duration, 300)
        self.assertEqual(session.page_views, 5)


if __name__ == '__main__':
    # 创建测试目录
    os.makedirs('tests', exist_ok=True)
    
    # 运行测试
    unittest.main(verbosity=2)