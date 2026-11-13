variable "name" {
  description = "Cluster name"
  type        = string
}

variable "tier" {
  description = "Size tier: small, medium, or large (used only for labeling here — node_type/node_count below carry the actual sizing)"
  type        = string
}

variable "network_id" {
  description = "VPC id from the network module"
  type        = string
}

variable "private_subnet_ids" {
  description = "Subnet id(s) from the network module — GKE uses element 0; a single regional subnetwork covers the whole cluster"
  type        = list(string)
}

variable "region" {
  description = "GCP region; the cluster itself runs zonal (region + \"-a\") to avoid GKE's default regional behavior of tripling node count across all zones"
  type        = string
}

variable "node_type" {
  description = "GCE machine type for worker nodes, e.g. module.tiers.node_type"
  type        = string
  default     = "e2-medium"
}

variable "node_count" {
  description = "Number of worker nodes, e.g. module.tiers.node_count"
  type        = number
  default     = 2
}

variable "kubernetes_version" {
  description = "GKE Kubernetes version (\"latest\" lets GKE pick its current default)"
  type        = string
  default     = "latest"
}
