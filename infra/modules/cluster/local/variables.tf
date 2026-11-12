variable "name" {
  description = "Cluster name"
  type        = string
}

variable "tier" {
  description = "Size tier: small, medium, or large"
  type        = string
}

variable "network_id" {
  description = "Unused on the local backend; accepted for contract parity"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Unused on the local backend; accepted for contract parity"
  type        = list(string)
  default     = []
}

variable "node_count" {
  description = "Number of worker nodes (in addition to the single control-plane node)"
  type        = number
  default     = 1
}

variable "install_cilium" {
  description = "Whether to disable kind's default CNI and install Cilium instead"
  type        = bool
  default     = true
}

variable "kubeconfig_path" {
  description = "Where kind writes this cluster's kubeconfig. Fixed (not computed) so the root's helm/kubernetes/kubectl providers can point at it without a provider-config dependency cycle."
  type        = string
}
