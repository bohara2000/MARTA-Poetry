param location string
param functionAppName string = 'marta-poetry-functions'

resource functionApp 'Microsoft.Web/sites@2021-02-01' = {
  name: functionAppName
  location: location
  properties: {
    serverFarmId: resourceId('Microsoft.Web/serverfarms', functionAppName)
  }
}
