param location string
param appServicePlanName string = 'marta-poetry-plan'
param appServiceName string = 'marta-poetry-app'

resource appServicePlan 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: appServicePlanName
  location: location
  sku: {
    tier: 'Basic'
    name: 'B1'
  }
}

resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: appServiceName
  location: location
  properties: {
    serverFarmId: appServicePlan.id
  }
}
