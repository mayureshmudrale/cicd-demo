variable "name" {
  description = "Cluster name"
  type        = string
}

variable "tier" {
  description = "Size tier: small, medium, or large (used only for tagging here — node_type/node_count below carry the actual sizing, same as the local backend's own split)"
  type        = string
}

variable "network_id" {
  description = "VPC id from the network module"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet ids from the network module — EKS control plane ENIs and worker nodes both live entirely here"
  type        = list(string)
}

variable "node_type" {
  description = "EC2 instance type for worker nodes, e.g. module.tiers.node_type"
  type        = string
  default     = "t3.medium"
}

variable "node_count" {
  description = "Number of worker nodes, e.g. module.tiers.node_count"
  type        = number
  default     = 2
}

variable "kubernetes_version" {
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.31"
}
