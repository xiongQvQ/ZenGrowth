"""
数据处理智能体模块

该模块实现DataProcessingAgent类，负责GA4数据的解析、验证和预处理。
智能体集成了GA4数据解析器、数据验证器和数据清洗工具。
"""

import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator
from tools.data_cleaner import DataCleaner
from tools.data_storage_manager import DataStorageManager
from config.crew_config import get_llm

logger = logging.getLogger(__name__)


class GA4DataProcessingTool(BaseTool):
    """GA4数据处理工具"""
    
    name: str = "ga4_data_processing"
    description: str = "解析和处理GA4 NDJSON格式的事件数据，包括数据验证、清洗和标准化"
    
    def __init__(self):
        super().__init__()
        # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'parser', GA4DataParser())
        object.__setattr__(self, 'validator', DataValidator())
        object.__setattr__(self, 'cleaner', DataCleaner())
        
    def _run(self, file_path: str) -> Dict[str, Any]:
        """
        执行GA4数据处理
        
        Args:
            file_path: GA4 NDJSON文件路径
            
        Returns:
            处理结果字典
        """
        try:
            logger.info(f"开始处理GA4数据文件: {file_path}")
            
            # 1. 解析NDJSON文件
            raw_data = self.parser.parse_ndjson(file_path)
            logger.info(f"成功解析{len(raw_data)}条原始事件数据")
            
            # 2. 数据验证
            validation_report = self.validator.validate_dataframe(raw_data)
            logger.info(f"数据验证完成: {len(validation_report['errors'])}个错误，{len(validation_report['warnings'])}个警告")
            
            # 3. 数据清洗和标准化
            cleaned_data = self.cleaner.clean_dataframe(raw_data)
            logger.info(f"数据清洗完成，处理后数据量: {len(cleaned_data)}")
            
            # 4. 提取结构化数据
            events_by_type = self.parser.extract_events(cleaned_data)
            user_properties = self.parser.extract_user_properties(cleaned_data)
            sessions = self.parser.extract_sessions(cleaned_data)
            
            # 5. 生成数据质量报告
            quality_report = self.parser.validate_data_quality(cleaned_data)
            
            result = {
                'status': 'success',
                'raw_data_count': len(raw_data),
                'processed_data_count': len(cleaned_data),
                'events_by_type': {event_type: len(events) for event_type, events in events_by_type.items()},
                'unique_users': len(user_properties),
                'total_sessions': len(sessions),
                'validation_report': validation_report,
                'quality_report': quality_report,
                'data': {
                    'events_by_type': events_by_type,
                    'user_properties': user_properties,
                    'sessions': sessions,
                    'cleaned_data': cleaned_data
                }
            }
            
            logger.info("GA4数据处理完成")
            return result
            
        except Exception as e:
            logger.error(f"GA4数据处理失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'data': None
            }


class DataValidationTool(BaseTool):
    """数据验证工具"""
    
    name: str = "data_validation"
    description: str = "验证数据质量和完整性，检查数据结构和一致性问题"
    
    def __init__(self):
        super().__init__()
        # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'validator', DataValidator())
        
    def _run(self, data: Any) -> Dict[str, Any]:
        """
        执行数据验证
        
        Args:
            data: 要验证的DataFrame
            
        Returns:
            验证结果
        """
        try:
            logger.info("开始数据验证")
            
            # 基础验证
            validation_report = self.validator.validate_dataframe(data)
            
            # 事件序列验证
            sequence_report = self.validator.validate_event_sequence(data)
            
            # 生成修复建议
            suggestions = self.validator.suggest_data_fixes(validation_report)
            
            result = {
                'status': 'success',
                'validation_report': validation_report,
                'sequence_report': sequence_report,
                'suggestions': suggestions,
                'summary': {
                    'total_errors': len(validation_report.get('errors', [])),
                    'total_warnings': len(validation_report.get('warnings', [])),
                    'validation_passed': validation_report.get('validation_passed', False)
                }
            }
            
            logger.info(f"数据验证完成: {result['summary']}")
            return result
            
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }


class DataStorageTool(BaseTool):
    """数据存储工具"""
    
    name: str = "data_storage"
    description: str = "将处理后的数据存储到内存数据库中，支持后续分析查询"
    
    def __init__(self):
        super().__init__()
        # Initialize components as instance variables (not Pydantic fields)
        object.__setattr__(self, 'storage_manager', DataStorageManager())
        
    def _run(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        存储处理后的数据
        
        Args:
            processed_data: 处理后的数据字典
            
        Returns:
            存储结果
        """
        try:
            logger.info("开始存储处理后的数据")
            
            data = processed_data.get('data', {})
            
            # 存储事件数据
            events_by_type = data.get('events_by_type', {})
            if events_by_type:
                # 合并所有事件数据进行存储
                all_events = pd.concat(events_by_type.values(), ignore_index=True)
                self.storage_manager.store_events(all_events)
                
            # 存储用户属性
            user_properties = data.get('user_properties')
            if user_properties is not None and not user_properties.empty:
                self.storage_manager.store_users(user_properties)
                
            # 存储会话数据
            sessions = data.get('sessions')
            if sessions is not None and not sessions.empty:
                self.storage_manager.store_sessions(sessions)
                
            # 获取存储统计
            storage_stats = self.storage_manager.get_statistics()
            
            result = {
                'status': 'success',
                'storage_stats': storage_stats,
                'message': '数据存储完成'
            }
            
            logger.info(f"数据存储完成: {storage_stats}")
            return result
            
        except Exception as e:
            logger.error(f"数据存储失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }


class DataProcessingAgent:
    """数据处理智能体类"""
    
    def __init__(self):
        """初始化数据处理智能体"""
        self.tools = [
            GA4DataProcessingTool(),
            DataValidationTool(),
            DataStorageTool()
        ]
        
        self.agent = Agent(
            role="数据处理专家",
            goal="解析和预处理GA4事件数据，确保数据质量和完整性",
            backstory="""你是一位经验丰富的数据工程师，专门处理大规模用户行为数据。
                        你精通各种数据格式解析，能够快速识别数据质量问题并提供解决方案。
                        你的任务是确保所有输入的GA4数据都经过严格的验证、清洗和标准化处理，
                        为后续的分析工作提供高质量的数据基础。""",
            tools=self.tools,
            llm=get_llm(),
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
        
    def process_ga4_data(self, file_path: str) -> Dict[str, Any]:
        """
        处理GA4数据文件
        
        Args:
            file_path: GA4 NDJSON文件路径
            
        Returns:
            处理结果
        """
        try:
            logger.info(f"数据处理智能体开始处理文件: {file_path}")
            
            # 使用GA4数据处理工具
            processing_tool = GA4DataProcessingTool()
            result = processing_tool._run(file_path)
            
            if result['status'] == 'success':
                # 存储处理后的数据
                storage_tool = DataStorageTool()
                storage_result = storage_tool._run(result)
                
                # 合并结果
                result['storage_result'] = storage_result
                
                logger.info("数据处理智能体任务完成")
            else:
                logger.error(f"数据处理失败: {result.get('error_message')}")
                
            return result
            
        except Exception as e:
            logger.error(f"数据处理智能体执行失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'data': None
            }
            
    def validate_data_quality(self, data: Any) -> Dict[str, Any]:
        """
        验证数据质量
        
        Args:
            data: 要验证的数据
            
        Returns:
            验证结果
        """
        try:
            validation_tool = DataValidationTool()
            return validation_tool._run(data)
        except Exception as e:
            logger.error(f"数据质量验证失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e)
            }
            
    def get_agent(self) -> Agent:
        """获取CrewAI智能体实例"""
        return self.agent
        
    def get_tools(self) -> List[BaseTool]:
        """获取智能体工具列表"""
        return self.tools