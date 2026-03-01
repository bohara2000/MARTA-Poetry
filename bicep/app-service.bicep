// This Bicep file deploys an App Service Plan and an App Service.

@description('The location where the resources will be deployed.')
param location string

@description('The name of the App Service Plan.')
param appServicePlanName string = 'marta-poetry-plan-linux'

@description('The name of the App Service.')
param appServiceName string = 'marta-poetry-app'

resource appServicePlan 'Microsoft.Web/serverfarms@2021-02-01' = {
  name: appServicePlanName
  location: location
  kind: 'linux'
  properties: {
    reserved: true
  }
  sku: {
    tier: 'Basic'
    name: 'B1'
  }
}

resource appService 'Microsoft.Web/sites@2021-02-01' = {
  name: appServiceName
  location: location
  kind: 'app,linux'
  properties: {
    serverFarmId: appServicePlan.id
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'gunicorn -w 2 -k uvicorn.workers.UvicornWorker app:app'
      alwaysOn: true
    }
  }
}

resource appServiceAppSettings 'Microsoft.Web/sites/config@2021-02-01' = {
  name: 'appsettings'
  parent: appService
  properties: {
    SCM_DO_BUILD_DURING_DEPLOYMENT: 'true'
    ENABLE_ORYX_BUILD: 'true'
    WEBSITES_PORT: '8000'
  }
}
output appServiceName string = appService.name
output appServiceId string = appService.id
output appServiceUrl string = 'https://${appService.properties.defaultHostName}'