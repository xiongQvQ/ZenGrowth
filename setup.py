"""
项目安装和设置脚本
"""

import os
import sys
import subprocess
from pathlib import Path


def create_virtual_environment():
    """创建Python虚拟环境"""
    print("🔧 创建Python虚拟环境...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ 虚拟环境已存在")
        return
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ 虚拟环境创建成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 虚拟环境创建失败: {e}")
        sys.exit(1)


def install_dependencies():
    """安装项目依赖"""
    print("📦 安装项目依赖...")
    
    # 确定pip路径
    if os.name == "nt":  # Windows
        pip_path = Path("venv/Scripts/pip")
    else:  # Unix/Linux/macOS
        pip_path = Path("venv/bin/pip")
    
    try:
        subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
        print("✅ 依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        sys.exit(1)


def setup_environment_file():
    """设置环境变量文件"""
    print("⚙️ 设置环境配置...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")
        print("✅ 已创建.env配置文件，请编辑其中的API密钥")
    else:
        print("ℹ️ .env文件已存在或.env.example不存在")


def create_directories():
    """创建必要的目录"""
    print("📁 创建项目目录...")
    
    directories = ["logs", "data/uploads", "data/processed", "reports"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ 项目目录创建完成")


def main():
    """主设置函数"""
    print("🚀 开始设置用户行为分析智能体平台...")
    print("=" * 50)
    
    create_virtual_environment()
    install_dependencies()
    setup_environment_file()
    create_directories()
    
    print("=" * 50)
    print("✅ 项目设置完成！")
    print("\n📋 下一步操作:")
    print("1. 编辑.env文件，设置GOOGLE_API_KEY")
    print("2. 激活虚拟环境:")
    if os.name == "nt":
        print("   Windows: venv\\Scripts\\activate")
    else:
        print("   Unix/Linux/macOS: source venv/bin/activate")
    print("3. 运行应用: streamlit run main.py")


if __name__ == "__main__":
    main()