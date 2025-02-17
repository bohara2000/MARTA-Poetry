// This Bicep file deploys an App Service Plan and an App Service.

@description('The location where the resources will be deployed.')
param location string

@description('The name of the App Service Plan.')
param appServicePlanName string = 'marta-poetry-plan'

@description('The name of the App Service.')
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
