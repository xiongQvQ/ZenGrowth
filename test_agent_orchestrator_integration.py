"""
智能体编排器集成测试

测试AgentOrchestrator与实际智能体的集成，验证：
- 智能体团队协作流程
- 任务依赖关系执行
- 结果传递和数据流
- 错误处理和恢复机制
"""

import os
import sys
import json
import tempfile
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.agent_orchestrator import AgentOrchestrator, TaskStatus
from tools.data_storage_manager import DataStorageManager
from utils.logger import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


def create_test_ga4_data():
    """创建测试用的GA4数据文件"""
    test_data = [
        {
            "event_date": "20241201",
            "event_timestamp": 1733097600000000,
            "event_name": "page_view",
            "user_pseudo_id": "user_001",
            "user_id": "registered_user_001",
            "platform": "WEB",
            "device": {
                "category": "desktop",
                "operating_system": "Windows"
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
                {"key": "page_title", "value": {"string_value": "Home Page"}},
                {"key": "page_location", "value": {"string_value": "https://example.com/"}}
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
            "user_pseudo_id": "user_002",
            "user_id": "registered_user_002",
            "platform": "WEB",
            "device": {
                "category": "mobile",
                "operating_system": "iOS"
            },
            "geo": {
                "country": "US",
                "city": "Los Angeles"
            },
            "traffic_source": {
                "source": "facebook",
                "medium": "social"
            },
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
            "user_pseudo_id": "user_001",
            "user_id": "registered_user_001",
            "platform": "WEB",
            "device": {
                "category": "desktop",
                "operating_system": "Windows"
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
                {"key": "currency", "value": {"string_value": "USD"}},
                {"key": "value", "value": {"double_value": 99.99}},
                {"key": "transaction_id", "value": {"string_value": "txn_001"}}
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
    
    for event in test_data:
        temp_file.write(json.dumps(event) + '\n')
    
    temp_file.close()
    return temp_file.name


def test_orchestrator_initialization():
    """测试编排器初始化"""
    print("=" * 60)
    print("测试1: 智能体编排器初始化")
    print("=" * 60)
    
    try:
        # 创建存储管理器
        storage_manager = DataStorageManager()
        
        # 创建编排器
        orchestrator = AgentOrchestrator(storage_manager)
        
        print(f"✓ 成功初始化编排器")
        print(f"✓ 智能体数量: {len(orchestrator.agents)}")
        print(f"✓ 默认任务数量: {len(orchestrator.tasks)}")
        
        # 显示智能体类型
        print("\n智能体类型:")
        for agent_type in orchestrator.agents.keys():
            print(f"  - {agent_type.value}")
        
        # 显示任务列表
        print("\n默认任务:")
        for task_id, task_def in orchestrator.tasks.items():
            print(f"  - {task_id}: {task_def.description[:50]}...")
        
        return orchestrator
        
    except Exception as e:
        print(f"✗ 编排器初始化失败: {e}")
        return None


def test_task_execution_order(orchestrator):
    """测试任务执行顺序"""
    print("\n" + "=" * 60)
    print("测试2: 任务执行顺序计算")
    print("=" * 60)
    
    try:
        execution_order = orchestrator.get_task_execution_order()
        
        print(f"✓ 成功计算任务执行顺序")
        print(f"✓ 任务总数: {len(execution_order)}")
        
        print("\n执行顺序:")
        for i, task_id in enumerate(execution_order, 1):
            task_def = orchestrator.tasks[task_id]
            deps = ", ".join(task_def.dependencies) if task_def.dependencies else "无"
            print(f"  {i}. {task_id} (依赖: {deps})")
        
        # 验证依赖关系
        print("\n依赖关系验证:")
        for i, task_id in enumerate(execution_order):
            task_def = orchestrator.tasks[task_id]
            for dep in task_def.dependencies:
                dep_index = execution_order.index(dep)
                if dep_index >= i:
                    print(f"✗ 依赖关系错误: {task_id} 依赖 {dep}，但执行顺序不正确")
                    return False
        
        print("✓ 所有依赖关系验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 任务执行顺序计算失败: {e}")
        return False


def test_single_task_execution(orchestrator, test_file_path):
    """测试单个任务执行"""
    print("\n" + "=" * 60)
    print("测试3: 单个任务执行")
    print("=" * 60)
    
    try:
        # 执行数据处理任务
        print("执行数据处理任务...")
        result = orchestrator.execute_single_task("data_processing", file_path=test_file_path)
        
        print(f"✓ 任务执行完成")
        print(f"  - 任务ID: {result.task_id}")
        print(f"  - 状态: {result.status.value}")
        print(f"  - 执行时间: {result.execution_time:.2f}秒")
        
        if result.status == TaskStatus.COMPLETED:
            print(f"  - 结果状态: {result.result_data.get('status', 'unknown')}")
            if 'raw_data_count' in result.result_data:
                print(f"  - 原始数据量: {result.result_data['raw_data_count']}")
            if 'processed_data_count' in result.result_data:
                print(f"  - 处理后数据量: {result.result_data['processed_data_count']}")
        else:
            print(f"  - 错误信息: {result.error_message}")
        
        return result.status == TaskStatus.COMPLETED
        
    except Exception as e:
        print(f"✗ 单个任务执行失败: {e}")
        return False


def test_dependent_task_execution(orchestrator):
    """测试依赖任务执行"""
    print("\n" + "=" * 60)
    print("测试4: 依赖任务执行")
    print("=" * 60)
    
    try:
        # 执行事件分析任务（依赖数据处理任务）
        print("执行事件分析任务...")
        result = orchestrator.execute_single_task("event_analysis")
        
        print(f"✓ 依赖任务执行完成")
        print(f"  - 任务ID: {result.task_id}")
        print(f"  - 状态: {result.status.value}")
        print(f"  - 执行时间: {result.execution_time:.2f}秒")
        
        if result.status == TaskStatus.COMPLETED:
            print(f"  - 结果状态: {result.result_data.get('status', 'unknown')}")
            
            # 显示分析结果摘要
            if 'frequency_analysis' in result.result_data:
                freq_summary = result.result_data['frequency_analysis'].get('summary', {})
                if freq_summary:
                    print(f"  - 频次分析: {freq_summary.get('total_events_analyzed', 0)}种事件类型")
            
            if 'key_event_analysis' in result.result_data:
                key_summary = result.result_data['key_event_analysis'].get('summary', {})
                if key_summary:
                    print(f"  - 关键事件: {key_summary.get('total_events_analyzed', 0)}个事件分析")
        else:
            print(f"  - 错误信息: {result.error_message}")
        
        return result.status == TaskStatus.COMPLETED
        
    except Exception as e:
        print(f"✗ 依赖任务执行失败: {e}")
        return False


def test_execution_status_monitoring(orchestrator):
    """测试执行状态监控"""
    print("\n" + "=" * 60)
    print("测试5: 执行状态监控")
    print("=" * 60)
    
    try:
        status = orchestrator.get_execution_status()
        
        print(f"✓ 成功获取执行状态")
        print(f"  - 总任务数: {status['total_tasks']}")
        print(f"  - 已完成任务: {status['completed_tasks']}")
        print(f"  - 失败任务: {status['failed_tasks']}")
        print(f"  - 待执行任务: {status['pending_tasks']}")
        print(f"  - 完成率: {status['completion_rate']:.1%}")
        
        print("\n任务详细状态:")
        for task_id, task_status in status['task_results'].items():
            print(f"  - {task_id}: {task_status['status']} "
                  f"(耗时: {task_status['execution_time']:.2f}s)")
            if task_status['error_message']:
                print(f"    错误: {task_status['error_message']}")
        
        return True
        
    except Exception as e:
        print(f"✗ 执行状态监控失败: {e}")
        return False


def test_configuration_export_import(orchestrator):
    """测试配置导出和导入"""
    print("\n" + "=" * 60)
    print("测试6: 配置导出和导入")
    print("=" * 60)
    
    try:
        # 导出配置
        config = orchestrator.export_configuration()
        
        print(f"✓ 成功导出配置")
        print(f"  - 任务配置数量: {len(config['tasks'])}")
        print(f"  - 智能体数量: {len(config['agents'])}")
        print(f"  - 执行历史记录: {len(config['execution_history'])}")
        
        # 创建新的编排器并导入配置
        new_orchestrator = AgentOrchestrator()
        new_orchestrator.import_configuration(config)
        
        print(f"✓ 成功导入配置到新编排器")
        print(f"  - 导入任务数量: {len(new_orchestrator.tasks)}")
        print(f"  - 导入执行历史: {len(new_orchestrator.execution_history)}")
        
        # 验证配置一致性
        original_task_ids = set(orchestrator.tasks.keys())
        imported_task_ids = set(new_orchestrator.tasks.keys())
        
        if original_task_ids == imported_task_ids:
            print("✓ 任务配置导入验证通过")
        else:
            print("✗ 任务配置导入验证失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 配置导出导入失败: {e}")
        return False


def test_error_handling(orchestrator):
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试7: 错误处理")
    print("=" * 60)
    
    try:
        # 测试执行不存在的任务
        print("测试执行不存在的任务...")
        try:
            orchestrator.execute_single_task("non_existent_task")
            print("✗ 应该抛出异常但没有")
            return False
        except ValueError as e:
            print(f"✓ 正确处理不存在的任务: {e}")
        
        # 测试执行缺少依赖的任务
        print("\n测试执行缺少依赖的任务...")
        orchestrator.reset_execution_state()  # 清除之前的任务结果
        
        try:
            orchestrator.execute_single_task("event_analysis")
            print("✗ 应该抛出依赖异常但没有")
            return False
        except ValueError as e:
            print(f"✓ 正确处理依赖缺失: {e}")
        
        # 测试循环依赖检测
        print("\n测试循环依赖检测...")
        original_deps = orchestrator.tasks["event_analysis"].dependencies.copy()
        
        try:
            # 创建循环依赖
            orchestrator.tasks["event_analysis"].dependencies.append("retention_analysis")
            orchestrator.tasks["retention_analysis"].dependencies.append("event_analysis")
            
            orchestrator.get_task_execution_order()
            print("✗ 应该检测到循环依赖但没有")
            return False
        except ValueError as e:
            print(f"✓ 正确检测循环依赖: {e}")
        finally:
            # 恢复原始依赖
            orchestrator.tasks["event_analysis"].dependencies = original_deps
            orchestrator.tasks["retention_analysis"].dependencies = ["data_processing"]
        
        return True
        
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("智能体编排器集成测试")
    print("=" * 60)
    
    # 创建测试数据文件
    test_file_path = create_test_ga4_data()
    print(f"创建测试数据文件: {test_file_path}")
    
    try:
        # 测试结果统计
        test_results = []
        
        # 1. 测试编排器初始化
        orchestrator = test_orchestrator_initialization()
        test_results.append(orchestrator is not None)
        
        if orchestrator is None:
            print("\n编排器初始化失败，跳过后续测试")
            return
        
        # 2. 测试任务执行顺序
        test_results.append(test_task_execution_order(orchestrator))
        
        # 3. 测试单个任务执行
        test_results.append(test_single_task_execution(orchestrator, test_file_path))
        
        # 4. 测试依赖任务执行
        test_results.append(test_dependent_task_execution(orchestrator))
        
        # 5. 测试执行状态监控
        test_results.append(test_execution_status_monitoring(orchestrator))
        
        # 6. 测试配置导出导入
        test_results.append(test_configuration_export_import(orchestrator))
        
        # 7. 测试错误处理
        test_results.append(test_error_handling(orchestrator))
        
        # 输出测试结果摘要
        print("\n" + "=" * 60)
        print("测试结果摘要")
        print("=" * 60)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        test_names = [
            "编排器初始化",
            "任务执行顺序",
            "单个任务执行",
            "依赖任务执行",
            "执行状态监控",
            "配置导出导入",
            "错误处理"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, test_results)):
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{i+1}. {name}: {status}")
        
        print(f"\n总体结果: {passed_tests}/{total_tests} 测试通过")
        
        if passed_tests == total_tests:
            print("🎉 所有测试通过！智能体编排器集成测试成功")
        else:
            print("⚠️  部分测试失败，请检查相关功能")
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
            print(f"\n清理测试文件: {test_file_path}")


if __name__ == "__main__":
    main()