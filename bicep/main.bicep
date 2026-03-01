// This Bicep file orchestrates the deployment of multiple resources including Storage Account, App Service, Cosmos DB, and Key Vault.

@description('The location where the resources will be deployed.')
param location string = 'eastus'

@description('The name of the resource group where the resources will be deployed.')
param resourceGroupName string = 'MartaPoetryRG'

@description('The object ID of the service principal or user who will have access to the Key Vault.')
param keyVaultObjectId string

@description('GitHub repository URL for Static Web App (for CI/CD). Leave empty to deploy manually.')
param githubRepoUrl string = ''

@description('GitHub personal access token for Static Web App (required if githubRepoUrl is provided).')
param githubToken string = ''

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

module staticWebApp './static-web-app.bicep' = {
  name: 'deployStaticWebApp'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
    repositoryUrl: githubRepoUrl
    repositoryToken: githubToken
    appServiceUrl: 'https://${appService.outputs.appServiceName}.azurewebsites.net'
  }
}

output storageAccountName string = storage.outputs.storageAccountName
output appServiceUrl string = 'https://${appService.outputs.appServiceName}.azurewebsites.net'
output staticWebAppUrl string = staticWebApp.outputs.staticWebAppUrl
