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
            
            # 分析引擎
            self.event_engine = EventAnalysisEngine()
            self.retention_engine = RetentionAnalysisEngine()
            self.conversion_engine = ConversionAnalysisEngine()
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
            
            # 创建分析结果
            analysis_result = AnalysisResult(
                analysis_type=analysis_type,
                status='completed',
                data=result_data.get('data', {}),
                insights=result_data.get('insights', []),
                recommendations=result_data.get('recommendations', []),
                visualizations=result_data.get('visualizations', {}),
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
                visualizations = {
                    'event_timeline': self.chart_generator.create_event_timeline(events_data),
                    'event_distribution': self.chart_generator.create_event_distribution_chart(events_data)
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
        users_data = self.storage_manager.get_users()
        if not users_data.empty:
            try:
                visualizations = {
                    'retention_heatmap': self.advanced_visualizer.create_retention_heatmap(users_data),
                    'cohort_analysis': self.advanced_visualizer.create_cohort_analysis_heatmap(users_data)
                }
                result['visualizations'] = visualizations
            except Exception as e:
                self.logger.warning(f"可视化生成失败: {e}")
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
        events_data = self.storage_manager.get_events()
        if not events_data.empty:
            try:
                visualizations = {
                    'conversion_funnel': self.chart_generator.create_funnel_chart(events_data),
                    'conversion_trends': self.chart_generator.create_event_timeline(events_data)
                }
                result['visualizations'] = visualizations
            except Exception as e:
                self.logger.warning(f"可视化生成失败: {e}")
                result['visualizations'] = {}
        
        return result
    
    def _execute_segmentation_analysis(self) -> Dict[str, Any]:
        """执行用户分群分析"""
        if AGENTS_AVAILABLE:
            agent = UserSegmentationAgent(self.storage_manager)
            result = agent.comprehensive_segmentation_analysis()
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
                visualizations = {
                    'user_segments': self.advanced_visualizer.create_user_segmentation_scatter(users_data),
                    'segment_comparison': self.advanced_visualizer.create_feature_radar_chart(users_data)
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
        
        # 生成可视化
        sessions_data = self.storage_manager.get_sessions()
        if not sessions_data.empty:
            try:
                visualizations = {
                    'user_flow': self.advanced_visualizer.create_user_behavior_flow(sessions_data),
                    'path_analysis': self.advanced_visualizer.create_path_analysis_network(sessions_data)
                }
                result['visualizations'] = visualizations
            except Exception as e:
                self.logger.warning(f"可视化生成失败: {e}")
                result['visualizations'] = {}
        
        return result
    
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
                # 使用报告生成智能体
                agent = ReportGenerationAgent()
                
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
            'analysis_results': {
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