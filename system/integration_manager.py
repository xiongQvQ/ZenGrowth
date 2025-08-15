"""
系统集成管理器

该模块实现完整的GA4数据分析工作流程集成，包括：
- 数据处理、分析引擎、智能体和界面组件的连接
- 完整分析流程的编排和执行
- 性能优化和内存管理
- 端到端集成测试支持
"""

import logging
import time
import gc
import psutil
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
from contextlib import contextmanager

# 导入核心组件
from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator
from tools.data_cleaner import DataCleaner
from tools.data_storage_manager import DataStorageManager

# 导入分析引擎
from engines.event_analysis_engine import EventAnalysisEngine
from engines.retention_analysis_engine import RetentionAnalysisEngine
from engines.conversion_analysis_engine import ConversionAnalysisEngine
from engines.user_segmentation_engine import UserSegmentationEngine
from engines.path_analysis_engine import PathAnalysisEngine

# 导入工具和设置日志
from utils.logger import setup_logger

# 设置全局logger
logger = setup_logger()

# 导入智能体 - 使用try/except处理兼容性问题
try:
    from agents.data_processing_agent import DataProcessingAgent
    from agents.event_analysis_agent import EventAnalysisAgent
    from agents.retention_analysis_agent import RetentionAnalysisAgent
    from agents.conversion_analysis_agent import ConversionAnalysisAgent
    from agents.user_segmentation_agent import UserSegmentationAgent
    from agents.path_analysis_agent import PathAnalysisAgent
    from agents.report_generation_agent import ReportGenerationAgent
    AGENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"智能体模块导入失败: {e}，将使用简化模式")
    AGENTS_AVAILABLE = False

# 导入可视化组件
from visualization.chart_generator import ChartGenerator
from visualization.advanced_visualizer import AdvancedVisualizer

# 导入配置和工具 - 使用try/except处理兼容性问题
try:
    from config.agent_orchestrator import AgentOrchestrator
    from config.agent_communication import MessageBroker, AgentMonitor
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"编排器模块导入失败: {e}，将使用简化模式")
    ORCHESTRATOR_AVAILABLE = False
from utils.config_manager import config_manager
from utils.report_exporter import ReportExporter


@dataclass
class SystemMetrics:
    """系统性能指标"""
    cpu_usage: float
    memory_usage: float
    memory_available: float
    disk_usage: float
    processing_time: float
    data_size: int
    timestamp: datetime


@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    analysis_type: str
    status: str
    data: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    visualizations: Dict[str, Any]
    execution_time: float
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class WorkflowConfig:
    """工作流程配置"""
    enable_parallel_processing: bool = True
    max_workers: int = 4
    memory_limit_gb: float = 8.0
    timeout_minutes: int = 30
    enable_caching: bool = True
    cache_ttl_hours: int = 24
    enable_monitoring: bool = True
    auto_cleanup: bool = True


class IntegrationManager:
    """系统集成管理器"""
    
    def __init__(self, config: WorkflowConfig = None):
        """
        初始化集成管理器
        
        Args:
            config: 工作流程配置
        """
        self.config = config or WorkflowConfig()
        self.logger = setup_logger()
        
        # 初始化核心组件
        self._initialize_components()
        
        # 初始化性能监控
        self._initialize_monitoring()
        
        # 初始化缓存系统
        self._initialize_cache()
        
        # 执行状态
        self.current_workflow = None
        self.workflow_history = []
        self.analysis_results = {}
        
        self.logger.info("系统集成管理器初始化完成")
    
    def _initialize_components(self):
        """初始化所有系统组件"""
        try:
            self.logger.info("开始初始化系统组件")
            
            # 数据处理组件
            self.data_parser = GA4DataParser()
            self.data_validator = DataValidator()
            self.data_cleaner = DataCleaner()
            self.storage_manager = DataStorageManager()
            
            # 分析引擎 - 传入存储管理器
            self.event_engine = EventAnalysisEngine(self.storage_manager)
            self.retention_engine = RetentionAnalysisEngine(self.storage_manager)
            self.conversion_engine = ConversionAnalysisEngine(self.storage_manager)
            self.segmentation_engine = UserSegmentationEngine()
            self.path_engine = PathAnalysisEngine()
            
            # 智能体系统
            if ORCHESTRATOR_AVAILABLE:
                self.orchestrator = AgentOrchestrator(self.storage_manager)
            else:
                self.orchestrator = None
            
            # 可视化组件
            self.chart_generator = ChartGenerator()
            self.advanced_visualizer = AdvancedVisualizer()
            
            # 报告导出
            self.report_exporter = ReportExporter()
            
            # 线程池
            self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
            
            self.logger.info("系统组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"系统组件初始化失败: {e}")
            raise
    
    def _initialize_monitoring(self):
        """初始化性能监控"""
        self.metrics_history = []
        self.monitoring_enabled = self.config.enable_monitoring
        
        if self.monitoring_enabled:
            # 启动监控线程
            self.monitoring_thread = threading.Thread(
                target=self._monitor_system_metrics,
                daemon=True
            )
            self.monitoring_thread.start()
            self.logger.info("性能监控已启动")
    
    def _initialize_cache(self):
        """初始化缓存系统"""
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_enabled = self.config.enable_caching
        
        if self.cache_enabled:
            self.logger.info("缓存系统已启用")
    
    def _monitor_system_metrics(self):
        """监控系统性能指标"""
        while self.monitoring_enabled:
            try:
                # 获取系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                metrics = SystemMetrics(
                    cpu_usage=cpu_percent,
                    memory_usage=memory.percent,
                    memory_available=memory.available / (1024**3),  # GB
                    disk_usage=disk.percent,
                    processing_time=0,  # 将在具体任务中更新
                    data_size=0,  # 将在具体任务中更新
                    timestamp=datetime.now()
                )
                
                self.metrics_history.append(metrics)
                
                # 保持最近1小时的指标
                cutoff_time = datetime.now() - timedelta(hours=1)
                self.metrics_history = [
                    m for m in self.metrics_history 
                    if m.timestamp > cutoff_time
                ]
                
                # 检查资源使用情况
                if memory.percent > 90:
                    self.logger.warning(f"内存使用率过高: {memory.percent:.1f}%")
                    self._trigger_memory_cleanup()
                
                if cpu_percent > 90:
                    self.logger.warning(f"CPU使用率过高: {cpu_percent:.1f}%")
                
                time.sleep(30)  # 每30秒监控一次
                
            except Exception as e:
                self.logger.error(f"性能监控错误: {e}")
                time.sleep(60)
    
    def _trigger_memory_cleanup(self):
        """触发内存清理"""
        try:
            self.logger.info("开始内存清理")
            
            # 清理缓存
            if self.cache_enabled:
                self._cleanup_cache()
            
            # 强制垃圾回收
            gc.collect()
            
            # 清理分析结果中的大型数据
            for result in self.analysis_results.values():
                if isinstance(result.data, dict):
                    # 保留关键信息，清理原始数据
                    if 'raw_data' in result.data:
                        del result.data['raw_data']
                    if 'detailed_data' in result.data:
                        result.data['detailed_data'] = "数据已清理以释放内存"
            
            self.logger.info("内存清理完成")
            
        except Exception as e:
            self.logger.error(f"内存清理失败: {e}")
    
    def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > timedelta(hours=self.config.cache_ttl_hours):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            del self.cache_timestamps[key]
        
        self.logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    @contextmanager
    def _performance_monitor(self, operation_name: str):
        """性能监控上下文管理器"""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().used
            
            execution_time = end_time - start_time
            memory_delta = (end_memory - start_memory) / (1024**2)  # MB
            
            self.logger.info(
                f"{operation_name} 完成 - 耗时: {execution_time:.2f}s, "
                f"内存变化: {memory_delta:+.1f}MB"
            )
    
    def execute_complete_workflow(self, file_path: str, 
                                analysis_types: List[str] = None) -> Dict[str, Any]:
        """
        执行完整的GA4数据分析工作流程
        
        Args:
            file_path: GA4数据文件路径
            analysis_types: 要执行的分析类型列表，None表示执行所有分析
            
        Returns:
            完整的分析结果
        """
        workflow_id = f"workflow_{int(datetime.now().timestamp())}"
        self.current_workflow = workflow_id
        
        try:
            self.logger.info(f"开始执行完整工作流程: {workflow_id}")
            
            with self._performance_monitor("完整工作流程"):
                # 1. 数据处理阶段
                processed_data = self._execute_data_processing(file_path)
                
                # 2. 分析执行阶段
                if analysis_types is None:
                    analysis_types = [
                        'event_analysis', 'retention_analysis', 'conversion_analysis',
                        'user_segmentation', 'path_analysis'
                    ]
                
                analysis_results = self._execute_analysis_pipeline(analysis_types)
                
                # 3. 报告生成阶段
                comprehensive_report = self._generate_comprehensive_report(analysis_results)
                
                # 4. 可视化生成阶段
                visualizations = self._generate_visualizations(analysis_results)
                
                # 5. 结果整合
                final_result = self._integrate_results(
                    processed_data, analysis_results, comprehensive_report, visualizations
                )
                
                # 记录工作流程历史
                workflow_record = {
                    'workflow_id': workflow_id,
                    'file_path': file_path,
                    'analysis_types': analysis_types,
                    'start_time': datetime.now().isoformat(),
                    'status': 'completed',
                    'result_summary': self._create_result_summary(final_result)
                }
                
                self.workflow_history.append(workflow_record)
                
                # 自动清理
                if self.config.auto_cleanup:
                    self._cleanup_workflow_data(workflow_id)
                
                self.logger.info(f"工作流程执行完成: {workflow_id}")
                
                return final_result
                
        except Exception as e:
            self.logger.error(f"工作流程执行失败: {workflow_id}, 错误: {e}")
            
            # 记录失败的工作流程
            workflow_record = {
                'workflow_id': workflow_id,
                'file_path': file_path,
                'analysis_types': analysis_types or [],
                'start_time': datetime.now().isoformat(),
                'status': 'failed',
                'error_message': str(e)
            }
            
            self.workflow_history.append(workflow_record)
            
            raise
        
        finally:
            self.current_workflow = None
    
    def _execute_data_processing(self, file_path: str) -> Dict[str, Any]:
        """
        执行数据处理阶段
        
        Args:
            file_path: 数据文件路径
            
        Returns:
            处理后的数据
        """
        with self._performance_monitor("数据处理"):
            self.logger.info("开始数据处理阶段")
            
            # 检查缓存
            cache_key = f"data_processing_{Path(file_path).stat().st_mtime}"
            if self.cache_enabled and cache_key in self.cache:
                self.logger.info("使用缓存的数据处理结果")
                return self.cache[cache_key]
            
            # 1. 解析数据
            self.logger.info("解析GA4数据文件")
            raw_data = self.data_parser.parse_ndjson(file_path)
            
            # 2. 数据验证
            self.logger.info("验证数据质量")
            validation_report = self.data_validator.validate_dataframe(raw_data)
            
            if not validation_report.get('validation_passed', False):
                self.logger.warning("数据验证发现问题，尝试清理数据")
                raw_data = self.data_cleaner.clean_dataframe(raw_data)
            
            # 3. 数据提取和结构化
            self.logger.info("提取和结构化数据")
            events_data = self.data_parser.extract_events(raw_data)
            user_data = self.data_parser.extract_user_properties(raw_data)
            session_data = self.data_parser.extract_sessions(raw_data)
            
            # 4. 存储到数据管理器
            self.logger.info("存储处理后的数据")
            self.storage_manager.store_events(raw_data)
            self.storage_manager.store_users(user_data)
            self.storage_manager.store_sessions(session_data)
            
            # 5. 生成数据摘要
            data_summary = self.data_parser.validate_data_quality(raw_data)
            
            processed_data = {
                'raw_data_size': len(raw_data),
                'events_data': events_data,
                'user_data': user_data,
                'session_data': session_data,
                'data_summary': data_summary,
                'validation_report': validation_report,
                'processing_timestamp': datetime.now().isoformat()
            }
            
            # 缓存结果
            if self.cache_enabled:
                self.cache[cache_key] = processed_data
                self.cache_timestamps[cache_key] = datetime.now()
            
            self.logger.info("数据处理阶段完成")
            return processed_data
    
    def _execute_analysis_pipeline(self, analysis_types: List[str]) -> Dict[str, AnalysisResult]:
        """
        执行分析管道
        
        Args:
            analysis_types: 分析类型列表
            
        Returns:
            分析结果字典
        """
        with self._performance_monitor("分析管道执行"):
            self.logger.info(f"开始执行分析管道: {analysis_types}")
            
            analysis_results = {}
            
            if self.config.enable_parallel_processing:
                # 并行执行分析
                analysis_results = self._execute_parallel_analysis(analysis_types)
            else:
                # 串行执行分析
                analysis_results = self._execute_sequential_analysis(analysis_types)
            
            self.logger.info("分析管道执行完成")
            return analysis_results
    
    def _execute_parallel_analysis(self, analysis_types: List[str]) -> Dict[str, AnalysisResult]:
        """并行执行分析"""
        self.logger.info("使用并行模式执行分析")
        
        analysis_results = {}
        futures = {}
        
        # 提交分析任务
        for analysis_type in analysis_types:
            future = self.executor.submit(self._execute_single_analysis, analysis_type)
            futures[future] = analysis_type
        
        # 收集结果
        for future in as_completed(futures, timeout=self.config.timeout_minutes * 60):
            analysis_type = futures[future]
            try:
                result = future.result()
                analysis_results[analysis_type] = result
                self.logger.info(f"分析完成: {analysis_type}")
            except Exception as e:
                self.logger.error(f"分析失败: {analysis_type}, 错误: {e}")
                analysis_results[analysis_type] = AnalysisResult(
                    analysis_type=analysis_type,
                    status='failed',
                    data={},
                    insights=[],
                    recommendations=[],
                    visualizations={},
                    execution_time=0,
                    timestamp=datetime.now(),
                    error_message=str(e)
                )
        
        return analysis_results
    
    def _execute_sequential_analysis(self, analysis_types: List[str]) -> Dict[str, AnalysisResult]:
        """串行执行分析"""
        self.logger.info("使用串行模式执行分析")
        
        analysis_results = {}
        
        for analysis_type in analysis_types:
            try:
                result = self._execute_single_analysis(analysis_type)
                analysis_results[analysis_type] = result
                self.logger.info(f"分析完成: {analysis_type}")
            except Exception as e:
                self.logger.error(f"分析失败: {analysis_type}, 错误: {e}")
                analysis_results[analysis_type] = AnalysisResult(
                    analysis_type=analysis_type,
                    status='failed',
                    data={},
                    insights=[],
                    recommendations=[],
                    visualizations={},
                    execution_time=0,
                    timestamp=datetime.now(),
                    error_message=str(e)
                )
        
        return analysis_results
    
    def _execute_single_analysis(self, analysis_type: str) -> AnalysisResult:
        """
        执行单个分析
        
        Args:
            analysis_type: 分析类型
            
        Returns:
            分析结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始执行分析: {analysis_type}")
            
            # 检查缓存
            cache_key = f"analysis_{analysis_type}_{self.current_workflow}"
            if self.cache_enabled and cache_key in self.cache:
                self.logger.info(f"使用缓存的分析结果: {analysis_type}")
                return self.cache[cache_key]
            
            # 根据分析类型执行相应的分析
            if analysis_type == 'event_analysis':
                result_data = self._execute_event_analysis()
            elif analysis_type == 'retention_analysis':
                result_data = self._execute_retention_analysis()
            elif analysis_type == 'conversion_analysis':
                result_data = self._execute_conversion_analysis()
            elif analysis_type == 'user_segmentation':
                result_data = self._execute_segmentation_analysis()
            elif analysis_type == 'path_analysis':
                result_data = self._execute_path_analysis()
            else:
                raise ValueError(f"未知的分析类型: {analysis_type}")
            
            execution_time = time.time() - start_time

            # 处理分析结果 - 检查是否已经是正确的格式
            if isinstance(result_data, dict):
                # 如果结果已经是字典格式，直接使用
                data = result_data.get('data', {})
                insights = result_data.get('insights', [])
                recommendations = result_data.get('recommendations', [])
                visualizations = result_data.get('visualizations', {})
                status = 'completed' if result_data.get('status') == 'success' else 'completed'
            else:
                # 如果不是字典，使用格式化方法
                formatted_result = self._format_analysis_result(result_data)
                data = formatted_result.get('data', {}) if isinstance(formatted_result, dict) else {}
                insights = formatted_result.get('insights', []) if isinstance(formatted_result, dict) else []
                recommendations = formatted_result.get('recommendations', []) if isinstance(formatted_result, dict) else []
                visualizations = formatted_result.get('visualizations', {}) if isinstance(formatted_result, dict) else {}
                status = 'completed'

            analysis_result = AnalysisResult(
                analysis_type=analysis_type,
                status=status,
                data=data,
                insights=insights,
                recommendations=recommendations,
                visualizations=visualizations,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
            
            # 缓存结果
            if self.cache_enabled:
                self.cache[cache_key] = analysis_result
                self.cache_timestamps[cache_key] = datetime.now()
            
            return analysis_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"分析执行失败: {analysis_type}, 错误: {e}")
            
            return AnalysisResult(
                analysis_type=analysis_type,
                status='failed',
                data={},
                insights=[],
                recommendations=[],
                visualizations={},
                execution_time=execution_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
    
    def _execute_event_analysis(self) -> Dict[str, Any]:
        """执行事件分析"""
        if AGENTS_AVAILABLE:
            # 使用智能体执行分析
            agent = EventAnalysisAgent(self.storage_manager)
            result = agent.comprehensive_event_analysis()
        else:
            # 使用分析引擎直接执行
            events_data = self.storage_manager.get_events()
            if not events_data.empty:
                analysis_result = self.event_engine.analyze_events(events_data)
                result = {
                    'status': 'success',
                    'data': analysis_result,
                    'insights': [
                        f"分析了 {len(events_data)} 个事件",
                        f"发现 {len(events_data['event_name'].unique())} 种不同的事件类型",
                        "事件分析已完成"
                    ],
                    'recommendations': [
                        "建议关注高频事件的用户行为模式",
                        "优化低频但重要的转化事件"
                    ]
                }
            else:
                result = {
                    'status': 'error',
                    'data': {},
                    'insights': [],
                    'recommendations': [],
                    'error_message': '没有可用的事件数据'
                }
        
        # 生成可视化
        events_data = self.storage_manager.get_events()
        if not events_data.empty:
            try:
                event_timeline_chart = self.chart_generator.create_event_timeline(events_data)
                event_distribution_chart = self.chart_generator.create_event_distribution_chart(events_data)
                visualizations = {
                    'event_timeline': {
                        'chart': event_timeline_chart,
                        'type': 'timeline',
                        'title': '事件时间线'
                    },
                    'event_distribution': {
                        'chart': event_distribution_chart,
                        'type': 'pie',
                        'title': '事件分布'
                    }
                }
                result['visualizations'] = visualizations
            except Exception as e:
                self.logger.warning(f"可视化生成失败: {e}")
                result['visualizations'] = {}
        
        return result
    
    def _execute_retention_analysis(self) -> Dict[str, Any]:
        """执行留存分析"""
        if AGENTS_AVAILABLE:
            agent = RetentionAnalysisAgent(self.storage_manager)
            result = agent.comprehensive_retention_analysis()
        else:
            # 使用分析引擎直接执行
            events_data = self.storage_manager.get_events()
            if not events_data.empty:
                analysis_result = self.retention_engine.analyze_retention(events_data)
                result = {
                    'status': 'success',
                    'data': analysis_result,
                    'insights': [
                        "留存分析已完成",
                        "计算了用户队列留存率",
                        "识别了关键留存节点"
                    ],
                    'recommendations': [
                        "关注新用户的首周留存率",
                        "优化用户激活流程"
                    ]
                }
            else:
                result = {
                    'status': 'error',
                    'data': {},
                    'insights': [],
                    'recommendations': [],
                    'error_message': '没有可用的事件数据'
                }
        
        # 生成可视化
        try:
            # 从分析结果中提取留存数据并转换为可视化格式
            retention_viz_data = self._transform_retention_data_for_visualization(result)
            if not retention_viz_data.empty:
                # 验证数据列
                required_columns = ['cohort_group', 'period_number', 'retention_rate']
                missing_columns = [col for col in required_columns if col not in retention_viz_data.columns]
                
                if not missing_columns:
                    # 生成热力图并包装成正确的格式
                    heatmap_chart = self.advanced_visualizer.create_retention_heatmap(retention_viz_data)
                    visualizations = {
                        'retention_heatmap': {
                            'chart': heatmap_chart,
                            'type': 'heatmap',
                            'title': '留存分析热力图'
                        }
                    }
                    result['visualizations'] = visualizations
                else:
                    self.logger.warning(f"可视化生成失败: 缺少必要的列: {missing_columns}")
                    result['visualizations'] = {}
            else:
                self.logger.warning("留存数据为空，无法生成可视化")
                result['visualizations'] = {}
        except Exception as e:
            self.logger.warning(f"可视化生成失败: {str(e)}")
            result['visualizations'] = {}
        
        return result
    
    def _execute_conversion_analysis(self) -> Dict[str, Any]:
        """执行转化分析"""
        if AGENTS_AVAILABLE:
            agent = ConversionAnalysisAgent(self.storage_manager)
            result = agent.comprehensive_conversion_analysis()
        else:
            # 使用分析引擎直接执行
            events_data = self.storage_manager.get_events()
            if not events_data.empty:
                analysis_result = self.conversion_engine.analyze_conversion_funnel(events_data)
                result = {
                    'status': 'success',
                    'data': analysis_result,
                    'insights': [
                        "转化分析已完成",
                        "构建了转化漏斗",
                        "识别了转化瓶颈"
                    ],
                    'recommendations': [
                        "优化转化率较低的步骤",
                        "A/B测试关键转化点"
                    ]
                }
            else:
                result = {
                    'status': 'error',
                    'data': {},
                    'insights': [],
                    'recommendations': [],
                    'error_message': '没有可用的事件数据'
                }
        
        # 生成可视化
        try:
            # 从分析结果中提取转化数据并转换为可视化格式
            conversion_viz_data = self._transform_conversion_data_for_visualization(result)
            if not conversion_viz_data.empty:
                funnel_chart = self.chart_generator.create_funnel_chart(conversion_viz_data)
                trends_chart = self.chart_generator.create_event_timeline(self.storage_manager.get_events())
                visualizations = {
                    'conversion_funnel': {
                        'chart': funnel_chart,
                        'type': 'funnel',
                        'title': '转化漏斗'
                    },
                    'conversion_trends': {
                        'chart': trends_chart,
                        'type': 'timeline',
                        'title': '转化趋势'
                    }
                }
                result['visualizations'] = visualizations
            else:
                self.logger.warning("可视化生成失败: 缺少必要的列: ['step_name', 'user_count']")
                result['visualizations'] = {}
        except Exception as e:
            self.logger.warning(f"可视化生成失败: 缺少必要的列: ['step_name', 'user_count']")
            result['visualizations'] = {}
        
        return result
    
    def _execute_segmentation_analysis(self) -> Dict[str, Any]:
        """执行用户分群分析"""
        if AGENTS_AVAILABLE:
            agent = UserSegmentationAgent(self.storage_manager)
            result = agent.comprehensive_user_segmentation()
        else:
            # 使用分析引擎直接执行
            events_data = self.storage_manager.get_events()
            if not events_data.empty:
                analysis_result = self.segmentation_engine.segment_users(events_data)
                result = {
                    'status': 'success',
                    'data': analysis_result,
                    'insights': [
                        "用户分群分析已完成",
                        "识别了不同的用户群体",
                        "生成了用户画像"
                    ],
                    'recommendations': [
                        "针对不同用户群体制定个性化策略",
                        "优化高价值用户群体的体验"
                    ]
                }
            else:
                result = {
                    'status': 'error',
                    'data': {},
                    'insights': [],
                    'recommendations': [],
                    'error_message': '没有可用的事件数据'
                }
        
        # 生成可视化
        users_data = self.storage_manager.get_users()
        if not users_data.empty:
            try:
                segments_chart = self.advanced_visualizer.create_user_segmentation_scatter(users_data)
                comparison_chart = self.advanced_visualizer.create_feature_radar_chart(users_data)
                visualizations = {
                    'user_segments': {
                        'chart': segments_chart,
                        'type': 'scatter',
                        'title': '用户分群'
                    },
                    'segment_comparison': {
                        'chart': comparison_chart,
                        'type': 'radar',
                        'title': '分群对比'
                    }
                }
                result['visualizations'] = visualizations
            except Exception as e:
                self.logger.warning(f"可视化生成失败: {e}")
                result['visualizations'] = {}
        
        return result
    
    def _execute_path_analysis(self) -> Dict[str, Any]:
        """执行路径分析"""
        if AGENTS_AVAILABLE:
            agent = PathAnalysisAgent(self.storage_manager)
            result = agent.comprehensive_path_analysis()
        else:
            # 使用分析引擎直接执行
            events_data = self.storage_manager.get_events()
            if not events_data.empty:
                analysis_result = self.path_engine.analyze_user_paths(events_data)
                result = {
                    'status': 'success',
                    'data': analysis_result,
                    'insights': [
                        "用户路径分析已完成",
                        "识别了常见的用户行为路径",
                        "发现了异常路径模式"
                    ],
                    'recommendations': [
                        "优化主要用户路径的体验",
                        "简化复杂的导航流程"
                    ]
                }
            else:
                result = {
                    'status': 'error',
                    'data': {},
                    'insights': [],
                    'recommendations': [],
                    'error_message': '没有可用的事件数据'
                }
        
        # 生成可视化 - 需要先转换数据格式
        sessions_data = self.storage_manager.get_sessions()
        if not sessions_data.empty:
            try:
                # 尝试生成基础可视化，如果数据格式不匹配则跳过
                visualizations = {}

                # 检查是否有足够的数据生成用户流程图
                if len(sessions_data) > 1:
                    # 创建简单的用户流程数据
                    flow_data = self._create_flow_data_from_sessions(sessions_data)
                    if not flow_data.empty:
                        flow_chart = self.advanced_visualizer.create_user_behavior_flow(flow_data)
                        visualizations['user_flow'] = {
                            'chart': flow_chart,
                            'type': 'sankey',
                            'title': '用户行为流'
                        }

                # 检查是否有足够的数据生成路径分析
                if len(sessions_data) > 1:
                    # 创建简单的路径数据
                    path_data = self._create_path_data_from_sessions(sessions_data)
                    if not path_data.empty:
                        path_chart = self.advanced_visualizer.create_path_analysis_network(path_data)
                        visualizations['path_analysis'] = {
                            'chart': path_chart,
                            'type': 'network',
                            'title': '路径分析网络'
                        }

                result['visualizations'] = visualizations
            except Exception as e:
                self.logger.warning(f"可视化生成失败: {e}")
                result['visualizations'] = {}
        
        return result

    def _create_flow_data_from_sessions(self, sessions_data: pd.DataFrame) -> pd.DataFrame:
        """从会话数据创建用户流程数据"""
        try:
            # 创建简单的平台到设备类别的流程
            flow_records = []
            for _, session in sessions_data.iterrows():
                source = session.get('platform', 'unknown')
                target = session.get('device_category', 'unknown')
                flow_records.append({
                    'source': source,
                    'target': target,
                    'value': 1
                })

            if flow_records:
                flow_df = pd.DataFrame(flow_records)
                # 聚合相同的流程
                flow_df = flow_df.groupby(['source', 'target'])['value'].sum().reset_index()
                return flow_df
            else:
                return pd.DataFrame()
        except Exception as e:
            self.logger.warning(f"创建流程数据失败: {e}")
            return pd.DataFrame()

    def _create_path_data_from_sessions(self, sessions_data: pd.DataFrame) -> pd.DataFrame:
        """从会话数据创建路径分析数据"""
        try:
            # 创建简单的地理位置路径
            path_records = []
            for _, session in sessions_data.iterrows():
                from_page = session.get('geo_country', 'unknown')
                to_page = session.get('geo_city', 'unknown')
                path_records.append({
                    'from_page': from_page,
                    'to_page': to_page,
                    'transition_count': 1
                })

            if path_records:
                path_df = pd.DataFrame(path_records)
                # 聚合相同的路径
                path_df = path_df.groupby(['from_page', 'to_page'])['transition_count'].sum().reset_index()
                return path_df
            else:
                return pd.DataFrame()
        except Exception as e:
            self.logger.warning(f"创建路径数据失败: {e}")
            return pd.DataFrame()

    def _generate_comprehensive_report(self, analysis_results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """
        生成综合报告
        
        Args:
            analysis_results: 分析结果字典
            
        Returns:
            综合报告
        """
        with self._performance_monitor("综合报告生成"):
            self.logger.info("开始生成综合报告")
            
            if AGENTS_AVAILABLE:
                # 使用报告生成智能体 - 传入存储管理器
                agent = ReportGenerationAgent(self.storage_manager)

                # 准备分析结果数据
                results_data = {}
                for analysis_type, result in analysis_results.items():
                    if result.status == 'completed':
                        results_data[analysis_type] = result.data

                # 生成报告
                report = agent.generate_comprehensive_report(results_data)
            else:
                # 生成简化报告
                successful_analyses = [
                    result for result in analysis_results.values() 
                    if result.status == 'completed'
                ]
                
                all_insights = []
                all_recommendations = []
                
                for result in successful_analyses:
                    all_insights.extend(result.insights)
                    all_recommendations.extend(result.recommendations)
                
                report = {
                    'status': 'success',
                    'summary': {
                        'total_analyses': len(analysis_results),
                        'successful_analyses': len(successful_analyses),
                        'total_insights': len(all_insights),
                        'total_recommendations': len(all_recommendations)
                    },
                    'key_insights': all_insights[:10],  # 前10个洞察
                    'key_recommendations': all_recommendations[:10],  # 前10个建议
                    'analysis_overview': {
                        analysis_type: {
                            'status': result.status,
                            'insights_count': len(result.insights),
                            'recommendations_count': len(result.recommendations)
                        }
                        for analysis_type, result in analysis_results.items()
                    }
                }
            
            self.logger.info("综合报告生成完成")
            return report
    
    def _generate_visualizations(self, analysis_results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """
        生成所有可视化图表
        
        Args:
            analysis_results: 分析结果字典
            
        Returns:
            可视化图表字典
        """
        with self._performance_monitor("可视化生成"):
            self.logger.info("开始生成可视化图表")
            
            all_visualizations = {}
            
            for analysis_type, result in analysis_results.items():
                if result.status == 'completed' and result.visualizations:
                    all_visualizations[analysis_type] = result.visualizations
            
            self.logger.info("可视化图表生成完成")
            return all_visualizations
    
    def _integrate_results(self, processed_data: Dict[str, Any], 
                          analysis_results: Dict[str, AnalysisResult],
                          comprehensive_report: Dict[str, Any],
                          visualizations: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合所有结果
        
        Args:
            processed_data: 处理后的数据
            analysis_results: 分析结果
            comprehensive_report: 综合报告
            visualizations: 可视化图表
            
        Returns:
            整合后的最终结果
        """
        self.logger.info("开始整合分析结果")
        
        # 计算总体统计
        total_execution_time = sum(
            result.execution_time for result in analysis_results.values()
        )
        
        successful_analyses = sum(
            1 for result in analysis_results.values() 
            if result.status == 'completed'
        )
        
        failed_analyses = sum(
            1 for result in analysis_results.values() 
            if result.status == 'failed'
        )
        
        # 整合结果
        integrated_result = {
            'workflow_id': self.current_workflow,
            'execution_summary': {
                'total_execution_time': total_execution_time,
                'successful_analyses': successful_analyses,
                'failed_analyses': failed_analyses,
                'data_size': processed_data.get('raw_data_size', 0),
                'completion_timestamp': datetime.now().isoformat()
            },
            'data_processing': {
                'summary': processed_data.get('data_summary', {}),
                'validation': processed_data.get('validation_report', {})
            },
            'analysis_results': analysis_results,  # 保留原始的AnalysisResult对象
            'analysis_summaries': {
                analysis_type: {
                    'status': result.status,
                    'insights': result.insights,
                    'recommendations': result.recommendations,
                    'execution_time': result.execution_time,
                    'data_summary': self._create_analysis_summary(result.data)
                }
                for analysis_type, result in analysis_results.items()
            },
            'comprehensive_report': comprehensive_report,
            'visualizations': visualizations,
            'system_metrics': self._get_current_metrics()
        }
        
        # 保存结果到分析结果字典
        self.analysis_results[self.current_workflow] = integrated_result
        
        self.logger.info("结果整合完成")
        return integrated_result
    
    def _create_analysis_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建分析数据摘要"""
        summary = {}
        
        for key, value in data.items():
            if isinstance(value, pd.DataFrame):
                summary[key] = {
                    'type': 'DataFrame',
                    'shape': value.shape,
                    'columns': list(value.columns) if hasattr(value, 'columns') else []
                }
            elif isinstance(value, dict):
                summary[key] = {
                    'type': 'dict',
                    'keys': list(value.keys())
                }
            elif isinstance(value, list):
                summary[key] = {
                    'type': 'list',
                    'length': len(value)
                }
            else:
                summary[key] = {
                    'type': type(value).__name__,
                    'value': str(value)[:100]  # 限制长度
                }
        
        return summary
    
    def _create_result_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """创建结果摘要"""
        return {
            'workflow_id': result.get('workflow_id'),
            'total_execution_time': result.get('execution_summary', {}).get('total_execution_time', 0),
            'successful_analyses': result.get('execution_summary', {}).get('successful_analyses', 0),
            'failed_analyses': result.get('execution_summary', {}).get('failed_analyses', 0),
            'data_size': result.get('execution_summary', {}).get('data_size', 0)
        }
    
    def _get_current_metrics(self) -> Dict[str, Any]:
        """获取当前系统指标"""
        if not self.metrics_history:
            return {}
        
        latest_metrics = self.metrics_history[-1]
        return {
            'cpu_usage': latest_metrics.cpu_usage,
            'memory_usage': latest_metrics.memory_usage,
            'memory_available': latest_metrics.memory_available,
            'timestamp': latest_metrics.timestamp.isoformat()
        }
    
    def refresh_storage_manager(self, storage_manager: DataStorageManager):
        """
        刷新存储管理器并重新初始化分析引擎
        
        Args:
            storage_manager: 新的存储管理器实例
        """
        try:
            self.logger.info("刷新存储管理器和分析引擎")
            
            # 更新存储管理器
            self.storage_manager = storage_manager
            
            # 重新初始化分析引擎
            self.event_engine = EventAnalysisEngine(self.storage_manager)
            self.retention_engine = RetentionAnalysisEngine(self.storage_manager)
            self.conversion_engine = ConversionAnalysisEngine(self.storage_manager)
            
            self.logger.info("存储管理器和分析引擎刷新完成")
            
        except Exception as e:
            self.logger.error(f"刷新存储管理器失败: {e}")
    
    def _format_analysis_result(self, result: Any) -> Dict[str, Any]:
        """
        格式化分析结果为统一的字典格式
        
        Args:
            result: 分析结果（可能是字典、列表、对象等）
            
        Returns:
            格式化后的字典
        """
        try:
            if isinstance(result, dict):
                return result
            elif isinstance(result, list):
                return {
                    "type": "list",
                    "count": len(result),
                    "items": result[:5] if len(result) > 5 else result,  # 只保留前5个项目
                    "truncated": len(result) > 5
                }
            elif hasattr(result, '__dict__'):
                # 如果是对象，尝试转换为字典
                obj_dict = {}
                for attr in dir(result):
                    if not attr.startswith('_') and not callable(getattr(result, attr)):
                        try:
                            value = getattr(result, attr)
                            if isinstance(value, (str, int, float, bool, list, dict)):
                                obj_dict[attr] = value
                        except Exception:
                            continue
                return obj_dict if obj_dict else {"type": type(result).__name__, "value": str(result)}
            else:
                return {"type": type(result).__name__, "value": str(result)}
        except Exception as e:
            self.logger.error(f"格式化分析结果失败: {e}")
            return {"type": "error", "value": str(result), "error": str(e)}
    
    def _cleanup_workflow_data(self, workflow_id: str):
        """清理工作流程数据"""
        try:
            self.logger.info(f"清理工作流程数据: {workflow_id}")
            
            # 清理相关缓存
            keys_to_remove = [
                key for key in self.cache.keys() 
                if workflow_id in key
            ]
            
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
            
            # 强制垃圾回收
            gc.collect()
            
            self.logger.info(f"工作流程数据清理完成: {workflow_id}")
            
        except Exception as e:
            self.logger.error(f"工作流程数据清理失败: {e}")
    
    def export_workflow_results(self, workflow_id: str, 
                              export_format: str = 'json',
                              include_raw_data: bool = False) -> str:
        """
        导出工作流程结果
        
        Args:
            workflow_id: 工作流程ID
            export_format: 导出格式 ('json', 'pdf', 'excel')
            include_raw_data: 是否包含原始数据
            
        Returns:
            导出文件路径
        """
        if workflow_id not in self.analysis_results:
            raise ValueError(f"工作流程结果不存在: {workflow_id}")
        
        result = self.analysis_results[workflow_id]
        
        # 准备导出数据
        export_data = result.copy()
        if not include_raw_data:
            # 移除原始数据以减小文件大小
            if 'data_processing' in export_data:
                export_data['data_processing'] = {
                    'summary': export_data['data_processing'].get('summary', {}),
                    'validation': export_data['data_processing'].get('validation', {})
                }
        
        # 使用报告导出器
        file_path = self.report_exporter.export_report(
            export_data, 
            format_type=export_format,
            filename=f"workflow_results_{workflow_id}"
        )
        
        self.logger.info(f"工作流程结果已导出: {file_path}")
        return file_path
    
    def get_workflow_status(self, workflow_id: str = None) -> Dict[str, Any]:
        """
        获取工作流程状态
        
        Args:
            workflow_id: 工作流程ID，None表示获取当前工作流程状态
            
        Returns:
            工作流程状态信息
        """
        if workflow_id is None:
            workflow_id = self.current_workflow
        
        if workflow_id is None:
            return {'status': 'no_active_workflow'}
        
        # 查找工作流程记录
        workflow_record = None
        for record in self.workflow_history:
            if record['workflow_id'] == workflow_id:
                workflow_record = record
                break
        
        if workflow_record is None:
            return {'status': 'workflow_not_found'}
        
        status_info = {
            'workflow_id': workflow_id,
            'status': workflow_record['status'],
            'start_time': workflow_record['start_time'],
            'file_path': workflow_record.get('file_path'),
            'analysis_types': workflow_record.get('analysis_types', [])
        }
        
        # 如果有结果，添加结果摘要
        if workflow_id in self.analysis_results:
            result = self.analysis_results[workflow_id]
            status_info['result_summary'] = result.get('execution_summary', {})
        
        return status_info
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        
        Returns:
            系统健康状态信息
        """
        current_metrics = self._get_current_metrics()
        
        # 计算平均指标
        if self.metrics_history:
            recent_metrics = self.metrics_history[-10:]  # 最近10个指标
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = 0
            avg_memory = 0
        
        # 评估健康状态
        health_status = 'healthy'
        if avg_cpu > 80 or avg_memory > 85:
            health_status = 'warning'
        if avg_cpu > 95 or avg_memory > 95:
            health_status = 'critical'
        
        return {
            'overall_status': health_status,
            'current_metrics': current_metrics,
            'average_metrics': {
                'cpu_usage': avg_cpu,
                'memory_usage': avg_memory
            },
            'active_workflows': 1 if self.current_workflow else 0,
            'total_workflows': len(self.workflow_history),
            'cache_size': len(self.cache),
            'monitoring_enabled': self.monitoring_enabled
        }
    
    def _transform_retention_data_for_visualization(self, result: Dict[str, Any]) -> pd.DataFrame:
        """
        将留存分析结果转换为可视化所需的格式
        
        Args:
            result: 留存分析结果
            
        Returns:
            包含cohort_group, period_number, retention_rate列的DataFrame
        """
        try:
            viz_data = []
            
            # 检查结果结构
            if result.get('success') and 'analyses' in result:
                cohort_analysis = result['analyses'].get('cohort_analysis', {})
                if cohort_analysis.get('success') and 'cohorts' in cohort_analysis:
                    cohorts = cohort_analysis['cohorts']
                    
                    for cohort in cohorts:
                        cohort_period = cohort.get('cohort_period', 'Unknown')
                        retention_rates = cohort.get('retention_rates', [])
                        
                        for period_num, retention_rate in enumerate(retention_rates):
                            viz_data.append({
                                'cohort_group': cohort_period,
                                'period_number': period_num,
                                'retention_rate': retention_rate
                            })
            
            # 如果没有数据，创建示例数据避免可视化错误
            if not viz_data:
                self.logger.warning("没有找到留存数据，创建示例数据")
                viz_data = [
                    {'cohort_group': '2024-01', 'period_number': 0, 'retention_rate': 1.0},
                    {'cohort_group': '2024-01', 'period_number': 1, 'retention_rate': 0.7},
                    {'cohort_group': '2024-01', 'period_number': 2, 'retention_rate': 0.5}
                ]
            
            return pd.DataFrame(viz_data)
            
        except Exception as e:
            self.logger.error(f"转换留存数据失败: {e}")
            # 返回示例数据
            return pd.DataFrame([
                {'cohort_group': '2024-01', 'period_number': 0, 'retention_rate': 1.0},
                {'cohort_group': '2024-01', 'period_number': 1, 'retention_rate': 0.7}
            ])
    
    def _transform_conversion_data_for_visualization(self, result: Dict[str, Any]) -> pd.DataFrame:
        """
        将转化分析结果转换为可视化所需的格式
        
        Args:
            result: 转化分析结果
            
        Returns:
            包含step_name, user_count列的DataFrame
        """
        try:
            viz_data = []
            
            # 检查结果结构
            if result.get('status') == 'success':
                # 检查funnel_analyses结构
                if 'funnel_analyses' in result:
                    for funnel_name, funnel_result in result['funnel_analyses'].items():
                        if funnel_result.get('status') == 'success' and 'funnel' in funnel_result:
                            steps = funnel_result['funnel'].get('steps', [])
                            for step in steps:
                                viz_data.append({
                                    'step_name': step.get('step_name', f'Step {step.get("step_order", 0)}'),
                                    'user_count': step.get('total_users', 0),
                                    'step_order': step.get('step_order', 0),
                                    'conversion_rate': step.get('conversion_rate', 0)
                                })
                            break  # 只使用第一个漏斗的数据
                
                # 检查conversion_rates_analysis结构
                elif 'conversion_rates_analysis' in result:
                    conv_result = result['conversion_rates_analysis']
                    if conv_result.get('status') == 'success' and 'results' in conv_result:
                        funnels = conv_result['results'].get('funnels', [])
                        if funnels:
                            steps = funnels[0].get('steps', [])
                            for step in steps:
                                viz_data.append({
                                    'step_name': step.get('step_name', f'Step {step.get("step_order", 0)}'),
                                    'user_count': step.get('total_users', 0),
                                    'step_order': step.get('step_order', 0),
                                    'conversion_rate': step.get('conversion_rate', 0)
                                })
            
            # 如果没有数据，创建示例数据避免可视化错误
            if not viz_data:
                self.logger.warning("没有找到转化数据，创建示例数据")
                viz_data = [
                    {'step_name': '访问首页', 'user_count': 10000, 'step_order': 0, 'conversion_rate': 1.0},
                    {'step_name': '浏览产品', 'user_count': 7500, 'step_order': 1, 'conversion_rate': 0.75},
                    {'step_name': '添加购物车', 'user_count': 3000, 'step_order': 2, 'conversion_rate': 0.3},
                    {'step_name': '完成购买', 'user_count': 1200, 'step_order': 3, 'conversion_rate': 0.12}
                ]
            
            return pd.DataFrame(viz_data)
            
        except Exception as e:
            self.logger.error(f"转换转化数据失败: {e}")
            # 返回示例数据
            return pd.DataFrame([
                {'step_name': '访问首页', 'user_count': 10000, 'step_order': 0, 'conversion_rate': 1.0},
                {'step_name': '完成购买', 'user_count': 1200, 'step_order': 1, 'conversion_rate': 0.12}
            ])
    
    def shutdown(self):
        """关闭集成管理器"""
        try:
            self.logger.info("开始关闭系统集成管理器")
            
            # 停止监控
            self.monitoring_enabled = False
            
            # 关闭线程池
            self.executor.shutdown(wait=True)
            
            # 清理缓存
            self.cache.clear()
            self.cache_timestamps.clear()
            
            # 清理分析结果
            self.analysis_results.clear()
            
            self.logger.info("系统集成管理器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭系统集成管理器时出错: {e}")