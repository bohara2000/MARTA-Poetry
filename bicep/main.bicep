// This Bicep file orchestrates the deployment of multiple resources including Storage Account, App Service, Cosmos DB, and Key Vault.

@description('The location where the resources will be deployed.')
param location string = 'eastus'

@description('The name of the resource group where the resources will be deployed.')
param resourceGroupName string = 'MartaPoetryRG'

@description('The object ID of the service principal or user who will have access to the Key Vault.')
param keyVaultObjectId string

@description('Whether to deploy a new Azure OpenAI resource as part of this deployment. Set to true if this project should create and manage its own Azure OpenAI instance. Leave as false when you are using an existing AI Foundry (Azure AI Studio) project or shared Azure OpenAI resource to avoid creating duplicate or conflicting resources.')
param deployOpenAi bool = false

module storage './storage.bicep' = {
  name: 'deployStorage'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}

module cosmosDB './cosmosdb.bicep' = {
  name: 'deployCosmosDB'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}

module appService './app-service.bicep' = {
  name: 'deployAppService'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}

module functions './functions.bicep' = {
  name: 'deployFunctions'
  scope: resourceGroup(resourceGroupName)
  dependsOn: [appService]
  params: {
    location: location
  }
}

module openAi './openai-service.bicep' = if (deployOpenAi) {
  name: 'deployOpenAI'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}

module keyVault './keyvault.bicep' = {
  name: 'deployKeyVault'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
    objectId: keyVaultObjectId
    cosmosDbResourceId: cosmosDB.outputs.cosmosDbResourceId
    cosmosDbAccountName: cosmosDB.outputs.cosmosDbAccountName
    cosmosDbEndpoint: cosmosDB.outputs.cosmosDbEndpoint
    storageAccountResourceId: storage.outputs.storageAccountResourceId
    storageAccountName: storage.outputs.storageAccountName
  }
}


