# 用户行为分析智能体平台

基于CrewAI多智能体框架的自动化用户行为分析系统，集成Google Gemini-2.5-pro模型，提供智能化的GA4数据分析和业务洞察。

## 🚀 功能特性

- **多智能体协作**: 基于CrewAI框架的专业化AI智能体团队
- **全面分析**: 事件分析、留存分析、转化分析、用户分群、路径分析
- **智能洞察**: 集成Google Gemini-2.5-pro生成业务建议和优化方案
- **可视化展示**: 基于Streamlit和Plotly的交互式数据可视化
- **易于扩展**: 模块化设计，支持插件式功能扩展

## 📋 系统要求

- Python 3.8+
- Google Gemini API密钥
- 8GB+ RAM (推荐)
- 2GB+ 可用磁盘空间

## 🛠️ 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd user-behavior-analytics-platform
```

### 2. 自动化设置
```bash
python setup.py
```

### 3. 配置API密钥
编辑 `.env` 文件，设置你的Google Gemini API密钥：
```env
GOOGLE_API_KEY=your_google_api_key_here
```

### 4. 激活虚拟环境
```bash
# Windows
venv\Scripts\activate

# Unix/Linux/macOS
source venv/bin/activate
```

### 5. 启动应用
```bash
streamlit run main.py
```

## 📁 项目结构

```
user-behavior-analytics-platform/
├── agents/                 # CrewAI智能体模块
├── tools/                  # 分析工具模块
├── engines/                # 分析引擎模块
├── ui/                     # 用户界面模块
├── config/                 # 配置管理模块
├── utils/                  # 工具函数模块
├── data/                   # 数据存储目录
├── logs/                   # 日志文件目录
├── reports/                # 报告输出目录
├── main.py                 # 主应用入口
├── requirements.txt        # 项目依赖
├── setup.py               # 安装设置脚本
└── README.md              # 项目说明
```

## 🔧 配置说明

### 环境变量配置
在 `.env` 文件中可配置以下参数：

```env
# 必需配置
GOOGLE_API_KEY=your_api_key

# 可选配置
LLM_MODEL=gemini-2.5-pro
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
APP_TITLE=用户行为分析智能体平台
LOG_LEVEL=INFO
```

### 系统配置
在 `config/settings.py` 中可调整：
- 数据处理参数
- 分析算法配置
- 可视化设置
- 日志配置

## 📊 使用指南

1. **数据上传**: 上传GA4 NDJSON格式的事件数据文件
2. **选择分析**: 从侧边栏选择需要的分析功能
3. **查看结果**: 在主界面查看分析结果和可视化图表
4. **导出报告**: 将分析结果导出为PDF、Excel或JSON格式

## 🤖 智能体说明

- **数据处理智能体**: 负责GA4数据解析和预处理
- **事件分析智能体**: 分析用户事件模式和趋势
- **留存分析智能体**: 计算用户留存率和流失分析
- **转化分析智能体**: 构建转化漏斗和瓶颈识别
- **用户分群智能体**: 基于行为特征进行用户分群
- **路径分析智能体**: 分析用户行为路径和导航模式
- **报告生成智能体**: 汇总结果并生成综合报告

## 🔍 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `.env` 文件中的 `GOOGLE_API_KEY` 设置
   - 确认API密钥有效且有足够配额

2. **依赖安装失败**
   - 确保Python版本3.8+
   - 尝试升级pip: `pip install --upgrade pip`

3. **内存不足**
   - 减少 `chunk_size` 配置参数
   - 处理较小的数据文件

4. **端口占用**
   - 使用不同端口启动: `streamlit run main.py --server.port 8502`

## 📚 详细文档

本README提供了快速开始指南。如需更详细的信息，请查阅我们的完整文档：

- **[📖 用户使用指南](docs/USER_GUIDE.md)** - 详细的功能说明和使用方法
- **[🔧 API文档和开发者指南](docs/API_DOCUMENTATION.md)** - 完整的API参考和开发指南
- **[⚙️ 配置说明和故障排除指南](docs/CONFIGURATION_TROUBLESHOOTING.md)** - 系统配置和问题解决
- **[💡 示例和最佳实践文档](docs/EXAMPLES_BEST_PRACTICES.md)** - 实际使用案例和最佳实践

### 快速导航
- 🚀 **新用户**: 从[用户使用指南](docs/USER_GUIDE.md)开始
- 👨‍💻 **开发者**: 查看[API文档](docs/API_DOCUMENTATION.md)
- 🔧 **管理员**: 参考[配置指南](docs/CONFIGURATION_TROUBLESHOOTING.md)
- 📊 **分析师**: 学习[最佳实践](docs/EXAMPLES_BEST_PRACTICES.md)

## 📝 开发说明

详细的开发指南请参考[API文档和开发者指南](docs/API_DOCUMENTATION.md#🔌-扩展开发)。

### 快速开发指引
1. **添加新智能体**: 参考[自定义智能体开发](docs/API_DOCUMENTATION.md#智能体创建和配置)
2. **扩展分析功能**: 查看[添加新的分析引擎](docs/API_DOCUMENTATION.md#添加新的分析引擎)
3. **自定义可视化**: 学习[添加新的可视化组件](docs/API_DOCUMENTATION.md#添加新的可视化组件)

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！贡献指南请参考[开发者文档](docs/API_DOCUMENTATION.md)。

## 📞 支持

如有问题或建议，请通过以下方式联系：
- 📖 **查看文档**: 首先查阅[文档中心](docs/README.md)
- 🐛 **提交Issue**: 在GitHub仓库提交详细的问题报告
- 💬 **社区讨论**: 参与GitHub Discussions
- 📧 **邮件支持**: 联系项目维护者

### 问题排查顺序
1. 查看[故障排除指南](docs/CONFIGURATION_TROUBLESHOOTING.md)
2. 检查[常见问题](docs/CONFIGURATION_TROUBLESHOOTING.md#常见问题及解决方案)
3. 使用[诊断工具](docs/CONFIGURATION_TROUBLESHOOTING.md#🔍-诊断工具)
4. 提交详细的Issue报告