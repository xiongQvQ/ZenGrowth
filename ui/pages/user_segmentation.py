"""
用户分群页面
进行用户细分和特征分析
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
    """显示用户分群页面"""
    st.header("👥 " + t("pages.user_segmentation.title", "用户分群"))
    st.markdown("---")
    
    st.markdown(t('analysis.user_segmentation_description', '用户分群分析通过机器学习算法识别具有相似行为特征的用户群体，帮助您制定精准的营销策略和个性化服务。'))
    
    # 获取状态管理器
    state_manager = get_state_manager()
    
    # 初始化分析引擎
    if 'segmentation_engine' not in st.session_state:
        st.session_state.segmentation_engine = UserSegmentationEngine()
    if 'advanced_visualizer' not in st.session_state:
        st.session_state.advanced_visualizer = AdvancedVisualizer()
    if 'chart_generator' not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()
    
    # 分析配置
    with st.expander(t('analysis.user_segmentation_config', '用户分群配置'), expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            clustering_method = st.selectbox(
                t('analysis.clustering_method', '分群方法'),
                options=[
                    ('kmeans', 'K-Means聚类'),
                    ('dbscan', 'DBSCAN聚类'),
                    ('behavioral', '行为分群'),
                    ('value_based', '价值分群'),
                    ('engagement', '参与度分群')
                ],
                format_func=lambda x: x[1],
                index=0,
                help=t('analysis.clustering_method_help', '选择用户分群的算法方法')
            )
        
        with col2:
            n_clusters = st.slider(
                t('analysis.cluster_count', '分群数量'),
                min_value=3,
                max_value=10,
                value=5,
                help=t('analysis.cluster_count_help', '设置要创建的用户分群数量')
            )
        
        with col3:
            include_features = st.multiselect(
                t('analysis.feature_types', '特征类型'),
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
                    'behavioral_features': '行为特征',
                    'demographic_features': '人口统计特征',
                    'engagement_features': '参与度特征',
                    'conversion_features': '转化特征',
                    'temporal_features': '时间特征'
                }.get(x, x),
                help=t('analysis.feature_types_help', '选择用于分群分析的特征类型')
            )
    
    # 高级配置
    with st.expander(t('analysis.advanced_config', '高级配置'), expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            enable_pca = st.checkbox(
                t('analysis.enable_pca', '启用PCA降维'),
                value=False,
                help=t('analysis.pca_help', '对高维特征进行主成分分析降维')
            )
            
            if enable_pca:
                pca_components = st.slider(
                    t('analysis.pca_components', 'PCA主成分数'),
                    min_value=2,
                    max_value=10,
                    value=3
                )
        
        with col2:
            quality_threshold = st.slider(
                t('analysis.quality_threshold', '质量阈值'),
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help=t('analysis.quality_threshold_help', '分群质量的最低要求（轮廓系数）')
            )
            
            auto_optimize = st.checkbox(
                t('analysis.auto_optimize', '自动优化参数'),
                value=True,
                help=t('analysis.auto_optimize_help', '自动寻找最优的分群参数')
            )
    
    # 执行用户分群分析
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button(t('analysis.start_segmentation_analysis', '开始用户分群'), type="primary"):
            execute_segmentation_analysis(
                clustering_method[0], n_clusters, include_features,
                enable_pca, pca_components if enable_pca else None,
                quality_threshold, auto_optimize
            )
    
    with col2:
        if st.button(t('analysis.view_feature_summary', '查看特征摘要')):
            show_feature_summary()
    
    # 显示分群分析结果
    results = state_manager.get_analysis_results('user_segmentation')
    
    if results:
        show_segmentation_results()

def execute_segmentation_analysis(method, n_clusters, include_features, 
                                enable_pca, pca_components, quality_threshold, auto_optimize):
    """执行用户分群分析"""
    state_manager = get_state_manager()
    
    # 创建进度容器
    progress_container = st.container()
    
    with progress_container:
        st.subheader("⚙️ 用户分群分析进度")
        
        # 创建进度条和状态显示
        progress_bar = st.progress(0)
        status_text = st.empty()
        metrics_container = st.empty()
        
        try:
            status_text.text("🔍 初始化分群引擎...")
            progress_bar.progress(10)
            
            # 获取原始数据
            raw_data = state_manager.get_raw_data()
            if raw_data is None or raw_data.empty:
                st.error("❌ 未找到分析数据，请先上传数据文件")
                return
            
            # 初始化分群引擎
            engine = st.session_state.segmentation_engine
            
            status_text.text("📊 提取用户特征...")
            progress_bar.progress(30)
            
            # 提取用户特征
            start_time = time.time()
            user_features = engine.extract_user_features(raw_data)
            
            if not user_features:
                st.error("❌ 无法提取用户特征，请检查数据格式")
                return
            
            feature_extraction_time = time.time() - start_time
            
            status_text.text(f"🎯 执行{method}分群算法...")
            progress_bar.progress(60)
            
            # 执行分群
            clustering_start = time.time()
            
            # 根据是否启用自动优化调整参数
            if auto_optimize and method == 'kmeans':
                # 尝试不同的聚类数量，找到最优解
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
                st.error("❌ 分群分析失败，请尝试调整参数")
                return
            
            status_text.text("📈 生成可视化图表...")
            progress_bar.progress(80)
            
            # 生成可视化数据
            visualizations = generate_segmentation_visualizations(segmentation_result, user_features)
            
            status_text.text("✨ 分析特征重要性...")
            progress_bar.progress(90)
            
            # 分析分群特征
            segment_analysis = engine.analyze_segment_characteristics(segmentation_result)
            
            # 更新进度
            progress_bar.progress(100)
            status_text.text("✅ 用户分群分析完成!")
            
            total_time = time.time() - start_time
            
            # 准备结果数据
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
            
            # 存储结果
            state_manager.set_analysis_results('user_segmentation', results_data)
            
            # 显示执行指标
            with metrics_container.container():
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "分析耗时",
                        f"{total_time:.2f}秒",
                        help="完整分群分析的执行时间"
                    )
                
                with col2:
                    st.metric(
                        "用户数量",
                        len(user_features),
                        help="参与分群分析的用户总数"
                    )
                
                with col3:
                    st.metric(
                        "分群数量",
                        len(segmentation_result.segments),
                        help="识别出的用户分群数量"
                    )
                
                with col4:
                    quality_score = segmentation_result.quality_metrics.get('silhouette_score', 0)
                    st.metric(
                        "质量评分",
                        f"{quality_score:.3f}",
                        help="分群质量评分（轮廓系数）"
                    )
            
            st.success("🎉 用户分群分析完成！请查看下方的详细结果。")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 用户分群分析执行失败: {str(e)}")
            import traceback
            st.text("详细错误信息:")
            st.text(traceback.format_exc())

def generate_segmentation_visualizations(segmentation_result, user_features):
    """生成分群可视化图表"""
    try:
        visualizations = {}
        advanced_viz = st.session_state.advanced_visualizer
        
        # 1. 用户分群散点图
        if segmentation_result.segments:
            scatter_data = []
            for segment in segmentation_result.segments:
                for user_id in segment.user_ids:
                    # 使用主要特征作为X和Y轴
                    user_feature = next((uf for uf in user_features if uf.user_id == user_id), None)
                    if user_feature:
                        # 选择两个重要特征作为坐标
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
                    'title': '用户分群散点图'
                }
        
        # 2. 特征雷达图
        if segmentation_result.feature_importance:
            radar_data = []
            top_features = sorted(
                segmentation_result.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:6]  # 取前6个重要特征
            
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
                    'title': '分群特征雷达图'
                }
        
        # 3. 分群大小分布图
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
            
            # 创建饼图显示分群分布
            import plotly.graph_objects as go
            pie_chart = go.Figure(data=[go.Pie(
                labels=size_df['segment_name'],
                values=size_df['user_count'],
                hole=0.3,
                hovertemplate='<b>%{label}</b><br>' +
                             '用户数量: %{value}<br>' +
                             '占比: %{percent}<br>' +
                             '<extra></extra>',
                textinfo='label+percent',
                textposition='auto'
            )])
            
            pie_chart.update_layout(
                title='用户分群分布',
                height=500,
                template='plotly_white',
                showlegend=True
            )
            
            visualizations['segment_distribution'] = {
                'chart': pie_chart,
                'type': 'pie',
                'title': '用户分群分布'
            }
        
        return visualizations
        
    except Exception as e:
        st.warning(f"可视化生成失败: {e}")
        return {}

def show_feature_summary():
    """显示特征摘要"""
    state_manager = get_state_manager()
    engine = st.session_state.segmentation_engine
    
    # 设置数据存储管理器
    engine.storage_manager = state_manager
    
    with st.spinner("正在分析特征..."):
        try:
            summary = engine.get_analysis_summary()
            
            if 'error' in summary:
                st.error(f"❌ 获取特征摘要失败: {summary['error']}")
                return
            
            st.subheader("📊 数据特征摘要")
            
            # 基础数据统计
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总事件数", f"{summary['total_events']:,}")
            with col2:
                st.metric("唯一用户数", summary['unique_users'])
            with col3:
                st.metric("事件类型数", summary['unique_event_types'])
            with col4:
                st.metric("用户记录数", summary['total_user_records'])
            
            # 时间范围
            st.write("**📅 数据时间范围:**")
            st.write(f"从 {summary['date_range']['start']} 到 {summary['date_range']['end']}")
            
            # 可用分群方法
            st.write("**🔧 可用分群方法:**")
            methods_display = {
                'kmeans': 'K-Means聚类',
                'dbscan': 'DBSCAN聚类',
                'behavioral': '行为分群',
                'value_based': '价值分群',
                'engagement': '参与度分群'
            }
            
            method_cols = st.columns(len(summary['available_methods']))
            for i, method in enumerate(summary['available_methods']):
                with method_cols[i]:
                    st.info(f"✅ {methods_display.get(method, method)}")
            
            # 特征类型说明
            st.write("**📈 可用特征类型:**")
            for feature_type, features in summary['feature_types'].items():
                with st.expander(f"{feature_type.replace('_', ' ').title()}", expanded=False):
                    st.write("主要特征：")
                    for feature in features:
                        st.write(f"• {feature}")
            
            # 建议的聚类范围
            cluster_range = summary['recommended_cluster_range']
            st.info(f"💡 **建议分群数量**: {cluster_range[0]} - {cluster_range[1]} 个")
            
        except Exception as e:
            st.error(f"❌ 分析特征摘要失败: {str(e)}")

def show_segmentation_results():
    """显示分群分析结果"""
    state_manager = get_state_manager()
    results = state_manager.get_analysis_results('user_segmentation')
    
    if not results:
        st.info("暂无分群分析结果")
        return
    
    st.subheader("📋 用户分群分析结果")
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 结果概览", 
        "🔍 分群详情", 
        "📈 可视化图表", 
        "📊 特征分析",
        "💡 洞察建议"
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
    """显示分群概览"""
    st.write("### 📊 分群分析概览")
    
    segmentation_result = results['segmentation_result']
    execution_metrics = results['execution_metrics']
    
    # 执行指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "分析方法",
            execution_metrics['method_used'].upper(),
            help="使用的分群算法"
        )
    
    with col2:
        st.metric(
            "分群数量",
            execution_metrics['segments_created'],
            help="识别出的用户分群数量"
        )
    
    with col3:
        st.metric(
            "质量评分",
            f"{execution_metrics['quality_score']:.3f}",
            help="分群质量评分（轮廓系数）"
        )
    
    with col4:
        st.metric(
            "分析用户",
            f"{execution_metrics['total_users']:,}",
            help="参与分群分析的用户总数"
        )
    
    # 质量评估
    st.write("### 🎯 分群质量评估")
    
    quality_score = execution_metrics['quality_score']
    if quality_score > 0.7:
        st.success(f"✅ 分群质量优秀 (评分: {quality_score:.3f})")
        st.write("分群边界清晰，用户群体区分明显，适合制定精准营销策略。")
    elif quality_score > 0.5:
        st.info(f"👌 分群质量良好 (评分: {quality_score:.3f})")
        st.write("分群具有一定的区分度，可以作为用户策略制定的参考。")
    elif quality_score > 0.3:
        st.warning(f"⚠️ 分群质量一般 (评分: {quality_score:.3f})")
        st.write("分群重叠较多，建议调整参数或尝试其他分群方法。")
    else:
        st.error(f"❌ 分群质量较差 (评分: {quality_score:.3f})")
        st.write("用户群体区分不明显，建议重新分析或检查数据质量。")
    
    # 分群大小分布
    st.write("### 📊 分群大小分布")
    
    segment_data = []
    total_users = sum(segment.user_count for segment in segmentation_result.segments)
    
    for segment in segmentation_result.segments:
        percentage = (segment.user_count / total_users) * 100
        segment_data.append({
            '分群名称': segment.segment_name,
            '用户数量': segment.user_count,
            '占比': f"{percentage:.1f}%",
            '主要特征': ', '.join(segment.key_characteristics[:2])
        })
    
    df = pd.DataFrame(segment_data)
    st.dataframe(df, use_container_width=True)

def show_segment_details(results):
    """显示分群详情"""
    st.write("### 🔍 用户分群详细信息")
    
    segmentation_result = results['segmentation_result']
    
    # 选择要查看的分群
    segment_options = [(i, segment.segment_name) for i, segment in enumerate(segmentation_result.segments)]
    selected_segment_idx = st.selectbox(
        "选择分群",
        options=[idx for idx, _ in segment_options],
        format_func=lambda x: segment_options[x][1]
    )
    
    if selected_segment_idx is not None:
        segment = segmentation_result.segments[selected_segment_idx]
        
        # 分群基本信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**分群名称**: {segment.segment_name}")
            st.write(f"**用户数量**: {segment.user_count}")
            st.write(f"**分群ID**: {segment.segment_id}")
        
        with col2:
            st.write("**关键特征**:")
            for characteristic in segment.key_characteristics:
                st.write(f"• {characteristic}")
        
        # 分群画像
        st.write("#### 👤 分群画像")
        profile = segment.segment_profile
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**主要平台**: {profile.get('dominant_platform', 'N/A')}")
            st.write(f"**主要设备**: {profile.get('dominant_device', 'N/A')}")
        
        with col2:
            st.write(f"**参与度等级**: {profile.get('engagement_level', 'N/A')}")
            st.write(f"**价值等级**: {profile.get('value_level', 'N/A')}")
        
        with col3:
            st.write(f"**平均事件数**: {profile.get('avg_total_events', 0):.1f}")
            st.write(f"**平均转化率**: {profile.get('avg_conversion_ratio', 0):.3f}")
        
        # 特征详情
        st.write("#### 📊 平均特征值")
        
        if segment.avg_features:
            # 分组显示特征
            feature_groups = {
                '行为特征': [k for k in segment.avg_features.keys() if any(x in k for x in ['event', 'behavior', 'total'])],
                '参与度特征': [k for k in segment.avg_features.keys() if any(x in k for x in ['active', 'frequency', 'engagement'])],
                '转化特征': [k for k in segment.avg_features.keys() if any(x in k for x in ['conversion', 'purchase'])],
                '时间特征': [k for k in segment.avg_features.keys() if any(x in k for x in ['time', 'hour', 'day', 'week'])]
            }
            
            for group_name, features in feature_groups.items():
                if features:
                    with st.expander(group_name, expanded=False):
                        feature_df = pd.DataFrame([
                            {'特征名称': feature, '数值': f"{segment.avg_features[feature]:.3f}"}
                            for feature in features
                        ])
                        st.dataframe(feature_df, use_container_width=True)

def show_segmentation_visualizations(results):
    """显示分群可视化图表"""
    st.write("### 📈 分群可视化图表")
    
    visualizations = results.get('visualizations', {})
    
    if not visualizations:
        st.info("📊 暂无可视化图表数据")
        return
    
    # 选择要查看的可视化
    viz_options = list(visualizations.keys())
    viz_names = {
        'segmentation_scatter': '用户分群散点图',
        'feature_radar': '分群特征雷达图',
        'segment_distribution': '用户分群分布'
    }
    
    selected_viz = st.selectbox(
        "选择可视化图表",
        options=viz_options,
        format_func=lambda x: viz_names.get(x, x)
    )
    
    if selected_viz and selected_viz in visualizations:
        viz_data = visualizations[selected_viz]
        
        if isinstance(viz_data, dict) and 'chart' in viz_data:
            st.plotly_chart(viz_data['chart'], use_container_width=True)
            
            # 图表说明
            chart_descriptions = {
                'segmentation_scatter': "该散点图展示了用户在主要特征维度上的分布，不同颜色代表不同的用户分群。菱形标记表示各分群的中心点。",
                'feature_radar': "雷达图显示了各个用户分群在重要特征上的平均表现，可以直观比较不同分群的特征差异。",
                'segment_distribution': "饼图展示了各用户分群的规模分布，帮助了解不同分群的相对大小。"
            }
            
            description = chart_descriptions.get(selected_viz, "")
            if description:
                st.info(f"💡 **图表说明**: {description}")
        else:
            st.write("图表数据格式不支持显示")

def show_feature_analysis(results):
    """显示特征分析"""
    st.write("### 📊 特征重要性分析")
    
    segmentation_result = results['segmentation_result']
    
    if not segmentation_result.feature_importance:
        st.info("暂无特征重要性数据")
        return
    
    # 特征重要性排序
    feature_importance = sorted(
        segmentation_result.feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # 显示前10个重要特征
    top_features = feature_importance[:10]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("#### 🎯 Top 10 重要特征")
        
        feature_df = pd.DataFrame([
            {
                '特征名称': feature,
                '重要性评分': f"{importance:.3f}",
                '相对重要性': f"{importance/feature_importance[0][1]*100:.1f}%"
            }
            for feature, importance in top_features
        ])
        
        st.dataframe(feature_df, use_container_width=True)
    
    with col2:
        st.write("#### 📈 重要性分布")
        
        # 创建条形图
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
            title='特征重要性分布',
            xaxis_title='重要性评分',
            yaxis_title='特征名称',
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 特征解释
    st.write("#### 💡 特征解释")
    
    feature_explanations = {
        'total_events': '用户产生的总事件数，反映用户活跃程度',
        'conversion_ratio': '用户的转化率，反映用户价值',
        'activity_frequency': '用户活动频率，反映用户参与度',
        'behavior_diversity': '用户行为多样性，反映用户兴趣广度',
        'recency_score': '用户最近活跃度评分',
        'total_conversions': '用户总转化次数',
        'active_days': '用户活跃天数',
        'avg_events_per_day': '用户平均每日事件数'
    }
    
    explanations = []
    for feature, importance in top_features[:5]:
        explanation = feature_explanations.get(feature, '该特征对用户分群具有重要影响')
        explanations.append(f"**{feature}**: {explanation}")
    
    for explanation in explanations:
        st.write(f"• {explanation}")

def show_insights_and_recommendations(results):
    """显示洞察和建议"""
    st.write("### 💡 分群洞察与行动建议")
    
    segmentation_result = results['segmentation_result']
    segment_analysis = results.get('segment_analysis', {})
    
    # 分群洞察
    st.write("#### 🔍 关键洞察")
    
    insights = segment_analysis.get('segment_insights', [])
    if insights:
        for insight in insights:
            st.write(f"• {insight}")
    else:
        # 生成基于分群的洞察
        total_users = sum(segment.user_count for segment in segmentation_result.segments)
        largest_segment = max(segmentation_result.segments, key=lambda s: s.user_count)
        smallest_segment = min(segmentation_result.segments, key=lambda s: s.user_count)
        
        st.write(f"• 识别出 {len(segmentation_result.segments)} 个不同的用户分群")
        st.write(f"• 最大分群是'{largest_segment.segment_name}'，包含 {largest_segment.user_count} 个用户（{largest_segment.user_count/total_users*100:.1f}%）")
        st.write(f"• 最小分群是'{smallest_segment.segment_name}'，包含 {smallest_segment.user_count} 个用户（{smallest_segment.user_count/total_users*100:.1f}%）")
        
        # 分析高价值分群
        high_value_segments = [
            s for s in segmentation_result.segments
            if s.segment_profile.get('value_level') == 'high'
        ]
        
        if high_value_segments:
            high_value_users = sum(s.user_count for s in high_value_segments)
            st.write(f"• 高价值用户分群包含 {high_value_users} 个用户，占总用户的 {high_value_users/total_users*100:.1f}%")
    
    # 行动建议
    st.write("#### 🎯 行动建议")
    
    recommendations = segment_analysis.get('recommendations', [])
    if recommendations:
        for recommendation in recommendations:
            st.write(f"• {recommendation}")
    else:
        # 生成基于分群特征的建议
        recommendations = []
        
        for segment in segmentation_result.segments:
            engagement_level = segment.segment_profile.get('engagement_level', 'unknown')
            value_level = segment.segment_profile.get('value_level', 'unknown')
            
            if engagement_level == 'high' and value_level == 'high':
                recommendations.append(f"针对{segment.segment_name}：提供VIP服务和专属权益，保持高忠诚度")
            elif engagement_level == 'high' and value_level in ['medium', 'low']:
                recommendations.append(f"针对{segment.segment_name}：通过个性化推荐提升转化率")
            elif engagement_level in ['medium', 'low'] and value_level == 'high':
                recommendations.append(f"针对{segment.segment_name}：增加互动活动，提升参与度")
            elif engagement_level == 'low' and value_level == 'low':
                recommendations.append(f"针对{segment.segment_name}：实施激活策略，提供新用户引导")
        
        # 添加通用建议
        if segmentation_result.quality_metrics.get('silhouette_score', 0) > 0.5:
            recommendations.append("分群质量良好，可以制定针对性的营销策略和产品优化方案")
        
        recommendations.append("定期监控各分群的行为变化，及时调整策略")
        recommendations.append("A/B测试不同分群的营销内容和用户体验")
        
        for recommendation in recommendations:
            st.write(f"• {recommendation}")
    
    # 下一步行动
    st.write("#### 📋 建议的下一步行动")
    
    next_actions = [
        "为每个分群制定个性化的用户体验策略",
        "设计A/B测试验证分群特征的有效性",
        "建立分群监控仪表板，跟踪分群变化",
        "与营销团队协作，设计分群专属的营销活动",
        "分析各分群的用户生命周期和价值贡献"
    ]
    
    for i, action in enumerate(next_actions, 1):
        st.write(f"{i}. {action}")