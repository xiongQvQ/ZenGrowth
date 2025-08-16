"""
Enhanced internationalization (i18n) module with comprehensive text localization support.
Implements Zen framework patterns for complete language support across all analysis engines.
"""

import logging
from functools import wraps
from typing import Any, Dict, Optional
from utils.i18n import i18n, t as base_t

logger = logging.getLogger(__name__)

def enhanced_t(key: str, default: Optional[str] = None, **kwargs) -> str:
    """
    Enhanced translation function with parameter substitution support.
    
    Args:
        key: Translation key with dot notation support
        default: Fallback text if translation not found
        **kwargs: Parameters for string formatting
    
    Returns:
        Localized text with parameter substitution
    """
    try:
        # Get base translation
        text = base_t(key, default)
        
        # Apply parameter substitution if kwargs provided
        if kwargs:
            text = text.format(**kwargs)
            
        return text
    except Exception as e:
        logger.warning(f"Translation failed for key '{key}': {e}")
        return default or key

def localized_logger_message(key: str, default: str = None, **kwargs):
    """
    Decorator to automatically localize logger messages.
    
    Args:
        key: Translation key for the message
        default: Fallback message
        **kwargs: Parameters for message formatting
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **func_kwargs):
            try:
                # Get localized message
                message = enhanced_t(key, default, **kwargs)
                # Replace the original message
                if args:
                    args = (message,) + args[1:]
                return func(*args, **func_kwargs)
            except Exception:
                return func(*args, **func_kwargs)
        return wrapper
    return decorator

class LocalizedInsightGenerator:
    """
    Generates localized insights and recommendations for analysis results.
    Implements zen framework patterns for consistent, high-quality analysis output.
    """
    
    @staticmethod
    def format_performance_insight(funnel_name: str, conversion_rate: float, is_best: bool = True) -> str:
        """
        Generate localized performance insight text.
        
        Args:
            funnel_name: Name of the funnel
            conversion_rate: Conversion rate as decimal
            is_best: Whether this is the best or worst performing funnel
        
        Returns:
            Localized insight text
        """
        key = 'conversion_analysis.insights.best_funnel_performance' if is_best else 'conversion_analysis.insights.worst_funnel_performance'
        default = f"{'Best' if is_best else 'Worst'} performing funnel is {funnel_name} with conversion rate of {conversion_rate:.1%}"
        
        return enhanced_t(
            key, 
            default,
            name=funnel_name,
            rate=f"{conversion_rate:.1%}"
        )
    
    @staticmethod
    def format_bottleneck_recommendation(step_name: str) -> str:
        """
        Generate localized bottleneck optimization recommendation.
        
        Args:
            step_name: Name of the bottleneck step
        
        Returns:
            Localized recommendation text
        """
        return enhanced_t(
            'conversion_analysis.recommendations.optimize_common_bottleneck',
            'Focus on optimizing {step} step, which is a common bottleneck across multiple funnels',
            step=step_name
        )
    
    @staticmethod
    def format_segment_insight(segment_name: str, user_count: int, percentage: float) -> str:
        """
        Generate localized user segmentation insight.
        
        Args:
            segment_name: Name of the user segment
            user_count: Number of users in segment
            percentage: Percentage of total users
        
        Returns:
            Localized insight text
        """
        return enhanced_t(
            'user_segmentation.insights.segment_summary',
            '{segment_name} contains {user_count} users, accounting for {percentage:.1f}% of total users',
            segment_name=segment_name,
            user_count=f"{user_count:,}",
            percentage=percentage
        )
    
    # Path analysis specific generators
    @staticmethod
    def format_session_summary(total_sessions: int, avg_path_length: float) -> str:
        """Generate localized session summary."""
        return enhanced_t(
            'path_analysis.insights.session_summary',
            'Analyzed {total_sessions} user sessions with average path length of {avg_path_length:.1f} steps',
            total_sessions=total_sessions,
            avg_path_length=avg_path_length
        )
    
    @staticmethod
    def format_conversion_summary(conversion_rate: float, conversion_sessions: int) -> str:
        """Generate localized conversion summary."""
        return enhanced_t(
            'path_analysis.insights.conversion_summary',
            'Overall conversion rate is {conversion_rate} with {conversion_sessions} converting sessions',
            conversion_rate=f"{conversion_rate:.1%}",
            conversion_sessions=conversion_sessions
        )
    
    @staticmethod
    def format_common_path_insight(path_sequence: list, frequency: int) -> str:
        """Generate localized common path insight."""
        path_str = ' → '.join(path_sequence)
        return enhanced_t(
            'path_analysis.insights.most_common_path',
            'Most common user path is: {path}, appearing {frequency} times',
            path=path_str,
            frequency=frequency
        )
    
    @staticmethod
    def format_conversion_patterns_insight(count: int) -> str:
        """Generate localized conversion patterns insight."""
        return enhanced_t(
            'path_analysis.insights.high_conversion_patterns',
            'Found {count} high-conversion path patterns with conversion rate over 30%',
            count=count
        )
    
    @staticmethod
    def format_anomalous_patterns_insight(count: int) -> str:
        """Generate localized anomalous patterns insight."""
        return enhanced_t(
            'path_analysis.insights.anomalous_patterns',
            'Identified {count} anomalous user behavior patterns that need special attention',
            count=count
        )
    
    @staticmethod
    def format_shortest_conversion_path(length: int, path_sequence: list) -> str:
        """Generate localized shortest conversion path insight."""
        path_str = ' → '.join(path_sequence)
        return enhanced_t(
            'path_analysis.insights.shortest_conversion_path',
            'Shortest conversion path is {length} steps: {path}',
            length=length,
            path=path_str
        )
    
    @staticmethod
    def format_optimization_recommendation(path_sequence: list) -> str:
        """Generate localized path optimization recommendation."""
        path_str = ' → '.join(path_sequence)
        return enhanced_t(
            'path_analysis.recommendations.optimize_common_path',
            'Optimize the most common path "{path}" user experience',
            path=path_str
        )
    
    @staticmethod
    def format_exit_point_recommendation(exit_point: str) -> str:
        """Generate localized exit point optimization recommendation."""
        return enhanced_t(
            'path_analysis.recommendations.optimize_exit_point',
            'Users often leave after "{event}" event, need to optimize the user experience at this stage',
            event=exit_point
        )
    
    # Event analysis specific generators
    @staticmethod
    def format_event_activity_insight(event_types: list) -> str:
        """Generate localized most active event types insight."""
        events_str = ', '.join(event_types)
        return enhanced_t(
            'event_analysis.insights.most_active_events',
            'Most active event types: {events}',
            events=events_str
        )
    
    @staticmethod
    def format_high_frequency_recommendation() -> str:
        """Generate localized high frequency event recommendation."""
        return enhanced_t(
            'event_analysis.recommendations.optimize_high_frequency',
            'Consider focusing on optimizing high-frequency events to improve user experience'
        )
    
    @staticmethod
    def format_trend_insight(increasing_trends: list) -> str:
        """Generate localized increasing trend insight."""
        trends_str = ', '.join(increasing_trends[:3])
        return enhanced_t(
            'event_analysis.insights.increasing_trends',
            'Events with increasing trends: {trends}',
            trends=trends_str
        )
    
    @staticmethod
    def format_trend_recommendation() -> str:
        """Generate localized trend optimization recommendation."""
        return enhanced_t(
            'event_analysis.recommendations.optimize_trends',
            'Continue optimizing features with upward trends to expand their impact'
        )
    
    @staticmethod
    def format_correlation_insight(correlations: list) -> str:
        """Generate localized correlation insight."""
        correlation_str = ', '.join(correlations[:2])
        return enhanced_t(
            'event_analysis.insights.strong_correlations',
            'Found strongly correlated event pairs: {pairs}',
            pairs=correlation_str
        )
    
    @staticmethod
    def format_correlation_recommendation() -> str:
        """Generate localized correlation recommendation."""
        return enhanced_t(
            'event_analysis.recommendations.leverage_correlations',
            'Leverage event correlations to design user guidance flows'
        )
    
    @staticmethod
    def format_key_events_insight(count: int) -> str:
        """Generate localized key events insight."""
        return enhanced_t(
            'event_analysis.insights.key_events_found',
            'Identified {count} key conversion events',
            count=count
        )
    
    @staticmethod
    def format_key_events_recommendation() -> str:
        """Generate localized key events recommendation."""
        return enhanced_t(
            'event_analysis.recommendations.monitor_key_events',
            'Focus on monitoring and optimizing key conversion event performance'
        )
    
    @staticmethod
    def format_event_reason(reason_key: str) -> str:
        """Generate localized event importance reason."""
        reasons_map = {
            'high_engagement': 'event_analysis.reasons.high_engagement',
            'very_high_engagement': 'event_analysis.reasons.very_high_engagement',
            'high_conversion_impact': 'event_analysis.reasons.high_conversion_impact',
            'moderate_conversion_impact': 'event_analysis.reasons.moderate_conversion_impact',
            'high_retention_impact': 'event_analysis.reasons.high_retention_impact',
            'moderate_retention_impact': 'event_analysis.reasons.moderate_retention_impact',
            'conversion_event': 'event_analysis.reasons.conversion_event',
            'engagement_event': 'event_analysis.reasons.engagement_event',
            'basic_event': 'event_analysis.reasons.basic_event'
        }
        
        key = reasons_map.get(reason_key, 'event_analysis.reasons.basic_event')
        defaults = {
            'event_analysis.reasons.high_engagement': 'High user engagement, important value',
            'event_analysis.reasons.very_high_engagement': 'Extremely high user engagement, core user behavior',
            'event_analysis.reasons.high_conversion_impact': 'Significant positive impact on user conversion',
            'event_analysis.reasons.moderate_conversion_impact': 'Closely related to user conversion behavior',
            'event_analysis.reasons.high_retention_impact': 'Significantly improves user retention rate',
            'event_analysis.reasons.moderate_retention_impact': 'Positive impact on user retention',
            'event_analysis.reasons.conversion_event': 'Core conversion event',
            'event_analysis.reasons.engagement_event': 'Important engagement event',
            'event_analysis.reasons.basic_event': 'Basic user behavior event'
        }
        
        return enhanced_t(key, defaults.get(key, 'Basic user behavior event'))
    
    # Retention analysis specific generators
    @staticmethod
    def format_retention_summary(cohort_count: int, analysis_type: str) -> str:
        """Generate localized retention analysis summary."""
        return enhanced_t(
            'retention.insights.analysis_summary',
            'Completed {analysis_type} retention analysis, containing {cohort_count} cohorts',
            analysis_type=analysis_type,
            cohort_count=cohort_count
        )
    
    @staticmethod
    def format_cohorts_built(cohort_count: int) -> str:
        """Generate localized cohorts built message."""
        return enhanced_t(
            'retention.insights.cohorts_built',
            'Built {cohort_count} user cohorts',
            cohort_count=cohort_count
        )
    
    @staticmethod
    def format_month1_retention_insight(retention_rate: float) -> str:
        """Generate localized month 1 retention insight."""
        return enhanced_t(
            'retention.insights.month1_retention',
            'Month 1 retention rate: {rate}%',
            rate=f"{retention_rate:.1f}"
        )
    
    @staticmethod
    def format_month3_retention_insight(retention_rate: float) -> str:
        """Generate localized month 3 retention insight."""
        return enhanced_t(
            'retention.insights.month3_retention',
            'Month 3 retention rate: {rate}%',
            rate=f"{retention_rate:.1f}"
        )
    
    @staticmethod
    def format_cohorts_analyzed_insight(cohort_count: int) -> str:
        """Generate localized cohorts analyzed insight."""
        return enhanced_t(
            'retention.insights.analyzed_cohorts',
            'Analyzed {count} user cohorts',
            count=cohort_count
        )
    
    @staticmethod
    def format_user_profiles_created(profile_count: int) -> str:
        """Generate localized user profiles created message."""
        return enhanced_t(
            'retention.insights.created_profiles',
            'Created {count} user retention profiles',
            count=profile_count
        )
    
    @staticmethod
    def format_retention_decline_trend() -> str:
        """Generate localized retention decline trend insight."""
        return enhanced_t(
            'retention.insights.gradual_decline',
            'Retention rate decline trend is relatively gradual'
        )
    
    @staticmethod
    def format_retention_fast_decline() -> str:
        """Generate localized retention fast decline insight."""
        return enhanced_t(
            'retention.insights.fast_decline',
            'Retention rate declines rapidly'
        )
    
    @staticmethod
    def format_retention_recommendation(rec_type: str) -> str:
        """Generate localized retention recommendations."""
        rec_map = {
            'low_first_period': 'retention.recommendations.low_first_period',
            'improve_first_period': 'retention.recommendations.improve_first_period',
            'low_long_term': 'retention.recommendations.low_long_term',
            'small_cohort_size': 'retention.recommendations.small_cohort_size',
            'large_variance': 'retention.recommendations.large_variance',
            'good_performance': 'retention.recommendations.good_performance',
            'insufficient_data': 'retention.recommendations.insufficient_data',
            'month1_low': 'retention.recommendations.month1_low',
            'month1_good': 'retention.recommendations.month1_good',
            'month3_low': 'retention.recommendations.month3_low',
            'maintain_strategy': 'retention.recommendations.maintain_strategy',
            'urgent_optimization': 'retention.recommendations.urgent_optimization',
            'sufficient_cohorts': 'retention.recommendations.sufficient_cohorts',
            'insufficient_cohorts': 'retention.recommendations.insufficient_cohorts'
        }
        
        key = rec_map.get(rec_type, 'retention.recommendations.good_performance')
        defaults = {
            'retention.recommendations.low_first_period': 'First period retention rate is too low, recommend optimizing new user onboarding process and first experience',
            'retention.recommendations.improve_first_period': 'First period retention rate needs improvement, recommend strengthening user activation strategy',
            'retention.recommendations.low_long_term': 'Long-term retention rate is low, recommend establishing user loyalty programs',
            'retention.recommendations.small_cohort_size': 'Cohort size is small, recommend increasing user acquisition efforts',
            'retention.recommendations.large_variance': 'Large variance in retention rates between cohorts, recommend analyzing characteristics of high retention cohorts',
            'retention.recommendations.good_performance': 'Retention performance is good, recommend continuing current strategy',
            'retention.recommendations.insufficient_data': 'Insufficient data, recommend collecting more user behavior data',
            'retention.recommendations.month1_low': 'Month 1 retention rate is low, need to improve new user onboarding experience',
            'retention.recommendations.month1_good': 'Month 1 retention rate performs well, can be used as benchmark to optimize other periods',
            'retention.recommendations.month3_low': 'Long-term retention rate needs improvement, consider adding user stickiness features',
            'retention.recommendations.maintain_strategy': 'Maintain current user experience strategy, continue monitoring retention performance',
            'retention.recommendations.urgent_optimization': 'Need urgent optimization of user retention strategy',
            'retention.recommendations.sufficient_cohorts': 'Sufficient cohort data for trend analysis, recommend regular monitoring of cohort performance',
            'retention.recommendations.insufficient_cohorts': 'Limited cohort data, recommend accumulating more data for more accurate retention insights'
        }
        
        return enhanced_t(key, defaults.get(key, 'Continue monitoring retention performance'))
    
    @staticmethod 
    def format_retention_risk(risk_type: str, period: int = None) -> str:
        """Generate localized retention risk messages."""
        if risk_type == 'sharp_decline' and period:
            return enhanced_t(
                'retention.risks.period_sharp_decline',
                'Period {period} retention rate declines sharply',
                period=period
            )
        
        risk_map = {
            'overall_low': 'retention.risks.overall_low',
            'declining_trend': 'retention.risks.declining_trend',
            'no_obvious_risks': 'retention.risks.no_obvious_risks'
        }
        
        key = risk_map.get(risk_type, 'retention.risks.no_obvious_risks')
        defaults = {
            'retention.risks.overall_low': 'Overall retention rate is too low',
            'retention.risks.declining_trend': 'Recent cohort retention rates show declining trend',
            'retention.risks.no_obvious_risks': 'No obvious retention risk factors detected'
        }
        
        return enhanced_t(key, defaults.get(key, 'No obvious retention risk factors detected'))
    
    # User segmentation specific generators
    @staticmethod
    def format_segmentation_summary(segment_count: int, method: str, user_count: int) -> str:
        """Generate localized user segmentation summary."""
        return enhanced_t(
            'user_segmentation.insights.analysis_summary',
            'Completed {method} user segmentation, created {segment_count} segments for {user_count} users',
            method=method,
            segment_count=segment_count,
            user_count=user_count
        )
    
    @staticmethod
    def format_features_extracted(feature_count: int, user_count: int) -> str:
        """Generate localized features extracted message."""
        return enhanced_t(
            'user_segmentation.insights.features_extracted',
            'Extracted {feature_count} features for {user_count} users',
            feature_count=feature_count,
            user_count=user_count
        )
    
    @staticmethod
    def format_segment_profile(segment_name: str, user_count: int, percentage: float) -> str:
        """Generate localized segment profile insight."""
        return enhanced_t(
            'user_segmentation.insights.segment_profile',
            '{segment_name} contains {user_count} users, accounting for {percentage:.1f}% of total users',
            segment_name=segment_name,
            user_count=f"{user_count:,}",
            percentage=percentage
        )
    
    @staticmethod
    def format_high_value_segment_insight(segment_name: str, avg_value: float) -> str:
        """Generate localized high value segment insight."""
        return enhanced_t(
            'user_segmentation.insights.high_value_segment',
            '{segment_name} is a high-value segment with average value of {avg_value:.2f}',
            segment_name=segment_name,
            avg_value=avg_value
        )
    
    @staticmethod
    def format_engagement_insight(segment_name: str, engagement_level: str) -> str:
        """Generate localized engagement level insight."""
        return enhanced_t(
            'user_segmentation.insights.engagement_level',
            '{segment_name} shows {engagement_level} engagement level',
            segment_name=segment_name,
            engagement_level=engagement_level
        )
    
    @staticmethod
    def format_segmentation_recommendation(rec_type: str, segment_name: str = None) -> str:
        """Generate localized segmentation recommendations."""
        rec_map = {
            'good_quality_precision_marketing': 'user_segmentation.recommendations.good_quality_precision_marketing',
            'size_uneven_readjust_clusters': 'user_segmentation.recommendations.size_uneven_readjust_clusters',
            'focus_high_value_retention': 'user_segmentation.recommendations.focus_high_value_retention',
            'small_segment_merge_or_target': 'user_segmentation.recommendations.small_segment_merge_or_target',
            'large_segment_further_subdivide': 'user_segmentation.recommendations.large_segment_further_subdivide',
            'focus_high_value_needs_quality_service': 'user_segmentation.recommendations.focus_high_value_needs_quality_service',
            'improve_low_value_engagement': 'user_segmentation.recommendations.improve_low_value_engagement',
            'good_segmentation_distribution': 'user_segmentation.recommendations.good_segmentation_distribution'
        }
        
        key = rec_map.get(rec_type, 'user_segmentation.recommendations.good_segmentation_distribution')
        defaults = {
            'user_segmentation.recommendations.good_quality_precision_marketing': 'Segmentation quality is good, can be used for precision marketing',
            'user_segmentation.recommendations.size_uneven_readjust_clusters': 'Segment sizes are uneven, recommend readjusting cluster count',
            'user_segmentation.recommendations.focus_high_value_retention': 'Focus on high-value user segments and develop specialized retention strategies',
            'user_segmentation.recommendations.small_segment_merge_or_target': '{segment_name} user group is small, consider merging with other groups or developing targeted marketing strategies',
            'user_segmentation.recommendations.large_segment_further_subdivide': '{segment_name} user group is large, recommend further subdivision for more precise services',
            'user_segmentation.recommendations.focus_high_value_needs_quality_service': 'Focus on high-value user group needs and provide quality services to improve retention',
            'user_segmentation.recommendations.improve_low_value_engagement': 'Improve engagement strategies for low-value segments to increase their value',
            'user_segmentation.recommendations.good_segmentation_distribution': 'Segmentation distribution is balanced and effective'
        }
        
        if segment_name:
            return enhanced_t(key, defaults.get(key, 'Continue monitoring segmentation performance'), segment_name=segment_name)
        else:
            return enhanced_t(key, defaults.get(key, 'Continue monitoring segmentation performance'))
    
    @staticmethod
    def format_clustering_quality_insight(silhouette_score: float) -> str:
        """Generate localized clustering quality insight."""
        return enhanced_t(
            'user_segmentation.insights.clustering_quality',
            'Clustering quality score: {score:.3f}',
            score=silhouette_score
        )
    
    @staticmethod
    def format_optimal_clusters_insight(optimal_k: int) -> str:
        """Generate localized optimal clusters insight."""
        return enhanced_t(
            'user_segmentation.insights.optimal_clusters',
            'Recommended optimal number of clusters: {k}',
            k=optimal_k
        )

# Enhanced translation function for global use
t = enhanced_t

# Export commonly used functions
__all__ = ['enhanced_t', 't', 'LocalizedInsightGenerator', 'localized_logger_message']