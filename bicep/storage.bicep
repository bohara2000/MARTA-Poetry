// This Bicep file deploys a Storage Account with blob container for audio files.

@description('The location where the resources will be deployed.')
param location string

@description('The prefix for the Storage Account name.')
param storageAccountPrefix string = 'martastorage'

@description('The name of the blob container for audio files.')
param audioBlobContainerName string = 'audio'

var uniqueStorageAccountName = take(toLower('${storageAccountPrefix}${uniqueString(resourceGroup().id)}'),24)

resource storage 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: uniqueStorageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2021-09-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

resource audioContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2021-09-01' = {
  parent: blobService
  name: audioBlobContainerName
  properties: {
    publicAccess: 'None'
  }
}

@description('Output the storage account name.')
output storageAccountName string = storage.name

@description('Output the storage account primary endpoint.')
output blobEndpoint string = storage.properties.primaryEndpoints.blob

@description('Output the audio container name.')
output audioContainerName string = audioContainer.name

@description('Output the storage account resource ID for Key Vault to reference.')
output storageAccountResourceId string = storage.id
