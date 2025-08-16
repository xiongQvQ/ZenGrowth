"""
Path Analysis Page
Analyzes user behavior paths and flows
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import numpy as np

from engines.path_analysis_engine import PathAnalysisEngine
from visualization.chart_generator import ChartGenerator
from visualization.advanced_visualizer import AdvancedVisualizer
from utils.i18n import t
from ui.components.common import render_no_data_warning, render_data_status_check

class PathAnalysisPage:
    """Path analysis page class"""
    
    def __init__(self):
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize analysis engines and visualization components"""
        if 'path_engine' not in st.session_state:
            st.session_state.path_engine = PathAnalysisEngine()
        if 'chart_generator' not in st.session_state:
            st.session_state.chart_generator = ChartGenerator()
        if 'advanced_visualizer' not in st.session_state:
            st.session_state.advanced_visualizer = AdvancedVisualizer()
    
    def render(self):
        """Render path analysis page"""
        from ui.state import get_state_manager
        
        # Check data status
        state_manager = get_state_manager()
        if not state_manager.is_data_loaded():
            render_no_data_warning()
            return
        
        st.header(t("path_analysis", "🛤️ Path Analysis"))
        st.markdown("---")
        
        # Analysis configuration panel
        config = self._render_analysis_config()
        
        # Execute analysis button
        if st.button(t('start_path_analysis', '🚀 Start Path Analysis'), type="primary"):
            self._execute_path_analysis(config)
        
        # Display analysis results
        if 'path_analysis_results' in st.session_state:
            self._render_analysis_results()
    
    def _render_analysis_config(self) -> Dict[str, Any]:
        """Render analysis configuration panel"""
        with st.expander(t('analysis.path_config', 'Path Analysis Configuration'), expanded=False):
            
            # Basic configuration
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_range = st.date_input(
                    t('analysis.time_range_label', 'Time Range'),
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    help=t('analysis.time_range_help', 'Select time range for analysis')
                )
            
            with col2:
                analysis_type = st.selectbox(
                    t('analysis.path_analysis_type', 'Analysis Type'),
                    options=[
                        t('analysis.session_reconstruction', 'Session Reconstruction'),
                        t('analysis.pattern_mining', 'Pattern Mining'),
                        t('analysis.flow_analysis', 'Flow Analysis'),
                        t('analysis.comprehensive_path', 'Comprehensive Path Analysis')
                    ],
                    index=3,
                    help=t('analysis.path_type_help', 'Select type of path analysis')
                )
            
            with col3:
                session_timeout = st.slider(
                    t('analysis.session_timeout', 'Session Timeout (minutes)'),
                    min_value=5,
                    max_value=120,
                    value=30,
                    help=t('analysis.session_timeout_help', 'Session intervals exceeding this time are considered new sessions')
                )
            
            # Advanced configuration
            with st.expander(t('analysis.advanced_config', 'Advanced Configuration'), expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    min_path_length = st.slider(
                        t('analysis.min_path_length', 'Minimum Path Length'),
                        min_value=1,
                        max_value=20,
                        value=2,
                        help=t('analysis.min_path_help', 'Minimum number of steps in analyzed paths')
                    )
                    
                    max_path_length = st.slider(
                        t('analysis.max_path_length', 'Maximum Path Length'),
                        min_value=3,
                        max_value=50,
                        value=15,
                        help=t('analysis.max_path_help', 'Maximum number of steps in analyzed paths')
                    )
                
                with col2:
                    min_pattern_frequency = st.slider(
                        t('analysis.min_pattern_freq', 'Minimum Pattern Frequency'),
                        min_value=1,
                        max_value=100,
                        value=5,
                        help=t('analysis.pattern_freq_help', 'Minimum number of times a pattern must appear')
                    )
                    
                    include_anomalies = st.checkbox(
                        t('analysis.include_anomalies', 'Include Anomalous Paths'),
                        value=True,
                        help=t('analysis.anomalies_help', 'Identify and analyze anomalous user paths')
                    )
            
            # Specific path analysis configuration
            specific_paths = []
            if analysis_type in [t('analysis.flow_analysis', 'Flow Analysis'), t('analysis.comprehensive_path', 'Comprehensive Path Analysis')]:
                st.subheader(t('analysis.specific_path_config', 'Specific Path Configuration'))
                
                # Get available event types
                from ui.state import get_state_manager
                state_manager = get_state_manager()
                data_summary = state_manager.get_data_summary()
                event_types = list(data_summary.get('event_types', {}).keys()) if data_summary else []
                
                if event_types:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        start_events = st.multiselect(
                            t('analysis.start_events', 'Start Events'),
                            options=event_types,
                            default=[],
                            help=t('analysis.start_events_help', 'Select starting events for path analysis')
                        )
                    
                    with col2:
                        end_events = st.multiselect(
                            t('analysis.end_events', 'End Events'),
                            options=event_types,
                            default=[],
                            help=t('analysis.end_events_help', 'Select ending events for path analysis')
                        )
                    
                    specific_paths = start_events + end_events
                else:
                    st.warning(t('analysis.no_event_types', 'No available event types'))
        
        return {
            'date_range': date_range,
            'analysis_type': analysis_type,
            'session_timeout': session_timeout,
            'min_path_length': min_path_length,
            'max_path_length': max_path_length,
            'min_pattern_frequency': min_pattern_frequency,
            'include_anomalies': include_anomalies,
            'specific_paths': specific_paths
        }
    
    def _execute_path_analysis(self, config: Dict[str, Any]):
        """Execute path analysis"""
        from ui.state import get_state_manager
        
        with st.spinner(t('analysis.path_processing', 'Executing path analysis...')):
            try:
                # Get data
                state_manager = get_state_manager()
                raw_data = state_manager.get_raw_data()
                
                if raw_data.empty:
                    st.error(t('analysis.no_data', 'No data available for analysis'))
                    return
                
                # Initialize engine
                engine = st.session_state.path_engine
                engine.session_timeout_minutes = config.get('session_timeout', 30)
                engine.min_pattern_frequency = config.get('min_pattern_frequency', 5)
                
                # Apply time filtering
                filtered_data = self._filter_data_by_time(raw_data, config['date_range'])
                
                # Execute path analysis
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Step 1: Session reconstruction
                status_text.text(t('analysis.step_session_reconstruction', 'Reconstructing user sessions...'))
                progress_bar.progress(20)
                
                sessions = engine.reconstruct_user_sessions(filtered_data)
                
                # Step 2: Path pattern identification
                status_text.text(t('analysis.step_pattern_identification', 'Identifying path patterns...'))
                progress_bar.progress(50)
                
                path_patterns = engine.identify_path_patterns(sessions)
                
                # Step 3: Path mining
                status_text.text(t('analysis.step_path_mining', 'Mining user paths...'))
                progress_bar.progress(70)
                
                mined_paths = engine.mine_user_paths(
                    filtered_data, 
                    min_length=config.get('min_path_length', 2),
                    max_length=config.get('max_path_length', 15)
                )
                
                # Step 4: Generate insights
                status_text.text(t('analysis.step_generating_insights', 'Generating analysis insights...'))
                progress_bar.progress(90)
                
                insights = self._generate_path_insights(sessions, path_patterns, mined_paths)
                
                # Complete analysis
                status_text.text(t('analysis.step_completed', 'Analysis completed'))
                progress_bar.progress(100)
                
                # Store analysis results
                results = {
                    'sessions': sessions,
                    'path_patterns': path_patterns,
                    'mined_paths': mined_paths,
                    'insights': insights,
                    'config': config,
                    'data_size': len(filtered_data),
                    'analysis_time': datetime.now().isoformat()
                }
                
                # Use StateManager to store results
                state_manager.set_analysis_results('path', results)
                st.session_state.path_analysis_results = results
                
                st.success(t('analysis.path_complete', '✅ Path analysis completed!'))
                
            except Exception as e:
                st.error(f"{t('analysis.analysis_failed', 'Path analysis failed')}: {str(e)}")
                import traceback
                st.text(t('common.detailed_error', 'Detailed error information:'))
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
            
            # Filter by time range
            filtered_data = data[
                (data['event_datetime'].dt.date >= start_date) &
                (data['event_datetime'].dt.date <= end_date)
            ].copy()
            
            return filtered_data
            
        except Exception as e:
            st.warning(f"{t('common.filter_failed', 'Filter failed')}: {e}")
            return data
    
    def _generate_path_insights(self, sessions, path_patterns, mined_paths):
        """Generate path analysis insights"""
        insights = {
            'basic_stats': {},
            'pattern_insights': [],
            'flow_insights': [],
            'recommendations': []
        }
        
        # Basic statistics
        if sessions:
            total_sessions = len(sessions)
            avg_path_length = np.mean([len(s.path_sequence) for s in sessions])
            max_path_length = max([len(s.path_sequence) for s in sessions])
            
            # Process PathAnalysisResult object
            total_patterns = 0
            if path_patterns and hasattr(path_patterns, 'common_patterns'):
                total_patterns = (
                    len(path_patterns.common_patterns) + 
                    len(path_patterns.anomalous_patterns) + 
                    len(path_patterns.conversion_paths) + 
                    len(path_patterns.exit_patterns)
                )
            
            insights['basic_stats'] = {
                'total_sessions': total_sessions,
                'avg_path_length': avg_path_length,
                'max_path_length': max_path_length,
                'total_patterns': total_patterns
            }
        
        # Pattern insights
        if path_patterns and hasattr(path_patterns, 'common_patterns'):
            common_patterns = path_patterns.common_patterns
            conversion_patterns = path_patterns.conversion_paths
            
            if common_patterns:
                top_pattern = max(common_patterns, key=lambda x: x.frequency)
                insights['pattern_insights'].append(f"{t('analysis.most_common_path', 'Most common path')}: {' → '.join(top_pattern.path_sequence)}")
                insights['pattern_insights'].append(f"{t('analysis.frequency', 'Frequency')}: {top_pattern.frequency} {t('common.times', 'times')}")
            
            if conversion_patterns:
                insights['pattern_insights'].append(f"{t('analysis.found_conversion_patterns', 'Found {count} conversion path patterns').format(count=len(conversion_patterns))}")
        
        # Recommendations
        insights['recommendations'] = [
            t('analysis.recommendation_optimize_paths', 'Optimize the most common user paths to improve user experience'),
            t('analysis.recommendation_analyze_anomalies', 'Analyze anomalous path patterns to discover potential user confusion points'),
            t('analysis.recommendation_focus_conversion', 'Focus on conversion path patterns to improve conversion efficiency')
        ]
        
        return insights
    
    def _render_analysis_results(self):
        """Render analysis results"""
        results = st.session_state.path_analysis_results
        
        if not results:
            st.warning(t('analysis.no_results', 'No analysis results to display'))
            return
        
        st.markdown("---")
        st.subheader("🛤️ " + t('path_results', 'Path Analysis Results'))
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 " + t('overview', 'Overview'),
            "🗺️ " + t('path_patterns', 'Path Patterns'),
            "📈 " + t('visualizations', 'Visualizations'),
            "🔍 " + t('sessions', 'Session Details'),
            "💡 " + t('insights', 'Insights & Recommendations')
        ])
        
        with tab1:
            self._render_overview(results)
        
        with tab2:
            self._render_path_patterns(results)
        
        with tab3:
            self._render_visualizations(results)
        
        with tab4:
            self._render_session_details(results)
        
        with tab5:
            self._render_insights_and_recommendations(results)
    
    def _render_overview(self, results: Dict[str, Any]):
        """Render overview tab"""
        st.subheader("📊 " + t('analysis.key_metrics', 'Key Metrics'))
        
        sessions = results.get('sessions', [])
        path_patterns = results.get('path_patterns', [])
        insights = results.get('insights', {})
        
        if not sessions:
            st.info(t('analysis.no_session_data', 'No session data available'))
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        basic_stats = insights.get('basic_stats', {})
        
        with col1:
            st.metric(
                t('analysis.total_sessions', 'Total Sessions'),
                f"{basic_stats.get('total_sessions', 0):,}",
                help=t('analysis.sessions_help', 'Total number of user sessions analyzed')
            )
        
        with col2:
            st.metric(
                t('analysis.avg_path_length', 'Average Path Length'),
                f"{basic_stats.get('avg_path_length', 0):.1f}",
                help=t('analysis.path_length_help', 'Average number of steps in user paths')
            )
        
        with col3:
            st.metric(
                t('analysis.max_path_length', 'Maximum Path Length'),
                f"{basic_stats.get('max_path_length', 0)}",
                help=t('analysis.max_path_help', 'Maximum number of steps in user paths')
            )
        
        with col4:
            st.metric(
                t('analysis.total_patterns', 'Identified Patterns'),
                f"{basic_stats.get('total_patterns', 0)}",
                help=t('analysis.patterns_help', 'Total number of identified path patterns')
            )
        
        # Path length distribution
        st.subheader("📏 " + t('analysis.path_length_distribution', 'Path Length Distribution'))
        
        path_lengths = [len(s.path_sequence) for s in sessions if hasattr(s, 'path_sequence') and s.path_sequence]
        
        if path_lengths:
            fig = px.histogram(
                x=path_lengths,
                nbins=min(20, max(path_lengths)),
                title=t('analysis.path_length_hist', 'User Path Length Distribution'),
                labels={'x': t('analysis.path_length', 'Path Length'), 'y': t('analysis.session_count', 'Session Count')}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Session duration distribution
        st.subheader("⏱️ " + t('analysis.session_duration_distribution', 'Session Duration Distribution'))
        
        durations = [s.duration_seconds / 60 for s in sessions if hasattr(s, 'duration_seconds') and s.duration_seconds and s.duration_seconds > 0]  # Convert to minutes
        
        if durations:
            fig = px.histogram(
                x=durations,
                nbins=20,
                title=t('analysis.session_duration_hist', 'Session Duration Distribution'),
                labels={'x': t('analysis.duration_minutes', 'Duration (minutes)'), 'y': t('analysis.session_count', 'Session Count')}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_path_patterns(self, results: Dict[str, Any]):
        """Render path patterns tab"""
        st.subheader("🗺️ " + t('analysis.identified_patterns', 'Identified Path Patterns'))
        
        path_patterns = results.get('path_patterns')
        
        if not path_patterns or not hasattr(path_patterns, 'common_patterns'):
            st.info(t('analysis.no_patterns', 'No path patterns available'))
            return
        
        # Get patterns by type
        pattern_types = {
            'common': path_patterns.common_patterns,
            'conversion': path_patterns.conversion_paths,
            'anomalous': path_patterns.anomalous_patterns,
            'exit': path_patterns.exit_patterns
        }
        
        # Display patterns by type
        for pattern_type, patterns in pattern_types.items():
            if not patterns:
                continue
                
            if pattern_type == 'common':
                st.subheader("🔥 " + t('analysis.common_patterns', 'Common Path Patterns'))
            elif pattern_type == 'conversion':
                st.subheader("🎯 " + t('analysis.conversion_patterns', 'Conversion Path Patterns'))
            elif pattern_type == 'anomalous':
                st.subheader("⚠️ " + t('analysis.anomalous_patterns', 'Anomalous Path Patterns'))
            elif pattern_type == 'exit':
                st.subheader("🚪 " + t('analysis.exit_patterns', 'Exit Path Patterns'))
            
            # Display pattern table
            pattern_data = []
            for pattern in patterns[:10]:  # Display first 10 patterns
                pattern_data.append({
                    t('analysis.path_pattern', 'Path Pattern'): ' → '.join(pattern.path_sequence),
                    t('analysis.frequency', 'Frequency'): pattern.frequency,
                    t('analysis.user_count', 'User Count'): pattern.user_count,
                    t('analysis.avg_duration_minutes', 'Avg Duration (minutes)'): f"{pattern.avg_duration/60:.1f}" if pattern.avg_duration else 'N/A',
                    t('analysis.conversion_rate', 'Conversion Rate'): f"{pattern.conversion_rate:.1%}" if pattern.conversion_rate else 'N/A'
                })
            
            if pattern_data:
                df = pd.DataFrame(pattern_data)
                st.dataframe(df, use_container_width=True)
                
                if len(patterns) > 10:
                    st.info(t('analysis.showing_top_patterns', 'Showing top 10 patterns, found {count} {type} patterns').format(count=len(patterns), type=pattern_type))
    
    def _render_visualizations(self, results: Dict[str, Any]):
        """Render visualizations tab"""
        st.subheader("📈 " + t('analysis.path_visualizations', 'Path Visualizations'))
        
        sessions = results.get('sessions', [])
        path_patterns = results.get('path_patterns', [])
        
        if not sessions:
            st.info(t('analysis.no_visualization_data', 'No visualization data available'))
            return
        
        # Path flow chart
        self._create_path_flow_chart(sessions)
        
        # Pattern frequency chart
        if path_patterns:
            self._create_pattern_frequency_chart(path_patterns)
        
        # Path sankey diagram
        self._create_path_sankey_diagram(sessions)
    
    def _create_path_flow_chart(self, sessions):
        """Create path flow chart"""
        st.subheader("🌊 " + t('analysis.path_flow_chart', 'Path Flow Chart'))
        
        # Count event transitions
        transitions = {}
        
        for session in sessions:
            if hasattr(session, 'path_sequence') and session.path_sequence:
                path = session.path_sequence
                for i in range(len(path) - 1):
                    current = path[i]
                    next_event = path[i + 1]
                    transition = f"{current} → {next_event}"
                    transitions[transition] = transitions.get(transition, 0) + 1
        
        if transitions:
            # Get top 20 most common transitions
            top_transitions = sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:20]
            
            transition_names = [item[0] for item in top_transitions]
            transition_counts = [item[1] for item in top_transitions]
            
            fig = px.bar(
                x=transition_counts,
                y=transition_names,
                orientation='h',
                title=t('analysis.top_transitions', 'Most Common Path Transitions'),
                labels={'x': t('analysis.transition_count', 'Transition Count'), 'y': t('analysis.transition', 'Transition')}
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
    
    def _create_pattern_frequency_chart(self, path_patterns):
        """Create pattern frequency chart"""
        st.subheader("📊 " + t('analysis.pattern_frequency_chart', 'Pattern Frequency Chart'))
        
        if not path_patterns or not hasattr(path_patterns, 'common_patterns'):
            st.info(t('analysis.no_pattern_data', 'No pattern data available'))
            return
        
        # Group statistics by type
        pattern_type_counts = {
            'common': len(path_patterns.common_patterns),
            'conversion': len(path_patterns.conversion_paths),
            'anomalous': len(path_patterns.anomalous_patterns),
            'exit': len(path_patterns.exit_patterns)
        }
        
        # Filter out types with count 0
        pattern_type_counts = {k: v for k, v in pattern_type_counts.items() if v > 0}
        
        if pattern_type_counts:
            type_names = list(pattern_type_counts.keys())
            type_counts = list(pattern_type_counts.values())
            
            fig = px.pie(
                values=type_counts,
                names=type_names,
                title=t('analysis.pattern_type_distribution', 'Path Pattern Type Distribution')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Display patterns with highest frequency
        all_patterns = (
            path_patterns.common_patterns + 
            path_patterns.conversion_paths + 
            path_patterns.anomalous_patterns + 
            path_patterns.exit_patterns
        )
        
        if all_patterns:
            top_patterns = sorted(all_patterns, key=lambda x: x.frequency, reverse=True)[:10]
            
            pattern_names = [' → '.join(p.path_sequence[:3]) + '...' if len(p.path_sequence) > 3 
                           else ' → '.join(p.path_sequence) for p in top_patterns]
            frequencies = [p.frequency for p in top_patterns]
            
            fig = px.bar(
                x=frequencies,
                y=pattern_names,
                orientation='h',
                title=t('analysis.top_pattern_frequencies', 'Highest Frequency Path Patterns'),
                labels={'x': t('analysis.frequency', 'Frequency'), 'y': t('analysis.pattern', 'Pattern')}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    def _create_path_sankey_diagram(self, sessions):
        """Create path sankey diagram"""
        st.subheader("🌊 " + t('analysis.path_sankey', 'Path Sankey Diagram'))
        
        # Limit display steps to avoid overly complex charts
        max_steps = 5
        
        # Count event distribution for each step
        step_events = {}
        
        for session in sessions:
            if hasattr(session, 'path_sequence') and session.path_sequence:
                path = session.path_sequence[:max_steps]  # Only take first few steps
                for step, event in enumerate(path):
                    if step not in step_events:
                        step_events[step] = {}
                    step_events[step][event] = step_events[step].get(event, 0) + 1
        
        if len(step_events) > 1:
            # Build sankey diagram data
            all_events = set()
            for step_data in step_events.values():
                all_events.update(step_data.keys())
            
            # Create unique identifier for each event
            event_to_id = {event: i for i, event in enumerate(all_events)}
            
            # Build connections
            source = []
            target = []
            value = []
            
            for session in sessions:
                if hasattr(session, 'path_sequence') and session.path_sequence:
                    path = session.path_sequence[:max_steps]
                    for i in range(len(path) - 1):
                        current_event = path[i]
                        next_event = path[i + 1]
                        
                        source.append(event_to_id[current_event])
                        target.append(event_to_id[next_event])
                    
            # Count connection weights
            connections = {}
            if source and target and len(source) == len(target):
                for s, target_val in zip(source, target):
                    key = (s, target_val)
                    connections[key] = connections.get(key, 0) + 1
            
            # Prepare final data
            final_source = []
            final_target = []
            final_value = []
            
            if connections:
                for connection_key, weight in connections.items():
                    if isinstance(connection_key, tuple) and len(connection_key) == 2:
                        s, target_node = connection_key
                        if weight > 1:  # Only show connections that appear multiple times
                            final_source.append(s)
                            final_target.append(target_node)
                            final_value.append(weight)
            
            if final_source:
                # Create sankey diagram
                fig = go.Figure(data=[go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=list(all_events),
                    ),
                    link=dict(
                        source=final_source,
                        target=final_target,
                        value=final_value
                    )
                )])
                
                fig.update_layout(
                    title_text=t('analysis.user_path_flow', 'User Path Flow'),
                    font_size=10,
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_session_details(self, results: Dict[str, Any]):
        """Render session details tab"""
        st.subheader("🔍 " + t('analysis.session_details', 'Session Details'))
        
        sessions = results.get('sessions', [])
        
        if not sessions:
            st.info(t('analysis.no_session_details', 'No session details available'))
            return
        
        # Session filtering
        col1, col2 = st.columns(2)
        
        with col1:
            min_length = st.slider(
                t('analysis.filter_min_length', 'Minimum Path Length'),
                min_value=1,
                max_value=20,
                value=1,
                key='session_filter_min'
            )
        
        with col2:
            max_length = st.slider(
                t('analysis.filter_max_length', 'Maximum Path Length'),
                min_value=2,
                max_value=50,
                value=20,
                key='session_filter_max'
            )
        
        # Filter sessions
        filtered_sessions = [
            s for s in sessions 
            if min_length <= len(s.path_sequence) <= max_length
        ]
        
        st.info(t('analysis.showing_sessions', 'Showing {shown} sessions (out of {total} total)').format(shown=len(filtered_sessions), total=len(sessions)))
        
        # Display session samples
        session_data = []
        for i, session in enumerate(filtered_sessions[:20]):  # Display first 20 sessions
            path_text = ' → '.join(session.path_sequence)
            session_data.append({
                t('analysis.session_id', 'Session ID'): session.session_id,
                t('analysis.user_id', 'User ID'): session.user_id,
                t('analysis.path_length', 'Path Length'): len(session.path_sequence),
                t('analysis.duration_minutes', 'Duration (minutes)'): f"{session.duration_seconds/60:.1f}" if session.duration_seconds else 'N/A',
                t('analysis.page_views', 'Page Views'): session.page_views,
                t('analysis.conversions', 'Conversions'): session.conversions,
                t('analysis.path_sequence', 'Path Sequence'): path_text[:100] + '...' if len(path_text) > 100 else path_text
            })
        
        if session_data:
            df = pd.DataFrame(session_data)
            st.dataframe(df, use_container_width=True)
        
        if len(filtered_sessions) > 20:
            st.info(t('analysis.showing_top_sessions', 'Showing top 20 sessions, filtered {count} sessions').format(count=len(filtered_sessions)))
    
    def _render_insights_and_recommendations(self, results: Dict[str, Any]):
        """Render insights and recommendations tab"""
        st.subheader("💡 " + t('analysis.insights_and_recommendations', 'Insights & Recommendations'))
        
        insights = results.get('insights', {})
        
        # Pattern insights
        pattern_insights = insights.get('pattern_insights', [])
        if pattern_insights:
            st.subheader("🔍 " + t('analysis.pattern_insights', 'Pattern Insights'))
            for insight in pattern_insights:
                st.info(insight)
        
        # Flow insights
        flow_insights = insights.get('flow_insights', [])
        if flow_insights:
            st.subheader("🌊 " + t('analysis.flow_insights', 'Flow Insights'))
            for insight in flow_insights:
                st.success(insight)
        
        # Optimization recommendations
        recommendations = insights.get('recommendations', [])
        if recommendations:
            st.subheader("📋 " + t('analysis.optimization_recommendations', 'Optimization Recommendations'))
            for i, recommendation in enumerate(recommendations, 1):
                st.write(f"**{i}.** {recommendation}")
        
        # Additional data-based insights
        sessions = results.get('sessions', [])
        if sessions:
            st.subheader("📊 " + t('analysis.additional_insights', 'Additional Insights'))
            
            # Calculate some additional statistical information
            total_sessions = len(sessions)
            conversion_sessions = len([s for s in sessions if s.conversions > 0])
            avg_conversions = np.mean([s.conversions for s in sessions])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(t('analysis.conversion_session_ratio', 'Conversion Session Ratio'), f"{conversion_sessions/total_sessions:.1%}")
                st.metric(t('analysis.avg_conversions', 'Average Conversions'), f"{avg_conversions:.2f}")
            
            with col2:
                # Path diversity analysis
                unique_paths = set()
                for session in sessions:
                    path_str = ' → '.join(session.path_sequence)
                    unique_paths.add(path_str)
                
                path_diversity = len(unique_paths) / total_sessions if total_sessions > 0 else 0
                st.metric(t('analysis.path_diversity', 'Path Diversity'), f"{path_diversity:.2f}")
                
                # Average page views
                avg_page_views = np.mean([s.page_views for s in sessions])
                st.metric(t('analysis.avg_page_views', 'Average Page Views'), f"{avg_page_views:.1f}")


@render_data_status_check
def show_path_analysis_page():
    """Display path analysis page - maintain backward compatibility"""
    page = PathAnalysisPage()
    page.render()
