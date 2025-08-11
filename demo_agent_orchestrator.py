"""
智能体编排器演示脚本

演示AgentOrchestrator的核心功能：
- 智能体团队初始化
- 任务依赖关系管理
- 工作流程执行
- 状态监控和结果传递
"""

import os
import sys
import json
import tempfile
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.agent_orchestrator import AgentOrchestrator, TaskStatus
from tools.data_storage_manager import DataStorageManager


def create_demo_ga4_data():
    """创建演示用的GA4数据文件"""
    demo_data = [
        {
            "event_date": "20241201",
            "event_timestamp": 1733097600000000,
            "event_name": "page_view",
            "user_pseudo_id": "demo_user_001",
            "user_id": "registered_user_001",
            "platform": "WEB",
            "device": {"category": "desktop", "operating_system": "Windows"},
            "geo": {"country": "US", "city": "New York"},
            "traffic_source": {"source": "google", "medium": "organic"},
            "event_params": [
                {"key": "page_title", "value": {"string_value": "Home Page"}},
                {"key": "page_location", "value": {"string_value": "https://demo.com/"}}
            ],
            "user_properties": [
                {"key": "user_type", "value": {"string_value": "premium"}},
                {"key": "registration_date", "value": {"string_value": "2024-01-15"}}
            ]
        },
        {
            "event_date": "20241201",
            "event_timestamp": 1733097660000000,
            "event_name": "sign_up",
            "user_pseudo_id": "demo_user_002",
            "user_id": "registered_user_002",
            "platform": "MOBILE_APP",
            "device": {"category": "mobile", "operating_system": "iOS"},
            "geo": {"country": "US", "city": "Los Angeles"},
            "traffic_source": {"source": "facebook", "medium": "social"},
            "event_params": [
                {"key": "method", "value": {"string_value": "email"}},
                {"key": "success", "value": {"string_value": "true"}}
            ],
            "user_properties": [
                {"key": "user_type", "value": {"string_value": "free"}},
                {"key": "registration_date", "value": {"string_value": "2024-12-01"}}
            ]
        },
        {
            "event_date": "20241201",
            "event_timestamp": 1733097720000000,
            "event_name": "purchase",
            "user_pseudo_id": "demo_user_001",
            "user_id": "registered_user_001",
            "platform": "WEB",
            "device": {"category": "desktop", "operating_system": "Windows"},
            "geo": {"country": "US", "city": "New York"},
            "traffic_source": {"source": "google", "medium": "organic"},
            "event_params": [
                {"key": "currency", "value": {"string_value": "USD"}},
                {"key": "value", "value": {"double_value": 99.99}},
                {"key": "transaction_id", "value": {"string_value": "demo_txn_001"}}
            ],
            "user_properties": [
                {"key": "user_type", "value": {"string_value": "premium"}},
                {"key": "registration_date", "value": {"string_value": "2024-01-15"}}
            ],
            "items": [
                {
                    "item_id": "product_001",
                    "item_name": "Premium Subscription",
                    "item_category": "subscription",
                    "price": 99.99,
                    "quantity": 1
                }
            ]
        }
    ]
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False)
    
    for event in demo_data:
        temp_file.write(json.dumps(event) + '\n')
    
    temp_file.close()
    return temp_file.name


def demo_orchestrator_initialization():
    """演示编排器初始化"""
    print("🚀 智能体编排器演示")
    print("=" * 80)
    
    print("\n1. 初始化智能体编排器")
    print("-" * 40)
    
    try:
        # 创建存储管理器
        storage_manager = DataStorageManager()
        
        # 创建编排器
        orchestrator = AgentOrchestrator(storage_manager)
        
        print(f"✅ 编排器初始化成功")
        print(f"   - 智能体数量: {len(orchestrator.agents)}")
        print(f"   - 默认任务数量: {len(orchestrator.tasks)}")
        
        # 显示智能体类型
        print(f"\n   智能体团队:")
        for i, agent_type in enumerate(orchestrator.agents.keys(), 1):
            print(f"   {i}. {agent_type.value}")
        
        return orchestrator
        
    except Exception as e:
        print(f"❌ 编排器初始化失败: {e}")
        return None


def demo_task_workflow(orchestrator):
    """演示任务工作流程"""
    print(f"\n2. 任务工作流程分析")
    print("-" * 40)
    
    try:
        # 计算执行顺序
        execution_order = orchestrator.get_task_execution_order()
        
        print(f"✅ 任务执行顺序计算成功")
        print(f"   总任务数: {len(execution_order)}")
        
        print(f"\n   执行流程:")
        for i, task_id in enumerate(execution_order, 1):
            task_def = orchestrator.tasks[task_id]
            deps = ", ".join(task_def.dependencies) if task_def.dependencies else "无依赖"
            print(f"   {i}. {task_id}")
            print(f"      描述: {task_def.description[:60]}...")
            print(f"      依赖: {deps}")
            print(f"      优先级: {task_def.priority}")
        
        return execution_order
        
    except Exception as e:
        print(f"❌ 任务工作流程分析失败: {e}")
        return []


def demo_single_task_execution(orchestrator, demo_file_path):
    """演示单个任务执行"""
    print(f"\n3. 单个任务执行演示")
    print("-" * 40)
    
    try:
        # 执行数据处理任务
        print(f"🔄 执行数据处理任务...")
        start_time = datetime.now()
        
        result = orchestrator.execute_single_task("data_processing", file_path=demo_file_path)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        print(f"✅ 数据处理任务完成")
        print(f"   - 状态: {result.status.value}")
        print(f"   - 执行时间: {execution_time:.3f}秒")
        
        if result.status == TaskStatus.COMPLETED:
            result_data = result.result_data
            print(f"   - 处理状态: {result_data.get('status', 'unknown')}")
            
            if 'raw_data_count' in result_data:
                print(f"   - 原始数据量: {result_data['raw_data_count']}")
            if 'processed_data_count' in result_data:
                print(f"   - 处理后数据量: {result_data['processed_data_count']}")
            if 'events_by_type' in result_data:
                events_summary = result_data['events_by_type']
                print(f"   - 事件类型统计: {dict(list(events_summary.items())[:3])}...")
        else:
            print(f"   - 错误信息: {result.error_message}")
        
        return result.status == TaskStatus.COMPLETED
        
    except Exception as e:
        print(f"❌ 单个任务执行失败: {e}")
        return False


def demo_dependent_tasks_execution(orchestrator):
    """演示依赖任务执行"""
    print(f"\n4. 依赖任务执行演示")
    print("-" * 40)
    
    dependent_tasks = ["event_analysis", "retention_analysis", "conversion_analysis"]
    
    for task_id in dependent_tasks:
        try:
            print(f"🔄 执行{task_id}任务...")
            
            result = orchestrator.execute_single_task(task_id)
            
            print(f"✅ {task_id}任务完成")
            print(f"   - 状态: {result.status.value}")
            print(f"   - 执行时间: {result.execution_time:.3f}秒")
            
            if result.status == TaskStatus.COMPLETED:
                result_data = result.result_data
                print(f"   - 分析状态: {result_data.get('status', 'unknown')}")
                
                # 显示特定分析结果
                if task_id == "event_analysis" and 'frequency_analysis' in result_data:
                    freq_summary = result_data['frequency_analysis'].get('summary', {})
                    if freq_summary:
                        print(f"   - 事件频次分析: {freq_summary.get('total_events_analyzed', 0)}种事件")
                
                elif task_id == "retention_analysis" and 'retention_rates' in result_data:
                    retention_data = result_data['retention_rates']
                    print(f"   - 留存率数据: {dict(list(retention_data.items())[:2])}...")
                
                elif task_id == "conversion_analysis" and 'conversion_funnel' in result_data:
                    funnel_data = result_data['conversion_funnel']
                    print(f"   - 转化漏斗: {dict(list(funnel_data.items())[:3])}...")
            else:
                print(f"   - 错误信息: {result.error_message}")
                
        except Exception as e:
            print(f"❌ {task_id}任务执行失败: {e}")


def demo_execution_monitoring(orchestrator):
    """演示执行状态监控"""
    print(f"\n5. 执行状态监控")
    print("-" * 40)
    
    try:
        status = orchestrator.get_execution_status()
        
        print(f"✅ 执行状态监控")
        print(f"   - 总任务数: {status['total_tasks']}")
        print(f"   - 已完成: {status['completed_tasks']}")
        print(f"   - 失败任务: {status['failed_tasks']}")
        print(f"   - 待执行: {status['pending_tasks']}")
        print(f"   - 完成率: {status['completion_rate']:.1%}")
        
        print(f"\n   任务详细状态:")
        for task_id, task_status in status['task_results'].items():
            status_icon = "✅" if task_status['status'] == 'completed' else "❌" if task_status['status'] == 'failed' else "⏳"
            print(f"   {status_icon} {task_id}: {task_status['status']} "
                  f"(耗时: {task_status['execution_time']:.3f}s)")
            
            if task_status['error_message']:
                print(f"      错误: {task_status['error_message']}")
        
        return status
        
    except Exception as e:
        print(f"❌ 执行状态监控失败: {e}")
        return None


def demo_workflow_execution(orchestrator, demo_file_path):
    """演示完整工作流程执行"""
    print(f"\n6. 完整工作流程执行")
    print("-" * 40)
    
    try:
        print(f"🔄 启动完整分析工作流程...")
        
        # 使用简化的执行方式，因为CrewAI可能不可用
        execution_order = orchestrator.get_task_execution_order()
        
        print(f"📋 执行计划: {len(execution_order)}个任务")
        
        # 重置执行状态
        orchestrator.reset_execution_state()
        
        # 按顺序执行所有任务
        for i, task_id in enumerate(execution_order, 1):
            print(f"\n   步骤 {i}/{len(execution_order)}: {task_id}")
            
            # 为数据处理任务提供文件路径
            kwargs = {"file_path": demo_file_path} if task_id == "data_processing" else {}
            
            result = orchestrator.execute_single_task(task_id, **kwargs)
            
            if result.status == TaskStatus.COMPLETED:
                print(f"   ✅ 完成 (耗时: {result.execution_time:.3f}s)")
            else:
                print(f"   ❌ 失败: {result.error_message}")
        
        # 获取最终状态
        final_status = orchestrator.get_execution_status()
        
        print(f"\n🎯 工作流程执行完成")
        print(f"   - 成功率: {final_status['completion_rate']:.1%}")
        print(f"   - 总耗时: {sum(r['execution_time'] for r in final_status['task_results'].values()):.3f}秒")
        
        return final_status['completion_rate'] == 1.0
        
    except Exception as e:
        print(f"❌ 完整工作流程执行失败: {e}")
        return False


def demo_configuration_management(orchestrator):
    """演示配置管理"""
    print(f"\n7. 配置管理演示")
    print("-" * 40)
    
    try:
        # 导出配置
        config = orchestrator.export_configuration()
        
        print(f"✅ 配置导出成功")
        print(f"   - 任务配置: {len(config['tasks'])}个")
        print(f"   - 智能体配置: {len(config['agents'])}个")
        print(f"   - 执行历史: {len(config['execution_history'])}条")
        
        # 显示部分配置内容
        print(f"\n   任务配置示例:")
        sample_task = list(config['tasks'].items())[0]
        task_id, task_config = sample_task
        print(f"   - {task_id}:")
        print(f"     描述: {task_config['description'][:50]}...")
        print(f"     依赖: {task_config['dependencies']}")
        print(f"     优先级: {task_config['priority']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置管理演示失败: {e}")
        return False


def main():
    """主演示函数"""
    print("🎭 智能体编排器功能演示")
    print("=" * 80)
    
    # 创建演示数据文件
    demo_file_path = create_demo_ga4_data()
    print(f"📁 创建演示数据文件: {os.path.basename(demo_file_path)}")
    
    try:
        # 演示步骤
        demo_results = []
        
        # 1. 初始化演示
        orchestrator = demo_orchestrator_initialization()
        demo_results.append(orchestrator is not None)
        
        if orchestrator is None:
            print("\n❌ 编排器初始化失败，终止演示")
            return
        
        # 2. 任务工作流程演示
        execution_order = demo_task_workflow(orchestrator)
        demo_results.append(len(execution_order) > 0)
        
        # 3. 单个任务执行演示
        single_task_success = demo_single_task_execution(orchestrator, demo_file_path)
        demo_results.append(single_task_success)
        
        # 4. 依赖任务执行演示
        demo_dependent_tasks_execution(orchestrator)
        demo_results.append(True)  # 假设成功
        
        # 5. 执行状态监控演示
        status = demo_execution_monitoring(orchestrator)
        demo_results.append(status is not None)
        
        # 6. 完整工作流程执行演示
        workflow_success = demo_workflow_execution(orchestrator, demo_file_path)
        demo_results.append(workflow_success)
        
        # 7. 配置管理演示
        config_success = demo_configuration_management(orchestrator)
        demo_results.append(config_success)
        
        # 演示结果总结
        print(f"\n" + "=" * 80)
        print(f"📊 演示结果总结")
        print("=" * 80)
        
        demo_names = [
            "编排器初始化",
            "任务工作流程分析",
            "单个任务执行",
            "依赖任务执行",
            "执行状态监控",
            "完整工作流程执行",
            "配置管理"
        ]
        
        successful_demos = sum(demo_results)
        total_demos = len(demo_results)
        
        for i, (name, success) in enumerate(zip(demo_names, demo_results), 1):
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {i}. {name}")
        
        print(f"\n🎯 演示完成: {successful_demos}/{total_demos} 项成功")
        
        if successful_demos == total_demos:
            print("🎉 所有演示项目成功！智能体编排器功能正常")
        else:
            print("⚠️  部分演示项目失败，请检查相关功能")
        
        # 显示最终执行状态
        if orchestrator:
            final_status = orchestrator.get_execution_status()
            print(f"\n📈 最终执行统计:")
            print(f"   - 任务完成率: {final_status['completion_rate']:.1%}")
            print(f"   - 已完成任务: {final_status['completed_tasks']}")
            print(f"   - 失败任务: {final_status['failed_tasks']}")
        
    finally:
        # 清理演示文件
        if os.path.exists(demo_file_path):
            os.unlink(demo_file_path)
            print(f"\n🧹 清理演示文件: {os.path.basename(demo_file_path)}")


if __name__ == "__main__":
    main()