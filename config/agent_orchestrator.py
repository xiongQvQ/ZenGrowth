"""
CrewAI智能体团队编排器

该模块实现智能体团队的编排和协作，包括：
- 智能体团队配置和初始化
- 任务依赖和协作流程定义
- 智能体任务分配和结果传递
- 团队执行状态监控
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Try to import CrewAI components, handle version compatibility issues
try:
    from crewai import Agent, Task, Crew, Process
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except (ImportError, TypeError) as e:
    logging.warning(f"CrewAI not fully available: {e}. Some features may be limited.")
    CREWAI_AVAILABLE = False
    
    # Create mock classes for compatibility
    class BaseTool:
        def __init__(self):
            self.name = ""
            self.description = ""
    
    class Agent:
        def __init__(self, **kwargs):
            pass
    
    class Task:
        def __init__(self, **kwargs):
            pass
    
    class Crew:
        def __init__(self, **kwargs):
            pass
        
        def kickoff(self, inputs=None):
            return {"status": "mock_execution", "inputs": inputs}
    
    class Process:
        sequential = "sequential"
        hierarchical = "hierarchical"

from agents.data_processing_agent import DataProcessingAgent
from agents.event_analysis_agent import EventAnalysisAgent
from agents.retention_analysis_agent import RetentionAnalysisAgent
from agents.conversion_analysis_agent import ConversionAnalysisAgent
from agents.user_segmentation_agent import UserSegmentationAgent
from agents.path_analysis_agent import PathAnalysisAgent
from agents.report_generation_agent import ReportGenerationAgent
from tools.data_storage_manager import DataStorageManager
from config.crew_config import get_llm
from utils.logger import setup_logger
from config.agent_communication import (
    MessageBroker, ErrorHandler, AgentMonitor, Message, MessageType, 
    AgentStatus, ErrorInfo, RetryPolicy
)

logger = setup_logger()


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
    dependencies: List[str]  # 依赖的任务ID列表
    parameters: Dict[str, Any]
    priority: int = 1  # 优先级，数字越小优先级越高
    timeout: int = 300  # 超时时间（秒）
    retry_count: int = 2  # 重试次数


class AgentOrchestrator:
    """智能体团队编排器"""
    
    def __init__(self, storage_manager: DataStorageManager = None, 
                 retry_policy: RetryPolicy = None):
        """
        初始化智能体编排器
        
        Args:
            storage_manager: 数据存储管理器
            retry_policy: 重试策略
        """
        self.storage_manager = storage_manager or DataStorageManager()
        self.agents = {}
        self.tasks = {}
        self.task_results = {}
        self.execution_history = []
        self.crew = None
        
        # 初始化通信和错误处理组件
        self.message_broker = MessageBroker()
        self.error_handler = ErrorHandler(retry_policy or RetryPolicy())
        self.agent_monitor = AgentMonitor()
        
        # 启动监控
        self.agent_monitor.start_monitoring()
        
        # 初始化智能体
        self._initialize_agents()
        
        # 定义默认任务流程
        self._define_default_workflow()
        
        # 注册错误处理器
        self._register_error_handlers()
        
        logger.info("智能体编排器初始化完成")
    
    def _initialize_agents(self):
        """初始化所有智能体"""
        try:
            logger.info("开始初始化智能体团队")
            
            # 初始化各个智能体
            self.agents[AgentType.DATA_PROCESSOR] = DataProcessingAgent()
            self.agents[AgentType.EVENT_ANALYST] = EventAnalysisAgent(self.storage_manager)
            self.agents[AgentType.RETENTION_ANALYST] = RetentionAnalysisAgent(self.storage_manager)
            self.agents[AgentType.CONVERSION_ANALYST] = ConversionAnalysisAgent(self.storage_manager)
            self.agents[AgentType.SEGMENTATION_ANALYST] = UserSegmentationAgent(self.storage_manager)
            self.agents[AgentType.PATH_ANALYST] = PathAnalysisAgent(self.storage_manager)
            self.agents[AgentType.REPORT_GENERATOR] = ReportGenerationAgent()
            
            # 注册智能体到通信系统
            for agent_type, agent in self.agents.items():
                agent_id = agent_type.value
                self.message_broker.register_agent(agent_id, self._handle_agent_message)
                self.agent_monitor.register_agent(agent_id)
                
                # 订阅相关消息类型
                self.message_broker.subscribe(agent_id, MessageType.DATA_REQUEST)
                self.message_broker.subscribe(agent_id, MessageType.STATUS_UPDATE)
                self.message_broker.subscribe(agent_id, MessageType.ERROR_NOTIFICATION)
            
            logger.info(f"成功初始化{len(self.agents)}个智能体")
            
        except Exception as e:
            error_info = self.error_handler.handle_error("orchestrator", e, 
                                                       {"operation": "agent_initialization"})
            logger.error(f"智能体初始化失败: {e}")
            raise
    
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
        
        logger.info(f"定义了{len(self.tasks)}个默认任务")
    
    def add_custom_task(self, task_definition: AgentTaskDefinition):
        """
        添加自定义任务
        
        Args:
            task_definition: 任务定义
        """
        self.tasks[task_definition.task_id] = task_definition
        logger.info(f"添加自定义任务: {task_definition.task_id}")
    
    def remove_task(self, task_id: str):
        """
        移除任务
        
        Args:
            task_id: 任务ID
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"移除任务: {task_id}")
    
    def get_task_execution_order(self) -> List[str]:
        """
        根据依赖关系和优先级计算任务执行顺序
        
        Returns:
            任务ID列表，按执行顺序排列
        """
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
        
        logger.info(f"任务执行顺序: {execution_order}")
        return execution_order
    
    def create_crewai_tasks(self, file_path: str = None) -> List[Task]:
        """
        创建CrewAI任务列表
        
        Args:
            file_path: GA4数据文件路径
            
        Returns:
            CrewAI任务列表
        """
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI不可用，返回空任务列表")
            return []
            
        crewai_tasks = []
        execution_order = self.get_task_execution_order()
        
        for task_id in execution_order:
            task_def = self.tasks[task_id]
            
            # 设置任务参数
            if task_id == "data_processing" and file_path:
                task_def.parameters["file_path"] = file_path
            
            # 创建CrewAI任务
            crewai_task = Task(
                description=task_def.description,
                expected_output=task_def.expected_output,
                agent=self.agents[task_def.agent_type].get_agent(),
                context=self._get_task_context(task_def),
                output_json=True,
                output_file=f"reports/{task_id}_result.json"
            )
            
            crewai_tasks.append(crewai_task)
        
        logger.info(f"创建了{len(crewai_tasks)}个CrewAI任务")
        return crewai_tasks
    
    def _get_task_context(self, task_def: AgentTaskDefinition) -> List[Task]:
        """
        获取任务上下文（依赖任务的结果）
        
        Args:
            task_def: 任务定义
            
        Returns:
            上下文任务列表
        """
        context_tasks = []
        
        for dep_task_id in task_def.dependencies:
            if dep_task_id in self.task_results:
                # 如果依赖任务已完成，将其结果作为上下文
                context_tasks.append(self.task_results[dep_task_id])
        
        return context_tasks
    
    def create_crew(self, file_path: str = None, process_type: str = "sequential") -> Crew:
        """
        创建CrewAI团队
        
        Args:
            file_path: GA4数据文件路径
            process_type: 执行流程类型 ("sequential" 或 "hierarchical")
            
        Returns:
            CrewAI团队实例
        """
        try:
            logger.info(f"创建CrewAI团队，流程类型: {process_type}")
            
            if not CREWAI_AVAILABLE:
                logger.warning("CrewAI不可用，返回模拟团队")
                self.crew = Crew()
                return self.crew
            
            # 创建任务列表
            tasks = self.create_crewai_tasks(file_path)
            
            # 获取所有智能体
            agents = [agent.get_agent() for agent in self.agents.values()]
            
            # 设置流程类型
            if process_type == "hierarchical":
                process = Process.hierarchical
                manager_llm = get_llm()
            else:
                process = Process.sequential
                manager_llm = None
            
            # 创建团队
            self.crew = Crew(
                agents=agents,
                tasks=tasks,
                process=process,
                manager_llm=manager_llm,
                verbose=True,
                memory=True,
                embedder={
                    "provider": "google",
                    "config": {
                        "model": "models/embedding-001"
                    }
                }
            )
            
            logger.info("CrewAI团队创建成功")
            return self.crew
            
        except Exception as e:
            logger.error(f"CrewAI团队创建失败: {e}")
            raise
    
    def execute_workflow(self, file_path: str, process_type: str = "sequential") -> Dict[str, Any]:
        """
        执行完整的分析工作流程
        
        Args:
            file_path: GA4数据文件路径
            process_type: 执行流程类型
            
        Returns:
            执行结果
        """
        try:
            start_time = datetime.now()
            logger.info(f"开始执行分析工作流程，文件: {file_path}")
            
            # 创建团队
            crew = self.create_crew(file_path, process_type)
            
            # 准备输入参数
            inputs = {
                "file_path": file_path,
                "analysis_timestamp": start_time.isoformat()
            }
            
            # 执行工作流程
            result = crew.kickoff(inputs=inputs)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 记录执行历史
            execution_record = {
                "execution_id": f"exec_{int(start_time.timestamp())}",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "execution_time": execution_time,
                "file_path": file_path,
                "process_type": process_type,
                "status": "completed",
                "result": result
            }
            
            self.execution_history.append(execution_record)
            
            logger.info(f"工作流程执行完成，耗时: {execution_time:.2f}秒")
            
            return {
                "status": "success",
                "execution_time": execution_time,
                "result": result,
                "execution_id": execution_record["execution_id"]
            }
            
        except Exception as e:
            logger.error(f"工作流程执行失败: {e}")
            
            # 记录失败的执行
            execution_record = {
                "execution_id": f"exec_{int(datetime.now().timestamp())}",
                "start_time": start_time.isoformat() if 'start_time' in locals() else None,
                "end_time": datetime.now().isoformat(),
                "file_path": file_path,
                "process_type": process_type,
                "status": "failed",
                "error_message": str(e)
            }
            
            self.execution_history.append(execution_record)
            
            return {
                "status": "error",
                "error_message": str(e),
                "execution_id": execution_record["execution_id"]
            }
    
    def execute_single_task(self, task_id: str, **kwargs) -> TaskResult:
        """
        执行单个任务（带错误处理和重试机制）
        
        Args:
            task_id: 任务ID
            **kwargs: 任务参数
            
        Returns:
            任务执行结果
        """
        retry_count = 0
        max_retries = kwargs.get("max_retries", 3)
        
        while retry_count <= max_retries:
            try:
                start_time = datetime.now()
                logger.info(f"开始执行任务: {task_id} (尝试 {retry_count + 1}/{max_retries + 1})")
                
                if task_id not in self.tasks:
                    raise ValueError(f"任务不存在: {task_id}")
                
                task_def = self.tasks[task_id]
                agent = self.agents[task_def.agent_type]
                agent_id = task_def.agent_type.value
                
                # 更新智能体状态
                self.agent_monitor.update_agent_status(
                    agent_id, AgentStatus.PROCESSING, task_id, 0.0
                )
                
                # 发送任务开始消息
                self.send_message_to_agent(agent_id, MessageType.STATUS_UPDATE, {
                    "status": "processing",
                    "task_id": task_id,
                    "retry_count": retry_count
                })
                
                # 检查依赖任务是否完成
                for dep_task_id in task_def.dependencies:
                    if dep_task_id not in self.task_results or \
                       self.task_results[dep_task_id].status != TaskStatus.COMPLETED:
                        raise ValueError(f"依赖任务未完成: {dep_task_id}")
                
                # 合并参数
                parameters = {**task_def.parameters, **kwargs}
                
                # 执行任务
                result_data = self._execute_task_with_monitoring(task_id, agent, parameters, agent_id)
                
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
                
                # 更新智能体状态
                final_status = AgentStatus.COMPLETED if task_result.status == TaskStatus.COMPLETED else AgentStatus.ERROR
                self.agent_monitor.update_agent_status(agent_id, final_status, task_id, 1.0)
                
                # 发送任务完成消息
                self.send_message_to_agent(agent_id, MessageType.TASK_COMPLETION, {
                    "task_id": task_id,
                    "status": task_result.status.value,
                    "execution_time": execution_time
                })
                
                logger.info(f"任务执行完成: {task_id}, 状态: {task_result.status.value}, 耗时: {execution_time:.2f}秒")
                
                return task_result
                
            except Exception as e:
                # 处理错误
                error_info = self.error_handler.handle_error(
                    task_def.agent_type.value, e, 
                    {"task_id": task_id, "retry_count": retry_count}
                )
                
                # 更新智能体状态
                self.agent_monitor.update_agent_status(
                    task_def.agent_type.value, AgentStatus.ERROR, task_id, 0.0,
                    {"error_id": error_info.error_id}
                )
                
                # 发送错误通知
                self.send_message_to_agent(task_def.agent_type.value, MessageType.ERROR_NOTIFICATION, {
                    "error_id": error_info.error_id,
                    "error_message": str(e),
                    "task_id": task_id,
                    "retry_count": retry_count
                })
                
                # 判断是否应该重试
                if retry_count < max_retries and self.error_handler.should_retry(error_info):
                    retry_count += 1
                    retry_delay = self.error_handler.get_retry_delay(retry_count)
                    
                    logger.warning(f"任务执行失败，将在 {retry_delay:.2f} 秒后重试: {task_id}, 错误: {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"任务执行最终失败: {task_id}, 错误: {e}")
                    
                    task_result = TaskResult(
                        task_id=task_id,
                        agent_type=task_def.agent_type,
                        status=TaskStatus.FAILED,
                        result_data={"error_id": error_info.error_id},
                        execution_time=0,
                        error_message=str(e),
                        timestamp=datetime.now()
                    )
                    
                    self.task_results[task_id] = task_result
                    return task_result
    
    def _execute_task_with_monitoring(self, task_id: str, agent: Any, 
                                    parameters: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """
        执行任务并监控进度
        
        Args:
            task_id: 任务ID
            agent: 智能体实例
            parameters: 任务参数
            agent_id: 智能体ID
            
        Returns:
            任务执行结果
        """
        # 根据任务类型执行相应的方法
        if task_id == "data_processing":
            # 更新进度
            self.agent_monitor.update_agent_status(agent_id, AgentStatus.PROCESSING, task_id, 0.2)
            result_data = agent.process_ga4_data(parameters.get("file_path"))
            
        elif task_id == "event_analysis":
            self.agent_monitor.update_agent_status(agent_id, AgentStatus.PROCESSING, task_id, 0.3)
            result_data = agent.comprehensive_event_analysis()
            
        elif task_id == "retention_analysis":
            self.agent_monitor.update_agent_status(agent_id, AgentStatus.PROCESSING, task_id, 0.4)
            result_data = agent.comprehensive_retention_analysis()
            
        elif task_id == "conversion_analysis":
            self.agent_monitor.update_agent_status(agent_id, AgentStatus.PROCESSING, task_id, 0.5)
            result_data = agent.comprehensive_conversion_analysis()
            
        elif task_id == "segmentation_analysis":
            self.agent_monitor.update_agent_status(agent_id, AgentStatus.PROCESSING, task_id, 0.6)
            result_data = agent.comprehensive_segmentation_analysis()
            
        elif task_id == "path_analysis":
            self.agent_monitor.update_agent_status(agent_id, AgentStatus.PROCESSING, task_id, 0.7)
            result_data = agent.comprehensive_path_analysis()
            
        elif task_id == "report_generation":
            self.agent_monitor.update_agent_status(agent_id, AgentStatus.PROCESSING, task_id, 0.8)
            # 收集所有分析结果
            analysis_results = {
                tid: result.result_data for tid, result in self.task_results.items()
                if result.status == TaskStatus.COMPLETED
            }
            result_data = agent.generate_comprehensive_report(analysis_results)
            
        else:
            raise ValueError(f"未知的任务类型: {task_id}")
        
        # 最终进度更新
        self.agent_monitor.update_agent_status(agent_id, AgentStatus.PROCESSING, task_id, 0.9)
        
        return result_data
    
    def get_execution_status(self) -> Dict[str, Any]:
        """
        获取执行状态
        
        Returns:
            执行状态信息
        """
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
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Returns:
            执行历史列表
        """
        return self.execution_history
    
    def reset_execution_state(self):
        """重置执行状态"""
        self.task_results.clear()
        logger.info("执行状态已重置")
    
    def export_configuration(self) -> Dict[str, Any]:
        """
        导出配置
        
        Returns:
            配置字典
        """
        return {
            "tasks": {
                task_id: asdict(task_def) 
                for task_id, task_def in self.tasks.items()
            },
            "agents": list(self.agents.keys()),
            "execution_history": self.execution_history
        }
    
    def import_configuration(self, config: Dict[str, Any]):
        """
        导入配置
        
        Args:
            config: 配置字典
        """
        # 导入任务配置
        if "tasks" in config:
            self.tasks = {
                task_id: AgentTaskDefinition(**task_data)
                for task_id, task_data in config["tasks"].items()
            }
        
        # 导入执行历史
        if "execution_history" in config:
            self.execution_history = config["execution_history"]
        
        logger.info("配置导入完成")
    
    def _register_error_handlers(self):
        """注册错误处理器"""
        def handle_connection_error(error_info: ErrorInfo) -> bool:
            """处理连接错误"""
            logger.info(f"尝试处理连接错误: {error_info.error_id}")
            # 实现连接重试逻辑
            return False  # 暂时返回False，表示需要重试
        
        def handle_timeout_error(error_info: ErrorInfo) -> bool:
            """处理超时错误"""
            logger.info(f"尝试处理超时错误: {error_info.error_id}")
            # 实现超时处理逻辑
            return False  # 暂时返回False，表示需要重试
        
        def handle_data_error(error_info: ErrorInfo) -> bool:
            """处理数据错误"""
            logger.info(f"尝试处理数据错误: {error_info.error_id}")
            # 数据错误通常不应该重试
            return True
        
        # 注册错误处理器
        self.error_handler.register_error_handler("ConnectionError", handle_connection_error)
        self.error_handler.register_error_handler("TimeoutError", handle_timeout_error)
        self.error_handler.register_error_handler("ValueError", handle_data_error)
        self.error_handler.register_error_handler("TypeError", handle_data_error)
        
        logger.info("错误处理器注册完成")
    
    def _handle_agent_message(self, message: Message) -> Any:
        """
        处理智能体消息
        
        Args:
            message: 接收到的消息
            
        Returns:
            处理结果
        """
        try:
            logger.debug(f"处理消息: {message.message_id} from {message.sender_id}")
            
            if message.message_type == MessageType.STATUS_UPDATE:
                # 处理状态更新消息
                payload = message.payload
                self.agent_monitor.update_agent_status(
                    message.sender_id,
                    AgentStatus(payload.get("status", "idle")),
                    payload.get("current_task"),
                    payload.get("progress"),
                    payload.get("metadata")
                )
                
            elif message.message_type == MessageType.ERROR_NOTIFICATION:
                # 处理错误通知消息
                payload = message.payload
                error_info = self.error_handler.handle_error(
                    message.sender_id,
                    Exception(payload.get("error_message", "Unknown error")),
                    payload.get("context", {})
                )
                
                # 如果需要重试，发送重试消息
                if self.error_handler.should_retry(error_info):
                    retry_delay = self.error_handler.get_retry_delay(
                        error_info.context.get("retry_count", 0)
                    )
                    logger.info(f"将在 {retry_delay:.2f} 秒后重试任务")
                
            elif message.message_type == MessageType.DATA_REQUEST:
                # 处理数据请求消息
                payload = message.payload
                requested_data = self._get_requested_data(payload)
                
                # 发送响应消息
                response_message = Message(
                    message_id=f"resp_{message.message_id}",
                    sender_id="orchestrator",
                    receiver_id=message.sender_id,
                    message_type=MessageType.DATA_RESPONSE,
                    payload={"data": requested_data},
                    timestamp=datetime.now()
                )
                
                self.message_broker.send_message(response_message)
            
            elif message.message_type == MessageType.HEARTBEAT:
                # 处理心跳消息
                self.agent_monitor.heartbeat(message.sender_id)
            
            return {"status": "processed", "message_id": message.message_id}
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            error_info = self.error_handler.handle_error("orchestrator", e, 
                                                       {"message_id": message.message_id})
            return {"status": "error", "error_id": error_info.error_id}
    
    def _get_requested_data(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取请求的数据
        
        Args:
            request_payload: 请求载荷
            
        Returns:
            请求的数据
        """
        data_type = request_payload.get("data_type")
        filters = request_payload.get("filters", {})
        
        try:
            if data_type == "events":
                return {"events": self.storage_manager.get_events(filters)}
            elif data_type == "users":
                return {"users": self.storage_manager.get_users(filters)}
            elif data_type == "sessions":
                return {"sessions": self.storage_manager.get_sessions(filters)}
            elif data_type == "task_results":
                return {"task_results": self.task_results}
            else:
                return {"error": f"Unknown data type: {data_type}"}
                
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            return {"error": str(e)}
    
    def send_message_to_agent(self, agent_id: str, message_type: MessageType, 
                            payload: Dict[str, Any]) -> bool:
        """
        向智能体发送消息
        
        Args:
            agent_id: 智能体ID
            message_type: 消息类型
            payload: 消息载荷
            
        Returns:
            是否发送成功
        """
        message = Message(
            message_id=f"msg_{int(time.time() * 1000)}",
            sender_id="orchestrator",
            receiver_id=agent_id,
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now()
        )
        
        return self.message_broker.send_message(message)
    
    def broadcast_message(self, message_type: MessageType, payload: Dict[str, Any]) -> int:
        """
        广播消息给所有智能体
        
        Args:
            message_type: 消息类型
            payload: 消息载荷
            
        Returns:
            成功发送的消息数量
        """
        message = Message(
            message_id=f"broadcast_{int(time.time() * 1000)}",
            sender_id="orchestrator",
            receiver_id="all",
            message_type=message_type,
            payload=payload,
            timestamp=datetime.now()
        )
        
        return self.message_broker.broadcast_message(message)
    
    def get_communication_statistics(self) -> Dict[str, Any]:
        """
        获取通信统计信息
        
        Returns:
            通信统计信息
        """
        return {
            "message_broker": self.message_broker.get_statistics(),
            "error_handler": self.error_handler.get_error_statistics(),
            "agent_monitor": self.agent_monitor.get_monitoring_statistics()
        }
    
    def shutdown_communication(self):
        """关闭通信系统"""
        try:
            # 发送关闭消息
            self.broadcast_message(MessageType.SHUTDOWN, {"reason": "orchestrator_shutdown"})
            
            # 停止监控
            self.agent_monitor.stop_monitoring()
            
            # 注销所有智能体
            for agent_type in self.agents.keys():
                agent_id = agent_type.value
                self.message_broker.unregister_agent(agent_id)
                self.agent_monitor.unregister_agent(agent_id)
            
            logger.info("通信系统已关闭")
            
        except Exception as e:
            logger.error(f"关闭通信系统失败: {e}")