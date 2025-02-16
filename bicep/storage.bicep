param location string
param storageAccountPrefix string = 'martastorage'

var uniqueStorageAccountName = toLower('${storageAccountPrefix}${uniqueString(resourceGroup().id)}')

resource storage 'Microsoft.Storage/storageAccounts@2021-09-01' = {
  name: uniqueStorageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}
