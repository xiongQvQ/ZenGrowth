"""
智能体通信和错误处理测试

测试智能体间通信协议、错误处理和重试机制的功能
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from config.agent_communication import (
    MessageBroker, ErrorHandler, AgentMonitor, Message, MessageType,
    AgentStatus, ErrorInfo, ErrorSeverity, RetryPolicy
)


class TestMessage:
    """测试消息类"""
    
    def test_message_creation(self):
        """测试消息创建"""
        message = Message(
            message_id="test_msg_001",
            sender_id="agent_1",
            receiver_id="agent_2",
            message_type=MessageType.DATA_REQUEST,
            payload={"data_type": "events"},
            timestamp=datetime.now()
        )
        
        assert message.message_id == "test_msg_001"
        assert message.sender_id == "agent_1"
        assert message.receiver_id == "agent_2"
        assert message.message_type == MessageType.DATA_REQUEST
        assert message.payload == {"data_type": "events"}
        assert message.priority == 1
        assert message.retry_count == 0
        assert message.max_retries == 3
    
    def test_message_to_dict(self):
        """测试消息转换为字典"""
        timestamp = datetime.now()
        message = Message(
            message_id="test_msg_002",
            sender_id="agent_1",
            receiver_id="agent_2",
            message_type=MessageType.STATUS_UPDATE,
            payload={"status": "processing"},
            timestamp=timestamp
        )
        
        message_dict = message.to_dict()
        
        assert message_dict["message_id"] == "test_msg_002"
        assert message_dict["sender_id"] == "agent_1"
        assert message_dict["receiver_id"] == "agent_2"
        assert message_dict["message_type"] == "status_update"
        assert message_dict["payload"] == {"status": "processing"}
        assert message_dict["timestamp"] == timestamp.isoformat()
    
    def test_message_from_dict(self):
        """测试从字典创建消息"""
        timestamp = datetime.now()
        message_dict = {
            "message_id": "test_msg_003",
            "sender_id": "agent_1",
            "receiver_id": "agent_2",
            "message_type": "error_notification",
            "payload": {"error": "test error"},
            "timestamp": timestamp.isoformat(),
            "priority": 2,
            "retry_count": 1,
            "max_retries": 5,
            "timeout": 60.0
        }
        
        message = Message.from_dict(message_dict)
        
        assert message.message_id == "test_msg_003"
        assert message.sender_id == "agent_1"
        assert message.receiver_id == "agent_2"
        assert message.message_type == MessageType.ERROR_NOTIFICATION
        assert message.payload == {"error": "test error"}
        assert message.timestamp == timestamp
        assert message.priority == 2
        assert message.retry_count == 1
        assert message.max_retries == 5
        assert message.timeout == 60.0


class TestRetryPolicy:
    """测试重试策略"""
    
    def test_default_retry_policy(self):
        """测试默认重试策略"""
        policy = RetryPolicy()
        
        assert policy.max_retries == 3
        assert policy.base_delay == 1.0
        assert policy.max_delay == 60.0
        assert policy.backoff_factor == 2.0
        assert policy.jitter == True
    
    def test_get_delay(self):
        """测试获取延迟时间"""
        policy = RetryPolicy(base_delay=2.0, backoff_factor=2.0, jitter=False)
        
        assert policy.get_delay(0) == 2.0
        assert policy.get_delay(1) == 4.0
        assert policy.get_delay(2) == 8.0
        assert policy.get_delay(3) == 16.0
    
    def test_get_delay_with_max_limit(self):
        """测试延迟时间上限"""
        policy = RetryPolicy(base_delay=10.0, max_delay=20.0, backoff_factor=3.0, jitter=False)
        
        assert policy.get_delay(0) == 10.0
        assert policy.get_delay(1) == 20.0  # 30.0 被限制为 20.0
        assert policy.get_delay(2) == 20.0  # 90.0 被限制为 20.0
    
    def test_should_retry(self):
        """测试是否应该重试"""
        policy = RetryPolicy(max_retries=3)
        
        # 测试重试次数限制
        assert policy.should_retry(0, Exception("test")) == True
        assert policy.should_retry(2, Exception("test")) == True
        assert policy.should_retry(3, Exception("test")) == False
        assert policy.should_retry(5, Exception("test")) == False
        
        # 测试不可重试的错误类型
        assert policy.should_retry(0, ValueError("test")) == False
        assert policy.should_retry(0, TypeError("test")) == False
        assert policy.should_retry(0, KeyError("test")) == False
        
        # 测试可重试的错误类型
        assert policy.should_retry(0, ConnectionError("test")) == True
        assert policy.should_retry(0, TimeoutError("test")) == True


class TestMessageBroker:
    """测试消息代理"""
    
    def setup_method(self):
        """设置测试环境"""
        self.broker = MessageBroker()
        self.mock_handler = Mock()
    
    def test_register_agent(self):
        """测试注册智能体"""
        self.broker.register_agent("agent_1", self.mock_handler)
        
        assert "agent_1" in self.broker.message_handlers
        assert self.broker.message_handlers["agent_1"] == self.mock_handler
    
    def test_unregister_agent(self):
        """测试注销智能体"""
        self.broker.register_agent("agent_1", self.mock_handler)
        self.broker.unregister_agent("agent_1")
        
        assert "agent_1" not in self.broker.message_handlers
        assert "agent_1" not in self.broker.message_queues
    
    def test_subscribe_and_unsubscribe(self):
        """测试订阅和取消订阅"""
        self.broker.register_agent("agent_1", self.mock_handler)
        
        # 测试订阅
        self.broker.subscribe("agent_1", MessageType.DATA_REQUEST)
        assert "agent_1" in self.broker.subscribers[MessageType.DATA_REQUEST]
        
        # 测试取消订阅
        self.broker.unsubscribe("agent_1", MessageType.DATA_REQUEST)
        assert "agent_1" not in self.broker.subscribers[MessageType.DATA_REQUEST]
    
    def test_send_message(self):
        """测试发送消息"""
        self.broker.register_agent("agent_1", self.mock_handler)
        self.broker.register_agent("agent_2", self.mock_handler)
        
        message = Message(
            message_id="test_msg",
            sender_id="agent_1",
            receiver_id="agent_2",
            message_type=MessageType.DATA_REQUEST,
            payload={"test": "data"},
            timestamp=datetime.now()
        )
        
        result = self.broker.send_message(message)
        
        assert result == True
        assert len(self.broker.message_queues["agent_2"]) == 1
        assert self.broker.message_queues["agent_2"][0] == message
    
    def test_send_message_to_nonexistent_agent(self):
        """测试向不存在的智能体发送消息"""
        message = Message(
            message_id="test_msg",
            sender_id="agent_1",
            receiver_id="nonexistent_agent",
            message_type=MessageType.DATA_REQUEST,
            payload={"test": "data"},
            timestamp=datetime.now()
        )
        
        result = self.broker.send_message(message)
        
        assert result == False
    
    def test_broadcast_message(self):
        """测试广播消息"""
        # 注册多个智能体
        for i in range(3):
            agent_id = f"agent_{i}"
            self.broker.register_agent(agent_id, self.mock_handler)
            self.broker.subscribe(agent_id, MessageType.STATUS_UPDATE)
        
        message = Message(
            message_id="broadcast_msg",
            sender_id="agent_0",
            receiver_id="all",
            message_type=MessageType.STATUS_UPDATE,
            payload={"status": "completed"},
            timestamp=datetime.now()
        )
        
        success_count = self.broker.broadcast_message(message, exclude_sender=True)
        
        assert success_count == 2  # 排除发送者，应该发送给2个智能体
        assert len(self.broker.message_queues["agent_1"]) == 1
        assert len(self.broker.message_queues["agent_2"]) == 1
        assert len(self.broker.message_queues["agent_0"]) == 0  # 发送者被排除
    
    def test_get_messages(self):
        """测试获取消息"""
        self.broker.register_agent("agent_1", self.mock_handler)
        
        # 发送多条消息
        for i in range(5):
            message = Message(
                message_id=f"msg_{i}",
                sender_id="sender",
                receiver_id="agent_1",
                message_type=MessageType.DATA_REQUEST,
                payload={"index": i},
                timestamp=datetime.now()
            )
            self.broker.send_message(message)
        
        # 获取消息
        messages = self.broker.get_messages("agent_1", max_count=3)
        
        assert len(messages) == 3
        assert messages[0].payload["index"] == 0
        assert messages[1].payload["index"] == 1
        assert messages[2].payload["index"] == 2
        
        # 队列中应该还剩2条消息
        assert self.broker.get_queue_size("agent_1") == 2
    
    def test_clear_queue(self):
        """测试清空队列"""
        self.broker.register_agent("agent_1", self.mock_handler)
        
        # 发送消息
        message = Message(
            message_id="test_msg",
            sender_id="sender",
            receiver_id="agent_1",
            message_type=MessageType.DATA_REQUEST,
            payload={"test": "data"},
            timestamp=datetime.now()
        )
        self.broker.send_message(message)
        
        assert self.broker.get_queue_size("agent_1") == 1
        
        # 清空队列
        self.broker.clear_queue("agent_1")
        
        assert self.broker.get_queue_size("agent_1") == 0
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        # 注册智能体
        self.broker.register_agent("agent_1", self.mock_handler)
        self.broker.register_agent("agent_2", self.mock_handler)
        
        # 订阅消息类型
        self.broker.subscribe("agent_1", MessageType.DATA_REQUEST)
        self.broker.subscribe("agent_2", MessageType.DATA_REQUEST)
        self.broker.subscribe("agent_1", MessageType.STATUS_UPDATE)
        
        # 发送消息
        message = Message(
            message_id="test_msg",
            sender_id="sender",
            receiver_id="agent_1",
            message_type=MessageType.DATA_REQUEST,
            payload={"test": "data"},
            timestamp=datetime.now()
        )
        self.broker.send_message(message)
        
        stats = self.broker.get_statistics()
        
        assert stats["registered_agents"] == 2
        assert stats["total_queues"] == 2
        assert stats["queue_sizes"]["agent_1"] == 1
        assert stats["queue_sizes"]["agent_2"] == 0
        assert stats["subscribers"]["data_request"] == 2
        assert stats["subscribers"]["status_update"] == 1


class TestErrorHandler:
    """测试错误处理器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.error_handler = ErrorHandler()
    
    def test_handle_error(self):
        """测试处理错误"""
        error = ValueError("Test error")
        context = {"operation": "test_operation"}
        
        error_info = self.error_handler.handle_error("agent_1", error, context)
        
        assert error_info.agent_id == "agent_1"
        assert error_info.error_type == "ValueError"
        assert error_info.error_message == "Test error"
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.context == context
        assert error_info.resolved == False
        assert len(self.error_handler.error_history) == 1
    
    def test_determine_severity(self):
        """测试确定错误严重程度"""
        # 测试不同类型的错误
        critical_error = SystemError("Critical error")
        high_error = ConnectionError("High error")
        medium_error = ValueError("Medium error")
        low_error = RuntimeError("Low error")
        
        critical_info = self.error_handler.handle_error("agent", critical_error)
        high_info = self.error_handler.handle_error("agent", high_error)
        medium_info = self.error_handler.handle_error("agent", medium_error)
        low_info = self.error_handler.handle_error("agent", low_error)
        
        assert critical_info.severity == ErrorSeverity.CRITICAL
        assert high_info.severity == ErrorSeverity.HIGH
        assert medium_info.severity == ErrorSeverity.MEDIUM
        assert low_info.severity == ErrorSeverity.LOW
    
    def test_register_error_handler(self):
        """测试注册错误处理器"""
        def custom_handler(error_info):
            error_info.resolved = True
            return True
        
        self.error_handler.register_error_handler("ValueError", custom_handler)
        
        error = ValueError("Test error")
        error_info = self.error_handler.handle_error("agent_1", error)
        
        assert error_info.resolved == True
        assert error_info.resolution_notes == "由处理器 ValueError 解决"
    
    def test_should_retry(self):
        """测试是否应该重试"""
        error = ConnectionError("Connection failed")
        error_info = self.error_handler.handle_error("agent_1", error, {"retry_count": 1})
        
        # 未解决的错误应该重试
        assert self.error_handler.should_retry(error_info) == True
        
        # 已解决的错误不应该重试
        error_info.resolved = True
        assert self.error_handler.should_retry(error_info) == False
    
    def test_get_retry_delay(self):
        """测试获取重试延迟"""
        delay_0 = self.error_handler.get_retry_delay(0)
        delay_1 = self.error_handler.get_retry_delay(1)
        delay_2 = self.error_handler.get_retry_delay(2)
        
        # 延迟应该递增
        assert delay_1 > delay_0
        assert delay_2 > delay_1
    
    def test_get_error_statistics(self):
        """测试获取错误统计"""
        # 创建不同类型的错误
        errors = [
            ValueError("Error 1"),
            ValueError("Error 2"),
            ConnectionError("Error 3"),
            SystemError("Error 4")
        ]
        
        for error in errors:
            self.error_handler.handle_error("agent_1", error)
        
        # 解决一个错误
        self.error_handler.error_history[0].resolved = True
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats["total_errors"] == 4
        assert stats["resolved_errors"] == 1
        assert stats["error_types"]["ValueError"] == 2
        assert stats["error_types"]["ConnectionError"] == 1
        assert stats["error_types"]["SystemError"] == 1
        assert stats["severity_distribution"]["medium"] == 2
        assert stats["severity_distribution"]["high"] == 1
        assert stats["severity_distribution"]["critical"] == 1
        assert stats["resolution_rate"] == 0.25


class TestAgentMonitor:
    """测试智能体监控器"""
    
    def setup_method(self):
        """设置测试环境"""
        self.monitor = AgentMonitor(heartbeat_interval=1.0, timeout_threshold=3.0)
    
    def test_register_agent(self):
        """测试注册智能体"""
        self.monitor.register_agent("agent_1")
        
        assert "agent_1" in self.monitor.agent_status
        status_info = self.monitor.agent_status["agent_1"]
        assert status_info.agent_id == "agent_1"
        assert status_info.status == AgentStatus.IDLE
    
    def test_unregister_agent(self):
        """测试注销智能体"""
        self.monitor.register_agent("agent_1")
        self.monitor.unregister_agent("agent_1")
        
        assert "agent_1" not in self.monitor.agent_status
        assert "agent_1" not in self.monitor.status_history
    
    def test_update_agent_status(self):
        """测试更新智能体状态"""
        self.monitor.register_agent("agent_1")
        
        self.monitor.update_agent_status(
            "agent_1", 
            AgentStatus.PROCESSING, 
            "test_task", 
            0.5,
            {"test": "metadata"}
        )
        
        status_info = self.monitor.agent_status["agent_1"]
        assert status_info.status == AgentStatus.PROCESSING
        assert status_info.current_task == "test_task"
        assert status_info.progress == 0.5
        assert status_info.metadata == {"test": "metadata"}
        
        # 检查状态历史
        assert len(self.monitor.status_history["agent_1"]) == 1
        history_record = self.monitor.status_history["agent_1"][0]
        assert history_record["old_status"] == "idle"
        assert history_record["new_status"] == "processing"
        assert history_record["current_task"] == "test_task"
        assert history_record["progress"] == 0.5
    
    def test_heartbeat(self):
        """测试心跳"""
        self.monitor.register_agent("agent_1")
        
        old_heartbeat = self.monitor.agent_status["agent_1"].last_heartbeat
        time.sleep(0.1)  # 等待一小段时间
        
        self.monitor.heartbeat("agent_1")
        
        new_heartbeat = self.monitor.agent_status["agent_1"].last_heartbeat
        assert new_heartbeat > old_heartbeat
    
    def test_get_agent_status(self):
        """测试获取智能体状态"""
        self.monitor.register_agent("agent_1")
        
        status_info = self.monitor.get_agent_status("agent_1")
        assert status_info is not None
        assert status_info.agent_id == "agent_1"
        
        # 测试不存在的智能体
        status_info = self.monitor.get_agent_status("nonexistent_agent")
        assert status_info is None
    
    def test_get_all_agent_status(self):
        """测试获取所有智能体状态"""
        self.monitor.register_agent("agent_1")
        self.monitor.register_agent("agent_2")
        
        all_status = self.monitor.get_all_agent_status()
        
        assert len(all_status) == 2
        assert "agent_1" in all_status
        assert "agent_2" in all_status
    
    def test_check_timeouts(self):
        """测试检查超时"""
        self.monitor.register_agent("agent_1")
        self.monitor.register_agent("agent_2")
        
        # 模拟agent_1超时
        old_time = datetime.now() - timedelta(seconds=5)
        self.monitor.agent_status["agent_1"].last_heartbeat = old_time
        
        timeout_agents = self.monitor.check_timeouts()
        
        assert "agent_1" in timeout_agents
        assert "agent_2" not in timeout_agents
        assert self.monitor.agent_status["agent_1"].status == AgentStatus.OFFLINE
    
    def test_get_monitoring_statistics(self):
        """测试获取监控统计"""
        self.monitor.register_agent("agent_1")
        self.monitor.register_agent("agent_2")
        
        self.monitor.update_agent_status("agent_1", AgentStatus.PROCESSING)
        self.monitor.update_agent_status("agent_2", AgentStatus.COMPLETED)
        
        stats = self.monitor.get_monitoring_statistics()
        
        assert stats["total_agents"] == 2
        assert stats["status_distribution"]["processing"] == 1
        assert stats["status_distribution"]["completed"] == 1
        assert stats["heartbeat_interval"] == 1.0
        assert stats["timeout_threshold"] == 3.0
    
    def test_start_stop_monitoring(self):
        """测试启动和停止监控"""
        assert self.monitor.monitoring == False
        
        self.monitor.start_monitoring()
        assert self.monitor.monitoring == True
        
        self.monitor.stop_monitoring()
        assert self.monitor.monitoring == False


class TestIntegration:
    """集成测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.broker = MessageBroker()
        self.error_handler = ErrorHandler()
        self.monitor = AgentMonitor()
        
        # 模拟智能体处理器
        self.agent_handlers = {}
        
        def create_handler(agent_id):
            def handler(message):
                return {"agent_id": agent_id, "processed": True, "message_id": message.message_id}
            return handler
        
        # 注册多个智能体
        for i in range(3):
            agent_id = f"agent_{i}"
            handler = create_handler(agent_id)
            self.agent_handlers[agent_id] = handler
            
            self.broker.register_agent(agent_id, handler)
            self.monitor.register_agent(agent_id)
            self.broker.subscribe(agent_id, MessageType.DATA_REQUEST)
            self.broker.subscribe(agent_id, MessageType.STATUS_UPDATE)
    
    def test_end_to_end_communication(self):
        """测试端到端通信"""
        # 发送数据请求消息
        message = Message(
            message_id="integration_test_msg",
            sender_id="agent_0",
            receiver_id="agent_1",
            message_type=MessageType.DATA_REQUEST,
            payload={"data_type": "events", "filters": {}},
            timestamp=datetime.now()
        )
        
        # 发送消息
        success = self.broker.send_message(message)
        assert success == True
        
        # 获取消息
        messages = self.broker.get_messages("agent_1", max_count=1)
        assert len(messages) == 1
        assert messages[0].message_id == "integration_test_msg"
        
        # 更新智能体状态
        self.monitor.update_agent_status("agent_1", AgentStatus.PROCESSING, "data_request")
        
        # 检查状态
        status = self.monitor.get_agent_status("agent_1")
        assert status.status == AgentStatus.PROCESSING
        assert status.current_task == "data_request"
    
    def test_error_handling_with_retry(self):
        """测试错误处理和重试"""
        # 模拟错误
        error = ConnectionError("Connection failed")
        error_info = self.error_handler.handle_error("agent_1", error, {"retry_count": 0})
        
        # 检查是否应该重试
        should_retry = self.error_handler.should_retry(error_info)
        assert should_retry == True
        
        # 获取重试延迟
        delay = self.error_handler.get_retry_delay(0)
        assert delay > 0
        
        # 更新智能体状态为错误
        self.monitor.update_agent_status("agent_1", AgentStatus.ERROR, metadata={"error_id": error_info.error_id})
        
        # 检查状态
        status = self.monitor.get_agent_status("agent_1")
        assert status.status == AgentStatus.ERROR
        assert status.metadata["error_id"] == error_info.error_id
    
    def test_broadcast_with_monitoring(self):
        """测试广播消息和监控"""
        # 广播状态更新消息
        message = Message(
            message_id="broadcast_status",
            sender_id="orchestrator",
            receiver_id="all",
            message_type=MessageType.STATUS_UPDATE,
            payload={"command": "start_processing"},
            timestamp=datetime.now()
        )
        
        success_count = self.broker.broadcast_message(message, exclude_sender=False)
        assert success_count == 3  # 发送给所有3个智能体
        
        # 检查所有智能体都收到了消息
        for i in range(3):
            agent_id = f"agent_{i}"
            messages = self.broker.get_messages(agent_id, max_count=1)
            assert len(messages) == 1
            assert messages[0].payload["command"] == "start_processing"
            
            # 更新智能体状态
            self.monitor.update_agent_status(agent_id, AgentStatus.PROCESSING)
        
        # 检查所有智能体状态
        all_status = self.monitor.get_all_agent_status()
        for agent_id, status in all_status.items():
            assert status.status == AgentStatus.PROCESSING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])