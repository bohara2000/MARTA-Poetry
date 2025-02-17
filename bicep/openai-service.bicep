param location string = 'eastus'  // OpenAI is available in specific regions
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
