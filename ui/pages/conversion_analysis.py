"""
Conversion Analysis Page
Analyze user conversion paths and effectiveness
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from engines.conversion_analysis_engine import ConversionAnalysisEngine
from visualization.chart_generator import ChartGenerator
from visualization.advanced_visualizer import AdvancedVisualizer
from utils.i18n import t
from ui.components.common import render_no_data_warning, render_data_status_check

class ConversionAnalysisPage:
    """Conversion Analysis Page Class"""
    
    def __init__(self):
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize analysis engines and visualization components"""
        if 'conversion_engine' not in st.session_state:
            st.session_state.conversion_engine = ConversionAnalysisEngine()
        if 'chart_generator' not in st.session_state:
            st.session_state.chart_generator = ChartGenerator()
        if 'advanced_visualizer' not in st.session_state:
            st.session_state.advanced_visualizer = AdvancedVisualizer()
    
    def render(self):
        """Render conversion analysis page"""
        from ui.state import get_state_manager
        
        # Check data status
        state_manager = get_state_manager()
        if not state_manager.is_data_loaded():
            render_no_data_warning()
            return
        
        st.header("🎯 " + t("pages.conversion_analysis.title", "Conversion Analysis"))
        st.markdown("---")
        
        # Analysis configuration panel
        config = self._render_analysis_config()
        
        # Execute analysis button
        if st.button(t('analysis.start_conversion_analysis', 'Start Conversion Analysis'), type="primary"):
            self._execute_conversion_analysis(config)
        
        # Display analysis results
        if 'conversion_analysis_results' in st.session_state:
            self._render_analysis_results()
    
    def _render_analysis_config(self) -> Dict[str, Any]:
        """Render analysis configuration panel"""
        with st.expander(t('analysis.conversion_config', 'Conversion Analysis Configuration'), expanded=False):
            
            # Basic configuration
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_range = st.date_input(
                    t('analysis.time_range_label', 'Time Range'),
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    help=t('analysis.time_range_help', 'Select the time range for analysis')
                )
            
            with col2:
                analysis_type = st.selectbox(
                    t('analysis.analysis_type', 'Analysis Type'),
                    options=[
                        t('analysis.predefined_funnels', 'Predefined Funnels'),
                        t('analysis.custom_funnel', 'Custom Funnel'),
                        t('analysis.all_funnels', 'All Funnels')
                    ],
                    index=0,
                    help=t('analysis.analysis_type_help', 'Select the type of conversion analysis')
                )
            
            with col3:
                time_window = st.slider(
                    t('analysis.time_window', 'Time Window (hours)'),
                    min_value=1,
                    max_value=168,  # 7 days
                    value=24,
                    help=t('analysis.time_window_help', 'Maximum time interval between conversion steps')
                )
            
            # Advanced configuration
            with st.expander(t('analysis.advanced_config', 'Advanced Configuration'), expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    include_attribution = st.checkbox(
                        t('analysis.include_attribution', 'Include Attribution Analysis'),
                        value=True,
                        help=t('analysis.attribution_help', 'Analyze conversion attribution patterns')
                    )
                    
                    include_segments = st.checkbox(
                        t('analysis.include_segments', 'Include Segment Analysis'),
                        value=True,
                        help=t('analysis.segments_help', 'Analyze by platform, device and other dimensions')
                    )
                
                with col2:
                    min_users_threshold = st.slider(
                        t('analysis.min_users_threshold', 'Minimum Users Threshold'),
                        min_value=1,
                        max_value=100,
                        value=10,
                        help=t('analysis.min_users_help', 'Minimum user count requirement for funnel analysis')
                    )
                    
                    attribution_window = st.slider(
                        t('analysis.attribution_window', 'Attribution Window (days)'),
                        min_value=1,
                        max_value=30,
                        value=7,
                        help=t('analysis.attribution_window_help', 'Time window for attribution analysis')
                    )
            
            # Custom funnel configuration
            custom_funnel_steps = []
            if analysis_type == t('analysis.custom_funnel', 'Custom Funnel'):
                st.subheader(t('analysis.custom_funnel_config', 'Custom Funnel Configuration'))
                
                # Get available event types
                from ui.state import get_state_manager
                state_manager = get_state_manager()
                data_summary = state_manager.get_data_summary()
                event_types = list(data_summary.get('event_types', {}).keys()) if data_summary else []
                
                if event_types:
                    custom_funnel_steps = st.multiselect(
                        t('analysis.funnel_steps', 'Funnel Steps'),
                        options=event_types,
                        default=[],
                        help=t('analysis.funnel_steps_help', 'Select funnel steps in order')
                    )
                else:
                    st.warning(t('analysis.no_event_types', 'No available event types'))
        
        return {
            'date_range': date_range,
            'analysis_type': analysis_type,
            'time_window': time_window,
            'include_attribution': include_attribution,
            'include_segments': include_segments,
            'min_users_threshold': min_users_threshold,
            'attribution_window': attribution_window,
            'custom_funnel_steps': custom_funnel_steps
        }
    
    def _execute_conversion_analysis(self, config: Dict[str, Any]):
        """Execute conversion analysis"""
        from ui.state import get_state_manager
        
        with st.spinner(t('analysis.conversion_processing', 'Executing conversion analysis...')):
            try:
                # Get data
                state_manager = get_state_manager()
                raw_data = state_manager.get_raw_data()
                
                if raw_data.empty:
                    st.error(t('analysis.no_data', 'No data available for analysis'))
                    return
                
                # Initialize engine
                engine = st.session_state.conversion_engine
                
                # Apply time filtering
                filtered_data = self._filter_data_by_time(raw_data, config['date_range'])
                
                # Execute conversion analysis
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Basic conversion analysis
                status_text.text(t('analysis.step_basic_conversion', 'Executing basic conversion analysis...'))
                progress_bar.progress(20)
                
                conversion_result = self._perform_conversion_analysis(engine, filtered_data, config)
                
                # Step 2: Attribution analysis (if enabled)
                attribution_result = None
                if config.get('include_attribution', False):
                    status_text.text(t('analysis.step_attribution', 'Executing attribution analysis...'))
                    progress_bar.progress(50)
                    attribution_result = engine.analyze_conversion_attribution(
                        filtered_data, 
                        config.get('attribution_window', 7)
                    )
                
                # Step 3: Drop-off point analysis
                status_text.text(t('analysis.step_dropoff_analysis', 'Analyzing drop-off points...'))
                progress_bar.progress(70)
                
                dropoff_result = self._analyze_dropoff_points(engine, filtered_data, config)
                
                # Step 4: User journey analysis
                status_text.text(t('analysis.step_user_journeys', 'Analyzing user journeys...'))
                progress_bar.progress(90)
                
                user_journeys = self._analyze_user_journeys(engine, filtered_data, config)
                
                # Complete analysis
                status_text.text(t('analysis.step_completed', 'Analysis completed'))
                progress_bar.progress(100)
                
                # Store analysis results
                results = {
                    'conversion_result': conversion_result,
                    'attribution_result': attribution_result,
                    'dropoff_result': dropoff_result,
                    'user_journeys': user_journeys,
                    'config': config,
                    'data_size': len(filtered_data),
                    'analysis_time': datetime.now().isoformat()
                }
                
                # Use StateManager to store results
                state_manager.set_analysis_results('conversion', results)
                st.session_state.conversion_analysis_results = results
                
                st.success(t('analysis.conversion_complete', '✅ Conversion analysis completed!'))
                
            except Exception as e:
                st.error(f"{t('analysis.analysis_failed', 'Conversion analysis failed')}: {str(e)}")
                import traceback
                st.text(t('errors.detailed_error_info'))
                st.text(traceback.format_exc())
    
    def _filter_data_by_time(self, data: pd.DataFrame, date_range) -> pd.DataFrame:
        """Filter data by time range"""
        try:
            if not hasattr(date_range, '__len__') or len(date_range) != 2:
                return data
            
            start_date, end_date = date_range
            
            # Ensure time column exists
            if 'event_datetime' not in data.columns:
                if 'event_timestamp' in data.columns:
                    data['event_datetime'] = pd.to_datetime(data['event_timestamp'], unit='us')
                else:
                    return data
            
            # Filter time range
            filtered_data = data[
                (data['event_datetime'].dt.date >= start_date) &
                (data['event_datetime'].dt.date <= end_date)
            ].copy()
            
            return filtered_data
            
        except Exception as e:
            st.warning(f"{t('common.filter_failed', 'Filter failed')}: {e}")
            return data
    
    def _perform_conversion_analysis(self, engine, data: pd.DataFrame, config: Dict[str, Any]):
        """Perform conversion analysis"""
        try:
            analysis_type = config.get('analysis_type', '')
            
            if analysis_type == t('analysis.custom_funnel', 'Custom Funnel'):
                # Custom funnel analysis
                custom_steps = config.get('custom_funnel_steps', [])
                if not custom_steps:
                    st.warning(t('analysis.no_custom_steps', 'Please configure custom funnel steps'))
                    return None
                
                funnel_definitions = {'custom_funnel': custom_steps}
                return engine.calculate_conversion_rates(data, funnel_definitions)
            
            elif analysis_type == t('analysis.all_funnels', 'All Funnels'):
                # All predefined funnel analysis
                return engine.calculate_conversion_rates(data)
            
            else:
                # Predefined funnel analysis (default)
                return engine.calculate_conversion_rates(data)
                
        except Exception as e:
            st.error(f"{t('analysis.conversion_execution_failed', 'Conversion analysis execution failed')}: {e}")
            return None
    
    def _analyze_dropoff_points(self, engine, data: pd.DataFrame, config: Dict[str, Any]):
        """Analyze drop-off points"""
        try:
            custom_steps = config.get('custom_funnel_steps', [])
            if custom_steps:
                return engine.identify_drop_off_points(data, custom_steps)
            else:
                return engine.identify_drop_off_points(data)
        except Exception as e:
            st.warning(f"{t('analysis.dropoff_analysis_failed', 'Drop-off point analysis failed')}: {e}")
            return None
    
    def _analyze_user_journeys(self, engine, data: pd.DataFrame, config: Dict[str, Any]):
        """Analyze user journeys"""
        try:
            custom_steps = config.get('custom_funnel_steps', [])
            if custom_steps:
                return engine.create_user_conversion_journeys(data, custom_steps)
            else:
                return engine.create_user_conversion_journeys(data)
        except Exception as e:
            st.warning(f"{t('analysis.journey_analysis_failed', 'User journey analysis failed')}: {e}")
            return []
    
    def _render_analysis_results(self):
        """Render analysis results"""
        results = st.session_state.conversion_analysis_results
        
        if not results:
            st.warning(t('analysis.no_results', 'No analysis results to display'))
            return
        
        st.markdown("---")
        st.subheader("📊 " + t('analysis.conversion_results', 'Conversion Analysis Results'))
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 " + t('analysis.overview', 'Overview'),
            "🔍 " + t('analysis.funnel_details', 'Funnel Details'),
            "📊 " + t('analysis.visualizations', 'Visualizations'),
            "🛤️ " + t('analysis.user_journeys', 'User Journeys'),
            "💡 " + t('analysis.insights', 'Insights & Recommendations')
        ])
        
        with tab1:
            self._render_overview(results)
        
        with tab2:
            self._render_funnel_details(results)
        
        with tab3:
            self._render_visualizations(results)
        
        with tab4:
            self._render_user_journeys(results)
        
        with tab5:
            self._render_insights_and_recommendations(results)
    
    def _render_overview(self, results: Dict[str, Any]):
        """Render overview tab"""
        st.subheader("📈 " + t('analysis.key_metrics', 'Key Metrics'))
        
        conversion_result = results.get('conversion_result')
        if not conversion_result or not conversion_result.funnels:
            st.info(t('analysis.no_conversion_data', 'No conversion data available'))
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        funnels = conversion_result.funnels
        avg_conversion = sum(f.overall_conversion_rate for f in funnels) / len(funnels)
        max_conversion = max(f.overall_conversion_rate for f in funnels)
        total_users_analyzed = sum(f.total_users_entered for f in funnels)
        total_conversions = sum(f.total_users_converted for f in funnels)
        
        with col1:
            st.metric(
                t('analysis.avg_conversion_rate', 'Average Conversion Rate'),
                f"{avg_conversion:.1%}",
                help=t('analysis.avg_conversion_help', 'Average conversion rate of all funnels')
            )
        
        with col2:
            st.metric(
                t('analysis.best_conversion_rate', 'Best Conversion Rate'),
                f"{max_conversion:.1%}",
                help=t('analysis.best_conversion_help', 'Best performing funnel conversion rate')
            )
        
        with col3:
            st.metric(
                t('analysis.total_users_analyzed', 'Total Users Analyzed'),
                f"{total_users_analyzed:,}",
                help=t('analysis.total_users_help', 'Total number of users in conversion analysis')
            )
        
        with col4:
            st.metric(
                t('analysis.total_conversions', 'Total Conversions'),
                f"{total_conversions:,}",
                help=t('analysis.total_conversions_help', 'Total number of successfully converted users')
            )
        
        # Funnel performance comparison
        st.subheader("🏆 " + t('analysis.funnel_performance', 'Funnel Performance Comparison'))
        
        funnel_data = []
        for funnel in funnels:
            funnel_data.append({
                t('analysis.funnel_name', 'Funnel Name'): funnel.funnel_name,
                t('analysis.conversion_rate', 'Conversion Rate'): f"{funnel.overall_conversion_rate:.1%}",
                t('analysis.users_entered', 'Users Entered'): funnel.total_users_entered,
                t('analysis.users_converted', 'Users Converted'): funnel.total_users_converted,
                t('analysis.bottleneck_step', 'Bottleneck Step'): funnel.bottleneck_step or 'N/A'
            })
        
        if funnel_data:
            df = pd.DataFrame(funnel_data)
            st.dataframe(df, use_container_width=True)
    
    def _render_funnel_details(self, results: Dict[str, Any]):
        """Render funnel details tab"""
        st.subheader("🔍 " + t('analysis.detailed_funnel_analysis', 'Detailed Funnel Analysis'))
        
        conversion_result = results.get('conversion_result')
        if not conversion_result or not conversion_result.funnels:
            st.info(t('analysis.no_funnel_details', 'No funnel details available'))
            return
        
        # Select funnel
        funnel_names = [f.funnel_name for f in conversion_result.funnels]
        selected_funnel_name = st.selectbox(
            t('analysis.select_funnel', 'Select Funnel'),
            options=funnel_names,
            index=0
        )
        
        selected_funnel = next(f for f in conversion_result.funnels if f.funnel_name == selected_funnel_name)
        
        # Funnel basic information
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(t('analysis.overall_conversion', 'Overall Conversion Rate'), f"{selected_funnel.overall_conversion_rate:.1%}")
            st.metric(t('analysis.users_entered', 'Users Entered'), f"{selected_funnel.total_users_entered:,}")
        
        with col2:
            st.metric(t('analysis.users_converted', 'Users Converted'), f"{selected_funnel.total_users_converted:,}")
            if selected_funnel.avg_completion_time:
                st.metric(t('analysis.avg_completion_time', 'Average Completion Time'), f"{selected_funnel.avg_completion_time/60:.1f} minutes")
        
        # Step details
        st.subheader("📋 " + t('analysis.step_details', 'Step Details'))
        
        step_data = []
        for step in selected_funnel.steps:
            step_data.append({
                t('analysis.step', 'Step'): step.step_name,
                t('analysis.order', 'Order'): step.step_order + 1,
                t('analysis.users_reached', 'Users Reached'): f"{step.total_users:,}",
                t('analysis.conversion_rate', 'Conversion Rate'): f"{step.conversion_rate:.1%}",
                t('analysis.dropoff_rate', 'Drop-off Rate'): f"{step.drop_off_rate:.1%}",
                t('analysis.avg_time_to_next', 'Avg Time to Next'): f"{step.avg_time_to_next_step/60:.1f} {t('common.minutes', 'minutes')}" if step.avg_time_to_next_step else 'N/A'
            })
        
        if step_data:
            df = pd.DataFrame(step_data)
            st.dataframe(df, use_container_width=True)
        
        # Bottleneck analysis
        if selected_funnel.bottleneck_step:
            st.warning(f"🚨 **{t('analysis.bottleneck_step', 'Bottleneck Step')}**: {selected_funnel.bottleneck_step}")
            st.info(f"💡 {t('analysis.optimize_bottleneck', 'Focus on optimizing this step to improve overall conversion rate')}")
    
    def _render_visualizations(self, results: Dict[str, Any]):
        """Render visualizations tab"""
        st.subheader("📊 " + t('analysis.conversion_visualizations', 'Conversion Visualizations'))
        
        conversion_result = results.get('conversion_result')
        if not conversion_result or not conversion_result.funnels:
            st.info(t('analysis.no_visualization_data', 'No visualization data available'))
            return
        
        # Funnel chart
        self._create_funnel_chart(conversion_result.funnels)
        
        # Conversion rate comparison chart
        self._create_conversion_comparison_chart(conversion_result.funnels)
        
        # Drop-off analysis chart
        dropoff_result = results.get('dropoff_result')
        if dropoff_result:
            self._create_dropoff_analysis_chart(dropoff_result)
    
    def _create_funnel_chart(self, funnels):
        """Create funnel chart"""
        st.subheader("🏺 " + t('analysis.funnel_chart', 'Conversion Funnel Chart'))
        
        # Select funnel
        funnel_names = [f.funnel_name for f in funnels]
        selected_funnel_name = st.selectbox(
            t('analysis.select_funnel_for_chart', 'Select funnel to display'),
            options=funnel_names,
            key='funnel_chart_select'
        )
        
        selected_funnel = next(f for f in funnels if f.funnel_name == selected_funnel_name)
        
        # Prepare data
        steps = []
        values = []
        
        for step in selected_funnel.steps:
            steps.append(step.step_name)
            values.append(step.total_users)
        
        # Create funnel chart
        fig = go.Figure(go.Funnel(
            y=steps,
            x=values,
            textinfo="value+percent initial",
            opacity=0.8,
            marker={"color": ["deepskyblue", "lightsalmon", "tan", "teal", "silver"],
                   "line": {"width": [4, 2, 2, 3, 1, 1], "color": ["wheat", "wheat", "blue", "wheat", "wheat"]}},
            connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
        ))
        
        fig.update_layout(
            title=f"{selected_funnel_name} {t('analysis.conversion_funnel', 'Conversion Funnel')}",
            font_size=12,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_conversion_comparison_chart(self, funnels):
        """Create conversion rate comparison chart"""
        st.subheader("📊 " + t('analysis.conversion_comparison', 'Conversion Rate Comparison'))
        
        funnel_names = [f.funnel_name for f in funnels]
        conversion_rates = [f.overall_conversion_rate * 100 for f in funnels]
        
        fig = px.bar(
            x=funnel_names,
            y=conversion_rates,
            title=t('analysis.overall_conversion_rates', 'Overall Conversion Rates by Funnel'),
            labels={'x': t('analysis.funnel_name', 'Funnel Name'), 'y': t('analysis.conversion_rate_percent', 'Conversion Rate (%)')},
            color=conversion_rates,
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_dropoff_analysis_chart(self, dropoff_result):
        """Create drop-off analysis chart"""
        if not dropoff_result or 'funnel_steps' not in dropoff_result:
            return
        
        st.subheader("📉 " + t('analysis.dropoff_analysis', 'Drop-off Analysis'))
        
        steps_data = dropoff_result['funnel_steps']
        if not steps_data:
            st.info(t('analysis.no_dropoff_data', 'No drop-off data available'))
            return
        
        # Prepare data
        step_names = []
        users_lost_rates = []
        
        for step_info in steps_data:
            if 'users_lost_rate' in step_info:
                step_names.append(step_info['step_name'])
                users_lost_rates.append(step_info['users_lost_rate'] * 100)
        
        if step_names and users_lost_rates:
            fig = px.bar(
                x=step_names,
                y=users_lost_rates,
                title=t('analysis.step_dropoff_rates', 'Drop-off Rates by Step'),
                labels={'x': t('analysis.step_name', 'Step Name'), 'y': t('analysis.dropoff_rate_percent', 'Drop-off Rate (%)')},
                color=users_lost_rates,
                color_continuous_scale='reds'
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_user_journeys(self, results: Dict[str, Any]):
        """Render user journeys tab"""
        st.subheader("🛤️ " + t('analysis.user_conversion_journeys', 'User Conversion Journeys'))
        
        user_journeys = results.get('user_journeys', [])
        if not user_journeys:
            st.info(t('analysis.no_journey_data', 'No user journey data available'))
            return
        
        # Journey statistics
        col1, col2, col3 = st.columns(3)
        
        total_journeys = len(user_journeys)
        converted_journeys = len([j for j in user_journeys if j.conversion_status == 'converted'])
        conversion_rate = (converted_journeys / total_journeys * 100) if total_journeys > 0 else 0
        
        with col1:
            st.metric(t('analysis.total_journeys', 'Total Journeys'), f"{total_journeys:,}")
        
        with col2:
            st.metric(t('analysis.converted_journeys', 'Converted Journeys'), f"{converted_journeys:,}")
        
        with col3:
            st.metric(t('analysis.journey_conversion_rate', 'Journey Conversion Rate'), f"{conversion_rate:.1f}%")
        
        # Journey status distribution
        st.subheader("📈 " + t('analysis.journey_status_distribution', 'Journey Status Distribution'))
        
        status_counts = {}
        for journey in user_journeys:
            status = journey.conversion_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title=t('analysis.journey_status_breakdown', 'User Journey Status Breakdown')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Journey samples
        st.subheader("🔍 " + t('analysis.journey_samples', 'Journey Samples'))
        
        # Display first 10 journeys
        journey_data = []
        for i, journey in enumerate(user_journeys[:10]):
            steps_text = ' → '.join([step['step_name'] for step in journey.journey_steps])
            journey_data.append({
                t('analysis.user_id', 'User ID'): journey.user_id,
                t('analysis.conversion_status', 'Conversion Status'): journey.conversion_status,
                t('analysis.journey_steps', 'Journey Steps'): steps_text,
                t('analysis.total_duration_min', 'Total Duration (min)'): f"{journey.total_journey_time/60:.1f}" if journey.total_journey_time else 'N/A',
                t('analysis.dropoff_step', 'Drop-off Step'): journey.drop_off_step or 'N/A'
            })
        
        if journey_data:
            df = pd.DataFrame(journey_data)
            st.dataframe(df, use_container_width=True)
    
    def _render_insights_and_recommendations(self, results: Dict[str, Any]):
        """Render insights and recommendations tab"""
        st.subheader("💡 " + t('analysis.insights_and_recommendations', 'Insights & Recommendations'))
        
        conversion_result = results.get('conversion_result')
        if not conversion_result:
            st.info(t('analysis.no_insights_data', 'No insights data available'))
            return
        
        # Get insights
        engine = st.session_state.conversion_engine
        insights = engine.get_conversion_insights(conversion_result)
        
        # Key metrics insights
        if insights.get('key_metrics'):
            st.subheader("📊 " + t('analysis.key_insights', 'Key Insights'))
            metrics = insights['key_metrics']
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**{t('analysis.avg_conversion_rate', 'Average Conversion Rate')}**: {metrics.get('avg_conversion_rate', 0):.1%}")
                st.info(f"**{t('analysis.best_conversion_rate', 'Best Conversion Rate')}**: {metrics.get('best_conversion_rate', 0):.1%}")
            
            with col2:
                st.info(f"**{t('analysis.worst_conversion_rate', 'Worst Conversion Rate')}**: {metrics.get('worst_conversion_rate', 0):.1%}")
                st.info(f"**{t('analysis.total_funnels_analyzed', 'Total Funnels Analyzed')}**: {metrics.get('total_funnels_analyzed', 0)}")
        
        # Optimization opportunities
        if insights.get('optimization_opportunities'):
            st.subheader("🎯 " + t('analysis.optimization_opportunities', 'Optimization Opportunities'))
            for opportunity in insights['optimization_opportunities']:
                with st.expander(f"🔧 {opportunity.get('funnel', 'Unknown')} - {opportunity.get('bottleneck_step', 'Unknown')}"):
                    st.write(f"**{t('analysis.conversion_rate', 'Conversion Rate')}**: {opportunity.get('conversion_rate', 0):.1%}")
                    st.write(f"**{t('analysis.improvement_suggestion', 'Improvement Suggestion')}**: {opportunity.get('improvement_potential', 'N/A')}")
        
        # Performance insights
        if insights.get('performance_insights'):
            st.subheader("🏆 " + t('analysis.performance_insights', 'Performance Insights'))
            for insight in insights['performance_insights']:
                st.success(insight)
        
        # Recommendations list
        if insights.get('recommendations'):
            st.subheader("📋 " + t('analysis.recommendations', 'Optimization Recommendations'))
            for i, recommendation in enumerate(insights['recommendations'], 1):
                st.write(f"**{i}.** {recommendation}")
        
        # Attribution analysis insights
        attribution_result = results.get('attribution_result')
        if attribution_result and attribution_result.get('attribution_insights'):
            st.subheader("🎯 " + t('analysis.attribution_insights', 'Attribution Insights'))
            for insight in attribution_result['attribution_insights']:
                st.info(insight)


@render_data_status_check
def show_conversion_analysis_page():
    """Show conversion analysis page - maintain backward compatibility"""
    page = ConversionAnalysisPage()
    page.render()
