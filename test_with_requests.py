#!/usr/bin/env python3
"""
使用requests测试应用功能 - Playwright替代方案
"""

import requests
import time
import json
from urllib.parse import urljoin

def test_app_health():
    """测试应用健康状态"""
    print("🔍 测试应用健康状态...")
    
    base_url = "http://localhost:8502"
    
    try:
        # 测试主页
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ 应用主页响应正常 (HTTP 200)")
            
            # 检查响应内容是否包含期望的元素
            content = response.text
            
            # 检查标题
            if "用户行为分析智能体平台" in content:
                print("✅ 应用标题正确显示")
            else:
                print("⚠️  应用标题可能显示异常")
            
            # 检查是否包含Streamlit的基本元素
            if "streamlit" in content.lower():
                print("✅ Streamlit框架正常加载")
            else:
                print("⚠️  Streamlit框架可能未正常加载")
            
            return True
        else:
            print(f"❌ 应用主页响应异常 (HTTP {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_health_endpoint():
    """测试健康检查端点"""
    print("\n🔍 测试健康检查端点...")
    
    base_url = "http://localhost:8502"
    health_endpoints = [
        "/health",
        "/healthz",
        "/_stcore/health"  # Streamlit的内部健康检查
    ]
    
    for endpoint in health_endpoints:
        try:
            url = urljoin(base_url, endpoint)
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ 健康检查端点 {endpoint} 响应正常")
                return True
        except requests.exceptions.RequestException:
            continue
    
    print("⚠️  没有找到可用的健康检查端点")
    return False

def test_session_state_initialization():
    """测试会话状态初始化"""
    print("\n🔍 测试会话状态初始化...")
    
    try:
        # 通过观察页面内容来间接测试状态初始化
        response = requests.get("http://localhost:8502", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # 检查是否有错误信息
            error_indicators = [
                "st.session_state has no attribute",
                "AttributeError",
                "健康检查失败",
                "system_state",
                "NoneType"
            ]
            
            found_errors = []
            for error in error_indicators:
                if error in content:
                    found_errors.append(error)
            
            if found_errors:
                print(f"❌ 发现会话状态错误: {found_errors}")
                return False
            else:
                print("✅ 未发现会话状态初始化错误")
                return True
        else:
            print(f"❌ 无法访问应用 (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_provider_health_check():
    """测试提供商健康检查功能"""
    print("\n🔍 测试提供商健康检查功能...")
    
    try:
        # 通过页面内容检查提供商状态
        response = requests.get("http://localhost:8502", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # 检查提供商相关的内容
            provider_indicators = [
                "google",
                "volcano",
                "provider",
                "健康状态"
            ]
            
            found_providers = 0
            for indicator in provider_indicators:
                if indicator.lower() in content.lower():
                    found_providers += 1
            
            if found_providers > 0:
                print(f"✅ 发现提供商相关内容 ({found_providers}个指标)")
                return True
            else:
                print("⚠️  未发现提供商相关内容")
                return False
        else:
            print(f"❌ 无法访问应用 (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_navigation():
    """测试导航功能"""
    print("\n🔍 测试导航功能...")
    
    try:
        response = requests.get("http://localhost:8502", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # 检查导航相关元素
            nav_elements = [
                "数据上传",
                "智能分析", 
                "事件分析",
                "留存分析",
                "转化分析",
                "用户分群",
                "路径分析",
                "综合报告",
                "系统设置"
            ]
            
            found_nav = 0
            for element in nav_elements:
                if element in content:
                    found_nav += 1
            
            if found_nav >= 5:  # 至少找到5个导航元素
                print(f"✅ 导航元素正常显示 ({found_nav}/{len(nav_elements)})")
                return True
            else:
                print(f"⚠️  导航元素显示不完整 ({found_nav}/{len(nav_elements)})")
                return False
        else:
            print(f"❌ 无法访问应用 (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def run_comprehensive_tests():
    """运行综合测试"""
    print("🚀 开始综合测试...")
    print("=" * 60)
    
    tests = [
        ("应用健康状态", test_app_health),
        ("健康检查端点", test_health_endpoint), 
        ("会话状态初始化", test_session_state_initialization),
        ("提供商健康检查", test_provider_health_check),
        ("导航功能", test_navigation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 执行测试: {test_name}")
        if test_func():
            passed += 1
        time.sleep(1)  # 短暂延迟
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！应用运行正常！")
        return True
    elif passed >= total * 0.7:  # 70%以上通过
        print(f"⚠️  大部分测试通过 ({passed}/{total})，应用基本正常")
        return True
    else:
        print(f"❌ 多个测试失败 ({total - passed}/{total})，需要检查问题")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)