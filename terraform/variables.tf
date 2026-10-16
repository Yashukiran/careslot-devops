variable "region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-south-1"
}

variable "owner" {
  description = "Tag value so it's obvious who created the resources"
  type        = string
  default     = "yashukiran"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "careslot-eks"
}

variable "kubernetes_version" {
  description = "EKS control plane version - keep it on a version in standard support (extended support costs extra)"
  type        = string
  default     = "1.35"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "node_instance_types" {
  description = "Instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "github_repository" {
  description = "owner/repo allowed to deploy to the cluster from GitHub Actions"
  type        = string
  default     = "Yashukiran/careslot-devops"
}

variable "create_github_oidc_provider" {
  description = "Set to false if the account already has the token.actions.githubusercontent.com OIDC provider"
  type        = bool
  default     = true
}
