#!/usr/bin/env python3
"""
测试 Volcano 响应格式
"""

from config.volcano_llm_client_monitored import MonitoredVolcanoLLMClient
from config.settings import settings

def test_volcano_response():
    """测试 Volcano 响应"""
    try:
        client = MonitoredVolcanoLLMClient(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
            model=settings.ark_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        test_prompt = "Hello, this is a health check."
        response = client.invoke(test_prompt)
        
        print(f"响应类型: {type(response)}")
        print(f"响应内容: {response}")
        print(f"响应字符串: {str(response)}")
        print(f"响应长度: {len(str(response))}")
        print(f"响应去空格后长度: {len(str(response).strip())}")
        
        # 检查是否有效
        is_valid = response and len(str(response).strip()) > 0
        print(f"响应是否有效: {is_valid}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_volcano_response()