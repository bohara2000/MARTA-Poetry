param location string = 'eastus'
param resourceGroupName string = 'MartaPoetryRG'

module appService './app-service.bicep' = {
  name: 'deployAppService'
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

module openAi './openai-service.bicep' = {
  name: 'deployOpenAI'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}

module storage './storage.bicep' = {
  name: 'deployStorage'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}

module functions './functions.bicep' = {
  name: 'deployFunctions'
  scope: resourceGroup(resourceGroupName)
  params: {
    location: location
  }
}
