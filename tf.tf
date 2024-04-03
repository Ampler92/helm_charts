resource "azurerm_resource_group" "example" {
  name     = "example-resources"
  location = "West Europe"
}

resource "azurerm_user_assigned_identity" "example" {
  name                = "example-uai"
  location            = azurerm_resource_group.example.location
  resource_group_name = azurerm_resource_group.example.name
}

resource "azurerm_resource_deployment_script_azure_power_shell" "example" {
  name                = "example-rdsaps"
  resource_group_name = azurerm_resource_group.example.name
  location            = "West Europe"
  version             = "8.3"
  retention_interval  = "P1D"
  command_line        = "-apiServer \"https://api.ocpazrs02.cloud.internal:6443\" -namespace \"014981-comcdservices01-prd\" -podName \"gcp-service-5b8967958b-kbq89\" -Token \"sha256~FHnPxn5HFfwC2GgyAyjb6tc4EU7tej13n2Yo370c8vc\""
  cleanup_preference  = "OnSuccess"
  force_update_tag    = "1"
  timeout             = "PT30M"
  
  script_content = <<EOF
param(
    [string] \$apiServer,
    [string] \$namespace,
    [string] \$podName,
    [string] \$Token
)
\$apiUrl = "\$apiServer/api/v1/namespaces/\$namespace/pods/\$podName/log?follow=true&container=gcp-service"

# Set up the header with the authorization token
\$headers = @{
    Authorization = "Bearer \$Token"
}

curl -ks -X GET "\$apiUrl" -H "Authorization: Bearer \$Token"
EOF

  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.example.id
    ]
  }

  tags = {
    key = "value"
  }
}