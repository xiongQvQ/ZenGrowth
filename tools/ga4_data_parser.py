"""
GA4数据解析器模块

该模块提供GA4 NDJSON格式数据的解析、验证和清洗功能。
支持事件数据提取、用户属性解析和会话数据重构。
"""

import json
import pandas as pd
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
from dataclasses import dataclass
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class EventData:
    """事件数据模型"""
    event_date: str
    event_timestamp: int
    event_name: str
    user_pseudo_id: str
    user_id: Optional[str]
    platform: str
    device: Dict[str, Any]
    geo: Dict[str, Any]
    traffic_source: Dict[str, Any]
    event_params: List[Dict[str, Any]]
    user_properties: List[Dict[str, Any]]
    items: Optional[List[Dict[str, Any]]] = None


@dataclass
class UserSession:
    """用户会话数据模型"""
    session_id: str
    user_id: str
    user_pseudo_id: str
    start_time: datetime
    end_time: datetime
    events: List[EventData]
    duration: int
    page_views: int
    conversions: int
    platform: str
    device: Dict[str, Any]
    geo: Dict[str, Any]


class GA4DataParser:
    """GA4数据解析器类"""
    
    def __init__(self):
        """初始化解析器"""
        self.supported_events = {
            'page_view', 'sign_up', 'login', 'search', 'view_item', 
            'view_item_list', 'select_item', 'add_to_cart', 'begin_checkout',
            'purchase', 'remove_from_cart', 'view_cart', 'add_payment_info',
            'add_shipping_info', 'view_promotion', 'select_promotion'
        }
        self.conversion_events = {
            'sign_up', 'login', 'purchase', 'begin_checkout', 'add_to_cart'
        }
        
    def parse_ndjson(self, file_path: str) -> pd.DataFrame:
        """
        解析NDJSON格式的GA4数据文件
        
        Args:
            file_path: NDJSON文件路径
            
        Returns:
            包含解析后数据的DataFrame
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
                
            events_data = []
            
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        event_json = json.loads(line)
                        # 验证必需字段
                        if self._validate_event_structure(event_json):
                            events_data.append(event_json)
                        else:
                            logger.warning(f"第{line_num}行数据结构不完整，已跳过")
                    except json.JSONDecodeError as e:
                        logger.error(f"第{line_num}行JSON解析错误: {e}")
                        continue
                        
            if not events_data:
                raise ValueError("未找到有效的事件数据")
                
            df = pd.DataFrame(events_data)
            logger.info(f"成功解析{len(df)}条事件数据")
            
            return df
            
        except Exception as e:
            logger.error(f"解析NDJSON文件失败: {e}")
            raise
            
    def _validate_event_structure(self, event: Dict[str, Any]) -> bool:
        """
        验证事件数据结构完整性
        
        Args:
            event: 事件数据字典
            
        Returns:
            验证结果
        """
        required_fields = [
            'event_date', 'event_timestamp', 'event_name', 
            'user_pseudo_id', 'platform', 'device', 'geo'
        ]
        
        for field in required_fields:
            if field not in event:
                return False
                
        # 验证嵌套结构
        if not isinstance(event.get('device'), dict):
            return False
        if not isinstance(event.get('geo'), dict):
            return False
        if not isinstance(event.get('event_params', []), list):
            return False
        if not isinstance(event.get('user_properties', []), list):
            return False
            
        return True
        
    def extract_events(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        从原始数据中提取和分类事件数据
        
        Args:
            data: 原始事件数据DataFrame
            
        Returns:
            按事件类型分类的数据字典
        """
        try:
            events_by_type = {}
            
            # 数据清洗和标准化
            cleaned_data = self._clean_event_data(data)
            
            # 按事件类型分组
            for event_type in cleaned_data['event_name'].unique():
                event_data = cleaned_data[cleaned_data['event_name'] == event_type].copy()
                
                # 解析事件参数
                event_data = self._parse_event_params(event_data)
                
                # 解析用户属性
                event_data = self._parse_user_properties(event_data)
                
                # 解析商品信息（如果存在）
                if 'items' in event_data.columns:
                    event_data = self._parse_items(event_data)
                
                events_by_type[event_type] = event_data
                
            logger.info(f"成功提取{len(events_by_type)}种事件类型")
            return events_by_type
            
        except Exception as e:
            logger.error(f"事件数据提取失败: {e}")
            raise
            
    def _clean_event_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        清洗和标准化事件数据
        
        Args:
            data: 原始数据DataFrame
            
        Returns:
            清洗后的数据DataFrame
        """
        cleaned_data = data.copy()
        
        # 转换时间戳
        cleaned_data['event_datetime'] = pd.to_datetime(
            cleaned_data['event_timestamp'], unit='us'
        )
        
        # 标准化事件名称
        cleaned_data['event_name'] = cleaned_data['event_name'].str.lower()
        
        # 处理缺失值
        cleaned_data['user_id'] = cleaned_data['user_id'].fillna('')
        
        # 添加派生字段
        cleaned_data['event_date_parsed'] = pd.to_datetime(
            cleaned_data['event_date'], format='%Y%m%d'
        )
        
        # 过滤支持的事件类型
        if self.supported_events:
            cleaned_data = cleaned_data[
                cleaned_data['event_name'].isin(self.supported_events)
            ]
            
        return cleaned_data
        
    def _parse_event_params(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        解析事件参数到独立列
        
        Args:
            data: 事件数据DataFrame
            
        Returns:
            包含解析参数的DataFrame
        """
        result_data = data.copy()
        
        # 提取常见参数
        param_columns = {}
        
        for idx, row in data.iterrows():
            params = row['event_params']
            if params is None or (isinstance(params, list) and len(params) == 0):
                continue
                
            for param in params:
                if not isinstance(param, dict) or 'key' not in param:
                    continue
                    
                key = param['key']
                value = self._extract_param_value(param.get('value', {}))
                
                if key not in param_columns:
                    param_columns[key] = {}
                param_columns[key][idx] = value
                
        # 添加参数列到DataFrame
        for param_name, values in param_columns.items():
            column_name = f"param_{param_name}"
            result_data[column_name] = pd.Series(values)
            
        return result_data
        
    def _parse_user_properties(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        解析用户属性到独立列
        
        Args:
            data: 事件数据DataFrame
            
        Returns:
            包含解析用户属性的DataFrame
        """
        result_data = data.copy()
        
        # 提取用户属性
        property_columns = {}
        
        for idx, row in data.iterrows():
            props = row['user_properties']
            if props is None or (isinstance(props, list) and len(props) == 0):
                continue
                
            for prop in props:
                if not isinstance(prop, dict) or 'key' not in prop:
                    continue
                    
                key = prop['key']
                value = self._extract_param_value(prop.get('value', {}))
                
                if key not in property_columns:
                    property_columns[key] = {}
                property_columns[key][idx] = value
                
        # 添加属性列到DataFrame
        for prop_name, values in property_columns.items():
            column_name = f"user_{prop_name}"
            result_data[column_name] = pd.Series(values)
            
        return result_data
        
    def _parse_items(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        解析商品信息
        
        Args:
            data: 事件数据DataFrame
            
        Returns:
            包含解析商品信息的DataFrame
        """
        result_data = data.copy()
        
        # 提取商品信息
        item_columns = {
            'item_ids': {},
            'item_categories': {},
            'item_prices': {},
            'item_quantities': {}
        }
        
        for idx, row in data.iterrows():
            items = row.get('items')
            if items is None or (isinstance(items, list) and len(items) == 0):
                continue
                
            # items already defined above
            if not isinstance(items, list):
                continue
                
            # 提取商品信息
            item_ids = []
            item_categories = []
            item_prices = []
            item_quantities = []
            
            for item in items:
                if isinstance(item, dict):
                    item_ids.append(item.get('item_id', ''))
                    item_categories.append(item.get('item_category', ''))
                    item_prices.append(item.get('price', 0))
                    item_quantities.append(item.get('quantity', 0))
                    
            item_columns['item_ids'][idx] = item_ids
            item_columns['item_categories'][idx] = item_categories
            item_columns['item_prices'][idx] = item_prices
            item_columns['item_quantities'][idx] = item_quantities
            
        # 添加商品列到DataFrame
        for column_name, values in item_columns.items():
            result_data[column_name] = pd.Series(values)
            
        return result_data
        
    def _extract_param_value(self, value_dict: Dict[str, Any]) -> Any:
        """
        从参数值字典中提取实际值
        
        Args:
            value_dict: 参数值字典
            
        Returns:
            提取的值
        """
        if not isinstance(value_dict, dict):
            return value_dict
            
        # GA4参数值的不同类型
        if 'string_value' in value_dict:
            return value_dict['string_value']
        elif 'int_value' in value_dict:
            return value_dict['int_value']
        elif 'double_value' in value_dict:
            return value_dict['double_value']
        elif 'float_value' in value_dict:
            return value_dict['float_value']
        else:
            return str(value_dict)
            
    def extract_user_properties(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        提取用户属性数据
        
        Args:
            data: 原始事件数据DataFrame
            
        Returns:
            用户属性数据DataFrame
        """
        try:
            # 确保有event_datetime列
            if 'event_datetime' not in data.columns:
                data = self._clean_event_data(data)
                
            # 按用户分组，获取最新的用户属性
            user_properties = []
            
            for user_id in data['user_pseudo_id'].unique():
                user_data = data[data['user_pseudo_id'] == user_id].copy()
                user_data = user_data.sort_values('event_timestamp')
                
                # 获取最新的用户信息
                latest_event = user_data.iloc[-1]
                
                user_info = {
                    'user_pseudo_id': user_id,
                    'user_id': latest_event.get('user_id', ''),
                    'platform': latest_event['platform'],
                    'device_category': latest_event['device'].get('category', ''),
                    'device_os': latest_event['device'].get('operating_system', ''),
                    'device_browser': latest_event['device'].get('browser', ''),
                    'geo_country': latest_event['geo'].get('country', ''),
                    'geo_city': latest_event['geo'].get('city', ''),
                    'first_seen': user_data['event_datetime'].min(),
                    'last_seen': user_data['event_datetime'].max(),
                    'total_events': len(user_data),
                    'unique_sessions': user_data['param_ga_session_id'].nunique() if 'param_ga_session_id' in user_data.columns else 1
                }
                
                # 提取用户属性
                user_props = latest_event['user_properties']
                if user_props is not None and isinstance(user_props, list) and len(user_props) > 0:
                    for prop in user_props:
                        if isinstance(prop, dict) and 'key' in prop:
                            key = f"user_{prop['key']}"
                            value = self._extract_param_value(prop.get('value', {}))
                            user_info[key] = value
                            
                user_properties.append(user_info)
                
            result_df = pd.DataFrame(user_properties)
            logger.info(f"成功提取{len(result_df)}个用户的属性数据")
            
            return result_df
            
        except Exception as e:
            logger.error(f"用户属性提取失败: {e}")
            raise
            
    def extract_sessions(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        提取和重构用户会话数据
        
        Args:
            data: 原始事件数据DataFrame
            
        Returns:
            会话数据DataFrame
        """
        try:
            # 确保有event_datetime列
            if 'event_datetime' not in data.columns:
                data = self._clean_event_data(data)
                
            sessions = []
            
            # 按用户和会话ID分组
            if 'param_ga_session_id' not in data.columns:
                # 如果没有会话ID，按用户和时间窗口分组
                sessions_data = self._create_sessions_by_time_window(data)
            else:
                sessions_data = data.groupby(['user_pseudo_id', 'param_ga_session_id'])
                
            for (user_id, session_id), session_events in sessions_data:
                session_events = session_events.sort_values('event_timestamp')
                
                # 计算会话统计
                start_time = session_events['event_datetime'].min()
                end_time = session_events['event_datetime'].max()
                duration = int((end_time - start_time).total_seconds())
                
                page_views = len(session_events[session_events['event_name'] == 'page_view'])
                conversions = len(session_events[session_events['event_name'].isin(self.conversion_events)])
                
                # 获取会话信息
                first_event = session_events.iloc[0]
                
                session_info = {
                    'session_id': str(session_id),
                    'user_pseudo_id': user_id,
                    'user_id': first_event.get('user_id', ''),
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_seconds': duration,
                    'event_count': len(session_events),
                    'page_views': page_views,
                    'conversions': conversions,
                    'platform': first_event['platform'],
                    'device_category': first_event['device'].get('category', ''),
                    'device_os': first_event['device'].get('operating_system', ''),
                    'geo_country': first_event['geo'].get('country', ''),
                    'geo_city': first_event['geo'].get('city', ''),
                    'traffic_source': first_event.get('traffic_source', {}),
                    'events': session_events.to_dict('records')
                }
                
                sessions.append(session_info)
                
            result_df = pd.DataFrame(sessions)
            logger.info(f"成功提取{len(result_df)}个用户会话")
            
            return result_df
            
        except Exception as e:
            logger.error(f"会话数据提取失败: {e}")
            raise
            
    def _create_sessions_by_time_window(self, data: pd.DataFrame, window_minutes: int = 30) -> pd.DataFrame:
        """
        基于时间窗口创建会话分组
        
        Args:
            data: 事件数据DataFrame
            window_minutes: 会话超时时间（分钟）
            
        Returns:
            带有会话ID的数据DataFrame
        """
        data_with_sessions = data.copy()
        data_with_sessions['param_ga_session_id'] = ''
        
        for user_id in data['user_pseudo_id'].unique():
            user_events = data[data['user_pseudo_id'] == user_id].sort_values('event_timestamp')
            
            session_id = 1
            last_timestamp = None
            
            for idx, event in user_events.iterrows():
                current_timestamp = event['event_datetime']
                
                if last_timestamp is None:
                    data_with_sessions.loc[idx, 'param_ga_session_id'] = f"{user_id}_{session_id}"
                else:
                    time_diff = (current_timestamp - last_timestamp).total_seconds() / 60
                    if time_diff > window_minutes:
                        session_id += 1
                    data_with_sessions.loc[idx, 'param_ga_session_id'] = f"{user_id}_{session_id}"
                    
                last_timestamp = current_timestamp
                
        return data_with_sessions.groupby(['user_pseudo_id', 'param_ga_session_id'])
        
    def validate_data_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        验证数据质量和完整性
        
        Args:
            data: 要验证的数据DataFrame
            
        Returns:
            数据质量报告
        """
        try:
            # 确保有event_datetime列
            if 'event_datetime' not in data.columns:
                data = self._clean_event_data(data)
                
            quality_report = {
                'total_events': len(data),
                'unique_users': data['user_pseudo_id'].nunique(),
                'date_range': {
                    'start': data['event_datetime'].min().strftime('%Y-%m-%d'),
                    'end': data['event_datetime'].max().strftime('%Y-%m-%d')
                },
                'event_types': data['event_name'].value_counts().to_dict(),
                'platforms': data['platform'].value_counts().to_dict(),
                'missing_data': {
                    'user_id': data['user_id'].isna().sum(),
                    'event_params': data['event_params'].isna().sum(),
                    'user_properties': data['user_properties'].isna().sum()
                },
                'data_issues': []
            }
            
            # 检查数据问题
            if quality_report['missing_data']['user_id'] > len(data) * 0.5:
                quality_report['data_issues'].append("超过50%的事件缺少user_id")
                
            if len(quality_report['event_types']) < 3:
                quality_report['data_issues'].append("事件类型过少，可能影响分析质量")
                
            # 检查时间戳一致性
            invalid_timestamps = data[data['event_timestamp'] <= 0]
            if len(invalid_timestamps) > 0:
                quality_report['data_issues'].append(f"发现{len(invalid_timestamps)}个无效时间戳")
                
            logger.info("数据质量验证完成")
            return quality_report
            
        except Exception as e:
            logger.error(f"数据质量验证失败: {e}")
            raise
            
    def clean_and_standardize(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        数据清洗和标准化
        
        Args:
            data: 原始数据DataFrame
            
        Returns:
            清洗后的数据DataFrame
        """
        try:
            cleaned_data = data.copy()
            
            # 移除重复事件
            cleaned_data = cleaned_data.drop_duplicates(
                subset=['user_pseudo_id', 'event_timestamp', 'event_name']
            )
            
            # 标准化事件名称
            cleaned_data['event_name'] = cleaned_data['event_name'].str.lower().str.strip()
            
            # 处理异常值
            cleaned_data = cleaned_data[cleaned_data['event_timestamp'] > 0]
            
            # 标准化地理位置信息
            if 'geo' in cleaned_data.columns:
                cleaned_data['geo_country'] = cleaned_data['geo'].apply(
                    lambda x: x.get('country', '').upper() if isinstance(x, dict) else ''
                )
                cleaned_data['geo_city'] = cleaned_data['geo'].apply(
                    lambda x: x.get('city', '').title() if isinstance(x, dict) else ''
                )
                
            # 标准化设备信息
            if 'device' in cleaned_data.columns:
                cleaned_data['device_category'] = cleaned_data['device'].apply(
                    lambda x: x.get('category', '').lower() if isinstance(x, dict) else ''
                )
                
            logger.info(f"数据清洗完成，处理了{len(data) - len(cleaned_data)}条重复或异常数据")
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"数据清洗失败: {e}")
            raise