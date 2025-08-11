"""
用户分群智能体测试模块

测试UserSegmentationAgent类的各项功能，包括特征提取、聚类分析和画像生成。
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.user_segmentation_agent import (
    UserSegmentationAgent,
    FeatureExtractionTool,
    ClusteringAnalysisTool,
    SegmentProfileTool
)
from tools.data_storage_manager import DataStorageManager
from engines.user_segmentation_engine import UserFeatures


class TestFeatureExtractionTool:
    """特征提取工具测试类"""
    
    @pytest.fixture
    def mock_storage_manager(self):
        """创建模拟存储管理器"""
        storage_manager = Mock(spec=DataStorageManager)
        
        # 创建测试事件数据
        events_data = pd.DataFrame({
            'user_pseudo_id': ['user1', 'user1', 'user2', 'user2', 'user3'],
            'event_name': ['page_view', 'purchase', 'page_view', 'add_to_cart', 'login'],
            'event_timestamp': [1640995200000000, 1640995260000000, 1640995320000000, 1640995380000000, 1640995440000000],
            'platform': ['web', 'web', 'mobile', 'mobile', 'web'],
            'device': [
                {'category': 'desktop'},
                {'category': 'desktop'},
                {'category': 'mobile'},
                {'category': 'mobile'},
                {'category': 'desktop'}
            ],
            'geo': [
                {'country': 'US'},
                {'country': 'US'},
                {'country': 'CN'},
                {'country': 'CN'},
                {'country': 'US'}
            ]
        })
        
        # 添加时间列
        events_data['event_datetime'] = pd.to_datetime(events_data['event_timestamp'], unit='us')
        
        # 创建测试用户数据
        users_data = pd.DataFrame({
            'user_pseudo_id': ['user1', 'user2', 'user3'],
            'platform': ['web', 'mobile', 'web'],
            'device_category': ['desktop', 'mobile', 'desktop'],
            'geo_country': ['US', 'CN', 'US']
        })
        
        # 创建测试会话数据
        sessions_data = pd.DataFrame({
            'user_pseudo_id': ['user1', 'user2', 'user3'],
            'session_id': ['session1', 'session2', 'session3'],
            'duration_seconds': [300, 150, 450],
            'event_count': [2, 2, 1]
        })
        
        storage_manager.get_data.side_effect = lambda data_type: {
            'events': events_data,
            'users': users_data,
            'sessions': sessions_data
        }.get(data_type, pd.DataFrame())
        
        return storage_manager
    
    @pytest.fixture
    def feature_tool(self, mock_storage_manager):
        """创建特征提取工具实例"""
        return FeatureExtractionTool(mock_storage_manager)
    
    def test_feature_extraction_success(self, feature_tool):
        """测试成功的特征提取"""
        result = feature_tool._run()
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'feature_extraction'
        assert 'user_features' in result
        assert 'feature_statistics' in result
        assert 'insights' in result
        
        # 验证用户特征数据
        user_features = result['user_features']
        assert len(user_features) == 3  # 3个用户
        
        # 验证特征结构
        for user_feature in user_features:
            assert 'user_id' in user_feature
            assert 'behavioral_features' in user_feature
            assert 'demographic_features' in user_feature
            assert 'engagement_features' in user_feature
            assert 'conversion_features' in user_feature
            assert 'temporal_features' in user_feature
    
    def test_feature_extraction_with_filters(self, feature_tool):
        """测试带过滤器的特征提取"""
        result = feature_tool._run(
            include_behavioral=True,
            include_demographic=False,
            include_engagement=True,
            include_conversion=False,
            include_temporal=False
        )
        
        assert result['status'] == 'success'
        
        # 验证只包含指定的特征类型
        user_features = result['user_features']
        for user_feature in user_features:
            assert len(user_feature['behavioral_features']) > 0
            assert len(user_feature['demographic_features']) == 0
            assert len(user_feature['engagement_features']) > 0
            assert len(user_feature['conversion_features']) == 0
            assert len(user_feature['temporal_features']) == 0
    
    def test_feature_extraction_empty_data(self, mock_storage_manager):
        """测试空数据的特征提取"""
        # 设置空数据
        mock_storage_manager.get_data.return_value = pd.DataFrame()
        
        feature_tool = FeatureExtractionTool(mock_storage_manager)
        result = feature_tool._run()
        
        assert result['status'] == 'error'
        assert 'error_message' in result
    
    def test_feature_statistics_generation(self, feature_tool):
        """测试特征统计生成"""
        result = feature_tool._run()
        
        stats = result['feature_statistics']
        assert 'total_users' in stats
        assert 'feature_categories' in stats
        assert 'numerical_feature_stats' in stats
        
        # 验证特征类别统计
        categories = stats['feature_categories']
        assert 'behavioral' in categories
        assert 'demographic' in categories
        assert 'engagement' in categories
        assert 'conversion' in categories
        assert 'temporal' in categories


class TestClusteringAnalysisTool:
    """聚类分析工具测试类"""
    
    @pytest.fixture
    def mock_storage_manager(self):
        """创建模拟存储管理器"""
        return Mock(spec=DataStorageManager)
    
    @pytest.fixture
    def clustering_tool(self, mock_storage_manager):
        """创建聚类分析工具实例"""
        return ClusteringAnalysisTool(mock_storage_manager)
    
    @pytest.fixture
    def sample_user_features(self):
        """创建示例用户特征数据"""
        return [
            {
                'user_id': 'user1',
                'behavioral_features': {'total_events': 10, 'unique_event_types': 3},
                'demographic_features': {'platform': 'web', 'device_category': 'desktop'},
                'engagement_features': {'active_days': 5, 'recency_score': 0.8},
                'conversion_features': {'conversion_ratio': 0.2, 'purchase_frequency': 1},
                'temporal_features': {'work_hours_ratio': 0.6, 'weekday_ratio': 0.7}
            },
            {
                'user_id': 'user2',
                'behavioral_features': {'total_events': 20, 'unique_event_types': 5},
                'demographic_features': {'platform': 'mobile', 'device_category': 'mobile'},
                'engagement_features': {'active_days': 10, 'recency_score': 0.9},
                'conversion_features': {'conversion_ratio': 0.3, 'purchase_frequency': 2},
                'temporal_features': {'work_hours_ratio': 0.4, 'weekday_ratio': 0.8}
            },
            {
                'user_id': 'user3',
                'behavioral_features': {'total_events': 5, 'unique_event_types': 2},
                'demographic_features': {'platform': 'web', 'device_category': 'desktop'},
                'engagement_features': {'active_days': 2, 'recency_score': 0.3},
                'conversion_features': {'conversion_ratio': 0.1, 'purchase_frequency': 0},
                'temporal_features': {'work_hours_ratio': 0.8, 'weekday_ratio': 0.5}
            }
        ]
    
    def test_clustering_analysis_success(self, clustering_tool, sample_user_features):
        """测试成功的聚类分析"""
        result = clustering_tool._run(
            method='kmeans',
            n_clusters=2,
            user_features=sample_user_features
        )
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'clustering_analysis'
        assert result['segmentation_method'] == 'kmeans'
        assert 'segments' in result
        assert 'feature_importance' in result
        assert 'quality_metrics' in result
        assert 'insights' in result
        
        # 验证分群数据
        segments = result['segments']
        assert len(segments) <= 2  # 最多2个分群
        
        for segment in segments:
            assert 'segment_id' in segment
            assert 'segment_name' in segment
            assert 'user_count' in segment
            assert 'user_ids' in segment
            assert 'segment_profile' in segment
            assert 'key_characteristics' in segment
            assert 'avg_features' in segment
    
    def test_clustering_different_methods(self, clustering_tool, sample_user_features):
        """测试不同的聚类方法"""
        methods = ['kmeans', 'dbscan', 'behavioral', 'value_based', 'engagement']
        
        for method in methods:
            result = clustering_tool._run(
                method=method,
                n_clusters=2,
                user_features=sample_user_features
            )
            
            assert result['status'] == 'success'
            assert result['segmentation_method'] == method
    
    def test_clustering_without_features(self, clustering_tool):
        """测试没有特征数据的聚类分析"""
        with patch.object(clustering_tool.engine, 'extract_user_features', return_value=[]):
            result = clustering_tool._run(method='kmeans', n_clusters=2)
            
            assert result['status'] == 'error'
            assert 'error_message' in result
    
    def test_clustering_insights_generation(self, clustering_tool, sample_user_features):
        """测试聚类洞察生成"""
        result = clustering_tool._run(
            method='kmeans',
            n_clusters=2,
            user_features=sample_user_features
        )
        
        insights = result['insights']
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        # 验证洞察内容
        insights_text = ' '.join(insights)
        assert '用户' in insights_text or 'user' in insights_text.lower()


class TestSegmentProfileTool:
    """分群画像工具测试类"""
    
    @pytest.fixture
    def profile_tool(self):
        """创建分群画像工具实例"""
        return SegmentProfileTool()
    
    @pytest.fixture
    def sample_segments(self):
        """创建示例分群数据"""
        return [
            {
                'segment_id': 0,
                'segment_name': '高价值用户',
                'user_count': 100,
                'user_ids': ['user1', 'user2'],
                'segment_profile': {
                    'primary_platform': 'web',
                    'primary_device_category': 'desktop',
                    'primary_geo_country': 'US',
                    'top_events': ['purchase', 'page_view']
                },
                'key_characteristics': ['高转化率', '高参与度'],
                'avg_features': {
                    'conversion_ratio': 0.3,
                    'recency_score': 0.8,
                    'active_days': 15,
                    'avg_session_duration': 300,
                    'avg_events_per_day': 10,
                    'behavior_diversity': 3.5,
                    'purchase_frequency': 2
                }
            },
            {
                'segment_id': 1,
                'segment_name': '潜在用户',
                'user_count': 200,
                'user_ids': ['user3', 'user4'],
                'segment_profile': {
                    'primary_platform': 'mobile',
                    'primary_device_category': 'mobile',
                    'primary_geo_country': 'CN',
                    'top_events': ['page_view', 'login']
                },
                'key_characteristics': ['低转化率', '中等参与度'],
                'avg_features': {
                    'conversion_ratio': 0.1,
                    'recency_score': 0.5,
                    'active_days': 8,
                    'avg_session_duration': 150,
                    'avg_events_per_day': 5,
                    'behavior_diversity': 2.0,
                    'purchase_frequency': 0
                }
            }
        ]
    
    def test_segment_profile_generation(self, profile_tool, sample_segments):
        """测试分群画像生成"""
        result = profile_tool._run(sample_segments)
        
        assert result['status'] == 'success'
        assert result['analysis_type'] == 'segment_profile'
        assert 'segment_profiles' in result
        assert 'summary' in result
        
        # 验证分群画像数据
        profiles = result['segment_profiles']
        assert len(profiles) == 2
        
        for profile in profiles:
            assert 'segment_id' in profile
            assert 'segment_name' in profile
            assert 'user_count' in profile
            assert 'detailed_profile' in profile
            assert 'marketing_recommendations' in profile
            assert 'operation_strategies' in profile
            assert 'key_insights' in profile
    
    def test_detailed_profile_structure(self, profile_tool, sample_segments):
        """测试详细画像结构"""
        result = profile_tool._run(sample_segments)
        
        profiles = result['segment_profiles']
        detailed_profile = profiles[0]['detailed_profile']
        
        # 验证画像结构
        assert 'demographic_profile' in detailed_profile
        assert 'behavioral_profile' in detailed_profile
        assert 'engagement_profile' in detailed_profile
        assert 'conversion_profile' in detailed_profile
        
        # 验证人口统计画像
        demo_profile = detailed_profile['demographic_profile']
        assert 'primary_platform' in demo_profile
        assert 'primary_device' in demo_profile
        assert 'primary_location' in demo_profile
    
    def test_marketing_recommendations(self, profile_tool, sample_segments):
        """测试营销建议生成"""
        result = profile_tool._run(sample_segments)
        
        profiles = result['segment_profiles']
        
        for profile in profiles:
            recommendations = profile['marketing_recommendations']
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            
            # 验证建议内容
            recommendations_text = ' '.join(recommendations)
            assert any(keyword in recommendations_text for keyword in ['用户', '营销', '转化', '活跃'])
    
    def test_operation_strategies(self, profile_tool, sample_segments):
        """测试运营策略生成"""
        result = profile_tool._run(sample_segments)
        
        profiles = result['segment_profiles']
        
        for profile in profiles:
            strategies = profile['operation_strategies']
            assert isinstance(strategies, list)
            assert len(strategies) > 0
            
            # 验证策略内容
            strategies_text = ' '.join(strategies)
            assert any(keyword in strategies_text for keyword in ['策略', '用户', '体验', '功能'])
    
    def test_profile_summary(self, profile_tool, sample_segments):
        """测试画像总结"""
        result = profile_tool._run(sample_segments)
        
        summary = result['summary']
        assert 'total_segments' in summary
        assert 'total_users_profiled' in summary
        assert 'largest_segment' in summary
        assert 'avg_segment_size' in summary
        
        assert summary['total_segments'] == 2
        assert summary['total_users_profiled'] == 300
        assert summary['largest_segment'] == '潜在用户'
        assert summary['avg_segment_size'] == 150


class TestUserSegmentationAgent:
    """用户分群智能体测试类"""
    
    @pytest.fixture
    def mock_storage_manager(self):
        """创建模拟存储管理器"""
        return Mock(spec=DataStorageManager)
    
    @pytest.fixture
    def agent(self, mock_storage_manager):
        """创建用户分群智能体实例"""
        return UserSegmentationAgent(mock_storage_manager)
    
    def test_agent_initialization(self, agent):
        """测试智能体初始化"""
        assert agent.storage_manager is not None
        assert len(agent.tools) == 3
        assert agent.agent is not None
        
        # 验证工具类型
        tool_names = [tool.name for tool in agent.tools]
        assert 'feature_extraction' in tool_names
        assert 'clustering_analysis' in tool_names
        assert 'segment_profile' in tool_names
    
    def test_extract_user_features(self, agent):
        """测试特征提取方法"""
        with patch.object(agent.tools[0], '_run') as mock_run:
            mock_run.return_value = {
                'status': 'success',
                'analysis_type': 'feature_extraction',
                'user_features': [],
                'feature_statistics': {},
                'insights': []
            }
            
            result = agent.extract_user_features()
            
            assert result['status'] == 'success'
            mock_run.assert_called_once()
    
    def test_perform_clustering(self, agent):
        """测试聚类分析方法"""
        with patch.object(agent.tools[1], '_run') as mock_run:
            mock_run.return_value = {
                'status': 'success',
                'analysis_type': 'clustering_analysis',
                'segments': [],
                'insights': []
            }
            
            result = agent.perform_clustering(method='kmeans', n_clusters=3)
            
            assert result['status'] == 'success'
            mock_run.assert_called_once_with('kmeans', 3, None)
    
    def test_generate_segment_profiles(self, agent):
        """测试分群画像生成方法"""
        sample_segments = [
            {
                'segment_id': 0,
                'segment_name': '测试分群',
                'user_count': 50,
                'segment_profile': {},
                'avg_features': {}
            }
        ]
        
        with patch.object(agent.tools[2], '_run') as mock_run:
            mock_run.return_value = {
                'status': 'success',
                'analysis_type': 'segment_profile',
                'segment_profiles': [],
                'summary': {}
            }
            
            result = agent.generate_segment_profiles(sample_segments)
            
            assert result['status'] == 'success'
            mock_run.assert_called_once_with(sample_segments)
    
    def test_comprehensive_user_segmentation(self, agent):
        """测试综合用户分群分析"""
        # 模拟各个步骤的返回结果
        feature_result = {
            'status': 'success',
            'user_features': [{'user_id': 'user1'}],
            'insights': ['特征提取完成']
        }
        
        clustering_result = {
            'status': 'success',
            'segments': [{'segment_id': 0, 'user_count': 1}],
            'insights': ['聚类分析完成']
        }
        
        profile_result = {
            'status': 'success',
            'segment_profiles': [{'segment_id': 0}],
            'insights': ['画像生成完成']
        }
        
        with patch.object(agent, 'extract_user_features', return_value=feature_result), \
             patch.object(agent, 'perform_clustering', return_value=clustering_result), \
             patch.object(agent, 'generate_segment_profiles', return_value=profile_result):
            
            result = agent.comprehensive_user_segmentation(method='kmeans', n_clusters=3)
            
            assert result['status'] == 'success'
            assert result['analysis_type'] == 'comprehensive_user_segmentation'
            assert 'feature_extraction' in result
            assert 'clustering_analysis' in result
            assert 'segment_profiles' in result
            assert 'summary' in result
    
    def test_comprehensive_segmentation_failure_handling(self, agent):
        """测试综合分析的失败处理"""
        # 模拟特征提取失败
        feature_result = {
            'status': 'error',
            'error_message': '特征提取失败'
        }
        
        with patch.object(agent, 'extract_user_features', return_value=feature_result):
            result = agent.comprehensive_user_segmentation()
            
            assert result['status'] == 'error'
            assert result['error_message'] == '特征提取失败'
    
    def test_get_agent_and_tools(self, agent):
        """测试获取智能体和工具方法"""
        crewai_agent = agent.get_agent()
        tools = agent.get_tools()
        
        assert crewai_agent is not None
        assert isinstance(tools, list)
        assert len(tools) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])