#!/bin/bash

echo "🚀 启动Docker容器和语言切换测试"
echo "=================================="

# 1. 启动容器
echo "📦 启动Docker容器..."
docker-compose up -d

# 2. 等待容器启动
echo "⏳ 等待容器启动完成..."
sleep 10

# 3. 检查容器状态
echo "🔍 检查容器状态..."
docker-compose ps

# 4. 检查容器日志
echo "📋 检查应用启动日志..."
docker-compose logs --tail=20 analytics-platform

# 5. 快速健康检查
echo "🏥 运行健康检查..."
python quick_test.py

# 6. 提示开始Playwright测试
echo ""
echo "✅ 容器启动完成！"
echo "🎭 现在可以使用Playwright MCP进行语言切换测试"
echo ""
echo "📋 测试步骤:"
echo "1. 访问: http://localhost:8501"
echo "2. 验证中文界面"
echo "3. 切换到系统设置"
echo "4. 修改语言为英文"
echo "5. 验证英文界面"
echo "6. 切换回中文"
echo ""
echo "🔧 Playwright MCP命令参考:"
echo "browser_navigate(url='http://localhost:8501')"
echo "browser_snapshot()"
echo "browser_click(element='下拉菜单', ref='selectbox_ref')"