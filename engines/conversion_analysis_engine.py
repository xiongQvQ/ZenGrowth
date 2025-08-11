"""
转化分析引擎模块

提供转化漏斗构建和转化率计算功能。
支持瓶颈识别和流失点分析。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict, OrderedDict
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


@dataclass
class FunnelStep:
    """漏斗步骤数据模型"""
    step_name: str
    step_order: int
    total_users: int
    conversion_rate: float
    drop_off_rate: float
    avg_time_to_next_step: Optional[float]
    median_time_to_next_step: Optional[float]


@dataclass
class ConversionFunnel:
    """转化漏斗数据模型"""
    funnel_name: str
    steps: List[FunnelStep]
    overall_conversion_rate: float
    total_users_entered: int
    total_users_converted: int
    avg_completion_time: Optional[float]
    bottleneck_step: Optional[str]


@dataclass
class ConversionAnalysisResult:
    """转化分析结果"""
    funnels: List[ConversionFunnel]
    conversion_metrics: Dict[str, float]
    bottleneck_analysis: Dict[str, Any]
    time_analysis: Dict[str, Any]
    segment_analysis: Dict[str, Any]


@dataclass
class UserConversionJourney:
    """用户转化旅程"""
    user_id: str
    journey_steps: List[Dict[str, Any]]
    conversion_status: str  # 'converted', 'dropped_off', 'in_progress'
    drop_off_step: Optional[str]
    total_journey_time: Optional[float]
    conversion_value: Optional[float]


class ConversionAnalysisEngine:
    """转化分析引擎类"""
    
    def __init__(self, storage_manager=None):
        """
        初始化转化分析引擎
        
        Args:
            storage_manager: 数据存储管理器实例
        """
        self.storage_manager = storage_manager
        
        # 预定义的转化漏斗
        self.predefined_funnels = {
            'user_registration': [
                'page_view', 'sign_up', 'login'
            ],
            'purchase_funnel': [
                'page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase'
            ],
            'engagement_funnel': [
                'page_view', 'view_item', 'search', 'view_item_list'
            ],
            'checkout_funnel': [
                'add_to_cart', 'begin_checkout', 'add_payment_info', 'purchase'
            ]
        }
        
        # 转化事件定义
        self.conversion_events = {
            'sign_up', 'login', 'purchase', 'begin_checkout', 
            'add_to_cart', 'add_payment_info', 'subscribe'
        }
        
        logger.info("转化分析引擎初始化完成")
        
    def build_conversion_funnel(self,
                              events: Optional[pd.DataFrame] = None,
                              funnel_steps: List[str] = None,
                              funnel_name: str = "custom_funnel",
                              time_window_hours: int = 24) -> ConversionFunnel:
        """
        构建转化漏斗
        
        Args:
            events: 事件数据DataFrame
            funnel_steps: 漏斗步骤列表
            funnel_name: 漏斗名称
            time_window_hours: 时间窗口（小时）
            
        Returns:
            转化漏斗对象
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if events.empty:
                logger.warning("事件数据为空，无法构建转化漏斗")
                return ConversionFunnel(
                    funnel_name=funnel_name,
                    steps=[],
                    overall_conversion_rate=0.0,
                    total_users_entered=0,
                    total_users_converted=0,
                    avg_completion_time=None,
                    bottleneck_step=None
                )
                
            if not funnel_steps:
                raise ValueError("必须提供漏斗步骤")
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("缺少时间字段")
                    
            # 筛选相关事件
            funnel_events = events[events['event_name'].isin(funnel_steps)].copy()
            
            if funnel_events.empty:
                logger.warning(f"没有找到漏斗步骤相关的事件: {funnel_steps}")
                return ConversionFunnel(
                    funnel_name=funnel_name,
                    steps=[],
                    overall_conversion_rate=0.0,
                    total_users_entered=0,
                    total_users_converted=0,
                    avg_completion_time=None,
                    bottleneck_step=None
                )
                
            # 按用户分组分析转化路径
            user_journeys = self._analyze_user_journeys(
                funnel_events, funnel_steps, time_window_hours
            )
            
            # 构建漏斗步骤
            funnel_step_objects = self._build_funnel_steps(
                user_journeys, funnel_steps
            )
            
            # 计算整体转化率
            total_users_entered = len(user_journeys)
            total_users_converted = sum(
                1 for journey in user_journeys.values() 
                if journey['completed_all_steps']
            )
            
            overall_conversion_rate = (
                total_users_converted / total_users_entered 
                if total_users_entered > 0 else 0
            )
            
            # 计算平均完成时间
            completion_times = [
                journey['total_time'] for journey in user_journeys.values()
                if journey['completed_all_steps'] and journey['total_time'] is not None
            ]
            
            avg_completion_time = np.mean(completion_times) if completion_times else None
            
            # 识别瓶颈步骤
            bottleneck_step = self._identify_bottleneck_step(funnel_step_objects)
            
            funnel = ConversionFunnel(
                funnel_name=funnel_name,
                steps=funnel_step_objects,
                overall_conversion_rate=overall_conversion_rate,
                total_users_entered=total_users_entered,
                total_users_converted=total_users_converted,
                avg_completion_time=avg_completion_time,
                bottleneck_step=bottleneck_step
            )
            
            logger.info(f"构建转化漏斗 '{funnel_name}' 完成，整体转化率: {overall_conversion_rate:.3f}")
            return funnel
            
        except Exception as e:
            logger.error(f"构建转化漏斗失败: {e}")
            raise
            
    def _analyze_user_journeys(self,
                             events: pd.DataFrame,
                             funnel_steps: List[str],
                             time_window_hours: int) -> Dict[str, Dict[str, Any]]:
        """
        分析用户转化旅程
        
        Args:
            events: 事件数据
            funnel_steps: 漏斗步骤
            time_window_hours: 时间窗口
            
        Returns:
            用户旅程字典
        """
        try:
            user_journeys = {}
            
            # 按用户分组
            for user_id in events['user_pseudo_id'].unique():
                user_events = events[events['user_pseudo_id'] == user_id].sort_values('event_datetime')
                
                # 分析用户的转化路径
                journey = self._analyze_single_user_journey(
                    user_events, funnel_steps, time_window_hours
                )
                
                if journey:
                    user_journeys[user_id] = journey
                    
            return user_journeys
            
        except Exception as e:
            logger.warning(f"分析用户旅程失败: {e}")
            return {}
            
    def _analyze_single_user_journey(self,
                                   user_events: pd.DataFrame,
                                   funnel_steps: List[str],
                                   time_window_hours: int) -> Optional[Dict[str, Any]]:
        """
        分析单个用户的转化旅程
        
        Args:
            user_events: 用户事件数据
            funnel_steps: 漏斗步骤
            time_window_hours: 时间窗口
            
        Returns:
            用户旅程信息
        """
        try:
            # 找到用户完成的步骤
            completed_steps = []
            step_times = {}
            
            # 按顺序查找每个步骤
            last_step_time = None
            
            for step_idx, step_name in enumerate(funnel_steps):
                # 查找该步骤的事件
                step_events = user_events[user_events['event_name'] == step_name]
                
                if step_events.empty:
                    # 用户没有完成这个步骤
                    break
                    
                # 如果不是第一步，检查时间窗口
                if last_step_time is not None:
                    # 找到在时间窗口内的事件
                    valid_events = step_events[
                        step_events['event_datetime'] >= last_step_time
                    ]
                    valid_events = valid_events[
                        (valid_events['event_datetime'] - last_step_time).dt.total_seconds() 
                        <= time_window_hours * 3600
                    ]
                    
                    if valid_events.empty:
                        # 没有在时间窗口内完成
                        break
                        
                    step_time = valid_events['event_datetime'].iloc[0]
                else:
                    # 第一步，取最早的事件
                    step_time = step_events['event_datetime'].iloc[0]
                    
                completed_steps.append(step_name)
                step_times[step_name] = step_time
                last_step_time = step_time
                
            if not completed_steps:
                return None
                
            # 计算旅程信息
            completed_all_steps = len(completed_steps) == len(funnel_steps)
            
            # 计算总时间
            if len(completed_steps) > 1:
                first_step_time = step_times[completed_steps[0]]
                last_step_time = step_times[completed_steps[-1]]
                total_time = (last_step_time - first_step_time).total_seconds()
            else:
                total_time = None
                
            # 计算步骤间时间
            step_durations = {}
            for i in range(len(completed_steps) - 1):
                current_step = completed_steps[i]
                next_step = completed_steps[i + 1]
                duration = (step_times[next_step] - step_times[current_step]).total_seconds()
                step_durations[f"{current_step}_to_{next_step}"] = duration
                
            return {
                'completed_steps': completed_steps,
                'step_times': step_times,
                'completed_all_steps': completed_all_steps,
                'total_time': total_time,
                'step_durations': step_durations,
                'drop_off_step': completed_steps[-1] if not completed_all_steps else None
            }
            
        except Exception as e:
            logger.warning(f"分析单用户旅程失败: {e}")
            return None
            
    def _build_funnel_steps(self,
                          user_journeys: Dict[str, Dict[str, Any]],
                          funnel_steps: List[str]) -> List[FunnelStep]:
        """
        构建漏斗步骤对象
        
        Args:
            user_journeys: 用户旅程数据
            funnel_steps: 漏斗步骤列表
            
        Returns:
            漏斗步骤对象列表
        """
        try:
            funnel_step_objects = []
            total_users = len(user_journeys)
            
            for step_idx, step_name in enumerate(funnel_steps):
                # 计算到达该步骤的用户数
                users_reached_step = sum(
                    1 for journey in user_journeys.values()
                    if step_name in journey['completed_steps']
                )
                
                # 计算转化率
                if step_idx == 0:
                    # 第一步的转化率是到达率
                    conversion_rate = users_reached_step / total_users if total_users > 0 else 0
                else:
                    # 其他步骤的转化率是相对于上一步的
                    prev_step = funnel_steps[step_idx - 1]
                    users_reached_prev_step = sum(
                        1 for journey in user_journeys.values()
                        if prev_step in journey['completed_steps']
                    )
                    conversion_rate = (
                        users_reached_step / users_reached_prev_step 
                        if users_reached_prev_step > 0 else 0
                    )
                    
                # 计算流失率
                drop_off_rate = 1 - conversion_rate
                
                # 计算到下一步的时间
                if step_idx < len(funnel_steps) - 1:
                    next_step = funnel_steps[step_idx + 1]
                    transition_key = f"{step_name}_to_{next_step}"
                    
                    transition_times = [
                        journey['step_durations'].get(transition_key)
                        for journey in user_journeys.values()
                        if transition_key in journey.get('step_durations', {})
                    ]
                    
                    avg_time_to_next = np.mean(transition_times) if transition_times else None
                    median_time_to_next = np.median(transition_times) if transition_times else None
                else:
                    avg_time_to_next = None
                    median_time_to_next = None
                    
                funnel_step = FunnelStep(
                    step_name=step_name,
                    step_order=step_idx,
                    total_users=users_reached_step,
                    conversion_rate=conversion_rate,
                    drop_off_rate=drop_off_rate,
                    avg_time_to_next_step=avg_time_to_next,
                    median_time_to_next_step=median_time_to_next
                )
                
                funnel_step_objects.append(funnel_step)
                
            return funnel_step_objects
            
        except Exception as e:
            logger.warning(f"构建漏斗步骤失败: {e}")
            return []
            
    def _identify_bottleneck_step(self, funnel_steps: List[FunnelStep]) -> Optional[str]:
        """
        识别瓶颈步骤
        
        Args:
            funnel_steps: 漏斗步骤列表
            
        Returns:
            瓶颈步骤名称
        """
        try:
            if len(funnel_steps) < 2:
                return None
                
            # 找到转化率最低的步骤（排除第一步）
            min_conversion_rate = float('inf')
            bottleneck_step = None
            
            for step in funnel_steps[1:]:  # 排除第一步
                if step.conversion_rate < min_conversion_rate:
                    min_conversion_rate = step.conversion_rate
                    bottleneck_step = step.step_name
                    
            return bottleneck_step
            
        except Exception as e:
            logger.warning(f"识别瓶颈步骤失败: {e}")
            return None
            
    def calculate_conversion_rates(self,
                                 events: Optional[pd.DataFrame] = None,
                                 funnel_definitions: Optional[Dict[str, List[str]]] = None) -> ConversionAnalysisResult:
        """
        计算转化率
        
        Args:
            events: 事件数据DataFrame
            funnel_definitions: 漏斗定义字典
            
        Returns:
            转化分析结果
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if events.empty:
                logger.warning("事件数据为空，无法计算转化率")
                return ConversionAnalysisResult(
                    funnels=[],
                    conversion_metrics={},
                    bottleneck_analysis={},
                    time_analysis={},
                    segment_analysis={}
                )
                
            # 使用预定义漏斗或自定义漏斗
            if funnel_definitions is None:
                funnel_definitions = self.predefined_funnels
                
            # 构建所有漏斗
            funnels = []
            for funnel_name, funnel_steps in funnel_definitions.items():
                try:
                    funnel = self.build_conversion_funnel(
                        events, funnel_steps, funnel_name
                    )
                    if funnel.steps:  # 只添加有效的漏斗
                        funnels.append(funnel)
                except Exception as e:
                    logger.warning(f"构建漏斗 {funnel_name} 失败: {e}")
                    continue
                    
            # 计算转化指标
            conversion_metrics = self._calculate_conversion_metrics(funnels, events)
            
            # 瓶颈分析
            bottleneck_analysis = self._analyze_bottlenecks(funnels)
            
            # 时间分析
            time_analysis = self._analyze_conversion_times(funnels)
            
            # 分段分析
            segment_analysis = self._analyze_conversion_segments(events, funnels)
            
            result = ConversionAnalysisResult(
                funnels=funnels,
                conversion_metrics=conversion_metrics,
                bottleneck_analysis=bottleneck_analysis,
                time_analysis=time_analysis,
                segment_analysis=segment_analysis
            )
            
            logger.info(f"完成转化分析，包含{len(funnels)}个漏斗")
            return result
            
        except Exception as e:
            logger.error(f"计算转化率失败: {e}")
            raise
            
    def _calculate_conversion_metrics(self,
                                    funnels: List[ConversionFunnel],
                                    events: pd.DataFrame) -> Dict[str, float]:
        """
        计算转化指标
        
        Args:
            funnels: 漏斗列表
            events: 事件数据
            
        Returns:
            转化指标字典
        """
        try:
            metrics = {}
            
            if not funnels:
                return metrics
                
            # 整体转化指标
            total_users = events['user_pseudo_id'].nunique()
            
            # 计算各个转化事件的转化率
            for event_name in self.conversion_events:
                converted_users = events[events['event_name'] == event_name]['user_pseudo_id'].nunique()
                conversion_rate = converted_users / total_users if total_users > 0 else 0
                metrics[f"{event_name}_conversion_rate"] = conversion_rate
                
            # 计算漏斗平均转化率
            funnel_conversion_rates = [funnel.overall_conversion_rate for funnel in funnels]
            if funnel_conversion_rates:
                metrics['avg_funnel_conversion_rate'] = np.mean(funnel_conversion_rates)
                metrics['max_funnel_conversion_rate'] = np.max(funnel_conversion_rates)
                metrics['min_funnel_conversion_rate'] = np.min(funnel_conversion_rates)
                
            # 计算转化用户占比
            conversion_event_users = set()
            for event_name in self.conversion_events:
                event_users = set(events[events['event_name'] == event_name]['user_pseudo_id'])
                conversion_event_users.update(event_users)
                
            metrics['overall_conversion_user_rate'] = (
                len(conversion_event_users) / total_users if total_users > 0 else 0
            )
            
            return metrics
            
        except Exception as e:
            logger.warning(f"计算转化指标失败: {e}")
            return {}
            
    def _analyze_bottlenecks(self, funnels: List[ConversionFunnel]) -> Dict[str, Any]:
        """
        分析瓶颈
        
        Args:
            funnels: 漏斗列表
            
        Returns:
            瓶颈分析结果
        """
        try:
            bottleneck_analysis = {
                'funnel_bottlenecks': {},
                'common_bottlenecks': [],
                'bottleneck_severity': {}
            }
            
            # 分析每个漏斗的瓶颈
            bottleneck_counts = defaultdict(int)
            
            for funnel in funnels:
                if funnel.bottleneck_step:
                    bottleneck_analysis['funnel_bottlenecks'][funnel.funnel_name] = {
                        'bottleneck_step': funnel.bottleneck_step,
                        'overall_conversion_rate': funnel.overall_conversion_rate
                    }
                    bottleneck_counts[funnel.bottleneck_step] += 1
                    
            # 找出常见瓶颈
            if bottleneck_counts:
                sorted_bottlenecks = sorted(
                    bottleneck_counts.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                bottleneck_analysis['common_bottlenecks'] = [
                    {'step': step, 'frequency': count} 
                    for step, count in sorted_bottlenecks
                ]
                
            # 分析瓶颈严重程度
            for funnel in funnels:
                for step in funnel.steps[1:]:  # 排除第一步
                    if step.conversion_rate < 0.3:  # 转化率低于30%认为是严重瓶颈
                        severity = 'high' if step.conversion_rate < 0.1 else 'medium'
                        bottleneck_analysis['bottleneck_severity'][step.step_name] = {
                            'severity': severity,
                            'conversion_rate': step.conversion_rate,
                            'funnel': funnel.funnel_name
                        }
                        
            return bottleneck_analysis
            
        except Exception as e:
            logger.warning(f"分析瓶颈失败: {e}")
            return {}
            
    def _analyze_conversion_times(self, funnels: List[ConversionFunnel]) -> Dict[str, Any]:
        """
        分析转化时间
        
        Args:
            funnels: 漏斗列表
            
        Returns:
            时间分析结果
        """
        try:
            time_analysis = {
                'funnel_completion_times': {},
                'step_transition_times': {},
                'time_insights': []
            }
            
            # 分析每个漏斗的完成时间
            for funnel in funnels:
                if funnel.avg_completion_time is not None:
                    time_analysis['funnel_completion_times'][funnel.funnel_name] = {
                        'avg_completion_time_seconds': funnel.avg_completion_time,
                        'avg_completion_time_minutes': funnel.avg_completion_time / 60,
                        'avg_completion_time_hours': funnel.avg_completion_time / 3600
                    }
                    
            # 分析步骤转换时间
            for funnel in funnels:
                funnel_step_times = {}
                
                for step in funnel.steps:
                    if step.avg_time_to_next_step is not None:
                        funnel_step_times[step.step_name] = {
                            'avg_time_seconds': step.avg_time_to_next_step,
                            'median_time_seconds': step.median_time_to_next_step,
                            'avg_time_minutes': step.avg_time_to_next_step / 60
                        }
                        
                if funnel_step_times:
                    time_analysis['step_transition_times'][funnel.funnel_name] = funnel_step_times
                    
            # 生成时间洞察
            insights = []
            
            # 找出最慢的转换步骤
            all_step_times = []
            for funnel in funnels:
                for step in funnel.steps:
                    if step.avg_time_to_next_step is not None:
                        all_step_times.append({
                            'funnel': funnel.funnel_name,
                            'step': step.step_name,
                            'time': step.avg_time_to_next_step
                        })
                        
            if all_step_times:
                slowest_step = max(all_step_times, key=lambda x: x['time'])
                insights.append(f"最慢的转换步骤是 {slowest_step['funnel']} 漏斗中的 {slowest_step['step']}，"
                              f"平均需要 {slowest_step['time']/60:.1f} 分钟")
                
            time_analysis['time_insights'] = insights
            
            return time_analysis
            
        except Exception as e:
            logger.warning(f"分析转化时间失败: {e}")
            return {}
            
    def _analyze_conversion_segments(self,
                                   events: pd.DataFrame,
                                   funnels: List[ConversionFunnel]) -> Dict[str, Any]:
        """
        分析转化分段
        
        Args:
            events: 事件数据
            funnels: 漏斗列表
            
        Returns:
            分段分析结果
        """
        try:
            segment_analysis = {
                'platform_conversion': {},
                'device_conversion': {},
                'geo_conversion': {},
                'segment_insights': []
            }
            
            # 按平台分析转化
            if 'platform' in events.columns:
                platform_conversion = {}
                for platform in events['platform'].unique():
                    platform_events = events[events['platform'] == platform]
                    platform_users = platform_events['user_pseudo_id'].nunique()
                    
                    # 计算该平台的转化用户数
                    platform_converted = 0
                    for event_name in self.conversion_events:
                        converted_users = platform_events[
                            platform_events['event_name'] == event_name
                        ]['user_pseudo_id'].nunique()
                        platform_converted = max(platform_converted, converted_users)
                        
                    conversion_rate = platform_converted / platform_users if platform_users > 0 else 0
                    platform_conversion[platform] = {
                        'total_users': platform_users,
                        'converted_users': platform_converted,
                        'conversion_rate': conversion_rate
                    }
                    
                segment_analysis['platform_conversion'] = platform_conversion
                
            # 按设备分析转化（如果有设备信息）
            if 'device' in events.columns:
                device_conversion = {}
                for _, row in events.iterrows():
                    device_info = row.get('device', {})
                    if isinstance(device_info, dict) and 'category' in device_info:
                        device_category = device_info['category']
                        if device_category not in device_conversion:
                            device_conversion[device_category] = {'users': set(), 'converted': set()}
                            
                        device_conversion[device_category]['users'].add(row['user_pseudo_id'])
                        
                        if row['event_name'] in self.conversion_events:
                            device_conversion[device_category]['converted'].add(row['user_pseudo_id'])
                            
                # 计算转化率
                for device, data in device_conversion.items():
                    total_users = len(data['users'])
                    converted_users = len(data['converted'])
                    conversion_rate = converted_users / total_users if total_users > 0 else 0
                    
                    segment_analysis['device_conversion'][device] = {
                        'total_users': total_users,
                        'converted_users': converted_users,
                        'conversion_rate': conversion_rate
                    }
                    
            return segment_analysis
            
        except Exception as e:
            logger.warning(f"分析转化分段失败: {e}")
            return {}
            
    def identify_drop_off_points(self,
                               events: Optional[pd.DataFrame] = None,
                               funnel_steps: List[str] = None) -> Dict[str, Any]:
        """
        识别流失点
        
        Args:
            events: 事件数据DataFrame
            funnel_steps: 漏斗步骤列表
            
        Returns:
            流失点分析结果
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if not funnel_steps:
                funnel_steps = self.predefined_funnels['purchase_funnel']
                
            # 构建漏斗
            funnel = self.build_conversion_funnel(events, funnel_steps, "drop_off_analysis")
            
            drop_off_analysis = {
                'funnel_steps': [],
                'major_drop_off_points': [],
                'drop_off_insights': []
            }
            
            # 分析每个步骤的流失情况
            for i, step in enumerate(funnel.steps):
                step_info = {
                    'step_name': step.step_name,
                    'step_order': step.step_order,
                    'users_reached': step.total_users,
                    'conversion_rate': step.conversion_rate,
                    'drop_off_rate': step.drop_off_rate
                }
                
                # 如果不是第一步，计算相对于上一步的流失
                if i > 0:
                    prev_step = funnel.steps[i-1]
                    users_lost = prev_step.total_users - step.total_users
                    step_info['users_lost'] = users_lost
                    step_info['users_lost_rate'] = users_lost / prev_step.total_users if prev_step.total_users > 0 else 0
                    
                drop_off_analysis['funnel_steps'].append(step_info)
                
            # 识别主要流失点（流失率超过50%的步骤）
            for step_info in drop_off_analysis['funnel_steps']:
                if step_info.get('users_lost_rate', 0) > 0.5:
                    drop_off_analysis['major_drop_off_points'].append({
                        'step_name': step_info['step_name'],
                        'drop_off_rate': step_info['users_lost_rate'],
                        'users_lost': step_info.get('users_lost', 0)
                    })
                    
            # 生成流失洞察
            insights = []
            
            if drop_off_analysis['major_drop_off_points']:
                worst_drop_off = max(
                    drop_off_analysis['major_drop_off_points'],
                    key=lambda x: x['drop_off_rate']
                )
                insights.append(
                    f"最严重的流失点是 {worst_drop_off['step_name']}，"
                    f"流失率达到 {worst_drop_off['drop_off_rate']*100:.1f}%"
                )
            else:
                insights.append("未发现严重的流失点，转化流程相对顺畅")
                
            # 分析整体流失模式
            total_entered = funnel.total_users_entered
            total_converted = funnel.total_users_converted
            
            if total_entered > 0:
                overall_drop_off = (total_entered - total_converted) / total_entered
                insights.append(
                    f"整体流失率为 {overall_drop_off*100:.1f}%，"
                    f"共有 {total_entered - total_converted} 用户在转化过程中流失"
                )
                
            drop_off_analysis['drop_off_insights'] = insights
            
            return drop_off_analysis
            
        except Exception as e:
            logger.error(f"识别流失点失败: {e}")
            raise    
        
    def create_user_conversion_journeys(self,
                                       events: Optional[pd.DataFrame] = None,
                                       funnel_steps: List[str] = None) -> List[UserConversionJourney]:
        """
        创建用户转化旅程
        
        Args:
            events: 事件数据DataFrame
            funnel_steps: 漏斗步骤列表
            
        Returns:
            用户转化旅程列表
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if not funnel_steps:
                funnel_steps = self.predefined_funnels['purchase_funnel']
                
            if events.empty:
                logger.warning("事件数据为空，无法创建用户转化旅程")
                return []
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("缺少时间字段")
                    
            journeys = []
            
            # 筛选相关事件
            funnel_events = events[events['event_name'].isin(funnel_steps)]
            
            # 按用户分组创建旅程
            for user_id in funnel_events['user_pseudo_id'].unique():
                user_events = funnel_events[funnel_events['user_pseudo_id'] == user_id].sort_values('event_datetime')
                
                journey = self._create_single_user_journey(user_events, funnel_steps, user_id)
                
                if journey:
                    journeys.append(journey)
                    
            logger.info(f"创建了{len(journeys)}个用户转化旅程")
            return journeys
            
        except Exception as e:
            logger.error(f"创建用户转化旅程失败: {e}")
            raise
            
    def _create_single_user_journey(self,
                                   user_events: pd.DataFrame,
                                   funnel_steps: List[str],
                                   user_id: str) -> Optional[UserConversionJourney]:
        """
        创建单个用户的转化旅程
        
        Args:
            user_events: 用户事件数据
            funnel_steps: 漏斗步骤
            user_id: 用户ID
            
        Returns:
            用户转化旅程
        """
        try:
            if user_events.empty:
                return None
                
            # 构建旅程步骤
            journey_steps = []
            completed_steps = set()
            
            for _, event in user_events.iterrows():
                step_info = {
                    'step_name': event['event_name'],
                    'timestamp': event['event_datetime'],
                    'step_order': funnel_steps.index(event['event_name']) if event['event_name'] in funnel_steps else -1
                }
                journey_steps.append(step_info)
                completed_steps.add(event['event_name'])
                
            # 按步骤顺序排序
            journey_steps.sort(key=lambda x: (x['step_order'], x['timestamp']))
            
            # 确定转化状态
            final_step = funnel_steps[-1]
            if final_step in completed_steps:
                conversion_status = 'converted'
                drop_off_step = None
            else:
                conversion_status = 'dropped_off'
                # 找到最后完成的步骤
                last_completed_order = -1
                for step_name in completed_steps:
                    if step_name in funnel_steps:
                        step_order = funnel_steps.index(step_name)
                        if step_order > last_completed_order:
                            last_completed_order = step_order
                            drop_off_step = step_name
                            
            # 计算总旅程时间
            if len(journey_steps) > 1:
                total_journey_time = (
                    journey_steps[-1]['timestamp'] - journey_steps[0]['timestamp']
                ).total_seconds()
            else:
                total_journey_time = None
                
            # 计算转化价值（如果有购买事件）
            conversion_value = None
            if 'purchase' in completed_steps:
                # 这里可以根据实际业务逻辑计算转化价值
                # 暂时设为固定值或从事件参数中提取
                conversion_value = 100.0  # 示例值
                
            return UserConversionJourney(
                user_id=user_id,
                journey_steps=journey_steps,
                conversion_status=conversion_status,
                drop_off_step=drop_off_step,
                total_journey_time=total_journey_time,
                conversion_value=conversion_value
            )
            
        except Exception as e:
            logger.warning(f"创建用户 {user_id} 转化旅程失败: {e}")
            return None
            
    def analyze_conversion_attribution(self,
                                     events: Optional[pd.DataFrame] = None,
                                     attribution_window_days: int = 7) -> Dict[str, Any]:
        """
        分析转化归因
        
        Args:
            events: 事件数据DataFrame
            attribution_window_days: 归因窗口天数
            
        Returns:
            转化归因分析结果
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("未提供事件数据且存储管理器未初始化")
                events = self.storage_manager.get_data('events')
                
            if events.empty:
                logger.warning("事件数据为空，无法进行转化归因分析")
                return {}
                
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("缺少时间字段")
                    
            attribution_analysis = {
                'first_touch_attribution': {},
                'last_touch_attribution': {},
                'multi_touch_attribution': {},
                'attribution_insights': []
            }
            
            # 获取转化事件
            conversion_events = events[events['event_name'].isin(self.conversion_events)]
            
            if conversion_events.empty:
                return attribution_analysis
                
            # 按用户分析归因
            for user_id in conversion_events['user_pseudo_id'].unique():
                user_events = events[events['user_pseudo_id'] == user_id].sort_values('event_datetime')
                user_conversions = conversion_events[conversion_events['user_pseudo_id'] == user_id]
                
                for _, conversion in user_conversions.iterrows():
                    conversion_time = conversion['event_datetime']
                    attribution_window_start = conversion_time - timedelta(days=attribution_window_days)
                    
                    # 获取归因窗口内的事件
                    attribution_events = user_events[
                        (user_events['event_datetime'] >= attribution_window_start) &
                        (user_events['event_datetime'] <= conversion_time) &
                        (user_events['event_name'] != conversion['event_name'])  # 排除转化事件本身
                    ]
                    
                    if not attribution_events.empty:
                        # 首次接触归因
                        first_touch_event = attribution_events.iloc[0]['event_name']
                        if first_touch_event not in attribution_analysis['first_touch_attribution']:
                            attribution_analysis['first_touch_attribution'][first_touch_event] = 0
                        attribution_analysis['first_touch_attribution'][first_touch_event] += 1
                        
                        # 最后接触归因
                        last_touch_event = attribution_events.iloc[-1]['event_name']
                        if last_touch_event not in attribution_analysis['last_touch_attribution']:
                            attribution_analysis['last_touch_attribution'][last_touch_event] = 0
                        attribution_analysis['last_touch_attribution'][last_touch_event] += 1
                        
                        # 多点接触归因（平均分配）
                        unique_events = attribution_events['event_name'].unique()
                        attribution_weight = 1.0 / len(unique_events)
                        
                        for event_name in unique_events:
                            if event_name not in attribution_analysis['multi_touch_attribution']:
                                attribution_analysis['multi_touch_attribution'][event_name] = 0
                            attribution_analysis['multi_touch_attribution'][event_name] += attribution_weight
                            
            # 生成归因洞察
            insights = []
            
            # 分析首次接触归因
            if attribution_analysis['first_touch_attribution']:
                top_first_touch = max(
                    attribution_analysis['first_touch_attribution'].items(),
                    key=lambda x: x[1]
                )
                insights.append(f"首次接触归因中，{top_first_touch[0]} 贡献了 {top_first_touch[1]} 次转化")
                
            # 分析最后接触归因
            if attribution_analysis['last_touch_attribution']:
                top_last_touch = max(
                    attribution_analysis['last_touch_attribution'].items(),
                    key=lambda x: x[1]
                )
                insights.append(f"最后接触归因中，{top_last_touch[0]} 贡献了 {top_last_touch[1]} 次转化")
                
            attribution_analysis['attribution_insights'] = insights
            
            return attribution_analysis
            
        except Exception as e:
            logger.error(f"转化归因分析失败: {e}")
            raise
            
    def get_conversion_insights(self,
                              conversion_result: ConversionAnalysisResult) -> Dict[str, Any]:
        """
        获取转化分析洞察
        
        Args:
            conversion_result: 转化分析结果
            
        Returns:
            洞察字典
        """
        try:
            insights = {
                'key_metrics': {},
                'optimization_opportunities': [],
                'performance_insights': [],
                'recommendations': []
            }
            
            if not conversion_result.funnels:
                insights['recommendations'].append("数据不足，建议收集更多转化相关数据")
                return insights
                
            # 关键指标
            funnel_conversion_rates = [f.overall_conversion_rate for f in conversion_result.funnels]
            insights['key_metrics'] = {
                'avg_conversion_rate': np.mean(funnel_conversion_rates),
                'best_conversion_rate': np.max(funnel_conversion_rates),
                'worst_conversion_rate': np.min(funnel_conversion_rates),
                'total_funnels_analyzed': len(conversion_result.funnels)
            }
            
            # 优化机会
            for funnel in conversion_result.funnels:
                if funnel.bottleneck_step:
                    bottleneck_step_obj = next(
                        (step for step in funnel.steps if step.step_name == funnel.bottleneck_step),
                        None
                    )
                    if bottleneck_step_obj and bottleneck_step_obj.conversion_rate < 0.5:
                        insights['optimization_opportunities'].append({
                            'funnel': funnel.funnel_name,
                            'bottleneck_step': funnel.bottleneck_step,
                            'conversion_rate': bottleneck_step_obj.conversion_rate,
                            'improvement_potential': f"提升 {funnel.bottleneck_step} 步骤可能带来显著改善"
                        })
                        
            # 性能洞察
            best_funnel = max(conversion_result.funnels, key=lambda f: f.overall_conversion_rate)
            worst_funnel = min(conversion_result.funnels, key=lambda f: f.overall_conversion_rate)
            
            insights['performance_insights'].append(
                f"表现最好的漏斗是 {best_funnel.funnel_name}，转化率为 {best_funnel.overall_conversion_rate:.3f}"
            )
            insights['performance_insights'].append(
                f"表现最差的漏斗是 {worst_funnel.funnel_name}，转化率为 {worst_funnel.overall_conversion_rate:.3f}"
            )
            
            # 生成建议
            recommendations = []
            
            # 基于瓶颈的建议
            bottleneck_analysis = conversion_result.bottleneck_analysis
            if bottleneck_analysis.get('common_bottlenecks'):
                most_common_bottleneck = bottleneck_analysis['common_bottlenecks'][0]
                recommendations.append(
                    f"重点优化 {most_common_bottleneck['step']} 步骤，它是多个漏斗的共同瓶颈"
                )
                
            # 基于转化率的建议
            avg_conversion_rate = insights['key_metrics']['avg_conversion_rate']
            if avg_conversion_rate < 0.1:
                recommendations.append("整体转化率较低，建议全面审查用户体验和转化流程")
            elif avg_conversion_rate < 0.3:
                recommendations.append("转化率有提升空间，建议重点优化关键转化步骤")
                
            # 基于时间分析的建议
            time_analysis = conversion_result.time_analysis
            if time_analysis.get('time_insights'):
                recommendations.extend(time_analysis['time_insights'])
                
            insights['recommendations'] = recommendations
            
            return insights
            
        except Exception as e:
            logger.error(f"获取转化分析洞察失败: {e}")
            return {}
            
    def analyze_conversion_funnel(self, events: pd.DataFrame) -> Dict[str, Any]:
        """
        执行转化漏斗分析（集成管理器接口）
        
        Args:
            events: 事件数据DataFrame
            
        Returns:
            转化分析结果字典
        """
        try:
            if events.empty:
                return {
                    'status': 'error',
                    'message': '事件数据为空',
                    'insights': [],
                    'recommendations': []
                }
            
            # 使用预定义的漏斗进行分析
            conversion_result = self.calculate_conversion_rates(events)
            
            # 生成洞察和建议
            insights = []
            recommendations = []
            
            if conversion_result and conversion_result.funnels:
                # 分析每个漏斗
                for funnel in conversion_result.funnels:
                    overall_rate = funnel.overall_conversion_rate * 100
                    insights.append(f"{funnel.funnel_name}整体转化率: {overall_rate:.1f}%")
                    
                    # 识别瓶颈步骤
                    if funnel.bottleneck_step:
                        insights.append(f"{funnel.funnel_name}瓶颈步骤: {funnel.bottleneck_step}")
                        recommendations.append(f"重点优化{funnel.bottleneck_step}步骤以提升整体转化率")
                    
                    # 分析各步骤转化率
                    low_conversion_steps = [step for step in funnel.steps if step.conversion_rate < 0.3]
                    if low_conversion_steps:
                        step_names = [step.step_name for step in low_conversion_steps]
                        recommendations.append(f"以下步骤转化率较低，需要优化: {', '.join(step_names)}")
                
                # 整体转化分析
                avg_conversion = sum(f.overall_conversion_rate for f in conversion_result.funnels) / len(conversion_result.funnels)
                if avg_conversion < 0.1:
                    recommendations.append("整体转化率偏低，建议全面审查用户体验流程")
                elif avg_conversion > 0.3:
                    insights.append("转化表现良好，可以作为优化基准")
                    recommendations.append("保持当前优秀的转化策略，并考虑扩展到其他场景")
            
            # 分析转化用户特征
            conversion_events = events[events['event_name'].isin(self.conversion_events)]
            if not conversion_events.empty:
                conversion_users = conversion_events['user_pseudo_id'].nunique()
                total_users = events['user_pseudo_id'].nunique()
                conversion_user_rate = conversion_users / total_users * 100
                
                insights.append(f"转化用户占比: {conversion_user_rate:.1f}%")
                
                if conversion_user_rate < 10:
                    recommendations.append("转化用户比例较低，需要提升产品吸引力和转化引导")
                elif conversion_user_rate > 30:
                    recommendations.append("转化用户比例良好，可以重点关注提升转化深度")
            
            return {
                'status': 'success',
                'analysis_type': 'conversion_analysis',
                'data_size': len(events),
                'unique_users': events['user_pseudo_id'].nunique() if 'user_pseudo_id' in events.columns else 0,
                'insights': insights,
                'recommendations': recommendations,
                'detailed_results': {
                    'conversion_result': conversion_result,
                    'funnel_count': len(conversion_result.funnels) if conversion_result else 0
                },
                'execution_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"转化分析执行失败: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'insights': [],
                'recommendations': []
            }
            
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        获取分析摘要
        
        Returns:
            分析摘要字典
        """
        try:
            if self.storage_manager is None:
                return {"error": "存储管理器未初始化"}
                
            events = self.storage_manager.get_data('events')
            
            if events.empty:
                return {"error": "无事件数据"}
                
            # 基础统计
            total_events = len(events)
            unique_users = events['user_pseudo_id'].nunique()
            unique_event_types = events['event_name'].nunique()
            
            # 转化事件统计
            conversion_events_count = len(events[events['event_name'].isin(self.conversion_events)])
            conversion_users_count = events[events['event_name'].isin(self.conversion_events)]['user_pseudo_id'].nunique()
            
            # 时间范围
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                    
            if 'event_datetime' in events.columns:
                date_range = {
                    'start': events['event_datetime'].min().strftime('%Y-%m-%d'),
                    'end': events['event_datetime'].max().strftime('%Y-%m-%d')
                }
            else:
                date_range = {'start': 'N/A', 'end': 'N/A'}
                
            # 可用的漏斗
            available_funnels = list(self.predefined_funnels.keys())
            
            # 转化事件分布
            conversion_event_distribution = {}
            for event_name in self.conversion_events:
                event_count = len(events[events['event_name'] == event_name])
                if event_count > 0:
                    conversion_event_distribution[event_name] = event_count
                    
            return {
                'total_events': total_events,
                'unique_users': unique_users,
                'unique_event_types': unique_event_types,
                'conversion_events_count': conversion_events_count,
                'conversion_users_count': conversion_users_count,
                'conversion_user_rate': conversion_users_count / unique_users if unique_users > 0 else 0,
                'date_range': date_range,
                'available_funnels': available_funnels,
                'conversion_event_distribution': conversion_event_distribution,
                'analysis_capabilities': [
                    'conversion_funnel_building',
                    'conversion_rate_calculation',
                    'bottleneck_identification',
                    'drop_off_point_analysis',
                    'user_journey_creation',
                    'conversion_attribution_analysis'
                ]
            }
            
        except Exception as e:
            logger.error(f"获取分析摘要失败: {e}")
            return {"error": str(e)}