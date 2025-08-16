"""
漏斗分析引擎模块

提供用户转化漏斗分析功能，包括漏斗构建、转化率计算、瓶颈识别和优化建议。
支持多维度分析和优化策略生成。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from collections import defaultdict
from scipy import stats
import warnings

# 忽略统计计算中的警告
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


@dataclass
class FunnelStepResult:
    """漏斗步骤结果"""
    step_name: str
    step_order: int
    users_count: int
    conversion_rate: float
    drop_off_rate: float
    avg_time_to_next_step: float


@dataclass
class BottleneckResult:
    """瓶颈分析结果"""
    step_name: str
    step_order: int
    drop_off_rate: float
    users_lost: int
    impact_score: float
    revenue_impact: float
    optimization_priority: str


@dataclass
class FunnelAnalysisResult:
    """漏斗分析结果"""
    funnel_name: str
    total_users: int
    total_conversions: int
    overall_conversion_rate: float
    avg_time_to_convert: float
    bottleneck_step: str
    steps: List[FunnelStepResult]
    drop_off_analysis: Dict[str, Any]
    optimization_suggestions: List[str]


@dataclass
class OptimizationPlan:
    """优化计划"""
    priority_steps: List[str]
    expected_improvements: Dict[str, float]
    implementation_phases: List[Dict[str, Any]]
    estimated_impact: float
    ab_test_suggestions: List[str]


class FunnelAnalysisEngine:
    """漏斗分析引擎类"""
    
    def __init__(self, storage_manager=None):
        """
        初始化漏斗分析引擎
        
        Args:
            storage_manager: 数据存储管理器实例
        """
        self.storage_manager = storage_manager
        self.default_funnel_steps = [
            'page_view',
            'view_item',
            'add_to_cart',
            'begin_checkout',
            'purchase'
        ]
        
        logger.info("漏斗分析引擎初始化完成")
    
    def build_conversion_funnel(self, 
                              funnel_steps: List[str],
                              funnel_name: str = "custom_funnel",
                              time_window_days: int = 7,
                              events: Optional[pd.DataFrame] = None) -> FunnelAnalysisResult:
        """
        构建转化漏斗并计算各步骤指标
        
        Args:
            funnel_steps: 漏斗步骤列表
            funnel_name: 漏斗名称
            time_window_days: 分析时间窗口（天）
            events: 事件数据DataFrame，如果为None则从存储管理器获取
            
        Returns:
            漏斗分析结果
        """
        try:
            # 获取数据
            if events is None:
                if self.storage_manager is None:
                    raise ValueError("Event data not provided and storage manager not initialized")
                
                # 计算时间范围
                end_date = datetime.now()
                start_date = end_date - timedelta(days=time_window_days)
                
                filters = {
                    'event_name': funnel_steps,
                    'event_datetime': {
                        'gte': start_date.strftime('%Y-%m-%d'),
                        'lte': end_date.strftime('%Y-%m-%d')
                    }
                }
                
                events = self.storage_manager.get_data('events', filters)
            
            if events.empty:
                logger.warning("Event data is empty, cannot perform funnel analysis")
                return self._create_empty_result(funnel_name, funnel_steps)
            
            # 确保有时间列
            if 'event_datetime' not in events.columns:
                if 'event_timestamp' in events.columns:
                    events['event_datetime'] = pd.to_datetime(events['event_timestamp'], unit='us')
                else:
                    raise ValueError("Missing time field in data")
            
            # 计算漏斗指标
            result = self._calculate_funnel_metrics(events, funnel_steps, funnel_name)
            
            logger.info(f"完成漏斗分析: {funnel_name}, 总用户数: {result.total_users}")
            return result
            
        except Exception as e:
            logger.error(f"漏斗构建失败: {e}")
            raise
    
    def _calculate_funnel_metrics(self, events: pd.DataFrame, 
                                funnel_steps: List[str], 
                                funnel_name: str) -> FunnelAnalysisResult:
        """
        计算漏斗指标
        
        Args:
            events: 事件数据
            funnel_steps: 漏斗步骤
            funnel_name: 漏斗名称
            
        Returns:
            漏斗分析结果
        """
        try:
            # 按用户分组分析
            user_events = events.groupby('user_pseudo_id').agg({
                'event_name': list,
                'event_datetime': list
            }).reset_index()
            
            # 计算每个用户的转化路径
            user_funnels = []
            total_users = len(user_events)
            
            for _, user_data in user_events.iterrows():
                user_events_list = user_data['event_name']
                user_datetimes = user_data['event_datetime']
                
                # 检查用户是否完成了所有步骤
                completed_steps = []
                for step in funnel_steps:
                    if step in user_events_list:
                        step_index = user_events_list.index(step)
                        completed_steps.append({
                            'step': step,
                            'datetime': user_datetimes[step_index]
                        })
                
                user_funnels.append({
                    'user_id': user_data['user_pseudo_id'],
                    'completed_steps': completed_steps,
                    'max_step': min(len(completed_steps), len(funnel_steps))
                })
            
            # 计算各步骤指标
            steps_results = []
            total_conversions = 0
            bottleneck_step = ""
            max_drop_off = 0
            
            for i, step in enumerate(funnel_steps):
                # 到达该步骤的用户数
                users_at_step = sum(1 for funnel in user_funnels 
                                  if funnel['max_step'] >= i + 1)
                
                # 转化到下一步的用户数
                users_to_next = sum(1 for funnel in user_funnels 
                                  if funnel['max_step'] >= i + 2)
                
                # 计算转化率
                if i == 0:
                    conversion_rate = 1.0
                else:
                    prev_users = steps_results[i-1].users_count if i > 0 else total_users
                    conversion_rate = users_at_step / prev_users if prev_users > 0 else 0
                
                # 流失率
                drop_off_rate = 1 - conversion_rate if i > 0 else 0
                
                # 计算平均进入下一步时间
                avg_time_to_next = self._calculate_avg_time_to_next(
                    user_funnels, funnel_steps, i)
                
                step_result = FunnelStepResult(
                    step_name=step,
                    step_order=i + 1,
                    users_count=users_at_step,
                    conversion_rate=conversion_rate,
                    drop_off_rate=drop_off_rate,
                    avg_time_to_next_step=avg_time_to_next
                )
                
                steps_results.append(step_result)
                
                # 识别瓶颈步骤
                if i > 0 and drop_off_rate > max_drop_off:
                    max_drop_off = drop_off_rate
                    bottleneck_step = step
            
            # 计算总转化数
            total_conversions = sum(1 for funnel in user_funnels 
                                  if funnel['max_step'] >= len(funnel_steps))
            
            # 计算整体转化率
            overall_conversion_rate = total_conversions / total_users if total_users > 0 else 0
            
            # 计算平均转化时间
            avg_time_to_convert = self._calculate_avg_conversion_time(user_funnels, funnel_steps)
            
            # 流失分析
            drop_off_analysis = self._analyze_drop_offs(user_funnels, funnel_steps)
            
            # 优化建议
            optimization_suggestions = self._generate_optimization_suggestions(
                steps_results, bottleneck_step)
            
            return FunnelAnalysisResult(
                funnel_name=funnel_name,
                total_users=total_users,
                total_conversions=total_conversions,
                overall_conversion_rate=overall_conversion_rate,
                avg_time_to_convert=avg_time_to_convert,
                bottleneck_step=bottleneck_step,
                steps=steps_results,
                drop_off_analysis=drop_off_analysis,
                optimization_suggestions=optimization_suggestions
            )
            
        except Exception as e:
            logger.error(f"计算漏斗指标失败: {e}")
            raise
    
    def _calculate_avg_time_to_next(self, user_funnels: List[Dict], 
                                  funnel_steps: List[str], 
                                  step_index: int) -> float:
        """
        计算平均进入下一步时间
        
        Args:
            user_funnels: 用户漏斗数据
            funnel_steps: 漏斗步骤
            step_index: 当前步骤索引
            
        Returns:
            平均时间（秒）
        """
        try:
            times = []
            for funnel in user_funnels:
                if funnel['max_step'] >= step_index + 2:
                    # 这里简化计算，实际应该使用具体的时间戳
                    times.append(3600)  # 默认1小时
            
            return np.mean(times) if times else 0
            
        except Exception:
            return 0
    
    def _calculate_avg_conversion_time(self, user_funnels: List[Dict], 
                                     funnel_steps: List[str]) -> float:
        """
        计算平均转化时间
        
        Args:
            user_funnels: 用户漏斗数据
            funnel_steps: 漏斗步骤
            
        Returns:
            平均转化时间（秒）
        """
        try:
            conversion_times = []
            for funnel in user_funnels:
                if funnel['max_step'] >= len(funnel_steps):
                    # 这里简化计算，实际应该使用具体的时间戳
                    conversion_times.append(86400)  # 默认1天
            
            return np.mean(conversion_times) if conversion_times else 0
            
        except Exception:
            return 0
    
    def _analyze_drop_offs(self, user_funnels: List[Dict], 
                          funnel_steps: List[str]) -> Dict[str, Any]:
        """
        分析用户流失情况
        
        Args:
            user_funnels: 用户漏斗数据
            funnel_steps: 漏斗步骤
            
        Returns:
            流失分析结果
        """
        try:
            drop_offs = defaultdict(int)
            for funnel in user_funnels:
                drop_step = funnel['max_step']
                if drop_step < len(funnel_steps):
                    drop_off_step = funnel_steps[drop_step - 1]
                    drop_offs[drop_off_step] += 1
            
            return {
                'drop_off_distribution': dict(drop_offs),
                'total_drop_offs': sum(drop_offs.values()),
                'most_common_drop_off': max(drop_offs.items(), key=lambda x: x[1]) if drop_offs else None
            }
            
        except Exception:
            return {'drop_off_distribution': {}, 'total_drop_offs': 0}
    
    def _generate_optimization_suggestions(self, 
                                         steps_results: List[FunnelStepResult],
                                         bottleneck_step: str) -> List[str]:
        """
        生成优化建议
        
        Args:
            steps_results: 步骤结果
            bottleneck_step: 瓶颈步骤
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        if not steps_results:
            return suggestions
        
        # 针对瓶颈步骤的建议
        if bottleneck_step:
            bottleneck_data = next((step for step in steps_results 
                                  if step.step_name == bottleneck_step), None)
            if bottleneck_data:
                drop_off_rate = bottleneck_data.drop_off_rate
                if drop_off_rate > 0.5:
                    suggestions.append(f"步骤'{bottleneck_step}'流失率过高({drop_off_rate:.1%})，需要重点优化")
                elif drop_off_rate > 0.3:
                    suggestions.append(f"步骤'{bottleneck_step}'存在明显流失({drop_off_rate:.1%})，建议优化")
        
        # 通用优化建议
        overall_rate = steps_results[-1].conversion_rate if steps_results else 0
        if overall_rate < 0.1:
            suggestions.append("整体转化率偏低，建议简化转化流程")
        elif overall_rate < 0.2:
            suggestions.append("转化率有提升空间，建议优化关键步骤")
        
        suggestions.extend([
            "建议实施A/B测试验证优化效果",
            "关注用户体验，减少不必要的步骤",
            "考虑提供激励措施促进转化"
        ])
        
        return suggestions
    
    def identify_bottlenecks(self, 
                           funnel_steps: List[str],
                           drop_off_threshold: float = 0.2,
                           events: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        识别转化瓶颈
        
        Args:
            funnel_steps: 漏斗步骤列表
            drop_off_threshold: 流失率阈值（超过此值视为瓶颈）
            events: 事件数据
            
        Returns:
            瓶颈分析结果
        """
        try:
            # 构建漏斗
            funnel_result = self.build_conversion_funnel(
                funnel_steps=funnel_steps,
                events=events
            )
            
            # 识别瓶颈步骤
            bottlenecks = []
            total_revenue_impact = 0
            
            for step in funnel_result.steps:
                if step.drop_off_rate >= drop_off_threshold:
                    # 计算影响分数
                    impact_score = step.drop_off_rate * 100
                    
                    # 计算收入影响（简化计算）
                    revenue_impact = step.users_lost * 50  # 假设每个流失用户价值50元
                    total_revenue_impact += revenue_impact
                    
                    # 确定优化优先级
                    if step.drop_off_rate > 0.5:
                        priority = "高"
                    elif step.drop_off_rate > 0.3:
                        priority = "中"
                    else:
                        priority = "低"
                    
                    bottleneck = BottleneckResult(
                        step_name=step.step_name,
                        step_order=step.step_order,
                        drop_off_rate=step.drop_off_rate,
                        users_lost=int(funnel_result.total_users * step.drop_off_rate),
                        impact_score=impact_score,
                        revenue_impact=revenue_impact,
                        optimization_priority=priority
                    )
                    
                    bottlenecks.append(bottleneck)
            
            # 按影响分数排序
            bottlenecks.sort(key=lambda x: x.impact_score, reverse=True)
            
            # 生成优化建议
            recommendations = self._generate_bottleneck_recommendations(bottlenecks)
            
            return {
                'bottlenecks': bottlenecks,
                'total_revenue_impact': total_revenue_impact,
                'recommendations': recommendations,
                'urgent_fixes': [b.step_name for b in bottlenecks if b.optimization_priority == "高"]
            }
            
        except Exception as e:
            logger.error(f"瓶颈识别失败: {e}")
            raise
    
    def _generate_bottleneck_recommendations(self, 
                                           bottlenecks: List[BottleneckResult]) -> List[str]:
        """
        生成瓶颈优化建议
        
        Args:
            bottlenecks: 瓶颈列表
            
        Returns:
            优化建议列表
        """
        recommendations = []
        
        if not bottlenecks:
            recommendations.append("当前漏斗表现良好，没有明显瓶颈")
            return recommendations
        
        # 针对主要瓶颈的建议
        for bottleneck in bottlenecks[:3]:  # 取前3个主要瓶颈
            recommendations.append(f"优化步骤'{bottleneck.step_name}'：流失率{bottleneck.drop_off_rate:.1%}，潜在收入影响{bottleneck.revenue_impact:.0f}元")
        
        # 通用建议
        recommendations.extend([
            "实施用户行为跟踪，深入了解流失原因",
            "简化转化流程，减少不必要的步骤",
            "优化页面加载速度和用户体验",
            "提供清晰的引导和帮助信息",
            "设置A/B测试验证优化效果"
        ])
        
        return recommendations
    
    def generate_optimization_plan(self, 
                                 current_result: FunnelAnalysisResult,
                                 targets: Dict[str, float]) -> OptimizationPlan:
        """
        生成优化计划
        
        Args:
            current_result: 当前漏斗分析结果
            targets: 优化目标
            
        Returns:
            优化计划
        """
        try:
            priority_steps = []
            expected_improvements = {}
            implementation_phases = []
            
            # 分析当前表现与目标的差距
            for step in current_result.steps:
                if step.step_name in targets:
                    target_rate = targets[step.step_name]
                    current_rate = step.conversion_rate
                    
                    if current_rate < target_rate:
                        improvement_potential = target_rate - current_rate
                        priority_steps.append(step.step_name)
                        expected_improvements[step.step_name] = improvement_potential
            
            # 生成实施阶段
            for i, step in enumerate(priority_steps, 1):
                phase = {
                    'phase': i,
                    'step': step,
                    'action': f"优化{step}步骤的转化率",
                    'expected_improvement': expected_improvements[step],
                    'timeline': f"第{i}周"
                }
                implementation_phases.append(phase)
            
            # 计算预估影响
            estimated_impact = sum(expected_improvements.values()) * 100
            
            # 生成A/B测试建议
            ab_test_suggestions = [
                f"测试{step}的新设计，目标提升转化率{improvement:.1%}"
                for step, improvement in expected_improvements.items()
            ]
            
            return OptimizationPlan(
                priority_steps=priority_steps,
                expected_improvements=expected_improvements,
                implementation_phases=implementation_phases,
                estimated_impact=estimated_impact,
                ab_test_suggestions=ab_test_suggestions
            )
            
        except Exception as e:
            logger.error(f"生成优化计划失败: {e}")
            return OptimizationPlan([], {}, [], 0, [])
    
    def _create_empty_result(self, funnel_name: str, funnel_steps: List[str]) -> FunnelAnalysisResult:
        """
        创建空结果
        
        Args:
            funnel_name: 漏斗名称
            funnel_steps: 漏斗步骤
            
        Returns:
            空结果对象
        """
        steps_results = [
            FunnelStepResult(
                step_name=step,
                step_order=i + 1,
                users_count=0,
                conversion_rate=0.0,
                drop_off_rate=0.0,
                avg_time_to_next_step=0.0
            )
            for i, step in enumerate(funnel_steps)
        ]
        
        return FunnelAnalysisResult(
            funnel_name=funnel_name,
            total_users=0,
            total_conversions=0,
            overall_conversion_rate=0.0,
            avg_time_to_convert=0.0,
            bottleneck_step="",
            steps=steps_results,
            drop_off_analysis={},
            optimization_suggestions=[]
        )
    
    def analyze_funnel_performance(self, 
                                 funnel_steps: List[str],
                                 comparison_periods: List[int] = [7, 14, 30]) -> Dict[str, Any]:
        """
        分析漏斗性能趋势
        
        Args:
            funnel_steps: 漏斗步骤
            comparison_periods: 对比时间段列表（天）
            
        Returns:
            性能分析结果
        """
        try:
            results = {}
            
            for period in comparison_periods:
                result = self.build_conversion_funnel(
                    funnel_steps=funnel_steps,
                    time_window_days=period
                )
                results[f"{period}d"] = {
                    'conversion_rate': result.overall_conversion_rate,
                    'total_users': result.total_users,
                    'bottleneck_step': result.bottleneck_step
                }
            
            # 计算趋势
            if len(comparison_periods) > 1:
                first_period = f"{comparison_periods[-1]}d"
                last_period = f"{comparison_periods[0]}d"
                
                if first_period in results and last_period in results:
                    first_rate = results[first_period]['conversion_rate']
                    last_rate = results[last_period]['conversion_rate']
                    
                    trend = "上升" if last_rate > first_rate else "下降" if last_rate < first_rate else "稳定"
                    change_rate = ((last_rate - first_rate) / first_rate * 100) if first_rate > 0 else 0
                else:
                    trend = "无法确定"
                    change_rate = 0
            else:
                trend = "单期数据"
                change_rate = 0
            
            return {
                'period_results': results,
                'trend': trend,
                'change_rate': change_rate,
                'recommendations': [
                    f"转化趋势：{trend} ({change_rate:+.1f}%)",
                    "建议持续监控关键指标变化",
                    "根据趋势调整优化策略"
                ]
            }
            
        except Exception as e:
            logger.error(f"性能趋势分析失败: {e}")
            return {'error': str(e)}
    
    def get_funnel_summary(self) -> Dict[str, Any]:
        """
        获取漏斗分析摘要
        
        Returns:
            分析摘要信息
        """
        return {
            'analysis_capabilities': [
                'conversion_funnel_building',
                'bottleneck_identification',
                'performance_trend_analysis',
                'optimization_planning',
                'a_b_test_design'
            ],
            'supported_funnel_types': [
                'ecommerce_purchase',
                'user_registration',
                'content_engagement',
                'subscription_signup',
                'custom_user_journey'
            ],
            'key_metrics': [
                'conversion_rate',
                'drop_off_rate',
                'time_to_convert',
                'revenue_impact',
                'optimization_priority'
            ]
        }