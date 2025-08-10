# PenTest AI API

A Python FastAPI application that integrates CrewAI agents for automated penetration testing using the Ollama Deepseek model.

## Features

- **FastAPI Web Framework**: Modern, fast API with automatic documentation
- **CrewAI Integration**: Multi-agent framework for collaborative AI penetration testing
- **Ollama Deepseek Model**: Local LLM inference for privacy and control
- **Modular Agent Architecture**: Specialized agents for different testing phases
- **Automated Model Management**: Automatic Ollama installation and model downloading

## Project Structure

```
├── main.py                    # FastAPI application entry point
├── start.py                   # Startup script with setup automation
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── agents/
│   ├── __init__.py
│   └── pentest_crew.py       # CrewAI agents for penetration testing
├── models/
│   ├── __init__.py
│   └── ollama_manager.py     # Ollama service and model management
├── config/
│   ├── __init__.py
│   └── settings.py           # Application configuration
└── .github/
    └── copilot-instructions.md
```

## Specialized Agents

The application includes four specialized CrewAI agents:

1. **Reconnaissance Agent**: Information gathering and target analysis
2. **Vulnerability Assessment Agent**: Security flaw identification and analysis
3. **Exploitation Agent**: Safe vulnerability demonstration and validation
4. **Report Generation Agent**: Comprehensive security report creation

## Installation

### Prerequisites

- Python 3.8 or higher
- macOS or Linux (for automatic Ollama installation)

### Quick Start

1. **Clone and setup the project:**
   ```bash
   cd /path/to/your/project
   pip install -r requirements.txt
   ```

2. **Configure environment (optional):**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

3. **Start the application:**
   ```bash
   python start.py
   ```
   
   **OR directly with uvicorn:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### ⚠️ **Current Status: Ollama Required for Full AI Features**

The API is **currently running in fallback mode** because Ollama is not installed. 

**What works now:**
- ✅ All API endpoints are functional
- ✅ Basic penetration testing workflows
- ✅ API documentation and health checks
- ✅ Structured response format

**For full AI-powered analysis, install Ollama:**

#### Option 1: Homebrew (macOS - Recommended)
```bash
brew install ollama
ollama serve
ollama pull deepseek-r1:1.5b
```

#### Option 2: Direct Download
- **macOS**: https://ollama.ai/download/mac
- **Linux**: https://ollama.ai/download/linux  
- **Windows**: https://ollama.ai/download/windows

#### Option 3: Install Script (Linux/macOS)
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull deepseek-r1:1.5b
```

**After Ollama installation:**
1. Restart the API server
2. The API will automatically detect Ollama and enable full AI features
3. Check status at: `http://localhost:8000/models/status`

## API Usage

### Main Endpoint

**POST** `/invokePentest`

Invoke the CrewAI penetration testing agents.

#### Request Body

```json
{
  "target": "example.com",
  "scope": "basic",
  "additional_params": {
    "deep_scan": true,
    "exclude_paths": ["/admin", "/secure"]
  }
}
```

#### Response

```json
{
  "status": "success",
  "message": "Penetration testing completed successfully",
  "results": {
    "target": "example.com",
    "scope": "basic",
    "status": "completed",
    "findings": {
      "reconnaissance": "Reconnaissance completed successfully",
      "vulnerabilities": "Vulnerability assessment completed",
      "exploitation": "Safe exploitation testing completed",
      "report": "Final report generated"
    },
    "raw_output": "Detailed crew execution results...",
    "additional_params": {...}
  }
}
```

### Additional Endpoints

- **GET** `/`: Health check
- **GET** `/health`: Service status
- **GET** `/models/status`: Ollama model status
- **GET** `/docs`: Interactive API documentation (Swagger UI)

## API Examples

### Using curl

```bash
# Basic penetration test
curl -X POST "http://localhost:8000/invokePentest" \
     -H "Content-Type: application/json" \
     -d '{
       "target": "testphp.vulnweb.com",
       "scope": "basic"
     }'

# Check model status
curl "http://localhost:8000/models/status"
```

### Using Python requests

```python
import requests

# Invoke penetration test
response = requests.post(
    "http://localhost:8000/invokePentest",
    json={
        "target": "testphp.vulnweb.com",
        "scope": "comprehensive",
        "additional_params": {
            "max_depth": 3,
            "timeout": 300
        }
    }
)

print(response.json())
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
OLLAMA_MODEL=deepseek-r1:1.5b
OLLAMA_BASE_URL=http://localhost:11434
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### Model Configuration

You can change the default Ollama model by modifying the `OLLAMA_MODEL` environment variable or updating the `OllamaManager` initialization in the code.

## Development

### Adding New Agents

To add new specialized agents, modify `agents/pentest_crew.py`:

```python
# Add new agent
new_agent = Agent(
    role='Custom Security Specialist',
    goal='Perform specialized security testing',
    backstory='Expert in custom security analysis...',
    verbose=True,
    allow_delegation=False,
    llm=self.ollama_manager.get_llm_instance()
)
```

### Extending API Endpoints

Add new endpoints in `main.py`:

```python
@app.post("/custom-endpoint")
async def custom_endpoint(request: CustomRequest):
    # Your custom logic here
    pass
```

## Security Considerations

⚠️ **Important Security Notes:**

- This tool is for **authorized penetration testing only**
- Always obtain proper permission before testing any system
- Use only in controlled, legal environments
- The tool includes safety measures but should be used responsibly
- Review and understand the code before deployment

## Troubleshooting

### Common Issues

1. **Ollama installation fails:**
   - Ensure you have administrator privileges
   - Check your internet connection
   - Manually install Ollama from https://ollama.ai

2. **Model download is slow:**
   - The Deepseek model is large (~1GB)
   - Ensure stable internet connection
   - Monitor progress in the logs

3. **API startup errors:**
   - Check if port 8000 is available
   - Verify all dependencies are installed
   - Check the logs for specific error messages

4. **Agent execution fails:**
   - Ensure Ollama service is running
   - Verify the model is downloaded
   - Check available system resources

### Logs

The application provides detailed logging. Check the console output for:
- Service startup status
- Model download progress
- Agent execution details
- Error messages and stack traces

## License

This project is for educational and authorized security testing purposes only. Use responsibly and in compliance with applicable laws and regulations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue with detailed information
