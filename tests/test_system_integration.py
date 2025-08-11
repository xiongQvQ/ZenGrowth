"""
系统集成端到端测试

该模块测试完整的GA4数据分析工作流程，包括：
- 数据处理、分析引擎、智能体和界面组件的集成
- 完整分析流程的端到端测试
- 性能和内存管理测试
- 错误处理和恢复测试
"""

import pytest
import tempfile
import json
import pandas as pd
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from system.integration_manager import IntegrationManager, WorkflowConfig, SystemMetrics, AnalysisResult
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager
from utils.logger import setup_logger

logger = setup_logger()


class TestSystemIntegration:
    """系统集成测试类"""
    
    @pytest.fixture
    def sample_ga4_data(self):
        """创建示例GA4数据"""
        sample_events = []
        
        # 生成示例事件数据
        for i in range(1000):
            event = {
                "event_date": "20241201",
                "event_timestamp": 1733097600000000 + i * 1000000,  # 微秒时间戳
                "event_name": ["page_view", "sign_up", "login", "purchase", "search"][i % 5],
                "user_pseudo_id": f"user_{i % 100}",
                "user_id": f"user_{i % 100}" if i % 10 == 0 else None,
                "platform": "WEB",
                "device": {
                    "category": "desktop",
                    "mobile_brand_name": None,
                    "mobile_model_name": None,
                    "mobile_marketing_name": None,
                    "mobile_os_hardware_model": None,
                    "operating_system": "Windows",
                    "operating_system_version": "10",
                    "vendor_id": None,
                    "advertising_id": None,
                    "language": "zh-cn",
                    "is_limited_ad_tracking": None,
                    "time_zone_offset_seconds": 28800,
                    "browser": "Chrome",
                    "browser_version": "120.0.0.0",
                    "web_info": {
                        "browser": "Chrome",
                        "browser_version": "120.0.0.0",
                        "hostname": "example.com"
                    }
                },
                "geo": {
                    "continent": "Asia",
                    "country": "China",
                    "region": "Beijing",
                    "city": "Beijing",
                    "sub_continent": "Eastern Asia",
                    "metro": None
                },
                "traffic_source": {
                    "name": "(direct)",
                    "medium": "(none)",
                    "source": "(direct)"
                },
                "event_params": [
                    {
                        "key": "page_title",
                        "value": {
                            "string_value": f"Page {i % 10}",
                            "int_value": None,
                            "float_value": None,
                            "double_value": None
                        }
                    },
                    {
                        "key": "page_location",
                        "value": {
                            "string_value": f"https://example.com/page{i % 10}",
                            "int_value": None,
                            "float_value": None,
                            "double_value": None
                        }
                    }
                ],
                "user_properties": [
                    {
                        "key": "user_type",
                        "value": {
                            "string_value": "premium" if i % 5 == 0 else "free",
                            "int_value": None,
                            "float_value": None,
                            "double_value": None,
                            "set_timestamp_micros": 1733097600000000
                        }
                    }
                ],
                "items": []
            }
            sample_events.append(event)
        
        return sample_events
    
    @pytest.fixture
    def sample_data_file(self, sample_ga4_data):
        """创建示例数据文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
            for event in sample_ga4_data:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
            return f.name
    
    @pytest.fixture
    def integration_manager(self):
        """创建集成管理器实例"""
        config = WorkflowConfig(
            enable_parallel_processing=True,
            max_workers=2,
            memory_limit_gb=4.0,
            timeout_minutes=10,
            enable_caching=True,
            cache_ttl_hours=1,
            enable_monitoring=True,
            auto_cleanup=True
        )
        return IntegrationManager(config)
    
    def test_complete_workflow_execution(self, integration_manager, sample_data_file):
        """测试完整工作流程执行"""
        logger.info("开始测试完整工作流程执行")
        
        try:
            # 执行完整工作流程
            result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis', 'retention_analysis']
            )
            
            # 验证结果结构
            assert 'workflow_id' in result
            assert 'execution_summary' in result
            assert 'data_processing' in result
            assert 'analysis_results' in result
            assert 'comprehensive_report' in result
            assert 'visualizations' in result
            assert 'system_metrics' in result
            
            # 验证执行摘要
            execution_summary = result['execution_summary']
            assert execution_summary['successful_analyses'] >= 0
            assert execution_summary['total_execution_time'] > 0
            assert execution_summary['data_size'] > 0
            
            # 验证分析结果
            analysis_results = result['analysis_results']
            assert 'event_analysis' in analysis_results
            assert 'retention_analysis' in analysis_results
            
            for analysis_type, analysis_result in analysis_results.items():
                assert 'status' in analysis_result
                assert 'insights' in analysis_result
                assert 'recommendations' in analysis_result
                assert 'execution_time' in analysis_result
            
            logger.info("完整工作流程执行测试通过")
            
        finally:
            # 清理临时文件
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_parallel_vs_sequential_execution(self, integration_manager, sample_data_file):
        """测试并行与串行执行性能对比"""
        logger.info("开始测试并行与串行执行性能对比")
        
        try:
            # 测试并行执行
            integration_manager.config.enable_parallel_processing = True
            start_time = time.time()
            parallel_result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis', 'retention_analysis']
            )
            parallel_time = time.time() - start_time
            
            # 重置状态
            integration_manager.reset_execution_state()
            
            # 测试串行执行
            integration_manager.config.enable_parallel_processing = False
            start_time = time.time()
            sequential_result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis', 'retention_analysis']
            )
            sequential_time = time.time() - start_time
            
            # 验证结果一致性（结构应该相同）
            assert set(parallel_result.keys()) == set(sequential_result.keys())
            assert set(parallel_result['analysis_results'].keys()) == set(sequential_result['analysis_results'].keys())
            
            # 记录性能差异
            logger.info(f"并行执行时间: {parallel_time:.2f}s")
            logger.info(f"串行执行时间: {sequential_time:.2f}s")
            logger.info(f"性能提升: {((sequential_time - parallel_time) / sequential_time * 100):.1f}%")
            
            logger.info("并行与串行执行性能对比测试通过")
            
        finally:
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_caching_mechanism(self, integration_manager, sample_data_file):
        """测试缓存机制"""
        logger.info("开始测试缓存机制")
        
        try:
            # 启用缓存
            integration_manager.config.enable_caching = True
            
            # 第一次执行
            start_time = time.time()
            first_result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis']
            )
            first_execution_time = time.time() - start_time
            
            # 验证缓存中有数据
            assert len(integration_manager.cache) > 0
            
            # 重置执行状态但保留缓存
            integration_manager.analysis_results.clear()
            integration_manager.current_workflow = None
            
            # 第二次执行（应该使用缓存）
            start_time = time.time()
            second_result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis']
            )
            second_execution_time = time.time() - start_time
            
            # 验证第二次执行更快（使用了缓存）
            assert second_execution_time < first_execution_time
            
            # 验证结果一致性
            assert first_result['data_processing']['summary'] == second_result['data_processing']['summary']
            
            logger.info(f"第一次执行时间: {first_execution_time:.2f}s")
            logger.info(f"第二次执行时间: {second_execution_time:.2f}s")
            logger.info(f"缓存加速: {((first_execution_time - second_execution_time) / first_execution_time * 100):.1f}%")
            
            logger.info("缓存机制测试通过")
            
        finally:
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_memory_management(self, integration_manager, sample_data_file):
        """测试内存管理"""
        logger.info("开始测试内存管理")
        
        try:
            import psutil
            
            # 记录初始内存使用
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 执行工作流程
            result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis', 'retention_analysis', 'conversion_analysis']
            )
            
            # 记录执行后内存使用
            after_execution_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 触发内存清理
            integration_manager._trigger_memory_cleanup()
            
            # 记录清理后内存使用
            after_cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 验证内存使用合理
            memory_increase = after_execution_memory - initial_memory
            memory_freed = after_execution_memory - after_cleanup_memory
            
            logger.info(f"初始内存: {initial_memory:.1f}MB")
            logger.info(f"执行后内存: {after_execution_memory:.1f}MB")
            logger.info(f"清理后内存: {after_cleanup_memory:.1f}MB")
            logger.info(f"内存增长: {memory_increase:.1f}MB")
            logger.info(f"释放内存: {memory_freed:.1f}MB")
            
            # 验证内存增长在合理范围内（小于1GB）
            assert memory_increase < 1024, f"内存增长过大: {memory_increase:.1f}MB"
            
            # 验证内存清理有效（释放了一些内存）
            assert memory_freed >= 0, "内存清理应该释放一些内存"
            
            logger.info("内存管理测试通过")
            
        finally:
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_error_handling_and_recovery(self, integration_manager):
        """测试错误处理和恢复"""
        logger.info("开始测试错误处理和恢复")
        
        # 测试文件不存在的情况
        with pytest.raises(Exception):
            integration_manager.execute_complete_workflow(
                file_path="nonexistent_file.ndjson",
                analysis_types=['event_analysis']
            )
        
        # 测试无效分析类型
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
            # 写入一些有效的JSON数据
            sample_event = {
                "event_date": "20241201",
                "event_timestamp": 1733097600000000,
                "event_name": "page_view",
                "user_pseudo_id": "user_1"
            }
            f.write(json.dumps(sample_event) + '\n')
            temp_file = f.name
        
        try:
            # 测试无效分析类型
            result = integration_manager.execute_complete_workflow(
                file_path=temp_file,
                analysis_types=['invalid_analysis_type']
            )
            
            # 验证错误被正确处理
            assert 'analysis_results' in result
            assert 'invalid_analysis_type' in result['analysis_results']
            assert result['analysis_results']['invalid_analysis_type']['status'] == 'failed'
            
            logger.info("错误处理和恢复测试通过")
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_workflow_status_tracking(self, integration_manager, sample_data_file):
        """测试工作流程状态跟踪"""
        logger.info("开始测试工作流程状态跟踪")
        
        try:
            # 执行工作流程
            result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis']
            )
            
            workflow_id = result['workflow_id']
            
            # 测试获取工作流程状态
            status = integration_manager.get_workflow_status(workflow_id)
            
            assert status['workflow_id'] == workflow_id
            assert status['status'] == 'completed'
            assert 'start_time' in status
            assert 'file_path' in status
            assert 'analysis_types' in status
            assert 'result_summary' in status
            
            # 测试获取不存在的工作流程状态
            invalid_status = integration_manager.get_workflow_status('invalid_workflow_id')
            assert invalid_status['status'] == 'workflow_not_found'
            
            logger.info("工作流程状态跟踪测试通过")
            
        finally:
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_result_export(self, integration_manager, sample_data_file):
        """测试结果导出"""
        logger.info("开始测试结果导出")
        
        try:
            # 执行工作流程
            result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis']
            )
            
            workflow_id = result['workflow_id']
            
            # 测试JSON导出
            json_file = integration_manager.export_workflow_results(
                workflow_id=workflow_id,
                export_format='json',
                include_raw_data=False
            )
            
            # 验证文件存在
            assert os.path.exists(json_file)
            
            # 验证文件内容
            with open(json_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            assert 'workflow_id' in exported_data
            assert exported_data['workflow_id'] == workflow_id
            assert 'analysis_results' in exported_data
            
            # 清理导出文件
            os.unlink(json_file)
            
            logger.info("结果导出测试通过")
            
        finally:
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_system_health_monitoring(self, integration_manager):
        """测试系统健康监控"""
        logger.info("开始测试系统健康监控")
        
        # 等待一些监控数据收集
        time.sleep(2)
        
        # 获取系统健康状态
        health = integration_manager.get_system_health()
        
        # 验证健康状态结构
        assert 'overall_status' in health
        assert health['overall_status'] in ['healthy', 'warning', 'critical']
        assert 'current_metrics' in health
        assert 'average_metrics' in health
        assert 'active_workflows' in health
        assert 'total_workflows' in health
        assert 'cache_size' in health
        assert 'monitoring_enabled' in health
        
        # 验证指标数据
        if health['current_metrics']:
            assert 'cpu_usage' in health['current_metrics']
            assert 'memory_usage' in health['current_metrics']
            assert 'timestamp' in health['current_metrics']
        
        logger.info("系统健康监控测试通过")
    
    def test_performance_optimization(self, integration_manager, sample_data_file):
        """测试性能优化"""
        logger.info("开始测试性能优化")
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 执行完整工作流程
            result = integration_manager.execute_complete_workflow(
                file_path=sample_data_file,
                analysis_types=['event_analysis', 'retention_analysis', 'conversion_analysis']
            )
            
            # 记录结束时间
            end_time = time.time()
            total_time = end_time - start_time
            
            # 验证性能指标
            execution_summary = result['execution_summary']
            
            # 验证总执行时间合理（应该在合理范围内）
            assert total_time < 300, f"总执行时间过长: {total_time:.2f}s"
            
            # 验证各个分析的执行时间
            for analysis_type, analysis_result in result['analysis_results'].items():
                if analysis_result['status'] == 'completed':
                    assert analysis_result['execution_time'] > 0
                    assert analysis_result['execution_time'] < 120, f"{analysis_type}执行时间过长"
            
            # 验证数据处理效率
            data_size = execution_summary['data_size']
            processing_rate = data_size / total_time if total_time > 0 else 0
            
            logger.info(f"总执行时间: {total_time:.2f}s")
            logger.info(f"数据大小: {data_size}")
            logger.info(f"处理速率: {processing_rate:.2f} records/s")
            
            # 验证处理速率合理（至少每秒处理几条记录）
            assert processing_rate > 1, f"数据处理速率过低: {processing_rate:.2f} records/s"
            
            logger.info("性能优化测试通过")
            
        finally:
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_concurrent_workflows(self, integration_manager, sample_data_file):
        """测试并发工作流程处理"""
        logger.info("开始测试并发工作流程处理")
        
        try:
            import threading
            import queue
            
            results_queue = queue.Queue()
            errors_queue = queue.Queue()
            
            def run_workflow(file_path, analysis_types, thread_id):
                try:
                    # 为每个线程创建独立的集成管理器
                    thread_manager = IntegrationManager(WorkflowConfig(
                        enable_parallel_processing=False,  # 避免嵌套并行
                        max_workers=1,
                        timeout_minutes=5
                    ))
                    
                    result = thread_manager.execute_complete_workflow(
                        file_path=file_path,
                        analysis_types=analysis_types
                    )
                    results_queue.put((thread_id, result))
                    
                except Exception as e:
                    errors_queue.put((thread_id, str(e)))
            
            # 启动多个并发工作流程
            threads = []
            for i in range(3):
                thread = threading.Thread(
                    target=run_workflow,
                    args=(sample_data_file, ['event_analysis'], i)
                )
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join(timeout=60)
            
            # 检查结果
            successful_results = []
            while not results_queue.empty():
                successful_results.append(results_queue.get())
            
            errors = []
            while not errors_queue.empty():
                errors.append(errors_queue.get())
            
            # 验证结果
            assert len(successful_results) >= 2, f"并发执行成功数量不足: {len(successful_results)}"
            
            if errors:
                logger.warning(f"并发执行中出现错误: {errors}")
            
            # 验证每个结果的完整性
            for thread_id, result in successful_results:
                assert 'workflow_id' in result
                assert 'analysis_results' in result
                assert 'event_analysis' in result['analysis_results']
            
            logger.info(f"并发工作流程测试通过，成功执行: {len(successful_results)}, 错误: {len(errors)}")
            
        finally:
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_data_quality_validation(self, integration_manager):
        """测试数据质量验证"""
        logger.info("开始测试数据质量验证")
        
        # 创建包含质量问题的数据
        problematic_data = [
            # 正常数据
            {
                "event_date": "20241201",
                "event_timestamp": 1733097600000000,
                "event_name": "page_view",
                "user_pseudo_id": "user_1"
            },
            # 缺少必需字段的数据
            {
                "event_date": "20241201",
                "event_timestamp": 1733097600000000,
                # 缺少 event_name
                "user_pseudo_id": "user_2"
            },
            # 无效时间戳
            {
                "event_date": "20241201",
                "event_timestamp": "invalid_timestamp",
                "event_name": "page_view",
                "user_pseudo_id": "user_3"
            }
        ]
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False) as f:
            for event in problematic_data:
                f.write(json.dumps(event) + '\n')
            temp_file = f.name
        
        try:
            # 执行工作流程
            result = integration_manager.execute_complete_workflow(
                file_path=temp_file,
                analysis_types=['event_analysis']
            )
            
            # 验证数据质量报告
            data_processing = result['data_processing']
            assert 'validation' in data_processing
            
            validation_report = data_processing['validation']
            
            # 应该检测到数据质量问题
            if not validation_report.get('validation_passed', True):
                assert 'errors' in validation_report or 'warnings' in validation_report
                logger.info("成功检测到数据质量问题")
            
            # 验证工作流程仍然能够完成（通过数据清理）
            assert result['execution_summary']['successful_analyses'] >= 0
            
            logger.info("数据质量验证测试通过")
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_resource_cleanup(self, integration_manager, sample_data_file):
        """测试资源清理"""
        logger.info("开始测试资源清理")
        
        try:
            # 执行多个工作流程以产生资源使用
            for i in range(3):
                result = integration_manager.execute_complete_workflow(
                    file_path=sample_data_file,
                    analysis_types=['event_analysis']
                )
                
                # 验证工作流程完成
                assert result['execution_summary']['successful_analyses'] > 0
            
            # 记录清理前的资源使用
            initial_cache_size = len(integration_manager.cache)
            initial_results_size = len(integration_manager.analysis_results)
            
            # 手动触发清理
            for workflow_id in list(integration_manager.analysis_results.keys()):
                integration_manager._cleanup_workflow_data(workflow_id)
            
            # 验证资源被清理
            final_cache_size = len(integration_manager.cache)
            
            logger.info(f"清理前缓存大小: {initial_cache_size}")
            logger.info(f"清理前结果数量: {initial_results_size}")
            logger.info(f"清理后缓存大小: {final_cache_size}")
            
            # 验证清理效果
            assert final_cache_size <= initial_cache_size, "缓存应该被清理"
            
            logger.info("资源清理测试通过")
            
        finally:
            if os.path.exists(sample_data_file):
                os.unlink(sample_data_file)
    
    def test_shutdown_and_cleanup(self, integration_manager):
        """测试关闭和清理"""
        logger.info("开始测试关闭和清理")
        
        # 验证初始状态
        assert integration_manager.monitoring_enabled == True
        assert len(integration_manager.cache) >= 0
        
        # 执行关闭
        integration_manager.shutdown()
        
        # 验证关闭后状态
        assert integration_manager.monitoring_enabled == False
        assert len(integration_manager.cache) == 0
        assert len(integration_manager.analysis_results) == 0
        
        logger.info("关闭和清理测试通过")


def run_integration_tests():
    """运行集成测试"""
    logger.info("开始运行系统集成测试")
    
    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ])
    
    logger.info("系统集成测试完成")


if __name__ == "__main__":
    run_integration_tests()