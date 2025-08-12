#!/usr/bin/env python3
"""
应用启动脚本
确保提供商健康后启动 Streamlit 应用
"""

import subprocess
import sys
import time
from config.llm_provider_manager import get_provider_manager, reset_provider_manager
from config.crew_config import get_llm

def check_and_fix_providers():
    """检查并修复提供商状态"""
    print("🔧 检查提供商状态...")
    
    try:
        # 重置提供商管理器
        reset_provider_manager()
        
        # 获取新的管理器实例
        manager = get_provider_manager()
        
        # 强制执行健康检查
        health_results = manager.force_health_check()
        
        print("📊 提供商健康状态:")
        healthy_providers = []
        
        for provider, result in health_results.items():
            status = result.status if isinstance(result.status, str) else result.status.value
            if status in ["available", "degraded"]:
                healthy_providers.append(provider)
                print(f"  ✅ {provider}: {status}")
            else:
                print(f"  ❌ {provider}: {status}")
                if result.error_message:
                    print(f"     错误: {result.error_message}")
        
        if not healthy_providers:
            print("❌ 没有可用的提供商，请检查配置")
            return False
        
        # 测试默认提供商
        print(f"\n🧪 测试默认提供商...")
        try:
            llm = get_llm()
            response = llm.invoke("Hello")
            print(f"✅ 默认提供商测试成功，响应长度: {len(response)}")
        except Exception as e:
            print(f"⚠️  默认提供商测试失败: {e}")
            # 尝试使用第一个健康的提供商
            if healthy_providers:
                try:
                    llm = get_llm(provider=healthy_providers[0])
                    response = llm.invoke("Hello")
                    print(f"✅ 使用 {healthy_providers[0]} 提供商成功")
                except Exception as e2:
                    print(f"❌ 备用提供商也失败: {e2}")
                    return False
        
        print(f"🎉 提供商检查完成，可用提供商: {healthy_providers}")
        return True
        
    except Exception as e:
        print(f"❌ 提供商检查失败: {e}")
        return False

def start_streamlit():
    """启动 Streamlit 应用"""
    print("\n🚀 启动 Streamlit 应用...")
    print("📝 应用将在 http://localhost:8501 启动")
    print("⏹️  按 Ctrl+C 停止应用")
    
    try:
        # 启动 Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "main.py", 
               "--server.port", "8501", 
               "--server.headless", "true",
               "--server.enableCORS", "false"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动应用失败: {e}")

def main():
    """主函数"""
    print("🎯 用户行为分析平台启动器")
    print("=" * 50)
    
    # 检查提供商状态
    if not check_and_fix_providers():
        print("\n❌ 提供商检查失败，无法启动应用")
        print("请检查:")
        print("1. API 密钥是否正确配置")
        print("2. 网络连接是否正常")
        print("3. 提供商服务是否可用")
        sys.exit(1)
    
    # 等待一下确保状态稳定
    print("\n⏳ 等待提供商状态稳定...")
    time.sleep(2)
    
    # 启动应用
    start_streamlit()

if __name__ == "__main__":
    main()