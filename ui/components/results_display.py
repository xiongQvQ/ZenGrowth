"""
结果显示组件
提供统一的结果展示模式
"""

import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Optional, Union


class MetricsCard:
    """指标卡片组件"""
    
    @staticmethod
    def render_single_metric(label: str, value: Union[int, float, str], 
                           delta: Optional[str] = None, help_text: Optional[str] = None,
                           format_number: bool = True) -> None:
        """渲染单个指标卡片"""
        if format_number and isinstance(value, (int, float)):
            display_value = f"{value:,}" if isinstance(value, int) else f"{value:.2f}"
        else:
            display_value = str(value)
        
        st.metric(
            label=label,
            value=display_value,
            delta=delta,
            help=help_text
        )
    
    @staticmethod
    def render_metrics_row(metrics: List[Dict[str, Any]]) -> None:
        """渲染指标行"""
        cols = st.columns(len(metrics))
        
        for i, metric in enumerate(metrics):
            with cols[i]:
                MetricsCard.render_single_metric(
                    label=metric.get('label', ''),
                    value=metric.get('value', ''),
                    delta=metric.get('delta'),
                    help_text=metric.get('help'),
                    format_number=metric.get('format_number', True)
                )


class StatusDisplay:
    """状态显示组件"""
    
    @staticmethod
    def render_success_status(message: str, details: str = "") -> None:
        """渲染成功状态"""
        st.success(f"✅ {message}")
        if details:
            st.write(details)
    
    @staticmethod
    def render_error_status(message: str, details: str = "") -> None:
        """渲染错误状态"""
        st.error(f"❌ {message}")
        if details:
            with st.expander("错误详情"):
                st.text(details)
    
    @staticmethod
    def render_warning_status(message: str, details: str = "") -> None:
        """渲染警告状态"""
        st.warning(f"⚠️ {message}")
        if details:
            st.write(details)
    
    @staticmethod
    def render_info_status(message: str, details: str = "") -> None:
        """渲染信息状态"""
        st.info(f"ℹ️ {message}")
        if details:
            st.write(details)


class ResultsTable:
    """结果表格组件"""
    
    @staticmethod
    def render_dataframe(df: pd.DataFrame, title: str = "", 
                        max_rows: int = 1000, use_container_width: bool = True) -> None:
        """渲染数据框"""
        if title:
            st.subheader(title)
        
        if df is not None and not df.empty:
            # 限制显示行数
            if len(df) > max_rows:
                st.info(f"显示前 {max_rows} 行，共 {len(df)} 行数据")
                df_display = df.head(max_rows)
            else:
                df_display = df
            
            st.dataframe(df_display, use_container_width=use_container_width)
            
            # 显示统计信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总行数", len(df))
            with col2:
                st.metric("列数", len(df.columns))
            with col3:
                st.metric("内存使用", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
        else:
            st.warning("没有数据可显示")
    
    @staticmethod
    def render_summary_table(data: Dict[str, Any], title: str = "摘要") -> None:
        """渲染摘要表格"""
        if title:
            st.subheader(title)
        
        if data:
            summary_df = pd.DataFrame(list(data.items()), columns=['指标', '值'])
            st.dataframe(summary_df, use_container_width=True)
        else:
            st.warning("没有摘要数据")


class InsightsDisplay:
    """洞察展示组件"""
    
    @staticmethod
    def render_insight_card(title: str, content: str, importance: str = "normal") -> None:
        """渲染洞察卡片"""
        # 根据重要性选择样式
        if importance == "high":
            st.error(f"🔥 **{title}**")
        elif importance == "medium":
            st.warning(f"💡 **{title}**")
        else:
            st.info(f"📝 **{title}**")
        
        st.write(content)
    
    @staticmethod
    def render_insights_list(insights: List[Dict[str, Any]]) -> None:
        """渲染洞察列表"""
        for insight in insights:
            InsightsDisplay.render_insight_card(
                title=insight.get('title', ''),
                content=insight.get('content', ''),
                importance=insight.get('importance', 'normal')
            )
            st.markdown("---")


class VisualizationDisplay:
    """可视化展示组件"""
    
    @staticmethod
    def render_chart_container(chart_func, title: str = "", 
                              description: str = "") -> None:
        """渲染图表容器"""
        if title:
            st.subheader(title)
        
        if description:
            st.write(description)
        
        try:
            chart_func()
        except Exception as e:
            st.error(f"图表渲染失败: {str(e)}")
    
    @staticmethod
    def render_chart_with_data(df: pd.DataFrame, chart_type: str = "line",
                              x_column: str = None, y_column: str = None) -> None:
        """根据数据渲染图表"""
        if df is None or df.empty:
            st.warning("没有数据用于绘制图表")
            return
        
        try:
            if chart_type == "line":
                if x_column and y_column:
                    st.line_chart(df.set_index(x_column)[y_column])
                else:
                    st.line_chart(df.select_dtypes(include=['number']))
            elif chart_type == "bar":
                if x_column and y_column:
                    st.bar_chart(df.set_index(x_column)[y_column])
                else:
                    st.bar_chart(df.select_dtypes(include=['number']))
            elif chart_type == "area":
                if x_column and y_column:
                    st.area_chart(df.set_index(x_column)[y_column])
                else:
                    st.area_chart(df.select_dtypes(include=['number']))
            else:
                st.warning(f"不支持的图表类型: {chart_type}")
        except Exception as e:
            st.error(f"图表渲染失败: {str(e)}")


class ExportDisplay:
    """导出展示组件"""
    
    @staticmethod
    def render_export_buttons(data: Union[pd.DataFrame, Dict[str, Any]], 
                             filename_prefix: str = "export") -> None:
        """渲染导出按钮"""
        col1, col2, col3 = st.columns(3)
        
        if isinstance(data, pd.DataFrame):
            with col1:
                csv = data.to_csv(index=False)
                st.download_button(
                    label="导出CSV",
                    data=csv,
                    file_name=f"{filename_prefix}.csv",
                    mime="text/csv"
                )
            
            with col2:
                try:
                    excel_data = data.to_excel(index=False)
                    st.download_button(
                        label="导出Excel",
                        data=excel_data,
                        file_name=f"{filename_prefix}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except:
                    st.write("Excel导出不可用")
        
        with col3:
            import json
            if isinstance(data, pd.DataFrame):
                json_data = data.to_json(orient='records', force_ascii=False)
            else:
                json_data = json.dumps(data, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="导出JSON",
                data=json_data,
                file_name=f"{filename_prefix}.json",
                mime="application/json"
            )


class WorkflowResultsRenderer:
    """工作流结果渲染器"""
    
    @staticmethod
    def render_analysis_results(results: Dict[str, Any], analysis_type: str) -> None:
        """渲染分析结果"""
        if not results:
            st.warning(f"没有{analysis_type}分析结果")
            return
        
        # 渲染关键指标
        if 'metrics' in results:
            st.subheader("关键指标")
            MetricsCard.render_metrics_row(results['metrics'])
        
        # 渲染数据表格
        if 'data' in results and isinstance(results['data'], pd.DataFrame):
            ResultsTable.render_dataframe(results['data'], "详细数据")
        
        # 渲染洞察
        if 'insights' in results:
            st.subheader("分析洞察")
            InsightsDisplay.render_insights_list(results['insights'])
        
        # 渲染图表
        if 'charts' in results:
            st.subheader("可视化图表")
            for chart_config in results['charts']:
                VisualizationDisplay.render_chart_container(
                    chart_func=lambda: chart_config.get('render_func', lambda: None)(),
                    title=chart_config.get('title', ''),
                    description=chart_config.get('description', '')
                )
        
        # 导出选项
        if results:
            st.subheader("导出选项")
            ExportDisplay.render_export_buttons(
                data=results.get('data', results),
                filename_prefix=f"{analysis_type}_analysis"
            )