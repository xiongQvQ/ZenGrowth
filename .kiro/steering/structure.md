# Project Structure & Organization

## Directory Structure

```
user-behavior-analytics-platform/
├── agents/                     # CrewAI智能体模块
│   ├── __init__.py
│   ├── data_processing_agent.py        # 数据处理智能体
│   ├── event_analysis_agent.py         # 事件分析智能体
│   ├── retention_analysis_agent.py     # 留存分析智能体
│   ├── conversion_analysis_agent.py    # 转化分析智能体
│   ├── user_segmentation_agent.py      # 用户分群智能体
│   ├── path_analysis_agent.py          # 路径分析智能体
│   └── report_generation_agent.py      # 报告生成智能体
│
├── engines/                    # 分析引擎模块
│   ├── __init__.py
│   ├── event_analysis_engine.py        # 事件分析引擎
│   ├── retention_analysis_engine.py    # 留存分析引擎
│   ├── conversion_analysis_engine.py   # 转化分析引擎
│   ├── user_segmentation_engine.py     # 用户分群引擎
│   └── path_analysis_engine.py         # 路径分析引擎
│
├── tools/                      # 数据处理工具
│   ├── __init__.py
│   ├── ga4_data_parser.py              # GA4数据解析器
│   ├── data_validator.py               # 数据验证器
│   ├── data_cleaner.py                 # 数据清洗器
│   └── data_storage_manager.py         # 数据存储管理器
│
├── config/                     # 配置管理
│   ├── __init__.py
│   ├── settings.py                     # 系统配置
│   ├── crew_config.py                  # CrewAI配置
│   ├── agent_orchestrator.py           # 智能体编排器
│   ├── analysis_config.json            # 分析参数配置
│   └── system_config.json              # 系统配置文件
│
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── logger.py                       # 日志配置
│   ├── config_manager.py               # 配置管理器
│   └── report_exporter.py              # 报告导出器
│
├── visualization/              # 可视化组件
│   ├── chart_generator.py              # 图表生成器
│   └── advanced_visualizer.py          # 高级可视化
│
├── system/                     # 系统集成
│   ├── integration_manager.py          # 集成管理器
│   └── standalone_integration_manager.py
│
├── tests/                      # 单元测试
│   ├── test_*.py                       # 各模块测试文件
│   └── __pycache__/
│
├── data/                       # 数据目录
│   ├── uploads/                        # 上传文件存储
│   ├── processed/                      # 处理后数据
│   └── events_ga4.ndjson              # 示例数据
│
├── reports/                    # 报告输出
├── logs/                       # 日志文件
├── ui/                         # 用户界面模块
├── docs/                       # 项目文档
└── .kiro/                      # Kiro IDE配置
    └── specs/                          # 项目规格文档
```

## Code Organization Patterns

### Agent Structure
Each agent follows a consistent pattern:
- **Agent Class**: Main CrewAI agent implementation
- **Tools**: Specialized tools for the agent's domain
- **Standalone Version**: Independent version for testing
- **Integration Tests**: Comprehensive testing suite

### Engine Structure
Analysis engines contain core algorithms:
- **Engine Class**: Main analysis logic
- **Data Models**: Pydantic models for type safety
- **Utility Functions**: Helper methods for calculations
- **Configuration**: Engine-specific parameters

### Tool Structure
Data processing tools follow common patterns:
- **Parser/Processor Class**: Main functionality
- **Validation Methods**: Data quality checks
- **Error Handling**: Comprehensive exception management
- **Logging**: Detailed operation logging

## File Naming Conventions

### Python Files
- **Agents**: `{domain}_analysis_agent.py`
- **Engines**: `{domain}_analysis_engine.py`
- **Tools**: `{function}_tool.py` or `{domain}_parser.py`
- **Tests**: `test_{module_name}.py`
- **Standalone Tests**: `test_{module}_standalone.py`

### Configuration Files
- **JSON Config**: `{domain}_config.json`
- **Python Config**: `{domain}_config.py`
- **Environment**: `.env` (with `.env.example` template)

### Data Files
- **GA4 Data**: `*.ndjson`, `*.json`, `*.jsonl`
- **Reports**: `{analysis_type}_report_{timestamp}.{format}`
- **Logs**: `app.log` (with rotation)

## Import Patterns

### Standard Import Order
1. Standard library imports
2. Third-party library imports
3. Local application imports

### Local Import Structure
```python
# Configuration imports
from config.settings import settings
from config.crew_config import get_llm

# Tool imports
from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator

# Engine imports
from engines.event_analysis_engine import EventAnalysisEngine

# Utility imports
from utils.logger import setup_logger
```

## Testing Organization

### Test Categories
- **Unit Tests**: `tests/test_{module}.py`
- **Integration Tests**: `test_{feature}_integration.py`
- **Standalone Tests**: `test_{agent}_standalone.py`
- **System Tests**: `test_system_integration.py`

### Test Data
- **Sample Data**: `data/events_ga4.ndjson`
- **Test Output**: `test_output/` (gitignored)
- **Mock Data**: Generated in test files using factories

## Configuration Hierarchy

### Environment-Based Configuration
1. **Environment Variables** (.env file)
2. **System Configuration** (config/settings.py)
3. **Analysis Configuration** (config/analysis_config.json)
4. **Agent Configuration** (config/crew_config.py)

### Configuration Priority
1. Environment variables (highest)
2. Configuration files
3. Default values (lowest)