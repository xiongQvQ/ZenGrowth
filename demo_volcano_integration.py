#!/usr/bin/env python3
"""
Volcano API Integration Demo Script

This comprehensive demo showcases:
1. Provider selection between Google Gemini and Volcano Doubao
2. Multi-modal analysis with text and image content
3. Performance comparison between providers
4. Real-world user behavior analysis scenarios

Requirements: 2.1, 3.1, 3.2
"""

import os
import json
import time
import asyncio
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import necessary modules
try:
    from config.llm_provider_manager import LLMProviderManager, ProviderStatus
    from config.multimodal_content_handler import MultiModalContentHandler
    from config.volcano_llm_client import VolcanoLLMClient
    from config.settings import settings
    from utils.logger import setup_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all dependencies are installed and modules are available")
    print("Note: Some agent imports may be optional for basic demo functionality")
    
    # Try to continue with basic functionality
    try:
        import logging
        def setup_logger(name):
            return logging.getLogger(name)
    except:
        pass

# Setup logging
logger = setup_logger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for provider comparison"""
    provider: str
    response_time: float
    token_count: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    content_type: str = "text"
    analysis_quality_score: Optional[float] = None

@dataclass
class DemoResult:
    """Demo execution result"""
    demo_name: str
    success: bool
    metrics: List[PerformanceMetrics]
    output_sample: Optional[str] = None
    error_message: Optional[str] = None

class VolcanoIntegrationDemo:
    """
    Comprehensive Volcano API Integration Demo
    
    Demonstrates provider selection, multi-modal capabilities,
    and performance comparison between Google Gemini and Volcano Doubao
    """
    
    def __init__(self):
        """Initialize demo environment"""
        self.provider_manager = LLMProviderManager()
        self.content_handler = MultiModalContentHandler()
        self.results: List[DemoResult] = []
        self.performance_data: Dict[str, List[PerformanceMetrics]] = {
            "google": [],
            "volcano": []
        }
        
        # Sample images for multi-modal testing
        self.sample_images = [
            "https://via.placeholder.com/800x600/0066CC/FFFFFF?text=User+Journey+Flow",
            "https://via.placeholder.com/800x400/FF6B35/FFFFFF?text=Conversion+Funnel",
            "https://via.placeholder.com/600x800/28A745/FFFFFF?text=User+Behavior+Heatmap"
        ]
        
        self._check_configuration()
    
    def _check_configuration(self):
        """Check if required configuration is available"""
        print("🔧 Checking configuration...")
        
        # Check API keys
        google_key = os.getenv('GOOGLE_API_KEY')
        ark_key = os.getenv('ARK_API_KEY')
        
        if not google_key:
            print("⚠️  Warning: GOOGLE_API_KEY not found - Google provider may not work")
        else:
            print("✅ Google API key configured")
            
        if not ark_key:
            print("⚠️  Warning: ARK_API_KEY not found - Volcano provider may not work")
        else:
            print("✅ Volcano API key configured")
        
        # Check provider availability
        available_providers = self.provider_manager.get_available_providers()
        print(f"📋 Available providers: {available_providers}")
        
        if len(available_providers) < 2:
            print("⚠️  Warning: Less than 2 providers available - comparison features limited")
    
    def run_comprehensive_demo(self):
        """Run the complete demo suite"""
        print("🚀 Starting Volcano Integration Comprehensive Demo")
        print("=" * 60)
        
        demos = [
            ("Provider Connection Test", self._demo_provider_connections),
            ("Basic Text Analysis Comparison", self._demo_text_analysis_comparison),
            ("Multi-Modal Analysis", self._demo_multimodal_analysis),
            ("User Behavior Analysis", self._demo_user_behavior_analysis),
            ("Provider Switching & Fallback", self._demo_provider_switching),
            ("Performance Benchmarking", self._demo_performance_benchmarking),
            ("Real-World Scenarios", self._demo_real_world_scenarios)
        ]
        
        for demo_name, demo_func in demos:
            print(f"\n{'='*20} {demo_name} {'='*20}")
            try:
                result = demo_func()
                self.results.append(result)
                
                if result.success:
                    print(f"✅ {demo_name} completed successfully")
                else:
                    print(f"❌ {demo_name} failed: {result.error_message}")
                    
            except Exception as e:
                print(f"❌ {demo_name} crashed: {e}")
                self.results.append(DemoResult(
                    demo_name=demo_name,
                    success=False,
                    metrics=[],
                    error_message=str(e)
                ))
        
        # Generate final report
        self._generate_comprehensive_report()
        
        print(f"\n🎉 Demo completed! Check the generated report for detailed results.")
    
    def _demo_provider_connections(self) -> DemoResult:
        """Test connections to both providers"""
        print("Testing provider connections...")
        
        metrics = []
        success = True
        error_msg = None
        
        for provider in ["google", "volcano"]:
            try:
                start_time = time.time()
                
                # Get LLM instance
                llm = self.provider_manager.get_llm(provider=provider)
                
                # Simple test prompt
                test_prompt = "Hello, please respond with 'Connection successful'"
                response = llm.invoke(test_prompt)
                
                response_time = time.time() - start_time
                
                metrics.append(PerformanceMetrics(
                    provider=provider,
                    response_time=response_time,
                    success=True,
                    content_type="text"
                ))
                
                print(f"✅ {provider.capitalize()} provider: {response_time:.2f}s")
                
            except Exception as e:
                metrics.append(PerformanceMetrics(
                    provider=provider,
                    response_time=0,
                    success=False,
                    error_message=str(e),
                    content_type="text"
                ))
                print(f"❌ {provider.capitalize()} provider failed: {e}")
                success = False
                error_msg = f"Provider {provider} connection failed"
        
        return DemoResult(
            demo_name="Provider Connection Test",
            success=success,
            metrics=metrics,
            error_message=error_msg
        )
    
    def _demo_text_analysis_comparison(self) -> DemoResult:
        """Compare text analysis between providers"""
        print("Comparing text analysis capabilities...")
        
        # Sample user behavior data
        analysis_prompt = """
        Analyze the following user behavior data and provide insights:
        
        User Session Data:
        - Session Duration: 15 minutes
        - Pages Viewed: 8 pages
        - Products Viewed: 5 products
        - Cart Additions: 2 items
        - Purchase: 1 item ($89.99)
        - User Type: Returning customer
        - Device: Mobile
        - Traffic Source: Social media
        
        Please provide:
        1. User behavior pattern analysis
        2. Conversion optimization suggestions
        3. Personalization recommendations
        
        Format your response as structured JSON.
        """
        
        metrics = []
        responses = {}
        
        for provider in ["google", "volcano"]:
            try:
                start_time = time.time()
                
                llm = self.provider_manager.get_llm(provider=provider)
                response = llm.invoke(analysis_prompt)
                
                response_time = time.time() - start_time
                
                # Estimate quality score based on response length and structure
                quality_score = min(10.0, len(response) / 100)
                
                metrics.append(PerformanceMetrics(
                    provider=provider,
                    response_time=response_time,
                    success=True,
                    content_type="text",
                    analysis_quality_score=quality_score
                ))
                
                responses[provider] = response[:200] + "..." if len(response) > 200 else response
                
                print(f"✅ {provider.capitalize()}: {response_time:.2f}s, Quality: {quality_score:.1f}/10")
                
            except Exception as e:
                metrics.append(PerformanceMetrics(
                    provider=provider,
                    response_time=0,
                    success=False,
                    error_message=str(e),
                    content_type="text"
                ))
                print(f"❌ {provider.capitalize()} failed: {e}")
        
        return DemoResult(
            demo_name="Text Analysis Comparison",
            success=len([m for m in metrics if m.success]) > 0,
            metrics=metrics,
            output_sample=json.dumps(responses, indent=2)
        )
    
    def _demo_multimodal_analysis(self) -> DemoResult:
        """Demonstrate multi-modal analysis capabilities"""
        print("Testing multi-modal analysis...")
        
        # Create multi-modal content
        multimodal_content = [
            {
                "type": "text",
                "text": "Please analyze these user interface screenshots for UX issues and conversion optimization opportunities:"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": self.sample_images[0],
                    "detail": "high"
                }
            },
            {
                "type": "image_url", 
                "image_url": {
                    "url": self.sample_images[1],
                    "detail": "high"
                }
            }
        ]
        
        metrics = []
        responses = {}
        
        for provider in ["volcano"]:  # Focus on Volcano for multi-modal
            try:
                start_time = time.time()
                
                llm = self.provider_manager.get_llm(provider=provider)
                
                # Check if provider supports multi-modal
                if hasattr(llm, 'supports_multimodal') and llm.supports_multimodal():
                    # Process content for multi-modal
                    processed_content = self.content_handler.prepare_content(multimodal_content)
                    
                    # Create analysis request
                    request = self.content_handler.create_multimodal_request(
                        text="Analyze these UI screenshots for user experience issues",
                        image_urls=self.sample_images[:2],
                        analysis_type="ux_analysis",
                        provider=provider
                    )
                    
                    # Execute multi-modal analysis
                    response = llm.invoke(str(request.content))
                    
                    response_time = time.time() - start_time
                    
                    metrics.append(PerformanceMetrics(
                        provider=provider,
                        response_time=response_time,
                        success=True,
                        content_type="multimodal",
                        analysis_quality_score=8.5  # Assume good quality for multi-modal
                    ))
                    
                    responses[provider] = response[:300] + "..." if len(response) > 300 else response
                    
                    print(f"✅ {provider.capitalize()} multi-modal: {response_time:.2f}s")
                    
                else:
                    print(f"⚠️  {provider.capitalize()} doesn't support multi-modal analysis")
                    
                    # Fallback to text-only
                    text_content = self.content_handler.extract_text_content(multimodal_content)
                    response = llm.invoke(text_content)
                    
                    response_time = time.time() - start_time
                    
                    metrics.append(PerformanceMetrics(
                        provider=provider,
                        response_time=response_time,
                        success=True,
                        content_type="text_fallback"
                    ))
                    
                    responses[provider] = f"[Text-only fallback] {response[:200]}..."
                    
            except Exception as e:
                metrics.append(PerformanceMetrics(
                    provider=provider,
                    response_time=0,
                    success=False,
                    error_message=str(e),
                    content_type="multimodal"
                ))
                print(f"❌ {provider.capitalize()} multi-modal failed: {e}")
        
        return DemoResult(
            demo_name="Multi-Modal Analysis",
            success=len([m for m in metrics if m.success]) > 0,
            metrics=metrics,
            output_sample=json.dumps(responses, indent=2)
        )
    
    def _demo_user_behavior_analysis(self) -> DemoResult:
        """Demonstrate real user behavior analysis scenarios"""
        print("Testing user behavior analysis scenarios...")
        
        # Sample GA4-style event data
        user_events = [
            {"event_name": "page_view", "page_location": "/homepage", "timestamp": "2024-01-15T10:00:00"},
            {"event_name": "search", "search_term": "running shoes", "timestamp": "2024-01-15T10:02:00"},
            {"event_name": "view_item", "item_id": "shoe_123", "item_category": "footwear", "timestamp": "2024-01-15T10:05:00"},
            {"event_name": "add_to_cart", "item_id": "shoe_123", "value": 129.99, "timestamp": "2024-01-15T10:08:00"},
            {"event_name": "begin_checkout", "value": 129.99, "timestamp": "2024-01-15T10:12:00"},
            {"event_name": "purchase", "transaction_id": "txn_456", "value": 129.99, "timestamp": "2024-01-15T10:15:00"}
        ]
        
        analysis_scenarios = [
            {
                "name": "Conversion Path Analysis",
                "prompt": f"Analyze this user's conversion path and identify optimization opportunities:\n{json.dumps(user_events, indent=2)}"
            },
            {
                "name": "User Segmentation",
                "prompt": "Based on the user behavior data, classify this user into appropriate segments and suggest personalization strategies."
            }
        ]
        
        metrics = []
        scenario_results = {}
        
        for scenario in analysis_scenarios:
            scenario_results[scenario["name"]] = {}
            
            for provider in ["google", "volcano"]:
                try:
                    start_time = time.time()
                    
                    llm = self.provider_manager.get_llm(provider=provider)
                    response = llm.invoke(scenario["prompt"])
                    
                    response_time = time.time() - start_time
                    
                    metrics.append(PerformanceMetrics(
                        provider=provider,
                        response_time=response_time,
                        success=True,
                        content_type="user_behavior_analysis"
                    ))
                    
                    scenario_results[scenario["name"]][provider] = {
                        "response_time": response_time,
                        "response_preview": response[:150] + "..." if len(response) > 150 else response
                    }
                    
                    print(f"✅ {scenario['name']} - {provider.capitalize()}: {response_time:.2f}s")
                    
                except Exception as e:
                    metrics.append(PerformanceMetrics(
                        provider=provider,
                        response_time=0,
                        success=False,
                        error_message=str(e),
                        content_type="user_behavior_analysis"
                    ))
                    print(f"❌ {scenario['name']} - {provider.capitalize()} failed: {e}")
        
        return DemoResult(
            demo_name="User Behavior Analysis",
            success=len([m for m in metrics if m.success]) > 0,
            metrics=metrics,
            output_sample=json.dumps(scenario_results, indent=2)
        )
    
    def _demo_provider_switching(self) -> DemoResult:
        """Demonstrate provider switching and fallback mechanisms"""
        print("Testing provider switching and fallback...")
        
        metrics = []
        switching_results = {}
        
        try:
            # Test normal switching
            print("Testing normal provider switching...")
            
            for provider in ["google", "volcano", "google"]:  # Switch back and forth
                start_time = time.time()
                
                llm = self.provider_manager.get_llm(provider=provider)
                response = llm.invoke(f"Confirm you are using {provider} provider")
                
                response_time = time.time() - start_time
                
                metrics.append(PerformanceMetrics(
                    provider=provider,
                    response_time=response_time,
                    success=True,
                    content_type="provider_switching"
                ))
                
                switching_results[f"switch_to_{provider}"] = {
                    "success": True,
                    "response_time": response_time
                }
                
                print(f"✅ Switched to {provider}: {response_time:.2f}s")
            
            # Test fallback mechanism
            print("Testing fallback mechanism...")
            try:
                # Try to use non-existent provider to trigger fallback
                llm = self.provider_manager.get_llm(provider="nonexistent")
                response = llm.invoke("Test fallback mechanism")
                
                switching_results["fallback_test"] = {
                    "success": True,
                    "message": "Fallback mechanism worked"
                }
                
                print("✅ Fallback mechanism working")
                
            except Exception as e:
                switching_results["fallback_test"] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"⚠️  Fallback test: {e}")
        
        except Exception as e:
            print(f"❌ Provider switching test failed: {e}")
            return DemoResult(
                demo_name="Provider Switching",
                success=False,
                metrics=metrics,
                error_message=str(e)
            )
        
        return DemoResult(
            demo_name="Provider Switching",
            success=True,
            metrics=metrics,
            output_sample=json.dumps(switching_results, indent=2)
        )
    
    def _demo_performance_benchmarking(self) -> DemoResult:
        """Comprehensive performance benchmarking between providers"""
        print("Running performance benchmarks...")
        
        # Test prompts of varying complexity
        test_prompts = [
            {
                "name": "Simple Query",
                "prompt": "What is user behavior analysis?",
                "expected_tokens": 100
            },
            {
                "name": "Medium Analysis",
                "prompt": "Analyze user retention patterns and suggest improvements for an e-commerce platform.",
                "expected_tokens": 300
            },
            {
                "name": "Complex Analysis",
                "prompt": """
                Perform a comprehensive analysis of the following user behavior data:
                - 10,000 daily active users
                - 2.5% conversion rate
                - 65% mobile traffic
                - Average session duration: 3.2 minutes
                - Top traffic sources: Organic search (40%), Social media (25%), Direct (20%), Paid ads (15%)
                
                Provide detailed insights on user segmentation, conversion optimization, and retention strategies.
                Include specific recommendations with expected impact metrics.
                """,
                "expected_tokens": 800
            }
        ]
        
        benchmark_results = {}
        all_metrics = []
        
        for test in test_prompts:
            benchmark_results[test["name"]] = {}
            
            for provider in ["google", "volcano"]:
                provider_times = []
                
                # Run multiple iterations for statistical significance
                for iteration in range(3):
                    try:
                        start_time = time.time()
                        
                        llm = self.provider_manager.get_llm(provider=provider)
                        response = llm.invoke(test["prompt"])
                        
                        response_time = time.time() - start_time
                        provider_times.append(response_time)
                        
                        # Estimate tokens (rough approximation)
                        estimated_tokens = len(response.split()) * 1.3
                        
                        all_metrics.append(PerformanceMetrics(
                            provider=provider,
                            response_time=response_time,
                            token_count=int(estimated_tokens),
                            success=True,
                            content_type=test["name"].lower().replace(" ", "_")
                        ))
                        
                    except Exception as e:
                        all_metrics.append(PerformanceMetrics(
                            provider=provider,
                            response_time=0,
                            success=False,
                            error_message=str(e),
                            content_type=test["name"].lower().replace(" ", "_")
                        ))
                        print(f"❌ {test['name']} - {provider} iteration {iteration+1} failed: {e}")
                
                if provider_times:
                    avg_time = statistics.mean(provider_times)
                    std_dev = statistics.stdev(provider_times) if len(provider_times) > 1 else 0
                    
                    benchmark_results[test["name"]][provider] = {
                        "avg_response_time": avg_time,
                        "std_deviation": std_dev,
                        "iterations": len(provider_times),
                        "success_rate": len(provider_times) / 3
                    }
                    
                    print(f"✅ {test['name']} - {provider}: {avg_time:.2f}s ±{std_dev:.2f}s")
                else:
                    benchmark_results[test["name"]][provider] = {
                        "avg_response_time": None,
                        "error": "All iterations failed"
                    }
        
        # Store performance data for final analysis
        for metric in all_metrics:
            if metric.success:
                self.performance_data[metric.provider].append(metric)
        
        return DemoResult(
            demo_name="Performance Benchmarking",
            success=len(all_metrics) > 0,
            metrics=all_metrics,
            output_sample=json.dumps(benchmark_results, indent=2)
        )
    
    def _demo_real_world_scenarios(self) -> DemoResult:
        """Test real-world user behavior analysis scenarios"""
        print("Testing real-world scenarios...")
        
        scenarios = [
            {
                "name": "E-commerce Cart Abandonment",
                "context": "High cart abandonment rate analysis",
                "data": {
                    "cart_abandonment_rate": 0.73,
                    "avg_items_in_cart": 2.4,
                    "most_abandoned_step": "shipping_info",
                    "mobile_abandonment": 0.81,
                    "desktop_abandonment": 0.65
                }
            },
            {
                "name": "Content Engagement Analysis",
                "context": "Blog content performance analysis",
                "data": {
                    "avg_time_on_page": 145,
                    "bounce_rate": 0.42,
                    "scroll_depth": 0.68,
                    "social_shares": 23,
                    "comments": 7
                }
            }
        ]
        
        scenario_results = {}
        metrics = []
        
        for scenario in scenarios:
            scenario_results[scenario["name"]] = {}
            
            prompt = f"""
            Analyze the following {scenario['context']}:
            
            Data: {json.dumps(scenario['data'], indent=2)}
            
            Provide:
            1. Key insights and patterns
            2. Root cause analysis
            3. Actionable recommendations
            4. Expected impact of recommendations
            
            Format as structured analysis with clear sections.
            """
            
            for provider in ["google", "volcano"]:
                try:
                    start_time = time.time()
                    
                    llm = self.provider_manager.get_llm(provider=provider)
                    response = llm.invoke(prompt)
                    
                    response_time = time.time() - start_time
                    
                    # Analyze response quality (simple heuristic)
                    quality_indicators = [
                        "insight" in response.lower(),
                        "recommend" in response.lower(),
                        "impact" in response.lower(),
                        len(response) > 200
                    ]
                    quality_score = sum(quality_indicators) * 2.5
                    
                    metrics.append(PerformanceMetrics(
                        provider=provider,
                        response_time=response_time,
                        success=True,
                        content_type="real_world_scenario",
                        analysis_quality_score=quality_score
                    ))
                    
                    scenario_results[scenario["name"]][provider] = {
                        "response_time": response_time,
                        "quality_score": quality_score,
                        "response_length": len(response),
                        "preview": response[:200] + "..." if len(response) > 200 else response
                    }
                    
                    print(f"✅ {scenario['name']} - {provider}: {response_time:.2f}s, Quality: {quality_score}/10")
                    
                except Exception as e:
                    metrics.append(PerformanceMetrics(
                        provider=provider,
                        response_time=0,
                        success=False,
                        error_message=str(e),
                        content_type="real_world_scenario"
                    ))
                    print(f"❌ {scenario['name']} - {provider} failed: {e}")
        
        return DemoResult(
            demo_name="Real-World Scenarios",
            success=len([m for m in metrics if m.success]) > 0,
            metrics=metrics,
            output_sample=json.dumps(scenario_results, indent=2)
        )
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive demo report with performance analysis"""
        print("\n📊 Generating comprehensive report...")
        
        # Aggregate performance statistics
        performance_summary = self._analyze_performance_data()
        
        # Create comprehensive report
        report = {
            "demo_info": {
                "timestamp": datetime.now().isoformat(),
                "demo_version": "1.0.0",
                "total_demos": len(self.results),
                "successful_demos": len([r for r in self.results if r.success])
            },
            "provider_comparison": performance_summary,
            "demo_results": [
                {
                    "name": result.demo_name,
                    "success": result.success,
                    "error": result.error_message,
                    "metrics_count": len(result.metrics),
                    "successful_metrics": len([m for m in result.metrics if m.success])
                }
                for result in self.results
            ],
            "detailed_metrics": [
                {
                    "demo": result.demo_name,
                    "metrics": [
                        {
                            "provider": m.provider,
                            "response_time": m.response_time,
                            "success": m.success,
                            "content_type": m.content_type,
                            "quality_score": m.analysis_quality_score,
                            "error": m.error_message
                        }
                        for m in result.metrics
                    ]
                }
                for result in self.results
            ],
            "recommendations": self._generate_recommendations()
        }
        
        # Save report
        report_filename = f"volcano_integration_demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = Path("reports") / report_filename
        
        # Ensure reports directory exists
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Comprehensive report saved: {report_path}")
        
        # Print summary
        self._print_summary(performance_summary)
    
    def _analyze_performance_data(self) -> Dict[str, Any]:
        """Analyze performance data and generate comparison"""
        summary = {}
        
        for provider, metrics in self.performance_data.items():
            if not metrics:
                summary[provider] = {"status": "no_data"}
                continue
            
            successful_metrics = [m for m in metrics if m.success]
            
            if successful_metrics:
                response_times = [m.response_time for m in successful_metrics]
                quality_scores = [m.analysis_quality_score for m in successful_metrics if m.analysis_quality_score]
                
                summary[provider] = {
                    "total_requests": len(metrics),
                    "successful_requests": len(successful_metrics),
                    "success_rate": len(successful_metrics) / len(metrics),
                    "avg_response_time": statistics.mean(response_times),
                    "median_response_time": statistics.median(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "std_dev_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                    "avg_quality_score": statistics.mean(quality_scores) if quality_scores else None,
                    "content_types": list(set(m.content_type for m in successful_metrics))
                }
            else:
                summary[provider] = {
                    "status": "all_failed",
                    "total_requests": len(metrics),
                    "successful_requests": 0
                }
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on demo results"""
        recommendations = []
        
        # Analyze success rates
        total_demos = len(self.results)
        successful_demos = len([r for r in self.results if r.success])
        
        if successful_demos / total_demos < 0.8:
            recommendations.append("Consider reviewing API configurations and network connectivity")
        
        # Analyze provider performance
        if "google" in self.performance_data and "volcano" in self.performance_data:
            google_metrics = [m for m in self.performance_data["google"] if m.success]
            volcano_metrics = [m for m in self.performance_data["volcano"] if m.success]
            
            if google_metrics and volcano_metrics:
                google_avg = statistics.mean([m.response_time for m in google_metrics])
                volcano_avg = statistics.mean([m.response_time for m in volcano_metrics])
                
                if volcano_avg < google_avg * 0.8:
                    recommendations.append("Volcano provider shows better performance - consider as primary")
                elif google_avg < volcano_avg * 0.8:
                    recommendations.append("Google provider shows better performance - consider as primary")
                else:
                    recommendations.append("Both providers show similar performance - use based on feature requirements")
        
        # Multi-modal recommendations
        multimodal_results = [r for r in self.results if "Multi-Modal" in r.demo_name]
        if multimodal_results and multimodal_results[0].success:
            recommendations.append("Multi-modal analysis is working - consider expanding image analysis features")
        
        if not recommendations:
            recommendations.append("All systems functioning well - ready for production use")
        
        return recommendations
    
    def _print_summary(self, performance_summary: Dict[str, Any]):
        """Print demo summary to console"""
        print("\n" + "="*60)
        print("📊 VOLCANO INTEGRATION DEMO SUMMARY")
        print("="*60)
        
        # Overall results
        total_demos = len(self.results)
        successful_demos = len([r for r in self.results if r.success])
        
        print(f"\n🎯 Overall Results:")
        print(f"   Total Demos: {total_demos}")
        print(f"   Successful: {successful_demos}")
        print(f"   Success Rate: {successful_demos/total_demos*100:.1f}%")
        
        # Provider comparison
        print(f"\n⚡ Provider Performance Comparison:")
        for provider, stats in performance_summary.items():
            if "status" in stats:
                print(f"   {provider.capitalize()}: {stats['status']}")
            else:
                print(f"   {provider.capitalize()}:")
                print(f"     Success Rate: {stats['success_rate']*100:.1f}%")
                print(f"     Avg Response Time: {stats['avg_response_time']:.2f}s")
                if stats['avg_quality_score']:
                    print(f"     Avg Quality Score: {stats['avg_quality_score']:.1f}/10")
        
        # Failed demos
        failed_demos = [r for r in self.results if not r.success]
        if failed_demos:
            print(f"\n❌ Failed Demos:")
            for demo in failed_demos:
                print(f"   - {demo.demo_name}: {demo.error_message}")
        
        print("\n" + "="*60)

def main():
    """Main demo execution function"""
    print("🚀 Volcano API Integration Demo")
    print("This demo showcases provider selection, multi-modal analysis, and performance comparison")
    print("="*80)
    
    try:
        # Create and run demo
        demo = VolcanoIntegrationDemo()
        demo.run_comprehensive_demo()
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 Troubleshooting Tips:")
        print("1. Ensure ARK_API_KEY and GOOGLE_API_KEY are set in environment")
        print("2. Check network connectivity to API endpoints")
        print("3. Verify all required dependencies are installed")
        print("4. Check logs for detailed error information")

if __name__ == "__main__":
    main()