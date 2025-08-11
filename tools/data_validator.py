"""
数据验证工具模块

提供GA4数据的验证、质量检查和完整性验证功能。
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器类"""
    
    def __init__(self):
        """初始化验证器"""
        self.required_fields = [
            'event_date', 'event_timestamp', 'event_name', 
            'user_pseudo_id', 'platform', 'device', 'geo'
        ]
        
        self.valid_platforms = {'WEB', 'ANDROID', 'IOS'}
        self.valid_event_patterns = {
            'page_view': r'^page_view$',
            'sign_up': r'^sign_up$',
            'login': r'^login$',
            'purchase': r'^purchase$',
            'search': r'^search$',
            'view_item': r'^view_item$',
            'add_to_cart': r'^add_to_cart$'
        }
        
    def validate_event_structure(self, event: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证单个事件的数据结构
        
        Args:
            event: 事件数据字典
            
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必需字段
        for field in self.required_fields:
            if field not in event:
                errors.append(f"缺少必需字段: {field}")
            elif event[field] is None or event[field] == '':
                errors.append(f"字段值为空: {field}")
                
        # 验证数据类型
        if 'event_timestamp' in event:
            if not isinstance(event['event_timestamp'], (int, float)):
                errors.append("event_timestamp必须为数字类型")
            elif event['event_timestamp'] <= 0:
                errors.append("event_timestamp必须为正数")
                
        if 'platform' in event:
            if event['platform'] not in self.valid_platforms:
                errors.append(f"无效的平台类型: {event['platform']}")
                
        # 验证嵌套结构
        if 'device' in event:
            if not isinstance(event['device'], dict):
                errors.append("device字段必须为字典类型")
            else:
                device_errors = self._validate_device_structure(event['device'])
                errors.extend(device_errors)
                
        if 'geo' in event:
            if not isinstance(event['geo'], dict):
                errors.append("geo字段必须为字典类型")
            else:
                geo_errors = self._validate_geo_structure(event['geo'])
                errors.extend(geo_errors)
                
        # 验证事件参数
        if 'event_params' in event:
            if not isinstance(event['event_params'], list):
                errors.append("event_params必须为列表类型")
            else:
                param_errors = self._validate_event_params(event['event_params'])
                errors.extend(param_errors)
                
        return len(errors) == 0, errors
        
    def _validate_device_structure(self, device: Dict[str, Any]) -> List[str]:
        """验证设备信息结构"""
        errors = []
        
        if 'category' not in device:
            errors.append("device缺少category字段")
        elif device['category'] not in ['desktop', 'mobile', 'tablet']:
            errors.append(f"无效的设备类别: {device['category']}")
            
        return errors
        
    def _validate_geo_structure(self, geo: Dict[str, Any]) -> List[str]:
        """验证地理位置信息结构"""
        errors = []
        
        if 'country' in geo:
            country = geo['country']
            if not isinstance(country, str) or len(country) != 2:
                errors.append("country应为2位国家代码")
                
        return errors
        
    def _validate_event_params(self, params: List[Dict[str, Any]]) -> List[str]:
        """验证事件参数结构"""
        errors = []
        
        for i, param in enumerate(params):
            if not isinstance(param, dict):
                errors.append(f"事件参数{i}必须为字典类型")
                continue
                
            if 'key' not in param:
                errors.append(f"事件参数{i}缺少key字段")
                
            if 'value' not in param:
                errors.append(f"事件参数{i}缺少value字段")
            elif not isinstance(param['value'], dict):
                errors.append(f"事件参数{i}的value必须为字典类型")
                
        return errors
        
    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证DataFrame的数据质量
        
        Args:
            df: 要验证的DataFrame
            
        Returns:
            验证报告
        """
        report = {
            'total_rows': len(df),
            'validation_passed': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            # 基础统计
            report['statistics'] = {
                'unique_users': df['user_pseudo_id'].nunique() if 'user_pseudo_id' in df.columns else 0,
                'unique_events': df['event_name'].nunique() if 'event_name' in df.columns else 0,
                'date_range': self._get_date_range(df),
                'null_counts': df.isnull().sum().to_dict()
            }
            
            # 检查必需列
            missing_columns = set(self.required_fields) - set(df.columns)
            if missing_columns:
                report['errors'].append(f"缺少必需列: {missing_columns}")
                report['validation_passed'] = False
                
            # 检查数据完整性
            completeness_issues = self._check_data_completeness(df)
            report['warnings'].extend(completeness_issues)
            
            # 检查数据一致性
            consistency_issues = self._check_data_consistency(df)
            report['warnings'].extend(consistency_issues)
            
            # 检查异常值
            outlier_issues = self._check_outliers(df)
            report['warnings'].extend(outlier_issues)
            
            logger.info(f"数据验证完成: {len(df)}行数据，{len(report['errors'])}个错误，{len(report['warnings'])}个警告")
            
        except Exception as e:
            report['errors'].append(f"验证过程出错: {str(e)}")
            report['validation_passed'] = False
            logger.error(f"数据验证失败: {e}")
            
        return report
        
    def _get_date_range(self, df: pd.DataFrame) -> Dict[str, str]:
        """获取数据的日期范围"""
        try:
            if 'event_timestamp' in df.columns:
                timestamps = pd.to_datetime(df['event_timestamp'], unit='us')
                return {
                    'start': timestamps.min().strftime('%Y-%m-%d %H:%M:%S'),
                    'end': timestamps.max().strftime('%Y-%m-%d %H:%M:%S'),
                    'days': (timestamps.max() - timestamps.min()).days
                }
        except Exception:
            pass
            
        return {'start': 'N/A', 'end': 'N/A', 'days': 0}
        
    def _check_data_completeness(self, df: pd.DataFrame) -> List[str]:
        """检查数据完整性"""
        issues = []
        
        # 检查关键字段的缺失率
        critical_fields = ['user_pseudo_id', 'event_name', 'event_timestamp']
        for field in critical_fields:
            if field in df.columns:
                null_rate = df[field].isnull().sum() / len(df)
                if null_rate > 0.1:  # 超过10%缺失
                    issues.append(f"{field}字段缺失率过高: {null_rate:.2%}")
                    
        return issues
        
    def _check_data_consistency(self, df: pd.DataFrame) -> List[str]:
        """检查数据一致性"""
        issues = []
        
        # 检查时间戳一致性
        if 'event_timestamp' in df.columns and 'event_date' in df.columns:
            try:
                df_copy = df.copy()
                df_copy['timestamp_date'] = pd.to_datetime(df_copy['event_timestamp'], unit='us').dt.strftime('%Y%m%d')
                inconsistent = df_copy[df_copy['event_date'] != df_copy['timestamp_date']]
                if len(inconsistent) > 0:
                    issues.append(f"发现{len(inconsistent)}条时间戳与日期不一致的记录")
            except Exception:
                issues.append("时间戳格式异常，无法验证一致性")
                
        # 检查用户ID一致性
        if 'user_pseudo_id' in df.columns and 'user_id' in df.columns:
            user_mapping = df.groupby('user_pseudo_id')['user_id'].nunique()
            inconsistent_users = user_mapping[user_mapping > 1]
            if len(inconsistent_users) > 0:
                issues.append(f"发现{len(inconsistent_users)}个用户的user_id不一致")
                
        return issues
        
    def _check_outliers(self, df: pd.DataFrame) -> List[str]:
        """检查异常值"""
        issues = []
        
        # 检查时间戳异常值
        if 'event_timestamp' in df.columns:
            try:
                timestamps = pd.to_datetime(df['event_timestamp'], unit='us')
                now = datetime.now()
                future_events = timestamps[timestamps > now]
                old_events = timestamps[timestamps < now - timedelta(days=365*2)]  # 2年前
                
                if len(future_events) > 0:
                    issues.append(f"发现{len(future_events)}个未来时间戳")
                if len(old_events) > 0:
                    issues.append(f"发现{len(old_events)}个过于久远的时间戳")
            except Exception:
                issues.append("时间戳格式异常")
                
        return issues
        
    def validate_event_sequence(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        验证事件序列的合理性
        
        Args:
            df: 事件数据DataFrame
            
        Returns:
            序列验证报告
        """
        report = {
            'valid_sequences': 0,
            'invalid_sequences': 0,
            'sequence_issues': []
        }
        
        try:
            # 按用户分组检查事件序列
            for user_id in df['user_pseudo_id'].unique():
                user_events = df[df['user_pseudo_id'] == user_id].sort_values('event_timestamp')
                
                # 检查事件时间顺序
                if not user_events['event_timestamp'].is_monotonic_increasing:
                    report['sequence_issues'].append(f"用户{user_id}的事件时间顺序异常")
                    report['invalid_sequences'] += 1
                else:
                    report['valid_sequences'] += 1
                    
                # 检查逻辑序列（例如：购买前应该有浏览行为）
                events_list = user_events['event_name'].tolist()
                if 'purchase' in events_list:
                    purchase_index = events_list.index('purchase')
                    pre_purchase_events = events_list[:purchase_index]
                    if not any(event in ['page_view', 'view_item', 'add_to_cart'] for event in pre_purchase_events):
                        report['sequence_issues'].append(f"用户{user_id}的购买行为缺少前置浏览行为")
                        
        except Exception as e:
            report['sequence_issues'].append(f"序列验证出错: {str(e)}")
            
        return report
        
    def suggest_data_fixes(self, validation_report: Dict[str, Any]) -> List[str]:
        """
        基于验证报告提供数据修复建议
        
        Args:
            validation_report: 验证报告
            
        Returns:
            修复建议列表
        """
        suggestions = []
        
        # 基于错误类型提供建议
        for error in validation_report.get('errors', []):
            if '缺少必需列' in error:
                suggestions.append("检查数据源配置，确保导出包含所有必需字段")
            elif 'event_timestamp' in error:
                suggestions.append("验证时间戳格式，确保使用微秒级Unix时间戳")
                
        # 基于警告提供建议
        for warning in validation_report.get('warnings', []):
            if '缺失率过高' in warning:
                suggestions.append("检查数据收集配置，减少关键字段的缺失")
            elif '时间戳与日期不一致' in warning:
                suggestions.append("检查时区设置，确保时间戳和日期字段一致")
            elif 'user_id不一致' in warning:
                suggestions.append("检查用户标识逻辑，确保同一用户的ID映射一致")
                
        return suggestions