"""
智能体编排器测试模块

测试AgentOrchestrator类的功能，包括：
- 智能体初始化和配置
- 任务依赖关系管理
- 工作流程执行
- 结果传递和状态监控
"""

import pytest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from config.agent_orchestrator import (
    AgentOrchestrator, 
    AgentTaskDefinition, 
    TaskResult, 
    TaskStatus, 
    AgentType
)
from tools.data_storage_manager import DataStorageManager


class TestAgentOrchestrator:
    """智能体编排器测试类"""
    
    @pytest.fixture
    def storage_manager(self):
        """创建测试用的存储管理器"""
        return DataStorageManager()
    
    @pytest.fixture
    def orchestrator(self, storage_manager):
        """创建测试用的编排器"""
        with patch('config.agent_orchestrator.DataProcessingAgent'), \
             patch('config.agent_orchestrator.EventAnalysisAgent'), \
             patch('config.agent_orchestrator.RetentionAnalysisAgent'), \
             patch('config.agent_orchestrator.ConversionAnalysisAgent'), \
             patch('config.agent_orchestrator.UserSegmentationAgent'), \
             patch('config.agent_orchestrator.PathAnalysisAgent'), \
             patch('config.agent_orchestrator.ReportGenerationAgent'):
            return AgentOrchestrator(storage_manager)
    
    def test_orchestrator_initialization(self, orchestrator):
        """测试编排器初始化"""
        # 验证智能体初始化
        assert len(orchestrator.agents) == 7
        assert AgentType.DATA_PROCESSOR in orchestrator.agents
        assert AgentType.EVENT_ANALYST in orchestrator.agents
        assert AgentType.RETENTION_ANALYST in orchestrator.agents
        assert AgentType.CONVERSION_ANALYST in orchestrator.agents
        assert AgentType.SEGMENTATION_ANALYST in orchestrator.agents
        assert AgentType.PATH_ANALYST in orchestrator.agents
        assert AgentType.REPORT_GENERATOR in orchestrator.agents
        
        # 验证默认任务定义
        assert len(orchestrator.tasks) == 7
        assert "data_processing" in orchestrator.tasks
        assert "event_analysis" in orchestrator.tasks
        assert "retention_analysis" in orchestrator.tasks
        assert "conversion_analysis" in orchestrator.tasks
        assert "segmentation_analysis" in orchestrator.tasks
        assert "path_analysis" in orchestrator.tasks
        assert "report_generation" in orchestrator.tasks
        
        # 验证初始状态
        assert len(orchestrator.task_results) == 0
        assert len(orchestrator.execution_history) == 0
        assert orchestrator.crew is None
    
    def test_add_custom_task(self, orchestrator):
        """测试添加自定义任务"""
        custom_task = AgentTaskDefinition(
            task_id="custom_analysis",
            agent_type=AgentType.EVENT_ANALYST,
            description="自定义分析任务",
            expected_output="自定义分析结果",
            dependencies=["data_processing"],
            parameters={"custom_param": "value"},
            priority=5
        )
        
        orchestrator.add_custom_task(custom_task)
        
        assert "custom_analysis" in orchestrator.tasks
        assert orchestrator.tasks["custom_analysis"].task_id == "custom_analysis"
        assert orchestrator.tasks["custom_analysis"].agent_type == AgentType.EVENT_ANALYST
        assert orchestrator.tasks["custom_analysis"].priority == 5
    
    def test_remove_task(self, orchestrator):
        """测试移除任务"""
        # 确认任务存在
        assert "event_analysis" in orchestrator.tasks
        
        # 移除任务
        orchestrator.remove_task("event_analysis")
        
        # 确认任务已移除
        assert "event_analysis" not in orchestrator.tasks
    
    def test_task_execution_order(self, orchestrator):
        """测试任务执行顺序计算"""
        execution_order = orchestrator.get_task_execution_order()
        
        # 验证数据处理任务是第一个
        assert execution_order[0] == "data_processing"
        
        # 验证报告生成任务是最后一个
        assert execution_order[-1] == "report_generation"
        
        # 验证依赖关系正确
        data_processing_index = execution_order.index("data_processing")
        event_analysis_index = execution_order.index("event_analysis")
        report_generation_index = execution_order.index("report_generation")
        
        assert data_processing_index < event_analysis_index
        assert event_analysis_index < report_generation_index
    
    def test_task_execution_order_with_circular_dependency(self, orchestrator):
        """测试循环依赖检测"""
        # 创建循环依赖
        orchestrator.tasks["event_analysis"].dependencies.append("retention_analysis")
        orchestrator.tasks["retention_analysis"].dependencies.append("event_analysis")
        
        # 应该抛出循环依赖异常
        with pytest.raises(ValueError, match="检测到循环依赖"):
            orchestrator.get_task_execution_order()
    
    def test_create_crewai_tasks(self, orchestrator):
        """测试创建CrewAI任务"""
        test_file_path = "/path/to/test/file.ndjson"
        
        with patch('config.agent_orchestrator.Task') as mock_task:
            tasks = orchestrator.create_crewai_tasks(test_file_path)
            
            # 验证任务数量
            assert len(tasks) == 7
            
            # 验证Task构造函数被调用
            assert mock_task.call_count == 7
            
            # 验证数据处理任务的文件路径参数
            assert orchestrator.tasks["data_processing"].parameters["file_path"] == test_file_path
    
    @patch('config.agent_orchestrator.Crew')
    def test_create_crew_sequential(self, mock_crew, orchestrator):
        """测试创建顺序执行的CrewAI团队"""
        test_file_path = "/path/to/test/file.ndjson"
        
        with patch.object(orchestrator, 'create_crewai_tasks') as mock_create_tasks:
            mock_create_tasks.return_value = []
            
            crew = orchestrator.create_crew(test_file_path, "sequential")
            
            # 验证Crew构造函数被调用
            mock_crew.assert_called_once()
            call_args = mock_crew.call_args[1]
            
            assert len(call_args['agents']) == 7
            assert call_args['process'].name == 'sequential'
            assert call_args['verbose'] is True
            assert call_args['memory'] is True
    
    @patch('config.agent_orchestrator.Crew')
    def test_create_crew_hierarchical(self, mock_crew, orchestrator):
        """测试创建层次化执行的CrewAI团队"""
        test_file_path = "/path/to/test/file.ndjson"
        
        with patch.object(orchestrator, 'create_crewai_tasks') as mock_create_tasks, \
             patch('config.agent_orchestrator.get_llm') as mock_get_llm:
            mock_create_tasks.return_value = []
            mock_llm = Mock()
            mock_get_llm.return_value = mock_llm
            
            crew = orchestrator.create_crew(test_file_path, "hierarchical")
            
            # 验证Crew构造函数被调用
            mock_crew.assert_called_once()
            call_args = mock_crew.call_args[1]
            
            assert len(call_args['agents']) == 7
            assert call_args['process'].name == 'hierarchical'
            assert call_args['manager_llm'] == mock_llm
    
    def test_execute_single_task_success(self, orchestrator):
        """测试成功执行单个任务"""
        # Mock数据处理智能体
        mock_agent = Mock()
        mock_agent.process_ga4_data.return_value = {
            "status": "success",
            "data": {"processed": True}
        }
        orchestrator.agents[AgentType.DATA_PROCESSOR] = mock_agent
        
        # 执行任务
        result = orchestrator.execute_single_task("data_processing", file_path="/test/file.ndjson")
        
        # 验证结果
        assert result.task_id == "data_processing"
        assert result.agent_type == AgentType.DATA_PROCESSOR
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["status"] == "success"
        assert result.error_message is None
        assert result.execution_time > 0
        
        # 验证任务结果被保存
        assert "data_processing" in orchestrator.task_results
        assert orchestrator.task_results["data_processing"] == result
    
    def test_execute_single_task_failure(self, orchestrator):
        """测试执行单个任务失败"""
        # Mock数据处理智能体抛出异常
        mock_agent = Mock()
        mock_agent.process_ga4_data.side_effect = Exception("处理失败")
        orchestrator.agents[AgentType.DATA_PROCESSOR] = mock_agent
        
        # 执行任务
        result = orchestrator.execute_single_task("data_processing", file_path="/test/file.ndjson")
        
        # 验证结果
        assert result.task_id == "data_processing"
        assert result.status == TaskStatus.FAILED
        assert result.error_message == "处理失败"
    
    def test_execute_single_task_missing_dependency(self, orchestrator):
        """测试执行缺少依赖的任务"""
        # 尝试执行依赖数据处理的事件分析任务
        with pytest.raises(ValueError, match="依赖任务未完成"):
            orchestrator.execute_single_task("event_analysis")
    
    def test_execute_workflow_success(self, orchestrator):
        """测试成功执行完整工作流程"""
        test_file_path = "/test/file.ndjson"
        
        # Mock CrewAI团队
        mock_crew = Mock()
        mock_crew.kickoff.return_value = {"analysis_complete": True}
        
        with patch.object(orchestrator, 'create_crew') as mock_create_crew:
            mock_create_crew.return_value = mock_crew
            
            result = orchestrator.execute_workflow(test_file_path)
            
            # 验证结果
            assert result["status"] == "success"
            assert result["execution_time"] > 0
            assert "execution_id" in result
            assert result["result"]["analysis_complete"] is True
            
            # 验证执行历史被记录
            assert len(orchestrator.execution_history) == 1
            history_record = orchestrator.execution_history[0]
            assert history_record["file_path"] == test_file_path
            assert history_record["status"] == "completed"
    
    def test_execute_workflow_failure(self, orchestrator):
        """测试工作流程执行失败"""
        test_file_path = "/test/file.ndjson"
        
        with patch.object(orchestrator, 'create_crew') as mock_create_crew:
            mock_create_crew.side_effect = Exception("团队创建失败")
            
            result = orchestrator.execute_workflow(test_file_path)
            
            # 验证结果
            assert result["status"] == "error"
            assert result["error_message"] == "团队创建失败"
            assert "execution_id" in result
            
            # 验证失败记录被保存
            assert len(orchestrator.execution_history) == 1
            history_record = orchestrator.execution_history[0]
            assert history_record["status"] == "failed"
    
    def test_get_execution_status(self, orchestrator):
        """测试获取执行状态"""
        # 添加一些任务结果
        orchestrator.task_results["task1"] = TaskResult(
            task_id="task1",
            agent_type=AgentType.DATA_PROCESSOR,
            status=TaskStatus.COMPLETED,
            result_data={},
            execution_time=1.5
        )
        
        orchestrator.task_results["task2"] = TaskResult(
            task_id="task2",
            agent_type=AgentType.EVENT_ANALYST,
            status=TaskStatus.FAILED,
            result_data={},
            execution_time=0.5,
            error_message="分析失败"
        )
        
        status = orchestrator.get_execution_status()
        
        # 验证状态信息
        assert status["total_tasks"] == 7  # 默认任务数量
        assert status["completed_tasks"] == 1
        assert status["failed_tasks"] == 1
        assert status["pending_tasks"] == 5
        assert status["completion_rate"] == 1/7
        
        # 验证任务结果详情
        assert "task1" in status["task_results"]
        assert status["task_results"]["task1"]["status"] == "completed"
        assert status["task_results"]["task2"]["status"] == "failed"
        assert status["task_results"]["task2"]["error_message"] == "分析失败"
    
    def test_reset_execution_state(self, orchestrator):
        """测试重置执行状态"""
        # 添加一些任务结果
        orchestrator.task_results["task1"] = TaskResult(
            task_id="task1",
            agent_type=AgentType.DATA_PROCESSOR,
            status=TaskStatus.COMPLETED,
            result_data={},
            execution_time=1.0
        )
        
        # 确认有任务结果
        assert len(orchestrator.task_results) == 1
        
        # 重置状态
        orchestrator.reset_execution_state()
        
        # 验证状态已重置
        assert len(orchestrator.task_results) == 0
    
    def test_export_configuration(self, orchestrator):
        """测试导出配置"""
        # 添加执行历史
        orchestrator.execution_history.append({
            "execution_id": "test_exec",
            "status": "completed"
        })
        
        config = orchestrator.export_configuration()
        
        # 验证配置内容
        assert "tasks" in config
        assert "agents" in config
        assert "execution_history" in config
        
        assert len(config["tasks"]) == 7
        assert len(config["agents"]) == 7
        assert len(config["execution_history"]) == 1
        
        # 验证任务配置结构
        task_config = config["tasks"]["data_processing"]
        assert task_config["task_id"] == "data_processing"
        assert task_config["agent_type"] == "AgentType.DATA_PROCESSOR"
        assert task_config["priority"] == 1
    
    def test_import_configuration(self, orchestrator):
        """测试导入配置"""
        # 准备测试配置
        test_config = {
            "tasks": {
                "custom_task": {
                    "task_id": "custom_task",
                    "agent_type": AgentType.EVENT_ANALYST,
                    "description": "自定义任务",
                    "expected_output": "自定义输出",
                    "dependencies": [],
                    "parameters": {},
                    "priority": 1,
                    "timeout": 300,
                    "retry_count": 2
                }
            },
            "execution_history": [
                {
                    "execution_id": "imported_exec",
                    "status": "completed"
                }
            ]
        }
        
        # 导入配置
        orchestrator.import_configuration(test_config)
        
        # 验证任务配置被导入
        assert "custom_task" in orchestrator.tasks
        assert orchestrator.tasks["custom_task"].task_id == "custom_task"
        assert orchestrator.tasks["custom_task"].agent_type == AgentType.EVENT_ANALYST
        
        # 验证执行历史被导入
        assert len(orchestrator.execution_history) == 1
        assert orchestrator.execution_history[0]["execution_id"] == "imported_exec"


class TestAgentTaskDefinition:
    """智能体任务定义测试类"""
    
    def test_task_definition_creation(self):
        """测试任务定义创建"""
        task_def = AgentTaskDefinition(
            task_id="test_task",
            agent_type=AgentType.EVENT_ANALYST,
            description="测试任务",
            expected_output="测试输出",
            dependencies=["dep1", "dep2"],
            parameters={"param1": "value1"},
            priority=2,
            timeout=600,
            retry_count=3
        )
        
        assert task_def.task_id == "test_task"
        assert task_def.agent_type == AgentType.EVENT_ANALYST
        assert task_def.description == "测试任务"
        assert task_def.expected_output == "测试输出"
        assert task_def.dependencies == ["dep1", "dep2"]
        assert task_def.parameters == {"param1": "value1"}
        assert task_def.priority == 2
        assert task_def.timeout == 600
        assert task_def.retry_count == 3
    
    def test_task_definition_defaults(self):
        """测试任务定义默认值"""
        task_def = AgentTaskDefinition(
            task_id="test_task",
            agent_type=AgentType.EVENT_ANALYST,
            description="测试任务",
            expected_output="测试输出",
            dependencies=[],
            parameters={}
        )
        
        assert task_def.priority == 1
        assert task_def.timeout == 300
        assert task_def.retry_count == 2


class TestTaskResult:
    """任务结果测试类"""
    
    def test_task_result_creation(self):
        """测试任务结果创建"""
        result_data = {"key": "value"}
        
        task_result = TaskResult(
            task_id="test_task",
            agent_type=AgentType.EVENT_ANALYST,
            status=TaskStatus.COMPLETED,
            result_data=result_data,
            execution_time=1.5,
            error_message=None
        )
        
        assert task_result.task_id == "test_task"
        assert task_result.agent_type == AgentType.EVENT_ANALYST
        assert task_result.status == TaskStatus.COMPLETED
        assert task_result.result_data == result_data
        assert task_result.execution_time == 1.5
        assert task_result.error_message is None
        assert task_result.timestamp is not None
    
    def test_task_result_with_error(self):
        """测试带错误的任务结果"""
        task_result = TaskResult(
            task_id="failed_task",
            agent_type=AgentType.DATA_PROCESSOR,
            status=TaskStatus.FAILED,
            result_data={},
            execution_time=0.5,
            error_message="任务执行失败"
        )
        
        assert task_result.status == TaskStatus.FAILED
        assert task_result.error_message == "任务执行失败"


if __name__ == "__main__":
    pytest.main([__file__])