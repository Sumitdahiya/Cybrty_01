import ollama
import asyncio
import logging
from typing import Dict, Any, Optional
import subprocess
import sys
import os

logger = logging.getLogger(__name__)

class OllamaManager:
    """Manager for Ollama integration and Deepseek model management"""
    
    def __init__(self, model_name: str = "deepseek-r1:1.5b"):
        self.model_name = model_name
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Ollama client"""
        try:
            self.client = ollama.Client()
            logger.info("Ollama client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {str(e)}")
            raise
    
    async def ensure_ollama_installed(self) -> bool:
        """Ensure Ollama is installed on the system"""
        try:
            # Check if ollama command is available
            result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Ollama is already installed at: {result.stdout.strip()}")
                return True
            
            logger.info("Ollama not found, attempting to install...")
            
            # Install Ollama (macOS/Linux)
            if sys.platform == "darwin" or sys.platform.startswith("linux"):
                logger.info("Attempting automatic Ollama installation...")
                install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
                result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
                
                logger.info(f"Install command stdout: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Install command stderr: {result.stderr}")
                
                if result.returncode == 0:
                    logger.info("Ollama installation command completed successfully")
                    
                    # Verify installation
                    await asyncio.sleep(2)  # Wait for installation to complete
                    verify_result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
                    if verify_result.returncode == 0:
                        logger.info("Ollama installed and verified successfully")
                        return True
                    else:
                        logger.error("Ollama installation completed but binary not found in PATH")
                        self._show_manual_install_instructions()
                        return False
                else:
                    logger.error(f"Failed to install Ollama. Return code: {result.returncode}")
                    logger.error(f"Stdout: {result.stdout}")
                    logger.error(f"Stderr: {result.stderr}")
                    self._show_manual_install_instructions()
                    return False
            else:
                logger.error("Automatic Ollama installation not supported on this platform")
                self._show_manual_install_instructions()
                return False
                
        except Exception as e:
            logger.error(f"Error checking/installing Ollama: {str(e)}")
            self._show_manual_install_instructions()
            return False
    
    def _show_manual_install_instructions(self):
        """Show manual installation instructions"""
        logger.info("="*60)
        logger.info("MANUAL OLLAMA INSTALLATION REQUIRED")
        logger.info("="*60)
        logger.info("Please install Ollama manually:")
        logger.info("")
        if sys.platform == "darwin":
            logger.info("Option 1 - Using Homebrew:")
            logger.info("  brew install ollama")
            logger.info("")
            logger.info("Option 2 - Download installer:")
            logger.info("  https://ollama.ai/download/mac")
            logger.info("")
        elif sys.platform.startswith("linux"):
            logger.info("Option 1 - Manual install script:")
            logger.info("  curl -fsSL https://ollama.ai/install.sh | sh")
            logger.info("")
            logger.info("Option 2 - Download from:")
            logger.info("  https://ollama.ai/download/linux")
            logger.info("")
        else:
            logger.info("Download from: https://ollama.ai/download")
            logger.info("")
        logger.info("After installation, restart the API server.")
        logger.info("="*60)
    
    async def start_ollama_service(self) -> bool:
        """Start Ollama service if not running"""
        try:
            # Check if Ollama service is running
            result = subprocess.run(['pgrep', 'ollama'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Ollama service is already running")
                return True
            
            logger.info("Starting Ollama service...")
            
            # Start Ollama in background
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait a bit for service to start
            await asyncio.sleep(3)
            
            # Verify service is running
            result = subprocess.run(['pgrep', 'ollama'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Ollama service started successfully")
                return True
            else:
                logger.error("Failed to start Ollama service")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Ollama service: {str(e)}")
            return False
    
    async def download_model(self) -> bool:
        """Download the Deepseek model if not already available"""
        try:
            logger.info(f"Checking if model {self.model_name} is available...")
            
            # List available models
            models = self.client.list()
            available_models = [model['name'] for model in models.get('models', [])]
            
            if self.model_name in available_models:
                logger.info(f"Model {self.model_name} is already available")
                return True
            
            logger.info(f"Downloading model {self.model_name}...")
            
            # Pull the model
            stream = self.client.pull(self.model_name, stream=True)
            
            for chunk in stream:
                if 'status' in chunk:
                    if chunk['status'] == 'downloading':
                        if 'completed' in chunk and 'total' in chunk:
                            progress = (chunk['completed'] / chunk['total']) * 100
                            logger.info(f"Download progress: {progress:.1f}%")
                    elif chunk['status'] == 'success':
                        logger.info(f"Model {self.model_name} downloaded successfully")
                        return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading model: {str(e)}")
            return False
    
    async def ensure_model_available(self) -> bool:
        """Ensure Ollama is installed, service is running, and model is downloaded"""
        try:
            # Check and install Ollama if needed
            if not await self.ensure_ollama_installed():
                logger.warning("Ollama installation failed. API will work without local model.")
                return False
            
            # Start Ollama service if needed
            if not await self.start_ollama_service():
                logger.warning("Failed to start Ollama service. API will work without local model.")
                return False
            
            # Download model if needed
            if not await self.download_model():
                logger.warning("Failed to download model. API will work without local model.")
                return False
            
            logger.info("Ollama and Deepseek model are ready")
            return True
            
        except Exception as e:
            logger.warning(f"Error ensuring model availability: {str(e)}. API will work without local model.")
            return False
    
    def get_llm_instance(self):
        """Get LLM instance for CrewAI integration"""
        try:
            # First check if Ollama is available
            result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("Ollama not found. Creating fallback LLM instance.")
                return self._create_fallback_llm()
            
            # Check if Ollama service is running
            service_check = subprocess.run(['pgrep', 'ollama'], capture_output=True, text=True)
            if service_check.returncode != 0:
                logger.warning("Ollama service not running. Creating fallback LLM instance.")
                return self._create_fallback_llm()
            
            # For CrewAI with LiteLLM integration, we need to use the correct format
            # CrewAI expects the model name to have the provider prefix
            try:
                from crewai import LLM
                
                # Use CrewAI's LLM class with the correct model format for Ollama
                ollama_model_name = f"ollama/{self.model_name}"
                
                llm_instance = LLM(
                    model=ollama_model_name,
                    base_url="http://localhost:11434"
                )
                logger.info(f"Created CrewAI LLM instance for model {ollama_model_name}")
                return llm_instance
                
            except ImportError:
                # Fallback to direct Ollama if CrewAI LLM not available
                logger.warning("CrewAI LLM not available, using direct Ollama")
                from langchain_community.llms import Ollama
                
                test_llm = Ollama(
                    model=self.model_name,
                    base_url="http://localhost:11434",
                    temperature=0.7
                )
                logger.info(f"Created direct Ollama LLM instance for model {self.model_name}")
                return test_llm
            except Exception as e:
                logger.warning(f"Failed to create CrewAI LLM instance: {e}. Trying direct Ollama...")
                
                # Fallback to direct Ollama
                from langchain_community.llms import Ollama
                
                test_llm = Ollama(
                    model=self.model_name,
                    base_url="http://localhost:11434",
                    temperature=0.7
                )
                logger.info(f"Created direct Ollama LLM instance for model {self.model_name}")
                return test_llm
            
        except ImportError:
            logger.warning("langchain_community not available. Installing...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "langchain-community"], 
                             capture_output=True, text=True)
                from langchain_community.llms import Ollama
                
                llm = Ollama(
                    model=self.model_name,
                    base_url="http://localhost:11434",
                    temperature=0.7
                )
                return llm
            except Exception as e:
                logger.warning(f"Failed to install/import langchain_community: {e}. Using fallback.")
                return self._create_fallback_llm()
        except Exception as e:
            logger.warning(f"Error creating LLM instance: {str(e)}. Using fallback.")
            return self._create_fallback_llm()
    
    def _create_fallback_llm(self):
        """Create a fallback LLM instance when Ollama is not available"""
        try:
            # Try to use OpenAI as fallback (if API key is available)
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                try:
                    from langchain_openai import ChatOpenAI
                    logger.info("Using OpenAI as fallback LLM")
                    return ChatOpenAI(
                        model="gpt-3.5-turbo",
                        temperature=0.7,
                        api_key=openai_key
                    )
                except ImportError:
                    logger.warning("OpenAI package not available")
                except Exception as e:
                    logger.warning(f"Failed to create OpenAI LLM: {e}")
            
            # If no OpenAI, create a simple mock LLM for testing
            logger.info("Creating mock LLM for testing purposes")
            return self._create_mock_llm()
            
        except Exception as e:
            logger.warning(f"Error creating fallback LLM: {e}")
            return self._create_mock_llm()
    
    def _create_mock_llm(self):
        """Create a simple mock LLM for when no real LLM is available"""
        class MockLLM:
            def __init__(self):
                self.model_name = "mock-llm"
            
            def __call__(self, prompt: str, **kwargs) -> str:
                return f"[MOCK RESPONSE] Analysis for: {prompt[:100]}..."
            
            def invoke(self, prompt: str, **kwargs) -> str:
                return f"[MOCK RESPONSE] Analysis for: {prompt[:100]}..."
            
            def predict(self, text: str, **kwargs) -> str:
                return f"[MOCK RESPONSE] Analysis for: {text[:100]}..."
        
        return MockLLM()
    
    async def get_model_status(self) -> Dict[str, Any]:
        """Get the current status of the model and Ollama service"""
        try:
            status = {
                "ollama_installed": False,
                "service_running": False,
                "model_available": False,
                "model_name": self.model_name
            }
            
            # Check if Ollama is installed
            result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
            status["ollama_installed"] = result.returncode == 0
            
            if status["ollama_installed"]:
                # Check if service is running
                result = subprocess.run(['pgrep', 'ollama'], capture_output=True, text=True)
                status["service_running"] = result.returncode == 0
                
                if status["service_running"]:
                    # Check if model is available
                    try:
                        models = self.client.list()
                        available_models = [model['name'] for model in models.get('models', [])]
                        status["model_available"] = self.model_name in available_models
                        status["available_models"] = available_models
                    except Exception as e:
                        status["error"] = f"Error checking models: {str(e)}"
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting model status: {str(e)}")
            return {"error": str(e)}
    
    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate response using the Deepseek model"""
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            response = self.client.generate(
                model=self.model_name,
                prompt=full_prompt,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2048
                }
            )
            
            return response['response']
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
