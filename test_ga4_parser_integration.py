"""
GA4数据解析器集成测试

使用实际的GA4数据文件测试解析器功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator
from tools.data_cleaner import DataCleaner
import pandas as pd
import json

def test_with_real_data():
    """使用真实GA4数据测试解析器"""
    
    # 初始化组件
    parser = GA4DataParser()
    validator = DataValidator()
    cleaner = DataCleaner()
    
    print("=== GA4数据解析器集成测试 ===\n")
    
    # 1. 解析NDJSON文件
    print("1. 解析GA4 NDJSON文件...")
    try:
        df = parser.parse_ndjson('data/events_ga4.ndjson')
        print(f"   ✓ 成功解析 {len(df)} 条事件数据")
        print(f"   ✓ 数据列: {list(df.columns)}")
        print(f"   ✓ 事件类型: {df['event_name'].unique()}")
        print(f"   ✓ 用户数量: {df['user_pseudo_id'].nunique()}")
    except Exception as e:
        print(f"   ✗ 解析失败: {e}")
        return
    
    # 2. 数据验证
    print("\n2. 数据质量验证...")
    try:
        validation_report = validator.validate_dataframe(df)
        print(f"   ✓ 验证通过: {validation_report['validation_passed']}")
        print(f"   ✓ 总行数: {validation_report['total_rows']}")
        print(f"   ✓ 唯一用户: {validation_report['statistics']['unique_users']}")
        print(f"   ✓ 唯一事件: {validation_report['statistics']['unique_events']}")
        print(f"   ✓ 日期范围: {validation_report['statistics']['date_range']}")
        
        if validation_report['errors']:
            print(f"   ⚠ 错误: {validation_report['errors']}")
        if validation_report['warnings']:
            print(f"   ⚠ 警告: {validation_report['warnings'][:3]}...")  # 只显示前3个警告
            
    except Exception as e:
        print(f"   ✗ 验证失败: {e}")
    
    # 3. 数据清洗
    print("\n3. 数据清洗...")
    try:
        cleaned_df = cleaner.clean_dataframe(df)
        cleaning_report = cleaner.generate_cleaning_report(df, cleaned_df)
        print(f"   ✓ 清洗完成")
        print(f"   ✓ 原始数据: {cleaning_report['original_rows']} 行")
        print(f"   ✓ 清洗后: {cleaning_report['cleaned_rows']} 行")
        print(f"   ✓ 移除率: {cleaning_report['removal_rate']:.2%}")
        
    except Exception as e:
        print(f"   ✗ 清洗失败: {e}")
        cleaned_df = df
    
    # 4. 事件数据提取
    print("\n4. 事件数据提取...")
    try:
        events_by_type = parser.extract_events(cleaned_df)
        print(f"   ✓ 提取了 {len(events_by_type)} 种事件类型")
        
        for event_type, event_data in events_by_type.items():
            print(f"   ✓ {event_type}: {len(event_data)} 条记录")
            # 显示参数列
            param_columns = [col for col in event_data.columns if col.startswith('param_')]
            if param_columns:
                print(f"     参数: {param_columns[:3]}...")  # 只显示前3个参数
                
    except Exception as e:
        print(f"   ✗ 事件提取失败: {e}")
    
    # 5. 用户属性提取
    print("\n5. 用户属性提取...")
    try:
        user_properties = parser.extract_user_properties(cleaned_df)
        print(f"   ✓ 提取了 {len(user_properties)} 个用户的属性")
        print(f"   ✓ 属性列: {[col for col in user_properties.columns if col.startswith('user_')][:5]}...")
        
        # 显示用户统计
        if len(user_properties) > 0:
            print(f"   ✓ 平台分布: {user_properties['platform'].value_counts().to_dict()}")
            print(f"   ✓ 设备类别: {user_properties['device_category'].value_counts().to_dict()}")
            
    except Exception as e:
        print(f"   ✗ 用户属性提取失败: {e}")
    
    # 6. 会话数据提取
    print("\n6. 会话数据提取...")
    try:
        sessions = parser.extract_sessions(cleaned_df)
        print(f"   ✓ 提取了 {len(sessions)} 个会话")
        
        if len(sessions) > 0:
            print(f"   ✓ 平均会话时长: {sessions['duration_seconds'].mean():.1f} 秒")
            print(f"   ✓ 平均事件数: {sessions['event_count'].mean():.1f}")
            print(f"   ✓ 平均页面浏览: {sessions['page_views'].mean():.1f}")
            print(f"   ✓ 转化会话: {sessions[sessions['conversions'] > 0].shape[0]}")
            
    except Exception as e:
        print(f"   ✗ 会话提取失败: {e}")
    
    # 7. 数据质量报告
    print("\n7. 最终数据质量报告...")
    try:
        final_quality = parser.validate_data_quality(cleaned_df)
        print(f"   ✓ 总事件数: {final_quality['total_events']}")
        print(f"   ✓ 唯一用户数: {final_quality['unique_users']}")
        print(f"   ✓ 日期范围: {final_quality['date_range']['start']} 到 {final_quality['date_range']['end']}")
        print(f"   ✓ 事件类型分布: {final_quality['event_types']}")
        
        if final_quality['data_issues']:
            print(f"   ⚠ 数据问题: {final_quality['data_issues']}")
        else:
            print("   ✓ 未发现数据质量问题")
            
    except Exception as e:
        print(f"   ✗ 质量报告生成失败: {e}")
    
    print("\n=== 集成测试完成 ===")

if __name__ == '__main__':
    test_with_real_data()