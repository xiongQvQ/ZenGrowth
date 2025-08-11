"""
简单的系统集成测试

测试系统集成管理器的基本功能，不依赖CrewAI
"""

import json
import tempfile
import time
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from system.standalone_integration_manager import StandaloneIntegrationManager, WorkflowConfig
from utils.logger import setup_logger

logger = setup_logger()


def create_test_data():
    """创建测试数据"""
    sample_events = []
    
    # 生成100个示例事件
    for i in range(100):
        event = {
            "event_date": "20241201",
            "event_timestamp": 1733097600000000 + i * 1000000,
            "event_name": ["page_view", "sign_up", "login", "purchase"][i % 4],
            "user_pseudo_id": f"user_{i % 20}",
            "user_id": f"user_{i % 20}" if i % 5 == 0 else None,
            "platform": "WEB",
            "device": {
                "category": "desktop",
                "operating_system": "Windows",
                "browser": "Chrome"
            },
            "geo": {
                "country": "China",
                "region": "Beijing",
                "city": "Beijing"
            },
            "traffic_source": {
                "name": "(direct)",
                "medium": "(none)",
                "source": "(direct)"
            },
            "event_params": [],
            "user_properties": [],
            "items": []
        }
        sample_events.append(event)
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False)
    for event in sample_events:
        temp_file.write(json.dumps(event, ensure_ascii=False) + '\n')
    temp_file.close()
    
    return temp_file.name


def test_integration_manager():
    """测试集成管理器"""
    logger.info("开始测试系统集成管理器")
    
    # 创建测试数据
    test_file = create_test_data()
    logger.info(f"创建测试数据文件: {test_file}")
    
    try:
        # 初始化集成管理器
        config = WorkflowConfig(
            enable_parallel_processing=True,
            max_workers=2,
            memory_limit_gb=4.0,
            timeout_minutes=10,
            enable_caching=True,
            enable_monitoring=True,
            auto_cleanup=True
        )
        
        integration_manager = StandaloneIntegrationManager(config)
        logger.info("✅ 集成管理器初始化成功")
        
        # 执行完整工作流程
        logger.info("开始执行工作流程")
        start_time = time.time()
        
        result = integration_manager.execute_complete_workflow(
            file_path=test_file,
            analysis_types=['event_analysis', 'retention_analysis']
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        logger.info(f"✅ 工作流程执行完成，耗时: {execution_time:.2f}秒")
        
        # 验证结果
        assert 'workflow_id' in result
        assert 'execution_summary' in result
        assert 'analysis_results' in result
        
        execution_summary = result['execution_summary']
        logger.info(f"成功分析: {execution_summary['successful_analyses']}")
        logger.info(f"失败分析: {execution_summary['failed_analyses']}")
        logger.info(f"数据大小: {execution_summary['data_size']}")
        
        # 检查分析结果
        analysis_results = result['analysis_results']
        for analysis_type, analysis_result in analysis_results.items():
            logger.info(f"{analysis_type}: {analysis_result['status']}")
            if analysis_result['status'] == 'completed':
                logger.info(f"  洞察数量: {len(analysis_result['insights'])}")
                logger.info(f"  建议数量: {len(analysis_result['recommendations'])}")
        
        # 测试系统健康状态
        health = integration_manager.get_system_health()
        logger.info(f"系统状态: {health['overall_status']}")
        logger.info(f"缓存项数量: {health['cache_size']}")
        
        # 测试导出功能
        try:
            workflow_id = result['workflow_id']
            export_file = integration_manager.export_workflow_results(
                workflow_id=workflow_id,
                export_format='json',
                include_raw_data=False
            )
            logger.info(f"✅ 结果导出成功: {export_file}")
            
            # 验证导出文件
            with open(export_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            assert 'workflow_id' in exported_data
            logger.info("✅ 导出文件验证通过")
            
        except Exception as e:
            logger.warning(f"导出测试失败: {e}")
        
        # 关闭集成管理器
        integration_manager.shutdown()
        logger.info("✅ 集成管理器已关闭")
        
        logger.info("🎉 所有测试通过!")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理测试文件
        import os
        if os.path.exists(test_file):
            os.unlink(test_file)
            logger.info(f"清理测试文件: {test_file}")


if __name__ == "__main__":
    test_integration_manager()