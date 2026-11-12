variable "name" {
  description = "Database identifier"
  type        = string
}

variable "tier" {
  description = "Size tier: small, medium, or large (used only for tagging here — db_class/ha below carry the actual sizing)"
  type        = string
}

variable "network_id" {
  description = "VPC id from the network module; the private subnets this module needs are looked up from here via their Access=private tag"
  type        = string
}

variable "allowed_from" {
  description = "CIDR blocks allowed to reach Postgres (5432) — pass the VPC/private-subnet CIDR(s), never 0.0.0.0/0; database_never_public is an enforced invariant, not just a default"
  type        = list(string)
  default     = []
}

variable "db_class" {
  description = "RDS instance class, e.g. module.tiers.db_class"
  type        = string
  default     = "db.t4g.micro"
}

variable "ha" {
  description = "Whether to enable Multi-AZ, e.g. module.tiers.db_ha"
  type        = bool
  default     = false
}

variable "storage_gb" {
  description = "Allocated storage, in GB"
  type        = number
  default     = 20
}

variable "engine_version" {
  type    = string
  default = "16"
}
