param location string
param openAiName string = 'marta-openai'

resource openAi 'Microsoft.CognitiveServices/accounts@2021-10-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
    tier: 'Standard'
  }
}
