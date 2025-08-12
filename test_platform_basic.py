#!/usr/bin/env python3
"""
测试用户行为分析平台基础功能
"""

import logging
from config.crew_config import get_llm, create_agent

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_agent():
    """测试基础智能体功能"""
    try:
        print("=== 测试基础智能体功能 ===")
        
        # 创建一个事件分析智能体
        agent = create_agent("event_analyst", provider="volcano")
        print(f"智能体创建成功: {agent.role}")
        print(f"智能体目标: {agent.goal}")
        
        # 测试简单的分析任务
        test_prompt = "请分析一下用户在电商网站上的购买行为模式。"
        
        # 使用智能体的 LLM 进行分析
        if hasattr(agent.llm, 'invoke'):
            response = agent.llm.invoke(test_prompt)
        else:
            # 使用旧版本的 predict 方法
            response = agent.llm.predict(test_prompt)
        
        print(f"\n智能体响应:")
        print(f"响应长度: {len(response)}")
        print(f"响应内容: {response[:200]}...")
        
        if response and len(response) > 50:
            print("✅ 智能体基础功能测试成功")
            return True
        else:
            print("❌ 智能体响应过短")
            return False
            
    except Exception as e:
        print(f"❌ 智能体测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_providers():
    """测试不同的 LLM 提供商"""
    try:
        print("\n=== 测试 LLM 提供商 ===")
        
        # 测试 Volcano 提供商
        print("测试 Volcano 提供商...")
        volcano_llm = get_llm(provider="volcano")
        volcano_response = volcano_llm.invoke("简单介绍一下用户行为分析的重要性。")
        print(f"Volcano 响应长度: {len(volcano_response)}")
        print(f"Volcano 响应: {volcano_response[:100]}...")
        
        # 测试默认提供商
        print("\n测试默认提供商...")
        default_llm = get_llm()
        default_response = default_llm.invoke("什么是用户留存分析？")
        print(f"默认提供商响应长度: {len(default_response)}")
        print(f"默认提供商响应: {default_response[:100]}...")
        
        print("✅ LLM 提供商测试成功")
        return True
        
    except Exception as e:
        print(f"❌ LLM 提供商测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("用户行为分析平台基础功能测试")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    # 测试基础智能体功能
    if test_basic_agent():
        success_count += 1
    
    # 测试 LLM 提供商
    if test_llm_providers():
        success_count += 1
    
    print(f"\n测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！平台基础功能正常")
    else:
        print("⚠️  部分测试失败，请检查配置")

if __name__ == "__main__":
    main()