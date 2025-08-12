#!/usr/bin/env python3
"""
快速测试留存分析功能
"""

import pandas as pd
import json
from pathlib import Path
from engines.retention_analysis_engine import RetentionAnalysisEngine
from tools.data_storage_manager import DataStorageManager
from tools.ga4_data_parser import GA4DataParser

def test_retention_analysis():
    """测试留存分析"""
    try:
        print("=== 快速留存分析测试 ===")
        
        # 1. 加载数据
        print("1. 加载数据...")
        data_file = Path("data/events_ga4.ndjson")
        
        if not data_file.exists():
            print("❌ 数据文件不存在")
            return False
        
        # 解析数据
        parser = GA4DataParser()
        raw_data = parser.parse_ndjson(str(data_file))
        
        print(f"✅ 加载了 {len(raw_data)} 个事件")
        
        # 2. 初始化存储管理器
        print("2. 初始化存储管理器...")
        storage_manager = DataStorageManager()
        storage_manager.store_events(raw_data)
        
        # 3. 创建留存分析引擎
        print("3. 创建留存分析引擎...")
        retention_engine = RetentionAnalysisEngine(storage_manager)
        
        # 4. 构建用户队列
        print("4. 构建用户队列...")
        cohorts = retention_engine.build_user_cohorts(
            events=raw_data,
            cohort_period='weekly',
            min_cohort_size=10  # 使用较小的最小队列大小
        )
        
        print(f"✅ 构建了 {len(cohorts)} 个队列")
        for cohort_period, users in list(cohorts.items())[:3]:  # 显示前3个队列
            print(f"  {cohort_period}: {len(users)} 用户")
        
        # 5. 计算留存率
        print("5. 计算留存率...")
        retention_result = retention_engine.calculate_retention_rates(
            events=raw_data,
            analysis_type='weekly'
        )
        
        if retention_result and retention_result.cohorts:
            print(f"✅ 计算了 {len(retention_result.cohorts)} 个队列的留存率")
            
            # 显示第一个队列的留存率
            first_cohort = retention_result.cohorts[0]
            print(f"示例队列 (大小: {first_cohort.cohort_size}):")
            for period, rate in zip(first_cohort.retention_periods, first_cohort.retention_rates):
                print(f"  第{period}天留存率: {rate:.2%}")
            
            print("🎉 留存分析测试成功！")
            return True
        else:
            print("❌ 留存率计算失败")
            return False
        
    except Exception as e:
        print(f"❌ 留存分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_retention_analysis()