"""
增强版智能体编排器测试

测试集成了通信和错误处理功能的智能体编排器
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from config.agent_orchestrator import AgentOrchestrator, TaskStatus, AgentType
from config.agent_communication import MessageType, AgentStatus, RetryPolicy
from tools.data_storage_manager import DataStorageManager


class TestEnhancedOrchestrator:
    """测试增强版智能体编排器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.storage_manager = DataStorageManager()
        self.retry_policy = RetryPolicy(max_retries=2, base_delay=0.1)
        self.orchestrator = AgentOrchestrator(self.storage_manager, self.retry_policy)
    
    def teardown_method(self):
        """清理测试环境"""
        self.orchestrator.shutdown_communication()
    
    def test_orchestrator_initialization(self):
        """测试编排器初始化"""
        assert self.orchestrator.storage_manager is not None
        assert self.orchestrator.message_broker is not None
        assert self.orchestrator.error_handler is not None
        assert self.orchestrator.agent_monitor is not None
        assert len(self.orchestrator.agents) == 7  # 7个智能体
        assert len(self.orchestrator.tasks) == 7   # 7个默认任务
    
    def test_agent_registration_in_communication_system(self):
        """测试智能体在通信系统中的注册"""
        # 检查所有智能体都已注册到消息代理
        broker_stats = self.orchestrator.message_broker.get_statistics()
        assert broker_stats["registered_agents"] == 7
        
        # 检查所有智能体都已注册到监控器
        monitor_stats = self.orchestrator.agent_monitor.get_monitoring_statistics()
        assert monitor_stats["total_agents"] == 7
        
        # 检查智能体状态
        all_status = self.orchestrator.agent_monitor.get_all_agent_status()
        assert len(all_status) == 7
        
        for agent_type in AgentType:
            agent_id = agent_type.value
            assert agent_id in all_status
            assert all_status[agent_id].status == AgentStatus.IDLE
    
    def test_send_message_to_agent(self):
        """测试向智能体发送消息"""
        agent_id = AgentType.DATA_PROCESSOR.value
        payload = {"command": "start_processing", "file_path": "test.json"}
        
        success = self.orchestrator.send_message_to_agent(
            agent_id, MessageType.STATUS_UPDATE, payload
        )
        
        assert success == True
        
        # 检查消息队列
        queue_size = self.orchestrator.message_broker.get_queue_size(agent_id)
        assert queue_size == 1
        
        # 获取消息
        messages = self.orchestrator.message_broker.get_messages(agent_id, max_count=1)
        assert len(messages) == 1
        assert messages[0].sender_id == "orchestrator"
        assert messages[0].receiver_id == agent_id
        assert messages[0].message_type == MessageType.STATUS_UPDATE
        assert messages[0].payload == payload
    
    def test_broadcast_message(self):
        """测试广播消息"""
        payload = {"command": "shutdown", "reason": "maintenance"}
        
        success_count = self.orchestrator.broadcast_message(MessageType.SHUTDOWN, payload)
        
        # 应该发送给所有订阅了SHUTDOWN消息的智能体
        assert success_count >= 0  # 取决于有多少智能体订阅了SHUTDOWN消息
        
        # 检查消息历史
        broker_stats = self.orchestrator.message_broker.get_statistics()
        assert broker_stats["message_history_size"] > 0
    
    @patch('agents.data_processing_agent.DataProcessingAgent.process_ga4_data')
    def test_execute_single_task_success(self, mock_process_data):
        """测试成功执行单个任务"""
        # 模拟成功的数据处理
        mock_process_data.return_value = {
            "status": "success",
            "events_count": 1000,
            "users_count": 100,
            "sessions_count": 200
        }
        
        # 执行数据处理任务
        result = self.orchestrator.execute_single_task("data_processing", file_path="test.json")
        
        assert result.status == TaskStatus.COMPLETED
        assert result.task_id == "data_processing"
        assert result.agent_type == AgentType.DATA_PROCESSOR
        assert result.result_data["status"] == "success"
        assert result.execution_time > 0
        assert result.error_message is None
        
        # 检查智能体状态
        agent_id = AgentType.DATA_PROCESSOR.value
        status = self.orchestrator.agent_monitor.get_agent_status(agent_id)
        assert status.status == AgentStatus.COMPLETED
        assert status.current_task == "data_processing"
        assert status.progress == 1.0
    
    @patch('agents.data_processing_agent.DataProcessingAgent.process_ga4_data')
    def test_execute_single_task_with_retry(self, mock_process_data):
        """测试任务执行失败后的重试机制"""
        # 模拟前两次失败，第三次成功
        mock_process_data.side_effect = [
            ConnectionError("Connection failed"),
            ConnectionError("Connection failed again"),
            {
                "status": "success",
                "events_count": 1000,
                "users_count": 100,
                "sessions_count": 200
            }
        ]
        
        # 执行任务
        result = self.orchestrator.execute_single_task("data_processing", file_path="test.json")
        
        # 应该最终成功
        assert result.status == TaskStatus.COMPLETED
        assert result.result_data["status"] == "success"
        
        # 检查调用次数（应该重试了2次）
        assert mock_process_data.call_count == 3
        
        # 检查错误历史
        error_stats = self.orchestrator.error_handler.get_error_statistics()
        assert error_stats["total_errors"] == 2  # 前两次失败
    
    @patch('agents.data_processing_agent.DataProcessingAgent.process_ga4_data')
    def test_execute_single_task_final_failure(self, mock_process_data):
        """测试任务最终失败"""
        # 模拟持续失败
        mock_process_data.side_effect = ConnectionError("Persistent connection error")
        
        # 执行任务
        result = self.orchestrator.execute_single_task("data_processing", file_path="test.json")
        
        # 应该最终失败
        assert result.status == TaskStatus.FAILED
        assert result.error_message == "Persistent connection error"
        
        # 检查重试次数（最大重试次数 + 1）
        assert mock_process_data.call_count == 3  # 1次初始尝试 + 2次重试
        
        # 检查智能体状态
        agent_id = AgentType.DATA_PROCESSOR.value
        status = self.orchestrator.agent_monitor.get_agent_status(agent_id)
        assert status.status == AgentStatus.ERROR
    
    @patch('agents.data_processing_agent.DataProcessingAgent.process_ga4_data')
    def test_execute_single_task_non_retryable_error(self, mock_process_data):
        """测试不可重试的错误"""
        # 模拟不可重试的错误（ValueError）
        mock_process_data.side_effect = ValueError("Invalid data format")
        
        # 执行任务
        result = self.orchestrator.execute_single_task("data_processing", file_path="test.json")
        
        # 应该立即失败，不重试
        assert result.status == TaskStatus.FAILED
        assert result.error_message == "Invalid data format"
        
        # 检查只调用了一次（没有重试）
        assert mock_process_data.call_count == 1
    
    def test_task_dependency_check(self):
        """测试任务依赖检查"""
        # 尝试执行依赖于data_processing的任务，但data_processing未完成
        result = self.orchestrator.execute_single_task("event_analysis")
        
        assert result.status == TaskStatus.FAILED
        assert "依赖任务未完成" in result.error_message
    
    @patch('agents.data_processing_agent.DataProcessingAgent.process_ga4_data')
    @patch('agents.event_analysis_agent.EventAnalysisAgent.comprehensive_event_analysis')
    def test_task_execution_with_dependencies(self, mock_event_analysis, mock_process_data):
        """测试带依赖的任务执行"""
        # 模拟数据处理成功
        mock_process_data.return_value = {"status": "success", "events_count": 1000}
        
        # 模拟事件分析成功
        mock_event_analysis.return_value = {"status": "success", "key_events": ["login", "purchase"]}
        
        # 先执行数据处理任务
        data_result = self.orchestrator.execute_single_task("data_processing", file_path="test.json")
        assert data_result.status == TaskStatus.COMPLETED
        
        # 再执行事件分析任务
        event_result = self.orchestrator.execute_single_task("event_analysis")
        assert event_result.status == TaskStatus.COMPLETED
        assert event_result.result_data["status"] == "success"
    
    def test_get_communication_statistics(self):
        """测试获取通信统计信息"""
        stats = self.orchestrator.get_communication_statistics()
        
        assert "message_broker" in stats
        assert "error_handler" in stats
        assert "agent_monitor" in stats
        
        # 检查消息代理统计
        broker_stats = stats["message_broker"]
        assert "registered_agents" in broker_stats
        assert "total_queues" in broker_stats
        assert "queue_sizes" in broker_stats
        
        # 检查错误处理统计
        error_stats = stats["error_handler"]
        assert "total_errors" in error_stats
        assert "resolved_errors" in error_stats
        assert "resolution_rate" in error_stats
        
        # 检查监控统计
        monitor_stats = stats["agent_monitor"]
        assert "total_agents" in monitor_stats
        assert "status_distribution" in monitor_stats
    
    def test_agent_status_monitoring_during_task_execution(self):
        """测试任务执行期间的智能体状态监控"""
        with patch('agents.data_processing_agent.DataProcessingAgent.process_ga4_data') as mock_process:
            # 模拟长时间运行的任务
            def slow_process(file_path):
                time.sleep(0.1)  # 模拟处理时间
                return {"status": "success", "events_count": 1000}
            
            mock_process.side_effect = slow_process
            
            # 执行任务
            result = self.orchestrator.execute_single_task("data_processing", file_path="test.json")
            
            assert result.status == TaskStatus.COMPLETED
            
            # 检查状态历史
            agent_id = AgentType.DATA_PROCESSOR.value
            status_history = self.orchestrator.agent_monitor.status_history[agent_id]
            
            # 应该有多个状态更新记录
            assert len(status_history) > 1
            
            # 检查状态变化序列
            status_values = [record["new_status"] for record in status_history]
            assert "processing" in status_values
            assert "completed" in status_values
    
    def test_error_handler_registration(self):
        """测试错误处理器注册"""
        # 检查是否注册了默认的错误处理器
        error_handler = self.orchestrator.error_handler
        
        # 测试连接错误处理
        connection_error = ConnectionError("Test connection error")
        error_info = error_handler.handle_error("test_agent", connection_error)
        
        assert error_info.error_type == "ConnectionError"
        assert not error_info.resolved  # 默认处理器返回False，表示需要重试
        
        # 测试数据错误处理
        value_error = ValueError("Test value error")
        error_info = error_handler.handle_error("test_agent", value_error)
        
        assert error_info.error_type == "ValueError"
        assert error_info.resolved  # 数据错误处理器返回True，表示已解决
    
    def test_shutdown_communication(self):
        """测试关闭通信系统"""
        # 发送一些消息
        self.orchestrator.send_message_to_agent(
            AgentType.DATA_PROCESSOR.value, 
            MessageType.STATUS_UPDATE, 
            {"test": "message"}
        )
        
        # 关闭通信系统
        self.orchestrator.shutdown_communication()
        
        # 检查监控是否停止
        assert not self.orchestrator.agent_monitor.monitoring
        
        # 检查智能体是否被注销
        broker_stats = self.orchestrator.message_broker.get_statistics()
        assert broker_stats["registered_agents"] == 0
        
        monitor_stats = self.orchestrator.agent_monitor.get_monitoring_statistics()
        assert monitor_stats["total_agents"] == 0


class TestMessageHandling:
    """测试消息处理"""
    
    def setup_method(self):
        """设置测试环境"""
        self.orchestrator = AgentOrchestrator()
    
    def teardown_method(self):
        """清理测试环境"""
        self.orchestrator.shutdown_communication()
    
    def test_handle_status_update_message(self):
        """测试处理状态更新消息"""
        from config.agent_communication import Message
        
        message = Message(
            message_id="test_status_msg",
            sender_id="agent_1",
            receiver_id="orchestrator",
            message_type=MessageType.STATUS_UPDATE,
            payload={
                "status": "processing",
                "current_task": "test_task",
                "progress": 0.5,
                "metadata": {"test": "data"}
            },
            timestamp=datetime.now()
        )
        
        result = self.orchestrator._handle_agent_message(message)
        
        assert result["status"] == "processed"
        assert result["message_id"] == "test_status_msg"
        
        # 检查智能体状态是否更新
        status = self.orchestrator.agent_monitor.get_agent_status("agent_1")
        assert status.status == AgentStatus.PROCESSING
        assert status.current_task == "test_task"
        assert status.progress == 0.5
        assert status.metadata == {"test": "data"}
    
    def test_handle_error_notification_message(self):
        """测试处理错误通知消息"""
        from config.agent_communication import Message
        
        message = Message(
            message_id="test_error_msg",
            sender_id="agent_1",
            receiver_id="orchestrator",
            message_type=MessageType.ERROR_NOTIFICATION,
            payload={
                "error_message": "Test error occurred",
                "context": {"operation": "data_processing", "retry_count": 1}
            },
            timestamp=datetime.now()
        )
        
        result = self.orchestrator._handle_agent_message(message)
        
        assert result["status"] == "processed"
        
        # 检查错误是否被记录
        error_stats = self.orchestrator.error_handler.get_error_statistics()
        assert error_stats["total_errors"] == 1
    
    def test_handle_data_request_message(self):
        """测试处理数据请求消息"""
        from config.agent_communication import Message
        
        # 先添加一些测试数据
        self.orchestrator.task_results["test_task"] = Mock()
        self.orchestrator.task_results["test_task"].result_data = {"test": "result"}
        
        message = Message(
            message_id="test_data_req_msg",
            sender_id="agent_1",
            receiver_id="orchestrator",
            message_type=MessageType.DATA_REQUEST,
            payload={
                "data_type": "task_results",
                "filters": {}
            },
            timestamp=datetime.now()
        )
        
        result = self.orchestrator._handle_agent_message(message)
        
        assert result["status"] == "processed"
        
        # 检查是否发送了响应消息
        messages = self.orchestrator.message_broker.get_messages("agent_1", max_count=1)
        assert len(messages) == 1
        
        response_message = messages[0]
        assert response_message.message_type == MessageType.DATA_RESPONSE
        assert response_message.sender_id == "orchestrator"
        assert response_message.receiver_id == "agent_1"
        assert "data" in response_message.payload
    
    def test_handle_heartbeat_message(self):
        """测试处理心跳消息"""
        from config.agent_communication import Message
        
        # 注册智能体
        self.orchestrator.agent_monitor.register_agent("agent_1")
        old_heartbeat = self.orchestrator.agent_monitor.get_agent_status("agent_1").last_heartbeat
        
        time.sleep(0.1)  # 等待一小段时间
        
        message = Message(
            message_id="test_heartbeat_msg",
            sender_id="agent_1",
            receiver_id="orchestrator",
            message_type=MessageType.HEARTBEAT,
            payload={},
            timestamp=datetime.now()
        )
        
        result = self.orchestrator._handle_agent_message(message)
        
        assert result["status"] == "processed"
        
        # 检查心跳时间是否更新
        new_heartbeat = self.orchestrator.agent_monitor.get_agent_status("agent_1").last_heartbeat
        assert new_heartbeat > old_heartbeat


if __name__ == "__main__":
    pytest.main([__file__, "-v"])