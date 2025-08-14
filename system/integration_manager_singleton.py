"""
集成管理器单例模式实现
解决页面切换时重复初始化导致的性能问题
"""

import threading
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from system.integration_manager import IntegrationManager, WorkflowConfig
from utils.logger import setup_logger

# 全局logger
logger = setup_logger()

# 全局单例实例和锁
_integration_manager_instance: Optional[IntegrationManager] = None
_integration_manager_lock = threading.Lock()
_initialization_started = False
_initialization_in_progress = False

class IntegrationManagerSingleton:
    """IntegrationManager全局单例管理器"""
    
    @classmethod
    def get_instance(cls, config: Optional[WorkflowConfig] = None) -> IntegrationManager:
        """
        获取IntegrationManager单例实例
        
        Args:
            config: 配置对象，仅在首次初始化时使用
            
        Returns:
            IntegrationManager实例
        """
        global _integration_manager_instance, _initialization_started, _initialization_in_progress
        
        # 快速路径：如果实例已存在，直接返回
        if _integration_manager_instance is not None:
            return _integration_manager_instance
        
        # 双重检查锁定模式
        with _integration_manager_lock:
            # 再次检查，防止并发初始化
            if _integration_manager_instance is not None:
                return _integration_manager_instance
            
            # 检查是否有其他线程正在初始化
            if _initialization_in_progress:
                logger.info("其他线程正在初始化IntegrationManager，等待完成...")
                # 等待初始化完成
                while _initialization_in_progress:
                    threading.Event().wait(0.1)  # 100ms 检查间隔
                
                if _integration_manager_instance is not None:
                    return _integration_manager_instance
            
            # 标记开始初始化
            _initialization_started = True
            _initialization_in_progress = True
            
            try:
                logger.info("开始初始化IntegrationManager全局单例...")
                start_time = datetime.now()
                
                # 创建实例
                _integration_manager_instance = IntegrationManager(config)
                
                end_time = datetime.now()
                initialization_time = (end_time - start_time).total_seconds()
                logger.info(f"IntegrationManager单例初始化完成，耗时: {initialization_time:.2f}秒")
                
                return _integration_manager_instance
                
            except Exception as e:
                logger.error(f"IntegrationManager单例初始化失败: {e}")
                # 重置状态，允许重试
                _initialization_started = False
                _integration_manager_instance = None
                raise
            finally:
                _initialization_in_progress = False
    
    @classmethod
    def is_initialized(cls) -> bool:
        """
        检查IntegrationManager是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return _integration_manager_instance is not None
    
    @classmethod
    def reset_instance(cls):
        """
        重置单例实例（主要用于测试）
        """
        global _integration_manager_instance, _initialization_started, _initialization_in_progress
        
        with _integration_manager_lock:
            if _integration_manager_instance is not None:
                try:
                    logger.info("正在关闭IntegrationManager单例...")
                    _integration_manager_instance.shutdown()
                except Exception as e:
                    logger.warning(f"关闭IntegrationManager时出错: {e}")
                
                _integration_manager_instance = None
                _initialization_started = False
                _initialization_in_progress = False
                logger.info("IntegrationManager单例已重置")
    
    @classmethod
    def get_initialization_status(cls) -> Dict[str, Any]:
        """
        获取初始化状态信息
        
        Returns:
            Dict: 初始化状态信息
        """
        return {
            'initialized': _integration_manager_instance is not None,
            'initialization_started': _initialization_started,
            'initialization_in_progress': _initialization_in_progress,
            'instance_id': id(_integration_manager_instance) if _integration_manager_instance else None
        }


class LazyIntegrationManager:
    """延迟加载的IntegrationManager包装器"""
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        初始化延迟加载管理器
        
        Args:
            config: 配置对象
        """
        self._config = config
        self._instance: Optional[IntegrationManager] = None
        self._lazy_initialized = False
        self.logger = setup_logger()
    
    def _ensure_initialized(self) -> IntegrationManager:
        """确保实例已初始化"""
        if not self._lazy_initialized:
            self.logger.info("延迟初始化IntegrationManager...")
            self._instance = IntegrationManagerSingleton.get_instance(self._config)
            self._lazy_initialized = True
        
        return self._instance
    
    def __getattr__(self, name):
        """代理所有属性和方法调用到实际的IntegrationManager实例"""
        instance = self._ensure_initialized()
        return getattr(instance, name)
    
    @property 
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._lazy_initialized and self._instance is not None


def get_integration_manager(config: Optional[WorkflowConfig] = None, 
                          lazy_loading: bool = True) -> IntegrationManager:
    """
    获取IntegrationManager实例的便捷函数
    
    Args:
        config: 配置对象
        lazy_loading: 是否使用延迟加载
        
    Returns:
        IntegrationManager实例或LazyIntegrationManager实例
    """
    if lazy_loading:
        # 返回延迟加载包装器
        return LazyIntegrationManager(config)
    else:
        # 返回真实的单例实例  
        return IntegrationManagerSingleton.get_instance(config)


def reset_integration_manager():
    """重置IntegrationManager单例（主要用于测试）"""
    IntegrationManagerSingleton.reset_instance()


def get_integration_manager_status() -> Dict[str, Any]:
    """获取IntegrationManager状态信息"""
    return IntegrationManagerSingleton.get_initialization_status()