# Azure Container Apps Deployment Guide

## 🚀 Complete Azure Container Apps Strategy

Azure Container Apps provides a serverless container platform with built-in scaling, traffic management, and simplified deployment. This guide shows how to deploy your AI-guided penetration testing system using Azure Container Apps.

## 📋 Architecture Overview

```
Azure Container Apps Environment
├── PenTest AI Container App (Main API)
├── Ollama AI Container App (AI Service)
├── MongoDB Container App (Database)
├── Nginx Container App (Load Balancer)
└── Shared Resources
    ├── Container Registry
    ├── Log Analytics Workspace
    ├── Key Vault
    └── Storage Account
```

## 🏗️ Benefits of Azure Container Apps

- **Serverless**: Pay only for what you use
- **Auto-scaling**: Scale to zero when not in use
- **Built-in ingress**: No need for separate load balancers
- **Multi-container support**: Run related containers together
- **Dapr integration**: Built-in service discovery and state management
- **Traffic splitting**: Blue/green deployments
- **Secret management**: Integrated with Key Vault

## 📦 Step 1: Container App Environment Setup

### Create Container Apps Environment

```bash
#!/bin/bash

# Azure Container Apps Deployment Script
set -e

# Configuration
RESOURCE_GROUP="pentest-containerapps-rg"
LOCATION="eastus"
ENVIRONMENT_NAME="pentest-env"
ACR_NAME="pentestacr$(date +%s)"
LOG_ANALYTICS_WORKSPACE="pentest-logs"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Log Analytics workspace
az monitor log-analytics workspace create \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_WORKSPACE \
    --location $LOCATION

# Get Log Analytics workspace ID and key
LOG_ANALYTICS_WORKSPACE_ID=$(az monitor log-analytics workspace show \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_WORKSPACE \
    --query customerId --output tsv)

LOG_ANALYTICS_WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_WORKSPACE \
    --query primarySharedKey --output tsv)

# Create Container Apps environment
az containerapp env create \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --logs-workspace-id $LOG_ANALYTICS_WORKSPACE_ID \
    --logs-workspace-key $LOG_ANALYTICS_WORKSPACE_KEY
```

## 📦 Step 2: Container Registry and Images

### Create Azure Container Registry

```bash
# Create Container Registry
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Build and push images
az acr build --registry $ACR_NAME --image pentest-ai:latest .
```

### Multi-Container Dockerfile (Optimized for Container Apps)

```dockerfile
# Build stage
FROM ubuntu:22.04 as builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies and tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    wget \
    git \
    build-essential \
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

# Production stage
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Copy tools from builder
COPY --from=builder /usr/bin/nmap /usr/bin/nmap
COPY --from=builder /usr/bin/nikto /usr/bin/nikto
COPY --from=builder /usr/bin/sqlmap /usr/bin/sqlmap
COPY --from=builder /usr/bin/hydra /usr/bin/hydra
COPY --from=builder /usr/bin/john /usr/bin/john
COPY --from=builder /usr/bin/enum4linux /usr/bin/enum4linux
COPY --from=builder /usr/bin/masscan /usr/bin/masscan
COPY --from=builder /usr/bin/gobuster /usr/bin/gobuster

# Install Python runtime and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 pentester && \
    chown -R pentester:pentester /app

USER pentester

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📦 Step 3: Deploy Main PenTest AI Container App

### Create Container App YAML Configuration

```yaml
# pentest-ai-containerapp.yaml
properties:
  managedEnvironmentId: /subscriptions/{subscription-id}/resourceGroups/pentest-containerapps-rg/providers/Microsoft.App/managedEnvironments/pentest-env
  configuration:
    secrets:
      - name: "mongodb-uri"
        keyVaultUrl: "https://pentest-kv.vault.azure.net/secrets/mongodb-uri"
        identity: "system"
      - name: "api-secret-key"
        keyVaultUrl: "https://pentest-kv.vault.azure.net/secrets/api-secret-key"
        identity: "system"
    registries:
      - server: pentestacr.azurecr.io
        identity: "system"
    ingress:
      external: true
      targetPort: 8000
      allowInsecure: false
      traffic:
        - weight: 100
          latestRevision: true
    dapr:
      enabled: true
      appId: "pentest-ai"
      appProtocol: "http"
      appPort: 8000
  template:
    containers:
      - image: pentestacr.azurecr.io/pentest-ai:latest
        name: pentest-ai
        env:
          - name: "MONGODB_URI"
            secretRef: "mongodb-uri"
          - name: "API_SECRET_KEY"
            secretRef: "api-secret-key"
          - name: "OLLAMA_HOST"
            value: "http://ollama-ai"
          - name: "ENVIRONMENT"
            value: "production"
          - name: "PYTHONPATH"
            value: "/app"
        resources:
          cpu: 1.0
          memory: "2Gi"
        probes:
          - type: "Liveness"
            httpGet:
              path: "/health"
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          - type: "Readiness"
            httpGet:
              path: "/health"
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
    scale:
      minReplicas: 0
      maxReplicas: 10
      rules:
        - name: "http-scaling"
          http:
            metadata:
              concurrentRequests: "50"
```

### Deploy Container App

```bash
# Deploy PenTest AI Container App
az containerapp create \
    --name pentest-ai \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image $ACR_NAME.azurecr.io/pentest-ai:latest \
    --target-port 8000 \
    --ingress 'external' \
    --registry-server $ACR_NAME.azurecr.io \
    --registry-identity system \
    --cpu 1.0 \
    --memory 2Gi \
    --min-replicas 0 \
    --max-replicas 10 \
    --env-vars \
        ENVIRONMENT=production \
        PYTHONPATH=/app \
        OLLAMA_HOST=http://ollama-ai \
    --secrets \
        mongodb-uri=keyvaultref:https://pentest-kv.vault.azure.net/secrets/mongodb-uri,identityref:system \
        api-secret-key=keyvaultref:https://pentest-kv.vault.azure.net/secrets/api-secret-key,identityref:system \
    --secret-env-vars \
        MONGODB_URI=mongodb-uri \
        API_SECRET_KEY=api-secret-key
```

## 📦 Step 4: Deploy Ollama AI Container App

### Ollama Container App

```bash
# Deploy Ollama AI Container App
az containerapp create \
    --name ollama-ai \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image ollama/ollama:latest \
    --target-port 11434 \
    --ingress 'internal' \
    --cpu 2.0 \
    --memory 4Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --env-vars \
        OLLAMA_HOST=0.0.0.0
```

## 📦 Step 5: Deploy MongoDB Container App

### MongoDB Container App

```bash
# Deploy MongoDB Container App
az containerapp create \
    --name mongodb \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image mongo:7.0 \
    --target-port 27017 \
    --ingress 'internal' \
    --cpu 1.0 \
    --memory 2Gi \
    --min-replicas 1 \
    --max-replicas 1 \
    --env-vars \
        MONGO_INITDB_ROOT_USERNAME=admin \
        MONGO_INITDB_DATABASE=crewai_pentest \
    --secrets \
        mongo-root-password=keyvaultref:https://pentest-kv.vault.azure.net/secrets/mongo-root-password,identityref:system \
    --secret-env-vars \
        MONGO_INITDB_ROOT_PASSWORD=mongo-root-password
```

## 📦 Step 6: Complete Deployment Script

### Automated Container Apps Deployment

```bash
#!/bin/bash
# complete-containerapp-deploy.sh

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
RESOURCE_GROUP="pentest-containerapps-rg"
LOCATION="eastus"
ENVIRONMENT_NAME="pentest-env"
ACR_NAME="pentestacr$(date +%s)"
LOG_ANALYTICS_WORKSPACE="pentest-logs"
KEYVAULT_NAME="pentest-kv-$(date +%s)"

print_status "Starting Azure Container Apps deployment..."

# Install Container Apps extension
az extension add --name containerapp --upgrade

# Create resource group
print_status "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Key Vault
print_status "Creating Key Vault..."
az keyvault create \
    --name $KEYVAULT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# Create Log Analytics workspace
print_status "Creating Log Analytics workspace..."
az monitor log-analytics workspace create \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_WORKSPACE \
    --location $LOCATION

# Get workspace credentials
LOG_ANALYTICS_WORKSPACE_ID=$(az monitor log-analytics workspace show \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_WORKSPACE \
    --query customerId --output tsv)

LOG_ANALYTICS_WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $LOG_ANALYTICS_WORKSPACE \
    --query primarySharedKey --output tsv)

# Create Container Apps environment
print_status "Creating Container Apps environment..."
az containerapp env create \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --logs-workspace-id $LOG_ANALYTICS_WORKSPACE_ID \
    --logs-workspace-key $LOG_ANALYTICS_WORKSPACE_KEY

# Create Container Registry
print_status "Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Standard \
    --admin-enabled true

# Build and push image
print_status "Building and pushing container image..."
az acr build --registry $ACR_NAME --image pentest-ai:latest .

# Enable managed identity for the environment
print_status "Configuring managed identity..."
az containerapp env identity assign \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --system-assigned

# Get the managed identity
IDENTITY_ID=$(az containerapp env identity show \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --query principalId --output tsv)

# Grant Key Vault access
az keyvault set-policy \
    --name $KEYVAULT_NAME \
    --object-id $IDENTITY_ID \
    --secret-permissions get list

# Create secrets in Key Vault
print_status "Creating secrets in Key Vault..."
az keyvault secret set \
    --vault-name $KEYVAULT_NAME \
    --name "mongodb-uri" \
    --value "mongodb://admin:secure_password_123@mongodb:27017/crewai_pentest?authSource=admin"

az keyvault secret set \
    --vault-name $KEYVAULT_NAME \
    --name "api-secret-key" \
    --value "your-secret-api-key-$(date +%s)"

az keyvault secret set \
    --vault-name $KEYVAULT_NAME \
    --name "mongo-root-password" \
    --value "secure_password_123"

# Deploy MongoDB
print_status "Deploying MongoDB container app..."
az containerapp create \
    --name mongodb \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image mongo:7.0 \
    --target-port 27017 \
    --ingress 'internal' \
    --cpu 1.0 \
    --memory 2Gi \
    --min-replicas 1 \
    --max-replicas 1 \
    --env-vars \
        MONGO_INITDB_ROOT_USERNAME=admin \
        MONGO_INITDB_DATABASE=crewai_pentest \
    --secrets \
        mongo-root-password=keyvaultref:https://$KEYVAULT_NAME.vault.azure.net/secrets/mongo-root-password,identityref:system \
    --secret-env-vars \
        MONGO_INITDB_ROOT_PASSWORD=mongo-root-password

# Deploy Ollama
print_status "Deploying Ollama container app..."
az containerapp create \
    --name ollama-ai \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image ollama/ollama:latest \
    --target-port 11434 \
    --ingress 'internal' \
    --cpu 2.0 \
    --memory 4Gi \
    --min-replicas 1 \
    --max-replicas 3 \
    --env-vars \
        OLLAMA_HOST=0.0.0.0

# Deploy Main PenTest AI App
print_status "Deploying PenTest AI container app..."
az containerapp create \
    --name pentest-ai \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image $ACR_NAME.azurecr.io/pentest-ai:latest \
    --target-port 8000 \
    --ingress 'external' \
    --registry-server $ACR_NAME.azurecr.io \
    --registry-identity system \
    --cpu 1.0 \
    --memory 2Gi \
    --min-replicas 0 \
    --max-replicas 10 \
    --env-vars \
        ENVIRONMENT=production \
        PYTHONPATH=/app \
        OLLAMA_HOST=http://ollama-ai \
    --secrets \
        mongodb-uri=keyvaultref:https://$KEYVAULT_NAME.vault.azure.net/secrets/mongodb-uri,identityref:system \
        api-secret-key=keyvaultref:https://$KEYVAULT_NAME.vault.azure.net/secrets/api-secret-key,identityref:system \
    --secret-env-vars \
        MONGODB_URI=mongodb-uri \
        API_SECRET_KEY=api-secret-key

# Get the application URL
APP_URL=$(az containerapp show \
    --name pentest-ai \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

print_success "✅ Deployment completed successfully!"
echo ""
echo "🌐 Application URL: https://$APP_URL"
echo "📊 Azure Portal: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP"
echo ""
echo "🔍 Test your deployment:"
echo "  curl https://$APP_URL/health"
echo "  curl https://$APP_URL/docs"
echo ""
```

## 📦 Step 7: Advanced Container Apps Features

### Dapr Integration for Service Discovery

```yaml
# dapr-components.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.azure.cosmosdb
  version: v1
  metadata:
  - name: url
    value: https://your-cosmosdb.documents.azure.com
  - name: masterKey
    secretKeyRef:
      name: cosmosdb-key
---
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.azure.servicebus
  version: v1
  metadata:
  - name: connectionString
    secretKeyRef:
      name: servicebus-connectionstring
```

### Traffic Splitting for Blue/Green Deployments

```bash
# Deploy new version with traffic splitting
az containerapp revision copy \
    --name pentest-ai \
    --resource-group $RESOURCE_GROUP \
    --from-revision pentest-ai--{old-revision} \
    --image $ACR_NAME.azurecr.io/pentest-ai:v2

# Split traffic 50/50 between versions
az containerapp ingress traffic set \
    --name pentest-ai \
    --resource-group $RESOURCE_GROUP \
    --revision-weight pentest-ai--{old-revision}=50 pentest-ai--{new-revision}=50
```

### Auto-scaling Configuration

```bash
# Configure advanced scaling rules
az containerapp update \
    --name pentest-ai \
    --resource-group $RESOURCE_GROUP \
    --scale-rule-name "cpu-scaling" \
    --scale-rule-type "cpu" \
    --scale-rule-metadata "type=Utilization" "value=70" \
    --scale-rule-auth "triggerParameter=value"

# Add HTTP-based scaling
az containerapp update \
    --name pentest-ai \
    --resource-group $RESOURCE_GROUP \
    --scale-rule-name "http-scaling" \
    --scale-rule-type "http" \
    --scale-rule-metadata "concurrentRequests=100"
```

## 📊 Monitoring and Logging

### Container Apps Monitoring

```bash
# Enable Application Insights
az monitor app-insights component create \
    --app pentest-ai-insights \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP

# Configure Container App to use Application Insights
INSIGHTS_KEY=$(az monitor app-insights component show \
    --app pentest-ai-insights \
    --resource-group $RESOURCE_GROUP \
    --query instrumentationKey --output tsv)

az containerapp update \
    --name pentest-ai \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars APPINSIGHTS_INSTRUMENTATIONKEY=$INSIGHTS_KEY
```

### Log Queries

```kusto
// Container Apps logs
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "pentest-ai"
| where TimeGenerated > ago(1h)
| project TimeGenerated, Log_s, ContainerName_s

// System metrics
ContainerAppSystemLogs_CL
| where ContainerAppName_s == "pentest-ai"
| summarize avg(CpuUsage), avg(MemoryUsage) by bin(TimeGenerated, 5m)
```

## 💰 Cost Optimization

### Container Apps Pricing Benefits

- **Pay per use**: No charges when scaled to zero
- **vCPU-second billing**: Pay only for compute time used
- **Shared infrastructure**: Lower overhead costs
- **Auto-scaling**: Optimize resource usage

### Cost Estimation

```bash
# Basic tier (0.5 vCPU, 1GB RAM, 100 requests/day)
# ~$15-30/month

# Standard tier (1 vCPU, 2GB RAM, 1000 requests/day)
# ~$50-100/month

# Production tier (2 vCPU, 4GB RAM, 10000 requests/day)
# ~$150-300/month
```

## 🔧 Testing Container Apps Deployment

### Health Check Scripts

```bash
#!/bin/bash
# test-containerapp.sh

APP_URL="https://pentest-ai.{random-string}.{location}.azurecontainerapps.io"

echo "🔍 Testing Container App deployment..."

# Test health endpoint
echo "Testing health endpoint..."
curl -f "$APP_URL/health" || exit 1

# Test API documentation
echo "Testing API docs..."
curl -f "$APP_URL/docs" || exit 1

# Test AI guidance
echo "Testing AI guidance..."
curl -X POST "$APP_URL/ai-guidance/next-task" \
  -H "Content-Type: application/json" \
  -d '{"target":"example.com","current_phase":"reconnaissance"}' || exit 1

echo "✅ All tests passed!"
```

## 🚀 Advantages of Container Apps vs App Service

| Feature | Container Apps | App Service |
|---------|----------------|-------------|
| **Scaling** | Scale to zero | Minimum 1 instance |
| **Pricing** | Pay per use | Fixed pricing |
| **Multi-container** | Native support | Limited |
| **Service discovery** | Built-in Dapr | Manual setup |
| **Traffic splitting** | Built-in | Requires slots |
| **Microservices** | Optimized | Monolith focused |

## 🎯 Next Steps

1. **Run Deployment**: Execute the complete deployment script
2. **Configure Secrets**: Update Key Vault with your actual values
3. **Test Scaling**: Verify auto-scaling behavior
4. **Set up CI/CD**: Configure GitHub Actions for automated deployments
5. **Monitor Performance**: Set up alerts and dashboards

Container Apps provides the perfect serverless container platform for your AI-guided penetration testing system! 🚀
