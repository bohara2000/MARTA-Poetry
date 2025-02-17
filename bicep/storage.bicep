// This Bicep file deploys a Storage Account.

@description('The location where the resources will be deployed.')
param location string

@description('The prefix for the Storage Account name.')
param storageAccountPrefix string = 'martastorage'

var uniqueStorageAccountName = take(toLower('${storageAccountPrefix}${uniqueString(resourceGroup().id)}'),24)

resource storage 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: uniqueStorageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}
