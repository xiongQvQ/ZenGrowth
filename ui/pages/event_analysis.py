"""
Event Analysis Page Component
Handles analysis and visualization of user event data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from engines.event_analysis_engine import EventAnalysisEngine
from visualization.chart_generator import ChartGenerator
from utils.i18n import t
from ui.components.common import render_no_data_warning


# Time granularity mapping (consistent with main.py)
TIME_GRANULARITY_MAPPING = {
    "日": "daily",
    "周": "weekly", 
    "月": "monthly",
    "Daily": "daily",
    "Weekly": "weekly",
    "Monthly": "monthly",
    "day": "daily",
    "week": "weekly",
    "month": "monthly"
}


def translate_time_granularity(chinese_term: str) -> str:
    """Translate Chinese time granularity to English"""
    return TIME_GRANULARITY_MAPPING.get(chinese_term, chinese_term)


class EventAnalysisPage:
    """Event Analysis Page Class"""
    
    def __init__(self):
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize analysis engines and visualization components"""
        if 'event_engine' not in st.session_state:
            st.session_state.event_engine = EventAnalysisEngine()
        if 'chart_generator' not in st.session_state:
            st.session_state.chart_generator = ChartGenerator()
    
    def render(self):
        """Render event analysis page"""
        from ui.state import get_state_manager
        
        # Check data status
        state_manager = get_state_manager()
        if not state_manager.is_data_loaded():
            render_no_data_warning()
            return
        
        st.header(t('analysis.event_title', 'Event Analysis'))
        
        # Analysis control panel
        config = self._render_analysis_config()
        
        # Execute analysis button
        if st.button(t('analysis.start_event_analysis', 'Start Event Analysis'), type="primary"):
            self._execute_analysis(config)
        
        # Display analysis results
        if 'event_analysis_results' in st.session_state:
            self._render_analysis_results()
    
    def _render_analysis_config(self) -> Dict[str, Any]:
        """Render analysis configuration panel"""
        from ui.state import get_state_manager
        
        with st.expander(t('analysis.analysis_config_expander', 'Analysis Configuration'), expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_range = st.date_input(
                    t('analysis.time_range_label', 'Time Range'),
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    help=t('analysis.time_range_help', 'Select the time period for analysis')
                )
            
            with col2:
                state_manager = get_state_manager()
                data_summary = state_manager.get_data_summary()
                event_types = list(data_summary.get('event_types', {}).keys()) if data_summary else []
                event_filter = st.multiselect(
                    t('analysis.event_filter_label', 'Event Filter'),
                    options=event_types,
                    default=event_types[:5] if event_types else [],
                    help=t('analysis.event_filter_help', 'Select event types to include in analysis')
                )
            
            with col3:
                analysis_granularity = st.selectbox(
                    t('analysis.analysis_granularity_label', 'Analysis Granularity'),
                    options=[t('analysis.daily', 'Daily'), t('analysis.weekly', 'Weekly'), t('analysis.monthly', 'Monthly')],
                    index=0,
                    help=t('analysis.analysis_granularity_help', 'Choose the time granularity for trend analysis')
                )
        
        return {
            'date_range': date_range,
            'event_filter': event_filter,
            'analysis_granularity': analysis_granularity
        }
    
    def _execute_analysis(self, config: Dict[str, Any]):
        """Execute event analysis"""
        from ui.state import get_state_manager
        
        with st.spinner(t('analysis.event_analysis_processing', 'Processing event analysis...')):
            try:
                # Get data
                state_manager = get_state_manager()
                raw_data = state_manager.get_raw_data()
                
                # Apply filters
                filtered_data = self._filter_data(raw_data, config)
                
                # Execute analysis
                engine = st.session_state.event_engine
                
                # Event frequency analysis
                frequency_results = engine.analyze_event_frequency(filtered_data)
                
                # Event trend analysis - convert Chinese granularity to English
                english_granularity = translate_time_granularity(config['analysis_granularity'])
                trend_results = engine.analyze_event_trends(filtered_data, time_granularity=english_granularity)
                
                # Store analysis results
                st.session_state.event_analysis_results = {
                    'frequency': frequency_results,
                    'trends': trend_results,
                    'filtered_data': filtered_data,
                    'config': config
                }
                
                st.success(t('analysis.event_analysis_complete', 'Event analysis completed successfully!'))
                
            except Exception as e:
                st.error(f"{t('analysis.analysis_failed', 'Analysis failed')}: {str(e)}")
    
    def _filter_data(self, raw_data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Filter data based on configuration"""
        filtered_data = raw_data.copy()
        
        # Event type filtering
        if config['event_filter']:
            filtered_data = filtered_data[filtered_data['event_name'].isin(config['event_filter'])]
        
        # Time range filtering (if needed)
        # Time range filtering logic can be added here
        
        return filtered_data
    
    def _render_analysis_results(self):
        """Render analysis results"""
        if 'event_analysis_results' not in st.session_state:
            st.warning(t('errors.no_analysis_results', 'No analysis results found. Please run analysis first.'))
            return
            
        results = st.session_state.event_analysis_results
        chart_gen = st.session_state.chart_generator
        
        # Validate results structure
        if not isinstance(results, dict):
            st.error(t('errors.analysis_result_format_error', 'Invalid analysis result format'))
            return
        
        st.markdown("---")
        st.subheader(t('analysis.analysis_results_header', 'Analysis Results'))
        
        # Key metrics overview
        self._render_key_metrics(results)
        
        # Event timeline chart
        self._render_timeline_chart(results, chart_gen)
        
        # Event frequency distribution and user activity distribution
        self._render_distribution_charts(results)
        
        # Detailed data table
        self._render_detailed_data(results)
    
    def _render_key_metrics(self, results: Dict[str, Any]):
        """Render key metrics"""
        col1, col2, col3, col4 = st.columns(4)
        
        # Defensive check to ensure filtered_data exists
        if 'filtered_data' not in results:
            st.error(t('errors.filter_data_missing', 'Filtered data is missing from results'))
            return
            
        filtered_data = results['filtered_data']
        
        with col1:
            total_events = len(filtered_data)
            st.metric(t('analysis.total_events', 'Total Events'), f"{total_events:,}")
        
        with col2:
            unique_users = filtered_data['user_pseudo_id'].nunique()
            st.metric(t('analysis.active_users', 'Active Users'), f"{unique_users:,}")
        
        with col3:
            avg_events_per_user = total_events / unique_users if unique_users > 0 else 0
            st.metric(t('analysis.avg_events_per_user', 'Avg Events per User'), f"{avg_events_per_user:.1f}")
        
        with col4:
            event_types = filtered_data['event_name'].nunique()
            st.metric(t('analysis.event_types_count', 'Event Types'), f"{event_types}")
    
    def _render_timeline_chart(self, results: Dict[str, Any], chart_gen: ChartGenerator):
        """Render timeline chart"""
        st.subheader(t('analysis.event_timeline', 'Event Timeline'))
        
        # Defensive check to ensure filtered_data exists
        if 'filtered_data' not in results:
            st.error(t('errors.timeline_chart_failed', 'Failed to render timeline chart'))
            return
            
        try:
            timeline_chart = chart_gen.create_event_timeline(results['filtered_data'])
            st.plotly_chart(timeline_chart, use_container_width=True)
        except Exception as e:
            st.error(f"{t('analysis.timeline_chart_failed', 'Timeline chart failed')}: {str(e)}")
    
    def _render_distribution_charts(self, results: Dict[str, Any]):
        """Render distribution charts"""
        col1, col2 = st.columns(2)
        
        # Defensive check to ensure filtered_data exists
        if 'filtered_data' not in results:
            st.error(t('errors.distribution_chart_failed', 'Failed to render distribution charts'))
            return
            
        filtered_data = results['filtered_data']
        
        with col1:
            st.subheader(t('analysis.event_frequency_distribution', 'Event Frequency Distribution'))
            event_counts = filtered_data['event_name'].value_counts()
            st.bar_chart(event_counts)
        
        with col2:
            st.subheader(t('analysis.user_activity_distribution', 'User Activity Distribution'))
            self._render_user_activity_histogram(filtered_data)
    
    def _render_user_activity_histogram(self, filtered_data: pd.DataFrame):
        """Render user activity histogram"""
        user_activity = filtered_data.groupby('user_pseudo_id').size()
        
        # Create user activity distribution histogram
        activity_df = pd.DataFrame({
            'user_id': user_activity.index,
            'event_count': user_activity.values
        })
        
        fig = px.histogram(
            activity_df,
            x='event_count',
            nbins=20,
            title=t('analysis.user_event_count_distribution', 'User Event Count Distribution'),
            labels={'event_count': t('analysis.event_count', 'Event Count'), 'count': t('analysis.user_count', 'User Count')}
        )
        fig.update_layout(
            xaxis_title=t('analysis.event_count', 'Event Count'),
            yaxis_title=t('analysis.user_count', 'User Count'),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_detailed_data(self, results: Dict[str, Any]):
        """Render detailed data table"""
        with st.expander(t('analysis.detailed_data', 'Detailed Data'), expanded=False):
            # Defensive check to ensure filtered_data exists
            if 'filtered_data' not in results:
                st.error(t('errors.detailed_data_failed', 'Failed to render detailed data'))
                return
                
            filtered_data = results['filtered_data']
            display_columns = ['event_date', 'event_name', 'user_pseudo_id', 'platform']
            
            # Ensure columns exist
            available_columns = [col for col in display_columns if col in filtered_data.columns]
            
            st.dataframe(
                filtered_data[available_columns].head(1000),
                use_container_width=True
            )


def show_event_analysis_page():
    """Event analysis page entry function - maintain backward compatibility"""
    page = EventAnalysisPage()
    page.render()