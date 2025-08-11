"""
留存分析智能体模块

该模块实现RetentionAnalysisAgent类，负责用户留存分析和队列分析。
智能体集成了留存分析引擎，提供留存率计算、队列分析和流失预测功能。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

from engines.retention_analysis_engine import RetentionAnalysisEngine, RetentionAnalysisResult
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


class CohortAnalysisTool(BaseTool):
    """队列分析工具"""
    
    name: str = "cohort_analysis"
    description: str = "执行用户队列分析，计算不同时间段的用户留存率"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', RetentionAnalysisEngine(storage_manager))
        
    def _run(self, analysis_type: str = 'weekly', periods: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        执行队列分析
        
        Args:
            analysis_type: 分析类型 ('daily', 'weekly', 'monthly')
            periods: 留存周期列表
            
        Returns:
            队列分析结果
        """
        try:
            if periods is None:
                periods = [1, 7, 14, 30]
                
            result = self.engine.analyze_cohort_retention(
                analysis_type=analysis_type,
                retention_periods=periods
            )
            
            return {
                'success': True,
                'analysis_type': result.analysis_type,
                'cohort_count': len(result.cohorts),
                'overall_retention_rates': result.overall_retention_rates,
                'summary_stats': result.summary_stats,
                'retention_matrix_shape': result.retention_matrix.shape if result.retention_matrix is not None else None
            }
            
        except Exception as e:
            logger.error(f"队列分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis_type': analysis_type
            }


class RetentionRateCalculationTool(BaseTool):
    """留存率计算工具"""
    
    name: str = "retention_rate_calculation"
    description: str = "计算指定时间段的用户留存率"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', RetentionAnalysisEngine(storage_manager))
        
    def _run(self, start_date: str, end_date: str, retention_days: int = 7) -> Dict[str, Any]:
        """
        计算留存率
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            retention_days: 留存天数
            
        Returns:
            留存率计算结果
        """
        try:
            result = self.engine.calculate_retention_rate(
                start_date=start_date,
                end_date=end_date,
                retention_days=retention_days
            )
            
            return {
                'success': True,
                'retention_rate': result,
                'start_date': start_date,
                'end_date': end_date,
                'retention_days': retention_days
            }
            
        except Exception as e:
            logger.error(f"留存率计算失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'retention_days': retention_days
            }


class UserLifecycleAnalysisTool(BaseTool):
    """用户生命周期分析工具"""
    
    name: str = "user_lifecycle_analysis"
    description: str = "分析用户生命周期，包括新用户、活跃用户、流失用户等"
    
    def __init__(self, storage_manager: DataStorageManager = None):
        super().__init__()
                # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'engine', RetentionAnalysisEngine(storage_manager))
        
    def _run(self, analysis_period: int = 30) -> Dict[str, Any]:
        """
        执行用户生命周期分析
        
        Args:
            analysis_period: 分析周期（天）
            
        Returns:
            用户生命周期分析结果
        """
        try:
            result = self.engine.analyze_user_lifecycle(analysis_period)
            
            return {
                'success': True,
                'analysis_period': analysis_period,
                'lifecycle_stats': result,
                'total_users': sum(result.values()) if isinstance(result, dict) else 0
            }
            
        except Exception as e:
            logger.error(f"用户生命周期分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis_period': analysis_period
            }


class RetentionAnalysisAgent:
    """留存分析智能体"""
    
    def __init__(self, storage_manager: DataStorageManager = None):
        """
        初始化留存分析智能体
        
        Args:
            storage_manager: 数据存储管理器
        """
        self.storage_manager = storage_manager
        self.engine = RetentionAnalysisEngine(storage_manager)
        
        # 初始化工具
        self.cohort_tool = CohortAnalysisTool(storage_manager)
        self.retention_rate_tool = RetentionRateCalculationTool(storage_manager)
        self.lifecycle_tool = UserLifecycleAnalysisTool(storage_manager)
        
        # 如果CrewAI可用，创建CrewAI智能体
        if CREWAI_AVAILABLE:
            self._create_crewai_agent()
        
        logger.info("留存分析智能体初始化完成")
    
    def _create_crewai_agent(self):
        """创建CrewAI智能体"""
        try:
            self.agent = Agent(
                role="留存分析专家",
                goal="分析用户留存模式，识别流失风险，提供留存优化建议",
                backstory="""
                你是一位经验丰富的用户留存分析专家，专门分析用户行为数据来理解用户留存模式。
                你擅长队列分析、留存率计算和用户生命周期分析，能够识别影响用户留存的关键因素。
                你的分析帮助产品团队制定有效的用户留存策略。
                """,
                tools=[self.cohort_tool, self.retention_rate_tool, self.lifecycle_tool],
                llm=get_llm(),
                verbose=True,
                allow_delegation=False
            )
        except Exception as e:
            logger.warning(f"CrewAI智能体创建失败: {e}")
            self.agent = None
    
    def analyze_cohort_retention(self, analysis_type: str = 'weekly', periods: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        执行队列留存分析
        
        Args:
            analysis_type: 分析类型 ('daily', 'weekly', 'monthly')
            periods: 留存周期列表
            
        Returns:
            队列留存分析结果
        """
        logger.info(f"开始执行队列留存分析: {analysis_type}")
        
        try:
            if periods is None:
                periods = [1, 7, 14, 30]
            
            # 使用引擎执行分析
            result = self.engine.analyze_cohort_retention(
                analysis_type=analysis_type,
                retention_periods=periods
            )
            
            # 构建返回结果
            analysis_result = {
                'success': True,
                'analysis_type': result.analysis_type,
                'cohort_count': len(result.cohorts),
                'overall_retention_rates': result.overall_retention_rates,
                'summary_stats': result.summary_stats,
                'cohorts': [
                    {
                        'cohort_period': cohort.cohort_period,
                        'cohort_size': cohort.cohort_size,
                        'first_activity_date': cohort.first_activity_date.isoformat() if cohort.first_activity_date else None,
                        'retention_rates': cohort.retention_rates,
                        'retention_counts': cohort.retention_counts
                    }
                    for cohort in result.cohorts
                ],
                'retention_matrix': result.retention_matrix.to_dict() if result.retention_matrix is not None else None
            }
            
            logger.info(f"队列留存分析完成，发现 {len(result.cohorts)} 个队列")
            return analysis_result
            
        except Exception as e:
            logger.error(f"队列留存分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis_type': analysis_type
            }
    
    def calculate_retention_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        计算留存指标
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            留存指标计算结果
        """
        logger.info(f"计算留存指标: {start_date} 到 {end_date}")
        
        try:
            # 计算不同周期的留存率
            retention_periods = [1, 7, 14, 30]
            retention_metrics = {}
            
            for period in retention_periods:
                rate = self.engine.calculate_retention_rate(
                    start_date=start_date,
                    end_date=end_date,
                    retention_days=period
                )
                retention_metrics[f'day_{period}_retention'] = rate
            
            return {
                'success': True,
                'start_date': start_date,
                'end_date': end_date,
                'retention_metrics': retention_metrics
            }
            
        except Exception as e:
            logger.error(f"留存指标计算失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_user_lifecycle(self, analysis_period: int = 30) -> Dict[str, Any]:
        """
        分析用户生命周期
        
        Args:
            analysis_period: 分析周期（天）
            
        Returns:
            用户生命周期分析结果
        """
        logger.info(f"开始用户生命周期分析，周期: {analysis_period}天")
        
        try:
            result = self.engine.analyze_user_lifecycle(analysis_period)
            
            return {
                'success': True,
                'analysis_period': analysis_period,
                'lifecycle_distribution': result,
                'total_users': sum(result.values()) if isinstance(result, dict) else 0
            }
            
        except Exception as e:
            logger.error(f"用户生命周期分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def comprehensive_retention_analysis(self) -> Dict[str, Any]:
        """
        执行综合留存分析
        
        Returns:
            综合留存分析结果
        """
        logger.info("开始执行综合留存分析")
        
        try:
            results = {
                'success': True,
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'analyses': {}
            }
            
            # 1. 队列分析
            logger.info("执行队列分析...")
            cohort_result = self.analyze_cohort_retention('weekly', [1, 7, 14, 30])
            results['analyses']['cohort_analysis'] = cohort_result
            
            # 2. 用户生命周期分析
            logger.info("执行用户生命周期分析...")
            lifecycle_result = self.analyze_user_lifecycle(30)
            results['analyses']['lifecycle_analysis'] = lifecycle_result
            
            # 3. 留存指标计算
            logger.info("计算留存指标...")
            # 使用最近30天的数据
            end_date = pd.Timestamp.now().strftime('%Y-%m-%d')
            start_date = (pd.Timestamp.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
            metrics_result = self.calculate_retention_metrics(start_date, end_date)
            results['analyses']['retention_metrics'] = metrics_result
            
            # 4. 生成分析摘要
            results['summary'] = self._generate_analysis_summary(results['analyses'])
            
            logger.info("综合留存分析完成")
            return results
            
        except Exception as e:
            logger.error(f"综合留存分析失败: {str(e)}")
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
            'successful_analyses': sum(1 for result in analyses.values() if result.get('success', False)),
            'key_insights': []
        }
        
        try:
            # 从队列分析中提取关键洞察
            cohort_analysis = analyses.get('cohort_analysis', {})
            if cohort_analysis.get('success'):
                cohort_count = cohort_analysis.get('cohort_count', 0)
                overall_rates = cohort_analysis.get('overall_retention_rates', {})
                
                summary['key_insights'].append(f"分析了 {cohort_count} 个用户队列")
                
                if overall_rates:
                    day_7_rate = overall_rates.get(7, 0)
                    day_30_rate = overall_rates.get(30, 0)
                    summary['key_insights'].append(f"7天留存率: {day_7_rate:.2%}")
                    summary['key_insights'].append(f"30天留存率: {day_30_rate:.2%}")
            
            # 从生命周期分析中提取洞察
            lifecycle_analysis = analyses.get('lifecycle_analysis', {})
            if lifecycle_analysis.get('success'):
                total_users = lifecycle_analysis.get('total_users', 0)
                summary['key_insights'].append(f"分析了 {total_users} 个用户的生命周期")
            
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
            'agent_type': 'RetentionAnalysisAgent',
            'crewai_available': CREWAI_AVAILABLE,
            'crewai_agent_created': hasattr(self, 'agent') and self.agent is not None,
            'storage_manager_available': self.storage_manager is not None,
            'engine_available': self.engine is not None,
            'tools_count': 3,
            'tools': ['cohort_analysis', 'retention_rate_calculation', 'user_lifecycle_analysis']
        }


# 为了向后兼容，提供一个简单的工厂函数
def create_retention_analysis_agent(storage_manager: DataStorageManager = None) -> RetentionAnalysisAgent:
    """
    创建留存分析智能体实例
    
    Args:
        storage_manager: 数据存储管理器
        
    Returns:
        留存分析智能体实例
    """
    return RetentionAnalysisAgent(storage_manager)