#!/bin/bash

# Azure Deployment Script for AI-Guided Penetration Testing System
# Usage: ./deploy-azure.sh

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Modify these values as needed
RESOURCE_GROUP="pentest-ai-rg"
LOCATION="eastus"
ACR_NAME="pentestairegistry$(date +%s)"  # Add timestamp to ensure uniqueness
APP_SERVICE_PLAN="pentest-ai-plan"
APP_SERVICE_NAME="pentest-ai-app-$(date +%s)"  # Add timestamp to ensure uniqueness
KEYVAULT_NAME="pentest-ai-kv-$(date +%s)"  # Add timestamp to ensure uniqueness
CONTAINER_GROUP="ollama-container-group"
STORAGE_ACCOUNT="pentestaistorage$(date +%s)"

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

# Function to check if Azure CLI is installed and logged in
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

# Function to create Azure Container Registry
create_container_registry() {
    print_status "Creating Azure Container Registry: $ACR_NAME"
    
    az acr create --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true \
        --output none
    
    print_success "Container registry created successfully"
    
    # Get ACR login server
    ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
    print_status "ACR Login Server: $ACR_LOGIN_SERVER"
}

# Function to build and push Docker image
build_and_push_image() {
    print_status "Building and pushing Docker image to ACR..."
    
    # Build and push the image using ACR build
    az acr build --registry $ACR_NAME --image pentest-ai:latest . --output table
    
    print_success "Docker image built and pushed successfully"
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

# Function to create storage account for logs and data
create_storage_account() {
    print_status "Creating storage account: $STORAGE_ACCOUNT"
    
    az storage account create --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --output none
    
    print_success "Storage account created successfully"
}

# Function to create Ollama container instance
create_ollama_container() {
    print_status "Creating Ollama container instance..."
    
    az container create --resource-group $RESOURCE_GROUP \
        --name $CONTAINER_GROUP \
        --image ollama/ollama:latest \
        --ports 11434 \
        --protocol TCP \
        --cpu 2 \
        --memory 4 \
        --environment-variables OLLAMA_HOST=0.0.0.0 \
        --dns-name-label pentest-ollama-$(date +%s) \
        --restart-policy Always \
        --output table
    
    # Get the FQDN of the container
    OLLAMA_FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_GROUP --query ipAddress.fqdn --output tsv)
    print_success "Ollama container created at: http://$OLLAMA_FQDN:11434"
}

# Function to create App Service Plan
create_app_service_plan() {
    print_status "Creating App Service Plan: $APP_SERVICE_PLAN"
    
    az appservice plan create --name $APP_SERVICE_PLAN \
        --resource-group $RESOURCE_GROUP \
        --is-linux \
        --sku B2 \
        --output none
    
    print_success "App Service Plan created successfully"
}

# Function to create App Service
create_app_service() {
    print_status "Creating App Service: $APP_SERVICE_NAME"
    
    # Get ACR credentials
    ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)
    
    # Create the web app
    az webapp create --resource-group $RESOURCE_GROUP \
        --plan $APP_SERVICE_PLAN \
        --name $APP_SERVICE_NAME \
        --deployment-container-image-name $ACR_LOGIN_SERVER/pentest-ai:latest \
        --output none
    
    # Configure container settings
    az webapp config container set --name $APP_SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --docker-custom-image-name $ACR_LOGIN_SERVER/pentest-ai:latest \
        --docker-registry-server-url https://$ACR_LOGIN_SERVER \
        --docker-registry-server-user $ACR_USERNAME \
        --docker-registry-server-password $ACR_PASSWORD \
        --output none
    
    print_success "App Service created successfully"
}

# Function to configure App Service settings
configure_app_service() {
    print_status "Configuring App Service settings..."
    
    # Enable managed identity
    PRINCIPAL_ID=$(az webapp identity assign --name $APP_SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --query principalId --output tsv)
    
    # Grant Key Vault access to the managed identity
    az keyvault set-policy --name $KEYVAULT_NAME \
        --object-id $PRINCIPAL_ID \
        --secret-permissions get list \
        --output none
    
    # Configure app settings
    az webapp config appsettings set --name $APP_SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --settings \
        WEBSITES_PORT=8000 \
        AZURE_KEYVAULT_URL="https://$KEYVAULT_NAME.vault.azure.net/" \
        OLLAMA_HOST="http://$OLLAMA_FQDN:11434" \
        ENVIRONMENT="production" \
        PYTHONPATH="/app" \
        --output none
    
    print_success "App Service configured successfully"
}

# Function to set up Application Insights
setup_application_insights() {
    print_status "Setting up Application Insights..."
    
    # Install Application Insights extension if not already installed
    az extension add --name application-insights --output none 2>/dev/null || true
    
    # Create Application Insights resource
    APPINSIGHTS_KEY=$(az monitor app-insights component create \
        --app $APP_SERVICE_NAME-insights \
        --location $LOCATION \
        --resource-group $RESOURCE_GROUP \
        --query instrumentationKey --output tsv)
    
    # Add Application Insights key to app settings
    az webapp config appsettings set --name $APP_SERVICE_NAME \
        --resource-group $RESOURCE_GROUP \
        --settings APPINSIGHTS_INSTRUMENTATIONKEY=$APPINSIGHTS_KEY \
        --output none
    
    print_success "Application Insights configured successfully"
}

# Function to create sample secrets in Key Vault
create_sample_secrets() {
    print_status "Creating sample secrets in Key Vault..."
    
    # Note: Replace these with your actual values
    print_warning "Please update these secrets with your actual values:"
    print_warning "1. MongoDB URI"
    print_warning "2. API Keys"
    print_warning "3. Other sensitive configuration"
    
    # Create placeholder secrets
    az keyvault secret set --vault-name $KEYVAULT_NAME \
        --name 'mongodb-uri' \
        --value 'mongodb+srv://username:password@cluster.mongodb.net/crewai_pentest' \
        --output none
    
    az keyvault secret set --vault-name $KEYVAULT_NAME \
        --name 'api-secret-key' \
        --value 'your-secret-api-key-here' \
        --output none
    
    print_success "Sample secrets created (please update with real values)"
}

# Function to restart App Service to apply new configuration
restart_app_service() {
    print_status "Restarting App Service to apply configuration..."
    
    az webapp restart --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP --output none
    
    print_success "App Service restarted successfully"
}

# Function to display deployment summary
display_summary() {
    echo ""
    echo "==================================================================================="
    print_success "🚀 AZURE DEPLOYMENT COMPLETED SUCCESSFULLY! 🚀"
    echo "==================================================================================="
    echo ""
    echo "📋 Deployment Summary:"
    echo "  • Resource Group: $RESOURCE_GROUP"
    echo "  • Location: $LOCATION"
    echo "  • Container Registry: $ACR_NAME"
    echo "  • App Service: $APP_SERVICE_NAME"
    echo "  • Key Vault: $KEYVAULT_NAME"
    echo "  • Storage Account: $STORAGE_ACCOUNT"
    echo ""
    echo "🌐 Application URLs:"
    echo "  • Main Application: https://$APP_SERVICE_NAME.azurewebsites.net"
    echo "  • Health Check: https://$APP_SERVICE_NAME.azurewebsites.net/health"
    echo "  • API Docs: https://$APP_SERVICE_NAME.azurewebsites.net/docs"
    echo "  • Ollama Service: http://$OLLAMA_FQDN:11434"
    echo ""
    echo "🔐 Key Vault:"
    echo "  • Name: $KEYVAULT_NAME"
    echo "  • URL: https://$KEYVAULT_NAME.vault.azure.net/"
    echo ""
    echo "📊 Monitoring:"
    echo "  • Application Insights: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/microsoft.insights/components/$APP_SERVICE_NAME-insights"
    echo ""
    echo "🔧 Next Steps:"
    echo "  1. Update MongoDB URI in Key Vault:"
    echo "     az keyvault secret set --vault-name $KEYVAULT_NAME --name 'mongodb-uri' --value 'your-actual-mongodb-uri'"
    echo ""
    echo "  2. Test the deployment:"
    echo "     curl https://$APP_SERVICE_NAME.azurewebsites.net/health"
    echo ""
    echo "  3. Access Azure Portal to monitor resources:"
    echo "     https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP"
    echo ""
    echo "==================================================================================="
}

# Main deployment function
main() {
    echo "🚀 Starting Azure deployment for AI-Guided Penetration Testing System"
    echo "==================================================================================="
    
    check_prerequisites
    create_resource_group
    create_container_registry
    create_storage_account
    create_key_vault
    build_and_push_image
    create_ollama_container
    create_app_service_plan
    create_app_service
    configure_app_service
    setup_application_insights
    create_sample_secrets
    restart_app_service
    display_summary
}

# Error handling
trap 'print_error "Deployment failed! Check the error messages above."; exit 1' ERR

# Run main function
main

print_success "Deployment script completed! 🎉"
