"""
智能体通信和错误处理集成测试

测试通信协议和错误处理的核心功能，不依赖完整的智能体系统
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock

from config.agent_communication import (
    MessageBroker, ErrorHandler, AgentMonitor, Message, MessageType,
    AgentStatus, ErrorInfo, ErrorSeverity, RetryPolicy
)


def test_message_broker_basic_functionality():
    """测试消息代理基本功能"""
    broker = MessageBroker()
    mock_handler = Mock()
    
    # 注册智能体
    broker.register_agent("agent_1", mock_handler)
    broker.register_agent("agent_2", mock_handler)
    
    # 订阅消息类型
    broker.subscribe("agent_1", MessageType.DATA_REQUEST)
    broker.subscribe("agent_2", MessageType.DATA_REQUEST)
    
    # 发送消息
    message = Message(
        message_id="test_msg_001",
        sender_id="agent_1",
        receiver_id="agent_2",
        message_type=MessageType.DATA_REQUEST,
        payload={"data_type": "events"},
        timestamp=datetime.now()
    )
    
    success = broker.send_message(message)
    assert success == True
    
    # 获取消息
    messages = broker.get_messages("agent_2", max_count=1)
    assert len(messages) == 1
    assert messages[0].message_id == "test_msg_001"
    
    # 广播消息
    broadcast_message = Message(
        message_id="broadcast_001",
        sender_id="orchestrator",
        receiver_id="all",
        message_type=MessageType.DATA_REQUEST,
        payload={"command": "shutdown"},
        timestamp=datetime.now()
    )
    
    success_count = broker.broadcast_message(broadcast_message)
    assert success_count == 2  # 发送给两个智能体
    
    print("✓ 消息代理基本功能测试通过")


def test_error_handler_functionality():
    """测试错误处理器功能"""
    error_handler = ErrorHandler()
    
    # 注册自定义错误处理器
    def custom_handler(error_info):
        if "recoverable" in error_info.error_message:
            error_info.resolved = True
            return True
        return False
    
    error_handler.register_error_handler("ValueError", custom_handler)
    
    # 测试可恢复错误
    recoverable_error = ValueError("This is a recoverable error")
    error_info = error_handler.handle_error("agent_1", recoverable_error)
    
    assert error_info.resolved == True
    assert error_info.error_type == "ValueError"
    
    # 测试不可恢复错误
    non_recoverable_error = ValueError("This is not recoverable")
    error_info = error_handler.handle_error("agent_1", non_recoverable_error)
    
    assert error_info.resolved == False
    
    # 测试重试策略
    retry_policy = RetryPolicy(max_retries=3, base_delay=0.1)
    assert retry_policy.should_retry(0, ConnectionError("test")) == True
    assert retry_policy.should_retry(3, ConnectionError("test")) == False
    assert retry_policy.should_retry(0, ValueError("test")) == False  # 不可重试的错误
    
    print("✓ 错误处理器功能测试通过")


def test_agent_monitor_functionality():
    """测试智能体监控器功能"""
    monitor = AgentMonitor(heartbeat_interval=1.0, timeout_threshold=2.0)
    
    # 注册智能体
    monitor.register_agent("agent_1")
    monitor.register_agent("agent_2")
    
    # 更新状态
    monitor.update_agent_status("agent_1", AgentStatus.PROCESSING, "test_task", 0.5)
    
    # 检查状态
    status = monitor.get_agent_status("agent_1")
    assert status.status == AgentStatus.PROCESSING
    assert status.current_task == "test_task"
    assert status.progress == 0.5
    
    # 心跳测试
    old_heartbeat = status.last_heartbeat
    time.sleep(0.1)
    monitor.heartbeat("agent_1")
    
    new_status = monitor.get_agent_status("agent_1")
    assert new_status.last_heartbeat > old_heartbeat
    
    # 获取所有状态
    all_status = monitor.get_all_agent_status()
    assert len(all_status) == 2
    assert "agent_1" in all_status
    assert "agent_2" in all_status
    
    print("✓ 智能体监控器功能测试通过")


def test_retry_policy_delays():
    """测试重试策略延迟计算"""
    policy = RetryPolicy(base_delay=1.0, backoff_factor=2.0, max_delay=10.0, jitter=False)
    
    # 测试延迟递增
    delay_0 = policy.get_delay(0)
    delay_1 = policy.get_delay(1)
    delay_2 = policy.get_delay(2)
    delay_3 = policy.get_delay(3)
    
    assert delay_0 == 1.0
    assert delay_1 == 2.0
    assert delay_2 == 4.0
    assert delay_3 == 8.0
    
    # 测试最大延迟限制
    delay_10 = policy.get_delay(10)  # 应该被限制为max_delay
    assert delay_10 == 10.0
    
    print("✓ 重试策略延迟计算测试通过")


def test_message_serialization():
    """测试消息序列化和反序列化"""
    timestamp = datetime.now()
    original_message = Message(
        message_id="serialize_test",
        sender_id="agent_1",
        receiver_id="agent_2",
        message_type=MessageType.STATUS_UPDATE,
        payload={"status": "processing", "progress": 0.75},
        timestamp=timestamp,
        priority=2,
        retry_count=1,
        max_retries=5,
        timeout=60.0
    )
    
    # 转换为字典
    message_dict = original_message.to_dict()
    
    # 从字典重建消息
    reconstructed_message = Message.from_dict(message_dict)
    
    # 验证所有字段
    assert reconstructed_message.message_id == original_message.message_id
    assert reconstructed_message.sender_id == original_message.sender_id
    assert reconstructed_message.receiver_id == original_message.receiver_id
    assert reconstructed_message.message_type == original_message.message_type
    assert reconstructed_message.payload == original_message.payload
    assert reconstructed_message.timestamp == original_message.timestamp
    assert reconstructed_message.priority == original_message.priority
    assert reconstructed_message.retry_count == original_message.retry_count
    assert reconstructed_message.max_retries == original_message.max_retries
    assert reconstructed_message.timeout == original_message.timeout
    
    print("✓ 消息序列化测试通过")


def test_error_severity_classification():
    """测试错误严重程度分类"""
    error_handler = ErrorHandler()
    
    # 测试不同类型的错误
    test_cases = [
        (SystemError("System error"), ErrorSeverity.CRITICAL),
        (MemoryError("Memory error"), ErrorSeverity.CRITICAL),
        (ConnectionError("Connection error"), ErrorSeverity.HIGH),
        (TimeoutError("Timeout error"), ErrorSeverity.HIGH),
        (ValueError("Value error"), ErrorSeverity.MEDIUM),
        (TypeError("Type error"), ErrorSeverity.MEDIUM),
        (RuntimeError("Runtime error"), ErrorSeverity.LOW),
    ]
    
    for error, expected_severity in test_cases:
        error_info = error_handler.handle_error("test_agent", error)
        assert error_info.severity == expected_severity, f"错误 {type(error).__name__} 的严重程度应该是 {expected_severity.value}"
    
    print("✓ 错误严重程度分类测试通过")


def test_integration_scenario():
    """测试完整的集成场景"""
    # 初始化组件
    broker = MessageBroker()
    error_handler = ErrorHandler()
    monitor = AgentMonitor()
    
    # 模拟智能体处理器
    def agent_handler(message):
        # 模拟处理消息
        if message.payload.get("simulate_error"):
            raise ConnectionError("Simulated connection error")
        return {"status": "processed", "message_id": message.message_id}
    
    # 注册智能体
    broker.register_agent("data_processor", agent_handler)
    broker.register_agent("event_analyst", agent_handler)
    monitor.register_agent("data_processor")
    monitor.register_agent("event_analyst")
    
    # 订阅消息类型
    broker.subscribe("data_processor", MessageType.DATA_REQUEST)
    broker.subscribe("event_analyst", MessageType.DATA_REQUEST)
    
    # 场景1：正常消息处理
    normal_message = Message(
        message_id="normal_001",
        sender_id="orchestrator",
        receiver_id="data_processor",
        message_type=MessageType.DATA_REQUEST,
        payload={"data_type": "events"},
        timestamp=datetime.now()
    )
    
    success = broker.send_message(normal_message)
    assert success == True
    
    # 更新智能体状态
    monitor.update_agent_status("data_processor", AgentStatus.PROCESSING, "data_request")
    
    # 场景2：错误处理
    error = ConnectionError("Network connection failed")
    error_info = error_handler.handle_error("data_processor", error, {"task": "data_processing"})
    
    assert error_info.error_type == "ConnectionError"
    assert error_info.severity == ErrorSeverity.HIGH
    
    # 更新智能体状态为错误
    monitor.update_agent_status("data_processor", AgentStatus.ERROR, metadata={"error_id": error_info.error_id})
    
    # 场景3：广播关闭消息
    shutdown_message = Message(
        message_id="shutdown_001",
        sender_id="orchestrator",
        receiver_id="all",
        message_type=MessageType.SHUTDOWN,
        payload={"reason": "maintenance"},
        timestamp=datetime.now()
    )
    
    # 先让智能体订阅关闭消息
    broker.subscribe("data_processor", MessageType.SHUTDOWN)
    broker.subscribe("event_analyst", MessageType.SHUTDOWN)
    
    success_count = broker.broadcast_message(shutdown_message)
    assert success_count == 2
    
    # 获取统计信息
    broker_stats = broker.get_statistics()
    error_stats = error_handler.get_error_statistics()
    monitor_stats = monitor.get_monitoring_statistics()
    
    assert broker_stats["registered_agents"] == 2
    assert error_stats["total_errors"] == 1
    assert monitor_stats["total_agents"] == 2
    
    print("✓ 集成场景测试通过")


def main():
    """运行所有测试"""
    print("开始智能体通信和错误处理集成测试...")
    print("=" * 60)
    
    try:
        test_message_broker_basic_functionality()
        test_error_handler_functionality()
        test_agent_monitor_functionality()
        test_retry_policy_delays()
        test_message_serialization()
        test_error_severity_classification()
        test_integration_scenario()
        
        print("=" * 60)
        print("✅ 所有测试通过！智能体通信和错误处理功能正常工作。")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)