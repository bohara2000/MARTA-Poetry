// This Bicep file deploys a Cosmos DB Account.

@description('The location where the resources will be deployed.')
param location string

@description('The name of the Cosmos DB Account.')
param cosmosDbAccountName string = 'martadb'

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2021-06-15' = {
  name: cosmosDbAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    locations: [
      {
        locationName: location
        failoverPriority: 0
      }
    ]
  }
}
