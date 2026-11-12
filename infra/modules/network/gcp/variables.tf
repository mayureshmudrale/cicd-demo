variable "name" {
  description = "Logical network name, used as a prefix for every resource this module creates"
  type        = string
}

variable "region" {
  description = "GCP region, e.g. us-central1"
  type        = string
}

variable "cidr" {
  description = "Primary subnet CIDR (GKE node IPs)"
  type        = string
  default     = "10.0.0.0/20"
}

variable "pods_cidr" {
  description = "Secondary range for GKE pod IPs (VPC-native cluster)"
  type        = string
  default     = "10.16.0.0/14"
}

variable "services_cidr" {
  description = "Secondary range for GKE service IPs (VPC-native cluster)"
  type        = string
  default     = "10.20.0.0/20"
}
