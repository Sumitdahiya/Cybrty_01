# Azure Deployment Guide for AI-Guided Penetration Testing System

## 🚀 Complete Azure Deployment Strategy

### Overview
This guide provides step-by-step instructions to deploy the AI-guided penetration testing system to Azure App Service with all required tools and dependencies.

## 📋 Prerequisites

1. **Azure Account** with active subscription
2. **Azure CLI** installed on your local machine
3. **Docker** (for containerized deployment)
4. **MongoDB Atlas** account (recommended for cloud database)

## 🏗️ Deployment Architecture

```
Azure Resource Group
├── App Service Plan (Linux)
├── App Service (Container)
├── Azure Container Registry
├── Azure KeyVault (for secrets)
├── Azure Application Insights
└── External: MongoDB Atlas
```

## 📦 Method 1: Azure Container Instances (Recommended)

### Step 1: Create Dockerfile

```dockerfile
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies and penetration testing tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    nmap \
    nikto \
    sqlmap \
    hydra \
    john \
    enum4linux \
    wireshark-common \
    tshark \
    masscan \
    gobuster \
    dirb \
    whatweb \
    dnsutils \
    netcat \
    telnet \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 pentester && \
    chown -R pentester:pentester /app
USER pentester

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Create requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pymongo==4.6.0
ollama==0.1.7
crewai==0.28.8
pydantic==2.5.0
python-multipart==0.0.6
aiofiles==23.2.1
httpx==0.25.2
python-dotenv==1.0.0
azure-keyvault-secrets==4.7.0
azure-identity==1.15.0
```

### Step 3: Create docker-compose.yml for Local Testing

```yaml
version: '3.8'
services:
  pentest-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - OLLAMA_HOST=${OLLAMA_HOST}
      - AZURE_KEYVAULT_URL=${AZURE_KEYVAULT_URL}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
```

### Step 4: Azure Deployment Scripts

Create `deploy-azure.sh`:

```bash
#!/bin/bash

# Azure Deployment Script for AI-Guided Penetration Testing System

set -e

# Configuration
RESOURCE_GROUP="pentest-ai-rg"
LOCATION="eastus"
ACR_NAME="pentestairegistry"
APP_SERVICE_PLAN="pentest-ai-plan"
APP_SERVICE_NAME="pentest-ai-app"
KEYVAULT_NAME="pentest-ai-kv"

echo "🚀 Starting Azure deployment..."

# Login to Azure (if not already logged in)
az login

# Create Resource Group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo "🏗️ Creating Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Build and push Docker image
echo "🐳 Building and pushing Docker image..."
az acr build --registry $ACR_NAME --image pentest-ai:latest .

# Create Key Vault
echo "🔐 Creating Azure Key Vault..."
az keyvault create --name $KEYVAULT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# Create App Service Plan (Linux)
echo "📱 Creating App Service Plan..."
az appservice plan create --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --is-linux \
    --sku B1

# Create App Service
echo "🌐 Creating App Service..."
az webapp create --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --name $APP_SERVICE_NAME \
    --deployment-container-image-name $ACR_LOGIN_SERVER/pentest-ai:latest

# Configure App Service to use ACR
echo "⚙️ Configuring App Service..."
az webapp config container set --name $APP_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $ACR_LOGIN_SERVER/pentest-ai:latest \
    --docker-registry-server-url https://$ACR_LOGIN_SERVER

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Set container registry credentials
az webapp config appsettings set --name $APP_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    DOCKER_REGISTRY_SERVER_URL=https://$ACR_LOGIN_SERVER \
    DOCKER_REGISTRY_SERVER_USERNAME=$ACR_USERNAME \
    DOCKER_REGISTRY_SERVER_PASSWORD=$ACR_PASSWORD

# Configure App Settings
echo "🔧 Setting application configuration..."
az webapp config appsettings set --name $APP_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
    WEBSITES_PORT=8000 \
    MONGODB_URI="@Microsoft.KeyVault(SecretUri=https://$KEYVAULT_NAME.vault.azure.net/secrets/mongodb-uri/)" \
    OLLAMA_HOST="http://localhost:11434" \
    AZURE_KEYVAULT_URL="https://$KEYVAULT_NAME.vault.azure.net/"

# Enable managed identity
echo "🆔 Enabling managed identity..."
PRINCIPAL_ID=$(az webapp identity assign --name $APP_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --query principalId --output tsv)

# Grant Key Vault access
echo "🔑 Granting Key Vault access..."
az keyvault set-policy --name $KEYVAULT_NAME \
    --object-id $PRINCIPAL_ID \
    --secret-permissions get list

# Enable Application Insights
echo "📊 Setting up Application Insights..."
az extension add --name application-insights
APPINSIGHTS_KEY=$(az monitor app-insights component create \
    --app $APP_SERVICE_NAME \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --query instrumentationKey --output tsv)

az webapp config appsettings set --name $APP_SERVICE_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY=$APPINSIGHTS_KEY

echo "✅ Deployment completed!"
echo "🌐 App URL: https://$APP_SERVICE_NAME.azurewebsites.net"
echo "📊 Application Insights: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/microsoft.insights/components/$APP_SERVICE_NAME"

# Store secrets in Key Vault
echo "💾 Remember to add your MongoDB URI to Key Vault:"
echo "az keyvault secret set --vault-name $KEYVAULT_NAME --name 'mongodb-uri' --value 'your-mongodb-connection-string'"
```

## 📦 Method 2: Azure App Service (Code Deployment)

### Step 1: Create Azure Resources

```bash
# Create resource group
az group create --name pentest-ai-rg --location eastus

# Create App Service Plan
az appservice plan create --name pentest-ai-plan \
    --resource-group pentest-ai-rg \
    --sku B1 \
    --is-linux

# Create App Service
az webapp create --resource-group pentest-ai-rg \
    --plan pentest-ai-plan \
    --name pentest-ai-app \
    --runtime "PYTHON|3.11"
```

### Step 2: Install Tools via Startup Script

Create `startup.sh`:

```bash
#!/bin/bash

# Azure App Service startup script to install penetration testing tools

echo "🔧 Installing penetration testing tools..."

# Update package list
apt-get update

# Install penetration testing tools
apt-get install -y \
    nmap \
    nikto \
    sqlmap \
    hydra \
    john \
    enum4linux \
    wireshark-common \
    tshark \
    masscan \
    gobuster \
    dirb \
    whatweb \
    dnsutils \
    netcat \
    telnet

echo "✅ Tools installation completed"

# Start the application
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Step 3: Configure App Service

```bash
# Set startup script
az webapp config set --resource-group pentest-ai-rg \
    --name pentest-ai-app \
    --startup-file startup.sh

# Configure app settings
az webapp config appsettings set --name pentest-ai-app \
    --resource-group pentest-ai-rg \
    --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    MONGODB_URI="your-mongodb-uri" \
    OLLAMA_HOST="https://ollama-api-endpoint.com"
```

## 🗄️ Database Setup (MongoDB Atlas)

### Step 1: Create MongoDB Atlas Cluster

1. Go to [MongoDB Atlas](https://cloud.mongodb.com)
2. Create new cluster (Free tier available)
3. Configure network access (add Azure App Service IP)
4. Create database user
5. Get connection string

### Step 2: Store Connection String in Azure Key Vault

```bash
# Add MongoDB URI to Key Vault
az keyvault secret set --vault-name pentest-ai-kv \
    --name 'mongodb-uri' \
    --value 'mongodb+srv://username:password@cluster.mongodb.net/crewai_pentest'
```

## 🤖 Ollama Setup Options

### Option 1: Azure Container Instances (Recommended)

```bash
# Create Ollama container instance
az container create --resource-group pentest-ai-rg \
    --name ollama-instance \
    --image ollama/ollama:latest \
    --ports 11434 \
    --protocol TCP \
    --cpu 2 \
    --memory 4 \
    --environment-variables OLLAMA_HOST=0.0.0.0 \
    --dns-name-label pentest-ollama
```

### Option 2: External Ollama Service

Use a cloud-hosted Ollama service or set up on a separate VM.

## 🔐 Security Configuration

### Environment Variables Setup

Create `.env.azure`:

```env
# Azure-specific environment variables
MONGODB_URI=@Microsoft.KeyVault(SecretUri=https://pentest-ai-kv.vault.azure.net/secrets/mongodb-uri/)
OLLAMA_HOST=http://pentest-ollama.eastus.azurecontainer.io:11434
AZURE_KEYVAULT_URL=https://pentest-ai-kv.vault.azure.net/
APPINSIGHTS_INSTRUMENTATIONKEY=your-app-insights-key
ENVIRONMENT=production
```

### Add Security Headers

Create `azure_security.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

def configure_azure_security(app: FastAPI):
    """Configure security for Azure deployment"""
    
    # CORS configuration for Azure
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://pentest-ai-app.azurewebsites.net"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["pentest-ai-app.azurewebsites.net", "localhost"]
    )
    
    return app
```

## 📊 Monitoring & Logging

### Application Insights Integration

Update `main.py`:

```python
import os
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

# Configure Azure Application Insights
if os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY"):
    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler(
        connection_string=f"InstrumentationKey={os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY')}"
    ))
```

## 🚀 Deployment Commands

### Complete Deployment Script

```bash
#!/bin/bash

# Complete Azure deployment
echo "🚀 Starting complete Azure deployment..."

# Make deployment script executable
chmod +x deploy-azure.sh

# Run deployment
./deploy-azure.sh

# Deploy code to App Service
az webapp deployment source config-zip --resource-group pentest-ai-rg \
    --name pentest-ai-app \
    --src deployment.zip

echo "✅ Deployment completed successfully!"
echo "🌐 Access your app at: https://pentest-ai-app.azurewebsites.net"
```

## 🔍 Testing Deployment

### Health Check Endpoint

Add to `main.py`:

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for Azure"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "tools_available": len(ToolManager().get_available_tools()),
        "mongodb_connected": CrewAIMongoDB().is_connected()
    }
```

### Test Commands

```bash
# Test health endpoint
curl https://pentest-ai-app.azurewebsites.net/health

# Test AI agents
curl https://pentest-ai-app.azurewebsites.net/ai-agents/available

# Test tool execution
curl -X POST "https://pentest-ai-app.azurewebsites.net/tools/nmap/execute?target=example.com"
```

## 💰 Cost Optimization

### Recommended Azure SKUs

1. **Development**: B1 Basic ($13.14/month)
2. **Production**: S1 Standard ($56.94/month)
3. **High Performance**: P1V2 Premium ($146.88/month)

### Cost-Saving Tips

1. Use Azure DevOps for CI/CD (free tier available)
2. Implement auto-scaling for variable workloads
3. Use Azure Container Instances for Ollama (pay-per-use)
4. Monitor with Azure Cost Management

## 📚 Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Container Registry](https://docs.microsoft.com/en-us/azure/container-registry/)
- [MongoDB Atlas on Azure](https://www.mongodb.com/cloud/atlas/azure)
- [Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/)

## 🎯 Next Steps

1. Set up CI/CD pipeline with Azure DevOps
2. Configure backup strategies
3. Implement blue-green deployment
4. Set up monitoring alerts
5. Configure auto-scaling rules

This deployment guide provides a production-ready setup for your AI-guided penetration testing system on Azure! 🚀
