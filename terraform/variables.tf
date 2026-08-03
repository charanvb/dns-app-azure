variable "subscription_id" {
  description = "Azure subscription ID for Foundation Services-01."
  type        = string
}

variable "resource_group_name" {
  description = "Existing resource group where all resources are created."
  type        = string
  default     = "bnlwe-fs01-n-00000-cloudbau-rg"
}

variable "acr_name" {
  description = "Azure Container Registry name (globally unique, alphanumeric only)."
  type        = string
  default     = "bnlwecloudbauacr01"
}

variable "container_app_env_name" {
  description = "Container Apps managed environment name."
  type        = string
  default     = "bnlwe-fs01-n-00000-dns-cae"
}

variable "container_app_name" {
  description = "Container App resource name."
  type        = string
  default     = "bnlwe-fs01-n-00000-dns-ca"
}

variable "initial_image" {
  description = "Placeholder image used only on first Terraform apply; replaced by CI."
  type        = string
  default     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}

variable "dns_subscription_id" {
  description = "Subscription ID containing the DNS zones."
  type        = string
  default     = "f5f0e79d-d6ab-43e4-b08c-60f2a53fd8be"
}

variable "dns_resource_group" {
  description = "Resource group containing the DNS zones."
  type        = string
  default     = "bnlwe-cc01-d-00000-mic-rg"
}
