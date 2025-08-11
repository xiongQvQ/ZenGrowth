# 配置说明和故障排除指南

## 📋 概述

本文档提供用户行为分析智能体平台的详细配置说明和常见问题的故障排除方案。涵盖系统配置、环境设置、性能调优和错误诊断等内容。

## ⚙️ 系统配置详解

### 1. 环境变量配置

#### 基础环境变量 (.env文件)

```env
# 必需配置
GOOGLE_API_KEY=your_google_gemini_api_key_here

# LLM模型配置
LLM_MODEL=gemini-2.5-pro
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000

# 应用配置
APP_TITLE=用户行为分析智能体平台
APP_ICON=📊

# 数据处理配置
MAX_FILE_SIZE_MB=100
CHUNK_SIZE=10000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 性能配置
MEMORY_LIMIT_GB=8
MAX_WORKERS=4
ENABLE_CACHING=true
CACHE_TTL_HOURS=24
```

#### 高级环境变量

```env
# API配置
API_TIMEOUT_SECONDS=30
API_RETRY_COUNT=3
API_RATE_LIMIT_PER_MINUTE=60

# 数据库配置 (可选)
DATABASE_URL=sqlite:///data/analytics.db
DATABASE_POOL_SIZE=10

# 缓存配置
REDIS_URL=redis://localhost:6379/0
CACHE_PREFIX=analytics_

# 安全配置
SECRET_KEY=your_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# 监控配置
ENABLE_MONITORING=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=60
```

### 2. 系统配置文件

#### config/system_config.json

```json
{
  "api_settings": {
    "google_api_key": "${GOOGLE_API_KEY}",
    "llm_model": "gemini-2.5-pro",
    "llm_temperature": 0.1,
    "llm_max_tokens": 4000,
    "timeout_seconds": 30,
    "retry_count": 3,
    "rate_limit_per_minute": 60
  },
  "data_processing": {
    "max_file_size_mb": 100,
    "chunk_size": 10000,
    "memory_limit_gb": 8,
    "cleanup_temp_files": true,
    "enable_parallel_processing": true,
    "max_workers": 4
  },
  "ui_settings": {
    "theme": "light",
    "language": "zh-CN",
    "page_size": 20,
    "show_debug_info": false,
    "auto_refresh_interval": 30
  },
  "export_settings": {
    "default_format": "json",
    "include_raw_data": false,
    "compress_exports": true,
    "export_dir": "reports",
    "filename_template": "analysis_report_{timestamp}"
  },
  "security": {
    "enable_encryption": true,
    "session_timeout_minutes": 60,
    "max_login_attempts": 5,
    "password_min_length": 8
  },
  "monitoring": {
    "enable_logging": true,
    "log_level": "INFO",
    "log_rotation": true,
    "max_log_size_mb": 100,
    "enable_metrics": true,
    "metrics_retention_days": 30
  }
}
```

#### config/analysis_config.json

```json
{
  "event_analysis": {
    "time_granularity": "day",
    "top_events_limit": 10,
    "trend_analysis_days": 30,
    "correlation_threshold": 0.5,
    "anomaly_detection_threshold": 2.0,
    "seasonal_analysis": true
  },
  "retention_analysis": {
    "retention_periods": [1, 7, 14, 30],
    "cohort_type": "weekly",
    "min_cohort_size": 100,
    "analysis_window_days": 90,
    "include_churned_users": true
  },
  "conversion_analysis": {
    "conversion_window_hours": 24,
    "min_funnel_users": 50,
    "attribution_model": "first_touch",
    "include_micro_conversions": true,
    "funnel_timeout_hours": 168
  },
  "user_segmentation": {
    "clustering_method": "kmeans",
    "n_clusters": 5,
    "min_cluster_size": 100,
    "feature_types": ["behavioral", "demographic"],
    "normalization_method": "standard",
    "random_state": 42
  },
  "path_analysis": {
    "min_path_support": 0.01,
    "max_path_length": 10,
    "session_timeout_minutes": 30,
    "include_bounce_sessions": false,
    "path_mining_algorithm": "sequential_pattern"
  }
}
```

### 3. 运行时配置

#### Streamlit配置 (.streamlit/config.toml)

```toml
[global]
developmentMode = false
logLevel = "info"

[server]
port = 8501
address = "0.0.0.0"
maxUploadSize = 200
maxMessageSize = 200
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[client]
caching = true
displayEnabled = true
showErrorDetails = true
```

#### 日志配置 (logging.conf)

```ini
[loggers]
keys=root,analytics,crewai

[handlers]
keys=consoleHandler,fileHandler,rotatingFileHandler

[formatters]
keys=simpleFormatter,detailedFormatter

[logger_root]
level=INFO
handlers=consoleHandler,rotatingFileHandler

[logger_analytics]
level=DEBUG
handlers=fileHandler
qualname=analytics
propagate=0

[logger_crewai]
level=WARNING
handlers=consoleHandler
qualname=crewai
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=detailedFormatter
args=('logs/analytics.log',)

[handler_rotatingFileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailedFormatter
args=('logs/app.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s
```

## 🔧 配置管理

### 动态配置更新

```python
from utils.config_manager import config_manager

# 更新系统配置
config_manager.update_system_config('api_settings', {
    'llm_temperature': 0.2,
    'llm_max_tokens': 5000
})

# 更新分析配置
config_manager.update_analysis_config('event_analysis', {
    'time_granularity': 'hour',
    'top_events_limit': 20
})

# 保存配置到文件
config_manager.save_config()

# 重新加载配置
config_manager.reload_config()
```

### 配置验证

```python
from config.settings import validate_config

# 验证配置完整性
is_valid = validate_config()
if not is_valid:
    print("配置验证失败，请检查配置文件")

# 验证特定配置项
def validate_api_config():
    try:
        from config.settings import get_google_api_key
        api_key = get_google_api_key()
        return len(api_key) > 20  # 基本长度检查
    except Exception:
        return False
```

## 🚨 故障排除指南

### 1. 安装和启动问题

#### 问题: Python版本不兼容

**症状**:
```
ERROR: Python 3.7 is not supported
```

**解决方案**:
1. 检查Python版本: `python --version`
2. 升级到Python 3.8+
3. 使用pyenv管理多个Python版本:
   ```bash
   pyenv install 3.9.0
   pyenv local 3.9.0
   ```

#### 问题: 依赖安装失败

**症状**:
```
ERROR: Could not install packages due to an EnvironmentError
```

**解决方案**:
1. 升级pip: `pip install --upgrade pip`
2. 清理pip缓存: `pip cache purge`
3. 使用国内镜像源:
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
   ```
4. 检查系统依赖:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-dev build-essential
   
   # CentOS/RHEL
   sudo yum install python3-devel gcc
   
   # macOS
   xcode-select --install
   ```

#### 问题: 虚拟环境创建失败

**症状**:
```
ERROR: Unable to create virtual environment
```

**解决方案**:
1. 手动创建虚拟环境:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```
2. 使用conda创建环境:
   ```bash
   conda create -n analytics python=3.9
   conda activate analytics
   ```

### 2. API配置问题

#### 问题: Google API密钥无效

**症状**:
```
ERROR: Invalid API key or quota exceeded
```

**解决方案**:
1. 验证API密钥格式:
   ```python
   import re
   api_key = "your_api_key"
   if not re.match(r'^[A-Za-z0-9_-]{39}$', api_key):
       print("API密钥格式不正确")
   ```

2. 检查API配额:
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 查看API使用情况和配额限制

3. 测试API连接:
   ```python
   from config.settings import get_google_api_key
   from langchain_google_genai import ChatGoogleGenerativeAI
   
   try:
       llm = ChatGoogleGenerativeAI(
           model="gemini-2.5-pro",
           google_api_key=get_google_api_key()
       )
       response = llm.invoke("测试连接")
       print("API连接正常")
   except Exception as e:
       print(f"API连接失败: {e}")
   ```

#### 问题: API请求超时

**症状**:
```
TimeoutError: Request timed out after 30 seconds
```

**解决方案**:
1. 增加超时时间:
   ```env
   API_TIMEOUT_SECONDS=60
   ```

2. 检查网络连接:
   ```bash
   ping google.com
   curl -I https://generativelanguage.googleapis.com
   ```

3. 使用代理 (如需要):
   ```env
   HTTP_PROXY=http://proxy.company.com:8080
   HTTPS_PROXY=http://proxy.company.com:8080
   ```

### 3. 数据处理问题

#### 问题: 文件解析失败

**症状**:
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**解决方案**:
1. 验证文件格式:
   ```python
   import json
   
   def validate_ndjson_file(file_path):
       try:
           with open(file_path, 'r', encoding='utf-8') as f:
               for line_num, line in enumerate(f, 1):
                   if line.strip():
                       json.loads(line)
           print("文件格式正确")
           return True
       except json.JSONDecodeError as e:
           print(f"第{line_num}行JSON格式错误: {e}")
           return False
   ```

2. 检查文件编码:
   ```python
   import chardet
   
   def detect_encoding(file_path):
       with open(file_path, 'rb') as f:
           result = chardet.detect(f.read())
       return result['encoding']
   ```

3. 修复常见格式问题:
   ```python
   def fix_ndjson_format(input_file, output_file):
       with open(input_file, 'r', encoding='utf-8') as infile, \
            open(output_file, 'w', encoding='utf-8') as outfile:
           for line in infile:
               line = line.strip()
               if line and not line.endswith(','):
                   try:
                       json.loads(line)
                       outfile.write(line + '\n')
                   except json.JSONDecodeError:
                       continue
   ```

#### 问题: 内存不足

**症状**:
```
MemoryError: Unable to allocate array
```

**解决方案**:
1. 减少数据处理块大小:
   ```env
   CHUNK_SIZE=5000
   ```

2. 启用数据分块处理:
   ```python
   def process_large_file_in_chunks(file_path, chunk_size=10000):
       for chunk in pd.read_json(file_path, lines=True, chunksize=chunk_size):
           # 处理数据块
           yield process_chunk(chunk)
           # 强制垃圾回收
           import gc
           gc.collect()
   ```

3. 监控内存使用:
   ```python
   import psutil
   import os
   
   def monitor_memory():
       process = psutil.Process(os.getpid())
       memory_info = process.memory_info()
       print(f"内存使用: {memory_info.rss / 1024 / 1024:.2f} MB")
   ```

### 4. CrewAI智能体问题

#### 问题: 智能体初始化失败

**症状**:
```
ImportError: No module named 'crewai'
```

**解决方案**:
1. 安装CrewAI:
   ```bash
   pip install crewai
   ```

2. 检查版本兼容性:
   ```python
   import crewai
   print(f"CrewAI版本: {crewai.__version__}")
   ```

3. 使用备用模式:
   ```python
   try:
       from crewai import Agent
       CREWAI_AVAILABLE = True
   except ImportError:
       CREWAI_AVAILABLE = False
       # 使用standalone模式
   ```

#### 问题: 智能体执行超时

**症状**:
```
TimeoutError: Agent execution timed out
```

**解决方案**:
1. 增加执行超时时间:
   ```python
   from config.crew_config import create_agent
   
   agent = create_agent('event_analyst')
   agent.max_execution_time = 300  # 5分钟
   ```

2. 优化任务描述:
   ```python
   # 避免过于复杂的任务描述
   task_description = "分析用户事件频次，重点关注top 10事件"
   # 而不是
   # task_description = "进行全面深入的用户行为事件分析，包括但不限于..."
   ```

### 5. 可视化问题

#### 问题: 图表显示异常

**症状**:
- 图表不显示
- 数据点重叠
- 坐标轴标签乱码

**解决方案**:
1. 检查数据格式:
   ```python
   def validate_chart_data(data):
       # 检查必需列
       required_columns = ['x', 'y']
       missing_columns = [col for col in required_columns if col not in data.columns]
       if missing_columns:
           raise ValueError(f"缺少必需列: {missing_columns}")
       
       # 检查数据类型
       if not pd.api.types.is_numeric_dtype(data['y']):
           raise ValueError("Y轴数据必须为数值类型")
   ```

2. 处理中文字体问题:
   ```python
   import plotly.graph_objects as go
   
   fig = go.Figure()
   fig.update_layout(
       font=dict(family="SimHei, Arial Unicode MS, sans-serif")
   )
   ```

3. 优化大数据集显示:
   ```python
   def optimize_large_dataset(data, max_points=10000):
       if len(data) > max_points:
           # 采样数据
           return data.sample(n=max_points)
       return data
   ```

### 6. 性能问题

#### 问题: 分析速度慢

**症状**:
- 分析任务执行时间过长
- 界面响应缓慢

**解决方案**:
1. 启用并行处理:
   ```env
   ENABLE_PARALLEL_PROCESSING=true
   MAX_WORKERS=4
   ```

2. 使用缓存:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_analysis(data_hash):
       # 耗时分析逻辑
       pass
   ```

3. 数据库索引优化:
   ```sql
   CREATE INDEX idx_event_timestamp ON events(event_timestamp);
   CREATE INDEX idx_user_id ON events(user_pseudo_id);
   ```

#### 问题: 磁盘空间不足

**症状**:
```
OSError: [Errno 28] No space left on device
```

**解决方案**:
1. 清理临时文件:
   ```bash
   find ./data/temp -type f -mtime +7 -delete
   find ./logs -name "*.log.*" -mtime +30 -delete
   ```

2. 启用自动清理:
   ```env
   CLEANUP_TEMP_FILES=true
   LOG_ROTATION=true
   MAX_LOG_SIZE_MB=100
   ```

3. 监控磁盘使用:
   ```python
   import shutil
   
   def check_disk_space(path='.'):
       total, used, free = shutil.disk_usage(path)
       free_gb = free / (1024**3)
       if free_gb < 1:  # 少于1GB
           print(f"警告: 磁盘空间不足，剩余 {free_gb:.2f} GB")
   ```

## 🔍 诊断工具

### 系统健康检查

```python
def system_health_check():
    """系统健康检查"""
    checks = {
        'python_version': check_python_version(),
        'dependencies': check_dependencies(),
        'api_connection': check_api_connection(),
        'disk_space': check_disk_space(),
        'memory_usage': check_memory_usage(),
        'config_validity': check_config_validity()
    }
    
    print("=== 系统健康检查报告 ===")
    for check_name, result in checks.items():
        status = "✅ 正常" if result['status'] else "❌ 异常"
        print(f"{check_name}: {status}")
        if not result['status']:
            print(f"  错误: {result['error']}")
            print(f"  建议: {result['suggestion']}")

def check_python_version():
    import sys
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        return {'status': True}
    else:
        return {
            'status': False,
            'error': f'Python版本 {version.major}.{version.minor} 不支持',
            'suggestion': '请升级到Python 3.8或更高版本'
        }
```

### 日志分析工具

```python
def analyze_error_logs(log_file='logs/app.log', hours=24):
    """分析错误日志"""
    import re
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    error_patterns = {
        'api_errors': r'API.*ERROR',
        'memory_errors': r'MemoryError|OutOfMemoryError',
        'timeout_errors': r'TimeoutError|timeout',
        'json_errors': r'JSONDecodeError',
        'import_errors': r'ImportError|ModuleNotFoundError'
    }
    
    error_counts = {pattern: 0 for pattern in error_patterns}
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                # 检查时间戳
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    log_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                    if log_time < cutoff_time:
                        continue
                
                # 检查错误模式
                for pattern_name, pattern in error_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        error_counts[pattern_name] += 1
    
    except FileNotFoundError:
        print(f"日志文件 {log_file} 不存在")
        return
    
    print(f"=== 最近{hours}小时错误统计 ===")
    for error_type, count in error_counts.items():
        if count > 0:
            print(f"{error_type}: {count} 次")
```

### 性能监控

```python
import time
import psutil
from contextlib import contextmanager

@contextmanager
def performance_monitor(operation_name):
    """性能监控上下文管理器"""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    try:
        yield
    finally:
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        duration = end_time - start_time
        memory_delta = end_memory - start_memory
        
        print(f"=== {operation_name} 性能报告 ===")
        print(f"执行时间: {duration:.2f} 秒")
        print(f"内存变化: {memory_delta:+.2f} MB")
        print(f"当前内存: {end_memory:.2f} MB")

# 使用示例
with performance_monitor("事件分析"):
    # 执行分析操作
    results = analyze_events()
```

## 📞 获取帮助

### 日志文件位置

- **应用日志**: `logs/app.log`
- **分析日志**: `logs/analytics.log`
- **错误日志**: `logs/error.log`
- **CrewAI日志**: `logs/crewai.log`

### 配置文件位置

- **环境变量**: `.env`
- **系统配置**: `config/system_config.json`
- **分析配置**: `config/analysis_config.json`
- **Streamlit配置**: `.streamlit/config.toml`

### 联系支持

1. **查看文档**: 首先查看用户指南和API文档
2. **检查日志**: 查看相关日志文件获取详细错误信息
3. **运行诊断**: 使用系统健康检查工具
4. **提交Issue**: 在GitHub仓库提交详细的问题报告
5. **联系开发团队**: 发送邮件至技术支持邮箱

### 问题报告模板

```
**问题描述**
简要描述遇到的问题

**环境信息**
- 操作系统: 
- Python版本: 
- 平台版本: 
- 浏览器 (如适用): 

**重现步骤**
1. 
2. 
3. 

**期望行为**
描述期望的正常行为

**实际行为**
描述实际发生的异常行为

**错误信息**
粘贴完整的错误信息和堆栈跟踪

**相关日志**
粘贴相关的日志片段

**配置信息**
相关的配置设置 (请隐藏敏感信息如API密钥)

**其他信息**
任何其他可能有助于诊断问题的信息
```

---

*本配置和故障排除指南持续更新中，如有新的问题或解决方案，欢迎贡献。*