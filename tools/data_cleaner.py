"""
数据清洗工具模块

提供GA4数据的清洗、标准化和预处理功能。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗器类"""
    
    def __init__(self):
        """初始化清洗器"""
        self.standard_event_names = {
            'pageview': 'page_view',
            'page-view': 'page_view',
            'signup': 'sign_up',
            'sign-up': 'sign_up',
            'signin': 'login',
            'sign-in': 'login',
            'log-in': 'login',
            'addtocart': 'add_to_cart',
            'add-to-cart': 'add_to_cart',
            'viewitem': 'view_item',
            'view-item': 'view_item'
        }
        
        self.standard_countries = {
            'usa': 'US',
            'united states': 'US',
            'china': 'CN',
            'japan': 'JP',
            'germany': 'DE',
            'france': 'FR',
            'uk': 'GB',
            'united kingdom': 'GB'
        }
        
        self.device_categories = {
            'pc': 'desktop',
            'computer': 'desktop',
            'laptop': 'desktop',
            'phone': 'mobile',
            'smartphone': 'mobile',
            'iphone': 'mobile',
            'android': 'mobile',
            'ipad': 'tablet',
            'tab': 'tablet'
        }
        
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗整个DataFrame
        
        Args:
            df: 原始数据DataFrame
            
        Returns:
            清洗后的DataFrame
        """
        try:
            logger.info(f"开始清洗数据，原始数据{len(df)}行")
            
            cleaned_df = df.copy()
            
            # 1. 移除重复数据
            cleaned_df = self._remove_duplicates(cleaned_df)
            
            # 2. 标准化事件名称
            cleaned_df = self._standardize_event_names(cleaned_df)
            
            # 3. 清洗时间戳数据
            cleaned_df = self._clean_timestamps(cleaned_df)
            
            # 4. 标准化地理位置信息
            cleaned_df = self._standardize_geo_data(cleaned_df)
            
            # 5. 标准化设备信息
            cleaned_df = self._standardize_device_data(cleaned_df)
            
            # 6. 处理缺失值
            cleaned_df = self._handle_missing_values(cleaned_df)
            
            # 7. 移除异常值
            cleaned_df = self._remove_outliers(cleaned_df)
            
            # 8. 数据类型转换
            cleaned_df = self._convert_data_types(cleaned_df)
            
            logger.info(f"数据清洗完成，清洗后数据{len(cleaned_df)}行，移除了{len(df) - len(cleaned_df)}行")
            
            return cleaned_df
            
        except Exception as e:
            logger.error(f"数据清洗失败: {e}")
            raise
            
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """移除重复数据"""
        original_count = len(df)
        
        # 基于关键字段去重
        key_columns = ['user_pseudo_id', 'event_timestamp', 'event_name']
        available_columns = [col for col in key_columns if col in df.columns]
        
        if available_columns:
            df_cleaned = df.drop_duplicates(subset=available_columns, keep='first')
            removed_count = original_count - len(df_cleaned)
            if removed_count > 0:
                logger.info(f"移除了{removed_count}条重复数据")
            return df_cleaned
        else:
            logger.warning("未找到去重所需的关键字段")
            return df
            
    def _standardize_event_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化事件名称"""
        if 'event_name' not in df.columns:
            return df
            
        df_cleaned = df.copy()
        
        # 转换为小写并去除空格
        df_cleaned['event_name'] = df_cleaned['event_name'].str.lower().str.strip()
        
        # 应用标准化映射
        df_cleaned['event_name'] = df_cleaned['event_name'].replace(self.standard_event_names)
        
        # 移除无效字符
        df_cleaned['event_name'] = df_cleaned['event_name'].str.replace(r'[^\w_]', '_', regex=True)
        
        logger.info("事件名称标准化完成")
        return df_cleaned
        
    def _clean_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗时间戳数据"""
        if 'event_timestamp' not in df.columns:
            return df
            
        df_cleaned = df.copy()
        
        # 移除无效时间戳
        df_cleaned = df_cleaned[df_cleaned['event_timestamp'] > 0]
        
        # 转换时间戳格式（确保是微秒级）
        df_cleaned['event_timestamp'] = pd.to_numeric(df_cleaned['event_timestamp'], errors='coerce')
        
        # 移除异常时间戳（未来时间或过于久远的时间）
        now_microseconds = int(datetime.now().timestamp() * 1000000)
        two_years_ago_microseconds = int((datetime.now() - timedelta(days=730)).timestamp() * 1000000)
        
        df_cleaned = df_cleaned[
            (df_cleaned['event_timestamp'] <= now_microseconds) &
            (df_cleaned['event_timestamp'] >= two_years_ago_microseconds)
        ]
        
        # 创建datetime列
        df_cleaned['event_datetime'] = pd.to_datetime(df_cleaned['event_timestamp'], unit='us')
        
        logger.info("时间戳数据清洗完成")
        return df_cleaned
        
    def _standardize_geo_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化地理位置信息"""
        if 'geo' not in df.columns:
            return df
            
        df_cleaned = df.copy()
        
        # 提取并标准化国家信息
        df_cleaned['geo_country'] = df_cleaned['geo'].apply(
            lambda x: self._extract_and_standardize_country(x) if isinstance(x, dict) else ''
        )
        
        # 提取并标准化城市信息
        df_cleaned['geo_city'] = df_cleaned['geo'].apply(
            lambda x: self._extract_and_standardize_city(x) if isinstance(x, dict) else ''
        )
        
        logger.info("地理位置信息标准化完成")
        return df_cleaned
        
    def _extract_and_standardize_country(self, geo_dict: Dict[str, Any]) -> str:
        """提取并标准化国家信息"""
        country = geo_dict.get('country', '')
        
        if not country or country is None:
            return ''
            
        country = str(country).strip().lower()
            
        # 应用标准化映射
        if country in self.standard_countries:
            return self.standard_countries[country]
            
        # 如果已经是2位代码，转换为大写
        if len(country) == 2 and country.isalpha():
            return country.upper()
            
        return country.upper()
        
    def _extract_and_standardize_city(self, geo_dict: Dict[str, Any]) -> str:
        """提取并标准化城市信息"""
        city = geo_dict.get('city', '')
        
        if not city or city is None:
            return ''
            
        # 标准化城市名称格式
        return str(city).strip().title()
        
    def _standardize_device_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化设备信息"""
        if 'device' not in df.columns:
            return df
            
        df_cleaned = df.copy()
        
        # 提取并标准化设备类别
        df_cleaned['device_category'] = df_cleaned['device'].apply(
            lambda x: self._extract_and_standardize_device_category(x) if isinstance(x, dict) else ''
        )
        
        # 提取并标准化操作系统
        df_cleaned['device_os'] = df_cleaned['device'].apply(
            lambda x: self._extract_and_standardize_os(x) if isinstance(x, dict) else ''
        )
        
        # 提取并标准化浏览器
        df_cleaned['device_browser'] = df_cleaned['device'].apply(
            lambda x: self._extract_and_standardize_browser(x) if isinstance(x, dict) else ''
        )
        
        logger.info("设备信息标准化完成")
        return df_cleaned
        
    def _extract_and_standardize_device_category(self, device_dict: Dict[str, Any]) -> str:
        """提取并标准化设备类别"""
        category = device_dict.get('category', '')
        
        if not category or category is None:
            return ''
            
        category = str(category).strip().lower()
            
        # 应用标准化映射
        if category in self.device_categories:
            return self.device_categories[category]
            
        return category
        
    def _extract_and_standardize_os(self, device_dict: Dict[str, Any]) -> str:
        """提取并标准化操作系统"""
        os_name = device_dict.get('operating_system', '')
        
        if not os_name or os_name is None:
            return ''
            
        os_name = str(os_name).strip().lower()
            
        # 标准化常见操作系统名称
        os_mapping = {
            'win': 'windows',
            'mac': 'macos',
            'osx': 'macos',
            'linux': 'linux',
            'android': 'android',
            'ios': 'ios',
            'chromeos': 'chrome_os'
        }
        
        for key, value in os_mapping.items():
            if key in os_name:
                return value
                
        return os_name
        
    def _extract_and_standardize_browser(self, device_dict: Dict[str, Any]) -> str:
        """提取并标准化浏览器"""
        browser = device_dict.get('browser', '')
        
        if not browser or browser is None:
            return ''
            
        browser = str(browser).strip().lower()
            
        # 标准化常见浏览器名称
        browser_mapping = {
            'chrome': 'chrome',
            'firefox': 'firefox',
            'safari': 'safari',
            'edge': 'edge',
            'ie': 'internet_explorer',
            'opera': 'opera'
        }
        
        for key, value in browser_mapping.items():
            if key in browser:
                return value
                
        return browser
        
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        df_cleaned = df.copy()
        
        # 字符串字段用空字符串填充
        string_columns = ['user_id', 'geo_country', 'geo_city', 'device_category', 'device_os', 'device_browser']
        for col in string_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = df_cleaned[col].fillna('')
                
        # 数值字段用0填充
        numeric_columns = ['event_timestamp']
        for col in numeric_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = df_cleaned[col].fillna(0)
                
        # 列表字段用空列表填充
        list_columns = ['event_params', 'user_properties', 'items']
        for col in list_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = df_cleaned[col].apply(lambda x: x if isinstance(x, list) else [])
                
        logger.info("缺失值处理完成")
        return df_cleaned
        
    def _remove_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """移除异常值"""
        df_cleaned = df.copy()
        original_count = len(df_cleaned)
        
        # 移除异常的事件名称（过长或包含特殊字符）
        if 'event_name' in df_cleaned.columns:
            df_cleaned = df_cleaned[
                (df_cleaned['event_name'].str.len() <= 50) &
                (df_cleaned['event_name'].str.match(r'^[a-zA-Z0-9_]+$'))
            ]
            
        # 移除异常的用户ID（过长）
        if 'user_pseudo_id' in df_cleaned.columns:
            df_cleaned = df_cleaned[df_cleaned['user_pseudo_id'].str.len() <= 100]
            
        removed_count = original_count - len(df_cleaned)
        if removed_count > 0:
            logger.info(f"移除了{removed_count}条异常数据")
            
        return df_cleaned
        
    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换数据类型"""
        df_cleaned = df.copy()
        
        # 确保时间戳为整数类型
        if 'event_timestamp' in df_cleaned.columns:
            df_cleaned['event_timestamp'] = df_cleaned['event_timestamp'].astype('int64')
            
        # 确保字符串字段为字符串类型
        string_columns = ['event_name', 'user_pseudo_id', 'user_id', 'platform', 
                         'geo_country', 'geo_city', 'device_category', 'device_os', 'device_browser']
        for col in string_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = df_cleaned[col].astype('string')
                
        logger.info("数据类型转换完成")
        return df_cleaned
        
    def clean_event_params(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗事件参数数据
        
        Args:
            df: 包含事件参数的DataFrame
            
        Returns:
            清洗后的DataFrame
        """
        if 'event_params' not in df.columns:
            return df
            
        df_cleaned = df.copy()
        
        # 标准化参数结构
        df_cleaned['event_params'] = df_cleaned['event_params'].apply(
            self._clean_params_list
        )
        
        logger.info("事件参数清洗完成")
        return df_cleaned
        
    def _clean_params_list(self, params: Any) -> List[Dict[str, Any]]:
        """清洗参数列表"""
        if not isinstance(params, list):
            return []
            
        cleaned_params = []
        
        for param in params:
            if not isinstance(param, dict):
                continue
                
            if 'key' not in param or 'value' not in param:
                continue
                
            # 标准化参数键名
            key = str(param['key']).strip().lower()
            if not key:
                continue
                
            # 清洗参数值
            value = self._clean_param_value(param['value'])
            
            cleaned_params.append({
                'key': key,
                'value': value
            })
            
        return cleaned_params
        
    def _clean_param_value(self, value: Any) -> Dict[str, Any]:
        """清洗参数值"""
        if not isinstance(value, dict):
            return {'string_value': str(value)}
            
        # 确保值结构正确
        cleaned_value = {}
        
        if 'string_value' in value:
            cleaned_value['string_value'] = str(value['string_value']).strip()
        elif 'int_value' in value:
            try:
                cleaned_value['int_value'] = int(value['int_value'])
            except (ValueError, TypeError):
                cleaned_value['string_value'] = str(value['int_value'])
        elif 'double_value' in value:
            try:
                cleaned_value['double_value'] = float(value['double_value'])
            except (ValueError, TypeError):
                cleaned_value['string_value'] = str(value['double_value'])
        else:
            cleaned_value['string_value'] = str(value)
            
        return cleaned_value
        
    def generate_cleaning_report(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成清洗报告
        
        Args:
            original_df: 原始数据
            cleaned_df: 清洗后数据
            
        Returns:
            清洗报告
        """
        report = {
            'original_rows': len(original_df),
            'cleaned_rows': len(cleaned_df),
            'removed_rows': len(original_df) - len(cleaned_df),
            'removal_rate': (len(original_df) - len(cleaned_df)) / len(original_df) if len(original_df) > 0 else 0,
            'data_quality_improvements': {},
            'standardizations_applied': []
        }
        
        # 比较数据质量改进
        if 'event_name' in original_df.columns and 'event_name' in cleaned_df.columns:
            original_unique_events = original_df['event_name'].nunique()
            cleaned_unique_events = cleaned_df['event_name'].nunique()
            report['data_quality_improvements']['event_standardization'] = {
                'original_unique_events': original_unique_events,
                'cleaned_unique_events': cleaned_unique_events,
                'reduction': original_unique_events - cleaned_unique_events
            }
            
        # 记录应用的标准化
        report['standardizations_applied'] = [
            'event_name_standardization',
            'geo_data_standardization',
            'device_data_standardization',
            'timestamp_cleaning',
            'duplicate_removal',
            'outlier_removal'
        ]
        
        return report