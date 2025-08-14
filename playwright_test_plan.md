# Playwright MCP 语言切换功能测试计划

## 测试目标
验证Docker容器中部署的用户行为分析平台语言切换功能是否正常工作。

## 测试环境
- **容器地址**: http://localhost:8501
- **测试工具**: Playwright MCP
- **测试语言**: 中文 (zh-CN) ↔ 英文 (en-US)

## 测试步骤

### 1. 环境准备
```bash
# 启动Docker容器
docker-compose up -d

# 验证容器状态
docker-compose ps

# 检查应用可访问性
curl http://localhost:8501
```

### 2. Playwright MCP测试流程

#### 步骤1: 导航到应用
- **操作**: 使用Playwright访问 `http://localhost:8501`
- **验证**: 页面正常加载，显示Streamlit界面

#### 步骤2: 验证默认语言（中文）
- **操作**: 检查页面主要元素文本
- **预期结果**:
  - 页面标题: "用户行为分析智能体平台"
  - 功能导航: "🚀 功能导航"
  - 模块选择: "选择功能模块"

#### 步骤3: 进入系统设置
- **操作**: 在下拉菜单中选择"⚙️ 系统设置"
- **验证**: 成功进入系统设置页面

#### 步骤4: 切换到英文
- **操作**: 
  1. 找到"界面语言"选择器
  2. 选择"English"选项
  3. 点击"💾 保存系统配置"按钮
- **验证**: 
  - 显示保存成功消息
  - 页面元素开始更新为英文

#### 步骤5: 验证英文界面
- **操作**: 检查主要元素是否已切换为英文
- **预期结果**:
  - 页面标题: "User Behavior Analytics Platform"
  - 功能导航: "🚀 Navigation"
  - 模块选择: "Select Module"
  - 系统设置: "⚙️ System Settings"

#### 步骤6: 切换回中文
- **操作**:
  1. 在英文界面中找到"Interface Language"
  2. 选择"中文"选项
  3. 点击"💾 Save System Configuration"
- **验证**: 界面切换回中文显示

#### 步骤7: 验证中文恢复
- **操作**: 检查所有元素是否恢复中文显示
- **预期结果**: 所有文本元素恢复为中文版本

## 关键验证点

### 中文界面元素
| 元素类型 | 中文文本 |
|---------|---------|
| 应用标题 | 用户行为分析智能体平台 |
| 功能导航 | 🚀 功能导航 |
| 模块选择 | 选择功能模块 |
| 数据上传 | 📁 数据上传 |
| 智能分析 | 🚀 智能分析 |
| 系统设置 | ⚙️ 系统设置 |
| 界面语言 | 界面语言 |
| 保存配置 | 💾 保存系统配置 |

### 英文界面元素  
| 元素类型 | 英文文本 |
|---------|---------|
| 应用标题 | User Behavior Analytics Platform |
| 功能导航 | 🚀 Navigation |
| 模块选择 | Select Module |
| 数据上传 | 📁 Data Upload |
| 智能分析 | 🚀 Intelligent Analysis |
| 系统设置 | ⚙️ System Settings |
| 界面语言 | Interface Language |
| 保存配置 | 💾 Save System Configuration |

## Playwright MCP命令示例

### 基础操作
```
# 导航到应用
browser_navigate(url="http://localhost:8501")

# 获取页面快照
browser_snapshot()

# 点击下拉菜单
browser_click(element="选择功能模块下拉菜单", ref="selectbox_ref")

# 选择选项
browser_select_option(element="模块选择器", ref="selectbox_ref", values=["⚙️ 系统设置"])

# 输入文本
browser_type(element="语言选择器", ref="language_ref", text="English")

# 点击按钮
browser_click(element="保存按钮", ref="save_button_ref")
```

### 验证检查
```
# 检查文本内容
browser_evaluate(function="() => document.title")
browser_evaluate(function="() => document.querySelector('h1').textContent")

# 等待元素出现
browser_wait_for(text="保存成功")

# 截图验证
browser_take_screenshot(filename="language_switch_test.png")
```

## 成功标准
1. ✅ 应用能够正常加载和访问
2. ✅ 默认显示中文界面
3. ✅ 能够成功进入系统设置页面
4. ✅ 语言切换功能正常工作
5. ✅ 英文界面所有关键元素正确显示
6. ✅ 能够切换回中文界面
7. ✅ 语言切换后配置能够保存
8. ✅ 页面刷新后语言设置保持

## 可能的问题排查

### Docker相关
- 容器是否正常启动: `docker-compose ps`
- 应用日志: `docker-compose logs -f analytics-platform`
- 端口是否可访问: `curl http://localhost:8501`

### i18n系统相关
- 语言文件是否存在: 检查 `languages/` 目录
- 配置文件是否正确: 检查 `config/system_config.json`
- i18n系统是否正常加载: 查看应用启动日志

### Playwright相关
- 浏览器是否正常安装: `browser_install`
- 页面是否正常渲染: `browser_snapshot`
- 元素选择器是否正确: 检查页面结构