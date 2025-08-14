#!/usr/bin/env python3
"""
快速验证Docker容器启动状态
"""

import requests
import time
import sys

def check_container_health():
    """检查容器健康状态"""
    print("🔍 检查Docker容器状态...")
    
    max_attempts = 24  # 最多等待2分钟
    for attempt in range(max_attempts):
        try:
            print(f"⏳ 尝试连接应用... ({attempt + 1}/{max_attempts})")
            response = requests.get("http://localhost:8501", timeout=5)
            
            if response.status_code == 200:
                print("✅ 容器已启动并可访问!")
                print(f"📊 响应状态: {response.status_code}")
                print(f"📏 响应大小: {len(response.text)} 字符")
                
                # 检查是否包含i18n相关内容
                if "用户行为分析智能体平台" in response.text:
                    print("🇨🇳 发现中文内容 - i18n系统可能正常工作")
                
                if "streamlit" in response.text.lower():
                    print("📱 Streamlit应用正常运行")
                
                return True
                
        except requests.exceptions.ConnectionError:
            print(f"🔄 连接失败，等待中... ({attempt + 1}/{max_attempts})")
            time.sleep(5)
        except Exception as e:
            print(f"❌ 检查失败: {str(e)}")
            time.sleep(5)
    
    print("❌ 容器未能正常启动或无法访问")
    return False

def main():
    print("🚀 Docker容器快速检查工具")
    print("=" * 50)
    
    if check_container_health():
        print("\n✅ 容器检查通过，可以开始Playwright测试!")
        return True
    else:
        print("\n❌ 容器检查失败，请检查Docker状态")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)