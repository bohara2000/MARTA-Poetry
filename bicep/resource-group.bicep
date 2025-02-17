// This Bicep file creates a resource group in Azure

targetScope = 'subscription'

@description('The location where the resources will be deployed.')
param location string = 'eastus'

@description('The name of the resource group where the resources will be deployed.')
param resourceGroupName string = 'MartaPoetryRG'

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
}
