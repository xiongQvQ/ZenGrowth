"""
系统集成演示

该脚本演示完整的GA4数据分析工作流程，包括：
- 数据处理、分析引擎、智能体和界面组件的集成
- 完整分析流程的执行
- 性能监控和结果展示
- 报告生成和导出
"""

import json
import time
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from system.integration_manager import IntegrationManager, WorkflowConfig
from utils.logger import setup_logger

logger = setup_logger()


def create_sample_ga4_data(num_events: int = 5000) -> str:
    """
    创建示例GA4数据文件
    
    Args:
        num_events: 事件数量
        
    Returns:
        临时文件路径
    """
    logger.info(f"创建包含 {num_events} 个事件的示例GA4数据")
    
    sample_events = []
    
    # 事件类型和权重
    event_types = [
        ("page_view", 0.4),
        ("scroll", 0.2),
        ("click", 0.15),
        ("sign_up", 0.1),
        ("login", 0.08),
        ("purchase", 0.05),
        ("search", 0.02)
    ]
    
    # 页面列表
    pages = [
        "/", "/products", "/about", "/contact", "/blog", 
        "/login", "/signup", "/checkout", "/profile", "/help"
    ]
    
    # 用户类型
    user_types = ["free", "premium", "enterprise"]
    
    # 设备类型
    devices = [
        {"category": "desktop", "os": "Windows", "browser": "Chrome"},
        {"category": "mobile", "os": "Android", "browser": "Chrome"},
        {"category": "mobile", "os": "iOS", "browser": "Safari"},
        {"category": "tablet", "os": "iPadOS", "browser": "Safari"}
    ]
    
    # 地理位置
    locations = [
        {"country": "China", "region": "Beijing", "city": "Beijing"},
        {"country": "China", "region": "Shanghai", "city": "Shanghai"},
        {"country": "China", "region": "Guangdong", "city": "Shenzhen"},
        {"country": "United States", "region": "California", "city": "San Francisco"},
        {"country": "United Kingdom", "region": "England", "city": "London"}
    ]
    
    import random
    
    # 生成事件数据
    for i in range(num_events):
        # 选择事件类型
        rand = random.random()
        cumulative = 0
        event_name = "page_view"
        for event_type, weight in event_types:
            cumulative += weight
            if rand <= cumulative:
                event_name = event_type
                break
        
        # 选择用户
        user_id = f"user_{i % (num_events // 10)}"  # 10%的用户数量
        
        # 选择设备和位置
        device = random.choice(devices)
        location = random.choice(locations)
        
        # 生成时间戳（最近30天内）
        base_timestamp = 1733097600000000  # 2024-12-01的微秒时间戳
        timestamp_offset = random.randint(0, 30 * 24 * 60 * 60 * 1000000)  # 30天内随机
        event_timestamp = base_timestamp + timestamp_offset
        
        # 创建事件
        event = {
            "event_date": datetime.fromtimestamp(event_timestamp / 1000000).strftime("%Y%m%d"),
            "event_timestamp": event_timestamp,
            "event_name": event_name,
            "user_pseudo_id": user_id,
            "user_id": user_id if random.random() < 0.3 else None,  # 30%的用户有user_id
            "platform": "WEB",
            "device": {
                "category": device["category"],
                "operating_system": device["os"],
                "browser": device["browser"],
                "browser_version": "120.0.0.0",
                "language": "zh-cn" if location["country"] == "China" else "en-us",
                "time_zone_offset_seconds": 28800 if location["country"] == "China" else -28800
            },
            "geo": {
                "continent": "Asia" if location["country"] == "China" else "North America" if location["country"] == "United States" else "Europe",
                "country": location["country"],
                "region": location["region"],
                "city": location["city"]
            },
            "traffic_source": {
                "name": random.choice(["(direct)", "google", "facebook", "twitter", "email"]),
                "medium": random.choice(["(none)", "organic", "cpc", "social", "email"]),
                "source": random.choice(["(direct)", "google.com", "facebook.com", "twitter.com", "newsletter"])
            },
            "event_params": [],
            "user_properties": [
                {
                    "key": "user_type",
                    "value": {
                        "string_value": random.choice(user_types),
                        "set_timestamp_micros": event_timestamp
                    }
                }
            ],
            "items": []
        }
        
        # 根据事件类型添加特定参数
        if event_name == "page_view":
            page = random.choice(pages)
            event["event_params"].extend([
                {
                    "key": "page_title",
                    "value": {"string_value": f"Page {page}"}
                },
                {
                    "key": "page_location",
                    "value": {"string_value": f"https://example.com{page}"}
                }
            ])
        elif event_name == "purchase":
            event["event_params"].extend([
                {
                    "key": "currency",
                    "value": {"string_value": "USD"}
                },
                {
                    "key": "value",
                    "value": {"double_value": random.uniform(10, 500)}
                }
            ])
            event["items"] = [
                {
                    "item_id": f"item_{random.randint(1, 100)}",
                    "item_name": f"Product {random.randint(1, 100)}",
                    "item_category": random.choice(["Electronics", "Clothing", "Books", "Home"]),
                    "price": random.uniform(10, 200),
                    "quantity": random.randint(1, 3)
                }
            ]
        elif event_name == "search":
            event["event_params"].append({
                "key": "search_term",
                "value": {"string_value": random.choice(["product", "help", "support", "pricing", "features"])}
            })
        
        sample_events.append(event)
    
    # 写入临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False)
    for event in sample_events:
        temp_file.write(json.dumps(event, ensure_ascii=False) + '\n')
    temp_file.close()
    
    logger.info(f"示例数据已创建: {temp_file.name}")
    return temp_file.name


def demonstrate_complete_workflow():
    """演示完整的工作流程"""
    logger.info("=" * 80)
    logger.info("开始演示完整的GA4数据分析工作流程")
    logger.info("=" * 80)
    
    # 1. 创建示例数据
    logger.info("\n1. 创建示例GA4数据")
    sample_file = create_sample_ga4_data(3000)
    
    try:
        # 2. 初始化集成管理器
        logger.info("\n2. 初始化系统集成管理器")
        config = WorkflowConfig(
            enable_parallel_processing=True,
            max_workers=4,
            memory_limit_gb=8.0,
            timeout_minutes=30,
            enable_caching=True,
            cache_ttl_hours=24,
            enable_monitoring=True,
            auto_cleanup=True
        )
        
        integration_manager = IntegrationManager(config)
        logger.info("✅ 集成管理器初始化完成")
        
        # 3. 执行完整工作流程
        logger.info("\n3. 执行完整的分析工作流程")
        start_time = time.time()
        
        result = integration_manager.execute_complete_workflow(
            file_path=sample_file,
            analysis_types=[
                'event_analysis',
                'retention_analysis', 
                'conversion_analysis',
                'user_segmentation',
                'path_analysis'
            ]
        )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"✅ 工作流程执行完成，总耗时: {total_time:.2f}秒")
        
        # 4. 展示执行结果
        logger.info("\n4. 分析结果摘要")
        logger.info("-" * 50)
        
        execution_summary = result['execution_summary']
        logger.info(f"工作流程ID: {result['workflow_id']}")
        logger.info(f"数据大小: {execution_summary['data_size']:,} 条记录")
        logger.info(f"成功分析: {execution_summary['successful_analyses']}")
        logger.info(f"失败分析: {execution_summary['failed_analyses']}")
        logger.info(f"总执行时间: {execution_summary['total_execution_time']:.2f}秒")
        
        # 5. 展示各个分析结果
        logger.info("\n5. 各分析模块结果")
        logger.info("-" * 50)
        
        analysis_results = result['analysis_results']
        for analysis_type, analysis_result in analysis_results.items():
            status_icon = "✅" if analysis_result['status'] == 'completed' else "❌"
            logger.info(f"{status_icon} {analysis_type}:")
            logger.info(f"   状态: {analysis_result['status']}")
            logger.info(f"   执行时间: {analysis_result['execution_time']:.2f}秒")
            logger.info(f"   洞察数量: {len(analysis_result['insights'])}")
            logger.info(f"   建议数量: {len(analysis_result['recommendations'])}")
            
            # 展示前几个洞察
            if analysis_result['insights']:
                logger.info("   主要洞察:")
                for i, insight in enumerate(analysis_result['insights'][:3]):
                    logger.info(f"     • {insight}")
                if len(analysis_result['insights']) > 3:
                    logger.info(f"     ... 还有 {len(analysis_result['insights']) - 3} 个洞察")
            
            logger.info("")
        
        # 6. 展示数据处理结果
        logger.info("\n6. 数据处理结果")
        logger.info("-" * 50)
        
        data_processing = result['data_processing']
        data_summary = data_processing['summary']
        
        logger.info(f"总事件数: {data_summary.get('total_events', 0):,}")
        logger.info(f"独立用户数: {data_summary.get('unique_users', 0):,}")
        logger.info(f"事件类型数: {len(data_summary.get('event_types', {}))}")
        logger.info(f"平台分布: {data_summary.get('platforms', {})}")
        
        date_range = data_summary.get('date_range', {})
        if date_range:
            logger.info(f"时间范围: {date_range.get('start')} - {date_range.get('end')}")
        
        # 7. 展示系统性能指标
        logger.info("\n7. 系统性能指标")
        logger.info("-" * 50)
        
        system_metrics = result['system_metrics']
        if system_metrics:
            logger.info(f"CPU使用率: {system_metrics.get('cpu_usage', 0):.1f}%")
            logger.info(f"内存使用率: {system_metrics.get('memory_usage', 0):.1f}%")
            logger.info(f"可用内存: {system_metrics.get('memory_available', 0):.1f}GB")
        
        # 8. 测试缓存性能
        logger.info("\n8. 测试缓存性能")
        logger.info("-" * 50)
        
        # 重置执行状态但保留缓存
        integration_manager.analysis_results.clear()
        integration_manager.current_workflow = None
        
        # 再次执行相同的工作流程
        cache_start_time = time.time()
        cached_result = integration_manager.execute_complete_workflow(
            file_path=sample_file,
            analysis_types=['event_analysis', 'retention_analysis']
        )
        cache_end_time = time.time()
        cache_time = cache_end_time - cache_start_time
        
        logger.info(f"缓存执行时间: {cache_time:.2f}秒")
        logger.info(f"性能提升: {((total_time - cache_time) / total_time * 100):.1f}%")
        
        # 9. 导出结果
        logger.info("\n9. 导出分析结果")
        logger.info("-" * 50)
        
        workflow_id = result['workflow_id']
        
        try:
            # 导出JSON格式
            json_file = integration_manager.export_workflow_results(
                workflow_id=workflow_id,
                export_format='json',
                include_raw_data=False
            )
            logger.info(f"✅ JSON报告已导出: {json_file}")
            
            # 检查文件大小
            file_size = Path(json_file).stat().st_size / 1024 / 1024  # MB
            logger.info(f"   文件大小: {file_size:.2f}MB")
            
        except Exception as e:
            logger.error(f"❌ 报告导出失败: {e}")
        
        # 10. 展示系统健康状态
        logger.info("\n10. 系统健康状态")
        logger.info("-" * 50)
        
        health = integration_manager.get_system_health()
        status_icon = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}.get(health['overall_status'], "❓")
        
        logger.info(f"整体状态: {status_icon} {health['overall_status']}")
        logger.info(f"活跃工作流程: {health['active_workflows']}")
        logger.info(f"总工作流程数: {health['total_workflows']}")
        logger.info(f"缓存项数量: {health['cache_size']}")
        logger.info(f"监控状态: {'启用' if health['monitoring_enabled'] else '禁用'}")
        
        if health['average_metrics']:
            logger.info(f"平均CPU使用率: {health['average_metrics']['cpu_usage']:.1f}%")
            logger.info(f"平均内存使用率: {health['average_metrics']['memory_usage']:.1f}%")
        
        # 11. 演示并发处理能力
        logger.info("\n11. 演示并发处理能力")
        logger.info("-" * 50)
        
        demonstrate_concurrent_processing(integration_manager, sample_file)
        
        # 12. 清理和关闭
        logger.info("\n12. 系统清理和关闭")
        logger.info("-" * 50)
        
        integration_manager.shutdown()
        logger.info("✅ 系统已正常关闭")
        
        logger.info("\n" + "=" * 80)
        logger.info("完整工作流程演示完成！")
        logger.info("=" * 80)
        
    finally:
        # 清理临时文件
        import os
        if os.path.exists(sample_file):
            os.unlink(sample_file)
            logger.info(f"临时文件已清理: {sample_file}")


def demonstrate_concurrent_processing(integration_manager, sample_file):
    """演示并发处理能力"""
    import threading
    import queue
    
    logger.info("启动3个并发分析任务...")
    
    results_queue = queue.Queue()
    start_time = time.time()
    
    def run_concurrent_analysis(thread_id):
        try:
            # 创建独立的集成管理器实例
            thread_config = WorkflowConfig(
                enable_parallel_processing=False,  # 避免嵌套并行
                max_workers=1,
                timeout_minutes=5,
                enable_caching=True
            )
            thread_manager = IntegrationManager(thread_config)
            
            result = thread_manager.execute_complete_workflow(
                file_path=sample_file,
                analysis_types=['event_analysis']
            )
            
            results_queue.put((thread_id, 'success', result['execution_summary']['total_execution_time']))
            
        except Exception as e:
            results_queue.put((thread_id, 'error', str(e)))
    
    # 启动并发线程
    threads = []
    for i in range(3):
        thread = threading.Thread(target=run_concurrent_analysis, args=(i,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join(timeout=60)
    
    end_time = time.time()
    total_concurrent_time = end_time - start_time
    
    # 收集结果
    successful_tasks = 0
    failed_tasks = 0
    total_task_time = 0
    
    while not results_queue.empty():
        thread_id, status, result = results_queue.get()
        if status == 'success':
            successful_tasks += 1
            total_task_time += result
            logger.info(f"  线程 {thread_id}: ✅ 成功 ({result:.2f}秒)")
        else:
            failed_tasks += 1
            logger.info(f"  线程 {thread_id}: ❌ 失败 - {result}")
    
    logger.info(f"并发执行结果:")
    logger.info(f"  总时间: {total_concurrent_time:.2f}秒")
    logger.info(f"  成功任务: {successful_tasks}")
    logger.info(f"  失败任务: {failed_tasks}")
    if successful_tasks > 0:
        logger.info(f"  平均任务时间: {total_task_time / successful_tasks:.2f}秒")
        logger.info(f"  并发效率: {(total_task_time / total_concurrent_time):.1f}x")


def demonstrate_error_handling():
    """演示错误处理能力"""
    logger.info("\n" + "=" * 80)
    logger.info("演示错误处理和恢复能力")
    logger.info("=" * 80)
    
    integration_manager = IntegrationManager()
    
    # 1. 测试文件不存在错误
    logger.info("\n1. 测试文件不存在错误处理")
    try:
        result = integration_manager.execute_complete_workflow(
            file_path="nonexistent_file.ndjson",
            analysis_types=['event_analysis']
        )
        logger.error("❌ 应该抛出异常但没有")
    except Exception as e:
        logger.info(f"✅ 正确捕获文件不存在错误: {type(e).__name__}")
    
    # 2. 测试无效分析类型
    logger.info("\n2. 测试无效分析类型处理")
    
    # 创建最小有效数据文件
    minimal_data = [
        {
            "event_date": "20241201",
            "event_timestamp": 1733097600000000,
            "event_name": "page_view",
            "user_pseudo_id": "user_1"
        }
    ]
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False)
    for event in minimal_data:
        temp_file.write(json.dumps(event) + '\n')
    temp_file.close()
    
    try:
        result = integration_manager.execute_complete_workflow(
            file_path=temp_file.name,
            analysis_types=['invalid_analysis_type']
        )
        
        # 验证错误被正确处理
        analysis_results = result['analysis_results']
        if 'invalid_analysis_type' in analysis_results:
            status = analysis_results['invalid_analysis_type']['status']
            if status == 'failed':
                logger.info("✅ 正确处理无效分析类型错误")
            else:
                logger.error(f"❌ 错误处理不正确，状态: {status}")
        
    except Exception as e:
        logger.error(f"❌ 意外错误: {e}")
    
    finally:
        import os
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
    
    integration_manager.shutdown()
    logger.info("✅ 错误处理演示完成")


def demonstrate_performance_optimization():
    """演示性能优化特性"""
    logger.info("\n" + "=" * 80)
    logger.info("演示性能优化特性")
    logger.info("=" * 80)
    
    # 创建大数据集
    logger.info("\n1. 创建大数据集进行性能测试")
    large_sample_file = create_sample_ga4_data(10000)
    
    try:
        # 测试串行vs并行性能
        logger.info("\n2. 比较串行与并行执行性能")
        
        # 串行执行
        logger.info("执行串行分析...")
        serial_config = WorkflowConfig(enable_parallel_processing=False, max_workers=1)
        serial_manager = IntegrationManager(serial_config)
        
        serial_start = time.time()
        serial_result = serial_manager.execute_complete_workflow(
            file_path=large_sample_file,
            analysis_types=['event_analysis', 'retention_analysis', 'conversion_analysis']
        )
        serial_time = time.time() - serial_start
        
        # 并行执行
        logger.info("执行并行分析...")
        parallel_config = WorkflowConfig(enable_parallel_processing=True, max_workers=4)
        parallel_manager = IntegrationManager(parallel_config)
        
        parallel_start = time.time()
        parallel_result = parallel_manager.execute_complete_workflow(
            file_path=large_sample_file,
            analysis_types=['event_analysis', 'retention_analysis', 'conversion_analysis']
        )
        parallel_time = time.time() - parallel_start
        
        # 性能对比
        logger.info(f"\n性能对比结果:")
        logger.info(f"串行执行时间: {serial_time:.2f}秒")
        logger.info(f"并行执行时间: {parallel_time:.2f}秒")
        
        if parallel_time < serial_time:
            speedup = serial_time / parallel_time
            improvement = ((serial_time - parallel_time) / serial_time) * 100
            logger.info(f"✅ 并行加速比: {speedup:.2f}x")
            logger.info(f"✅ 性能提升: {improvement:.1f}%")
        else:
            logger.info("⚠️ 并行执行未显示性能优势（可能由于数据量较小）")
        
        # 清理
        serial_manager.shutdown()
        parallel_manager.shutdown()
        
    finally:
        import os
        if os.path.exists(large_sample_file):
            os.unlink(large_sample_file)
    
    logger.info("✅ 性能优化演示完成")


def main():
    """主函数"""
    logger.info("🚀 开始GA4数据分析平台系统集成演示")
    
    try:
        # 1. 完整工作流程演示
        demonstrate_complete_workflow()
        
        # 2. 错误处理演示
        demonstrate_error_handling()
        
        # 3. 性能优化演示
        demonstrate_performance_optimization()
        
        logger.info("\n🎉 所有演示完成！")
        logger.info("\n主要特性展示:")
        logger.info("✅ 完整的GA4数据分析工作流程")
        logger.info("✅ 多智能体协作分析")
        logger.info("✅ 并行处理和性能优化")
        logger.info("✅ 智能缓存机制")
        logger.info("✅ 实时性能监控")
        logger.info("✅ 错误处理和恢复")
        logger.info("✅ 结果导出和报告生成")
        logger.info("✅ 系统健康监控")
        logger.info("✅ 资源管理和清理")
        
    except Exception as e:
        logger.error(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n👋 演示结束")


if __name__ == "__main__":
    main()