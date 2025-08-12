"""
用户分群智能体模块

该模块实现UserSegmentationAgent类，负责用户分群和画像生成。
智能体集成了用户分群引擎，提供特征提取、聚类分析和群体画像生成功能。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from engines.user_segmentation_engine import UserSegmentationEngine, SegmentationResult
from tools.data_storage_manager import DataStorageManager

# Try to import CrewAI components, but handle import errors gracefully
try:
    from crewai import Agent
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field
    from config.crew_config import get_llm
    CREWAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI not available: {e}. Agent will work in standalone mode.")
    CREWAI_AVAILABLE = False
    
    # Create mock classes for compatibility
    class BaseTool:
        def __init__(self):
            self.name = ""
            self.description = ""
            
    class Agent:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)


class FeatureExtractionTool(BaseTool):
    """特征提取工具"""
    
    name: str = "feature_extraction"
    description: str = "从用户行为数据中提取分群特征"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', UserSegmentationEngine(storage_manager))
        
    def _run(self, feature_types: List[str] = None) -> Dict[str, Any]:
        """
        执行特征提取
        
        Args:
            feature_types: 特征类型列表 ['behavioral', 'demographic', 'engagement', 'conversion', 'temporal']
            
        Returns:
            特征提取结果
        """
        try:
            if feature_types is None:
                feature_types = ['behavioral', 'demographic', 'engagement']
                
            result = self.engine.extract_user_features(feature_types)
            
            return {
                'success': True,
                'feature_types': feature_types,
                'user_count': len(result),
                'feature_summary': self._summarize_features(result)
            }
            
        except Exception as e:
            logger.error(f"特征提取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'feature_types': feature_types or []
            }
    
    def _summarize_features(self, features: List[Any]) -> Dict[str, Any]:
        """总结特征信息"""
        if not features:
            return {}
        
        # 这里应该根据实际的特征数据结构来实现
        return {
            'total_features': len(features),
            'feature_dimensions': 'varies'  # 实际实现中应该计算特征维度
        }


class ClusteringAnalysisTool(BaseTool):
    """聚类分析工具"""
    
    name: str = "clustering_analysis"
    description: str = "执行用户聚类分析，生成用户分群"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', UserSegmentationEngine(storage_manager))
        
    def _run(self, n_clusters: int = 5, clustering_method: str = 'kmeans') -> Dict[str, Any]:
        """
        执行聚类分析
        
        Args:
            n_clusters: 聚类数量
            clustering_method: 聚类方法 ('kmeans', 'dbscan')
            
        Returns:
            聚类分析结果
        """
        try:
            result = self.engine.perform_clustering(
                n_clusters=n_clusters,
                method=clustering_method
            )
            
            return {
                'success': True,
                'clustering_method': clustering_method,
                'n_clusters': len(result.segments),
                'total_users_clustered': sum(segment.user_count for segment in result.segments),
                'silhouette_score': result.quality_metrics.get('silhouette_score', 0),
                'segments': [
                    {
                        'segment_id': segment.segment_id,
                        'segment_name': segment.segment_name,
                        'user_count': segment.user_count,
                        'key_characteristics': segment.key_characteristics
                    }
                    for segment in result.segments
                ]
            }
            
        except Exception as e:
            logger.error(f"聚类分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'clustering_method': clustering_method
            }


class SegmentProfilingTool(BaseTool):
    """分群画像工具"""
    
    name: str = "segment_profiling"
    description: str = "生成用户分群的详细画像和特征描述"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', UserSegmentationEngine(storage_manager))
        
    def _run(self, segment_id: int) -> Dict[str, Any]:
        """
        生成分群画像
        
        Args:
            segment_id: 分群ID
            
        Returns:
            分群画像结果
        """
        try:
            result = self.engine.generate_segment_profile(segment_id)
            
            return {
                'success': True,
                'segment_id': segment_id,
                'segment_profile': result
            }
            
        except Exception as e:
            logger.error(f"分群画像生成失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'segment_id': segment_id
            }


class UserSegmentationAgent:
    """用户分群智能体"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """
        初始化用户分群智能体
        
        Args:
            storage_manager: 数据存储管理器
        """
        self.storage_manager = storage_manager
        self.engine = UserSegmentationEngine(storage_manager)
        
        # 初始化工具
        self.feature_tool = FeatureExtractionTool(storage_manager)
        self.clustering_tool = ClusteringAnalysisTool(storage_manager)
        self.profiling_tool = SegmentProfilingTool(storage_manager)
        
        # 如果CrewAI可用，创建CrewAI智能体
        if CREWAI_AVAILABLE:
            self._create_crewai_agent()
        
        logger.info("用户分群智能体初始化完成")
    
    def _create_crewai_agent(self):
        """创建CrewAI智能体"""
        try:
            self.agent = Agent(
                role="用户分群专家",
                goal="分析用户行为特征，构建用户分群，生成用户画像",
                backstory="""
                你是一位经验丰富的用户分群专家，专门分析用户行为数据来识别不同的用户群体。
                你擅长特征工程、聚类分析和用户画像生成，能够为精准营销和个性化推荐提供数据支持。
                你的分析帮助业务团队更好地理解用户需求和行为模式。
                """,
                tools=[self.feature_tool, self.clustering_tool, self.profiling_tool],
                llm=get_llm(),
                verbose=True,
                allow_delegation=False
            )
        except Exception as e:
            logger.warning(f"CrewAI智能体创建失败: {e}")
            self.agent = None
    
    def extract_user_features(self, feature_types: List[str] = None) -> Dict[str, Any]:
        """
        提取用户特征
        
        Args:
            feature_types: 特征类型列表
            
        Returns:
            特征提取结果
        """
        logger.info(f"提取用户特征: {feature_types}")
        
        try:
            if feature_types is None:
                feature_types = ['behavioral', 'demographic', 'engagement']
            
            result = self.engine.extract_user_features(feature_types)
            
            return {
                'success': True,
                'feature_types': feature_types,
                'user_count': len(result),
                'features_extracted': True
            }
            
        except Exception as e:
            logger.error(f"特征提取失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def perform_clustering(self, n_clusters: int = 5, method: str = 'kmeans') -> Dict[str, Any]:
        """
        执行用户聚类
        
        Args:
            n_clusters: 聚类数量
            method: 聚类方法
            
        Returns:
            聚类结果
        """
        logger.info(f"执行用户聚类: {method}, 聚类数: {n_clusters}")
        
        try:
            result = self.engine.perform_clustering(
                n_clusters=n_clusters,
                method=method
            )
            
            return {
                'success': True,
                'clustering_method': method,
                'n_clusters': len(result.segments),
                'total_users_clustered': sum(segment.user_count for segment in result.segments),
                'quality_metrics': result.quality_metrics,
                'segments': [
                    {
                        'segment_id': segment.segment_id,
                        'segment_name': segment.segment_name,
                        'user_count': segment.user_count,
                        'key_characteristics': segment.key_characteristics,
                        'avg_features': segment.avg_features
                    }
                    for segment in result.segments
                ]
            }
            
        except Exception as e:
            logger.error(f"用户聚类失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def comprehensive_segmentation_analysis(self) -> Dict[str, Any]:
        """
        执行综合分群分析
        
        Returns:
            综合分群分析结果
        """
        logger.info("开始执行综合分群分析")
        
        try:
            results = {
                'success': True,
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'analyses': {}
            }
            
            # 1. 特征提取
            logger.info("执行特征提取...")
            feature_result = self.extract_user_features(['behavioral', 'demographic', 'engagement'])
            results['analyses']['feature_extraction'] = feature_result
            
            # 2. 聚类分析
            logger.info("执行聚类分析...")
            clustering_result = self.perform_clustering(method='kmeans', n_clusters=5)
            results['analyses']['clustering_analysis'] = clustering_result
            
            # 3. 生成分群画像
            logger.info("生成分群画像...")
            if clustering_result.get('success') and clustering_result.get('segments'):
                profiles = []
                for segment in clustering_result['segments'][:3]:  # 只为前3个分群生成画像
                    profile_result = self.profiling_tool._run(segment['segment_id'])
                    profiles.append(profile_result)
                results['analyses']['segment_profiling'] = profiles
            
            # 4. 生成分析摘要
            results['summary'] = self._generate_analysis_summary(results['analyses'])
            
            logger.info("综合分群分析完成")
            return results
            
        except Exception as e:
            logger.error(f"综合分群分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            }
    
    def _generate_analysis_summary(self, analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成分析摘要
        
        Args:
            analyses: 分析结果字典
            
        Returns:
            分析摘要
        """
        summary = {
            'total_analyses': len(analyses),
            'successful_analyses': sum(1 for result in analyses.values() if isinstance(result, dict) and result.get('success', False)),
            'key_insights': []
        }
        
        try:
            # 从特征提取中提取洞察
            feature_analysis = analyses.get('feature_extraction', {})
            if feature_analysis.get('success'):
                user_count = feature_analysis.get('user_count', 0)
                feature_types = feature_analysis.get('feature_types', [])
                summary['key_insights'].append(f"提取了 {user_count} 个用户的 {len(feature_types)} 类特征")
            
            # 从聚类分析中提取洞察
            clustering_analysis = analyses.get('clustering_analysis', {})
            if clustering_analysis.get('success'):
                n_clusters = clustering_analysis.get('n_clusters', 0)
                total_users = clustering_analysis.get('total_users_clustered', 0)
                quality_score = clustering_analysis.get('quality_metrics', {}).get('silhouette_score', 0)
                summary['key_insights'].append(f"将 {total_users} 个用户分为 {n_clusters} 个群体")
                if quality_score > 0:
                    summary['key_insights'].append(f"聚类质量得分: {quality_score:.3f}")
            
        except Exception as e:
            logger.warning(f"生成分析摘要时出错: {e}")
        
        return summary
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        获取智能体状态
        
        Returns:
            智能体状态信息
        """
        return {
            'agent_type': 'UserSegmentationAgent',
            'crewai_available': CREWAI_AVAILABLE,
            'crewai_agent_created': hasattr(self, 'agent') and self.agent is not None,
            'storage_manager_available': self.storage_manager is not None,
            'engine_available': self.engine is not None,
            'tools_count': 3,
            'tools': ['feature_extraction', 'clustering_analysis', 'segment_profiling']
        }


# 为了向后兼容，提供一个简单的工厂函数
def create_user_segmentation_agent(storage_manager: DataStorageManager = None) -> UserSegmentationAgent:
    """
    创建用户分群智能体实例
    
    Args:
        storage_manager: 数据存储管理器
        
    Returns:
        用户分群智能体实例
    """
    return UserSegmentationAgent(storage_manager)

from engines.user_segmentation_engine import UserSegmentationEngine, UserFeatures, UserSegment, SegmentationResult
from tools.data_storage_manager import DataStorageManager

# Try to import CrewAI components, but handle import errors gracefully
try:
    from crewai import Agent
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field
    from config.crew_config import get_llm
    CREWAI_AVAILABLE = True
except ImportError as e:
    logging.warning(f"CrewAI not available: {e}. Agent will work in standalone mode.")
    CREWAI_AVAILABLE = False
    
    # Create mock classes for compatibility
    class BaseTool:
        def __init__(self):
            self.name = ""
            self.description = ""
            
    class Agent:
        def __init__(self, **kwargs):
            pass

logger = logging.getLogger(__name__)


class FeatureExtractionTool(BaseTool):
    """特征提取工具"""
    
    name: str = "feature_extraction"
    description: str = "从用户行为数据中提取多维度特征，包括行为、人口统计、参与度、转化和时间特征"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', UserSegmentationEngine(storage_manager))
        
    def _run(self, include_behavioral: bool = True, include_demographic: bool = True, 
             include_engagement: bool = True, include_conversion: bool = True, 
             include_temporal: bool = True) -> Dict[str, Any]:
        """
        执行用户特征提取
        
        Args:
            include_behavioral: 是否包含行为特征
            include_demographic: 是否包含人口统计特征
            include_engagement: 是否包含参与度特征
            include_conversion: 是否包含转化特征
            include_temporal: 是否包含时间特征
            
        Returns:
            特征提取结果
        """
        try:
            logger.info("开始用户特征提取")
            
            # 提取用户特征
            user_features = self.engine.extract_user_features()
            
            if not user_features:
                return {
                    'status': 'error',
                    'error_message': '没有可用的用户数据进行特征提取',
                    'analysis_type': 'feature_extraction'
                }
            
            # 过滤特征类型
            filtered_features = []
            for user_feature in user_features:
                filtered_feature = UserFeatures(
                    user_id=user_feature.user_id,
                    behavioral_features=user_feature.behavioral_features if include_behavioral else {},
                    demographic_features=user_feature.demographic_features if include_demographic else {},
                    engagement_features=user_feature.engagement_features if include_engagement else {},
                    conversion_features=user_feature.conversion_features if include_conversion else {},
                    temporal_features=user_feature.temporal_features if include_temporal else {}
                )
                filtered_features.append(filtered_feature)
            
            # 生成特征统计
            feature_stats = self._generate_feature_statistics(filtered_features)
            
            # 转换为可序列化格式
            serialized_features = []
            for user_feature in filtered_features:
                serialized_features.append({
                    'user_id': user_feature.user_id,
                    'behavioral_features': user_feature.behavioral_features,
                    'demographic_features': user_feature.demographic_features,
                    'engagement_features': user_feature.engagement_features,
                    'conversion_features': user_feature.conversion_features,
                    'temporal_features': user_feature.temporal_features
                })
            
            result = {
                'status': 'success',
                'analysis_type': 'feature_extraction',
                'user_features': serialized_features,
                'feature_statistics': feature_stats,
                'insights': self._generate_feature_insights(feature_stats)
            }
            
            logger.info(f"特征提取完成，处理了{len(filtered_features)}个用户")
            return result
            
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'feature_extraction'
            }
    
    def _generate_feature_statistics(self, user_features: List[UserFeatures]) -> Dict[str, Any]:
        """生成特征统计信息"""
        if not user_features:
            return {}
        
        stats = {
            'total_users': len(user_features),
            'feature_categories': {
                'behavioral': len(user_features[0].behavioral_features),
                'demographic': len(user_features[0].demographic_features),
                'engagement': len(user_features[0].engagement_features),
                'conversion': len(user_features[0].conversion_features),
                'temporal': len(user_features[0].temporal_features)
            }
        }
        
        # 计算数值特征的统计信息
        numerical_features = {}
        for feature_type in ['behavioral_features', 'engagement_features', 'conversion_features', 'temporal_features']:
            for user_feature in user_features:
                features_dict = getattr(user_feature, feature_type)
                for key, value in features_dict.items():
                    if isinstance(value, (int, float)):
                        if key not in numerical_features:
                            numerical_features[key] = []
                        numerical_features[key].append(value)
        
        # 计算统计指标
        feature_stats = {}
        for feature_name, values in numerical_features.items():
            if values:
                feature_stats[feature_name] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'std': (sum((x - sum(values)/len(values))**2 for x in values) / len(values))**0.5 if len(values) > 1 else 0
                }
        
        stats['numerical_feature_stats'] = feature_stats
        return stats
    
    def _generate_feature_insights(self, stats: Dict[str, Any]) -> List[str]:
        """生成特征洞察"""
        insights = []
        
        if not stats:
            return ["特征数据不足，无法生成洞察"]
        
        total_users = stats.get('total_users', 0)
        insights.append(f"成功提取了{total_users}个用户的特征")
        
        feature_categories = stats.get('feature_categories', {})
        total_features = sum(feature_categories.values())
        insights.append(f"总共提取了{total_features}个特征维度")
        
        # 分析特征分布
        numerical_stats = stats.get('numerical_feature_stats', {})
        if numerical_stats:
            high_variance_features = [name for name, stat in numerical_stats.items() 
                                    if stat.get('std', 0) > stat.get('mean', 0)]
            if high_variance_features:
                insights.append(f"发现{len(high_variance_features)}个高方差特征，适合用于用户分群")
        
        return insights


class ClusteringAnalysisTool(BaseTool):
    """聚类分析工具"""
    
    name: str = "clustering_analysis"
    description: str = "使用多种聚类算法对用户进行分群，支持K-means、DBSCAN等方法"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', UserSegmentationEngine(storage_manager))
        
    def _run(self, method: str = 'kmeans', n_clusters: int = 5, 
             user_features: Optional[List[Dict]] = None, **kwargs) -> Dict[str, Any]:
        """
        执行聚类分析
        
        Args:
            method: 聚类方法 ('kmeans', 'dbscan', 'behavioral', 'value_based', 'engagement')
            n_clusters: 聚类数量
            user_features: 用户特征数据（可选）
            **kwargs: 其他聚类参数
            
        Returns:
            聚类分析结果
        """
        try:
            logger.info(f"开始聚类分析，方法: {method}, 聚类数: {n_clusters}")
            
            # 如果没有提供特征数据，则提取特征
            features_list = None
            if user_features is None:
                features_list = self.engine.extract_user_features()
            else:
                # 转换输入的特征数据
                features_list = []
                for feature_dict in user_features:
                    user_feature = UserFeatures(
                        user_id=feature_dict['user_id'],
                        behavioral_features=feature_dict.get('behavioral_features', {}),
                        demographic_features=feature_dict.get('demographic_features', {}),
                        engagement_features=feature_dict.get('engagement_features', {}),
                        conversion_features=feature_dict.get('conversion_features', {}),
                        temporal_features=feature_dict.get('temporal_features', {})
                    )
                    features_list.append(user_feature)
            
            if not features_list:
                return {
                    'status': 'error',
                    'error_message': '没有可用的用户特征数据进行聚类',
                    'analysis_type': 'clustering_analysis'
                }
            
            # 执行聚类
            segmentation_result = self.engine.create_user_segments(
                user_features=features_list,
                method=method,
                n_clusters=n_clusters,
                **kwargs
            )
            
            # 转换为可序列化格式
            serialized_segments = []
            for segment in segmentation_result.segments:
                serialized_segments.append({
                    'segment_id': segment.segment_id,
                    'segment_name': segment.segment_name,
                    'user_count': segment.user_count,
                    'user_ids': segment.user_ids,
                    'segment_profile': segment.segment_profile,
                    'key_characteristics': segment.key_characteristics,
                    'avg_features': segment.avg_features
                })
            
            result = {
                'status': 'success',
                'analysis_type': 'clustering_analysis',
                'segmentation_method': segmentation_result.segmentation_method,
                'segments': serialized_segments,
                'feature_importance': segmentation_result.feature_importance,
                'quality_metrics': segmentation_result.quality_metrics,
                'segment_comparison': segmentation_result.segment_comparison.to_dict() if not segmentation_result.segment_comparison.empty else {},
                'insights': self._generate_clustering_insights(segmentation_result)
            }
            
            logger.info(f"聚类分析完成，生成了{len(serialized_segments)}个用户分群")
            return result
            
        except Exception as e:
            logger.error(f"聚类分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'clustering_analysis'
            }
    
    def _generate_clustering_insights(self, result: SegmentationResult) -> List[str]:
        """生成聚类分析洞察"""
        insights = []
        
        if not result.segments:
            return ["聚类分析未能生成有效的用户分群"]
        
        # 基本统计
        total_users = sum(segment.user_count for segment in result.segments)
        insights.append(f"成功将{total_users}个用户分为{len(result.segments)}个群体")
        
        # 分群大小分析
        segment_sizes = [segment.user_count for segment in result.segments]
        largest_segment = max(result.segments, key=lambda x: x.user_count)
        smallest_segment = min(result.segments, key=lambda x: x.user_count)
        
        insights.append(f"最大分群'{largest_segment.segment_name}'包含{largest_segment.user_count}个用户")
        insights.append(f"最小分群'{smallest_segment.segment_name}'包含{smallest_segment.user_count}个用户")
        
        # 质量指标分析
        quality_metrics = result.quality_metrics
        if 'silhouette_score' in quality_metrics:
            silhouette = quality_metrics['silhouette_score']
            if silhouette > 0.5:
                insights.append(f"聚类质量良好(轮廓系数: {silhouette:.3f})")
            elif silhouette > 0.25:
                insights.append(f"聚类质量中等(轮廓系数: {silhouette:.3f})")
            else:
                insights.append(f"聚类质量较低(轮廓系数: {silhouette:.3f})，建议调整参数")
        
        # 特征重要性分析
        if result.feature_importance:
            top_features = sorted(result.feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
            feature_names = [f[0] for f in top_features]
            insights.append(f"最重要的分群特征: {', '.join(feature_names)}")
        
        return insights


class SegmentProfileTool(BaseTool):
    """分群画像工具"""
    
    name: str = "segment_profile"
    description: str = "为用户分群生成详细的群体画像和特征描述"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', UserSegmentationEngine(storage_manager))
        
    def _run(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成分群画像
        
        Args:
            segments: 分群数据列表
            
        Returns:
            分群画像结果
        """
        try:
            logger.info(f"开始生成{len(segments)}个分群的画像")
            
            segment_profiles = []
            
            for segment_data in segments:
                # 生成详细画像
                detailed_profile = self._generate_detailed_profile(segment_data)
                
                # 生成营销建议
                marketing_recommendations = self._generate_marketing_recommendations(segment_data)
                
                # 生成运营策略
                operation_strategies = self._generate_operation_strategies(segment_data)
                
                profile_result = {
                    'segment_id': segment_data['segment_id'],
                    'segment_name': segment_data['segment_name'],
                    'user_count': segment_data['user_count'],
                    'detailed_profile': detailed_profile,
                    'marketing_recommendations': marketing_recommendations,
                    'operation_strategies': operation_strategies,
                    'key_insights': self._generate_segment_insights(segment_data)
                }
                
                segment_profiles.append(profile_result)
            
            result = {
                'status': 'success',
                'analysis_type': 'segment_profile',
                'segment_profiles': segment_profiles,
                'summary': self._generate_profile_summary(segment_profiles)
            }
            
            logger.info("分群画像生成完成")
            return result
            
        except Exception as e:
            logger.error(f"分群画像生成失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'segment_profile'
            }
    
    def _generate_detailed_profile(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细的分群画像"""
        profile = segment_data.get('segment_profile', {})
        avg_features = segment_data.get('avg_features', {})
        
        detailed_profile = {
            'demographic_profile': {
                'primary_platform': profile.get('primary_platform', 'unknown'),
                'primary_device': profile.get('primary_device_category', 'unknown'),
                'primary_location': profile.get('primary_geo_country', 'unknown')
            },
            'behavioral_profile': {
                'avg_events_per_day': avg_features.get('avg_events_per_day', 0),
                'behavior_diversity': avg_features.get('behavior_diversity', 0),
                'most_common_events': profile.get('top_events', [])
            },
            'engagement_profile': {
                'active_days': avg_features.get('active_days', 0),
                'avg_session_duration': avg_features.get('avg_session_duration', 0),
                'recency_score': avg_features.get('recency_score', 0)
            },
            'conversion_profile': {
                'conversion_ratio': avg_features.get('conversion_ratio', 0),
                'purchase_frequency': avg_features.get('purchase_frequency', 0),
                'conversion_depth': avg_features.get('conversion_depth', 0)
            }
        }
        
        return detailed_profile
    
    def _generate_marketing_recommendations(self, segment_data: Dict[str, Any]) -> List[str]:
        """生成营销建议"""
        recommendations = []
        avg_features = segment_data.get('avg_features', {})
        
        # 基于参与度的建议
        recency_score = avg_features.get('recency_score', 0)
        if recency_score > 0.8:
            recommendations.append("高活跃用户群体，适合推广新功能和高价值产品")
        elif recency_score > 0.5:
            recommendations.append("中等活跃用户，可通过个性化内容提升参与度")
        else:
            recommendations.append("低活跃用户，需要召回营销策略重新激活")
        
        # 基于转化的建议
        conversion_ratio = avg_features.get('conversion_ratio', 0)
        if conversion_ratio > 0.3:
            recommendations.append("高转化用户群体，适合交叉销售和升级营销")
        elif conversion_ratio > 0.1:
            recommendations.append("中等转化用户，可通过优惠和促销提升转化")
        else:
            recommendations.append("低转化用户，需要教育营销和价值传递")
        
        return recommendations
    
    def _generate_operation_strategies(self, segment_data: Dict[str, Any]) -> List[str]:
        """生成运营策略"""
        strategies = []
        avg_features = segment_data.get('avg_features', {})
        profile = segment_data.get('segment_profile', {})
        
        # 基于设备类型的策略
        primary_device = profile.get('primary_device_category', 'unknown')
        if primary_device == 'mobile':
            strategies.append("移动端优先策略，优化移动体验和推送通知")
        elif primary_device == 'desktop':
            strategies.append("桌面端深度体验策略，提供丰富的功能和内容")
        
        # 基于行为多样性的策略
        behavior_diversity = avg_features.get('behavior_diversity', 0)
        if behavior_diversity > 3:
            strategies.append("多元化用户，提供个性化推荐和多样化内容")
        else:
            strategies.append("专注型用户，深化核心功能体验")
        
        # 基于活跃度的策略
        active_days = avg_features.get('active_days', 0)
        if active_days > 20:
            strategies.append("高频用户，建立忠诚度计划和VIP服务")
        elif active_days > 10:
            strategies.append("中频用户，通过定期互动维持活跃度")
        else:
            strategies.append("低频用户，设计简单易用的产品体验")
        
        return strategies
    
    def _generate_segment_insights(self, segment_data: Dict[str, Any]) -> List[str]:
        """生成分群洞察"""
        insights = []
        key_characteristics = segment_data.get('key_characteristics', [])
        
        # 添加关键特征洞察
        if key_characteristics:
            insights.append(f"该分群的显著特征: {', '.join(key_characteristics[:3])}")
        
        # 基于用户数量的洞察
        user_count = segment_data.get('user_count', 0)
        if user_count > 1000:
            insights.append("大规模用户群体，具有重要的商业价值")
        elif user_count > 100:
            insights.append("中等规模用户群体，适合精细化运营")
        else:
            insights.append("小规模用户群体，可作为特殊关注对象")
        
        return insights
    
    def _generate_profile_summary(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成画像总结"""
        total_users = sum(profile['user_count'] for profile in profiles)
        
        return {
            'total_segments': len(profiles),
            'total_users_profiled': total_users,
            'largest_segment': max(profiles, key=lambda x: x['user_count'])['segment_name'] if profiles else None,
            'avg_segment_size': total_users / len(profiles) if profiles else 0
        }


class UserSegmentationAgent:
    """用户分群智能体类"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """初始化用户分群智能体"""
        self.storage_manager = storage_manager
        self.tools = [
            FeatureExtractionTool(storage_manager),
            ClusteringAnalysisTool(storage_manager),
            SegmentProfileTool(storage_manager)
        ]
        
        if CREWAI_AVAILABLE:
            self.agent = Agent(
                role="用户研究专家",
                goal="基于行为特征进行用户分群，生成详细的用户画像和运营建议",
                backstory="""你是一位经验丰富的用户研究专家，专注于用户行为分析和分群。
                            你擅长从复杂的用户数据中提取有价值的特征，并使用先进的机器学习算法
                            对用户进行精准分群。你的分析帮助产品和运营团队更好地理解用户，
                            制定个性化的用户策略。""",
                tools=self.tools,
                llm=get_llm(),
                verbose=True,
                allow_delegation=False,
                max_iter=3
            )
        else:
            self.agent = Agent(
                role="用户研究专家",
                goal="基于行为特征进行用户分群，生成详细的用户画像和运营建议"
            )
    
    def extract_user_features(self, include_behavioral: bool = True, include_demographic: bool = True,
                            include_engagement: bool = True, include_conversion: bool = True,
                            include_temporal: bool = True) -> Dict[str, Any]:
        """
        提取用户特征
        
        Args:
            include_behavioral: 是否包含行为特征
            include_demographic: 是否包含人口统计特征
            include_engagement: 是否包含参与度特征
            include_conversion: 是否包含转化特征
            include_temporal: 是否包含时间特征
            
        Returns:
            特征提取结果
        """
        try:
            feature_tool = FeatureExtractionTool(self.storage_manager)
            return feature_tool._run(include_behavioral, include_demographic, 
                                   include_engagement, include_conversion, include_temporal)
        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'feature_extraction'
            }
    
    def perform_clustering(self, method: str = 'kmeans', n_clusters: int = 5,
                          user_features: Optional[List[Dict]] = None, **kwargs) -> Dict[str, Any]:
        """
        执行用户聚类分析
        
        Args:
            method: 聚类方法
            n_clusters: 聚类数量
            user_features: 用户特征数据
            **kwargs: 其他聚类参数
            
        Returns:
            聚类分析结果
        """
        try:
            clustering_tool = ClusteringAnalysisTool(self.storage_manager)
            return clustering_tool._run(method, n_clusters, user_features, **kwargs)
        except Exception as e:
            logger.error(f"聚类分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'clustering_analysis'
            }
    
    def generate_segment_profiles(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成分群画像
        
        Args:
            segments: 分群数据列表
            
        Returns:
            分群画像结果
        """
        try:
            profile_tool = SegmentProfileTool(self.storage_manager)
            return profile_tool._run(segments)
        except Exception as e:
            logger.error(f"分群画像生成失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'segment_profile'
            }
    
    def comprehensive_user_segmentation(self, method: str = 'kmeans', n_clusters: int = 5,
                                      **kwargs) -> Dict[str, Any]:
        """
        综合用户分群分析
        
        Args:
            method: 聚类方法
            n_clusters: 聚类数量
            **kwargs: 其他参数
            
        Returns:
            综合分群分析结果
        """
        try:
            logger.info("开始综合用户分群分析")
            
            # 1. 提取用户特征
            feature_result = self.extract_user_features()
            if feature_result.get('status') != 'success':
                return feature_result
            
            # 2. 执行聚类分析
            clustering_result = self.perform_clustering(
                method=method,
                n_clusters=n_clusters,
                user_features=feature_result.get('user_features'),
                **kwargs
            )
            if clustering_result.get('status') != 'success':
                return clustering_result
            
            # 3. 生成分群画像
            segments = clustering_result.get('segments', [])
            profile_result = self.generate_segment_profiles(segments)
            
            # 4. 汇总结果
            comprehensive_result = {
                'status': 'success',
                'analysis_type': 'comprehensive_user_segmentation',
                'feature_extraction': feature_result,
                'clustering_analysis': clustering_result,
                'segment_profiles': profile_result,
                'summary': self._generate_comprehensive_summary([
                    feature_result, clustering_result, profile_result
                ])
            }
            
            logger.info("综合用户分群分析完成")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"综合用户分群分析失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'analysis_type': 'comprehensive_user_segmentation'
            }
    
    def _generate_comprehensive_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成综合分析摘要"""
        successful_analyses = [r for r in analysis_results if r.get('status') == 'success']
        
        summary = {
            'total_analyses_performed': len(analysis_results),
            'successful_analyses': len(successful_analyses),
            'key_findings': []
        }
        
        # 提取关键发现
        for result in successful_analyses:
            insights = result.get('insights', [])
            if insights:
                summary['key_findings'].extend(insights[:2])
        
        return summary
    
    def get_agent(self):
        """获取CrewAI智能体实例"""
        return self.agent
    
    def get_tools(self) -> List:
        """获取智能体工具列表"""
        return self.tools