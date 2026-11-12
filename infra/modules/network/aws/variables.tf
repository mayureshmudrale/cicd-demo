variable "name" {
  description = "Logical network name, used as a prefix for every resource this module creates"
  type        = string
}

variable "region" {
  description = "AWS region, e.g. us-east-1"
  type        = string
}

variable "cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to spread subnets across (EKS and RDS both want >= 2)"
  type        = number
  default     = 2
}
