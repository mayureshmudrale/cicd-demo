# Proposed defaults — confirm against current pricing/quotas before any cloud apply.
locals {
  tiers = {
    small = {
      aws   = { node_type = "t3.medium", node_count = 2, db_class = "db.t4g.micro", db_ha = false }
      gcp   = { node_type = "e2-medium", node_count = 2, db_class = "db-f1-micro", db_ha = false }
      local = { node_type = "kind-node", node_count = 1, db_class = "shared", db_ha = false }
    }
    medium = {
      aws   = { node_type = "t3.large", node_count = 2, db_class = "db.t4g.small", db_ha = false }
      gcp   = { node_type = "e2-standard-2", node_count = 2, db_class = "db-g1-small", db_ha = false }
      local = { node_type = "kind-node", node_count = 2, db_class = "shared", db_ha = false }
    }
    large = {
      aws   = { node_type = "m5.large", node_count = 3, db_class = "db.m5.large", db_ha = true }
      gcp   = { node_type = "e2-standard-4", node_count = 3, db_class = "db-custom-2-7680", db_ha = true }
      local = { node_type = "kind-node", node_count = 3, db_class = "shared", db_ha = false }
    }
  }

  selected = local.tiers[var.tier][var.cloud]
}
