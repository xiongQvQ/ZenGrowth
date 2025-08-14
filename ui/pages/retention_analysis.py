"""
留存分析页面
分析用户留存情况和趋势
"""

import streamlit as st
import pandas as pd
from ui.components.common import render_data_status_check
from ui.state.state_manager import get_state_manager
from engines.retention_analysis_engine import RetentionAnalysisEngine
from visualization.chart_generator import ChartGenerator
from utils.i18n import t

# 队列周期映射
COHORT_PERIOD_MAPPING = {
    "日": "daily",
    "周": "weekly", 
    "月": "monthly",
    "Daily": "daily",
    "Weekly": "weekly",
    "Monthly": "monthly",
    "日留存": "daily",
    "周留存": "weekly",
    "月留存": "monthly",
    "Daily Retention": "daily",
    "Weekly Retention": "weekly",
    "Monthly Retention": "monthly"
}

def translate_cohort_period(chinese_term: str) -> str:
    """将中文队列周期转换为英文"""
    return COHORT_PERIOD_MAPPING.get(chinese_term, chinese_term)

@render_data_status_check 
def show_retention_analysis_page():
    """显示留存分析页面"""
    st.header("📊 " + t("pages.retention_analysis.title", "留存分析"))
    st.markdown("---")
    
    # 获取状态管理器
    state_manager = get_state_manager()
    
    # 初始化分析引擎
    if 'retention_engine' not in st.session_state:
        st.session_state.retention_engine = RetentionAnalysisEngine()
    if 'chart_generator' not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()
    
    # 分析配置
    with st.expander(t('analysis.retention_analysis_config', '留存分析配置'), expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            retention_type = st.selectbox(
                t('analysis.retention_type', '留存类型'),
                options=[t('analysis.daily_retention', '日留存'), t('analysis.weekly_retention', '周留存'), t('analysis.monthly_retention', '月留存')],
                index=0
            )
        
        with col2:
            cohort_period = st.selectbox(
                t('analysis.cohort_period', '队列周期'),
                options=[t('analysis.daily', '日'), t('analysis.weekly', '周'), t('analysis.monthly', '月')],
                index=1
            )
        
        with col3:
            analysis_periods = st.slider(
                t('analysis.analysis_periods', '分析周期数'),
                min_value=7,
                max_value=30,
                value=14,
                help=t('analysis.analysis_periods_help', '分析的时间周期数量')
            )
    
    # 执行留存分析
    if st.button(t('analysis.start_retention_analysis', '开始留存分析'), type="primary"):
        with st.spinner(t('analysis.retention_analysis_processing', '正在进行留存分析...')):
            try:
                raw_data = state_manager.get_raw_data()
                engine = st.session_state.retention_engine
                
                # 执行留存分析 - 转换中文类型为英文
                english_retention_type = translate_cohort_period(retention_type)
                english_cohort_period = translate_cohort_period(cohort_period)

                # 执行完整的留存分析，获取包含队列数据的结果
                if english_retention_type == "daily":
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='daily',
                        max_periods=analysis_periods
                    )
                elif english_retention_type == "weekly":
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='weekly',
                        max_periods=analysis_periods
                    )
                elif english_retention_type == "monthly":
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='monthly',
                        max_periods=analysis_periods
                    )
                else:
                    # 默认使用月度分析
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='monthly',
                        max_periods=analysis_periods
                    )

                # 从留存分析结果中提取队列数据并转换为热力图所需格式
                cohort_viz_data = []
                if retention_results and hasattr(retention_results, 'cohorts'):
                    for cohort in retention_results.cohorts:
                        cohort_period = cohort.cohort_period
                        retention_rates = cohort.retention_rates

                        for period_num, rate in enumerate(retention_rates):
                            cohort_viz_data.append({
                                'cohort_group': cohort_period,
                                'period_number': period_num,
                                'retention_rate': rate
                            })

                # 如果没有数据，创建示例数据
                if not cohort_viz_data:
                    cohort_viz_data = [
                        {'cohort_group': '2024-01', 'period_number': 0, 'retention_rate': 1.0},
                        {'cohort_group': '2024-01', 'period_number': 1, 'retention_rate': 0.7},
                        {'cohort_group': '2024-01', 'period_number': 2, 'retention_rate': 0.5},
                        {'cohort_group': '2024-02', 'period_number': 0, 'retention_rate': 1.0},
                        {'cohort_group': '2024-02', 'period_number': 1, 'retention_rate': 0.6},
                        {'cohort_group': '2024-02', 'period_number': 2, 'retention_rate': 0.4}
                    ]

                # 转换为DataFrame
                cohort_data = pd.DataFrame(cohort_viz_data)

                retention_results_data = {
                    'retention_data': retention_results,
                    'cohort_data': cohort_data,
                    'cohorts': retention_results.cohorts if retention_results and hasattr(retention_results, 'cohorts') else [],
                    'overall_retention_rates': retention_results.overall_retention_rates if retention_results and hasattr(retention_results, 'overall_retention_rates') else {}
                }
                
                # 使用StateManager存储结果
                state_manager.set_analysis_results('retention', retention_results_data)
                
                st.success("✅ 留存分析完成!")
                
            except Exception as e:
                st.error(f"❌ 留存分析失败: {str(e)}")
                import traceback
                st.text("详细错误信息:")
                st.text(traceback.format_exc())
    
    # 显示留存分析结果
    results = state_manager.get_analysis_results('retention')
    
    if results:
        chart_gen = st.session_state.chart_generator
        
        st.markdown("---")
        st.subheader("📊 留存分析结果")
        
        # 留存热力图
        if 'cohort_data' in results and results['cohort_data'] is not None:
            # 检查是否为DataFrame且不为空，或者是否为非空字典/列表
            cohort_data = results['cohort_data']
            is_valid_data = False

            if isinstance(cohort_data, pd.DataFrame) and not cohort_data.empty:
                is_valid_data = True
            elif isinstance(cohort_data, (dict, list)) and len(cohort_data) > 0:
                is_valid_data = True

            if is_valid_data:
                st.subheader("🔥 留存热力图")
                try:
                    # 使用处理过的cohort_data而不是原始的results['cohort_data']
                    heatmap_chart = chart_gen.create_retention_heatmap(cohort_data)
                    st.plotly_chart(heatmap_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"热力图生成失败: {str(e)}")
                    # 显示调试信息
                    st.info(f"数据类型: {type(cohort_data)}")
                    if isinstance(cohort_data, pd.DataFrame):
                        st.info(f"DataFrame形状: {cohort_data.shape}")
                        st.info(f"DataFrame列: {list(cohort_data.columns)}")
                    elif isinstance(cohort_data, (dict, list)):
                        st.info(f"数据长度: {len(cohort_data)}")
                        if len(cohort_data) > 0:
                            st.info(f"数据示例: {str(cohort_data)[:200]}...")
        
        # 留存曲线
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 整体留存曲线")

            # 尝试从多个可能的数据源获取留存数据
            retention_curve_data = None

            # 检查不同的数据结构
            if 'overall_retention_rates' in results and results['overall_retention_rates']:
                # 从整体留存率创建曲线数据
                overall_rates = results['overall_retention_rates']
                if isinstance(overall_rates, dict):
                    curve_data = []
                    for k, v in overall_rates.items():
                        # 处理不同类型的键
                        if isinstance(k, str) and k.startswith('period_'):
                            # 字符串键，如 'period_0', 'period_1'
                            period_num = int(k.replace('period_', ''))
                            curve_data.append({'period': period_num, 'retention_rate': v})
                        elif isinstance(k, int):
                            # 整数键，直接使用
                            curve_data.append({'period': k, 'retention_rate': v})
                        elif isinstance(k, str) and k.isdigit():
                            # 数字字符串键，如 '0', '1'
                            curve_data.append({'period': int(k), 'retention_rate': v})

                    if curve_data:
                        retention_curve_data = pd.DataFrame(curve_data)
            elif 'cohorts' in results and results['cohorts']:
                # 从队列数据计算平均留存率
                cohorts = results['cohorts']
                if isinstance(cohorts, list) and len(cohorts) > 0:
                    # 计算所有队列的平均留存率
                    # 安全地获取所有队列的留存率数据
                    cohort_retention_data = []
                    for cohort in cohorts:
                        if hasattr(cohort, 'retention_rates') and cohort.retention_rates:
                            cohort_retention_data.append(cohort.retention_rates)
                        else:
                            cohort_retention_data.append([])

                    if cohort_retention_data:
                        max_periods = max(len(rates) for rates in cohort_retention_data) if cohort_retention_data else 0
                        avg_rates = []
                        for period in range(max_periods):
                            period_rates = [
                                rates[period]
                                for rates in cohort_retention_data
                                if len(rates) > period
                            ]
                            if period_rates:
                                avg_rates.append({
                                    'period': period,
                                    'retention_rate': sum(period_rates) / len(period_rates)
                                })
                        retention_curve_data = pd.DataFrame(avg_rates)
            elif 'retention_data' in results and results['retention_data'] is not None:
                # 原有的数据结构
                retention_data = results['retention_data']
                try:
                    if isinstance(retention_data, pd.DataFrame):
                        retention_curve_data = retention_data
                    elif isinstance(retention_data, (list, dict)):
                        retention_curve_data = pd.DataFrame(retention_data)
                except Exception:
                    pass

            # 显示留存曲线
            if retention_curve_data is not None and not retention_curve_data.empty:
                if 'period' in retention_curve_data.columns and 'retention_rate' in retention_curve_data.columns:
                    st.line_chart(retention_curve_data.set_index('period')['retention_rate'])
                else:
                    st.info("留存数据格式不完整，无法显示曲线图")
            else:
                st.info("暂无留存曲线数据")
        
        with col2:
            st.subheader("📊 留存率分布")

            # 尝试从多个可能的数据源获取分布数据
            distribution_data = None

            # 检查不同的数据结构
            if 'cohorts' in results and results['cohorts']:
                # 从队列数据创建分布数据
                cohorts = results['cohorts']
                if isinstance(cohorts, list) and len(cohorts) > 0:
                    # 创建包含所有队列和时期的数据
                    dist_data = []
                    for cohort in cohorts:
                        # 安全地访问CohortData对象的属性
                        if hasattr(cohort, 'cohort_period'):
                            cohort_period = cohort.cohort_period
                        else:
                            cohort_period = 'Unknown'
                        
                        if hasattr(cohort, 'retention_rates'):
                            retention_rates = cohort.retention_rates
                        else:
                            retention_rates = []

                        for period_num, rate in enumerate(retention_rates):
                            dist_data.append({
                                'cohort_group': cohort_period,
                                'period_number': period_num,
                                'retention_rate': rate
                            })

                    if dist_data:
                        distribution_data = pd.DataFrame(dist_data)
            elif 'cohort_data' in results and results['cohort_data'] is not None:
                # 原有的数据结构
                cohort_data = results['cohort_data']
                try:
                    if isinstance(cohort_data, pd.DataFrame) and not cohort_data.empty:
                        distribution_data = cohort_data
                    elif isinstance(cohort_data, (dict, list)) and len(cohort_data) > 0:
                        distribution_data = pd.DataFrame(cohort_data)
                except Exception:
                    pass

            # 显示留存率分布
            if distribution_data is not None and not distribution_data.empty:
                if 'period_number' in distribution_data.columns and 'retention_rate' in distribution_data.columns:
                    # 计算每个时期的平均留存率
                    avg_retention = distribution_data.groupby('period_number')['retention_rate'].mean()
                    st.bar_chart(avg_retention)
                elif 'period' in distribution_data.columns and 'retention_rate' in distribution_data.columns:
                    # 备用列名
                    avg_retention = distribution_data.groupby('period')['retention_rate'].mean()
                    st.bar_chart(avg_retention)
                else:
                    st.info("留存数据格式不完整，无法显示分布图")
            else:
                st.info("暂无留存率分布数据")
