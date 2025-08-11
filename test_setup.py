#!/usr/bin/env python3
"""
项目设置验证脚本
验证所有组件是否正确配置
"""

import sys
from pathlib import Path

def test_imports():
    """测试关键模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from config.settings import settings, validate_config
        print("✅ 配置模块导入成功")
        
        from utils.logger import setup_logger
        print("✅ 日志模块导入成功")
        
        from config.crew_config import CrewManager, AGENT_ROLES
        print("✅ CrewAI配置模块导入成功")
        
        return True
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False


def test_directory_structure():
    """测试目录结构"""
    print("\n📁 检查目录结构...")
    
    required_dirs = [
        "agents", "tools", "engines", "ui", "config", "utils",
        "data", "logs", "reports", "data/uploads", "data/processed"
    ]
    
    all_exist = True
    for directory in required_dirs:
        path = Path(directory)
        if path.exists():
            print(f"✅ {directory}/")
        else:
            print(f"❌ {directory}/ - 目录不存在")
            all_exist = False
    
    return all_exist


def test_configuration():
    """测试配置"""
    print("\n⚙️ 检查配置...")
    
    try:
        from config.settings import settings
        
        print(f"✅ 应用标题: {settings.app_title}")
        print(f"✅ LLM模型: {settings.llm_model}")
        print(f"✅ 日志级别: {settings.log_level}")
        
        # 检查.env文件
        env_file = Path(".env")
        env_example = Path(".env.example")
        
        if env_example.exists():
            print("✅ .env.example 文件存在")
        else:
            print("❌ .env.example 文件不存在")
        
        if env_file.exists():
            print("✅ .env 文件存在")
        else:
            print("⚠️ .env 文件不存在，请复制.env.example并配置API密钥")
        
        return True
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False


def test_agent_roles():
    """测试智能体角色配置"""
    print("\n🤖 检查智能体配置...")
    
    try:
        from config.crew_config import AGENT_ROLES
        
        expected_agents = [
            "data_processor", "event_analyst", "retention_analyst",
            "conversion_analyst", "segmentation_analyst", "path_analyst",
            "report_generator"
        ]
        
        all_exist = True
        for agent in expected_agents:
            if agent in AGENT_ROLES:
                print(f"✅ {AGENT_ROLES[agent]['role']}")
            else:
                print(f"❌ {agent} - 智能体配置缺失")
                all_exist = False
        
        return all_exist
    except Exception as e:
        print(f"❌ 智能体配置检查失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 用户行为分析智能体平台 - 设置验证")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("目录结构", test_directory_structure), 
        ("系统配置", test_configuration),
        ("智能体配置", test_agent_roles)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 所有测试通过！项目设置完成。")
        print("\n📋 下一步:")
        print("1. 编辑.env文件，设置GOOGLE_API_KEY")
        print("2. 运行: streamlit run main.py")
        return 0
    else:
        print("❌ 部分测试失败，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())