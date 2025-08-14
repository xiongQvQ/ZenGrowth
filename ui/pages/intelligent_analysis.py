"""
智能分析页面
提供全面的多维度分析功能
"""

import streamlit as st
import pandas as pd
import json
import time
from pathlib import Path
from ui.components.common import render_data_status_check
from ui.state.state_manager import get_state_manager
from system.integration_manager_singleton import get_integration_manager
from utils.i18n import t

@render_data_status_check
def show_intelligent_analysis_page():
    """显示智能分析页面"""
    st.header("🤖 " + t("pages.intelligent_analysis.title", "智能分析"))
    st.markdown("---")
    
    st.markdown(t('analysis.intelligent_description', '智能分析提供全面的多维度用户行为分析，帮助您深入了解用户行为模式、识别优化机会并制定数据驱动的决策。'))
    
    # 分析配置
    st.subheader(t('analysis.analysis_config_header', '分析配置'))
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_types = st.multiselect(
            t('analysis.select_analysis_types', '选择分析类型'),
            options=[
                'event_analysis',
                'retention_analysis', 
                'conversion_analysis',
                'user_segmentation',
                'path_analysis'
            ],
            default=[
                'event_analysis',
                'retention_analysis', 
                'conversion_analysis'
            ],
            format_func=lambda x: {
                'event_analysis': t('analysis.event_analysis_option', '事件分析'),
                'retention_analysis': t('analysis.retention_analysis_option', '留存分析'),
                'conversion_analysis': t('analysis.conversion_analysis_option', '转化分析'),
                'user_segmentation': t('analysis.user_segmentation_option', '用户分群'),
                'path_analysis': t('analysis.path_analysis_option', '路径分析')
            }.get(x, x)
        )
        
        enable_parallel = st.checkbox(
            t('analysis.enable_parallel_processing', '启用并行处理'),
            value=True,
            help=t('analysis.parallel_processing_help', '并行处理可以加速分析执行，但会消耗更多系统资源')
        )
    
    with col2:
        max_workers = st.slider(
            t('analysis.max_parallel_tasks', '最大并行任务数'),
            min_value=1,
            max_value=8,
            value=4,
            disabled=not enable_parallel
        )
        
        enable_caching = st.checkbox(
            t('analysis.enable_intelligent_cache', '启用智能缓存'),
            value=True,
            help=t('analysis.intelligent_cache_help', '智能缓存可以加速重复分析，提高响应速度')
        )
    
    # 执行分析
    st.subheader(t('analysis.execute_analysis_header', '执行分析'))
    
    if not analysis_types:
        st.warning(t('analysis.select_analysis_type_warning', '请至少选择一种分析类型'))
        return
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button(t('analysis.start_intelligent_analysis', '开始智能分析'), type="primary"):
            execute_intelligent_analysis(analysis_types, enable_parallel, max_workers, enable_caching)
    
    with col2:
        if st.button(t('analysis.view_system_status', '查看系统状态')):
            show_system_status()
    
    # 显示分析结果
    state_manager = get_state_manager()
    workflow_results = state_manager.get_analysis_results('workflow')
    
    if workflow_results:
        show_workflow_results()


def execute_intelligent_analysis(analysis_types, enable_parallel, max_workers, enable_caching):
    """执行智能分析"""
    state_manager = get_state_manager()
    
    # 获取集成管理器
    integration_manager = get_integration_manager()
    if integration_manager is None:
        st.error("❌ 系统未初始化，请刷新页面重试")
        return
    
    # 更新集成管理器配置
    if hasattr(integration_manager, 'config'):
        integration_manager.config.enable_parallel_processing = enable_parallel
        integration_manager.config.max_workers = max_workers
        integration_manager.config.enable_caching = enable_caching
    
    # 设置分析状态
    state_manager.set_analyzing(True)
    
    # 创建进度容器
    progress_container = st.container()
    
    with progress_container:
        st.subheader("⚙️ 智能分析进度")
        
        # 创建进度条和状态显示
        progress_bar = st.progress(0)
        status_text = st.empty()
        metrics_container = st.empty()
        
        try:
            # 准备临时文件路径
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 从状态管理器获取原始数据
            raw_data = state_manager.get_raw_data()
            
            if raw_data is not None:
                temp_file_path = upload_dir / f"temp_analysis_{int(time.time())}.ndjson"
                
                # 将DataFrame转换回NDJSON格式
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    for _, row in raw_data.iterrows():
                        # 重构原始事件格式
                        event_data = {
                            'event_date': row.get('event_date', ''),
                            'event_timestamp': row.get('event_timestamp', 0),
                            'event_name': row.get('event_name', ''),
                            'user_pseudo_id': row.get('user_pseudo_id', ''),
                            'user_id': row.get('user_id'),
                            'platform': row.get('platform', 'WEB'),
                            'device': row.get('device', {}),
                            'geo': row.get('geo', {}),
                            'traffic_source': row.get('traffic_source', {}),
                            'event_params': row.get('event_params', []),
                            'user_properties': row.get('user_properties', []),
                            'items': row.get('items', [])
                        }
                        f.write(json.dumps(event_data, ensure_ascii=False) + '\n')
                
                status_text.text("🚀 启动智能分析工作流程...")
                progress_bar.progress(10)
                
                # 执行完整工作流程
                start_time = time.time()
                
                result = integration_manager.execute_complete_workflow(
                    file_path=str(temp_file_path),
                    analysis_types=analysis_types
                )
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # 更新进度
                progress_bar.progress(100)
                status_text.text("✅ 智能分析完成!")
                
                # 存储工作流程结果
                state_manager.set_analysis_results('workflow', result)
                
                # 显示执行指标
                if result and 'execution_summary' in result:
                    execution_summary = result['execution_summary']
                    
                    with metrics_container.container():
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "总执行时间",
                                f"{total_time:.2f}秒",
                                help="完整工作流程的执行时间"
                            )
                        
                        with col2:
                            st.metric(
                                "成功分析",
                                execution_summary.get('successful_analyses', 0),
                                help="成功完成的分析任务数量"
                            )
                        
                        with col3:
                            st.metric(
                                "处理数据量",
                                f"{execution_summary.get('data_size', 0):,}",
                                help="处理的事件记录数量"
                            )
                        
                        with col4:
                            processing_rate = execution_summary.get('data_size', 0) / total_time if total_time > 0 else 0
                            st.metric(
                                "处理速率",
                                f"{processing_rate:.0f}/秒",
                                help="每秒处理的记录数量"
                            )
                
                # 清理临时文件
                try:
                    temp_file_path.unlink()
                except:
                    pass
                    
                st.success("🎉 智能分析完成！请查看下方的详细结果。")
                st.rerun()
                
            else:
                st.error("❌ 未找到分析数据，请先上传数据文件")
                
        except Exception as e:
            st.error(f"❌ 智能分析执行失败: {str(e)}")
            import traceback
            st.text("详细错误信息:")
            st.text(traceback.format_exc())
        finally:
            state_manager.set_analyzing(False)


def show_system_status():
    """显示系统状态"""
    state_manager = get_state_manager()
    integration_manager = get_integration_manager()
    
    st.subheader("🔧 系统状态")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**系统组件**")
        st.write(f"• 集成管理器: {'✅ 已初始化' if integration_manager else '❌ 未初始化'}")
        st.write(f"• 状态管理器: {'✅ 运行中' if state_manager else '❌ 未运行'}")
        st.write(f"• 数据状态: {'✅ 已加载' if state_manager.is_data_loaded() else '❌ 无数据'}")
    
    with col2:
        st.write("**分析状态**")
        if state_manager.is_analyzing():
            progress, step = state_manager.get_analysis_progress()
            st.write(f"• 正在分析: {step}")
            st.progress(progress)
        else:
            st.write("• 分析状态: 空闲")
        
        # API健康状态
        api_health = state_manager.get_api_health()
        if api_health:
            for provider, health_info in api_health.items():
                status = "✅ 健康" if health_info.get('healthy', False) else "❌ 异常"
                st.write(f"• {provider}: {status}")


def show_workflow_results():
    """显示工作流程结果"""
    st.subheader("📋 分析结果")
    
    state_manager = get_state_manager()
    result = state_manager.get_analysis_results('workflow')
    
    if not result:
        st.info("暂无分析结果")
        return
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 结果概览", "🔍 详细分析", "📈 可视化图表", "📥 导出报告"])
    
    with tab1:
        show_results_overview(result)
    
    with tab2:
        show_detailed_analysis(result)
    
    with tab3:
        show_visualizations(result)
    
    with tab4:
        show_export_options(result)


def show_results_overview(result):
    """显示结果概览"""
    st.write("### 📊 执行概览")
    
    execution_summary = result.get('execution_summary', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        workflow_id = result.get('workflow_id', 'unknown')
        st.metric(
            "工作流程ID",
            workflow_id[:12] + "..." if len(workflow_id) > 12 else workflow_id,
            help=f"完整ID: {workflow_id}"
        )
    
    with col2:
        st.metric(
            "总执行时间",
            f"{execution_summary.get('total_execution_time', 0):.2f}秒"
        )
    
    with col3:
        successful = execution_summary.get('successful_analyses', 0)
        failed = execution_summary.get('failed_analyses', 0)
        st.metric(
            "成功分析",
            f"{successful}/{successful + failed}"
        )
    
    with col4:
        st.metric(
            "数据规模",
            f"{execution_summary.get('data_size', 0):,} 条"
        )
    
    # 分析结果状态
    st.write("### 📈 分析模块状态")
    
    analysis_results = result.get('analysis_results', {})
    
    for analysis_type, analysis_result in analysis_results.items():
        status = getattr(analysis_result, 'status', 'unknown')
        status_icon = '✅' if status == 'completed' else '❌'
        
        with st.expander(f"{status_icon} {analysis_type.replace('_', ' ').title()}", 
                        expanded=(status == 'completed')):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**状态**: {status}")
                st.write(f"**执行时间**: {getattr(analysis_result, 'execution_time', 0):.2f}秒")
                insights_count = len(getattr(analysis_result, 'insights', []))
                recommendations_count = len(getattr(analysis_result, 'recommendations', []))
                st.write(f"**洞察数量**: {insights_count}")
                st.write(f"**建议数量**: {recommendations_count}")
            
            with col2:
                insights = getattr(analysis_result, 'insights', [])
                if insights:
                    st.write("**主要洞察**:")
                    for insight in insights[:3]:
                        st.write(f"• {insight}")

                    if len(insights) > 3:
                        st.write(f"... 还有 {len(insights) - 3} 个洞察")


def show_detailed_analysis(result):
    """显示详细分析"""
    st.write("### 🔍 详细分析结果")
    
    analysis_results = result.get('analysis_results', {})
    
    if not analysis_results:
        st.info("暂无详细分析结果")
        return
    
    # 选择要查看的分析
    selected_analysis = st.selectbox(
        "选择分析模块",
        options=list(analysis_results.keys()),
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_analysis:
        analysis_result = analysis_results[selected_analysis]
        status = getattr(analysis_result, 'status', 'unknown')
        
        if status == 'completed':
            # 显示洞察
            insights = getattr(analysis_result, 'insights', [])
            if insights:
                st.write("#### 💡 关键洞察")
                for i, insight in enumerate(insights, 1):
                    st.write(f"{i}. {insight}")

            # 显示建议
            recommendations = getattr(analysis_result, 'recommendations', [])
            if recommendations:
                st.write("#### 🎯 行动建议")
                for i, recommendation in enumerate(recommendations, 1):
                    st.write(f"{i}. {recommendation}")

            # 显示数据摘要
            if hasattr(analysis_result, 'data') and analysis_result.data:
                st.write("#### 📊 数据摘要")
                data_summary = analysis_result.data
                
                summary_data = []
                for key, value in data_summary.items():
                    if isinstance(value, dict):
                        summary_data.append({
                            '字段': key,
                            '类型': value.get('type', 'unknown'),
                            '描述': str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                        })
                
                if summary_data:
                    df = pd.DataFrame(summary_data)
                    st.dataframe(df, use_container_width=True)
        
        else:
            error_message = getattr(analysis_result, 'error_message', '未知错误')
            st.error(f"❌ 分析失败: {error_message}")


def show_visualizations(result):
    """显示可视化图表"""
    st.write("### 📈 可视化图表")
    
    visualizations = result.get('visualizations', {})
    
    if not visualizations:
        st.info("📊 暂无可视化图表数据")
        return
    
    # 选择要查看的可视化
    viz_options = []
    for analysis_type, viz_data in visualizations.items():
        if viz_data:
            for viz_name in viz_data.keys():
                viz_options.append(f"{analysis_type} - {viz_name}")
    
    if viz_options:
        selected_viz = st.selectbox(
            "选择可视化图表",
            options=viz_options
        )
        
        if selected_viz:
            analysis_type, viz_name = selected_viz.split(' - ', 1)
            viz_data = visualizations[analysis_type][viz_name]
            
            if isinstance(viz_data, dict) and 'chart' in viz_data:
                st.plotly_chart(viz_data['chart'], use_container_width=True)
            else:
                st.write("图表数据格式不支持显示")
                st.json(viz_data)
    else:
        st.info("📊 暂无可用的可视化图表")


def show_export_options(result):
    """显示导出选项"""
    st.write("### 📥 导出分析报告")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "导出格式",
            options=['json', 'pdf', 'excel'],
            format_func=lambda x: {
                'json': 'JSON 格式',
                'pdf': 'PDF 报告',
                'excel': 'Excel 表格'
            }.get(x, x)
        )
        
        include_raw_data = st.checkbox(
            "包含原始数据",
            value=False,
            help="包含原始数据会增加文件大小"
        )
    
    with col2:
        st.write("**导出内容预览**:")
        st.write("• 执行摘要")
        st.write("• 分析结果和洞察")
        st.write("• 行动建议")
        st.write("• 系统性能指标")
        if include_raw_data:
            st.write("• 原始数据")
    
    if st.button("📥 导出报告", type="primary"):
        try:
            integration_manager = get_integration_manager()
            workflow_id = result.get('workflow_id', 'unknown')
            
            # 生成报告数据
            report_data = {
                'workflow_id': workflow_id,
                'export_time': time.time(),
                'export_format': export_format,
                'analysis_results': result.get('analysis_results', {}),
                'execution_summary': result.get('execution_summary', {}),
                'visualizations': result.get('visualizations', {}) if not include_raw_data else {}
            }
            
            # 创建报告文件
            timestamp = int(time.time())
            filename = f"intelligent_analysis_report_{timestamp}.{export_format}"
            
            if export_format == 'json':
                file_content = json.dumps(report_data, ensure_ascii=False, indent=2)
                mime_type = 'application/json'
            else:
                # 其他格式的简化实现
                file_content = json.dumps(report_data, ensure_ascii=False, indent=2)
                mime_type = 'application/octet-stream'
            
            # 提供下载链接
            st.download_button(
                label=f"⬇️ 下载 {export_format.upper()} 报告",
                data=file_content.encode('utf-8'),
                file_name=filename,
                mime=mime_type
            )
            
            st.success(f"✅ 报告已生成: {filename}")
            
        except Exception as e:
            st.error(f"❌ 导出失败: {str(e)}")


def get_mime_type(export_format):
    """获取MIME类型"""
    mime_types = {
        'json': 'application/json',
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    return mime_types.get(export_format, 'application/octet-stream')