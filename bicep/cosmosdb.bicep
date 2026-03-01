// This Bicep file deploys a Cosmos DB Account with database and containers.

@description('The location where the resources will be deployed.')
param location string

@description('The name of the Cosmos DB Account.')
param cosmosDbAccountName string = 'martadb'

@description('The name of the Cosmos DB Database.')
param databaseName string = 'PoetryDatabase'

@description('Throughput for the database (RU/s).')
param databaseThroughput int = 400

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
    enableAutomaticFailover: false
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2021-06-15' = {
  parent: cosmosDb
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
    options: {
      throughput: databaseThroughput
    }
  }
}

resource poemsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-06-15' = {
  parent: database
  name: 'poems'
  properties: {
    resource: {
      id: 'poems'
      partitionKey: {
        paths: [
          '/type'
        ]
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

resource routesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-06-15' = {
  parent: database
  name: 'routes'
  properties: {
    resource: {
      id: 'routes'
      partitionKey: {
        paths: [
          '/type'
        ]
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

resource personalitiesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-06-15' = {
  parent: database
  name: 'personalities'
  properties: {
    resource: {
      id: 'personalities'
      partitionKey: {
        paths: [
          '/type'
        ]
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

resource graphContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2021-06-15' = {
  parent: database
  name: 'graph'
  properties: {
    resource: {
      id: 'graph'
      partitionKey: {
        paths: [
          '/nodeType'
        ]
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        includedPaths: [
          {
            path: '/*'
          }
        ]
      }
    }
  }
}

@description('Output the Cosmos DB Account endpoint.')
output cosmosDbEndpoint string = cosmosDb.properties.documentEndpoint

@description('Output the database name.')
output databaseName string = database.name

@description('Output the Cosmos DB Account resource ID for Key Vault to reference.')
output cosmosDbResourceId string = cosmosDb.id

@description('Output the Cosmos DB Account name.')
output cosmosDbAccountName string = cosmosDb.name
