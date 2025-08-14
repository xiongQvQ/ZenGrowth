# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a User Behavior Analytics Platform (用户行为分析智能体平台) - a multi-agent AI system built with CrewAI for analyzing Google Analytics 4 (GA4) data. It features a Streamlit web interface, 7 specialized AI agents, and supports both Google Gemini and Volcano ARK LLM providers.

## Development Commands

### Local Development
```bash
# Quick start (bypass complex setup)
python start_app_direct.py

# Manual start
streamlit run main.py

# Start with specific port
streamlit run main.py --server.port 8502

# Generate test data
python generate_clean_data.py

# Environment setup
python setup.py
```

### Docker Development
```bash
# Development environment (recommended)
./deploy.sh -e development -a up -b
# OR
docker-compose -f docker-compose.dev.yml up --build

# Production environment
./deploy.sh -e production -a up -d
# OR
docker-compose up -d

# View logs
./deploy.sh -e development -a logs -f
docker-compose logs -f

# Stop services
./deploy.sh -e development -a down
docker-compose down

# Build Docker image
./docker-build.sh [tag]
```

### Testing
```bash
# Core functionality tests
python test_minimal_integration.py
python test_visualization_only.py
python test_integration_manager_simple.py

# Individual component tests
python test_simple_llm.py
python test_fallback_simple.py
python test_data_cleaner_simple.py

# Agent-specific tests
python test_event_analysis_agent_standalone.py
python test_conversion_analysis_agent_standalone.py

# Comprehensive test suite
python test_data_quality_validation.py
```

### Health Checks & Diagnostics
```bash
# Basic system diagnostics
python diagnose.py

# Environment debugging
python debug_env.py
python debug_providers.py

# Configuration validation
python container_config_manager.py
python config_validator.py

# Health endpoint (when running)
curl http://localhost:8502/health
curl http://localhost:8502/health/detailed
```

## Architecture Overview

### Multi-Agent System
The platform uses CrewAI framework with 7 specialized agents:
- **DataProcessingAgent**: GA4 data parsing and preprocessing
- **EventAnalysisAgent**: User event patterns and trend analysis
- **RetentionAnalysisAgent**: User retention and churn analysis  
- **ConversionAnalysisAgent**: Funnel analysis and bottleneck identification
- **UserSegmentationAgent**: Behavioral clustering and profiling
- **PathAnalysisAgent**: User journey and navigation patterns
- **ReportGenerationAgent**: Comprehensive report compilation

### Core Components
- **main.py**: Streamlit application entry point with UI and workflow orchestration
- **system/integration_manager.py**: Central orchestrator managing all agents and engines
- **engines/**: Analysis engines for different analytics tasks (event, retention, conversion, etc.)
- **tools/**: Data processing utilities (GA4 parser, validators, storage manager)
- **config/**: Configuration management, LLM providers, and settings
- **visualization/**: Chart generation and advanced plotting components

### Data Flow
1. GA4 NDJSON files uploaded via Streamlit UI
2. `GA4DataParser` processes and validates event data
3. `DataStorageManager` manages in-memory storage
4. `IntegrationManager` orchestrates analysis workflow
5. Agents/Engines perform specialized analysis
6. Results displayed via `ChartGenerator`/`AdvancedVisualizer`
7. Reports exported via `ReportExporter`

### LLM Integration
- Dual provider support: Google Gemini + Volcano ARK
- Fallback mechanism with configurable order
- Provider health monitoring and circuit breaker pattern
- Multimodal content support for image analysis

## Configuration System

### Environment Variables (.env)
```bash
# Required (at least one)
GOOGLE_API_KEY=your_google_api_key
ARK_API_KEY=your_volcano_api_key

# LLM Configuration
DEFAULT_LLM_PROVIDER=volcano|google
ENABLED_PROVIDERS=["volcano", "google"]
FALLBACK_ORDER=["volcano", "google"]

# Application Settings
APP_TITLE=用户行为分析智能体平台
LOG_LEVEL=INFO|DEBUG|WARN|ERROR
STREAMLIT_SERVER_PORT=8501
```

### Configuration Files
- **config/system_config.json**: Main system configuration
- **config/analysis_config.json**: Analysis parameters
- **config/settings.py**: Pydantic settings with validation

### Language Settings Issue
**Known Issue**: Language setting (en-US vs zh-CN) in UI settings doesn't take effect properly.

**Root Cause**: 
- Language selection saved to `config/system_config.json` at `ui_settings.language`
- UI calls `st.rerun()` after saving but localization isn't implemented
- Interface remains Chinese regardless of en-US selection

**Location**: `main.py:809-884` (language selectbox and save logic)

**Fix Needed**: Implement proper i18n/localization system that reads `ui_settings.language` and applies appropriate language strings throughout the interface.

## Development Patterns

### Agent Development
- Agents have both integrated (`agents/`) and standalone (`agents/*_standalone.py`) versions
- Use `AGENTS_AVAILABLE` flag in `integration_manager.py` for fallback to engines
- Each agent follows CrewAI Task/Agent pattern with role, goal, and backstory

### Error Handling
- Comprehensive try/catch blocks with logging
- Graceful degradation when components fail
- Circuit breaker pattern for LLM providers
- Fallback mechanisms throughout the stack

### State Management
- Streamlit session state for UI data persistence
- `DataStorageManager` for in-memory data storage
- Configuration persistence via JSON files
- No database - file-based storage only

### Testing Approach
- Standalone test scripts (no pytest framework)
- Component-level and integration tests
- Mock data generation for testing
- Health check validation

## Key Files to Understand

- **main.py** (2500+ lines): Main Streamlit application with all UI logic
- **system/integration_manager.py**: Central orchestration and workflow management
- **config/llm_provider_manager.py**: LLM provider abstraction and fallback logic
- **config/settings.py**: Configuration validation and environment variable handling
- **tools/ga4_data_parser.py**: GA4 NDJSON parsing and event extraction
- **visualization/chart_generator.py**: Core plotting and visualization logic

## Performance Considerations

- In-memory data processing with pandas DataFrames
- Thread pool executors for parallel processing
- Memory monitoring with psutil
- Chunked data processing for large files
- LLM response caching to reduce API costs

## Deployment Notes

- Docker Compose setup with development/production profiles
- Health monitoring endpoints
- Volume mounts for development hot-reload
- Kubernetes security policies in `security/`
- Comprehensive logging to `logs/` directory