#!/usr/bin/env python3
"""
测试引擎方法修复
验证所有引擎方法的签名是否正确
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_engine_methods():
    """测试引擎方法签名"""
    print("=== 测试引擎方法修复 ===\n")
    
    # 创建测试数据
    test_events = pd.DataFrame({
        'event_name': ['page_view', 'click', 'purchase'] * 10,
        'user_id': [f'user_{i%5}' for i in range(30)],
        'timestamp': [datetime.now() - timedelta(days=i) for i in range(30)],
        'properties': [{'page': f'page_{i}'} for i in range(30)]
    })
    
    date_range = ('2024-01-01', '2024-12-31')
    
    try:
        # 测试事件分析引擎
        print("1. 测试 EventAnalysisEngine")
        from engines.event_analysis_engine import EventAnalysisEngine
        event_engine = EventAnalysisEngine()
        
        # 测试 analyze_event_correlation 方法
        try:
            result = event_engine.analyze_event_correlation(
                events=test_events,
                event_types=['page_view', 'click'],
                date_range=date_range
            )
            print("✓ analyze_event_correlation 方法签名正确")
        except Exception as e:
            print(f"✗ analyze_event_correlation 方法错误: {e}")
        
        # 测试转化分析引擎
        print("\n2. 测试 ConversionAnalysisEngine")
        from engines.conversion_analysis_engine import ConversionAnalysisEngine
        conversion_engine = ConversionAnalysisEngine()
        
        try:
            result = conversion_engine.analyze_conversion_funnel(
                events=test_events,
                funnel_steps=['page_view', 'click', 'purchase'],
                date_range=date_range
            )
            print("✓ analyze_conversion_funnel 方法签名正确")
        except Exception as e:
            print(f"✗ analyze_conversion_funnel 方法错误: {e}")
        
        # 测试留存分析引擎
        print("\n3. 测试 RetentionAnalysisEngine")
        from engines.retention_analysis_engine import RetentionAnalysisEngine
        retention_engine = RetentionAnalysisEngine()
        
        try:
            result = retention_engine.analyze_retention_rate(
                events=test_events,
                analysis_type='monthly',
                date_range=date_range
            )
            print("✓ analyze_retention_rate 方法签名正确")
        except Exception as e:
            print(f"✗ analyze_retention_rate 方法错误: {e}")
        
        # 测试用户分群引擎
        print("\n4. 测试 UserSegmentationEngine")
        from engines.user_segmentation_engine import UserSegmentationEngine
        segmentation_engine = UserSegmentationEngine()
        
        try:
            result = segmentation_engine.segment_users(
                events=test_events,
                features=['event_frequency'],
                n_clusters=3
            )
            print("✓ segment_users 方法签名正确")
        except Exception as e:
            print(f"✗ segment_users 方法错误: {e}")
        
        # 测试路径分析引擎
        print("\n5. 测试 PathAnalysisEngine")
        from engines.path_analysis_engine import PathAnalysisEngine
        path_engine = PathAnalysisEngine()
        
        try:
            result = path_engine.mine_user_paths(
                events=test_events,
                min_length=2,
                max_length=5,
                min_support=0.1,
                date_range=date_range
            )
            print("✓ mine_user_paths 方法签名正确")
        except Exception as e:
            print(f"✗ mine_user_paths 方法错误: {e}")
        
        print("\n=== 引擎方法测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        return False
    
    return True

def test_volcano_simple():
    """简单测试Volcano API连接"""
    print("\n=== 测试 Volcano API 连接 ===\n")
    
    try:
        from config.volcano_llm_client import VolcanoLLMClient
        from config.settings import settings
        
        # 创建客户端
        client = VolcanoLLMClient(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
            model=settings.ark_model,
            temperature=0.1
        )
        
        # 简单文本测试
        print("测试简单文本请求...")
        response = client.invoke("Hello, this is a test.")
        print(f"✓ Volcano API 响应: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Volcano API 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试引擎修复...")
    
    # 测试引擎方法
    engine_success = test_engine_methods()
    
    # 测试Volcano API
    volcano_success = test_volcano_simple()
    
    if engine_success and volcano_success:
        print("\n🎉 所有测试通过!")
    else:
        print("\n❌ 部分测试失败，请检查错误信息")