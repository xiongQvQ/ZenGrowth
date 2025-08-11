"""
数据存储管理器模块

提供内存数据存储、检索和查询功能，支持事件、用户、会话数据的管理。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading
import copy

logger = logging.getLogger(__name__)


@dataclass
class StorageStats:
    """存储统计信息"""
    total_events: int
    total_users: int
    total_sessions: int
    memory_usage_mb: float
    last_updated: datetime


class DataStorageManager:
    """数据存储管理器类"""
    
    def __init__(self):
        """初始化存储管理器"""
        self._events_data = pd.DataFrame()
        self._users_data = pd.DataFrame()
        self._sessions_data = pd.DataFrame()
        self._events_by_type = {}
        self._lock = threading.RLock()
        self._last_updated = datetime.now()
        
        # 索引配置
        self._event_indexes = ['user_pseudo_id', 'event_name', 'event_date']
        self._user_indexes = ['user_pseudo_id', 'platform', 'device_category']
        self._session_indexes = ['user_pseudo_id', 'session_id']
        
        logger.info("数据存储管理器初始化完成")
        
    def store_events(self, events: pd.DataFrame) -> None:
        """
        存储事件数据
        
        Args:
            events: 事件数据DataFrame
        """
        try:
            with self._lock:
                if events.empty:
                    logger.warning("尝试存储空的事件数据")
                    return
                    
                # 验证必需列
                required_columns = ['user_pseudo_id', 'event_name', 'event_timestamp']
                missing_columns = set(required_columns) - set(events.columns)
                if missing_columns:
                    raise ValueError(f"事件数据缺少必需列: {missing_columns}")
                
                # 存储主事件数据
                self._events_data = events.copy()
                
                # 按事件类型分组存储
                self._events_by_type = {}
                for event_type in events['event_name'].unique():
                    self._events_by_type[event_type] = events[
                        events['event_name'] == event_type
                    ].copy()
                
                # 创建索引
                self._create_event_indexes()
                
                self._last_updated = datetime.now()
                logger.info(f"成功存储{len(events)}条事件数据，包含{len(self._events_by_type)}种事件类型")
                
        except Exception as e:
            logger.error(f"存储事件数据失败: {e}")
            raise
            
    def store_users(self, users: pd.DataFrame) -> None:
        """
        存储用户数据
        
        Args:
            users: 用户数据DataFrame
        """
        try:
            with self._lock:
                if users.empty:
                    logger.warning("尝试存储空的用户数据")
                    return
                    
                # 验证必需列
                required_columns = ['user_pseudo_id']
                missing_columns = set(required_columns) - set(users.columns)
                if missing_columns:
                    raise ValueError(f"用户数据缺少必需列: {missing_columns}")
                
                self._users_data = users.copy()
                
                # 创建索引
                self._create_user_indexes()
                
                self._last_updated = datetime.now()
                logger.info(f"成功存储{len(users)}个用户数据")
                
        except Exception as e:
            logger.error(f"存储用户数据失败: {e}")
            raise
            
    def store_sessions(self, sessions: pd.DataFrame) -> None:
        """
        存储会话数据
        
        Args:
            sessions: 会话数据DataFrame
        """
        try:
            with self._lock:
                if sessions.empty:
                    logger.warning("尝试存储空的会话数据")
                    return
                    
                # 验证必需列
                required_columns = ['session_id', 'user_pseudo_id']
                missing_columns = set(required_columns) - set(sessions.columns)
                if missing_columns:
                    raise ValueError(f"会话数据缺少必需列: {missing_columns}")
                
                self._sessions_data = sessions.copy()
                
                # 创建索引
                self._create_session_indexes()
                
                self._last_updated = datetime.now()
                logger.info(f"成功存储{len(sessions)}个会话数据")
                
        except Exception as e:
            logger.error(f"存储会话数据失败: {e}")
            raise
            
    def get_data(self, data_type: str, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        获取数据
        
        Args:
            data_type: 数据类型 ('events', 'users', 'sessions', 'event_type:event_name')
            filters: 过滤条件字典
            
        Returns:
            过滤后的数据DataFrame
        """
        try:
            with self._lock:
                # 获取基础数据
                if data_type == 'events':
                    data = self._events_data.copy()
                elif data_type == 'users':
                    data = self._users_data.copy()
                elif data_type == 'sessions':
                    data = self._sessions_data.copy()
                elif data_type.startswith('event_type:'):
                    event_type = data_type.split(':', 1)[1]
                    data = self._events_by_type.get(event_type, pd.DataFrame())
                else:
                    raise ValueError(f"不支持的数据类型: {data_type}")
                
                if data.empty:
                    logger.warning(f"请求的数据类型 {data_type} 为空")
                    return pd.DataFrame()
                
                # 应用过滤条件
                if filters:
                    data = self._apply_filters(data, filters)
                
                logger.debug(f"获取{data_type}数据: {len(data)}条记录")
                return data
                
        except Exception as e:
            logger.error(f"获取数据失败: {e}")
            raise
            
    def _apply_filters(self, data: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        应用过滤条件
        
        Args:
            data: 原始数据
            filters: 过滤条件
            
        Returns:
            过滤后的数据
        """
        filtered_data = data.copy()
        
        for column, condition in filters.items():
            if column not in filtered_data.columns:
                logger.warning(f"过滤列 {column} 不存在，跳过")
                continue
                
            try:
                if isinstance(condition, dict):
                    # 复杂条件
                    filtered_data = self._apply_complex_filter(filtered_data, column, condition)
                elif isinstance(condition, (list, tuple)):
                    # IN 条件
                    filtered_data = filtered_data[filtered_data[column].isin(condition)]
                else:
                    # 等值条件
                    filtered_data = filtered_data[filtered_data[column] == condition]
                    
            except Exception as e:
                logger.warning(f"应用过滤条件 {column}={condition} 失败: {e}")
                continue
                
        return filtered_data
        
    def _apply_complex_filter(self, data: pd.DataFrame, column: str, condition: Dict[str, Any]) -> pd.DataFrame:
        """
        应用复杂过滤条件
        
        Args:
            data: 数据
            column: 列名
            condition: 复杂条件字典
            
        Returns:
            过滤后的数据
        """
        filtered_data = data.copy()
        
        for operator, value in condition.items():
            if operator == 'eq':
                filtered_data = filtered_data[filtered_data[column] == value]
            elif operator == 'ne':
                filtered_data = filtered_data[filtered_data[column] != value]
            elif operator == 'gt':
                filtered_data = filtered_data[filtered_data[column] > value]
            elif operator == 'gte':
                filtered_data = filtered_data[filtered_data[column] >= value]
            elif operator == 'lt':
                filtered_data = filtered_data[filtered_data[column] < value]
            elif operator == 'lte':
                filtered_data = filtered_data[filtered_data[column] <= value]
            elif operator == 'in':
                filtered_data = filtered_data[filtered_data[column].isin(value)]
            elif operator == 'not_in':
                filtered_data = filtered_data[~filtered_data[column].isin(value)]
            elif operator == 'contains':
                if filtered_data[column].dtype == 'object':
                    filtered_data = filtered_data[filtered_data[column].str.contains(str(value), na=False)]
            elif operator == 'startswith':
                if filtered_data[column].dtype == 'object':
                    filtered_data = filtered_data[filtered_data[column].str.startswith(str(value), na=False)]
            elif operator == 'endswith':
                if filtered_data[column].dtype == 'object':
                    filtered_data = filtered_data[filtered_data[column].str.endswith(str(value), na=False)]
            else:
                logger.warning(f"不支持的操作符: {operator}")
                
        return filtered_data
        
    def query_events(self, 
                    user_ids: Optional[List[str]] = None,
                    event_types: Optional[List[str]] = None,
                    date_range: Optional[Tuple[str, str]] = None,
                    limit: Optional[int] = None) -> pd.DataFrame:
        """
        查询事件数据
        
        Args:
            user_ids: 用户ID列表
            event_types: 事件类型列表
            date_range: 日期范围 (start_date, end_date)
            limit: 返回记录数限制
            
        Returns:
            查询结果DataFrame
        """
        try:
            filters = {}
            
            if user_ids:
                filters['user_pseudo_id'] = user_ids
            if event_types:
                filters['event_name'] = event_types
            if date_range:
                start_date, end_date = date_range
                filters['event_date'] = {'gte': start_date, 'lte': end_date}
                
            result = self.get_data('events', filters)
            
            if limit and len(result) > limit:
                result = result.head(limit)
                
            return result
            
        except Exception as e:
            logger.error(f"查询事件数据失败: {e}")
            raise
            
    def query_users(self,
                   platforms: Optional[List[str]] = None,
                   device_categories: Optional[List[str]] = None,
                   countries: Optional[List[str]] = None) -> pd.DataFrame:
        """
        查询用户数据
        
        Args:
            platforms: 平台列表
            device_categories: 设备类别列表
            countries: 国家列表
            
        Returns:
            查询结果DataFrame
        """
        try:
            filters = {}
            
            if platforms:
                filters['platform'] = platforms
            if device_categories:
                filters['device_category'] = device_categories
            if countries:
                filters['geo_country'] = countries
                
            return self.get_data('users', filters)
            
        except Exception as e:
            logger.error(f"查询用户数据失败: {e}")
            raise
            
    def query_sessions(self,
                      user_ids: Optional[List[str]] = None,
                      min_duration: Optional[int] = None,
                      min_events: Optional[int] = None,
                      has_conversions: Optional[bool] = None) -> pd.DataFrame:
        """
        查询会话数据
        
        Args:
            user_ids: 用户ID列表
            min_duration: 最小会话时长（秒）
            min_events: 最小事件数
            has_conversions: 是否有转化
            
        Returns:
            查询结果DataFrame
        """
        try:
            filters = {}
            
            if user_ids:
                filters['user_pseudo_id'] = user_ids
            if min_duration is not None:
                filters['duration_seconds'] = {'gte': min_duration}
            if min_events is not None:
                filters['event_count'] = {'gte': min_events}
            if has_conversions is not None:
                if has_conversions:
                    filters['conversions'] = {'gt': 0}
                else:
                    filters['conversions'] = 0
                    
            return self.get_data('sessions', filters)
            
        except Exception as e:
            logger.error(f"查询会话数据失败: {e}")
            raise
            
    def get_statistics(self) -> StorageStats:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        try:
            with self._lock:
                # 计算内存使用量
                memory_usage = 0
                if not self._events_data.empty:
                    memory_usage += self._events_data.memory_usage(deep=True).sum()
                if not self._users_data.empty:
                    memory_usage += self._users_data.memory_usage(deep=True).sum()
                if not self._sessions_data.empty:
                    memory_usage += self._sessions_data.memory_usage(deep=True).sum()
                
                memory_usage_mb = memory_usage / (1024 * 1024)
                
                return StorageStats(
                    total_events=len(self._events_data),
                    total_users=len(self._users_data),
                    total_sessions=len(self._sessions_data),
                    memory_usage_mb=memory_usage_mb,
                    last_updated=self._last_updated
                )
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            raise
            
    def clear_data(self, data_type: Optional[str] = None) -> None:
        """
        清空数据
        
        Args:
            data_type: 要清空的数据类型，None表示清空所有数据
        """
        try:
            with self._lock:
                if data_type is None or data_type == 'all':
                    self._events_data = pd.DataFrame()
                    self._users_data = pd.DataFrame()
                    self._sessions_data = pd.DataFrame()
                    self._events_by_type = {}
                    logger.info("已清空所有数据")
                elif data_type == 'events':
                    self._events_data = pd.DataFrame()
                    self._events_by_type = {}
                    logger.info("已清空事件数据")
                elif data_type == 'users':
                    self._users_data = pd.DataFrame()
                    logger.info("已清空用户数据")
                elif data_type == 'sessions':
                    self._sessions_data = pd.DataFrame()
                    logger.info("已清空会话数据")
                else:
                    raise ValueError(f"不支持的数据类型: {data_type}")
                    
                self._last_updated = datetime.now()
                
        except Exception as e:
            logger.error(f"清空数据失败: {e}")
            raise
            
    def export_data(self, data_type: str, file_path: str, format: str = 'csv') -> None:
        """
        导出数据到文件
        
        Args:
            data_type: 数据类型
            file_path: 文件路径
            format: 文件格式 ('csv', 'json', 'parquet')
        """
        try:
            data = self.get_data(data_type)
            
            if data.empty:
                logger.warning(f"数据类型 {data_type} 为空，无法导出")
                return
                
            if format.lower() == 'csv':
                data.to_csv(file_path, index=False)
            elif format.lower() == 'json':
                data.to_json(file_path, orient='records', lines=True)
            elif format.lower() == 'parquet':
                data.to_parquet(file_path, index=False)
            else:
                raise ValueError(f"不支持的文件格式: {format}")
                
            logger.info(f"成功导出{len(data)}条{data_type}数据到 {file_path}")
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            raise
            
    def import_data(self, data_type: str, file_path: str, format: str = 'csv') -> None:
        """
        从文件导入数据
        
        Args:
            data_type: 数据类型
            file_path: 文件路径
            format: 文件格式 ('csv', 'json', 'parquet')
        """
        try:
            if format.lower() == 'csv':
                data = pd.read_csv(file_path)
            elif format.lower() == 'json':
                data = pd.read_json(file_path, lines=True)
            elif format.lower() == 'parquet':
                data = pd.read_parquet(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {format}")
                
            # 存储数据
            if data_type == 'events':
                self.store_events(data)
            elif data_type == 'users':
                self.store_users(data)
            elif data_type == 'sessions':
                self.store_sessions(data)
            else:
                raise ValueError(f"不支持的数据类型: {data_type}")
                
            logger.info(f"成功从 {file_path} 导入{len(data)}条{data_type}数据")
            
        except Exception as e:
            logger.error(f"导入数据失败: {e}")
            raise
            
    def _create_event_indexes(self) -> None:
        """创建事件数据索引"""
        try:
            if self._events_data.empty:
                return
                
            # 为常用查询列创建索引（在pandas中主要是排序）
            for index_col in self._event_indexes:
                if index_col in self._events_data.columns:
                    self._events_data = self._events_data.sort_values(index_col)
                    
            logger.debug("事件数据索引创建完成")
            
        except Exception as e:
            logger.warning(f"创建事件索引失败: {e}")
            
    def _create_user_indexes(self) -> None:
        """创建用户数据索引"""
        try:
            if self._users_data.empty:
                return
                
            for index_col in self._user_indexes:
                if index_col in self._users_data.columns:
                    self._users_data = self._users_data.sort_values(index_col)
                    
            logger.debug("用户数据索引创建完成")
            
        except Exception as e:
            logger.warning(f"创建用户索引失败: {e}")
            
    def _create_session_indexes(self) -> None:
        """创建会话数据索引"""
        try:
            if self._sessions_data.empty:
                return
                
            for index_col in self._session_indexes:
                if index_col in self._sessions_data.columns:
                    self._sessions_data = self._sessions_data.sort_values(index_col)
                    
            logger.debug("会话数据索引创建完成")
            
        except Exception as e:
            logger.warning(f"创建会话索引失败: {e}")
            
    def get_event_types(self) -> List[str]:
        """
        获取所有事件类型
        
        Returns:
            事件类型列表
        """
        with self._lock:
            return list(self._events_by_type.keys())
            
    def get_user_count(self) -> int:
        """
        获取用户总数
        
        Returns:
            用户数量
        """
        with self._lock:
            return len(self._users_data)
            
    def get_event_count(self, event_type: Optional[str] = None) -> int:
        """
        获取事件总数
        
        Args:
            event_type: 特定事件类型，None表示所有事件
            
        Returns:
            事件数量
        """
        with self._lock:
            if event_type is None:
                return len(self._events_data)
            else:
                return len(self._events_by_type.get(event_type, pd.DataFrame()))
                
    def get_session_count(self) -> int:
        """
        获取会话总数
        
        Returns:
            会话数量
        """
        with self._lock:
            return len(self._sessions_data)
            
    def aggregate_events(self, 
                        group_by: List[str], 
                        agg_functions: Dict[str, str],
                        filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        聚合事件数据
        
        Args:
            group_by: 分组字段列表
            agg_functions: 聚合函数字典 {column: function}
            filters: 过滤条件
            
        Returns:
            聚合结果DataFrame
        """
        try:
            # 获取过滤后的数据
            data = self.get_data('events', filters)
            
            if data.empty:
                return pd.DataFrame()
                
            # 检查分组字段是否存在
            missing_columns = set(group_by) - set(data.columns)
            if missing_columns:
                raise ValueError(f"分组字段不存在: {missing_columns}")
                
            # 执行聚合
            result = data.groupby(group_by).agg(agg_functions).reset_index()
            
            logger.debug(f"聚合完成，结果包含{len(result)}行")
            return result
            
        except Exception as e:
            logger.error(f"聚合事件数据失败: {e}")
            raise
            
    def get_data_summary(self) -> Dict[str, Any]:
        """
        获取数据摘要信息
        
        Returns:
            数据摘要字典
        """
        try:
            with self._lock:
                summary = {
                    'events': {
                        'total_count': len(self._events_data),
                        'event_types': list(self._events_by_type.keys()),
                        'date_range': self._get_date_range_summary(self._events_data),
                        'top_events': self._get_top_events()
                    },
                    'users': {
                        'total_count': len(self._users_data),
                        'platforms': self._get_value_counts(self._users_data, 'platform'),
                        'device_categories': self._get_value_counts(self._users_data, 'device_category'),
                        'countries': self._get_value_counts(self._users_data, 'geo_country')
                    },
                    'sessions': {
                        'total_count': len(self._sessions_data),
                        'avg_duration': self._get_avg_value(self._sessions_data, 'duration_seconds'),
                        'avg_events': self._get_avg_value(self._sessions_data, 'event_count'),
                        'conversion_rate': self._get_conversion_rate()
                    },
                    'storage': {
                        'memory_usage_mb': self.get_statistics().memory_usage_mb,
                        'last_updated': self._last_updated.isoformat()
                    }
                }
                
                return summary
                
        except Exception as e:
            logger.error(f"获取数据摘要失败: {e}")
            raise
            
    def _get_date_range_summary(self, data: pd.DataFrame) -> Dict[str, str]:
        """获取日期范围摘要"""
        if data.empty or 'event_timestamp' not in data.columns:
            return {'start': 'N/A', 'end': 'N/A'}
            
        try:
            timestamps = pd.to_datetime(data['event_timestamp'], unit='us')
            return {
                'start': timestamps.min().strftime('%Y-%m-%d'),
                'end': timestamps.max().strftime('%Y-%m-%d')
            }
        except Exception:
            return {'start': 'N/A', 'end': 'N/A'}
            
    def _get_value_counts(self, data: pd.DataFrame, column: str) -> Dict[str, int]:
        """获取值计数"""
        if data.empty or column not in data.columns:
            return {}
            
        try:
            return data[column].value_counts().head(5).to_dict()
        except Exception:
            return {}
            
    def _get_avg_value(self, data: pd.DataFrame, column: str) -> float:
        """获取平均值"""
        if data.empty or column not in data.columns:
            return 0.0
            
        try:
            return float(data[column].mean())
        except Exception:
            return 0.0
            
    def _get_top_events(self) -> Dict[str, int]:
        """获取热门事件"""
        if self._events_data.empty:
            return {}
            
        try:
            return self._events_data['event_name'].value_counts().head(5).to_dict()
        except Exception:
            return {}
            
    def _get_conversion_rate(self) -> float:
        """获取转化率"""
        if self._sessions_data.empty or 'conversions' not in self._sessions_data.columns:
            return 0.0
            
        try:
            total_sessions = len(self._sessions_data)
            conversion_sessions = len(self._sessions_data[self._sessions_data['conversions'] > 0])
            return conversion_sessions / total_sessions if total_sessions > 0 else 0.0
        except Exception:
            return 0.0
            
    def get_events(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        获取事件数据（便捷方法）
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            事件数据DataFrame
        """
        return self.get_data('events', filters)
        
    def get_users(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        获取用户数据（便捷方法）
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            用户数据DataFrame
        """
        return self.get_data('users', filters)
        
    def get_sessions(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        获取会话数据（便捷方法）
        
        Args:
            filters: 过滤条件字典
            
        Returns:
            会话数据DataFrame
        """
        return self.get_data('sessions', filters)