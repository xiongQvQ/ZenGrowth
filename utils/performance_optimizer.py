"""
性能优化工具模块
为Streamlit应用提供缓存、懒加载和性能监控功能
"""

import streamlit as st
import time
import functools
import logging
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.timing_data: Dict[str, list] = {}
        self.cache_hits: Dict[str, int] = {}
        self.cache_misses: Dict[str, int] = {}
    
    def record_timing(self, operation: str, duration: float):
        """记录操作时间"""
        if operation not in self.timing_data:
            self.timing_data[operation] = []
        self.timing_data[operation].append({
            'duration': duration,
            'timestamp': datetime.now()
        })
        
        # 保留最近100条记录
        if len(self.timing_data[operation]) > 100:
            self.timing_data[operation] = self.timing_data[operation][-100:]
    
    def record_cache_hit(self, function_name: str):
        """记录缓存命中"""
        self.cache_hits[function_name] = self.cache_hits.get(function_name, 0) + 1
    
    def record_cache_miss(self, function_name: str):
        """记录缓存未命中"""
        self.cache_misses[function_name] = self.cache_misses.get(function_name, 0) + 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = {}
        
        for operation, timings in self.timing_data.items():
            if timings:
                durations = [t['duration'] for t in timings]
                stats[operation] = {
                    'avg_duration': sum(durations) / len(durations),
                    'min_duration': min(durations),
                    'max_duration': max(durations),
                    'call_count': len(durations),
                    'total_time': sum(durations)
                }
        
        # 缓存统计
        cache_stats = {}
        for func_name in set(list(self.cache_hits.keys()) + list(self.cache_misses.keys())):
            hits = self.cache_hits.get(func_name, 0)
            misses = self.cache_misses.get(func_name, 0)
            total = hits + misses
            cache_stats[func_name] = {
                'hits': hits,
                'misses': misses,
                'hit_rate': hits / total if total > 0 else 0
            }
        
        return {
            'timing_stats': stats,
            'cache_stats': cache_stats
        }


# 全局性能监控器
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    return _performance_monitor


def performance_timer(operation_name: str = None):
    """性能计时装饰器"""
    def decorator(func: Callable) -> Callable:
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                _performance_monitor.record_timing(name, duration)
                if duration > 1.0:  # 记录超过1秒的慢操作
                    logger.warning(f"慢操作检测: {name} 耗时 {duration:.2f}秒")
        
        return wrapper
    return decorator


@st.cache_resource
def get_cached_component(component_class, *args, **kwargs):
    """通用组件缓存函数"""
    return component_class(*args, **kwargs)


def cached_property(ttl_seconds: int = 300):
    """带TTL的属性缓存装饰器"""
    def decorator(func):
        cache_attr = f"_cached_{func.__name__}"
        cache_time_attr = f"_cached_{func.__name__}_time"
        
        @functools.wraps(func)
        def wrapper(self):
            current_time = time.time()
            
            # 检查缓存是否存在且未过期
            if (hasattr(self, cache_attr) and 
                hasattr(self, cache_time_attr) and
                current_time - getattr(self, cache_time_attr) < ttl_seconds):
                return getattr(self, cache_attr)
            
            # 计算新值并缓存
            result = func(self)
            setattr(self, cache_attr, result)
            setattr(self, cache_time_attr, current_time)
            return result
        
        return wrapper
    return decorator


def optimize_dataframe_memory(df):
    """优化DataFrame内存使用"""
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = df[col].astype('category')
            except:
                pass
        elif df[col].dtype == 'int64':
            if df[col].min() >= 0:
                if df[col].max() < 256:
                    df[col] = df[col].astype('uint8')
                elif df[col].max() < 65536:
                    df[col] = df[col].astype('uint16')
                elif df[col].max() < 4294967296:
                    df[col] = df[col].astype('uint32')
        elif df[col].dtype == 'float64':
            df[col] = df[col].astype('float32')
    
    return df


def display_performance_metrics():
    """在Streamlit侧边栏显示性能指标"""
    with st.sidebar:
        with st.expander("⚡ 性能监控", expanded=False):
            stats = get_performance_monitor().get_performance_stats()
            
            if stats['timing_stats']:
                st.write("**操作耗时统计:**")
                for operation, data in stats['timing_stats'].items():
                    st.write(f"• {operation}: {data['avg_duration']:.3f}s 平均")
            
            if stats['cache_stats']:
                st.write("**缓存命中率:**")
                for func_name, data in stats['cache_stats'].items():
                    hit_rate = data['hit_rate'] * 100
                    st.write(f"• {func_name}: {hit_rate:.1f}%")


def clear_all_caches():
    """清理所有Streamlit缓存"""
    st.cache_data.clear()
    st.cache_resource.clear()
    logger.info("已清理所有Streamlit缓存")


class LazyLoader:
    """延迟加载器"""
    
    def __init__(self, loader_func: Callable, *args, **kwargs):
        self.loader_func = loader_func
        self.args = args
        self.kwargs = kwargs
        self._loaded_value = None
        self._is_loaded = False
    
    def get(self):
        """获取延迟加载的值"""
        if not self._is_loaded:
            start_time = time.time()
            self._loaded_value = self.loader_func(*self.args, **self.kwargs)
            self._is_loaded = True
            duration = time.time() - start_time
            _performance_monitor.record_timing(f"lazy_load_{self.loader_func.__name__}", duration)
        
        return self._loaded_value
    
    def is_loaded(self) -> bool:
        """检查是否已加载"""
        return self._is_loaded
    
    def reset(self):
        """重置加载状态"""
        self._loaded_value = None
        self._is_loaded = False


def create_lazy_loader(loader_func: Callable, *args, **kwargs) -> LazyLoader:
    """创建延迟加载器"""
    return LazyLoader(loader_func, *args, **kwargs)