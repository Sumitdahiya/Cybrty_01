# Ollama Installation Guide

## Quick Installation

### macOS

#### Option 1: Using Homebrew (Recommended)
```bash
brew install ollama
```

#### Option 2: Download installer
1. Visit https://ollama.ai/download/mac
2. Download the installer
3. Follow the installation instructions

### Linux

#### Option 1: Using install script
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Option 2: Manual installation
1. Visit https://ollama.ai/download/linux
2. Download the appropriate package for your distribution
3. Install using your package manager

### Windows
1. Visit https://ollama.ai/download/windows
2. Download the installer
3. Run the installer

## Post-Installation Setup

1. **Start Ollama service:**
   ```bash
   ollama serve
   ```

2. **Download the Deepseek model:**
   ```bash
   ollama pull deepseek-r1:1.5b
   ```

3. **Verify installation:**
   ```bash
   ollama list
   ```

## Alternative Models

If you prefer to use a different model, you can change the model name in the configuration:

```bash
# Popular alternatives:
ollama pull llama2:7b
ollama pull codellama:7b
ollama pull mistral:7b
```

Then update the `OLLAMA_MODEL` environment variable in your `.env` file.

## Troubleshooting

### Service not starting
- Check if port 11434 is available
- Try running with explicit host: `ollama serve --host 0.0.0.0`

### Model not downloading
- Check internet connection
- Verify disk space (models can be 1-7GB)
- Try downloading manually: `ollama pull <model-name>`

### API integration issues
- Ensure Ollama service is running: `ollama ps`
- Check if model is loaded: `ollama list`
- Verify base URL in configuration: `http://localhost:11434`

## Configuration

After installation, the PenTest AI API will automatically:
- Detect Ollama installation
- Start the service if needed
- Download the required model
- Integrate with CrewAI agents

No additional configuration is required once Ollama is properly installed.
