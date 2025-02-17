// This Bicep file deploys an OpenAI Service.

@description('The location where the resources will be deployed. OpenAI is available in specific regions.')
param location string = 'eastus'

@description('The name of the OpenAI Service.')
param openAiName string = 'marta-openai'


resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
    tier: 'Standard'
  }
  properties: {
    publicNetworkAccess: 'Enabled'  // Allows public access
    encryption: {
      keySource: 'Microsoft.CognitiveServices'
    }
  }
}
