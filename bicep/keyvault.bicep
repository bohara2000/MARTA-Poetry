// This Bicep file deploys an Azure Key Vault for securely storing secrets.

@description('The location where the resources will be deployed.')
param location string

@description('The name of the Key Vault.')
param keyVaultName string = 'martakeyvault'

@description('The object ID of the service principal or user who will have access to the Key Vault.')
param objectId string

@description('Cosmos DB Account resource ID.')
param cosmosDbResourceId string

@description('Cosmos DB Account name.')
param cosmosDbAccountName string

@description('Cosmos DB endpoint.')
param cosmosDbEndpoint string

@description('Storage Account resource ID.')
param storageAccountResourceId string

@description('Storage Account name.')
param storageAccountName string

var uniqueKeyVaultName = take(toLower('${keyVaultName}-${uniqueString(resourceGroup().id)}'), 24)

// Reference existing resources to retrieve keys securely
resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2021-06-15' existing = {
  name: cosmosDbAccountName
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2021-09-01' existing = {
  name: storageAccountName
}

resource keyVault 'Microsoft.KeyVault/vaults@2021-06-01-preview' = {
  name: uniqueKeyVaultName
  location: location
  properties: {
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: false
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: objectId
        permissions: {
          keys: [
            'get'
            'list'
          ]
          secrets: [
            'get'
            'list'
            'set'
            'delete'
          ]
          certificates: [
            'get'
            'list'
          ]
        }
      }
    ]
  }
}

resource cosmosDbConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: keyVault
  name: 'CosmosDbConnectionString'
  properties: {
    value: 'AccountEndpoint=${cosmosDbEndpoint};AccountKey=${cosmosDbAccount.listKeys().primaryMasterKey};'
  }
}

resource storageAccountConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: keyVault
  name: 'StorageAccountConnectionString'
  properties: {
    value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
  }
}

resource cosmosDbEndpointSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: keyVault
  name: 'CosmosDbEndpoint'
  properties: {
    value: cosmosDbEndpoint
  }
}

resource cosmosDbKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: keyVault
  name: 'CosmosDbKey'
  properties: {
    value: cosmosDbAccount.listKeys().primaryMasterKey
  }
}

resource storageAccountNameSecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: keyVault
  name: 'StorageAccountName'
  properties: {
    value: storageAccountName
  }
}

resource storageAccountKeySecret 'Microsoft.KeyVault/vaults/secrets@2021-06-01-preview' = {
  parent: keyVault
  name: 'StorageAccountKey'
  properties: {
    value: storageAccount.listKeys().keys[0].value
  }
}

@description('Output the Key Vault name.')
output keyVaultName string = keyVault.name

@description('Output the Key Vault URI.')
output keyVaultUri string = keyVault.properties.vaultUri
