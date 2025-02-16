param location string
param appServiceName string = 'marta-poetry-app'

resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: appServiceName
  location: location
  properties: {
    serverFarmId: resourceId('Microsoft.Web/serverfarms', appServiceName)
  }
}
