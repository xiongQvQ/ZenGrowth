#!/usr/bin/env python3
"""
简化的应用启动脚本
跳过可能有问题的健康检查，直接启动应用
"""

import subprocess
import sys
from config.crew_config import get_llm

def quick_test():
    """快速测试 LLM 是否可用"""
    try:
        print("🧪 快速测试 LLM...")
        llm = get_llm()
        response = llm.invoke("Test")
        print(f"✅ LLM 测试成功，响应长度: {len(response)}")
        return True
    except Exception as e:
        print(f"❌ LLM 测试失败: {e}")
        return False

def start_streamlit():
    """启动 Streamlit 应用"""
    print("🚀 启动 Streamlit 应用...")
    print("📝 应用将在 http://localhost:8501 启动")
    print("⏹️  按 Ctrl+C 停止应用")
    print()
    
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "main.py", "--server.port", "8501"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

def main():
    print("🎯 用户行为分析平台 - 简化启动器")
    print("=" * 50)
    
    # 快速测试
    if not quick_test():
        print("\n⚠️  LLM 测试失败，但仍然尝试启动应用")
        print("💡 如果应用中出现提供商错误，请检查 .env 配置")
    
    print("\n" + "=" * 50)
    
    # 启动应用
    start_streamlit()

if __name__ == "__main__":
    main()