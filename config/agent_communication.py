"""
智能体通信协议和错误处理模块

该模块实现智能体间的通信协议、错误处理和重试机制，包括：
- 智能体间消息传递和数据交换
- 错误处理和重试机制
- 智能体状态监控和日志记录
- 通信协议定义和管理
"""

import logging
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock, Event
import traceback
from collections import defaultdict, deque

from utils.logger import setup_logger

logger = setup_logger()


class MessageType(Enum):
    """消息类型枚举"""
    DATA_REQUEST = "data_request"
    DATA_RESPONSE = "data_response"
    STATUS_UPDATE = "status_update"
    ERROR_NOTIFICATION = "error_notification"
    TASK_COMPLETION = "task_completion"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"


class AgentStatus(Enum):
    """智能体状态枚举"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    OFFLINE = "offline"


class ErrorSeverity(Enum):
    """错误严重程度枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Message:
    """智能体间通信消息"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 优先级，数字越小优先级越高
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 30.0  # 超时时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout": self.timeout
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息对象"""
        return cls(
            message_id=data["message_id"],
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            message_type=MessageType(data["message_type"]),
            payload=data["payload"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=data.get("priority", 1),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout=data.get("timeout", 30.0)
        )


@dataclass
class ErrorInfo:
    """错误信息"""
    error_id: str
    agent_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: datetime
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class AgentStatusInfo:
    """智能体状态信息"""
    agent_id: str
    status: AgentStatus
    last_heartbeat: datetime
    current_task: Optional[str] = None
    progress: float = 0.0  # 任务进度 (0.0-1.0)
    metadata: Optional[Dict[str, Any]] = None


class RetryPolicy:
    """重试策略"""
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True):
        """
        初始化重试策略
        
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            backoff_factor: 退避因子
            jitter: 是否添加随机抖动
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_delay(self, retry_count: int) -> float:
        """
        计算重试延迟时间
        
        Args:
            retry_count: 当前重试次数
            
        Returns:
            延迟时间（秒）
        """
        delay = min(self.base_delay * (self.backoff_factor ** retry_count), self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 添加50%的随机抖动
        
        return delay
    
    def should_retry(self, retry_count: int, error: Exception) -> bool:
        """
        判断是否应该重试
        
        Args:
            retry_count: 当前重试次数
            error: 错误对象
            
        Returns:
            是否应该重试
        """
        if retry_count >= self.max_retries:
            return False
        
        # 某些错误类型不应该重试
        non_retryable_errors = (ValueError, TypeError, KeyError)
        if isinstance(error, non_retryable_errors):
            return False
        
        return True


class MessageBroker:
    """消息代理，负责智能体间的消息传递"""
    
    def __init__(self):
        """初始化消息代理"""
        self.message_queues = defaultdict(deque)  # 每个智能体的消息队列
        self.subscribers = defaultdict(list)  # 消息类型订阅者
        self.message_handlers = {}  # 消息处理器
        self.pending_responses = {}  # 等待响应的消息
        self.message_history = deque(maxlen=1000)  # 消息历史
        self.lock = Lock()
        self.running = False
        
        logger.info("消息代理初始化完成")
    
    def register_agent(self, agent_id: str, message_handler: Callable[[Message], Any]):
        """
        注册智能体
        
        Args:
            agent_id: 智能体ID
            message_handler: 消息处理函数
        """
        with self.lock:
            self.message_handlers[agent_id] = message_handler
            logger.info(f"智能体已注册: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """
        注销智能体
        
        Args:
            agent_id: 智能体ID
        """
        with self.lock:
            if agent_id in self.message_handlers:
                del self.message_handlers[agent_id]
            if agent_id in self.message_queues:
                del self.message_queues[agent_id]
            logger.info(f"智能体已注销: {agent_id}")
    
    def subscribe(self, agent_id: str, message_type: MessageType):
        """
        订阅消息类型
        
        Args:
            agent_id: 智能体ID
            message_type: 消息类型
        """
        with self.lock:
            if agent_id not in self.subscribers[message_type]:
                self.subscribers[message_type].append(agent_id)
                logger.debug(f"智能体 {agent_id} 订阅了消息类型 {message_type.value}")
    
    def unsubscribe(self, agent_id: str, message_type: MessageType):
        """
        取消订阅消息类型
        
        Args:
            agent_id: 智能体ID
            message_type: 消息类型
        """
        with self.lock:
            if agent_id in self.subscribers[message_type]:
                self.subscribers[message_type].remove(agent_id)
                logger.debug(f"智能体 {agent_id} 取消订阅消息类型 {message_type.value}")
    
    def send_message(self, message: Message) -> bool:
        """
        发送消息
        
        Args:
            message: 消息对象
            
        Returns:
            是否发送成功
        """
        try:
            with self.lock:
                # 检查接收者是否存在
                if message.receiver_id not in self.message_handlers:
                    logger.warning(f"接收者不存在: {message.receiver_id}")
                    return False
                
                # 添加到接收者的消息队列
                self.message_queues[message.receiver_id].append(message)
                
                # 记录消息历史
                self.message_history.append(message)
                
                logger.debug(f"消息已发送: {message.message_id} from {message.sender_id} to {message.receiver_id}")
                return True
                
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    def broadcast_message(self, message: Message, exclude_sender: bool = True) -> int:
        """
        广播消息
        
        Args:
            message: 消息对象
            exclude_sender: 是否排除发送者
            
        Returns:
            成功发送的消息数量
        """
        success_count = 0
        
        with self.lock:
            # 获取订阅者列表
            subscribers = self.subscribers.get(message.message_type, [])
            
            for agent_id in subscribers:
                if exclude_sender and agent_id == message.sender_id:
                    continue
                
                # 创建副本消息
                broadcast_message = Message(
                    message_id=f"{message.message_id}_{agent_id}",
                    sender_id=message.sender_id,
                    receiver_id=agent_id,
                    message_type=message.message_type,
                    payload=message.payload.copy(),
                    timestamp=message.timestamp,
                    priority=message.priority,
                    retry_count=message.retry_count,
                    max_retries=message.max_retries,
                    timeout=message.timeout
                )
                
                if self.send_message(broadcast_message):
                    success_count += 1
        
        logger.info(f"广播消息完成: {message.message_id}, 成功发送 {success_count} 条")
        return success_count
    
    def get_messages(self, agent_id: str, max_count: int = 10) -> List[Message]:
        """
        获取智能体的消息
        
        Args:
            agent_id: 智能体ID
            max_count: 最大消息数量
            
        Returns:
            消息列表
        """
        messages = []
        
        with self.lock:
            queue = self.message_queues[agent_id]
            
            for _ in range(min(max_count, len(queue))):
                if queue:
                    messages.append(queue.popleft())
        
        return messages
    
    def get_queue_size(self, agent_id: str) -> int:
        """
        获取智能体消息队列大小
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            队列大小
        """
        with self.lock:
            return len(self.message_queues[agent_id])
    
    def clear_queue(self, agent_id: str):
        """
        清空智能体消息队列
        
        Args:
            agent_id: 智能体ID
        """
        with self.lock:
            self.message_queues[agent_id].clear()
            logger.info(f"已清空智能体 {agent_id} 的消息队列")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取消息代理统计信息
        
        Returns:
            统计信息字典
        """
        with self.lock:
            return {
                "registered_agents": len(self.message_handlers),
                "total_queues": len(self.message_queues),
                "queue_sizes": {
                    agent_id: len(queue) 
                    for agent_id, queue in self.message_queues.items()
                },
                "subscribers": {
                    msg_type.value: len(agents) 
                    for msg_type, agents in self.subscribers.items()
                },
                "message_history_size": len(self.message_history)
            }


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, retry_policy: RetryPolicy = None):
        """
        初始化错误处理器
        
        Args:
            retry_policy: 重试策略
        """
        self.retry_policy = retry_policy or RetryPolicy()
        self.error_history = deque(maxlen=1000)
        self.error_handlers = {}  # 错误类型处理器
        self.lock = Lock()
        
        logger.info("错误处理器初始化完成")
    
    def register_error_handler(self, error_type: str, handler: Callable[[ErrorInfo], bool]):
        """
        注册错误处理器
        
        Args:
            error_type: 错误类型
            handler: 错误处理函数，返回True表示错误已解决
        """
        self.error_handlers[error_type] = handler
        logger.info(f"已注册错误处理器: {error_type}")
    
    def handle_error(self, agent_id: str, error: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """
        处理错误
        
        Args:
            agent_id: 智能体ID
            error: 错误对象
            context: 错误上下文
            
        Returns:
            错误信息对象
        """
        error_info = ErrorInfo(
            error_id=f"err_{int(time.time() * 1000)}",
            agent_id=agent_id,
            error_type=type(error).__name__,
            error_message=str(error),
            severity=self._determine_severity(error),
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc(),
            context=context or {}
        )
        
        with self.lock:
            self.error_history.append(error_info)
        
        # 尝试使用注册的错误处理器
        if error_info.error_type in self.error_handlers:
            try:
                resolved = self.error_handlers[error_info.error_type](error_info)
                if resolved:
                    error_info.resolved = True
                    error_info.resolution_notes = f"由处理器 {error_info.error_type} 解决"
                    logger.info(f"错误已解决: {error_info.error_id}")
            except Exception as handler_error:
                logger.error(f"错误处理器执行失败: {handler_error}")
        
        logger.error(f"处理错误: {error_info.error_id} - {error_info.error_message}")
        return error_info
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """
        确定错误严重程度
        
        Args:
            error: 错误对象
            
        Returns:
            错误严重程度
        """
        # 根据错误类型确定严重程度
        critical_errors = (SystemError, MemoryError, KeyboardInterrupt)
        high_errors = (ConnectionError, TimeoutError, OSError)
        medium_errors = (ValueError, TypeError, AttributeError)
        
        if isinstance(error, critical_errors):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, high_errors):
            return ErrorSeverity.HIGH
        elif isinstance(error, medium_errors):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def should_retry(self, error_info: ErrorInfo) -> bool:
        """
        判断是否应该重试
        
        Args:
            error_info: 错误信息
            
        Returns:
            是否应该重试
        """
        # 如果错误已解决，不需要重试
        if error_info.resolved:
            return False
        
        # 使用重试策略判断
        return self.retry_policy.should_retry(
            error_info.context.get("retry_count", 0),
            Exception(error_info.error_message)
        )
    
    def get_retry_delay(self, retry_count: int) -> float:
        """
        获取重试延迟时间
        
        Args:
            retry_count: 重试次数
            
        Returns:
            延迟时间（秒）
        """
        return self.retry_policy.get_delay(retry_count)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Returns:
            错误统计信息
        """
        with self.lock:
            error_counts = defaultdict(int)
            severity_counts = defaultdict(int)
            resolved_count = 0
            
            for error_info in self.error_history:
                error_counts[error_info.error_type] += 1
                severity_counts[error_info.severity.value] += 1
                if error_info.resolved:
                    resolved_count += 1
            
            return {
                "total_errors": len(self.error_history),
                "resolved_errors": resolved_count,
                "error_types": dict(error_counts),
                "severity_distribution": dict(severity_counts),
                "resolution_rate": resolved_count / len(self.error_history) if self.error_history else 0
            }


class AgentMonitor:
    """智能体状态监控器"""
    
    def __init__(self, heartbeat_interval: float = 30.0, timeout_threshold: float = 120.0):
        """
        初始化监控器
        
        Args:
            heartbeat_interval: 心跳间隔（秒）
            timeout_threshold: 超时阈值（秒）
        """
        self.heartbeat_interval = heartbeat_interval
        self.timeout_threshold = timeout_threshold
        self.agent_status = {}  # 智能体状态信息
        self.status_history = defaultdict(deque)  # 状态历史
        self.lock = Lock()
        self.monitoring = False
        self.monitor_thread = None
        
        logger.info("智能体监控器初始化完成")
    
    def register_agent(self, agent_id: str):
        """
        注册智能体
        
        Args:
            agent_id: 智能体ID
        """
        with self.lock:
            self.agent_status[agent_id] = AgentStatusInfo(
                agent_id=agent_id,
                status=AgentStatus.IDLE,
                last_heartbeat=datetime.now()
            )
            logger.info(f"智能体已注册到监控器: {agent_id}")
    
    def unregister_agent(self, agent_id: str):
        """
        注销智能体
        
        Args:
            agent_id: 智能体ID
        """
        with self.lock:
            if agent_id in self.agent_status:
                del self.agent_status[agent_id]
            if agent_id in self.status_history:
                del self.status_history[agent_id]
            logger.info(f"智能体已从监控器注销: {agent_id}")
    
    def update_agent_status(self, agent_id: str, status: AgentStatus, 
                          current_task: str = None, progress: float = None,
                          metadata: Dict[str, Any] = None):
        """
        更新智能体状态
        
        Args:
            agent_id: 智能体ID
            status: 新状态
            current_task: 当前任务
            progress: 任务进度
            metadata: 元数据
        """
        with self.lock:
            if agent_id not in self.agent_status:
                self.register_agent(agent_id)
            
            old_status = self.agent_status[agent_id].status
            
            # 更新状态信息
            self.agent_status[agent_id].status = status
            self.agent_status[agent_id].last_heartbeat = datetime.now()
            
            if current_task is not None:
                self.agent_status[agent_id].current_task = current_task
            
            if progress is not None:
                self.agent_status[agent_id].progress = max(0.0, min(1.0, progress))
            
            if metadata is not None:
                self.agent_status[agent_id].metadata = metadata
            
            # 记录状态历史
            status_record = {
                "timestamp": datetime.now().isoformat(),
                "old_status": old_status.value if old_status else None,
                "new_status": status.value,
                "current_task": current_task,
                "progress": progress
            }
            
            self.status_history[agent_id].append(status_record)
            
            # 限制历史记录数量
            if len(self.status_history[agent_id]) > 100:
                self.status_history[agent_id].popleft()
            
            logger.debug(f"智能体状态更新: {agent_id} {old_status} -> {status}")
    
    def heartbeat(self, agent_id: str):
        """
        接收智能体心跳
        
        Args:
            agent_id: 智能体ID
        """
        with self.lock:
            if agent_id in self.agent_status:
                self.agent_status[agent_id].last_heartbeat = datetime.now()
                logger.debug(f"收到心跳: {agent_id}")
    
    def get_agent_status(self, agent_id: str) -> Optional[AgentStatusInfo]:
        """
        获取智能体状态
        
        Args:
            agent_id: 智能体ID
            
        Returns:
            智能体状态信息
        """
        with self.lock:
            return self.agent_status.get(agent_id)
    
    def get_all_agent_status(self) -> Dict[str, AgentStatusInfo]:
        """
        获取所有智能体状态
        
        Returns:
            所有智能体状态信息
        """
        with self.lock:
            return self.agent_status.copy()
    
    def check_timeouts(self) -> List[str]:
        """
        检查超时的智能体
        
        Returns:
            超时的智能体ID列表
        """
        timeout_agents = []
        current_time = datetime.now()
        
        with self.lock:
            for agent_id, status_info in self.agent_status.items():
                time_since_heartbeat = (current_time - status_info.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > self.timeout_threshold:
                    timeout_agents.append(agent_id)
                    # 更新状态为离线
                    if status_info.status != AgentStatus.OFFLINE:
                        self.update_agent_status(agent_id, AgentStatus.OFFLINE)
        
        if timeout_agents:
            logger.warning(f"检测到超时智能体: {timeout_agents}")
        
        return timeout_agents
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """
        获取监控统计信息
        
        Returns:
            监控统计信息
        """
        with self.lock:
            status_counts = defaultdict(int)
            total_agents = len(self.agent_status)
            
            for status_info in self.agent_status.values():
                status_counts[status_info.status.value] += 1
            
            return {
                "total_agents": total_agents,
                "status_distribution": dict(status_counts),
                "monitoring_active": self.monitoring,
                "heartbeat_interval": self.heartbeat_interval,
                "timeout_threshold": self.timeout_threshold
            }
    
    def start_monitoring(self):
        """启动监控"""
        if not self.monitoring:
            self.monitoring = True
            logger.info("智能体监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        if self.monitoring:
            self.monitoring = False
            logger.info("智能体监控已停止")