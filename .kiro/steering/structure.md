# Project Structure & Organization

## Architecture Overview
ZenGrowth follows a modular architecture with clear separation of concerns:
- **Multi-agent system** with CrewAI orchestration
- **Fallback engine pattern** for reliability
- **Layered UI architecture** with Streamlit
- **Centralized configuration management**
- **Singleton pattern** for integration management

## Directory Structure

### Core Application Modules
- **`agents/`**: CrewAI-based intelligent agents for specialized analysis tasks
  - Each agent handles specific analytics (events, retention, conversion, etc.)
  - Includes shared tools and base components
  - Standalone versions available for fallback scenarios

- **`engines/`**: Fallback analysis engines when agents are unavailable
  - Mirror agent functionality with simplified implementations
  - Direct data processing without LLM dependencies
  - Ensure system reliability during API failures

- **`ui/`**: Streamlit user interface components
  - `components/`: Reusable UI components (config panels, results display)
  - `pages/`: Individual page modules for different analysis types
  - `layouts/`: Layout management and navigation
  - `state/`: Centralized state management for UI

- **`config/`**: Configuration and system management
  - Settings management with Pydantic
  - LLM provider management and health monitoring
  - Agent orchestration and communication
  - Monitoring and fallback systems

### Data & Processing
- **`tools/`**: Data processing utilities
  - GA4 data parser and validator
  - Data storage management
  - Data cleaning and transformation tools

- **`visualization/`**: Chart generation and reporting
  - Plotly-based interactive visualizations
  - Advanced chart generators
  - Report export functionality

- **`utils/`**: Shared utilities
  - Internationalization (i18n) support
  - Performance optimization
  - Caching mechanisms
  - Logging configuration

### System Integration
- **`system/`**: Core system management
  - Integration manager (singleton pattern)
  - Cross-component coordination
  - System health monitoring

### Data & Output
- **`data/`**: Data storage with environment separation
  - `development/`, `production/` environment folders
  - `uploads/` for user data files
  - `processed/` for cleaned data

- **`logs/`**: Application logging
  - Environment-specific log directories
  - Monitoring and performance logs
  - Error tracking and debugging

- **`reports/`**: Generated analysis reports
  - JSON, PDF, and Excel export formats
  - Environment-specific report storage

### Configuration & Deployment
- **`languages/`**: Internationalization files (en-US.json, zh-CN.json)
- **`security/`**: Security policies and configurations
- **`tests/`**: Comprehensive test suite
- **Docker files**: Multi-environment containerization

## Key Patterns & Conventions

### Naming Conventions
- **Agents**: `*_agent.py` (e.g., `event_analysis_agent.py`)
- **Engines**: `*_engine.py` (e.g., `event_analysis_engine.py`)
- **UI Pages**: `*.py` in `ui/pages/` (e.g., `event_analysis.py`)
- **Test Files**: `test_*.py` with descriptive names

### Code Organization
- **Singleton Pattern**: Integration manager uses singleton for system-wide coordination
- **Pydantic Models**: All configuration classes inherit from BaseSettings
- **Error Handling**: Graceful degradation with fallback mechanisms
- **Logging**: Structured logging with configurable levels
- **State Management**: Centralized UI state with session persistence

### Configuration Hierarchy
1. **Environment Variables**: `.env` files (highest priority)
2. **JSON Config**: `config/system_config.json`
3. **Default Values**: Pydantic field defaults
4. **Runtime Settings**: Dynamic configuration updates

### Import Patterns
- Relative imports within modules
- Graceful handling of optional dependencies (CrewAI)
- Lazy loading for performance optimization
- Clear separation between core and optional components

### File Organization Best Practices
- One class per file for agents and engines
- Shared utilities in dedicated modules
- Environment-specific configurations
- Clear separation of concerns between layers