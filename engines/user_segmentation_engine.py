"""
用户分群引擎模块

提供用户特征提取和聚类分析功能。
支持基于行为和属性的用户分群，以及群体画像生成。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


@dataclass
class UserFeatures:
    """用户特征数据模型"""
    user_id: str
    behavioral_features: Dict[str, float]
    demographic_features: Dict[str, Any]
    engagement_features: Dict[str, float]
    conversion_features: Dict[str, float]
    temporal_features: Dict[str, float]


@dataclass
class UserSegment:
    """用户分群数据模型"""
    segment_id: int
    segment_name: str
    user_count: int
    user_ids: List[str]
    segment_profile: Dict[str, Any]
    key_characteristics: List[str]
    avg_features: Dict[str, float]


@dataclass
class SegmentationResult:
    """分群结果数据模型"""
    segments: List[UserSegment]
    segmentation_method: str
    feature_importance: Dict[str, float]
    quality_metrics: Dict[str, float]
    segment_comparison: pd.DataFrame


class UserSegmentationEngine:
    """用户分群引擎类"""
    
    def __init__(self, storage_manager=None):
        """
        初始化用户分群引擎
        
        Args:
            storage_manager: 数据存储管理器实例
        """
        self.storage_manager = storage_manager
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
        # 预定义的分群方法
        self.segmentation_methods = {
            'kmeans': self._kmeans_clustering,
            'dbscan': self._dbscan_clustering,
            'behavioral': self._behavioral_segmentation,
            'value_based': self._value_based_segmentation,
            'engagement': self._engagement_segmentation
        }
        
        logger.info("用户分群引擎初始化完成")
        
    def extract_user_features(self,
                            events: Optional[pd.DataFrame] = None,
                            users: Optional[pd.DataFrame] = None,
                            sessions: Optional[pd.DataFrame] = None) -> List[UserFeatures]:
        """
        提取用户特征
        
        Args:
            events: 事件数据DataFrame
            users: 用户数据DataFrame
            sessions: 会话数据DataFrame
            
        Returns:
            用户特征列表
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if users is None and self.storage_manager:
                users = self.storage_manager.get_data('users')
                
            if sessions is None and self.storage_manager:
                sessions = self.storage_manager.get_data('sessions')
                
            if events.empty:
                logger.warning("事件数据为空，无法提取用户特征")
                return []
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("缺少时间字段")
                    
            user_features_list = []
            
            # 按用户提取特征
            for user_id in events['user_pseudo_id'].unique():
                user_events = events[events['user_pseudo_id'] == user_id]
                user_info = users[users['user_pseudo_id'] == user_id].iloc[0] if not users.empty else None
                user_sessions = sessions[sessions['user_pseudo_id'] == user_id] if not sessions.empty else pd.DataFrame()
                
                # 提取各类特征
                behavioral_features = self._extract_behavioral_features(user_events)
                demographic_features = self._extract_demographic_features(user_info, user_events)
                engagement_features = self._extract_engagement_features(user_events, user_sessions)
                conversion_features = self._extract_conversion_features(user_events)
                temporal_features = self._extract_temporal_features(user_events)
                
                user_features = UserFeatures(
                    user_id=user_id,
                    behavioral_features=behavioral_features,
                    demographic_features=demographic_features,
                    engagement_features=engagement_features,
                    conversion_features=conversion_features,
                    temporal_features=temporal_features
                )
                
                user_features_list.append(user_features)
                
            logger.info(f"提取了{len(user_features_list)}个用户的特征")
            return user_features_list
            
        except Exception as e:
            logger.error(f"提取用户特征失败: {e}")
            raise
            
    def _extract_behavioral_features(self, user_events: pd.DataFrame) -> Dict[str, float]:
        """
        提取行为特征
        
        Args:
            user_events: 用户事件数据
            
        Returns:
            行为特征字典
        """
        try:
            features = {}
            
            # 基础行为统计
            features['total_events'] = len(user_events)
            features['unique_event_types'] = user_events['event_name'].nunique()
            features['avg_events_per_day'] = self._calculate_avg_events_per_day(user_events)
            
            # 事件类型分布
            event_counts = user_events['event_name'].value_counts()
            total_events = len(user_events)
            
            # 主要事件类型的比例
            common_events = ['page_view', 'login', 'purchase', 'add_to_cart', 'search', 'view_item']
            for event_type in common_events:
                features[f'{event_type}_ratio'] = event_counts.get(event_type, 0) / total_events if total_events > 0 else 0
                
            # 行为多样性（熵）
            if total_events > 0:
                event_probs = event_counts / total_events
                features['behavior_diversity'] = -sum(p * np.log2(p) for p in event_probs if p > 0)
            else:
                features['behavior_diversity'] = 0
                
            # 行为强度
            if 'event_datetime' in user_events.columns:
                time_span = (user_events['event_datetime'].max() - user_events['event_datetime'].min()).days + 1
                features['behavior_intensity'] = total_events / time_span if time_span > 0 else 0
            else:
                features['behavior_intensity'] = 0
                
            return features
            
        except Exception as e:
            logger.warning(f"提取行为特征失败: {e}")
            return {}
            
    def _extract_demographic_features(self, user_info: Optional[pd.Series], user_events: pd.DataFrame) -> Dict[str, Any]:
        """
        提取人口统计特征
        
        Args:
            user_info: 用户信息
            user_events: 用户事件数据
            
        Returns:
            人口统计特征字典
        """
        try:
            features = {}
            
            if user_info is not None:
                # 基础人口统计信息
                features['platform'] = user_info.get('platform', 'unknown')
                features['device_category'] = user_info.get('device_category', 'unknown')
                features['geo_country'] = user_info.get('geo_country', 'unknown')
            else:
                # 从事件数据中推断
                if not user_events.empty:
                    features['platform'] = user_events['platform'].iloc[0] if 'platform' in user_events.columns else 'unknown'
                    
                    # 从设备信息中提取
                    if 'device' in user_events.columns:
                        device_info = user_events['device'].iloc[0]
                        if isinstance(device_info, dict):
                            features['device_category'] = device_info.get('category', 'unknown')
                        else:
                            features['device_category'] = 'unknown'
                    else:
                        features['device_category'] = 'unknown'
                        
                    # 从地理信息中提取
                    if 'geo' in user_events.columns:
                        geo_info = user_events['geo'].iloc[0]
                        if isinstance(geo_info, dict):
                            features['geo_country'] = geo_info.get('country', 'unknown')
                        else:
                            features['geo_country'] = 'unknown'
                    else:
                        features['geo_country'] = 'unknown'
                else:
                    features['platform'] = 'unknown'
                    features['device_category'] = 'unknown'
                    features['geo_country'] = 'unknown'
                    
            return features
            
        except Exception as e:
            logger.warning(f"提取人口统计特征失败: {e}")
            return {'platform': 'unknown', 'device_category': 'unknown', 'geo_country': 'unknown'}
            
    def _extract_engagement_features(self, user_events: pd.DataFrame, user_sessions: pd.DataFrame) -> Dict[str, float]:
        """
        提取参与度特征
        
        Args:
            user_events: 用户事件数据
            user_sessions: 用户会话数据
            
        Returns:
            参与度特征字典
        """
        try:
            features = {}
            
            # 基于事件的参与度
            if not user_events.empty and 'event_datetime' in user_events.columns:
                # 活跃天数
                active_dates = user_events['event_datetime'].dt.date.unique()
                features['active_days'] = len(active_dates)
                
                # 活跃时间跨度
                time_span = (user_events['event_datetime'].max() - user_events['event_datetime'].min()).days + 1
                features['engagement_span_days'] = time_span
                
                # 活跃频率
                features['activity_frequency'] = len(active_dates) / time_span if time_span > 0 else 0
                
                # 最近活跃度
                last_activity = user_events['event_datetime'].max()
                days_since_last_activity = (datetime.now() - last_activity).days
                features['days_since_last_activity'] = days_since_last_activity
                features['recency_score'] = max(0, 1 - days_since_last_activity / 30)  # 30天内的活跃度得分
            else:
                features['active_days'] = 0
                features['engagement_span_days'] = 0
                features['activity_frequency'] = 0
                features['days_since_last_activity'] = 999
                features['recency_score'] = 0
                
            # 基于会话的参与度
            if not user_sessions.empty:
                features['total_sessions'] = len(user_sessions)
                features['avg_session_duration'] = user_sessions['duration_seconds'].mean() if 'duration_seconds' in user_sessions.columns else 0
                features['avg_events_per_session'] = user_sessions['event_count'].mean() if 'event_count' in user_sessions.columns else 0
                features['total_session_time'] = user_sessions['duration_seconds'].sum() if 'duration_seconds' in user_sessions.columns else 0
            else:
                features['total_sessions'] = 0
                features['avg_session_duration'] = 0
                features['avg_events_per_session'] = 0
                features['total_session_time'] = 0
                
            return features
            
        except Exception as e:
            logger.warning(f"提取参与度特征失败: {e}")
            return {}
            
    def _extract_conversion_features(self, user_events: pd.DataFrame) -> Dict[str, float]:
        """
        提取转化特征
        
        Args:
            user_events: 用户事件数据
            
        Returns:
            转化特征字典
        """
        try:
            features = {}
            
            # 转化事件定义
            conversion_events = {'sign_up', 'login', 'purchase', 'begin_checkout', 'add_to_cart'}
            
            # 转化事件统计
            total_events = len(user_events)
            conversion_event_counts = {}
            
            for event_type in conversion_events:
                count = len(user_events[user_events['event_name'] == event_type])
                conversion_event_counts[event_type] = count
                features[f'{event_type}_count'] = count
                features[f'{event_type}_ratio'] = count / total_events if total_events > 0 else 0
                
            # 总转化事件数
            total_conversions = sum(conversion_event_counts.values())
            features['total_conversions'] = total_conversions
            features['conversion_ratio'] = total_conversions / total_events if total_events > 0 else 0
            
            # 转化深度（完成了多少种转化事件）
            features['conversion_depth'] = sum(1 for count in conversion_event_counts.values() if count > 0)
            
            # 购买相关特征
            purchase_events = user_events[user_events['event_name'] == 'purchase']
            features['purchase_frequency'] = len(purchase_events)
            
            # 如果有购买，计算购买间隔
            if len(purchase_events) > 1:
                purchase_times = purchase_events['event_datetime'].sort_values()
                intervals = purchase_times.diff().dt.total_seconds() / (24 * 3600)  # 转换为天
                features['avg_purchase_interval_days'] = intervals.mean()
            else:
                features['avg_purchase_interval_days'] = 0
                
            return features
            
        except Exception as e:
            logger.warning(f"提取转化特征失败: {e}")
            return {}
            
    def _extract_temporal_features(self, user_events: pd.DataFrame) -> Dict[str, float]:
        """
        提取时间特征
        
        Args:
            user_events: 用户事件数据
            
        Returns:
            时间特征字典
        """
        try:
            features = {}
            
            if user_events.empty or 'event_datetime' not in user_events.columns:
                return {}
                
            # 活动时间模式
            user_events['hour'] = user_events['event_datetime'].dt.hour
            user_events['day_of_week'] = user_events['event_datetime'].dt.dayofweek
            
            # 活跃时段分布
            hour_counts = user_events['hour'].value_counts()
            total_events = len(user_events)
            
            # 工作时间 vs 非工作时间
            work_hours = user_events[(user_events['hour'] >= 9) & (user_events['hour'] <= 17)]
            features['work_hours_ratio'] = len(work_hours) / total_events if total_events > 0 else 0
            
            # 工作日 vs 周末
            weekdays = user_events[user_events['day_of_week'] < 5]
            features['weekday_ratio'] = len(weekdays) / total_events if total_events > 0 else 0
            
            # 活动时间集中度
            if len(hour_counts) > 0:
                hour_probs = hour_counts / total_events
                features['time_concentration'] = -sum(p * np.log2(p) for p in hour_probs if p > 0)
            else:
                features['time_concentration'] = 0
                
            # 最活跃时段
            if len(hour_counts) > 0:
                features['most_active_hour'] = hour_counts.index[0]
            else:
                features['most_active_hour'] = 12  # 默认中午
                
            # 活动规律性（标准差）
            daily_counts = user_events.groupby(user_events['event_datetime'].dt.date).size()
            features['activity_regularity'] = 1 / (daily_counts.std() + 1) if len(daily_counts) > 1 else 1
            
            return features
            
        except Exception as e:
            logger.warning(f"提取时间特征失败: {e}")
            return {}
            
    def _calculate_avg_events_per_day(self, user_events: pd.DataFrame) -> float:
        """
        计算平均每日事件数
        
        Args:
            user_events: 用户事件数据
            
        Returns:
            平均每日事件数
        """
        try:
            if user_events.empty or 'event_datetime' not in user_events.columns:
                return 0
                
            active_dates = user_events['event_datetime'].dt.date.unique()
            return len(user_events) / len(active_dates) if len(active_dates) > 0 else 0
            
        except Exception as e:
            logger.warning(f"计算平均每日事件数失败: {e}")
            return 0
            
    def create_user_segments(self,
                           user_features: Optional[List[UserFeatures]] = None,
                           method: str = 'kmeans',
                           n_clusters: int = 5,
                           **kwargs) -> SegmentationResult:
        """
        创建用户分群
        
        Args:
            user_features: 用户特征列表
            method: 分群方法
            n_clusters: 聚类数量
            **kwargs: 其他参数
            
        Returns:
            分群结果
        """
        try:
            # 获取用户特征
            if user_features is None:
                user_features = self.extract_user_features()
                
            if not user_features:
                logger.warning("用户特征为空，无法进行分群")
                return SegmentationResult(
                    segments=[],
                    segmentation_method=method,
                    feature_importance={},
                    quality_metrics={},
                    segment_comparison=pd.DataFrame()
                )
                
            # 准备特征矩阵
            feature_matrix, feature_names, user_ids = self._prepare_feature_matrix(user_features)
            
            if feature_matrix.shape[0] == 0:
                logger.warning("特征矩阵为空，无法进行分群")
                return SegmentationResult(
                    segments=[],
                    segmentation_method=method,
                    feature_importance={},
                    quality_metrics={},
                    segment_comparison=pd.DataFrame()
                )
                
            # 执行分群
            if method not in self.segmentation_methods:
                raise ValueError(f"不支持的分群方法: {method}")
                
            cluster_labels = self.segmentation_methods[method](
                feature_matrix, n_clusters, **kwargs
            )
            
            # 构建分群结果
            segments = self._build_segments(
                user_features, cluster_labels, feature_matrix, feature_names
            )
            
            # 计算特征重要性
            feature_importance = self._calculate_feature_importance(
                feature_matrix, cluster_labels, feature_names
            )
            
            # 计算质量指标
            quality_metrics = self._calculate_quality_metrics(
                feature_matrix, cluster_labels
            )
            
            # 创建分群对比表
            segment_comparison = self._create_segment_comparison(segments, feature_names)
            
            result = SegmentationResult(
                segments=segments,
                segmentation_method=method,
                feature_importance=feature_importance,
                quality_metrics=quality_metrics,
                segment_comparison=segment_comparison
            )
            
            logger.info(f"使用{method}方法创建了{len(segments)}个用户分群")
            return result
            
        except Exception as e:
            logger.error(f"创建用户分群失败: {e}")
            raise
            
    def _prepare_feature_matrix(self, user_features: List[UserFeatures]) -> Tuple[np.ndarray, List[str], List[str]]:
        """
        准备特征矩阵
        
        Args:
            user_features: 用户特征列表
            
        Returns:
            (特征矩阵, 特征名称列表, 用户ID列表)
        """
        try:
            if not user_features:
                return np.array([]), [], []
                
            # 收集所有数值特征
            all_features = []
            feature_names = set()
            user_ids = []
            
            for user_feature in user_features:
                user_feature_dict = {}
                user_ids.append(user_feature.user_id)
                
                # 合并所有数值特征
                for feature_dict in [
                    user_feature.behavioral_features,
                    user_feature.engagement_features,
                    user_feature.conversion_features,
                    user_feature.temporal_features
                ]:
                    for key, value in feature_dict.items():
                        if isinstance(value, (int, float)) and not np.isnan(value):
                            user_feature_dict[key] = value
                            feature_names.add(key)
                            
                # 处理分类特征（编码为数值）
                demographic_features = user_feature.demographic_features
                for key, value in demographic_features.items():
                    if isinstance(value, str):
                        if key not in self.label_encoders:
                            self.label_encoders[key] = LabelEncoder()
                            
                        # 确保编码器已经拟合
                        try:
                            encoded_value = self.label_encoders[key].transform([value])[0]
                        except ValueError:
                            # 新的类别，需要重新拟合
                            all_values = [uf.demographic_features.get(key, 'unknown') for uf in user_features]
                            self.label_encoders[key].fit(all_values)
                            encoded_value = self.label_encoders[key].transform([value])[0]
                            
                        user_feature_dict[key] = encoded_value
                        feature_names.add(key)
                        
                all_features.append(user_feature_dict)
                
            # 转换为矩阵
            feature_names = sorted(list(feature_names))
            feature_matrix = []
            
            for user_feature_dict in all_features:
                feature_vector = []
                for feature_name in feature_names:
                    value = user_feature_dict.get(feature_name, 0)
                    feature_vector.append(value)
                feature_matrix.append(feature_vector)
                
            feature_matrix = np.array(feature_matrix)
            
            # 标准化特征
            if feature_matrix.shape[0] > 0:
                feature_matrix = self.scaler.fit_transform(feature_matrix)
                
            return feature_matrix, feature_names, user_ids
            
        except Exception as e:
            logger.warning(f"准备特征矩阵失败: {e}")
            return np.array([]), [], []      
      
    def _kmeans_clustering(self, feature_matrix: np.ndarray, n_clusters: int, **kwargs) -> np.ndarray:
        """
        K-means聚类
        
        Args:
            feature_matrix: 特征矩阵
            n_clusters: 聚类数量
            **kwargs: 其他参数
            
        Returns:
            聚类标签
        """
        try:
            if feature_matrix.shape[0] < n_clusters:
                logger.warning(f"样本数({feature_matrix.shape[0]})少于聚类数({n_clusters})，调整聚类数")
                n_clusters = max(1, feature_matrix.shape[0])
                
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10,
                **kwargs
            )
            
            cluster_labels = kmeans.fit_predict(feature_matrix)
            return cluster_labels
            
        except Exception as e:
            logger.warning(f"K-means聚类失败: {e}")
            # 返回默认分群（所有用户在一个群中）
            return np.zeros(feature_matrix.shape[0])
            
    def _dbscan_clustering(self, feature_matrix: np.ndarray, n_clusters: int, **kwargs) -> np.ndarray:
        """
        DBSCAN聚类
        
        Args:
            feature_matrix: 特征矩阵
            n_clusters: 聚类数量（DBSCAN中不直接使用）
            **kwargs: 其他参数
            
        Returns:
            聚类标签
        """
        try:
            eps = kwargs.get('eps', 0.5)
            min_samples = kwargs.get('min_samples', 5)
            
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            cluster_labels = dbscan.fit_predict(feature_matrix)
            
            # DBSCAN可能产生噪声点（标签为-1），将其归为单独的群
            unique_labels = np.unique(cluster_labels)
            if -1 in unique_labels:
                # 将噪声点重新标记
                noise_mask = cluster_labels == -1
                max_label = cluster_labels[~noise_mask].max() if np.any(~noise_mask) else -1
                cluster_labels[noise_mask] = max_label + 1
                
            return cluster_labels
            
        except Exception as e:
            logger.warning(f"DBSCAN聚类失败: {e}")
            return np.zeros(feature_matrix.shape[0])
            
    def _behavioral_segmentation(self, feature_matrix: np.ndarray, n_clusters: int, **kwargs) -> np.ndarray:
        """
        基于行为的分群
        
        Args:
            feature_matrix: 特征矩阵
            n_clusters: 聚类数量
            **kwargs: 其他参数
            
        Returns:
            聚类标签
        """
        try:
            # 使用K-means作为基础，但可以添加特定的行为分群逻辑
            return self._kmeans_clustering(feature_matrix, n_clusters, **kwargs)
            
        except Exception as e:
            logger.warning(f"行为分群失败: {e}")
            return np.zeros(feature_matrix.shape[0])
            
    def _value_based_segmentation(self, feature_matrix: np.ndarray, n_clusters: int, **kwargs) -> np.ndarray:
        """
        基于价值的分群
        
        Args:
            feature_matrix: 特征矩阵
            n_clusters: 聚类数量
            **kwargs: 其他参数
            
        Returns:
            聚类标签
        """
        try:
            # 基于RFM模型的价值分群
            # 这里简化为使用K-means，实际可以实现更复杂的价值分群逻辑
            return self._kmeans_clustering(feature_matrix, n_clusters, **kwargs)
            
        except Exception as e:
            logger.warning(f"价值分群失败: {e}")
            return np.zeros(feature_matrix.shape[0])
            
    def _engagement_segmentation(self, feature_matrix: np.ndarray, n_clusters: int, **kwargs) -> np.ndarray:
        """
        基于参与度的分群
        
        Args:
            feature_matrix: 特征矩阵
            n_clusters: 聚类数量
            **kwargs: 其他参数
            
        Returns:
            聚类标签
        """
        try:
            # 基于参与度特征的分群
            return self._kmeans_clustering(feature_matrix, n_clusters, **kwargs)
            
        except Exception as e:
            logger.warning(f"参与度分群失败: {e}")
            return np.zeros(feature_matrix.shape[0])
            
    def _build_segments(self,
                       user_features: List[UserFeatures],
                       cluster_labels: np.ndarray,
                       feature_matrix: np.ndarray,
                       feature_names: List[str]) -> List[UserSegment]:
        """
        构建分群对象
        
        Args:
            user_features: 用户特征列表
            cluster_labels: 聚类标签
            feature_matrix: 特征矩阵
            feature_names: 特征名称列表
            
        Returns:
            用户分群列表
        """
        try:
            segments = []
            unique_labels = np.unique(cluster_labels)
            
            for segment_id in unique_labels:
                # 获取该分群的用户
                segment_mask = cluster_labels == segment_id
                segment_user_features = [user_features[i] for i in range(len(user_features)) if segment_mask[i]]
                segment_feature_matrix = feature_matrix[segment_mask]
                
                # 计算分群特征均值
                avg_features = {}
                if len(segment_feature_matrix) > 0:
                    avg_feature_values = np.mean(segment_feature_matrix, axis=0)
                    for i, feature_name in enumerate(feature_names):
                        avg_features[feature_name] = float(avg_feature_values[i])
                        
                # 生成分群画像
                segment_profile = self._generate_segment_profile(segment_user_features)
                
                # 识别关键特征
                key_characteristics = self._identify_key_characteristics(
                    segment_feature_matrix, feature_matrix, feature_names
                )
                
                # 生成分群名称
                segment_name = self._generate_segment_name(segment_id, segment_profile, key_characteristics)
                
                segment = UserSegment(
                    segment_id=int(segment_id),
                    segment_name=segment_name,
                    user_count=len(segment_user_features),
                    user_ids=[uf.user_id for uf in segment_user_features],
                    segment_profile=segment_profile,
                    key_characteristics=key_characteristics,
                    avg_features=avg_features
                )
                
                segments.append(segment)
                
            return segments
            
        except Exception as e:
            logger.warning(f"构建分群对象失败: {e}")
            return []
            
    def _generate_segment_profile(self, segment_user_features: List[UserFeatures]) -> Dict[str, Any]:
        """
        生成分群画像
        
        Args:
            segment_user_features: 分群用户特征列表
            
        Returns:
            分群画像字典
        """
        try:
            if not segment_user_features:
                return {}
                
            profile = {}
            
            # 人口统计特征统计
            platforms = [uf.demographic_features.get('platform', 'unknown') for uf in segment_user_features]
            devices = [uf.demographic_features.get('device_category', 'unknown') for uf in segment_user_features]
            countries = [uf.demographic_features.get('geo_country', 'unknown') for uf in segment_user_features]
            
            profile['dominant_platform'] = max(set(platforms), key=platforms.count)
            profile['dominant_device'] = max(set(devices), key=devices.count)
            profile['dominant_country'] = max(set(countries), key=countries.count)
            
            # 行为特征统计
            total_events = [uf.behavioral_features.get('total_events', 0) for uf in segment_user_features]
            conversion_ratios = [uf.conversion_features.get('conversion_ratio', 0) for uf in segment_user_features]
            active_days = [uf.engagement_features.get('active_days', 0) for uf in segment_user_features]
            
            profile['avg_total_events'] = np.mean(total_events)
            profile['avg_conversion_ratio'] = np.mean(conversion_ratios)
            profile['avg_active_days'] = np.mean(active_days)
            
            # 参与度分级
            avg_engagement = np.mean([uf.engagement_features.get('activity_frequency', 0) for uf in segment_user_features])
            if avg_engagement > 0.7:
                profile['engagement_level'] = 'high'
            elif avg_engagement > 0.3:
                profile['engagement_level'] = 'medium'
            else:
                profile['engagement_level'] = 'low'
                
            # 价值分级
            avg_conversions = np.mean([uf.conversion_features.get('total_conversions', 0) for uf in segment_user_features])
            if avg_conversions > 5:
                profile['value_level'] = 'high'
            elif avg_conversions > 1:
                profile['value_level'] = 'medium'
            else:
                profile['value_level'] = 'low'
                
            return profile
            
        except Exception as e:
            logger.warning(f"生成分群画像失败: {e}")
            return {}
            
    def _identify_key_characteristics(self,
                                    segment_features: np.ndarray,
                                    all_features: np.ndarray,
                                    feature_names: List[str]) -> List[str]:
        """
        识别分群关键特征
        
        Args:
            segment_features: 分群特征矩阵
            all_features: 全体特征矩阵
            feature_names: 特征名称列表
            
        Returns:
            关键特征列表
        """
        try:
            if len(segment_features) == 0 or len(all_features) == 0:
                return []
                
            characteristics = []
            
            # 计算分群特征均值与全体均值的差异
            segment_means = np.mean(segment_features, axis=0)
            overall_means = np.mean(all_features, axis=0)
            
            # 找出差异最大的特征
            differences = np.abs(segment_means - overall_means)
            top_indices = np.argsort(differences)[-5:]  # 取前5个最显著的特征
            
            for idx in reversed(top_indices):
                if idx < len(feature_names):
                    feature_name = feature_names[idx]
                    segment_value = segment_means[idx]
                    overall_value = overall_means[idx]
                    
                    if segment_value > overall_value:
                        characteristics.append(f"高{feature_name}")
                    else:
                        characteristics.append(f"低{feature_name}")
                        
            return characteristics[:3]  # 返回前3个最重要的特征
            
        except Exception as e:
            logger.warning(f"识别关键特征失败: {e}")
            return []
            
    def _generate_segment_name(self,
                             segment_id: int,
                             segment_profile: Dict[str, Any],
                             key_characteristics: List[str]) -> str:
        """
        生成分群名称
        
        Args:
            segment_id: 分群ID
            segment_profile: 分群画像
            key_characteristics: 关键特征
            
        Returns:
            分群名称
        """
        try:
            # 基于分群特征生成有意义的名称
            engagement_level = segment_profile.get('engagement_level', 'unknown')
            value_level = segment_profile.get('value_level', 'unknown')
            
            # 预定义的分群名称模板
            name_templates = {
                ('high', 'high'): '高价值活跃用户',
                ('high', 'medium'): '高活跃中价值用户',
                ('high', 'low'): '高活跃低价值用户',
                ('medium', 'high'): '中活跃高价值用户',
                ('medium', 'medium'): '中等用户',
                ('medium', 'low'): '中活跃低价值用户',
                ('low', 'high'): '低活跃高价值用户',
                ('low', 'medium'): '低活跃中价值用户',
                ('low', 'low'): '低价值用户'
            }
            
            name = name_templates.get((engagement_level, value_level), f'用户群{segment_id}')
            
            # 如果有关键特征，可以进一步细化名称
            if key_characteristics:
                main_characteristic = key_characteristics[0]
                if '高' in main_characteristic:
                    name = name.replace('用户', f'{main_characteristic}用户')
                    
            return name
            
        except Exception as e:
            logger.warning(f"生成分群名称失败: {e}")
            return f'用户群{segment_id}'
            
    def _calculate_feature_importance(self,
                                    feature_matrix: np.ndarray,
                                    cluster_labels: np.ndarray,
                                    feature_names: List[str]) -> Dict[str, float]:
        """
        计算特征重要性
        
        Args:
            feature_matrix: 特征矩阵
            cluster_labels: 聚类标签
            feature_names: 特征名称列表
            
        Returns:
            特征重要性字典
        """
        try:
            if len(feature_matrix) == 0 or len(feature_names) == 0:
                return {}
                
            importance = {}
            
            # 使用方差分析计算特征重要性
            unique_labels = np.unique(cluster_labels)
            
            for i, feature_name in enumerate(feature_names):
                feature_values = feature_matrix[:, i]
                
                # 计算组间方差和组内方差
                overall_mean = np.mean(feature_values)
                between_group_var = 0
                within_group_var = 0
                
                for label in unique_labels:
                    group_mask = cluster_labels == label
                    group_values = feature_values[group_mask]
                    
                    if len(group_values) > 0:
                        group_mean = np.mean(group_values)
                        group_size = len(group_values)
                        
                        # 组间方差
                        between_group_var += group_size * (group_mean - overall_mean) ** 2
                        
                        # 组内方差
                        within_group_var += np.sum((group_values - group_mean) ** 2)
                        
                # F统计量作为重要性指标
                if within_group_var > 0:
                    f_stat = between_group_var / within_group_var
                    importance[feature_name] = f_stat
                else:
                    importance[feature_name] = 0
                    
            # 标准化重要性分数
            if importance:
                max_importance = max(importance.values())
                if max_importance > 0:
                    importance = {k: v / max_importance for k, v in importance.items()}
                    
            return importance
            
        except Exception as e:
            logger.warning(f"计算特征重要性失败: {e}")
            return {}
            
    def _calculate_quality_metrics(self,
                                 feature_matrix: np.ndarray,
                                 cluster_labels: np.ndarray) -> Dict[str, float]:
        """
        计算分群质量指标
        
        Args:
            feature_matrix: 特征矩阵
            cluster_labels: 聚类标签
            
        Returns:
            质量指标字典
        """
        try:
            metrics = {}
            
            if len(feature_matrix) < 2:
                return metrics
                
            # 轮廓系数
            try:
                if len(np.unique(cluster_labels)) > 1:
                    silhouette_avg = silhouette_score(feature_matrix, cluster_labels)
                    metrics['silhouette_score'] = silhouette_avg
                else:
                    metrics['silhouette_score'] = 0
            except Exception:
                metrics['silhouette_score'] = 0
                
            # 簇内平方和
            try:
                inertia = 0
                unique_labels = np.unique(cluster_labels)
                
                for label in unique_labels:
                    cluster_points = feature_matrix[cluster_labels == label]
                    if len(cluster_points) > 0:
                        cluster_center = np.mean(cluster_points, axis=0)
                        inertia += np.sum((cluster_points - cluster_center) ** 2)
                        
                metrics['inertia'] = inertia
            except Exception:
                metrics['inertia'] = 0
                
            # 分群数量
            metrics['n_clusters'] = len(np.unique(cluster_labels))
            
            # 分群大小分布的均匀性
            cluster_sizes = [np.sum(cluster_labels == label) for label in np.unique(cluster_labels)]
            if cluster_sizes:
                size_std = np.std(cluster_sizes)
                size_mean = np.mean(cluster_sizes)
                metrics['size_uniformity'] = 1 - (size_std / size_mean) if size_mean > 0 else 0
            else:
                metrics['size_uniformity'] = 0
                
            return metrics
            
        except Exception as e:
            logger.warning(f"计算质量指标失败: {e}")
            return {}
            
    def _create_segment_comparison(self,
                                 segments: List[UserSegment],
                                 feature_names: List[str]) -> pd.DataFrame:
        """
        创建分群对比表
        
        Args:
            segments: 用户分群列表
            feature_names: 特征名称列表
            
        Returns:
            分群对比DataFrame
        """
        try:
            if not segments:
                return pd.DataFrame()
                
            comparison_data = []
            
            for segment in segments:
                row = {
                    'segment_id': segment.segment_id,
                    'segment_name': segment.segment_name,
                    'user_count': segment.user_count,
                    'engagement_level': segment.segment_profile.get('engagement_level', 'unknown'),
                    'value_level': segment.segment_profile.get('value_level', 'unknown'),
                    'dominant_platform': segment.segment_profile.get('dominant_platform', 'unknown'),
                    'avg_total_events': segment.segment_profile.get('avg_total_events', 0),
                    'avg_conversion_ratio': segment.segment_profile.get('avg_conversion_ratio', 0),
                    'key_characteristics': ', '.join(segment.key_characteristics)
                }
                
                # 添加主要特征值
                for feature_name in feature_names[:10]:  # 只显示前10个特征
                    row[feature_name] = segment.avg_features.get(feature_name, 0)
                    
                comparison_data.append(row)
                
            return pd.DataFrame(comparison_data)
            
        except Exception as e:
            logger.warning(f"创建分群对比表失败: {e}")
            return pd.DataFrame()
            
    def analyze_segment_characteristics(self, segmentation_result: SegmentationResult) -> Dict[str, Any]:
        """
        分析分群特征
        
        Args:
            segmentation_result: 分群结果
            
        Returns:
            分群特征分析结果
        """
        try:
            analysis = {
                'segment_summary': {},
                'feature_analysis': {},
                'segment_insights': [],
                'recommendations': []
            }
            
            if not segmentation_result.segments:
                return analysis
                
            # 分群摘要
            total_users = sum(segment.user_count for segment in segmentation_result.segments)
            analysis['segment_summary'] = {
                'total_segments': len(segmentation_result.segments),
                'total_users': total_users,
                'avg_segment_size': total_users / len(segmentation_result.segments),
                'largest_segment_size': max(segment.user_count for segment in segmentation_result.segments),
                'smallest_segment_size': min(segment.user_count for segment in segmentation_result.segments)
            }
            
            # 特征分析
            if segmentation_result.feature_importance:
                top_features = sorted(
                    segmentation_result.feature_importance.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
                
                analysis['feature_analysis'] = {
                    'most_important_features': [f[0] for f in top_features],
                    'feature_importance_scores': dict(top_features)
                }
                
            # 分群洞察
            insights = []
            
            # 找出最大和最小的分群
            largest_segment = max(segmentation_result.segments, key=lambda s: s.user_count)
            smallest_segment = min(segmentation_result.segments, key=lambda s: s.user_count)
            
            insights.append(f"最大分群是'{largest_segment.segment_name}'，包含{largest_segment.user_count}个用户")
            insights.append(f"最小分群是'{smallest_segment.segment_name}'，包含{smallest_segment.user_count}个用户")
            
            # 分析价值分群
            high_value_segments = [s for s in segmentation_result.segments 
                                 if s.segment_profile.get('value_level') == 'high']
            if high_value_segments:
                high_value_users = sum(s.user_count for s in high_value_segments)
                insights.append(f"高价值用户分群包含{high_value_users}个用户，占总用户的{high_value_users/total_users*100:.1f}%")
                
            # 分析参与度分群
            high_engagement_segments = [s for s in segmentation_result.segments 
                                      if s.segment_profile.get('engagement_level') == 'high']
            if high_engagement_segments:
                high_engagement_users = sum(s.user_count for s in high_engagement_segments)
                insights.append(f"高参与度用户分群包含{high_engagement_users}个用户，占总用户的{high_engagement_users/total_users*100:.1f}%")
                
            analysis['segment_insights'] = insights
            
            # 生成建议
            recommendations = []
            
            # 基于分群质量的建议
            quality_metrics = segmentation_result.quality_metrics
            silhouette_score = quality_metrics.get('silhouette_score', 0)
            
            if silhouette_score < 0.3:
                recommendations.append("分群质量较低，建议调整分群参数或特征选择")
            elif silhouette_score > 0.7:
                recommendations.append("分群质量良好，可以基于此进行精准营销")
                
            # 基于分群分布的建议
            size_uniformity = quality_metrics.get('size_uniformity', 0)
            if size_uniformity < 0.5:
                recommendations.append("分群大小不均匀，建议重新调整分群数量")
                
            # 基于高价值用户的建议
            if high_value_segments:
                recommendations.append("重点关注高价值用户分群，制定专门的保留策略")
                
            analysis['recommendations'] = recommendations
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析分群特征失败: {e}")
            return {}
            
    def segment_users(self, events: pd.DataFrame) -> Dict[str, Any]:
        """
        执行用户分群分析（集成管理器接口）
        
        Args:
            events: 事件数据DataFrame
            
        Returns:
            用户分群结果字典
        """
        try:
            if events.empty:
                return {
                    'status': 'error',
                    'message': '事件数据为空',
                    'insights': [],
                    'recommendations': []
                }
            
            # 提取用户特征
            user_features = self.extract_user_features(events)
            
            if not user_features:
                return {
                    'status': 'error',
                    'message': '无法提取用户特征',
                    'insights': [],
                    'recommendations': []
                }
            
            # 执行用户分群（使用KMeans方法）
            segmentation_result = self.create_user_segments(
                user_features=user_features,
                method='kmeans',
                n_clusters=min(5, max(3, len(user_features) // 10))
            )
            
            # 生成洞察和建议
            insights = []
            recommendations = []
            
            if segmentation_result and segmentation_result.segments:
                segment_count = len(segmentation_result.segments)
                insights.append(f"识别出 {segment_count} 个用户分群")
                
                # 分析各分群特征
                for segment in segmentation_result.segments:
                    user_count = segment.user_count
                    segment_name = segment.segment_name
                    
                    insights.append(f"{segment_name}: {user_count} 个用户")
                    
                    # 基于分群大小给出建议
                    if user_count < len(user_features) * 0.05:  # 小于5%的用户
                        recommendations.append(f"{segment_name}用户群体较小，可考虑与其他群体合并或制定精准营销策略")
                    elif user_count > len(user_features) * 0.4:  # 超过40%的用户
                        recommendations.append(f"{segment_name}用户群体较大，建议进一步细分以提供更精准的服务")
                
                # 分析分群质量
                if hasattr(segmentation_result, 'quality_metrics'):
                    silhouette_score = segmentation_result.quality_metrics.get('silhouette_score', 0)
                    if silhouette_score > 0.5:
                        insights.append("分群质量良好，用户群体区分明显")
                        recommendations.append("可以基于当前分群制定差异化的用户策略")
                    elif silhouette_score < 0.3:
                        insights.append("分群质量一般，用户群体重叠较多")
                        recommendations.append("建议调整分群参数或尝试其他分群方法")
                
                # 识别高价值用户群
                high_value_segments = []
                for segment in segmentation_result.segments:
                    avg_features = segment.avg_features
                    if (avg_features.get('total_conversions', 0) > 1 or 
                        avg_features.get('total_events', 0) > 50):
                        high_value_segments.append(segment.segment_name)
                
                if high_value_segments:
                    insights.append(f"高价值用户群: {', '.join(high_value_segments)}")
                    recommendations.append("重点关注高价值用户群的需求，提供优质服务以提升留存")
            
            # 特征重要性分析
            if user_features:
                sample_features = user_features[0].behavioral_features
                important_features = sorted(sample_features.keys())[:3]
                insights.append(f"主要区分特征: {', '.join(important_features)}")
                recommendations.append("基于主要区分特征设计个性化的用户体验")
            
            return {
                'status': 'success',
                'analysis_type': 'user_segmentation',
                'data_size': len(events),
                'unique_users': events['user_pseudo_id'].nunique() if 'user_pseudo_id' in events.columns else 0,
                'insights': insights,
                'recommendations': recommendations,
                'detailed_results': {
                    'segmentation_result': segmentation_result,
                    'segment_count': len(segmentation_result.segments) if segmentation_result else 0,
                    'user_features_count': len(user_features)
                },
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"用户分群分析执行失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'insights': [],
                'recommendations': []
            }
            
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        获取分析摘要
        
        Returns:
            分析摘要字典
        """
        try:
            if self.storage_manager is None:
                return {"error": "存储管理器未初始化"}
                
            events = self.storage_manager.get_data('events')
            users = self.storage_manager.get_data('users')
            
            if events.empty:
                return {"error": "无事件数据"}
                
            # 基础统计
            total_events = len(events)
            unique_users = events['user_pseudo_id'].nunique()
            unique_event_types = events['event_name'].nunique()
            
            # 时间范围
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                    
            if 'event_datetime' in events.columns:
                date_range = {
                    'start': events['event_datetime'].min().strftime('%Y-%m-%d'),
                    'end': events['event_datetime'].max().strftime('%Y-%m-%d')
                }
            else:
                date_range = {'start': 'N/A', 'end': 'N/A'}
                
            # 可用的分群方法
            available_methods = list(self.segmentation_methods.keys())
            
            # 特征类型统计
            feature_types = {
                'behavioral_features': ['total_events', 'unique_event_types', 'behavior_diversity'],
                'demographic_features': ['platform', 'device_category', 'geo_country'],
                'engagement_features': ['active_days', 'activity_frequency', 'recency_score'],
                'conversion_features': ['total_conversions', 'conversion_ratio', 'conversion_depth'],
                'temporal_features': ['work_hours_ratio', 'weekday_ratio', 'time_concentration']
            }
            
            return {
                'total_events': total_events,
                'unique_users': unique_users,
                'unique_event_types': unique_event_types,
                'total_user_records': len(users) if not users.empty else 0,
                'date_range': date_range,
                'available_methods': available_methods,
                'feature_types': feature_types,
                'recommended_cluster_range': [3, min(10, max(3, unique_users // 20))],
                'analysis_capabilities': [
                    'user_feature_extraction',
                    'kmeans_clustering',
                    'dbscan_clustering',
                    'behavioral_segmentation',
                    'value_based_segmentation',
                    'engagement_segmentation',
                    'segment_profile_generation',
                    'feature_importance_analysis'
                ]
            }
            
        except Exception as e:
            logger.error(f"获取分析摘要失败: {e}")
            return {"error": str(e)}