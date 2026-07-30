terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # All backend config is injected via -backend-config flags in infra.yml.
  backend "azurerm" {}
}

provider "azurerm" {
  subscription_id = var.subscription_id
  features {}
}

data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}
