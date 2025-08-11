"""
数据处理智能体测试模块

测试DataProcessingAgent的功能，包括GA4数据处理、验证和存储。
"""

import pytest
import pandas as pd
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from agents.data_processing_agent import (
    DataProcessingAgent, 
    GA4DataProcessingTool, 
    DataValidationTool, 
    DataStorageTool
)


class TestGA4DataProcessingTool:
    """测试GA4数据处理工具"""
    
    def setup_method(self):
        """测试前准备"""
        self.tool = GA4DataProcessingTool()
        
    def create_test_ga4_file(self, events_data):
        """创建测试用的GA4 NDJSON文件"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
        for event in events_data:
            temp_file.write(json.dumps(event) + '\n')
        temp_file.close()
        return temp_file.name
        
    def test_process_valid_ga4_data(self):
        """测试处理有效的GA4数据"""
        # 准备测试数据
        test_events = [
            {
                "event_date": "20240101",
                "event_timestamp": 1704067200000000,
                "event_name": "page_view",
                "user_pseudo_id": "user123",
                "user_id": "real_user123",
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
                "event_date": "20240101",
                "event_timestamp": 1704067260000000,
                "event_name": "purchase",
                "user_pseudo_id": "user123",
                "user_id": "real_user123",
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
                        "key": "value",
                        "value": {"double_value": 99.99}
                    }
                ],
                "user_properties": [],
                "items": [
                    {
                        "item_id": "product123",
                        "item_category": "electronics",
                        "price": 99.99,
                        "quantity": 1
                    }
                ]
            }
        ]
        
        # 创建临时文件
        test_file = self.create_test_ga4_file(test_events)
        
        try:
            # 执行处理
            result = self.tool._run(test_file)
            
            # 验证结果
            assert result['status'] == 'success'
            assert result['raw_data_count'] == 2
            assert result['processed_data_count'] > 0
            assert 'page_view' in result['events_by_type']
            assert 'purchase' in result['events_by_type']
            assert result['unique_users'] == 1
            assert result['validation_report'] is not None
            assert result['quality_report'] is not None
            assert result['data'] is not None
            
        finally:
            # 清理临时文件
            os.unlink(test_file)
            
    def test_process_invalid_file(self):
        """测试处理无效文件"""
        result = self.tool._run("nonexistent_file.ndjson")
        
        assert result['status'] == 'error'
        assert 'error_message' in result
        assert result['data'] is None
        
    def test_process_malformed_json(self):
        """测试处理格式错误的JSON"""
        # 创建包含错误JSON的文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
        temp_file.write('{"valid": "json"}\n')
        temp_file.write('invalid json line\n')
        temp_file.write('{"another": "valid"}\n')
        temp_file.close()
        
        try:
            result = self.tool._run(temp_file.name)
            
            # 应该能处理部分有效数据
            assert result['status'] == 'success'
            
        finally:
            os.unlink(temp_file.name)


class TestDataValidationTool:
    """测试数据验证工具"""
    
    def setup_method(self):
        """测试前准备"""
        self.tool = DataValidationTool()
        
    def test_validate_valid_data(self):
        """测试验证有效数据"""
        # 创建有效的测试数据
        test_data = pd.DataFrame([
            {
                'event_date': '20240101',
                'event_timestamp': 1704067200000000,
                'event_name': 'page_view',
                'user_pseudo_id': 'user123',
                'platform': 'WEB',
                'device': {'category': 'desktop'},
                'geo': {'country': 'US'},
                'event_params': [],
                'user_properties': []
            }
        ])
        
        result = self.tool._run(test_data)
        
        assert result['status'] == 'success'
        assert 'validation_report' in result
        assert 'sequence_report' in result
        assert 'suggestions' in result
        assert 'summary' in result
        
    def test_validate_invalid_data(self):
        """测试验证无效数据"""
        # 创建缺少必需字段的数据
        test_data = pd.DataFrame([
            {
                'event_name': 'page_view',
                'user_pseudo_id': 'user123'
                # 缺少其他必需字段
            }
        ])
        
        result = self.tool._run(test_data)
        
        assert result['status'] == 'success'
        assert result['summary']['total_errors'] > 0
        assert not result['summary']['validation_passed']
        
    def test_validate_empty_data(self):
        """测试验证空数据"""
        test_data = pd.DataFrame()
        
        result = self.tool._run(test_data)
        
        assert result['status'] == 'success'
        assert result['summary']['total_errors'] > 0


class TestDataStorageTool:
    """测试数据存储工具"""
    
    def setup_method(self):
        """测试前准备"""
        self.tool = DataStorageTool()
        
    @patch('agents.data_processing_agent.DataStorageManager')
    def test_store_processed_data(self, mock_storage_manager):
        """测试存储处理后的数据"""
        # 模拟存储管理器
        mock_manager = Mock()
        mock_storage_manager.return_value = mock_manager
        mock_manager.get_storage_statistics.return_value = {
            'total_events': 100,
            'total_users': 10,
            'total_sessions': 20
        }
        
        # 准备测试数据
        processed_data = {
            'data': {
                'events_by_type': {
                    'page_view': pd.DataFrame([{'event_name': 'page_view'}])
                },
                'user_properties': pd.DataFrame([{'user_id': 'user123'}]),
                'sessions': pd.DataFrame([{'session_id': 'session123'}]),
                'cleaned_data': pd.DataFrame([{'event_name': 'page_view'}])
            }
        }
        
        result = self.tool._run(processed_data)
        
        assert result['status'] == 'success'
        assert 'storage_stats' in result
        assert result['message'] == '数据存储完成'
        
        # 验证调用了存储方法
        mock_manager.store_events.assert_called()
        mock_manager.store_users.assert_called()
        mock_manager.store_sessions.assert_called()
        mock_manager.store_raw_data.assert_called()
        
    def test_store_invalid_data(self):
        """测试存储无效数据"""
        result = self.tool._run({})
        
        # 应该能处理空数据而不报错
        assert result['status'] == 'success'


class TestDataProcessingAgent:
    """测试数据处理智能体"""
    
    def setup_method(self):
        """测试前准备"""
        self.agent = DataProcessingAgent()
        
    def test_agent_initialization(self):
        """测试智能体初始化"""
        assert self.agent.agent is not None
        assert len(self.agent.tools) == 3
        assert self.agent.agent.role == "数据处理专家"
        
    def test_get_agent(self):
        """测试获取智能体实例"""
        agent = self.agent.get_agent()
        assert agent is not None
        assert agent.role == "数据处理专家"
        
    def test_get_tools(self):
        """测试获取工具列表"""
        tools = self.agent.get_tools()
        assert len(tools) == 3
        assert any(tool.name == "ga4_data_processing" for tool in tools)
        assert any(tool.name == "data_validation" for tool in tools)
        assert any(tool.name == "data_storage" for tool in tools)
        
    @patch.object(GA4DataProcessingTool, '_run')
    @patch.object(DataStorageTool, '_run')
    def test_process_ga4_data_success(self, mock_storage_run, mock_processing_run):
        """测试成功处理GA4数据"""
        # 模拟处理工具返回成功结果
        mock_processing_run.return_value = {
            'status': 'success',
            'data': {'events_by_type': {}}
        }
        
        # 模拟存储工具返回成功结果
        mock_storage_run.return_value = {
            'status': 'success',
            'storage_stats': {}
        }
        
        result = self.agent.process_ga4_data('test_file.ndjson')
        
        assert result['status'] == 'success'
        assert 'storage_result' in result
        mock_processing_run.assert_called_once_with('test_file.ndjson')
        mock_storage_run.assert_called_once()
        
    @patch.object(GA4DataProcessingTool, '_run')
    def test_process_ga4_data_failure(self, mock_processing_run):
        """测试处理GA4数据失败"""
        # 模拟处理工具返回失败结果
        mock_processing_run.return_value = {
            'status': 'error',
            'error_message': 'Test error'
        }
        
        result = self.agent.process_ga4_data('test_file.ndjson')
        
        assert result['status'] == 'error'
        assert result['error_message'] == 'Test error'
        
    @patch.object(DataValidationTool, '_run')
    def test_validate_data_quality(self, mock_validation_run):
        """测试数据质量验证"""
        # 模拟验证工具返回结果
        mock_validation_run.return_value = {
            'status': 'success',
            'validation_report': {}
        }
        
        test_data = pd.DataFrame([{'event_name': 'test'}])
        result = self.agent.validate_data_quality(test_data)
        
        assert result['status'] == 'success'
        mock_validation_run.assert_called_once_with(test_data)


if __name__ == '__main__':
    pytest.main([__file__])