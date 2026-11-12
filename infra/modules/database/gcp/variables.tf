variable "name" {
  description = "Database instance name"
  type        = string
}

variable "tier" {
  description = "Size tier: small, medium, or large (used only for labeling here — db_class/ha below carry the actual sizing)"
  type        = string
}

variable "network_id" {
  description = "VPC id from the network module — Cloud SQL gets a private IP via VPC peering into this network, never a public one"
  type        = string
}

variable "allowed_from" {
  description = "Unused on the GCP backend; accepted for contract parity. Cloud SQL private-IP access control is at the VPC-peering level (network_id), not a per-CIDR allowlist the way RDS' security group is — database_never_public is still enforced, just by a different mechanism (ipv4_enabled = false below, not a firewall rule)."
  type        = list(string)
  default     = []
}

variable "db_class" {
  description = "Cloud SQL tier, e.g. module.tiers.db_class"
  type        = string
  default     = "db-f1-micro"
}

variable "ha" {
  description = "Whether to enable regional (HA) availability, e.g. module.tiers.db_ha"
  type        = bool
  default     = false
}

variable "region" {
  type = string
}

variable "storage_gb" {
  type    = number
  default = 20
}

variable "database_version" {
  type    = string
  default = "POSTGRES_16"
}
