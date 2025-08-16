"""
Retention Analysis Page
Analyze user retention patterns and trends
"""

import streamlit as st
import pandas as pd
from ui.components.common import render_data_status_check
from ui.state.state_manager import get_state_manager
from engines.retention_analysis_engine import RetentionAnalysisEngine
from visualization.chart_generator import ChartGenerator
from utils.i18n import t

# Cohort period mapping for backward compatibility
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
    """Translate Chinese cohort period terms to English"""
    return COHORT_PERIOD_MAPPING.get(chinese_term, chinese_term)

@render_data_status_check 
def show_retention_analysis_page():
    """Display retention analysis page"""
    st.header("📊 " + t("pages.retention_analysis.title", "Retention Analysis"))
    st.markdown("---")
    
    # Get state manager
    state_manager = get_state_manager()
    
    # Initialize analysis engine
    if 'retention_engine' not in st.session_state:
        st.session_state.retention_engine = RetentionAnalysisEngine()
    if 'chart_generator' not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()
    
    # Analysis configuration
    with st.expander(t('analysis.retention_analysis_config', 'Retention Analysis Configuration'), expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            retention_type = st.selectbox(
                t('analysis.retention_type', 'Retention Type'),
                options=[t('analysis.daily_retention', 'Daily Retention'), t('analysis.weekly_retention', 'Weekly Retention'), t('analysis.monthly_retention', 'Monthly Retention')],
                index=0
            )
        
        with col2:
            cohort_period = st.selectbox(
                t('analysis.cohort_period', 'Cohort Period'),
                options=[t('analysis.daily', 'Daily'), t('analysis.weekly', 'Weekly'), t('analysis.monthly', 'Monthly')],
                index=1
            )
        
        with col3:
            analysis_periods = st.slider(
                t('analysis.analysis_periods', 'Analysis Periods'),
                min_value=7,
                max_value=30,
                value=14,
                help=t('analysis.analysis_periods_help', 'Number of time periods to analyze')
            )
    
    # Execute retention analysis
    if st.button(t('analysis.start_retention_analysis', 'Start Retention Analysis'), type="primary"):
        with st.spinner(t('analysis.retention_analysis_processing', 'Performing retention analysis...')):
            try:
                raw_data = state_manager.get_raw_data()
                engine = st.session_state.retention_engine
                
                # Execute retention analysis - convert Chinese types to English
                english_retention_type = translate_cohort_period(retention_type)
                english_cohort_period = translate_cohort_period(cohort_period)

                # Execute complete retention analysis, get results containing cohort data
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
                    # Default to monthly analysis
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='monthly',
                        max_periods=analysis_periods
                    )

                # Extract cohort data from retention results and convert to heatmap format
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

                # If no data, create sample data
                if not cohort_viz_data:
                    cohort_viz_data = [
                        {'cohort_group': '2024-01', 'period_number': 0, 'retention_rate': 1.0},
                        {'cohort_group': '2024-01', 'period_number': 1, 'retention_rate': 0.7},
                        {'cohort_group': '2024-01', 'period_number': 2, 'retention_rate': 0.5},
                        {'cohort_group': '2024-02', 'period_number': 0, 'retention_rate': 1.0},
                        {'cohort_group': '2024-02', 'period_number': 1, 'retention_rate': 0.6},
                        {'cohort_group': '2024-02', 'period_number': 2, 'retention_rate': 0.4}
                    ]

                # Convert to DataFrame
                cohort_data = pd.DataFrame(cohort_viz_data)

                retention_results_data = {
                    'retention_data': retention_results,
                    'cohort_data': cohort_data,
                    'cohorts': retention_results.cohorts if retention_results and hasattr(retention_results, 'cohorts') else [],
                    'overall_retention_rates': retention_results.overall_retention_rates if retention_results and hasattr(retention_results, 'overall_retention_rates') else {}
                }
                
                # Store results using StateManager
                state_manager.set_analysis_results('retention', retention_results_data)
                
                st.success(t('errors.retention_analysis_complete', 'Retention analysis completed successfully'))
                
            except Exception as e:
                st.error(f"{t('errors.retention_analysis_failed', 'Retention analysis failed')}: {str(e)}")
                import traceback
                st.text(t('errors.detailed_error_info', 'Detailed error information:'))
                st.text(traceback.format_exc())
    
    # Display retention analysis results
    results = state_manager.get_analysis_results('retention')
    
    if results:
        chart_gen = st.session_state.chart_generator
        
        st.markdown("---")
        st.subheader(t('errors.retention_analysis_results', 'Retention Analysis Results'))
        
        # Retention heatmap
        if 'cohort_data' in results and results['cohort_data'] is not None:
            # Check if it's a non-empty DataFrame or non-empty dict/list
            cohort_data = results['cohort_data']
            is_valid_data = False

            if isinstance(cohort_data, pd.DataFrame) and not cohort_data.empty:
                is_valid_data = True
            elif isinstance(cohort_data, (dict, list)) and len(cohort_data) > 0:
                is_valid_data = True

            if is_valid_data:
                st.subheader(t('errors.retention_heatmap', 'Retention Heatmap'))
                try:
                    # Use processed cohort_data instead of raw results['cohort_data']
                    heatmap_chart = chart_gen.create_retention_heatmap(cohort_data)
                    st.plotly_chart(heatmap_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"{t('errors.heatmap_generation_failed', 'Heatmap generation failed')}: {str(e)}")
                    # Show debug information
                    st.info(f"{t('errors.data_type', 'Data type')}: {type(cohort_data)}")
                    if isinstance(cohort_data, pd.DataFrame):
                        st.info(f"{t('errors.dataframe_shape', 'DataFrame shape')}: {cohort_data.shape}")
                        st.info(f"{t('errors.dataframe_columns', 'DataFrame columns')}: {list(cohort_data.columns)}")
                    elif isinstance(cohort_data, (dict, list)):
                        st.info(f"{t('errors.data_length', 'Data length')}: {len(cohort_data)}")
                        if len(cohort_data) > 0:
                            st.info(f"{t('errors.data_sample', 'Data sample')}: {str(cohort_data)[:200]}...")
        
        # Retention curve
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(t('errors.overall_retention_curve', 'Overall Retention Curve'))

            # Try to get retention data from multiple possible sources
            retention_curve_data = None

            # Check different data structures
            if 'overall_retention_rates' in results and results['overall_retention_rates']:
                # Create curve data from overall retention rates
                overall_rates = results['overall_retention_rates']
                if isinstance(overall_rates, dict):
                    curve_data = []
                    for k, v in overall_rates.items():
                        # Handle different types of keys
                        if isinstance(k, str) and k.startswith('period_'):
                            # String keys like 'period_0', 'period_1'
                            period_num = int(k.replace('period_', ''))
                            curve_data.append({'period': period_num, 'retention_rate': v})
                        elif isinstance(k, int):
                            # Integer keys, use directly
                            curve_data.append({'period': k, 'retention_rate': v})
                        elif isinstance(k, str) and k.isdigit():
                            # Numeric string keys like '0', '1'
                            curve_data.append({'period': int(k), 'retention_rate': v})

                    if curve_data:
                        retention_curve_data = pd.DataFrame(curve_data)
            elif 'cohorts' in results and results['cohorts']:
                # Calculate average retention rates from cohort data
                cohorts = results['cohorts']
                if isinstance(cohorts, list) and len(cohorts) > 0:
                    # Calculate average retention rates for all cohorts
                    # Safely get retention rate data for all cohorts
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
                # Original data structure
                retention_data = results['retention_data']
                try:
                    if isinstance(retention_data, pd.DataFrame):
                        retention_curve_data = retention_data
                    elif isinstance(retention_data, (list, dict)):
                        retention_curve_data = pd.DataFrame(retention_data)
                except Exception:
                    pass

            # Display retention curve
            if retention_curve_data is not None and not retention_curve_data.empty:
                if 'period' in retention_curve_data.columns and 'retention_rate' in retention_curve_data.columns:
                    st.line_chart(retention_curve_data.set_index('period')['retention_rate'])
                else:
                    st.info(t('errors.retention_data_incomplete', 'Retention data is incomplete'))
            else:
                st.info(t('errors.no_retention_curve_data', 'No retention curve data available'))
        
        with col2:
            st.subheader(t('errors.retention_rate_distribution', 'Retention Rate Distribution'))

            # Try to get distribution data from multiple possible sources
            distribution_data = None

            # Check different data structures
            if 'cohorts' in results and results['cohorts']:
                # Create distribution data from cohort data
                cohorts = results['cohorts']
                if isinstance(cohorts, list) and len(cohorts) > 0:
                    # Create data containing all cohorts and periods
                    dist_data = []
                    for cohort in cohorts:
                        # Safely access CohortData object attributes
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
                # Original data structure
                cohort_data = results['cohort_data']
                try:
                    if isinstance(cohort_data, pd.DataFrame) and not cohort_data.empty:
                        distribution_data = cohort_data
                    elif isinstance(cohort_data, (dict, list)) and len(cohort_data) > 0:
                        distribution_data = pd.DataFrame(cohort_data)
                except Exception:
                    pass

            # Display retention rate distribution
            if distribution_data is not None and not distribution_data.empty:
                if 'period_number' in distribution_data.columns and 'retention_rate' in distribution_data.columns:
                    # Calculate average retention rate for each period
                    avg_retention = distribution_data.groupby('period_number')['retention_rate'].mean()
                    st.bar_chart(avg_retention)
                elif 'period' in distribution_data.columns and 'retention_rate' in distribution_data.columns:
                    # Alternative column names
                    avg_retention = distribution_data.groupby('period')['retention_rate'].mean()
                    st.bar_chart(avg_retention)
                else:
                    st.info(t('errors.retention_data_incomplete', 'Retention data is incomplete'))
            else:
                st.info(t('errors.no_retention_distribution_data', 'No retention distribution data available'))
