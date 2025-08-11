"""
简单的数据清洗器测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.ga4_data_parser import GA4DataParser
from tools.data_cleaner import DataCleaner

def test_cleaner():
    parser = GA4DataParser()
    cleaner = DataCleaner()
    
    # 解析数据
    df = parser.parse_ndjson('data/events_ga4.ndjson')
    print(f"原始数据: {len(df)} 行")
    
    # 清洗数据
    try:
        cleaned_df = cleaner.clean_dataframe(df)
        print(f"清洗后: {len(cleaned_df)} 行")
        print("✓ 数据清洗成功")
    except Exception as e:
        print(f"✗ 数据清洗失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_cleaner()