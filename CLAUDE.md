# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **User Behavior Analytics Platform** (用户行为分析智能体平台) - a sophisticated multi-agent AI system built with CrewAI for analyzing Google Analytics 4 (GA4) data. It features a comprehensive Streamlit web interface, 7 specialized AI agents, and supports both Google Gemini and Volcano ARK LLM providers with failover capabilities.

## Architecture & Design Patterns

### Core Architecture
- **Frontend**: Streamlit-based web interface with modular UI components (`ui/`, `pages/`)
- **Orchestration**: `IntegrationManager` in `system/` provides centralized workflow coordination
- **Agents**: 7 specialized CrewAI agents (`agents/`) with standalone fallback implementations
- **Engines**: Simplified analysis engines (`engines/`) as fallback when agents unavailable
- **Data Processing**: File-based with pandas DataFrames, no database dependency
- **LLM Integration**: Dual provider support (Google Gemini + Volcano ARK) with circuit breaker pattern

### Key Design Decisions
- **Agent vs Engine Duality**: System maintains both CrewAI agents and simplified engines for resilience
- **Memory Model**: In-memory pandas processing for development, scalable to DuckDB for production
- **Configuration**: JSON-based configs with Pydantic validation, environment variable override
- **Testing**: Standalone test scripts (no pytest) for rapid iteration and CI integration

## Development Workflow

### Quick Start Commands
```bash
# Development (recommended)
./deploy.sh -e development -a up -b

# Production deployment
./deploy.sh -e production -a up -d

# Local development
python start_app_direct.py

# Specific port
streamlit run main.py --server.port 8502
```

### Environment Setup
```bash
# Create environment
python setup.py

# Configure API keys in .env
GOOGLE_API_KEY=your_key
ARK_API_KEY=your_volcano_key
```

### Development Patterns

#### Adding New Analysis Features
1. **Agent Path** (preferred): Create agent in `agents/` with role/goal/backstory
2. **Engine Path**: Create engine in `engines/` for simplified fallback
3. **Integration**: Update `IntegrationManager` to include new analysis type
4. **UI**: Add page in `ui/pages/` and update navigation

#### Testing Strategy
```bash
# Unit tests for individual components
python test_data_cleaner_simple.py
python test_simple_llm.py

# Integration tests
python test_integration_manager_simple.py
python test_minimal_integration.py

# Agent-specific tests
python test_event_analysis_agent_standalone.py
python test_conversion_analysis_agent_standalone.py

# Comprehensive validation
python test_data_quality_validation.py
```

#### Debugging & Diagnostics
```bash
# Health checks
curl http://localhost:8502/health
curl http://localhost:8502/health/detailed

# Environment diagnostics
python debug_env.py
python debug_providers.py

# Configuration validation
python container_config_manager.py
python config_validator.py
```

## Key Development Areas

### 1. Agent Development
**Location**: `agents/` directory
- Each agent has integrated version (CrewAI) and standalone version
- Follow pattern: `AgentName.py` + `AgentName_standalone.py`
- Use `AGENTS_AVAILABLE` flag in integration_manager.py for graceful degradation

### 2. Data Processing Pipeline
**Location**: `tools/` directory
- `GA4DataParser`: NDJSON parsing with validation
- `DataStorageManager`: In-memory data management
- `DataValidator`: Comprehensive data quality checks

### 3. UI Development
**Location**: `ui/` directory
- Modular page structure: `pages/` for individual analysis views
- Component-based design: `components/` for reusable UI elements
- State management: `state/` for Streamlit session persistence

### 4. Configuration Management
**Location**: `config/` directory
- `settings.py`: Pydantic-based configuration with validation
- `llm_provider_manager.py`: Dual provider management with failover
- JSON configs for system and analysis parameters

## Performance & Scalability

### Current Limitations
- **Memory**: In-memory pandas processing limits dataset size
- **Scalability**: Single-threaded analysis for complex operations
- **Storage**: File-based, no database persistence

### Scaling Path
1. **Short-term**: DuckDB integration for out-of-core processing
2. **Medium-term**: Async processing with ThreadPoolExecutor
3. **Long-term**: Database backend with caching layer

## Testing Framework

### Test Categories
```bash
# Basic functionality
python test_basic_setup.py

# Component integration
python test_ga4_parser_integration.py
python test_storage_integration.py

# Agent testing
python test_event_analysis_agent_standalone.py

# End-to-end
python test_comprehensive_integration.py
```

### Test Data Generation
```bash
# Generate clean test data
python generate_clean_data.py

# Quick data tests
python quick_data_test.py
```

## Deployment & Operations

### Docker Configuration
- **Development**: `docker-compose.dev.yml` with hot reload
- **Production**: `docker-compose.yml` with security policies
- **Health monitoring**: Built-in health endpoints

### Resource Requirements
- **Development**: 4GB RAM, 2GB disk
- **Production**: 8GB RAM, 10GB disk (for larger datasets)

## Known Issues & Fixes

### Language Localization Issue
**Problem**: UI language setting in `config/system_config.json` doesn't affect interface
**Location**: `main.py:809-884`
**Fix**: Implement i18n system reading from `ui_settings.language`

### Memory Management
**Problem**: Large datasets cause OOM errors
**Current mitigation**: Memory monitoring in `IntegrationManager._monitor_system_metrics`
**Solution**: Implement chunked processing with DuckDB

### Test Framework
**Current**: Standalone scripts
**Recommended**: Gradual migration to pytest for CI/CD integration

## File Structure Deep Dive

```
├── agents/                  # 7 CrewAI agents + standalone versions
├── engines/                 # Fallback analysis engines
├── tools/                   # Data processing utilities
├── ui/                      # Streamlit interface components
│   ├── components/          # Reusable UI elements
│   ├── pages/              # Individual analysis views
│   ├── layouts/            # Page layouts
│   └── state/              # Session state management
├── config/                  # Configuration management
├── system/                  # Core integration logic
├── data/                    # File storage for uploads
├── logs/                    # Application logs
└── tests/                   # Comprehensive test suite
```

## Critical Development Guidelines

### 1. Never Commit API Keys
- Use `.env` file for all secrets
- Validate configuration with `config_validator.py`

### 2. Maintain Agent/Engine Parity
- When adding new analysis type, implement both agent and engine
- Ensure feature parity between implementations

### 3. Memory-Conscious Development
- Always test with realistic dataset sizes
- Use `DataStorageManager` cleanup methods
- Monitor memory usage in development

### 4. Error Handling Patterns
- Use comprehensive try/catch throughout
- Implement graceful degradation
- Leverage fallback mechanisms for LLM providers

## Quick Reference Commands

```bash
# Development flow
./deploy.sh -e development -a up -b    # Start dev environment
python test_minimal_integration.py      # Quick validation
curl http://localhost:8502/health       # Health check

# Production deployment
./deploy.sh -e production -a up -d

# Troubleshooting
python diagnose.py                      # System diagnostics
python debug_env.py                     # Environment issues
python debug_providers.py               # LLM provider issues

# Testing
python test_all_fixes_final.py          # Comprehensive test run
python test_visualization_only.py       # UI-focused testing
```