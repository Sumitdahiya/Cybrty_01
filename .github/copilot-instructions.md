<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# PenTest AI API - Copilot Instructions

This is a Python FastAPI application that integrates CrewAI agents for penetration testing with Ollama Deepseek model integration.

## Project Structure
- `main.py`: FastAPI application with `/invokePentest` endpoint
- `agents/`: CrewAI agent implementations for penetration testing
  - `pentest_crew.py`: Main crew with specialized agents (recon, vulnerability, exploitation, reporting)
- `models/`: Ollama integration and model management
  - `ollama_manager.py`: Handles Ollama service and Deepseek model
- `config/`: Application configuration
- `start.py`: Startup script for the application

## Key Technologies
- **FastAPI**: Web framework for the API
- **CrewAI**: Multi-agent framework for AI collaboration
- **Ollama**: Local LLM inference with Deepseek model
- **Pydantic**: Data validation and settings management

## Development Guidelines
1. Follow async/await patterns for I/O operations
2. Use proper error handling and logging
3. Maintain modular agent structure with CrewAI
4. Ensure Ollama integration is robust and handles model downloading
5. API responses should be properly structured with Pydantic models

## Security Considerations
- This is for educational/ethical penetration testing purposes only
- All testing should be conducted with proper authorization
- Implement proper input validation and sanitization
- Use secure configurations for production deployments

## Common Tasks
- Adding new agents: Create new Agent instances in `pentest_crew.py`
- Modifying API endpoints: Update `main.py`
- Ollama configuration: Modify `ollama_manager.py`
- Environment settings: Update `.env` files
