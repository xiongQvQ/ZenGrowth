"""
配置面板组件
提供统一的配置界面模式
"""

import streamlit as st
from typing import Any, Dict, List, Optional, Union


class ConfigField:
    """配置字段定义"""
    
    def __init__(self, field_type: str, label: str, key: str, **kwargs):
        self.field_type = field_type
        self.label = label
        self.key = key
        self.kwargs = kwargs
    
    def render(self, current_value: Any = None) -> Any:
        """渲染配置字段"""
        if self.field_type == "selectbox":
            return st.selectbox(
                self.label,
                options=self.kwargs.get('options', []),
                index=self._get_index(current_value),
                help=self.kwargs.get('help'),
                key=self.key
            )
        elif self.field_type == "slider":
            return st.slider(
                self.label,
                min_value=self.kwargs.get('min_value', 0),
                max_value=self.kwargs.get('max_value', 100),
                value=current_value or self.kwargs.get('value', 50),
                help=self.kwargs.get('help'),
                key=self.key
            )
        elif self.field_type == "checkbox":
            return st.checkbox(
                self.label,
                value=current_value or self.kwargs.get('value', False),
                help=self.kwargs.get('help'),
                key=self.key
            )
        elif self.field_type == "text_input":
            return st.text_input(
                self.label,
                value=current_value or self.kwargs.get('value', ''),
                help=self.kwargs.get('help'),
                key=self.key
            )
        elif self.field_type == "number_input":
            return st.number_input(
                self.label,
                min_value=self.kwargs.get('min_value', 0),
                max_value=self.kwargs.get('max_value', 1000),
                value=current_value or self.kwargs.get('value', 0),
                help=self.kwargs.get('help'),
                key=self.key
            )
        else:
            st.error(f"未知字段类型: {self.field_type}")
            return None
    
    def _get_index(self, current_value: Any) -> int:
        """获取选择框的索引"""
        options = self.kwargs.get('options', [])
        if current_value in options:
            return options.index(current_value)
        return 0


class ConfigSection:
    """配置分组"""
    
    def __init__(self, title: str, fields: List[ConfigField]):
        self.title = title
        self.fields = fields
    
    def render(self, current_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """渲染配置分组"""
        current_values = current_values or {}
        values = {}
        
        if self.title:
            st.subheader(self.title)
        
        for field in self.fields:
            current_value = current_values.get(field.key)
            values[field.key] = field.render(current_value)
        
        return values


class ConfigPanel:
    """通用配置面板"""
    
    def __init__(self, title: str = "配置"):
        self.title = title
        self.sections: List[ConfigSection] = []
    
    def add_section(self, section: ConfigSection):
        """添加配置分组"""
        self.sections.append(section)
    
    def render(self, current_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """渲染配置面板"""
        current_config = current_config or {}
        config = {}
        
        if self.title:
            st.header(self.title)
        
        for section in self.sections:
            section_values = section.render(current_config)
            config.update(section_values)
        
        return config


class AnalysisConfigPanel:
    """分析配置面板"""
    
    @staticmethod
    def render_basic_config() -> Dict[str, Any]:
        """渲染基础分析配置"""
        st.subheader("基础配置")
        
        config = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            config['analysis_depth'] = st.slider(
                "分析深度",
                min_value=1,
                max_value=5,
                value=3,
                help="控制分析的详细程度"
            )
            
            config['time_range'] = st.selectbox(
                "时间范围",
                options=["最近7天", "最近30天", "最近90天", "全部时间"],
                index=1
            )
        
        with col2:
            config['enable_advanced'] = st.checkbox(
                "启用高级分析",
                value=False,
                help="包含更复杂的分析算法"
            )
            
            config['sample_size'] = st.number_input(
                "样本大小",
                min_value=100,
                max_value=10000,
                value=1000,
                help="用于分析的数据样本数量"
            )
        
        return config


class QuickConfigBuilder:
    """快速配置构建器"""
    
    @staticmethod
    def create_selectbox_config(label: str, key: str, options: List[str], 
                               default_index: int = 0, help_text: str = "") -> ConfigField:
        """创建选择框配置"""
        return ConfigField(
            field_type="selectbox",
            label=label,
            key=key,
            options=options,
            help=help_text
        )
    
    @staticmethod
    def create_slider_config(label: str, key: str, min_val: int, max_val: int, 
                            default_val: int, help_text: str = "") -> ConfigField:
        """创建滑块配置"""
        return ConfigField(
            field_type="slider",
            label=label,
            key=key,
            min_value=min_val,
            max_value=max_val,
            value=default_val,
            help=help_text
        )
    
    @staticmethod
    def create_checkbox_config(label: str, key: str, default_val: bool = False, 
                              help_text: str = "") -> ConfigField:
        """创建复选框配置"""
        return ConfigField(
            field_type="checkbox",
            label=label,
            key=key,
            value=default_val,
            help=help_text
        )