// Define parameters
param location string = 'eastus'
param appServiceName string = 'marta-poetry-app'
param storageAccountName string = 'martastorage'
param cosmosDbAccountName string = 'martadb'
param openAiName string = 'marta-openai'
param speechServiceName string = 'marta-speech'

// Resource Group
resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: 'MartaPoetryRG'
  location: location
}

// Web App (App Service)
resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: appServiceName
  location: location
  properties: {
    serverFarmId: resourceId('Microsoft.Web/serverfarms', appServiceName)
  }
}

// Storage Account
resource storage 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}

// Cosmos DB
resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2021-06-15' = {
  name: cosmosDbAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
  }
}

// Azure OpenAI Service
resource openAi 'Microsoft.CognitiveServices/accounts@2021-10-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
    tier: 'Standard'
  }
}

// Azure Speech Service
resource speech 'Microsoft.CognitiveServices/accounts@2021-10-01' = {
  name: speechServiceName
  location: location
  kind: 'SpeechServices'
  sku: {
    name: 'S0'
    tier: 'Standard'
  }
}

// Output results
output webAppUrl string = 'https://${appServiceName}.azurewebsites.net'
