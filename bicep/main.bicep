// This Bicep file orchestrates the deployment of multiple resources including Storage Account, App Service, and Cosmos DB.

@description('The location where the resources will be deployed.')
param location string = 'eastus'

@description('The name of the resource group where the resources will be deployed.')
param resourceGroupName string = 'MartaPoetryRG'

module storage './storage.bicep' = {
  name: 'deployStorage'
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
  dependsOn: [appService] // Ensure the app service is deployed before the functions
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

module openAi './openai-service.bicep' = {
  name: 'deployOpenAI'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}


