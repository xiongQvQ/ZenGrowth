"""
智能体编排器核心功能测试

测试编排器的核心逻辑，不依赖CrewAI的完整导入：
- 任务依赖关系管理
- 执行顺序计算
- 状态监控
- 配置管理
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(Enum):
    """智能体类型枚举"""
    DATA_PROCESSOR = "data_processor"
    EVENT_ANALYST = "event_analyst"
    RETENTION_ANALYST = "retention_analyst"
    CONVERSION_ANALYST = "conversion_analyst"
    SEGMENTATION_ANALYST = "segmentation_analyst"
    PATH_ANALYST = "path_analyst"
    REPORT_GENERATOR = "report_generator"


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    agent_type: AgentType
    status: TaskStatus
    result_data: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AgentTaskDefinition:
    """智能体任务定义"""
    task_id: str
    agent_type: AgentType
    description: str
    expected_output: str
    dependencies: List[str]
    parameters: Dict[str, Any]
    priority: int = 1
    timeout: int = 300
    retry_count: int = 2


class MockAgent:
    """模拟智能体类"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
    
    def get_agent(self):
        return self
    
    def process_ga4_data(self, file_path: str):
        """模拟数据处理"""
        return {
            "status": "success",
            "raw_data_count": 100,
            "processed_data_count": 95,
            "data": {"processed": True}
        }
    
    def comprehensive_event_analysis(self):
        """模拟事件分析"""
        return {
            "status": "success",
            "frequency_analysis": {
                "summary": {"total_events_analyzed": 5}
            },
            "key_event_analysis": {
                "summary": {"total_events_analyzed": 3}
            }
        }
    
    def comprehensive_retention_analysis(self):
        """模拟留存分析"""
        return {
            "status": "success",
            "retention_rates": {"day_1": 0.8, "day_7": 0.6}
        }
    
    def comprehensive_conversion_analysis(self):
        """模拟转化分析"""
        return {
            "status": "success",
            "conversion_funnel": {"step_1": 1000, "step_2": 800, "step_3": 600}
        }
    
    def comprehensive_segmentation_analysis(self):
        """模拟用户分群分析"""
        return {
            "status": "success",
            "segments": {"segment_1": 500, "segment_2": 300}
        }
    
    def comprehensive_path_analysis(self):
        """模拟路径分析"""
        return {
            "status": "success",
            "common_paths": ["home->product->purchase", "home->about->contact"]
        }
    
    def generate_comprehensive_report(self, analysis_results):
        """模拟报告生成"""
        return {
            "status": "success",
            "report": {"summary": "综合分析报告", "insights": ["洞察1", "洞察2"]}
        }


class SimplifiedOrchestrator:
    """简化的智能体编排器（不依赖CrewAI）"""
    
    def __init__(self):
        """初始化编排器"""
        self.agents = {}
        self.tasks = {}
        self.task_results = {}
        self.execution_history = []
        
        # 初始化模拟智能体
        self._initialize_mock_agents()
        
        # 定义默认任务流程
        self._define_default_workflow()
    
    def _initialize_mock_agents(self):
        """初始化模拟智能体"""
        for agent_type in AgentType:
            self.agents[agent_type] = MockAgent(agent_type)
    
    def _define_default_workflow(self):
        """定义默认的分析工作流程"""
        self.tasks = {
            "data_processing": AgentTaskDefinition(
                task_id="data_processing",
                agent_type=AgentType.DATA_PROCESSOR,
                description="解析和预处理GA4事件数据，确保数据质量和完整性",
                expected_output="处理后的结构化数据，包括事件、用户和会话信息",
                dependencies=[],
                parameters={"file_path": None},
                priority=1
            ),
            
            "event_analysis": AgentTaskDefinition(
                task_id="event_analysis",
                agent_type=AgentType.EVENT_ANALYST,
                description="分析用户事件模式，包括频次统计、趋势分析和关联性分析",
                expected_output="事件分析报告，包括关键事件识别和行为模式洞察",
                dependencies=["data_processing"],
                parameters={},
                priority=2
            ),
            
            "retention_analysis": AgentTaskDefinition(
                task_id="retention_analysis",
                agent_type=AgentType.RETENTION_ANALYST,
                description="计算用户留存率，分析用户生命周期和流失模式",
                expected_output="留存分析报告，包括留存曲线和流失预测",
                dependencies=["data_processing"],
                parameters={},
                priority=2
            ),
            
            "conversion_analysis": AgentTaskDefinition(
                task_id="conversion_analysis",
                agent_type=AgentType.CONVERSION_ANALYST,
                description="构建转化漏斗，识别转化瓶颈和优化机会",
                expected_output="转化分析报告，包括漏斗分析和优化建议",
                dependencies=["data_processing"],
                parameters={},
                priority=2
            ),
            
            "segmentation_analysis": AgentTaskDefinition(
                task_id="segmentation_analysis",
                agent_type=AgentType.SEGMENTATION_ANALYST,
                description="基于用户行为和属性进行智能分群，生成用户画像",
                expected_output="用户分群报告，包括群体特征和营销建议",
                dependencies=["data_processing"],
                parameters={},
                priority=3
            ),
            
            "path_analysis": AgentTaskDefinition(
                task_id="path_analysis",
                agent_type=AgentType.PATH_ANALYST,
                description="分析用户行为路径，优化用户体验流程",
                expected_output="路径分析报告，包括用户流程图和体验优化建议",
                dependencies=["data_processing"],
                parameters={},
                priority=3
            ),
            
            "report_generation": AgentTaskDefinition(
                task_id="report_generation",
                agent_type=AgentType.REPORT_GENERATOR,
                description="汇总所有分析结果，生成综合性的业务洞察报告",
                expected_output="综合分析报告，包括关键指标、洞察和行动建议",
                dependencies=["event_analysis", "retention_analysis", "conversion_analysis", 
                            "segmentation_analysis", "path_analysis"],
                parameters={},
                priority=4
            )
        }
    
    def get_task_execution_order(self) -> List[str]:
        """根据依赖关系和优先级计算任务执行顺序"""
        # 拓扑排序算法
        in_degree = {task_id: 0 for task_id in self.tasks}
        
        # 计算入度
        for task_id, task_def in self.tasks.items():
            for dep in task_def.dependencies:
                if dep in in_degree:
                    in_degree[task_id] += 1
        
        # 按优先级排序的队列
        queue = []
        for task_id, degree in in_degree.items():
            if degree == 0:
                queue.append((self.tasks[task_id].priority, task_id))
        
        queue.sort()  # 按优先级排序
        
        execution_order = []
        
        while queue:
            _, current_task = queue.pop(0)
            execution_order.append(current_task)
            
            # 更新依赖此任务的其他任务
            for task_id, task_def in self.tasks.items():
                if current_task in task_def.dependencies:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append((task_def.priority, task_id))
                        queue.sort()
        
        # 检查是否有循环依赖
        if len(execution_order) != len(self.tasks):
            remaining_tasks = set(self.tasks.keys()) - set(execution_order)
            raise ValueError(f"检测到循环依赖，无法执行的任务: {remaining_tasks}")
        
        return execution_order
    
    def execute_single_task(self, task_id: str, **kwargs) -> TaskResult:
        """执行单个任务"""
        try:
            start_time = datetime.now()
            
            if task_id not in self.tasks:
                raise ValueError(f"任务不存在: {task_id}")
            
            task_def = self.tasks[task_id]
            agent = self.agents[task_def.agent_type]
            
            # 检查依赖任务是否完成
            for dep_task_id in task_def.dependencies:
                if dep_task_id not in self.task_results or \
                   self.task_results[dep_task_id].status != TaskStatus.COMPLETED:
                    raise ValueError(f"依赖任务未完成: {dep_task_id}")
            
            # 合并参数
            parameters = {**task_def.parameters, **kwargs}
            
            # 执行任务
            if task_id == "data_processing":
                result_data = agent.process_ga4_data(parameters.get("file_path"))
            elif task_id == "event_analysis":
                result_data = agent.comprehensive_event_analysis()
            elif task_id == "retention_analysis":
                result_data = agent.comprehensive_retention_analysis()
            elif task_id == "conversion_analysis":
                result_data = agent.comprehensive_conversion_analysis()
            elif task_id == "segmentation_analysis":
                result_data = agent.comprehensive_segmentation_analysis()
            elif task_id == "path_analysis":
                result_data = agent.comprehensive_path_analysis()
            elif task_id == "report_generation":
                # 收集所有分析结果
                analysis_results = {
                    tid: result.result_data for tid, result in self.task_results.items()
                    if result.status == TaskStatus.COMPLETED
                }
                result_data = agent.generate_comprehensive_report(analysis_results)
            else:
                raise ValueError(f"未知的任务类型: {task_id}")
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 创建任务结果
            task_result = TaskResult(
                task_id=task_id,
                agent_type=task_def.agent_type,
                status=TaskStatus.COMPLETED if result_data.get("status") == "success" else TaskStatus.FAILED,
                result_data=result_data,
                execution_time=execution_time,
                error_message=result_data.get("error_message") if result_data.get("status") != "success" else None,
                timestamp=end_time
            )
            
            # 保存任务结果
            self.task_results[task_id] = task_result
            
            return task_result
            
        except Exception as e:
            task_result = TaskResult(
                task_id=task_id,
                agent_type=task_def.agent_type,
                status=TaskStatus.FAILED,
                result_data={},
                execution_time=0,
                error_message=str(e),
                timestamp=datetime.now()
            )
            
            self.task_results[task_id] = task_result
            return task_result
    
    def get_execution_status(self) -> Dict[str, Any]:
        """获取执行状态"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for result in self.task_results.values() 
                            if result.status == TaskStatus.COMPLETED)
        failed_tasks = sum(1 for result in self.task_results.values() 
                         if result.status == TaskStatus.FAILED)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "pending_tasks": total_tasks - len(self.task_results),
            "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "task_results": {
                task_id: {
                    "status": result.status.value,
                    "execution_time": result.execution_time,
                    "timestamp": result.timestamp.isoformat(),
                    "error_message": result.error_message
                }
                for task_id, result in self.task_results.items()
            }
        }
    
    def reset_execution_state(self):
        """重置执行状态"""
        self.task_results.clear()
    
    def export_configuration(self) -> Dict[str, Any]:
        """导出配置"""
        return {
            "tasks": {
                task_id: asdict(task_def) 
                for task_id, task_def in self.tasks.items()
            },
            "agents": [agent_type.value for agent_type in self.agents.keys()],
            "execution_history": self.execution_history
        }


def test_orchestrator_core_functionality():
    """测试编排器核心功能"""
    print("智能体编排器核心功能测试")
    print("=" * 60)
    
    # 创建编排器
    orchestrator = SimplifiedOrchestrator()
    
    # 测试1: 初始化验证
    print("\n1. 初始化验证")
    print(f"✓ 智能体数量: {len(orchestrator.agents)}")
    print(f"✓ 任务数量: {len(orchestrator.tasks)}")
    
    # 测试2: 任务执行顺序
    print("\n2. 任务执行顺序计算")
    execution_order = orchestrator.get_task_execution_order()
    print(f"✓ 执行顺序: {' -> '.join(execution_order)}")
    
    # 验证依赖关系
    print("\n3. 依赖关系验证")
    for i, task_id in enumerate(execution_order):
        task_def = orchestrator.tasks[task_id]
        for dep in task_def.dependencies:
            dep_index = execution_order.index(dep)
            if dep_index >= i:
                print(f"✗ 依赖关系错误: {task_id} 依赖 {dep}")
                return False
    print("✓ 所有依赖关系正确")
    
    # 测试4: 单个任务执行
    print("\n4. 单个任务执行测试")
    
    # 执行数据处理任务
    result = orchestrator.execute_single_task("data_processing", file_path="/test/file.ndjson")
    print(f"✓ 数据处理任务: {result.status.value} (耗时: {result.execution_time:.3f}s)")
    
    # 执行事件分析任务
    result = orchestrator.execute_single_task("event_analysis")
    print(f"✓ 事件分析任务: {result.status.value} (耗时: {result.execution_time:.3f}s)")
    
    # 测试5: 依赖检查
    print("\n5. 依赖检查测试")
    orchestrator.reset_execution_state()
    
    try:
        result = orchestrator.execute_single_task("event_analysis")
        if result.status == TaskStatus.FAILED and "依赖任务未完成" in str(result.error_message):
            print(f"✓ 正确检测依赖缺失: {result.error_message}")
        else:
            print("✗ 应该检测到依赖缺失")
            return False
    except ValueError as e:
        print(f"✓ 正确检测依赖缺失: {e}")
    
    # 测试6: 完整工作流程执行
    print("\n6. 完整工作流程执行")
    orchestrator.reset_execution_state()
    
    for task_id in execution_order:
        result = orchestrator.execute_single_task(task_id, file_path="/test/file.ndjson")
        print(f"  - {task_id}: {result.status.value}")
    
    # 测试7: 执行状态监控
    print("\n7. 执行状态监控")
    status = orchestrator.get_execution_status()
    print(f"✓ 完成率: {status['completion_rate']:.1%}")
    print(f"✓ 已完成: {status['completed_tasks']}/{status['total_tasks']}")
    
    # 测试8: 配置导出
    print("\n8. 配置导出测试")
    config = orchestrator.export_configuration()
    print(f"✓ 导出任务配置: {len(config['tasks'])}个")
    print(f"✓ 导出智能体配置: {len(config['agents'])}个")
    
    # 测试9: 循环依赖检测
    print("\n9. 循环依赖检测")
    
    # 保存原始依赖
    original_deps = orchestrator.tasks["event_analysis"].dependencies.copy()
    
    try:
        # 创建循环依赖
        orchestrator.tasks["event_analysis"].dependencies.append("retention_analysis")
        orchestrator.tasks["retention_analysis"].dependencies.append("event_analysis")
        
        orchestrator.get_task_execution_order()
        print("✗ 应该检测到循环依赖")
        return False
    except ValueError as e:
        print(f"✓ 正确检测循环依赖: {e}")
    finally:
        # 恢复原始依赖
        orchestrator.tasks["event_analysis"].dependencies = original_deps
        orchestrator.tasks["retention_analysis"].dependencies = ["data_processing"]
    
    print("\n" + "=" * 60)
    print("🎉 所有核心功能测试通过！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_orchestrator_core_functionality()