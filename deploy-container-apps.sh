Actual tool response or# Azure Container Apps Complete Deployment Script
# Usage: ./deploy-container-apps.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Modify these values as needed
RESOURCE_GROUP="pentest-containerapps-rg"
LOCATION="eastus"
ENVIRONMENT_NAME="pentest-env"
ACR_NAME="pentestacr$(date +%s)"
LOG_ANALYTICS_WORKSPACE="pentest-logs"
KEYVAULT_NAME="pentest-kv-$(date +%s)"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        print_warning "Not logged into Azure. Initiating login..."
        az login
    fi
    
    # Install Container Apps extension
    print_status "Installing/updating Container Apps extension..."
    az extension add --name containerapp --upgrade --only-show-errors
    
    print_success "Prerequisites check completed"
}

# Function to create resource group
create_resource_group() {
    print_status "Creating resource group: $RESOURCE_GROUP"
    
    if az group create --name $RESOURCE_GROUP --location $LOCATION --output none; then
        print_success "Resource group created successfully"
    else
        print_error "Failed to create resource group"
        exit 1
    fi
}

# Function to create Key Vault
create_key_vault() {
    print_status "Creating Azure Key Vault: $KEYVAULT_NAME"
    
    az keyvault create --name $KEYVAULT_NAME \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
    
    print_success "Key Vault created successfully"
}

# Function to create Log Analytics workspace
create_log_analytics() {
    print_status "Creating Log Analytics workspace: $LOG_ANALYTICS_WORKSPACE"
    
    az monitor log-analytics workspace create \
        --resource-group $RESOURCE_GROUP \
        --workspace-name $LOG_ANALYTICS_WORKSPACE \
        --location $LOCATION \
        --output none
    
    print_success "Log Analytics workspace created successfully"
}

# Function to create Container Apps environment
create_container_apps_environment() {
    print_status "Creating Container Apps environment: $ENVIRONMENT_NAME"
    
    # Get Log Analytics workspace credentials
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
        --logs-workspace-key $LOG_ANALYTICS_WORKSPACE_KEY \
        --output none
    
    print_success "Container Apps environment created successfully"
}

# Function to create and configure Container Registry
create_container_registry() {
    print_status "Creating Azure Container Registry: $ACR_NAME"
    
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Standard \
        --admin-enabled true \
        --output none
    
    print_success "Container registry created successfully"
    
    # Build and push the image
    print_status "Building and pushing container image..."
    az acr build --registry $ACR_NAME --image pentest-ai:latest . --output table
    
    print_success "Container image built and pushed successfully"
}

# Function to configure managed identity and secrets
configure_identity_and_secrets() {
    print_status "Configuring managed identity and secrets..."
    
    # Enable managed identity for the environment
    az containerapp env identity assign \
        --name $ENVIRONMENT_NAME \
        --resource-group $RESOURCE_GROUP \
        --system-assigned \
        --output none
    
    # Get the managed identity principal ID
    IDENTITY_ID=$(az containerapp env identity show \
        --name $ENVIRONMENT_NAME \
        --resource-group $RESOURCE_GROUP \
        --query principalId --output tsv)
    
    # Grant Key Vault access to the managed identity
    az keyvault set-policy \
        --name $KEYVAULT_NAME \
        --object-id $IDENTITY_ID \
        --secret-permissions get list \
        --output none
    
    # Create secrets in Key Vault
    print_status "Creating secrets in Key Vault..."
    
    az keyvault secret set \
        --vault-name $KEYVAULT_NAME \
        --name "mongodb-uri" \
        --value "mongodb://admin:secure_password_123@mongodb:27017/crewai_pentest?authSource=admin" \
        --output none
    
    az keyvault secret set \
        --vault-name $KEYVAULT_NAME \
        --name "api-secret-key" \
        --value "pentest-api-key-$(date +%s)" \
        --output none
    
    az keyvault secret set \
        --vault-name $KEYVAULT_NAME \
        --name "mongo-root-password" \
        --value "secure_password_123" \
        --output none
    
    print_success "Managed identity and secrets configured successfully"
}

# Function to deploy MongoDB container app
deploy_mongodb() {
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
            MONGO_INITDB_ROOT_PASSWORD=mongo-root-password \
        --output none
    
    print_success "MongoDB container app deployed successfully"
}

# Function to deploy Ollama AI container app
deploy_ollama() {
    print_status "Deploying Ollama AI container app..."
    
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
            OLLAMA_HOST=0.0.0.0 \
        --output none
    
    print_success "Ollama AI container app deployed successfully"
}

# Function to deploy main PenTest AI container app
deploy_pentest_ai() {
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
            API_SECRET_KEY=api-secret-key \
        --output none
    
    print_success "PenTest AI container app deployed successfully"
}

# Function to configure Application Insights
setup_application_insights() {
    print_status "Setting up Application Insights..."
    
    # Create Application Insights resource
    INSIGHTS_KEY=$(az monitor app-insights component create \
        --app $ENVIRONMENT_NAME-insights \
        --location $LOCATION \
        --resource-group $RESOURCE_GROUP \
        --query instrumentationKey --output tsv)
    
    # Update container app with Application Insights
    az containerapp update \
        --name pentest-ai \
        --resource-group $RESOURCE_GROUP \
        --set-env-vars APPINSIGHTS_INSTRUMENTATIONKEY=$INSIGHTS_KEY \
        --output none
    
    print_success "Application Insights configured successfully"
}

# Function to configure scaling rules
configure_scaling() {
    print_status "Configuring auto-scaling rules..."
    
    # Configure HTTP-based scaling
    az containerapp update \
        --name pentest-ai \
        --resource-group $RESOURCE_GROUP \
        --scale-rule-name "http-scaling" \
        --scale-rule-type "http" \
        --scale-rule-metadata "concurrentRequests=50" \
        --output none
    
    print_success "Auto-scaling rules configured successfully"
}

# Function to display deployment summary
display_summary() {
    # Get the application URL
    APP_URL=$(az containerapp show \
        --name pentest-ai \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    echo ""
    echo "==================================================================================="
    print_success "🚀 AZURE CONTAINER APPS DEPLOYMENT COMPLETED! 🚀"
    echo "==================================================================================="
    echo ""
    echo "📋 Deployment Summary:"
    echo "  • Resource Group: $RESOURCE_GROUP"
    echo "  • Location: $LOCATION"
    echo "  • Environment: $ENVIRONMENT_NAME"
    echo "  • Container Registry: $ACR_NAME"
    echo "  • Key Vault: $KEYVAULT_NAME"
    echo ""
    echo "🌐 Application URLs:"
    echo "  • Main Application: https://$APP_URL"
    echo "  • Health Check: https://$APP_URL/health"
    echo "  • API Documentation: https://$APP_URL/docs"
    echo ""
    echo "📱 Container Apps:"
    echo "  • PenTest AI: pentest-ai (External ingress)"
    echo "  • Ollama AI: ollama-ai (Internal ingress)"
    echo "  • MongoDB: mongodb (Internal ingress)"
    echo ""
    echo "🔐 Security:"
    echo "  • Key Vault: https://$KEYVAULT_NAME.vault.azure.net/"
    echo "  • Managed Identity: Enabled for secure secret access"
    echo ""
    echo "📊 Monitoring:"
    echo "  • Log Analytics: $LOG_ANALYTICS_WORKSPACE"
    echo "  • Application Insights: $ENVIRONMENT_NAME-insights"
    echo "  • Azure Portal: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP"
    echo ""
    echo "🔍 Test Commands:"
    echo "  # Health check"
    echo "  curl https://$APP_URL/health"
    echo ""
    echo "  # API documentation"
    echo "  curl https://$APP_URL/docs"
    echo ""
    echo "  # AI-guided penetration test"
    echo "  curl -X POST \"https://$APP_URL/ai-guided-pentest\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"target\":\"example.com\"}'"
    echo ""
    echo "✨ Key Features Enabled:"
    echo "  • Serverless scaling (0-10 replicas)"
    echo "  • Auto-scaling based on HTTP requests"
    echo "  • Secure secret management with Key Vault"
    echo "  • Internal service discovery"
    echo "  • Comprehensive monitoring and logging"
    echo "  • All penetration testing tools included"
    echo ""
    echo "💡 Next Steps:"
    echo "  1. Test the deployment with the commands above"
    echo "  2. Configure CI/CD pipeline for automated deployments"
    echo "  3. Set up monitoring alerts"
    echo "  4. Update secrets in Key Vault with production values"
    echo ""
    echo "==================================================================================="
}

# Function to test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    APP_URL=$(az containerapp show \
        --name pentest-ai \
        --resource-group $RESOURCE_GROUP \
        --query properties.configuration.ingress.fqdn \
        --output tsv)
    
    # Wait for app to be ready
    print_status "Waiting for application to be ready..."
    sleep 30
    
    # Test health endpoint
    if curl -f "https://$APP_URL/health" --max-time 30 &> /dev/null; then
        print_success "Health check passed ✅"
    else
        print_warning "Health check failed - app may still be starting up"
    fi
    
    print_success "Basic deployment test completed"
}

# Main deployment function
main() {
    echo "🚀 Starting Azure Container Apps deployment for AI-Guided Penetration Testing System"
    echo "==================================================================================="
    
    check_prerequisites
    create_resource_group
    create_key_vault
    create_log_analytics
    create_container_apps_environment
    create_container_registry
    configure_identity_and_secrets
    deploy_mongodb
    deploy_ollama
    deploy_pentest_ai
    setup_application_insights
    configure_scaling
    test_deployment
    display_summary
}

# Error handling
trap 'print_error "Deployment failed! Check the error messages above."; exit 1' ERR

# Run main function
main

print_success "🎉 Azure Container Apps deployment completed successfully!"
