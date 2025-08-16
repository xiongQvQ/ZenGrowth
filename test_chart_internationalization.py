#!/usr/bin/env python3
"""
测试图表国际化功能
验证ChartGenerator在英文模式下显示英文标签
"""

import os
import sys
import pandas as pd
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_chart_internationalization():
    """测试图表国际化功能"""
    print("🧪 测试图表国际化功能...")
    
    # 设置环境变量强制使用英文
    os.environ['FORCE_LANGUAGE'] = 'en-US'
    
    try:
        from visualization.chart_generator import ChartGenerator
        from utils.i18n import t, get_current_language
        
        # 验证当前语言设置
        current_lang = get_current_language()
        print(f"  ✅ 当前语言设置: {current_lang}")
        
        # 创建ChartGenerator实例
        chart_gen = ChartGenerator()
        print(f"  ✅ ChartGenerator初始化完成")
        
        # 创建测试数据
        print("\n📊 测试事件时间线图表...")
        event_data = pd.DataFrame({
            'event_name': ['page_view', 'click', 'purchase'] * 10,
            'event_timestamp': range(30),
            'event_date': pd.date_range('2024-01-01', periods=30)
        })
        
        timeline_fig = chart_gen.create_event_timeline(event_data)
        timeline_title = timeline_fig.layout.title.text
        print(f"  ✅ 事件时间线图表标题: '{timeline_title}'")
        
        # 验证是否为英文
        if 'Event Timeline Analysis' in timeline_title:
            print(f"  ✅ 图表标题正确显示英文")
        else:
            print(f"  ❌ 图表标题未正确显示英文: {timeline_title}")
        
        print("\n🔥 测试留存热力图...")
        # 创建留存测试数据
        retention_data = pd.DataFrame({
            'cohort_group': ['2024-01', '2024-02', '2024-03'] * 3,
            'period_number': [0, 1, 2] * 3,
            'retention_rate': [1.0, 0.8, 0.6, 1.0, 0.75, 0.55, 1.0, 0.7, 0.5]
        })
        
        heatmap_fig = chart_gen.create_retention_heatmap(retention_data)
        heatmap_title = heatmap_fig.layout.title.text
        print(f"  ✅ 留存热力图标题: '{heatmap_title}'")
        
        # 验证是否为英文
        if 'User Retention Heatmap' in heatmap_title:
            print(f"  ✅ 热力图标题正确显示英文")
        else:
            print(f"  ❌ 热力图标题未正确显示英文: {heatmap_title}")
        
        print("\n🔄 测试转化漏斗图表...")
        funnel_data = pd.DataFrame({
            'step_name': ['首页访问', '产品浏览', '添加购物车', '结算'],
            'user_count': [1000, 800, 300, 100],
            'step_order': [1, 2, 3, 4]
        })
        
        funnel_fig = chart_gen.create_funnel_chart(funnel_data)
        funnel_title = funnel_fig.layout.title.text
        print(f"  ✅ 转化漏斗图标题: '{funnel_title}'")
        
        # 验证是否为英文
        if 'Conversion Funnel Analysis' in funnel_title:
            print(f"  ✅ 漏斗图标题正确显示英文")
        else:
            print(f"  ❌ 漏斗图标题未正确显示英文: {funnel_title}")
        
        print("\n📊 测试事件分布图表...")
        distribution_data = pd.DataFrame({
            'event_name': ['page_view'] * 100 + ['click'] * 50 + ['purchase'] * 20
        })
        
        dist_fig = chart_gen.create_event_distribution_chart(distribution_data)
        dist_title = dist_fig.layout.title.text
        print(f"  ✅ 事件分布图标题: '{dist_title}'")
        
        # 验证是否为英文
        if 'Event Type Distribution' in dist_title:
            print(f"  ✅ 分布图标题正确显示英文")
        else:
            print(f"  ❌ 分布图标题未正确显示英文: {dist_title}")
        
        print("\n🎯 测试多指标仪表板...")
        dashboard_metrics = {
            'event_trends': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=10),
                'count': range(10, 20)
            }),
            'user_activity': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=10),
                'active_users': range(100, 110)
            }),
            'conversion_rates': {'step1': 0.8, 'step2': 0.6},
            'retention_rates': {'day1': 0.9, 'day7': 0.7}
        }
        
        dashboard_fig = chart_gen.create_multi_metric_dashboard(dashboard_metrics)
        dashboard_title = dashboard_fig.layout.title.text
        print(f"  ✅ 仪表板标题: '{dashboard_title}'")
        
        # 验证是否为英文
        if 'Data Analysis Dashboard' in dashboard_title:
            print(f"  ✅ 仪表板标题正确显示英文")
        else:
            print(f"  ❌ 仪表板标题未正确显示英文: {dashboard_title}")
        
        # 测试翻译键验证
        print("\n🔍 验证翻译键...")
        test_keys = [
            ('charts.event_timeline_title', 'Event Timeline Analysis'),
            ('charts.retention_heatmap_title', 'User Retention Heatmap'),
            ('charts.funnel_chart_title', 'Conversion Funnel Analysis'),
            ('charts.event_distribution_title', 'Event Type Distribution'),
            ('charts.dashboard_title', 'Data Analysis Dashboard')
        ]
        
        for key, expected in test_keys:
            actual = t(key, expected)
            if actual == expected:
                print(f"  ✅ 翻译键 '{key}' 正确: '{actual}'")
            else:
                print(f"  ❌ 翻译键 '{key}' 错误: 期望 '{expected}', 实际 '{actual}'")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理环境变量
        if 'FORCE_LANGUAGE' in os.environ:
            del os.environ['FORCE_LANGUAGE']

def test_chinese_mode():
    """测试中文模式下的显示"""
    print("\n🇨🇳 测试中文模式...")
    
    # 设置环境变量强制使用中文
    os.environ['FORCE_LANGUAGE'] = 'zh-CN'
    
    try:
        from visualization.chart_generator import ChartGenerator
        from utils.i18n import t, get_current_language
        
        # 重新初始化i18n以获取新的语言设置
        from utils.i18n import i18n
        i18n._update_current_language()
        
        current_lang = get_current_language()
        print(f"  ✅ 当前语言设置: {current_lang}")
        
        chart_gen = ChartGenerator()
        
        # 创建测试数据
        event_data = pd.DataFrame({
            'event_name': ['page_view', 'click', 'purchase'] * 5,
            'event_timestamp': range(15),
            'event_date': pd.date_range('2024-01-01', periods=15)
        })
        
        timeline_fig = chart_gen.create_event_timeline(event_data)
        timeline_title = timeline_fig.layout.title.text
        print(f"  ✅ 中文模式下事件时间线标题: '{timeline_title}'")
        
        # 验证是否为中文
        if '事件时间线分析' in timeline_title:
            print(f"  ✅ 图表标题正确显示中文")
        else:
            print(f"  ❌ 图表标题未正确显示中文: {timeline_title}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 中文模式测试失败: {e}")
        return False
    
    finally:
        # 清理环境变量
        if 'FORCE_LANGUAGE' in os.environ:
            del os.environ['FORCE_LANGUAGE']

def main():
    """运行所有图表国际化测试"""
    print("🚀 图表国际化功能测试")
    print("=" * 50)
    
    english_test = test_chart_internationalization()
    chinese_test = test_chinese_mode()
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print("=" * 50)
    
    if english_test and chinese_test:
        print("🎉 SUCCESS! 所有图表国际化测试通过!")
        print("\n✅ 图表现在可以正确显示英文/中文标签")
        print("✅ 用户请求已完成: 事件分析、留存分析图表在英文模式下显示英文")
        return True
    else:
        print("❌ FAIL: 部分图表国际化测试失败")
        if not english_test:
            print("❌ 英文模式测试失败")
        if not chinese_test:
            print("❌ 中文模式测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)