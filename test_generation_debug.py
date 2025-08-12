#!/usr/bin/env python3
"""
调试 generation 问题
"""

import logging
from config.volcano_llm_client_monitored import MonitoredVolcanoLLMClient
from config.settings import settings

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_generation_debug():
    """调试 generation 问题"""
    try:
        # 创建监控版本客户端
        client = MonitoredVolcanoLLMClient(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
            model=settings.ark_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        print("客户端创建成功")
        
        test_prompt = "Hello, this is a health check."
        print(f"测试提示: {test_prompt}")
        
        # 测试 _generate 方法
        print("\n=== 测试 _generate 方法 ===")
        result = client._generate([test_prompt])
        print(f"_generate 结果类型: {type(result)}")
        print(f"_generate 结果: {result}")
        
        if result.generations:
            first_generation = result.generations[0]
            print(f"第一个 generation: {first_generation}")
            if first_generation:
                first_gen = first_generation[0]
                print(f"第一个 gen 文本: '{first_gen.text}'")
                print(f"第一个 gen 信息: {first_gen.generation_info}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_generation_debug()