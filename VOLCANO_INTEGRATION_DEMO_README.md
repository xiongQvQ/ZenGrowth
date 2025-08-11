# Volcano Integration Demo Scripts

This directory contains demonstration scripts for the Volcano API integration feature, showcasing provider selection, multi-modal analysis, and performance comparison capabilities.

## Demo Scripts

### 1. `demo_volcano_simple.py` - Simple Demo (Recommended)

A lightweight demonstration that works without complex dependencies.

**Features:**
- ✅ Provider selection concepts
- ✅ Text analysis comparison simulation
- ✅ Multi-modal content processing examples
- ✅ Performance comparison metrics
- ✅ Error handling scenarios
- ✅ Works without API keys (simulation mode)

**Usage:**
```bash
python demo_volcano_simple.py
```

**Requirements:**
- Python 3.7+
- No external API keys required for simulation

### 2. `demo_volcano_integration.py` - Full Integration Demo

Comprehensive demonstration with real API calls and advanced features.

**Features:**
- 🔄 Real provider connections and switching
- 🖼️ Actual multi-modal analysis with images
- 📊 Live performance benchmarking
- 🤖 Integration with existing agents
- 📈 Detailed performance metrics and reporting

**Usage:**
```bash
# Set up environment variables
export GOOGLE_API_KEY="your_google_api_key"
export ARK_API_KEY="your_volcano_api_key"

# Run the demo
python demo_volcano_integration.py
```

**Requirements:**
- All project dependencies installed
- Valid API keys for both providers
- Network connectivity to API endpoints

### 3. `test_demo_volcano_integration.py` - Demo Validation

Test script to validate demo functionality.

**Usage:**
```bash
python test_demo_volcano_integration.py
```

## Demo Components

### Provider Selection (Requirement 2.1)

Both demos showcase:
- Dynamic provider selection between Google Gemini and Volcano Doubao
- Configuration management for different providers
- Provider-specific feature capabilities
- Automatic fallback mechanisms

**Example Output:**
```
🔄 Selecting Volcano Provider:
   ✅ Volcano Doubao selected
   📋 Features: Text + Image analysis, multilingual support
   🌐 Endpoint: ARK Beijing (OpenAI-compatible)
```

### Multi-Modal Analysis (Requirements 3.1, 3.2)

Demonstrates processing of mixed text and image content:
- Text + image content preparation
- Provider-specific content formatting
- Multi-modal request creation
- Content validation and error handling

**Example Content:**
```json
[
  {
    "type": "text",
    "text": "Please analyze this user interface for UX improvements:"
  },
  {
    "type": "image_url",
    "image_url": {
      "url": "https://example.com/ui_screenshot.png",
      "detail": "high"
    }
  }
]
```

### Performance Comparison

Both demos include performance analysis:
- Response time measurements
- Success rate tracking
- Quality score estimation
- Provider-specific metrics
- Comparative analysis and recommendations

**Sample Metrics:**
```
📊 Performance Metrics:
   Google:
      Response Time: 1.2s
      Success Rate: 98.0%
      Features: text_analysis, reasoning, code_generation
   
   Volcano:
      Response Time: 0.9s
      Success Rate: 96.0%
      Features: text_analysis, image_analysis, multilingual
```

## Sample Images

The `sample_images/` directory contains placeholder images for multi-modal testing:
- `README.md` - Documentation for sample images
- Placeholder URLs for testing (in demo scripts)
- Instructions for using custom images

## Generated Reports

Demo runs generate JSON reports in the `reports/` directory:
- `simple_volcano_demo_YYYYMMDD_HHMMSS.json` - Simple demo results
- `volcano_integration_demo_report_YYYYMMDD_HHMMSS.json` - Full demo results

**Report Structure:**
```json
{
  "demo_info": {
    "timestamp": "2024-01-15T10:30:00",
    "demo_version": "1.0.0"
  },
  "provider_comparison": {
    "google": { "avg_response_time": 1.2, "success_rate": 0.98 },
    "volcano": { "avg_response_time": 0.9, "success_rate": 0.96 }
  },
  "recommendations": [
    "Use Volcano for multi-modal analysis",
    "Implement fallback mechanism for high availability"
  ]
}
```

## Error Handling Examples

The demos showcase various error scenarios:
- API authentication failures
- Rate limiting and retry logic
- Network connectivity issues
- Unsupported content types
- Graceful degradation strategies

## Getting Started

### Quick Start (No Setup Required)
```bash
# Run the simple demo - works immediately
python demo_volcano_simple.py
```

### Full Setup for Live Testing
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up API keys
export GOOGLE_API_KEY="your_google_api_key"
export ARK_API_KEY="your_volcano_api_key"

# 3. Run full demo
python demo_volcano_integration.py

# 4. Check generated reports
ls reports/volcano_*
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Run the simple demo first: `python demo_volcano_simple.py`
   - Check that all dependencies are installed
   - Verify Python version (3.7+ required)

2. **API Key Issues**
   - Verify environment variables are set correctly
   - Check API key validity and permissions
   - Try the simple demo in simulation mode first

3. **Network Issues**
   - Check internet connectivity
   - Verify firewall settings
   - Try different network if corporate proxy blocks requests

4. **Dependency Issues**
   - Install missing packages: `pip install package_name`
   - Use virtual environment to avoid conflicts
   - Check requirements.txt for version compatibility

### Support

For issues with the demo scripts:
1. Check the console output for specific error messages
2. Review the generated log files in `logs/`
3. Run the test script: `python test_demo_volcano_integration.py`
4. Try the simple demo first to isolate issues

## Integration with Existing System

After running the demos successfully:
1. Review the generated reports for performance insights
2. Update your `.env` file with preferred provider settings
3. Integrate multi-modal capabilities into existing agents
4. Implement fallback mechanisms based on demo examples
5. Monitor performance in production using similar metrics

## Demo Validation

The demos fulfill the following task requirements:
- ✅ **Requirement 2.1**: Provider selection demonstration
- ✅ **Requirement 3.1**: Multi-modal analysis examples
- ✅ **Requirement 3.2**: Sample image processing
- ✅ **Performance comparison**: Between Google and Volcano providers
- ✅ **Error handling**: Comprehensive fallback scenarios
- ✅ **Documentation**: Complete usage instructions and examples