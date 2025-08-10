"""
Azure-specific configuration and utilities for the AI-Guided Penetration Testing System
"""

import os
import logging
from typing import Optional, Dict, Any
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.core.exceptions import AzureError
from fastapi import HTTPException

# Configure logging
logger = logging.getLogger(__name__)

class AzureKeyVaultManager:
    """Manages Azure Key Vault operations for secure secret retrieval"""
    
    def __init__(self):
        self.vault_url = os.getenv("AZURE_KEYVAULT_URL")
        self.client = None
        
        if self.vault_url:
            try:
                # Use managed identity in Azure or default credential locally
                credential = ManagedIdentityCredential() if os.getenv("ENVIRONMENT") == "production" else DefaultAzureCredential()
                self.client = SecretClient(vault_url=self.vault_url, credential=credential)
                logger.info(f"✅ Azure Key Vault client initialized for {self.vault_url}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Key Vault client: {e}")
    
    def get_secret(self, secret_name: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from Azure Key Vault
        
        Args:
            secret_name: Name of the secret to retrieve
            default_value: Default value if secret not found
            
        Returns:
            Secret value or default value
        """
        if not self.client:
            logger.warning(f"Key Vault client not available, using default for {secret_name}")
            return default_value
        
        try:
            secret = self.client.get_secret(secret_name)
            logger.info(f"✅ Retrieved secret: {secret_name}")
            return secret.value
        except AzureError as e:
            logger.warning(f"⚠️ Failed to retrieve secret {secret_name}: {e}")
            return default_value
        except Exception as e:
            logger.error(f"❌ Unexpected error retrieving secret {secret_name}: {e}")
            return default_value
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Set a secret in Azure Key Vault
        
        Args:
            secret_name: Name of the secret
            secret_value: Value of the secret
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Key Vault client not available")
            return False
        
        try:
            self.client.set_secret(secret_name, secret_value)
            logger.info(f"✅ Set secret: {secret_name}")
            return True
        except AzureError as e:
            logger.error(f"❌ Failed to set secret {secret_name}: {e}")
            return False

class AzureConfiguration:
    """Azure-specific configuration management"""
    
    def __init__(self):
        self.kv_manager = AzureKeyVaultManager()
        self._config_cache = {}
    
    def get_mongodb_uri(self) -> str:
        """Get MongoDB connection URI from Key Vault or environment"""
        uri = self.kv_manager.get_secret("mongodb-uri", os.getenv("MONGODB_URI"))
        if not uri:
            raise HTTPException(status_code=500, detail="MongoDB URI not configured")
        return uri
    
    def get_ollama_host(self) -> str:
        """Get Ollama host configuration"""
        return self.kv_manager.get_secret("ollama-host", os.getenv("OLLAMA_HOST", "http://localhost:11434"))
    
    def get_api_secret_key(self) -> str:
        """Get API secret key for authentication"""
        key = self.kv_manager.get_secret("api-secret-key", os.getenv("SECRET_KEY"))
        if not key:
            logger.warning("⚠️ No API secret key configured, using default")
            return "default-insecure-key-change-in-production"
        return key
    
    def get_application_insights_key(self) -> Optional[str]:
        """Get Application Insights instrumentation key"""
        return self.kv_manager.get_secret("appinsights-key", os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY"))
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        return {
            "environment": os.getenv("ENVIRONMENT", "development"),
            "azure_keyvault_url": self.kv_manager.vault_url,
            "mongodb_configured": bool(self.get_mongodb_uri()),
            "ollama_host": self.get_ollama_host(),
            "application_insights_configured": bool(self.get_application_insights_key()),
            "is_production": self.is_production()
        }

# Global configuration instance
azure_config = AzureConfiguration()

def configure_azure_logging():
    """Configure Azure Application Insights logging if available"""
    insights_key = azure_config.get_application_insights_key()
    
    if insights_key:
        try:
            from opencensus.ext.azure.log_exporter import AzureLogHandler
            
            # Configure Azure logging
            azure_handler = AzureLogHandler(connection_string=f"InstrumentationKey={insights_key}")
            
            # Add to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(azure_handler)
            
            logger.info("✅ Azure Application Insights logging configured")
            return True
        except ImportError:
            logger.warning("⚠️ Azure logging dependencies not available")
        except Exception as e:
            logger.error(f"❌ Failed to configure Azure logging: {e}")
    
    return False

def get_azure_health_info() -> Dict[str, Any]:
    """Get Azure-specific health information"""
    config = azure_config.get_all_config()
    
    health_info = {
        "azure_integration": {
            "key_vault_configured": bool(azure_config.kv_manager.vault_url),
            "key_vault_accessible": bool(azure_config.kv_manager.client),
            "application_insights_configured": config["application_insights_configured"],
            "environment": config["environment"],
            "is_production": config["is_production"]
        },
        "services": {
            "mongodb": {"configured": config["mongodb_configured"]},
            "ollama": {"host": config["ollama_host"]},
        }
    }
    
    return health_info
