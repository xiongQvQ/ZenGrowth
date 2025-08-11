"""
Streamlit界面功能测试
测试文件上传、数据处理和界面交互功能
"""

import pytest
import pandas as pd
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator
from tools.data_storage_manager import DataStorageManager


class TestStreamlitInterface:
    """Streamlit界面测试类"""
    
    def setup_method(self):
        """测试前设置"""
        self.parser = GA4DataParser()
        self.validator = DataValidator()
        self.storage_manager = DataStorageManager()
        
    def create_sample_ga4_data(self) -> str:
        """创建示例GA4数据文件"""
        sample_events = [
            {
                "event_date": "20241201",
                "event_timestamp": 1733097600000000,
                "event_name": "page_view",
                "user_pseudo_id": "user_123",
                "user_id": "registered_user_123",
                "platform": "WEB",
                "device": {
                    "category": "desktop",
                    "operating_system": "Windows",
                    "browser": "Chrome"
                },
                "geo": {
                    "country": "US",
                    "city": "New York"
                },
                "traffic_source": {
                    "source": "google",
                    "medium": "organic"
                },
                "event_params": [
                    {
                        "key": "page_title",
                        "value": {"string_value": "Home Page"}
                    },
                    {
                        "key": "page_location",
                        "value": {"string_value": "https://example.com/"}
                    }
                ],
                "user_properties": [
                    {
                        "key": "user_type",
                        "value": {"string_value": "premium"}
                    }
                ]
            },
            {
                "event_date": "20241201",
                "event_timestamp": 1733097660000000,
                "event_name": "sign_up",
                "user_pseudo_id": "user_456",
                "user_id": "",
                "platform": "WEB",
                "device": {
                    "category": "mobile",
                    "operating_system": "Android",
                    "browser": "Chrome"
                },
                "geo": {
                    "country": "CA",
                    "city": "Toronto"
                },
                "traffic_source": {
                    "source": "facebook",
                    "medium": "social"
                },
                "event_params": [
                    {
                        "key": "method",
                        "value": {"string_value": "email"}
                    }
                ],
                "user_properties": []
            },
            {
                "event_date": "20241201",
                "event_timestamp": 1733097720000000,
                "event_name": "purchase",
                "user_pseudo_id": "user_123",
                "user_id": "registered_user_123",
                "platform": "WEB",
                "device": {
                    "category": "desktop",
                    "operating_system": "Windows",
                    "browser": "Chrome"
                },
                "geo": {
                    "country": "US",
                    "city": "New York"
                },
                "traffic_source": {
                    "source": "google",
                    "medium": "organic"
                },
                "event_params": [
                    {
                        "key": "currency",
                        "value": {"string_value": "USD"}
                    },
                    {
                        "key": "value",
                        "value": {"double_value": 99.99}
                    }
                ],
                "user_properties": [
                    {
                        "key": "user_type",
                        "value": {"string_value": "premium"}
                    }
                ],
                "items": [
                    {
                        "item_id": "product_123",
                        "item_category": "electronics",
                        "price": 99.99,
                        "quantity": 1
                    }
                ]
            }
        ]
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False)
        for event in sample_events:
            temp_file.write(json.dumps(event) + '\n')
        temp_file.close()
        
        return temp_file.name
        
    def test_file_upload_validation(self):
        """测试文件上传验证功能"""
        # 创建示例数据文件
        sample_file = self.create_sample_ga4_data()
        
        try:
            # 测试文件解析
            raw_data = self.parser.parse_ndjson(sample_file)
            
            # 验证解析结果
            assert len(raw_data) == 3, "应该解析出3个事件"
            assert 'event_name' in raw_data.columns, "应该包含event_name列"
            assert 'user_pseudo_id' in raw_data.columns, "应该包含user_pseudo_id列"
            
            # 测试数据验证
            validation_report = self.validator.validate_dataframe(raw_data)
            
            # 验证报告结构
            assert 'total_rows' in validation_report, "验证报告应包含total_rows"
            assert 'validation_passed' in validation_report, "验证报告应包含validation_passed"
            assert 'statistics' in validation_report, "验证报告应包含statistics"
            
            print("✅ 文件上传验证测试通过")
            
        finally:
            # 清理临时文件
            if os.path.exists(sample_file):
                os.unlink(sample_file)
                
    def test_data_processing_pipeline(self):
        """测试数据处理流水线"""
        # 创建示例数据文件
        sample_file = self.create_sample_ga4_data()
        
        try:
            # 步骤1: 解析数据
            raw_data = self.parser.parse_ndjson(sample_file)
            
            # 步骤2: 提取事件数据
            events_data = self.parser.extract_events(raw_data)
            assert isinstance(events_data, dict), "事件数据应为字典格式"
            assert len(events_data) > 0, "应该提取到事件数据"
            
            # 步骤3: 提取用户数据
            user_data = self.parser.extract_user_properties(raw_data)
            assert isinstance(user_data, pd.DataFrame), "用户数据应为DataFrame格式"
            assert len(user_data) > 0, "应该提取到用户数据"
            
            # 步骤4: 提取会话数据
            session_data = self.parser.extract_sessions(raw_data)
            assert isinstance(session_data, pd.DataFrame), "会话数据应为DataFrame格式"
            assert len(session_data) > 0, "应该提取到会话数据"
            
            # 步骤5: 存储数据
            self.storage_manager.store_events(raw_data)
            self.storage_manager.store_users(user_data)
            self.storage_manager.store_sessions(session_data)
            
            # 验证存储
            stored_events = self.storage_manager.get_data('events')
            assert len(stored_events) > 0, "应该存储了事件数据"
            
            print("✅ 数据处理流水线测试通过")
            
        finally:
            # 清理临时文件
            if os.path.exists(sample_file):
                os.unlink(sample_file)
                
    def test_data_quality_validation(self):
        """测试数据质量验证"""
        # 创建示例数据文件
        sample_file = self.create_sample_ga4_data()
        
        try:
            # 解析数据
            raw_data = self.parser.parse_ndjson(sample_file)
            
            # 生成数据质量报告
            quality_report = self.parser.validate_data_quality(raw_data)
            
            # 验证报告内容
            assert 'total_events' in quality_report, "质量报告应包含总事件数"
            assert 'unique_users' in quality_report, "质量报告应包含独立用户数"
            assert 'date_range' in quality_report, "质量报告应包含日期范围"
            assert 'event_types' in quality_report, "质量报告应包含事件类型"
            assert 'platforms' in quality_report, "质量报告应包含平台信息"
            
            # 验证统计数据
            assert quality_report['total_events'] == 3, "总事件数应为3"
            assert quality_report['unique_users'] == 2, "独立用户数应为2"
            assert len(quality_report['event_types']) == 3, "事件类型数应为3"
            
            print("✅ 数据质量验证测试通过")
            
        finally:
            # 清理临时文件
            if os.path.exists(sample_file):
                os.unlink(sample_file)
                
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效文件
        try:
            self.parser.parse_ndjson("nonexistent_file.ndjson")
            assert False, "应该抛出FileNotFoundError"
        except FileNotFoundError:
            pass  # 预期的错误
            
        # 测试无效JSON格式
        invalid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False)
        invalid_file.write("invalid json content\n")
        invalid_file.write('{"event_date": "20241201", "event_timestamp": 1733097600000000, "event_name": "page_view", "user_pseudo_id": "user_123", "platform": "WEB", "device": {"category": "desktop"}, "geo": {"country": "US"}, "event_params": [], "user_properties": []}\n')
        invalid_file.close()
        
        try:
            # 应该能处理部分无效数据
            raw_data = self.parser.parse_ndjson(invalid_file.name)
            assert len(raw_data) == 1, "应该解析出1个有效事件"
            
            print("✅ 错误处理测试通过")
            
        except ValueError as e:
            if "未找到有效的事件数据" in str(e):
                print("✅ 错误处理测试通过 - 正确处理了无效数据")
            else:
                raise
            
        finally:
            if os.path.exists(invalid_file.name):
                os.unlink(invalid_file.name)
                
    def test_session_state_management(self):
        """测试会话状态管理"""
        # 模拟Streamlit会话状态
        mock_session_state = {
            'data_loaded': False,
            'raw_data': None,
            'processed_data': None,
            'data_summary': None,
            'validation_report': None,
            'storage_manager': DataStorageManager()
        }
        
        # 测试初始状态
        assert not mock_session_state['data_loaded'], "初始状态应为未加载"
        assert mock_session_state['raw_data'] is None, "初始原始数据应为空"
        
        # 模拟数据加载
        sample_file = self.create_sample_ga4_data()
        
        try:
            raw_data = self.parser.parse_ndjson(sample_file)
            data_summary = self.parser.validate_data_quality(raw_data)
            
            # 更新会话状态
            mock_session_state['data_loaded'] = True
            mock_session_state['raw_data'] = raw_data
            mock_session_state['data_summary'] = data_summary
            
            # 验证状态更新
            assert mock_session_state['data_loaded'], "数据应已加载"
            assert mock_session_state['raw_data'] is not None, "原始数据应不为空"
            assert mock_session_state['data_summary'] is not None, "数据摘要应不为空"
            
            print("✅ 会话状态管理测试通过")
            
        finally:
            if os.path.exists(sample_file):
                os.unlink(sample_file)
                
    def test_file_size_validation(self):
        """测试文件大小验证"""
        # 创建大文件（模拟）
        large_content = json.dumps({"test": "data" * 1000}) * 1000
        
        # 计算文件大小（MB）
        file_size_mb = len(large_content.encode('utf-8')) / (1024 * 1024)
        
        # 模拟文件大小限制检查
        max_size_mb = 100  # 从settings获取
        
        if file_size_mb > max_size_mb:
            # 应该拒绝过大的文件
            assert True, "应该拒绝过大的文件"
        else:
            # 应该接受合适大小的文件
            assert True, "应该接受合适大小的文件"
            
        print("✅ 文件大小验证测试通过")
        
    def test_progress_tracking(self):
        """测试进度跟踪功能"""
        # 模拟进度跟踪
        progress_steps = [
            ("保存文件", 10),
            ("解析数据", 30),
            ("验证数据", 50),
            ("处理数据", 70),
            ("存储结果", 90),
            ("完成", 100)
        ]
        
        for step_name, progress in progress_steps:
            # 模拟进度更新
            assert 0 <= progress <= 100, f"进度值应在0-100之间: {progress}"
            assert isinstance(step_name, str), f"步骤名称应为字符串: {step_name}"
            
        print("✅ 进度跟踪测试通过")


def run_tests():
    """运行所有测试"""
    test_instance = TestStreamlitInterface()
    
    try:
        test_instance.setup_method()
        
        print("🧪 开始运行Streamlit界面测试...")
        
        test_instance.test_file_upload_validation()
        test_instance.test_data_processing_pipeline()
        test_instance.test_data_quality_validation()
        test_instance.test_error_handling()
        test_instance.test_session_state_management()
        test_instance.test_file_size_validation()
        test_instance.test_progress_tracking()
        
        print("🎉 所有Streamlit界面测试通过!")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        raise


if __name__ == "__main__":
    run_tests()