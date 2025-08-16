"""
User Segmentation Page
Perform user segmentation and feature analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from ui.components.common import render_data_status_check
from ui.state.state_manager import get_state_manager
from engines.user_segmentation_engine import UserSegmentationEngine
from visualization.advanced_visualizer import AdvancedVisualizer
from visualization.chart_generator import ChartGenerator
from utils.i18n import t

@render_data_status_check
def show_user_segmentation_page():
    """Display user segmentation page"""
    st.header("👥 " + t("pages.user_segmentation.title", "User Segmentation"))
    st.markdown("---")
    
    st.markdown(t('analysis.user_segmentation_description', 'User segmentation analysis uses machine learning algorithms to identify user groups with similar behavioral characteristics, helping you develop precise marketing strategies and personalized services.'))
    
    # Get state manager
    state_manager = get_state_manager()
    
    # Initialize analysis engines
    if 'segmentation_engine' not in st.session_state:
        st.session_state.segmentation_engine = UserSegmentationEngine()
    if 'advanced_visualizer' not in st.session_state:
        st.session_state.advanced_visualizer = AdvancedVisualizer()
    if 'chart_generator' not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()
    
    # Analysis configuration
    with st.expander(t('analysis.user_segmentation_config', 'User Segmentation Configuration'), expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            clustering_method = st.selectbox(
                t('analysis.clustering_method', 'Clustering Method'),
                options=[
                    ('kmeans', 'K-Means Clustering'),
                    ('dbscan', 'DBSCAN Clustering'),
                    ('behavioral', 'Behavioral Segmentation'),
                    ('value_based', 'Value-Based Segmentation'),
                    ('engagement', 'Engagement Segmentation')
                ],
                format_func=lambda x: x[1],
                index=0,
                help=t('analysis.clustering_method_help', 'Select the algorithm method for user segmentation')
            )
        
        with col2:
            n_clusters = st.slider(
                t('analysis.cluster_count', 'Number of Clusters'),
                min_value=3,
                max_value=10,
                value=5,
                help=t('analysis.cluster_count_help', 'Set the number of user segments to create')
            )
        
        with col3:
            include_features = st.multiselect(
                t('analysis.feature_types', 'Feature Types'),
                options=[
                    'behavioral_features',
                    'demographic_features', 
                    'engagement_features',
                    'conversion_features',
                    'temporal_features'
                ],
                default=[
                    'behavioral_features',
                    'engagement_features',
                    'conversion_features'
                ],
                format_func=lambda x: {
                    'behavioral_features': 'Behavioral Features',
                    'demographic_features': 'Demographic Features',
                    'engagement_features': 'Engagement Features',
                    'conversion_features': 'Conversion Features',
                    'temporal_features': 'Temporal Features'
                }.get(x, x),
                help=t('analysis.feature_types_help', 'Select feature types for segmentation analysis')
            )
    
    # Advanced configuration
    with st.expander(t('analysis.advanced_config', 'Advanced Configuration'), expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            enable_pca = st.checkbox(
                t('analysis.enable_pca', 'Enable PCA Dimensionality Reduction'),
                value=False,
                help=t('analysis.pca_help', 'Perform principal component analysis dimensionality reduction on high-dimensional features')
            )
            
            if enable_pca:
                pca_components = st.slider(
                    t('analysis.pca_components', 'Number of PCA Components'),
                    min_value=2,
                    max_value=10,
                    value=3
                )
        
        with col2:
            quality_threshold = st.slider(
                t('analysis.quality_threshold', 'Quality Threshold'),
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help=t('analysis.quality_threshold_help', 'Minimum requirement for clustering quality (silhouette coefficient)')
            )
            
            auto_optimize = st.checkbox(
                t('analysis.auto_optimize', 'Auto-optimize Parameters'),
                value=True,
                help=t('analysis.auto_optimize_help', 'Automatically find optimal clustering parameters')
            )
    
    # Execute user segmentation analysis
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button(t('analysis.start_segmentation_analysis', 'Start User Segmentation'), type="primary"):
            execute_segmentation_analysis(
                clustering_method[0], n_clusters, include_features,
                enable_pca, pca_components if enable_pca else None,
                quality_threshold, auto_optimize
            )
    
    with col2:
        if st.button(t('analysis.view_feature_summary', 'View Feature Summary')):
            show_feature_summary()
    
    # Display segmentation analysis results
    results = state_manager.get_analysis_results('user_segmentation')
    
    if results:
        show_segmentation_results()

def execute_segmentation_analysis(method, n_clusters, include_features, 
                                enable_pca, pca_components, quality_threshold, auto_optimize):
    """Execute user segmentation analysis"""
    state_manager = get_state_manager()
    
    # Create progress container
    progress_container = st.container()
    
    with progress_container:
        st.subheader("⚙️ " + t('analysis.user_segmentation_progress', 'User Segmentation Analysis Progress'))
        
        # Create progress bar and status display
        progress_bar = st.progress(0)
        status_text = st.empty()
        metrics_container = st.empty()
        
        try:
            status_text.text("🔍 " + t('analysis.initializing_segmentation_engine', 'Initializing segmentation engine...'))
            progress_bar.progress(10)
            
            # Get raw data
            raw_data = state_manager.get_raw_data()
            if raw_data is None or raw_data.empty:
                st.error("❌ " + t('errors.no_analysis_data', 'No analysis data found, please upload data file first'))
                return
            
            # Initialize segmentation engine
            engine = st.session_state.segmentation_engine
            
            status_text.text("📊 " + t('analysis.extracting_user_features', 'Extracting user features...'))
            progress_bar.progress(30)
            
            # Extract user features
            start_time = time.time()
            user_features = engine.extract_user_features(raw_data)
            
            if not user_features:
                st.error("❌ " + t('errors.cannot_extract_features', 'Cannot extract user features, please check data format'))
                return
            
            feature_extraction_time = time.time() - start_time
            
            status_text.text(f"🎯 " + t('analysis.executing_clustering_algorithm', 'Executing {method} clustering algorithm...').format(method=method))
            progress_bar.progress(60)
            
            # Execute clustering
            clustering_start = time.time()
            
            # Adjust parameters based on whether auto-optimization is enabled
            if auto_optimize and method == 'kmeans':
                # Try different cluster numbers to find optimal solution
                best_result = None
                best_score = -1
                
                for test_clusters in range(max(2, n_clusters-2), min(len(user_features), n_clusters+3)):
                    test_result = engine.create_user_segments(
                        user_features=user_features,
                        method=method,
                        n_clusters=test_clusters
                    )
                    
                    if test_result and test_result.quality_metrics:
                        score = test_result.quality_metrics.get('silhouette_score', 0)
                        if score > best_score and score >= quality_threshold:
                            best_score = score
                            best_result = test_result
                
                segmentation_result = best_result if best_result else engine.create_user_segments(
                    user_features=user_features,
                    method=method,
                    n_clusters=n_clusters
                )
            else:
                segmentation_result = engine.create_user_segments(
                    user_features=user_features,
                    method=method,
                    n_clusters=n_clusters
                )
            
            clustering_time = time.time() - clustering_start
            
            if not segmentation_result or not segmentation_result.segments:
                st.error("❌ " + t('errors.segmentation_failed', 'Segmentation analysis failed, please try adjusting parameters'))
                return
            
            status_text.text("📈 " + t('analysis.generating_visualizations', 'Generating visualizations...'))
            progress_bar.progress(80)
            
            # Generate visualization data
            visualizations = generate_segmentation_visualizations(segmentation_result, user_features)
            
            status_text.text("✨ " + t('analysis.analyzing_feature_importance', 'Analyzing feature importance...'))
            progress_bar.progress(90)
            
            # Analyze segment characteristics
            segment_analysis = engine.analyze_segment_characteristics(segmentation_result)
            
            # Update progress
            progress_bar.progress(100)
            status_text.text("✅ " + t('analysis.segmentation_complete', 'User segmentation analysis complete!'))
            
            total_time = time.time() - start_time
            
            # Prepare result data
            results_data = {
                'segmentation_result': segmentation_result,
                'segment_analysis': segment_analysis,
                'user_features': user_features,
                'visualizations': visualizations,
                'execution_metrics': {
                    'total_time': total_time,
                    'feature_extraction_time': feature_extraction_time,
                    'clustering_time': clustering_time,
                    'total_users': len(user_features),
                    'segments_created': len(segmentation_result.segments),
                    'quality_score': segmentation_result.quality_metrics.get('silhouette_score', 0),
                    'method_used': method
                }
            }
            
            # Store results
            state_manager.set_analysis_results('user_segmentation', results_data)
            
            # Display execution metrics
            with metrics_container.container():
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        t('analysis.analysis_time', 'Analysis Time'),
                        f"{total_time:.2f}s",
                        help=t('analysis.analysis_time_help', 'Execution time for complete segmentation analysis')
                    )
                
                with col2:
                    st.metric(
                        t('analysis.user_count', 'User Count'),
                        len(user_features),
                        help=t('analysis.user_count_help', 'Total number of users participating in segmentation analysis')
                    )
                
                with col3:
                    st.metric(
                        t('analysis.segment_count', 'Segment Count'),
                        len(segmentation_result.segments),
                        help=t('analysis.segment_count_help', 'Number of user segments identified')
                    )
                
                with col4:
                    quality_score = segmentation_result.quality_metrics.get('silhouette_score', 0)
                    st.metric(
                        t('analysis.quality_score', 'Quality Score'),
                        f"{quality_score:.3f}",
                        help=t('analysis.quality_score_help', 'Clustering quality score (silhouette coefficient)')
                    )
            
            st.success("🎉 " + t('analysis.segmentation_success', 'User segmentation analysis complete! Please check the detailed results below.'))
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ " + t('errors.segmentation_execution_failed', 'User segmentation analysis execution failed') + f": {str(e)}")
            import traceback
            st.text(t('errors.detailed_error_info', 'Detailed error information:'))
            st.text(traceback.format_exc())

def generate_segmentation_visualizations(segmentation_result, user_features):
    """Generate segmentation visualization charts"""
    try:
        visualizations = {}
        advanced_viz = st.session_state.advanced_visualizer
        
        # 1. User segmentation scatter plot
        if segmentation_result.segments:
            scatter_data = []
            for segment in segmentation_result.segments:
                for user_id in segment.user_ids:
                    # Use main features as X and Y axes
                    user_feature = next((uf for uf in user_features if uf.user_id == user_id), None)
                    if user_feature:
                        # Select two important features as coordinates
                        x_feature = user_feature.behavioral_features.get('total_events', 0)
                        y_feature = user_feature.engagement_features.get('activity_frequency', 0)
                        
                        scatter_data.append({
                            'user_id': user_id,
                            'segment': segment.segment_name,
                            'x_feature': x_feature,
                            'y_feature': y_feature
                        })
            
            if scatter_data:
                scatter_df = pd.DataFrame(scatter_data)
                scatter_chart = advanced_viz.create_user_segmentation_scatter(scatter_df)
                visualizations['segmentation_scatter'] = {
                    'chart': scatter_chart,
                    'type': 'scatter',
                    'title': 'User Segmentation Scatter Plot'
                }
        
        # 2. Feature radar chart
        if segmentation_result.feature_importance:
            radar_data = []
            top_features = sorted(
                segmentation_result.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:6]  # Take top 6 important features
            
            for segment in segmentation_result.segments:
                for feature_name, _ in top_features:
                    feature_value = segment.avg_features.get(feature_name, 0)
                    radar_data.append({
                        'segment': segment.segment_name,
                        'feature_name': feature_name,
                        'feature_value': feature_value
                    })
            
            if radar_data:
                radar_df = pd.DataFrame(radar_data)
                radar_chart = advanced_viz.create_feature_radar_chart(radar_df)
                visualizations['feature_radar'] = {
                    'chart': radar_chart,
                    'type': 'radar',
                    'title': 'Segment Feature Radar Chart'
                }
        
        # 3. Segment size distribution chart
        segment_size_data = []
        for segment in segmentation_result.segments:
            segment_size_data.append({
                'segment_name': segment.segment_name,
                'user_count': segment.user_count,
                'percentage': segment.user_count / sum(s.user_count for s in segmentation_result.segments) * 100
            })
        
        if segment_size_data:
            size_df = pd.DataFrame(segment_size_data)
            chart_gen = st.session_state.chart_generator
            
            # Create pie chart to display segment distribution
            import plotly.graph_objects as go
            pie_chart = go.Figure(data=[go.Pie(
                labels=size_df['segment_name'],
                values=size_df['user_count'],
                hole=0.3,
                hovertemplate='<b>%{label}</b><br>' +
                             'User Count: %{value}<br>' +
                             'Percentage: %{percent}<br>' +
                             '<extra></extra>',
                textinfo='label+percent',
                textposition='auto'
            )])
            
            pie_chart.update_layout(
                title='User Segment Distribution',
                height=500,
                template='plotly_white',
                showlegend=True
            )
            
            visualizations['segment_distribution'] = {
                'chart': pie_chart,
                'type': 'pie',
                'title': 'User Segment Distribution'
            }
        
        return visualizations
        
    except Exception as e:
        st.warning(f"Visualization generation failed: {e}")
        return {}

def show_feature_summary():
    """Display feature summary"""
    state_manager = get_state_manager()
    engine = st.session_state.segmentation_engine
    
    # Set data storage manager
    engine.storage_manager = state_manager
    
    with st.spinner("Analyzing features..."):
        try:
            summary = engine.get_analysis_summary()
            
            if 'error' in summary:
                st.error(f"❌ Failed to get feature summary: {summary['error']}")
                return
            
            st.subheader("📊 Data Feature Summary")
            
            # Basic data statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Events", f"{summary['total_events']:,}")
            with col2:
                st.metric("Unique Users", summary['unique_users'])
            with col3:
                st.metric("Event Types", summary['unique_event_types'])
            with col4:
                st.metric("User Records", summary['total_user_records'])
            
            # Time range
            st.write("**📅 Data Time Range:**")
            st.write(f"From {summary['date_range']['start']} to {summary['date_range']['end']}")
            
            # Available clustering methods
            st.write("**🔧 Available Clustering Methods:**")
            methods_display = {
                'kmeans': 'K-Means Clustering',
                'dbscan': 'DBSCAN Clustering',
                'behavioral': 'Behavioral Segmentation',
                'value_based': 'Value-Based Segmentation',
                'engagement': 'Engagement Segmentation'
            }
            
            method_cols = st.columns(len(summary['available_methods']))
            for i, method in enumerate(summary['available_methods']):
                with method_cols[i]:
                    st.info(f"✅ {methods_display.get(method, method)}")
            
            # Feature type descriptions
            st.write("**📈 Available Feature Types:**")
            for feature_type, features in summary['feature_types'].items():
                with st.expander(f"{feature_type.replace('_', ' ').title()}", expanded=False):
                    st.write("Main Features:")
                    for feature in features:
                        st.write(f"• {feature}")
            
            # Recommended clustering range
            cluster_range = summary['recommended_cluster_range']
            st.info(f"💡 **Recommended Number of Clusters**: {cluster_range[0]} - {cluster_range[1]}")
            
        except Exception as e:
            st.error(f"❌ Failed to analyze feature summary: {str(e)}")

def show_segmentation_results():
    """Display segmentation analysis results"""
    state_manager = get_state_manager()
    results = state_manager.get_analysis_results('user_segmentation')
    
    if not results:
        st.info(t('analysis.no_segmentation_results', 'No segmentation analysis results available'))
        return
    
    st.subheader("📋 " + t('analysis.user_segmentation_results', 'User Segmentation Analysis Results'))
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 " + t('analysis.results_overview', 'Results Overview'), 
        "🔍 " + t('analysis.segment_details', 'Segment Details'), 
        "📈 " + t('analysis.visualizations', 'Visualizations'), 
        "📊 " + t('analysis.feature_analysis', 'Feature Analysis'),
        "💡 " + t('analysis.insights_recommendations', 'Insights & Recommendations')
    ])
    
    with tab1:
        show_segmentation_overview(results)
    
    with tab2:
        show_segment_details(results)
    
    with tab3:
        show_segmentation_visualizations(results)
    
    with tab4:
        show_feature_analysis(results)
    
    with tab5:
        show_insights_and_recommendations(results)

def show_segmentation_overview(results):
    """Display segmentation overview"""
    st.write("### 📊 " + t('analysis.segmentation_overview', 'Segmentation Analysis Overview'))
    
    segmentation_result = results['segmentation_result']
    execution_metrics = results['execution_metrics']
    
    # Execution metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            t('analysis.analysis_method', 'Analysis Method'),
            execution_metrics['method_used'].upper(),
            help=t('analysis.clustering_algorithm_used', 'Clustering algorithm used')
        )
    
    with col2:
        st.metric(
            t('analysis.segment_count', 'Segment Count'),
            execution_metrics['segments_created'],
            help=t('analysis.segment_count_help', 'Number of user segments identified')
        )
    
    with col3:
        st.metric(
            t('analysis.quality_score', 'Quality Score'),
            f"{execution_metrics['quality_score']:.3f}",
            help=t('analysis.quality_score_help', 'Clustering quality score (silhouette coefficient)')
        )
    
    with col4:
        st.metric(
            t('analysis.analyzed_users', 'Analyzed Users'),
            f"{execution_metrics['total_users']:,}",
            help=t('analysis.total_users_analyzed_help', 'Total number of users participating in segmentation analysis')
        )
    
    # Quality assessment
    st.write("### 🎯 " + t('analysis.segmentation_quality_assessment', 'Segmentation Quality Assessment'))
    
    quality_score = execution_metrics['quality_score']
    if quality_score > 0.7:
        st.success(f"✅ " + t('analysis.excellent_quality', 'Excellent clustering quality') + f" (" + t('analysis.score', 'Score') + f": {quality_score:.3f})")
        st.write(t('analysis.excellent_quality_desc', 'Clear cluster boundaries with distinct user groups, suitable for developing precise marketing strategies.'))
    elif quality_score > 0.5:
        st.info(f"👌 " + t('analysis.good_quality', 'Good clustering quality') + f" (" + t('analysis.score', 'Score') + f": {quality_score:.3f})")
        st.write(t('analysis.good_quality_desc', 'Clusters have certain distinctiveness and can serve as reference for user strategy development.'))
    elif quality_score > 0.3:
        st.warning(f"⚠️ " + t('analysis.average_quality', 'Average clustering quality') + f" (" + t('analysis.score', 'Score') + f": {quality_score:.3f})")
        st.write(t('analysis.average_quality_desc', 'Significant cluster overlap, recommend adjusting parameters or trying other clustering methods.'))
    else:
        st.error(f"❌ " + t('analysis.poor_quality', 'Poor clustering quality') + f" (" + t('analysis.score', 'Score') + f": {quality_score:.3f})")
        st.write(t('analysis.poor_quality_desc', 'User groups are not clearly distinguished, recommend re-analyzing or checking data quality.'))
    
    # Segment size distribution
    st.write("### 📊 " + t('analysis.segment_size_distribution', 'Segment Size Distribution'))
    
    segment_data = []
    total_users = sum(segment.user_count for segment in segmentation_result.segments)
    
    for segment in segmentation_result.segments:
        percentage = (segment.user_count / total_users) * 100
        segment_data.append({
            t('analysis.segment_name', 'Segment Name'): segment.segment_name,
            t('analysis.user_count', 'User Count'): segment.user_count,
            t('analysis.percentage', 'Percentage'): f"{percentage:.1f}%",
            t('analysis.main_features', 'Main Features'): ', '.join(segment.key_characteristics[:2])
        })
    
    df = pd.DataFrame(segment_data)
    st.dataframe(df, use_container_width=True)

def show_segment_details(results):
    """Display segment details"""
    st.write("### 🔍 " + t('analysis.detailed_segment_info', 'Detailed User Segment Information'))
    
    segmentation_result = results['segmentation_result']
    
    # Select segment to view
    segment_options = [(i, segment.segment_name) for i, segment in enumerate(segmentation_result.segments)]
    selected_segment_idx = st.selectbox(
        t('analysis.select_segment', 'Select Segment'),
        options=[idx for idx, _ in segment_options],
        format_func=lambda x: segment_options[x][1]
    )
    
    if selected_segment_idx is not None:
        segment = segmentation_result.segments[selected_segment_idx]
        
        # Basic segment information
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**{t('analysis.segment_name', 'Segment Name')}**: {segment.segment_name}")
            st.write(f"**{t('analysis.user_count', 'User Count')}**: {segment.user_count}")
            st.write(f"**{t('analysis.segment_id', 'Segment ID')}**: {segment.segment_id}")
        
        with col2:
            st.write("**" + t('analysis.key_characteristics', 'Key Characteristics') + ":**")
            for characteristic in segment.key_characteristics:
                st.write(f"• {characteristic}")
        
        # Segment profile
        st.write("#### 👤 " + t('analysis.segment_profile', 'Segment Profile'))
        profile = segment.segment_profile
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**{t('analysis.dominant_platform', 'Dominant Platform')}**: {profile.get('dominant_platform', 'N/A')}")
            st.write(f"**{t('analysis.dominant_device', 'Dominant Device')}**: {profile.get('dominant_device', 'N/A')}")
        
        with col2:
            st.write(f"**{t('analysis.engagement_level', 'Engagement Level')}**: {profile.get('engagement_level', 'N/A')}")
            st.write(f"**{t('analysis.value_level', 'Value Level')}**: {profile.get('value_level', 'N/A')}")
        
        with col3:
            st.write(f"**{t('analysis.avg_events', 'Average Events')}**: {profile.get('avg_total_events', 0):.1f}")
            st.write(f"**{t('analysis.avg_conversion_rate', 'Average Conversion Rate')}**: {profile.get('avg_conversion_ratio', 0):.3f}")
        
        # Feature details
        st.write("#### 📊 " + t('analysis.average_feature_values', 'Average Feature Values'))
        
        if segment.avg_features:
            # Group features for display
            feature_groups = {
                'Behavioral Features': [k for k in segment.avg_features.keys() if any(x in k for x in ['event', 'behavior', 'total'])],
                'Engagement Features': [k for k in segment.avg_features.keys() if any(x in k for x in ['active', 'frequency', 'engagement'])],
                'Conversion Features': [k for k in segment.avg_features.keys() if any(x in k for x in ['conversion', 'purchase'])],
                'Temporal Features': [k for k in segment.avg_features.keys() if any(x in k for x in ['time', 'hour', 'day', 'week'])]
            }
            
            for group_name, features in feature_groups.items():
                if features:
                    with st.expander(group_name, expanded=False):
                        feature_df = pd.DataFrame([
                            {'Feature Name': feature, 'Value': f"{segment.avg_features[feature]:.3f}"}
                            for feature in features
                        ])
                        st.dataframe(feature_df, use_container_width=True)

def show_segmentation_visualizations(results):
    """Display segmentation visualization charts"""
    st.write("### 📈 " + t('analysis.segmentation_visualizations', 'Segmentation Visualizations'))
    
    visualizations = results.get('visualizations', {})
    
    if not visualizations:
        st.info("📊 " + t('analysis.no_visualization_data', 'No visualization data available'))
        return
    
    # Select visualization to view
    viz_options = list(visualizations.keys())
    viz_names = {
        'segmentation_scatter': 'User Segmentation Scatter Plot',
        'feature_radar': 'Segment Feature Radar Chart',
        'segment_distribution': 'User Segment Distribution'
    }
    
    selected_viz = st.selectbox(
        t('analysis.select_visualization', 'Select Visualization'),
        options=viz_options,
        format_func=lambda x: viz_names.get(x, x)
    )
    
    if selected_viz and selected_viz in visualizations:
        viz_data = visualizations[selected_viz]
        
        if isinstance(viz_data, dict) and 'chart' in viz_data:
            st.plotly_chart(viz_data['chart'], use_container_width=True)
            
            # Chart description
            chart_descriptions = {
                'segmentation_scatter': "This scatter plot shows the distribution of users across main feature dimensions, with different colors representing different user segments. Diamond markers indicate cluster centers.",
                'feature_radar': "The radar chart displays the average performance of each user segment across important features, allowing intuitive comparison of feature differences between segments.",
                'segment_distribution': "The pie chart shows the size distribution of each user segment, helping understand the relative size of different segments."
            }
            
            description = chart_descriptions.get(selected_viz, "")
            if description:
                st.info(f"💡 **Chart Description**: {description}")
        else:
            st.write("Chart data format not supported for display")

def show_feature_analysis(results):
    """Display feature analysis"""
    st.write("### 📊 " + t('analysis.feature_importance_analysis', 'Feature Importance Analysis'))
    
    segmentation_result = results['segmentation_result']
    
    if not segmentation_result.feature_importance:
        st.info(t('analysis.no_feature_importance_data', 'No feature importance data available'))
        return
    
    # Sort feature importance
    feature_importance = sorted(
        segmentation_result.feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Display top 10 important features
    top_features = feature_importance[:10]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("#### 🎯 " + t('analysis.top_10_important_features', 'Top 10 Important Features'))
        
        feature_df = pd.DataFrame([
            {
                t('analysis.feature_name', 'Feature Name'): feature,
                t('analysis.importance_score', 'Importance Score'): f"{importance:.3f}",
                t('analysis.relative_importance', 'Relative Importance'): f"{importance/feature_importance[0][1]*100:.1f}%"
            }
            for feature, importance in top_features
        ])
        
        st.dataframe(feature_df, use_container_width=True)
    
    with col2:
        st.write("#### 📈 " + t('analysis.importance_distribution', 'Importance Distribution'))
        
        # Create bar chart
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[
            go.Bar(
                x=[importance for _, importance in top_features],
                y=[feature for feature, _ in top_features],
                orientation='h',
                marker_color='steelblue'
            )
        ])
        
        fig.update_layout(
            title=t('analysis.feature_importance_distribution', 'Feature Importance Distribution'),
            xaxis_title=t('analysis.importance_score', 'Importance Score'),
            yaxis_title=t('analysis.feature_name', 'Feature Name'),
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Feature explanations
    st.write("#### 💡 " + t('analysis.feature_explanations', 'Feature Explanations'))
    
    feature_explanations = {
        'total_events': 'Total number of events generated by user, reflecting user activity level',
        'conversion_ratio': 'User conversion rate, reflecting user value',
        'activity_frequency': 'User activity frequency, reflecting user engagement',
        'behavior_diversity': 'User behavior diversity, reflecting breadth of user interests',
        'recency_score': 'User recent activity score',
        'total_conversions': 'Total number of user conversions',
        'active_days': 'Number of active days for user',
        'avg_events_per_day': 'Average number of events per day for user'
    }
    
    explanations = []
    for feature, importance in top_features[:5]:
        explanation = feature_explanations.get(feature, 'This feature has important impact on user segmentation')
        explanations.append(f"**{feature}**: {explanation}")
    
    for explanation in explanations:
        st.write(f"• {explanation}")

def show_insights_and_recommendations(results):
    """Display insights and recommendations"""
    st.write("### 💡 " + t('analysis.segmentation_insights_and_recommendations', 'Segmentation Insights and Action Recommendations'))
    
    segmentation_result = results['segmentation_result']
    segment_analysis = results.get('segment_analysis', {})
    
    # Segment insights
    st.write("#### 🔍 " + t('analysis.key_insights', 'Key Insights'))
    
    insights = segment_analysis.get('segment_insights', [])
    if insights:
        for insight in insights:
            st.write(f"• {insight}")
    else:
        # Generate segmentation-based insights
        total_users = sum(segment.user_count for segment in segmentation_result.segments)
        largest_segment = max(segmentation_result.segments, key=lambda s: s.user_count)
        smallest_segment = min(segmentation_result.segments, key=lambda s: s.user_count)
        
        st.write("• " + t('analysis.identified_segments', 'Identified {count} different user segments').format(count=len(segmentation_result.segments)))
        st.write("• " + t('analysis.largest_segment', 'Largest segment is \'{name}\', containing {count} users ({percentage:.1f}%)').format(name=largest_segment.segment_name, count=largest_segment.user_count, percentage=largest_segment.user_count/total_users*100))
        st.write("• " + t('analysis.smallest_segment', 'Smallest segment is \'{name}\', containing {count} users ({percentage:.1f}%)').format(name=smallest_segment.segment_name, count=smallest_segment.user_count, percentage=smallest_segment.user_count/total_users*100))
        
        # Analyze high-value segments
        high_value_segments = [
            s for s in segmentation_result.segments
            if s.segment_profile.get('value_level') == 'high'
        ]
        
        if high_value_segments:
            high_value_users = sum(s.user_count for s in high_value_segments)
            st.write("• " + t('analysis.high_value_segment', 'High-value user segments contain {count} users, accounting for {percentage:.1f}% of total users').format(count=high_value_users, percentage=high_value_users/total_users*100))
    
    # Action recommendations
    st.write("#### 🎯 " + t('analysis.action_recommendations', 'Action Recommendations'))
    
    recommendations = segment_analysis.get('recommendations', [])
    if recommendations:
        for recommendation in recommendations:
            st.write(f"• {recommendation}")
    else:
        # Generate segment feature-based recommendations
        recommendations = []
        
        for segment in segmentation_result.segments:
            engagement_level = segment.segment_profile.get('engagement_level', 'unknown')
            value_level = segment.segment_profile.get('value_level', 'unknown')
            
            if engagement_level == 'high' and value_level == 'high':
                recommendations.append(t('analysis.vip_recommendation', 'For {name}: Provide VIP services and exclusive benefits to maintain high loyalty').format(name=segment.segment_name))
            elif engagement_level == 'high' and value_level in ['medium', 'low']:
                recommendations.append(t('analysis.personalization_recommendation', 'For {name}: Improve conversion rates through personalized recommendations').format(name=segment.segment_name))
            elif engagement_level in ['medium', 'low'] and value_level == 'high':
                recommendations.append(t('analysis.engagement_recommendation', 'For {name}: Increase interactive activities to improve engagement').format(name=segment.segment_name))
            elif engagement_level == 'low' and value_level == 'low':
                recommendations.append(t('analysis.activation_recommendation', 'For {name}: Implement activation strategies and provide new user guidance').format(name=segment.segment_name))
        
        # Add general recommendations
        if segmentation_result.quality_metrics.get('silhouette_score', 0) > 0.5:
            recommendations.append(t('analysis.quality_recommendation', 'Good clustering quality allows for targeted marketing strategies and product optimization plans'))
        
        recommendations.append(t('analysis.monitoring_recommendation', 'Regularly monitor behavioral changes in each segment and adjust strategies timely'))
        recommendations.append(t('analysis.ab_testing_recommendation', 'A/B test marketing content and user experience for different segments'))
        
        for recommendation in recommendations:
            st.write(f"• {recommendation}")
    
    # Next steps
    st.write("#### 📋 " + t('analysis.next_steps', 'Recommended Next Steps'))
    
    next_actions = [
        t('analysis.next_step_1', 'Develop personalized user experience strategies for each segment'),
        t('analysis.next_step_2', 'Design A/B tests to validate the effectiveness of segment characteristics'),
        t('analysis.next_step_3', 'Build segment monitoring dashboard to track segment changes'),
        t('analysis.next_step_4', 'Collaborate with marketing team to design segment-specific marketing campaigns'),
        t('analysis.next_step_5', 'Analyze user lifecycle and value contribution of each segment')
    ]
    
    for i, action in enumerate(next_actions, 1):
        st.write(f"{i}. {action}")