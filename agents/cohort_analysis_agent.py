"""
队列分析智能体模块

该模块实现CohortAnalysisAgent类，负责用户队列留存分析和行为模式分析。
智能体集成了队列分析引擎，提供队列构建、留存率计算、生命周期分析和用户行为洞察功能。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta

from engines.cohort_analysis_engine import CohortAnalysisEngine
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


class CohortBuilderTool(BaseTool):
    """队列构建工具"""
    
    name: str = "cohort_builder"
    description: str = "构建用户队列，按注册时间、首次购买时间或其他关键事件进行分组"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', CohortAnalysisEngine(storage_manager))
    
    def _run(self, cohort_type: str = "registration", cohort_size: int = 30,
             cohort_metric: str = "days") -> Dict[str, Any]:
        """
        执行队列构建
        
        Args:
            cohort_type: 队列类型 ('registration', 'first_purchase', 'custom')
            cohort_size: 队列大小（天/周/月）
            cohort_metric: 队列度量单位 ('days', 'weeks', 'months')
            
        Returns:
            队列构建结果
        """
        try:
            result = self.engine.build_cohorts(
                cohort_type=cohort_type,
                cohort_size=cohort_size,
                cohort_metric=cohort_metric
            )
            
            return {
                'success': True,
                'cohort_type': result.cohort_type,
                'total_cohorts': result.total_cohorts,
                'total_users': result.total_users,
                'cohort_periods': result.cohort_periods,
                'cohorts': [
                    {
                        'cohort_name': cohort.cohort_name,
                        'cohort_date': cohort.cohort_date.isoformat(),
                        'user_count': cohort.user_count,
                        'cohort_period': cohort.cohort_period
                    }
                    for cohort in result.cohorts
                ]
            }
            
        except Exception as e:
            logger.error(f"队列构建失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'cohort_type': cohort_type
            }


class RetentionAnalysisTool(BaseTool):
    """留存率分析工具"""
    
    name: str = "retention_analysis"
    description: str = "计算队列留存率，包括日留存、周留存、月留存和自定义周期留存"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', CohortAnalysisEngine(storage_manager))
    
    def _run(self, retention_periods: List[int] = [1, 7, 14, 30],
             retention_type: str = "days") -> Dict[str, Any]:
        """
        执行留存率分析
        
        Args:
            retention_periods: 留存周期列表
            retention_type: 留存类型 ('days', 'weeks', 'months')
            
        Returns:
            留存率分析结果
        """
        try:
            result = self.engine.calculate_retention_rates(
                retention_periods=retention_periods,
                retention_type=retention_type
            )
            
            return {
                'success': True,
                'retention_matrix': result.retention_matrix.to_dict('index'),
                'avg_retention_rates': result.avg_retention_rates,
                'best_performing_cohort': result.best_performing_cohort,
                'worst_performing_cohort': result.worst_performing_cohort,
                'retention_insights': result.retention_insights
            }
            
        except Exception as e:
            logger.error(f"留存率分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class LifecycleAnalysisTool(BaseTool):
    """用户生命周期分析工具"""
    
    name: str = "lifecycle_analysis"
    description: str = "分析用户生命周期价值(LTV)和生命周期阶段分布"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', CohortAnalysisEngine(storage_manager))
    
    def _run(self, revenue_metric: str = "total_revenue", 
             lifecycle_stages: List[str] = None) -> Dict[str, Any]:
        """
        执行生命周期分析
        
        Args:
            revenue_metric: 收入指标 ('total_revenue', 'avg_revenue', 'revenue_per_user')
            lifecycle_stages: 生命周期阶段
            
        Returns:
            生命周期分析结果
        """
        try:
            if lifecycle_stages is None:
                lifecycle_stages = ["new", "active", "dormant", "churned"]
                
            result = self.engine.analyze_lifecycle(
                revenue_metric=revenue_metric,
                lifecycle_stages=lifecycle_stages
            )
            
            return {
                'success': True,
                'ltv_by_cohort': result.ltv_by_cohort,
                'lifecycle_distribution': result.lifecycle_distribution,
                'avg_ltv': result.avg_ltv,
                'cohort_performance': result.cohort_performance,
                'lifecycle_insights': result.lifecycle_insights
            }
            
        except Exception as e:
            logger.error(f"生命周期分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class ChurnPredictionTool(BaseTool):
    """流失预测分析工具"""
    
    name: str = "churn_prediction"
    description: str = "基于队列行为模式预测用户流失风险"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', CohortAnalysisEngine(storage_manager))
    
    def _run(self, prediction_horizon: int = 30, 
             risk_threshold: float = 0.7) -> Dict[str, Any]:
        """
        执行流失预测分析
        
        Args:
            prediction_horizon: 预测时间范围（天）
            risk_threshold: 流失风险阈值
            
        Returns:
            流失预测结果
        """
        try:
            result = self.engine.predict_churn_risk(
                prediction_horizon=prediction_horizon,
                risk_threshold=risk_threshold
            )
            
            return {
                'success': True,
                'churn_predictions': result.churn_predictions,
                'high_risk_cohorts': result.high_risk_cohorts,
                'churn_reasons': result.churn_reasons,
                'prevention_strategies': result.prevention_strategies,
                'prediction_accuracy': result.prediction_accuracy
            }
            
        except Exception as e:
            logger.error(f"流失预测分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class BehavioralPatternTool(BaseTool):
    """用户行为模式分析工具"""
    
    name: str = "behavioral_pattern_analysis"
    description: str = "分析不同队列用户的特定行为模式和偏好差异"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
        object.__setattr__(self, 'engine', CohortAnalysisEngine(storage_manager))
    
    def _run(self, behavior_events: List[str] = None, 
             comparison_metrics: List[str] = None) -> Dict[str, Any]:
        """
        执行行为模式分析
        
        Args:
            behavior_events: 要分析的行为事件列表
            comparison_metrics: 比较指标列表
            
        Returns:
            行为模式分析结果
        """
        try:
            if behavior_events is None:
                behavior_events = ["page_view", "purchase", "login", "share"]
            
            if comparison_metrics is None:
                comparison_metrics = ["frequency", "recency", "monetary"]
                
            result = self.engine.analyze_behavioral_patterns(
                behavior_events=behavior_events,
                comparison_metrics=comparison_metrics
            )
            
            return {
                'success': True,
                'behavioral_patterns': result.behavioral_patterns,
                'cohort_differences': result.cohort_differences,
                'segmentation_insights': result.segmentation_insights,
                'recommendations': result.recommendations
            }
            
        except Exception as e:
            logger.error(f"行为模式分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class CohortAnalysisAgent:
    """队列分析智能体"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """
        初始化队列分析智能体
        
        Args:
            storage_manager: 数据存储管理器
        """
        self.storage_manager = storage_manager
        self.engine = CohortAnalysisEngine(storage_manager)
        
        # 初始化工具
        self.cohort_builder = CohortBuilderTool(storage_manager)
        self.retention_analyzer = RetentionAnalysisTool(storage_manager)
        self.lifecycle_analyzer = LifecycleAnalysisTool(storage_manager)
        self.churn_predictor = ChurnPredictionTool(storage_manager)
        self.behavioral_analyzer = BehavioralPatternTool(storage_manager)
        
        # 创建CrewAI智能体
        if CREWAI_AVAILABLE:
            self._create_crewai_agent()
        
        logger.info("队列分析智能体初始化完成")
    
    def _create_crewai_agent(self):
        """创建CrewAI智能体"""
        try:
            self.agent = Agent(
                role="队列分析专家",
                goal="构建和分析用户队列，提供留存率洞察和用户生命周期价值分析",
                backstory="""
                你是一位资深的用户留存分析专家，拥有超过8年的队列分析和用户生命周期管理经验。
                你精通各种队列构建方法，能够准确识别用户留存的关键驱动因素，
                并提供数据驱动的留存优化策略。你的分析帮助众多产品显著提升用户留存率，
                平均留存率提升达到25%以上。你特别擅长SaaS、电商和内容平台的用户留存优化。
                """,
                tools=[
                    self.cohort_builder,
                    self.retention_analyzer,
                    self.lifecycle_analyzer,
                    self.churn_predictor,
                    self.behavioral_analyzer
                ],
                llm=get_llm(),
                verbose=True,
                allow_delegation=False,
                max_iter=5
            )
        except Exception as e:
            logger.warning(f"CrewAI智能体创建失败: {e}")
            self.agent = None
    
    def build_cohorts(self, cohort_type: str = "registration", cohort_size: int = 30,
                     cohort_metric: str = "days") -> Dict[str, Any]:
        """
        构建用户队列
        
        Args:
            cohort_type: 队列类型
            cohort_size: 队列大小
            cohort_metric: 队列度量单位
            
        Returns:
            队列构建结果
        """
        logger.info(f"开始构建队列，类型: {cohort_type}")
        
        try:
            result = self.engine.build_cohorts(
                cohort_type=cohort_type,
                cohort_size=cohort_size,
                cohort_metric=cohort_metric
            )
            
            return {
                'success': True,
                'cohort_type': result.cohort_type,
                'total_cohorts': result.total_cohorts,
                'total_users': result.total_users,
                'cohort_periods': result.cohort_periods,
                'cohorts': [
                    {
                        'cohort_name': cohort.cohort_name,
                        'cohort_date': cohort.cohort_date.isoformat(),
                        'user_count': cohort.user_count,
                        'cohort_period': cohort.cohort_period
                    }
                    for cohort in result.cohorts
                ]
            }
            
        except Exception as e:
            logger.error(f"队列构建失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'cohort_type': cohort_type
            }
    
    def analyze_retention(self, retention_periods: List[int] = [1, 7, 14, 30],
                         retention_type: str = "days") -> Dict[str, Any]:
        """
        分析用户留存率
        
        Args:
            retention_periods: 留存周期列表
            retention_type: 留存类型
            
        Returns:
            留存率分析结果
        """
        logger.info("开始分析用户留存率")
        
        try:
            result = self.engine.calculate_retention_rates(
                retention_periods=retention_periods,
                retention_type=retention_type
            )
            
            return {
                'success': True,
                'retention_matrix': result.retention_matrix.to_dict('index'),
                'avg_retention_rates': result.avg_retention_rates,
                'best_performing_cohort': result.best_performing_cohort,
                'worst_performing_cohort': result.worst_performing_cohort,
                'retention_insights': result.retention_insights
            }
            
        except Exception as e:
            logger.error(f"留存率分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_lifecycle(self, revenue_metric: str = "total_revenue",
                         lifecycle_stages: List[str] = None) -> Dict[str, Any]:
        """
        分析用户生命周期
        
        Args:
            revenue_metric: 收入指标
            lifecycle_stages: 生命周期阶段
            
        Returns:
            生命周期分析结果
        """
        logger.info("开始分析用户生命周期")
        
        try:
            if lifecycle_stages is None:
                lifecycle_stages = ["new", "active", "dormant", "churned"]
                
            result = self.engine.analyze_lifecycle(
                revenue_metric=revenue_metric,
                lifecycle_stages=lifecycle_stages
            )
            
            return {
                'success': True,
                'ltv_by_cohort': result.ltv_by_cohort,
                'lifecycle_distribution': result.lifecycle_distribution,
                'avg_ltv': result.avg_ltv,
                'cohort_performance': result.cohort_performance,
                'lifecycle_insights': result.lifecycle_insights
            }
            
        except Exception as e:
            logger.error(f"生命周期分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict_churn(self, prediction_horizon: int = 30, 
                     risk_threshold: float = 0.7) -> Dict[str, Any]:
        """
        预测用户流失风险
        
        Args:
            prediction_horizon: 预测时间范围
            risk_threshold: 流失风险阈值
            
        Returns:
            流失预测结果
        """
        logger.info("开始预测用户流失风险")
        
        try:
            result = self.engine.predict_churn_risk(
                prediction_horizon=prediction_horizon,
                risk_threshold=risk_threshold
            )
            
            return {
                'success': True,
                'churn_predictions': result.churn_predictions,
                'high_risk_cohorts': result.high_risk_cohorts,
                'churn_reasons': result.churn_reasons,
                'prevention_strategies': result.prevention_strategies,
                'prediction_accuracy': result.prediction_accuracy
            }
            
        except Exception as e:
            logger.error(f"流失预测分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_behavioral_patterns(self, behavior_events: List[str] = None,
                                  comparison_metrics: List[str] = None) -> Dict[str, Any]:
        """
        分析用户行为模式
        
        Args:
            behavior_events: 行为事件列表
            comparison_metrics: 比较指标列表
            
        Returns:
            行为模式分析结果
        """
        logger.info("开始分析用户行为模式")
        
        try:
            if behavior_events is None:
                behavior_events = ["page_view", "purchase", "login", "share"]
            
            if comparison_metrics is None:
                comparison_metrics = ["frequency", "recency", "monetary"]
                
            result = self.engine.analyze_behavioral_patterns(
                behavior_events=behavior_events,
                comparison_metrics=comparison_metrics
            )
            
            return {
                'success': True,
                'behavioral_patterns': result.behavioral_patterns,
                'cohort_differences': result.cohort_differences,
                'segmentation_insights': result.segmentation_insights,
                'recommendations': result.recommendations
            }
            
        except Exception as e:
            logger.error(f"行为模式分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def comprehensive_cohort_analysis(self, 
                                    cohort_type: str = "registration",
                                    include_predictions: bool = True) -> Dict[str, Any]:
        """
        执行综合队列分析
        
        Args:
            cohort_type: 队列类型
            include_predictions: 是否包含预测分析
            
        Returns:
            综合分析结果
        """
        logger.info("开始执行综合队列分析")
        
        try:
            # 构建队列
            cohort_result = self.build_cohorts(cohort_type=cohort_type)
            
            # 留存率分析
            retention_result = self.analyze_retention()
            
            # 生命周期分析
            lifecycle_result = self.analyze_lifecycle()
            
            # 行为模式分析
            behavioral_result = self.analyze_behavioral_patterns()
            
            # 流失预测（可选）
            prediction_result = None
            if include_predictions:
                prediction_result = self.predict_churn()
            
            # 汇总洞察
            insights = []
            recommendations = []
            
            if retention_result.get('success'):
                avg_retention = retention_result['avg_retention_rates'].get('day_30', 0)
                if avg_retention < 0.2:
                    insights.append("30日留存率偏低，需要优化用户体验")
                    recommendations.append("重点关注新用户引导和激活")
                elif avg_retention > 0.4:
                    insights.append("30日留存率表现良好")
            
            if lifecycle_result.get('success'):
                avg_ltv = lifecycle_result['avg_ltv']
                if avg_ltv > 100:
                    insights.append("用户生命周期价值较高")
                else:
                    insights.append("用户生命周期价值有提升空间")
            
            return {
                'success': True,
                'analysis_type': 'comprehensive_cohort_analysis',
                'cohort_analysis': cohort_result,
                'retention_analysis': retention_result,
                'lifecycle_analysis': lifecycle_result,
                'behavioral_analysis': behavioral_result,
                'prediction_analysis': prediction_result,
                'insights': insights,
                'recommendations': recommendations,
                'summary': {
                    'total_cohorts_analyzed': len(cohort_result.get('cohorts', [])),
                    'analysis_completed': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"综合队列分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        获取智能体状态
        
        Returns:
            智能体状态信息
        """
        return {
            'agent_type': 'CohortAnalysisAgent',
            'crewai_available': CREWAI_AVAILABLE,
            'crewai_agent_created': hasattr(self, 'agent') and self.agent is not None,
            'storage_manager_available': self.storage_manager is not None,
            'engine_available': self.engine is not None,
            'tools_count': 5,
            'tools': [
                'cohort_builder',
                'retention_analysis',
                'lifecycle_analysis',
                'churn_prediction',
                'behavioral_pattern_analysis'
            ],
            'supported_analyses': [
                'cohort_building',
                'retention_rate_calculation',
                'lifecycle_value_analysis',
                'churn_risk_prediction',
                'behavioral_pattern_analysis'
            ]
        }


# 为了向后兼容，提供一个简单的工厂函数
def create_cohort_analysis_agent(storage_manager: DataStorageManager = None) -> CohortAnalysisAgent:
    """
    创建队列分析智能体实例
    
    Args:
        storage_manager: 数据存储管理器
        
    Returns:
        队列分析智能体实例
    """
    return CohortAnalysisAgent(storage_manager)