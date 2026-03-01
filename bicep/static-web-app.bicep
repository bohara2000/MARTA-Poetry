param location string = resourceGroup().location
param appName string = 'marta-poetry-frontend'
param repositoryUrl string = ''
param repositoryToken string = ''
param repositoryBranch string = 'main'
param appServiceUrl string = 'https://marta-poetry-app.azurewebsites.net'

// Static Web App for frontend
resource staticWebApp 'Microsoft.Web/staticSites@2023-12-01' = {
  name: appName
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {
    repositoryUrl: repositoryUrl
    branch: repositoryBranch
    repositoryToken: repositoryToken
    buildProperties: {
      apiLocation: ''
      appLocation: 'frontend'
      appBuildCommand: 'npm run build'
      outputLocation: 'dist'
    }
  }
}

// App settings with API endpoint
resource staticWebAppConfig 'Microsoft.Web/staticSites/config@2023-12-01' = {
  parent: staticWebApp
  name: 'appsettings'
  properties: {
    VITE_API_URL: appServiceUrl
  }
}

output staticWebAppUrl string = staticWebApp.properties.defaultHostname
output staticWebAppId string = staticWebApp.id
