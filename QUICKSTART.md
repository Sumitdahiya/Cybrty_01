# Quick Start Guide for Azure Deployment

## 🚀 Local Development with Docker

### 1. Clone and Setup
```bash
git clone <your-repo>
cd Cyrty_01
cp .env.docker .env
```

### 2. Run with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# Check logs
docker-compose logs -f pentest-ai
```

### 3. Access Services
- **Main API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MongoDB Express**: http://localhost:8081 (admin/admin)
- **Ollama**: http://localhost:11434

## ☁️ Azure Container Apps Deployment

### Prerequisites
1. Install Azure CLI: `brew install azure-cli` (macOS)
2. Login to Azure: `az login`
3. Set up MongoDB Atlas account

### Quick Azure Container Apps Deployment
```bash
# Make script executable
chmod +x deploy-container-apps.sh

# Run deployment
./deploy-container-apps.sh
```

### Manual Azure Container Apps Deployment Steps

#### 1. Set Variables
```bash
RESOURCE_GROUP="pentest-ai-rg"
LOCATION="eastus"
ACR_NAME="pentestairegistry$(date +%s)"
CONTAINERAPPS_ENVIRONMENT="pentest-ai-env"
APP_NAME="pentest-ai-app"
```

#### 2. Create Resources
```bash
# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create container registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Build and push image
az acr build --registry $ACR_NAME --image pentest-ai:latest .
```

#### 3. Deploy Container Apps
```bash
# Install Container Apps extension
az extension add --name containerapp --upgrade

# Create Container Apps environment
az containerapp env create --name $CONTAINERAPPS_ENVIRONMENT --resource-group $RESOURCE_GROUP --location $LOCATION

# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Create container app
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $CONTAINERAPPS_ENVIRONMENT \
  --image $ACR_LOGIN_SERVER/pentest-ai:latest \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 10
```

#### 4. Configure Settings
```bash
# Set environment variables
az containerapp update --name $APP_NAME --resource-group $RESOURCE_GROUP \
  --set-env-vars MONGODB_URI="your-mongodb-uri" OLLAMA_HOST="http://localhost:11434"
```

## 🗄️ Database Setup

### Option 1: MongoDB Atlas (Recommended)
1. Go to https://cloud.mongodb.com
2. Create free cluster
3. Add your Azure app IP to network access
4. Create database user
5. Get connection string
6. Add to Azure Key Vault or app settings

### Option 2: Azure Cosmos DB
```bash
az cosmosdb create --resource-group $RESOURCE_GROUP --name pentest-cosmosdb --kind MongoDB --default-consistency-level Session
```

## 🤖 AI Model Setup

### Option 1: Azure Container Instances
```bash
az container create --resource-group $RESOURCE_GROUP --name ollama-instance --image ollama/ollama:latest --ports 11434 --cpu 2 --memory 4 --dns-name-label pentest-ollama-$(date +%s)
```

### Option 2: External Service
- Use Ollama Cloud or hosted service
- Update `OLLAMA_HOST` environment variable

## 🔍 Testing Deployment

### Health Check
```bash
curl https://your-app.azurecontainerapps.io/health
```

### API Test
```bash
curl -X POST "https://your-app.azurecontainerapps.io/ai-guidance/next-task" -H "Content-Type: application/json" -d '{"target":"example.com","current_phase":"reconnaissance"}'
```

## 📊 Monitoring

### Application Insights
```bash
# Enable Application Insights for Container Apps
az monitor app-insights component create --app $APP_NAME-insights --location $LOCATION --resource-group $RESOURCE_GROUP
```

### View Logs
```bash
# Azure CLI
az containerapp logs show --name $APP_NAME --resource-group $RESOURCE_GROUP --follow

# Or in Azure Portal
# Go to Container Apps > Log stream
```

## 💰 Cost Estimation

### Development Environment (Scale-to-Zero)
- **Container Apps**: $0 when not in use
- **Container Registry Basic**: ~$5/month
- **Log Analytics Workspace**: ~$3/month
- **Total**: ~$8/month (minimal when idle)

### Production Environment
- **Container Apps**: ~$30-50/month (based on usage)
- **Container Registry Standard**: ~$20/month
- **Log Analytics Workspace**: ~$10/month
- **Application Insights**: ~$10/month
- **Total**: ~$70-90/month

## 🔧 Troubleshooting

### Common Issues

#### 1. Container Not Starting
```bash
# Check logs
az containerapp logs show --name $APP_NAME --resource-group $RESOURCE_GROUP --follow

# Check container app status
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.provisioningState"
```

#### 2. Database Connection Issues
```bash
# Test MongoDB connection
curl https://your-app.azurecontainerapps.io/health

# Check environment variables
az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query "properties.template.containers[0].env"
```

#### 3. Ollama Not Accessible
```bash
# Check if Ollama container is running in the same environment
az containerapp list --resource-group $RESOURCE_GROUP --environment $CONTAINERAPPS_ENVIRONMENT

# Test Ollama endpoint (if deployed separately)
curl http://ollama-app.azurecontainerapps.io:11434/api/version
```

### Performance Optimization

#### 1. Configure Scaling Rules
```bash
# Set HTTP scaling rule
az containerapp update --name $APP_NAME --resource-group $RESOURCE_GROUP \
  --scale-rule-name http-rule \
  --scale-rule-http-concurrency 50 \
  --min-replicas 0 \
  --max-replicas 10
```

#### 2. Configure Resource Limits
```bash
# Set CPU and memory limits
az containerapp update --name $APP_NAME --resource-group $RESOURCE_GROUP \
  --cpu 1.0 \
  --memory 2.0Gi
```

#### 3. Enable Ingress
```bash
# Configure external ingress
az containerapp ingress enable --name $APP_NAME --resource-group $RESOURCE_GROUP \
  --type external \
  --target-port 8000 \
  --allow-insecure
```

## 📚 Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Docker Multi-stage Builds](https://docs.docker.com/develop/dev-best-practices/dockerfile_best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [MongoDB Atlas on Azure](https://www.mongodb.com/cloud/atlas/azure)

## 🎯 Next Steps

1. **Security Hardening**
   - Configure Azure WAF
   - Set up SSL certificates
   - Enable authentication

2. **CI/CD Pipeline**
   - Azure DevOps integration
   - GitHub Actions
   - Automated testing

3. **Monitoring Enhancement**
   - Custom metrics
   - Alerting rules
   - Performance dashboards

4. **Backup Strategy**
   - Database backups
   - Container image versioning
   - Disaster recovery plan
