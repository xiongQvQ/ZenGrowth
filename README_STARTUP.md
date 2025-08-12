# 用户行为分析平台启动指南

## 🚀 快速启动

### 方法1：使用启动脚本（推荐）
```bash
# 激活虚拟环境
source venv/bin/activate

# 使用启动脚本（会自动检查提供商状态）
python start_app.py
```

### 方法2：直接启动 Streamlit
```bash
# 激活虚拟环境
source venv/bin/activate

# 直接启动（如果遇到提供商问题，先运行修复脚本）
streamlit run main.py
```

## 🔧 故障排除

### 如果遇到"提供商不健康"错误：

1. **运行修复脚本**：
```bash
source venv/bin/activate
python fix_providers_runtime.py
```

2. **检查配置**：
```bash
source venv/bin/activate
python debug_providers.py
```

3. **测试LLM**：
```bash
source venv/bin/activate
python test_simple_llm.py
```

### 如果遇到数据问题：

1. **检查数据状态**：
```bash
source venv/bin/activate
python check_data_status.py
```

2. **生成测试数据**：
```bash
source venv/bin/activate
python generate_clean_data.py
```

3. **测试留存分析**：
```bash
source venv/bin/activate
python test_retention_quick.py
```

## 📊 功能说明

### 已修复的功能：
- ✅ **LLM 提供商**：Volcano 和 Google（地区限制）
- ✅ **数据处理**：GA4 数据解析和存储
- ✅ **留存分析**：用户队列构建和留存率计算
- ✅ **配置管理**：最小队列大小已调整为合理值

### 可用的分析功能：
- 📊 **事件分析**：用户行为事件统计和趋势
- 📈 **留存分析**：用户留存率和队列分析
- 🔄 **转化分析**：转化漏斗和路径分析
- 👥 **用户分群**：基于行为的用户聚类
- 🛤️ **路径分析**：用户行为路径挖掘

## 🎯 使用流程

1. **启动应用**：使用 `python start_app.py`
2. **上传数据**：在"数据上传"页面上传 GA4 NDJSON 文件
3. **选择分析**：从侧边栏选择需要的分析功能
4. **查看结果**：分析结果会以图表和报告形式展示
5. **导出报告**：可以导出分析结果为 JSON、PDF 或 Excel

## 📝 注意事项

- 确保 API 密钥在 `.env` 文件中正确配置
- 数据文件需要符合 GA4 NDJSON 格式
- 留存分析需要至少10个用户的数据
- 应用默认在 http://localhost:8501 启动

## 🆘 获取帮助

如果遇到问题，请：
1. 检查终端输出的错误信息
2. 运行相应的故障排除脚本
3. 查看日志文件（如果有）
4. 确保所有依赖包已正确安装