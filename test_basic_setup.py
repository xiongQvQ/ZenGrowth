#!/usr/bin/env python3
"""
基础项目设置验证脚本
验证基本组件是否正确配置（不依赖外部库）
"""

import sys
from pathlib import Path

def test_directory_structure():
    """测试目录结构"""
    print("📁 检查目录结构...")
    
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


def test_required_files():
    """测试必需文件"""
    print("\n📄 检查必需文件...")
    
    required_files = [
        "main.py",
        "requirements.txt", 
        "setup.py",
        "README.md",
        ".env.example",
        "config/settings.py",
        "config/crew_config.py",
        "utils/logger.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 文件不存在")
            all_exist = False
    
    return all_exist


def test_basic_config():
    """测试基础配置（不导入外部依赖）"""
    print("\n⚙️ 检查基础配置...")
    
    try:
        # 检查.env.example内容
        env_example = Path(".env.example")
        if env_example.exists():
            content = env_example.read_text()
            if "GOOGLE_API_KEY" in content:
                print("✅ .env.example 包含API密钥配置")
            else:
                print("❌ .env.example 缺少API密钥配置")
                return False
        
        # 检查requirements.txt内容
        requirements = Path("requirements.txt")
        if requirements.exists():
            content = requirements.read_text()
            required_packages = ["crewai", "streamlit", "pandas", "plotly"]
            missing = []
            for package in required_packages:
                if package not in content:
                    missing.append(package)
            
            if not missing:
                print("✅ requirements.txt 包含所有必需依赖")
            else:
                print(f"❌ requirements.txt 缺少依赖: {missing}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ 基础配置检查失败: {e}")
        return False


def test_module_structure():
    """测试模块结构"""
    print("\n🐍 检查Python模块结构...")
    
    modules = ["agents", "tools", "engines", "ui", "config", "utils"]
    all_valid = True
    
    for module in modules:
        init_file = Path(module) / "__init__.py"
        if init_file.exists():
            print(f"✅ {module}/__init__.py")
        else:
            print(f"❌ {module}/__init__.py - 文件不存在")
            all_valid = False
    
    return all_valid


def main():
    """主测试函数"""
    print("🚀 用户行为分析智能体平台 - 基础设置验证")
    print("=" * 50)
    
    tests = [
        ("目录结构", test_directory_structure),
        ("必需文件", test_required_files),
        ("基础配置", test_basic_config),
        ("模块结构", test_module_structure)
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
        print("🎉 基础设置验证通过！")
        print("\n📋 下一步:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 复制配置: cp .env.example .env")
        print("3. 编辑.env文件，设置GOOGLE_API_KEY")
        print("4. 运行应用: streamlit run main.py")
        return 0
    else:
        print("❌ 基础设置验证失败，请检查上述错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())