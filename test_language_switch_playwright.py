#!/usr/bin/env python3
"""
使用Playwright MCP验证语言切换功能
验证Docker容器中的应用语言切换是否正常工作
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_language_switching_e2e():
    """端到端语言切换测试"""
    print("🎭 启动Playwright MCP端到端语言切换测试...")
    
    # 应用URL（Docker容器运行地址）
    app_url = "http://localhost:8501"
    
    print(f"📍 测试目标: {app_url}")
    print("🔍 测试步骤:")
    print("1. 访问应用主页")
    print("2. 验证初始语言（中文）")
    print("3. 进入系统设置页面")
    print("4. 切换到英文")
    print("5. 验证界面语言切换效果")
    print("6. 切换回中文")
    print("7. 验证界面恢复中文")
    
    return {
        "test_name": "language_switching_e2e",
        "app_url": app_url,
        "steps": [
            "navigate_to_app",
            "verify_chinese_default",
            "open_system_settings", 
            "switch_to_english",
            "verify_english_ui",
            "switch_to_chinese",
            "verify_chinese_ui"
        ],
        "expected_elements": {
            "chinese": {
                "title": "用户行为分析智能体平台",
                "navigation": "🚀 功能导航", 
                "select_module": "选择功能模块",
                "data_upload": "📁 数据上传",
                "system_settings": "⚙️ 系统设置",
                "interface_language": "界面语言",
                "save_config": "💾 保存系统配置"
            },
            "english": {
                "title": "User Behavior Analytics Platform",
                "navigation": "🚀 Navigation",
                "select_module": "Select Module", 
                "data_upload": "📁 Data Upload",
                "system_settings": "⚙️ System Settings",
                "interface_language": "Interface Language",
                "save_config": "💾 Save System Configuration"
            }
        }
    }

async def wait_for_docker_ready():
    """等待Docker容器启动就绪"""
    print("⏳ 等待Docker容器启动...")
    
    import requests
    max_wait = 120  # 最大等待2分钟
    wait_interval = 5  # 每5秒检查一次
    
    for attempt in range(0, max_wait, wait_interval):
        try:
            response = requests.get("http://localhost:8501", timeout=10)
            if response.status_code == 200:
                print(f"✅ Docker容器已就绪 (等待了 {attempt} 秒)")
                return True
        except Exception as e:
            print(f"⏳ 等待容器就绪... ({attempt}s/{max_wait}s) - {str(e)[:50]}")
            time.sleep(wait_interval)
    
    print(f"❌ 等待超时 ({max_wait}秒)，Docker容器可能启动失败")
    return False

def main():
    """主测试函数"""
    print("🚀 Playwright MCP语言切换测试准备就绪")
    
    # 准备测试配置
    test_config = asyncio.run(test_language_switching_e2e())
    
    print(f"\n📋 测试配置已准备:")
    print(f"- 测试名称: {test_config['test_name']}")
    print(f"- 应用地址: {test_config['app_url']}")
    print(f"- 测试步骤: {len(test_config['steps'])} 个")
    print(f"- 中文元素: {len(test_config['expected_elements']['chinese'])} 个")
    print(f"- 英文元素: {len(test_config['expected_elements']['english'])} 个")
    
    print(f"\n🎯 待验证的关键元素:")
    print("中文版本:")
    for key, value in test_config['expected_elements']['chinese'].items():
        print(f"  {key}: {value}")
    
    print("\n英文版本:")
    for key, value in test_config['expected_elements']['english'].items():
        print(f"  {key}: {value}")
    
    print(f"\n📋 详细测试步骤:")
    for i, step in enumerate(test_config['steps'], 1):
        print(f"  {i}. {step}")
    
    print("\n✅ 测试配置完成，等待Docker容器启动后可使用Playwright MCP执行")
    
    return test_config

if __name__ == "__main__":
    config = main()