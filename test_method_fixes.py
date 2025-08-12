#!/usr/bin/env python3
"""
测试方法修复
"""

import pandas as pd
from pathlib import Path
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager
from engines.event_analysis_engine import EventAnalysisEngine
from engines.retention_analysis_engine import RetentionAnalysisEngine

def test_method_fixes():
    """测试方法修复"""
    try:
        print("🧪 测试方法修复...")
        
        # 1. 准备数据
        data_file = Path("data/events_ga4.ndjson")
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        
        events_data = parser.extract_events(raw_data)
        if isinstance(events_data, dict):
            all_events_list = []
            for event_type, event_df in events_data.items():
                if not event_df.empty:
                    all_events_list.append(event_df)
            combined_events = pd.concat(all_events_list, ignore_index=True)
        else:
            combined_events = events_data
        
        storage_manager = DataStorageManager()
        storage_manager.store_events(combined_events)
        
        print(f"✅ 准备了 {len(combined_events)} 个事件")
        
        # 2. 测试事件分析引擎方法
        print("🔍 测试事件分析引擎...")
        event_engine = EventAnalysisEngine(storage_manager)
        
        # 测试修复后的 analyze_event_trends 方法
        try:
            trend_results = event_engine.analyze_event_trends(
                combined_events, 
                time_granularity='daily'  # 使用正确的参数名
            )
            print(f"✅ analyze_event_trends 成功，结果数: {len(trend_results)}")
        except Exception as e:
            print(f"❌ analyze_event_trends 失败: {e}")
            return False
        
        # 3. 测试留存分析引擎方法
        print("🔍 测试留存分析引擎...")
        retention_engine = RetentionAnalysisEngine(storage_manager)
        
        # 测试各种留存分析方法
        try:
            daily_results = retention_engine.analyze_daily_retention(combined_events)
            print(f"✅ analyze_daily_retention 成功")
        except Exception as e:
            print(f"❌ analyze_daily_retention 失败: {e}")
        
        try:
            weekly_results = retention_engine.analyze_weekly_retention(combined_events)
            print(f"✅ analyze_weekly_retention 成功")
        except Exception as e:
            print(f"❌ analyze_weekly_retention 失败: {e}")
        
        try:
            monthly_results = retention_engine.analyze_monthly_retention(combined_events)
            print(f"✅ analyze_monthly_retention 成功")
        except Exception as e:
            print(f"❌ analyze_monthly_retention 失败: {e}")
        
        # 测试队列构建方法
        try:
            cohort_data = retention_engine.build_user_cohorts(
                combined_events, 
                cohort_period='monthly'  # 使用正确的参数名
            )
            print(f"✅ build_user_cohorts 成功")
        except Exception as e:
            print(f"❌ build_user_cohorts 失败: {e}")
        
        print("\\n🎉 方法修复测试成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_method_fixes()
    if success:
        print("\\n✅ 所有方法修复成功！现在应用应该可以正常工作了。")
    else:
        print("\\n❌ 仍有方法需要修复。")