# 项目结构说明

## 📁 目录结构

```
user-behavior-analytics-platform/
├── .kiro/                          # Kiro IDE配置目录
│   └── specs/                      # 项目规格文档
│       └── user-behavior-analytics-platform/
│           ├── requirements.md     # 需求文档
│           ├── design.md          # 设计文档
│           └── tasks.md           # 任务列表
│
├── agents/                         # CrewAI智能体模块
│   └── __init__.py                # 智能体模块初始化
│
├── tools/                          # 分析工具模块
│   └── __init__.py                # 工具模块初始化
│
├── engines/                        # 分析引擎模块
│   └── __init__.py                # 引擎模块初始化
│
├── ui/                            # 用户界面模块
│   └── __init__.py                # UI模块初始化
│
├── config/                        # 配置管理模块
│   ├── __init__.py               # 配置模块初始化
│   ├── settings.py               # 系统配置管理
│   └── crew_config.py            # CrewAI智能体配置
│
├── utils/                         # 工具函数模块
│   ├── __init__.py               # 工具模块初始化
│   └── logger.py                 # 日志配置工具
│
├── data/                          # 数据存储目录
│   ├── uploads/                  # 上传文件存储
│   ├── processed/                # 处理后数据存储
│   └── events_ga4.ndjson         # 示例GA4数据文件
│
├── logs/                          # 日志文件目录
├── reports/                       # 报告输出目录
│
├── main.py                        # 主应用入口文件
├── setup.py                       # 项目安装设置脚本
├── requirements.txt               # Python依赖包列表
├── .env.example                   # 环境变量配置模板
├── README.md                      # 项目说明文档
├── PROJECT_STRUCTURE.md           # 项目结构说明（本文件）
├── test_setup.py                  # 完整设置验证脚本
└── test_basic_setup.py            # 基础设置验证脚本
```

## 🔧 核心文件说明

### 配置文件
- **config/settings.py**: 系统配置管理，包含API密钥、模型参数、分析配置等
- **config/crew_config.py**: CrewAI智能体团队配置，定义智能体角色和协作关系
- **.env.example**: 环境变量配置模板，需要复制为.env并设置实际值

### 应用文件
- **main.py**: Streamlit主应用，提供Web界面和功能导航
- **setup.py**: 自动化项目设置脚本，创建虚拟环境和安装依赖
- **requirements.txt**: Python依赖包列表，包含所有必需的第三方库

### 工具文件
- **utils/logger.py**: 日志配置工具，提供统一的日志记录功能
- **test_basic_setup.py**: 基础设置验证脚本，检查项目结构完整性
- **test_setup.py**: 完整设置验证脚本，测试所有组件功能

## 🚀 快速开始

1. **验证基础设置**:
   ```bash
   python test_basic_setup.py
   ```

2. **自动化安装**:
   ```bash
   python setup.py
   ```

3. **手动安装**:
   ```bash
   # 创建虚拟环境
   python -m venv venv
   
   # 激活虚拟环境
   source venv/bin/activate  # Linux/macOS
   # 或
   venv\Scripts\activate     # Windows
   
   # 安装依赖
   pip install -r requirements.txt
   ```

4. **配置环境**:
   ```bash
   cp .env.example .env
   # 编辑.env文件，设置GOOGLE_API_KEY
   ```

5. **启动应用**:
   ```bash
   streamlit run main.py
   ```

## 📋 开发规划

### 已完成 ✅
- [x] 项目目录结构创建
- [x] 基础配置文件设置
- [x] CrewAI智能体框架配置
- [x] Streamlit应用框架
- [x] 依赖管理和环境配置
- [x] 日志系统配置
- [x] 项目文档和说明

### 待开发 🔄
- [ ] GA4数据解析器实现
- [ ] 各类分析引擎开发
- [ ] CrewAI智能体实现
- [ ] 可视化组件开发
- [ ] Streamlit界面完善
- [ ] 测试用例编写
- [ ] 性能优化

## 🎯 下一步任务

根据 `.kiro/specs/user-behavior-analytics-platform/tasks.md` 中的实施计划，下一步应该执行：

**任务 2.1**: 实现GA4数据解析器
- 编写GA4DataParser类，支持NDJSON格式解析
- 实现事件数据提取和结构化转换功能
- 创建数据验证和清洗工具
- 编写单元测试验证解析准确性