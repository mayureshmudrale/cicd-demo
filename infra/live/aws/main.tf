# Thin root: network -> cluster -> database -> platform, same four-step
# wiring as infra/live/local, same module contract (variables.tf/outputs.tf
# identical in shape to the gcp/local backends) — everything cloud-specific
# is confined to the modules/*/aws implementations this root calls into.

module "network" {
  source = "../../modules/network/aws"
  name   = "idea-board"
  region = var.region
}

module "tiers" {
  source = "../../modules/tiers"
  cloud  = "aws"
  tier   = var.tier
}

module "cluster" {
  source = "../../modules/cluster/aws"

  name               = "idea-board"
  tier               = var.tier
  network_id         = module.network.network_id
  private_subnet_ids = module.network.private_subnet_ids
  node_type          = module.tiers.node_type
  node_count         = module.tiers.node_count
}

module "database" {
  source = "../../modules/database/aws"

  name         = "idea-board"
  tier         = var.tier
  network_id   = module.network.network_id
  allowed_from = module.network.private_subnet_cidrs
  db_class     = module.tiers.db_class
  ha           = module.tiers.db_ha

  depends_on = [module.cluster]
}

module "platform" {
  source = "../../platform"

  ingress_service_type = "LoadBalancer"
  ingress_annotations  = module.cluster.ingress_annotations
  ai_evaluator_image   = var.ai_evaluator_image
  gemini_api_key       = var.gemini_api_key

  depends_on = [module.cluster]
}
