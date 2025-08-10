#!/usr/bin/env python3
"""
Startup script for the PenTest AI API
"""

import asyncio
import subprocess
import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import crewai
        import ollama
        logger.info("All Python dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

async def setup_ollama():
    """Setup Ollama and download the Deepseek model"""
    try:
        from models.ollama_manager import OllamaManager
        
        logger.info("Setting up Ollama and Deepseek model...")
        ollama_manager = OllamaManager()
        await ollama_manager.ensure_model_available()
        logger.info("Ollama setup completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to setup Ollama: {e}")
        return False

async def start_api():
    """Start the FastAPI application"""
    try:
        import uvicorn
        from main import app
        
        logger.info("Starting PenTest AI API...")
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
        
    except Exception as e:
        logger.error(f"Failed to start API: {e}")
        return False

async def main():
    """Main startup function"""
    logger.info("Starting PenTest AI API setup...")
    
    # Check dependencies
    if not await check_dependencies():
        logger.error("Failed to check/install dependencies")
        return
    
    # Setup Ollama
    if not await setup_ollama():
        logger.error("Failed to setup Ollama")
        return
    
    # Start API
    logger.info("Setup completed. Starting API server...")
    await start_api()

if __name__ == "__main__":
    asyncio.run(main())
