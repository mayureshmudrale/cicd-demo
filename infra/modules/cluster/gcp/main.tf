data "google_client_config" "this" {}

# Zonal, not regional: a regional cluster (location = a region) spreads its
# default node pool across every zone in that region automatically, so
# node_count nodes becomes node_count * 3 actual nodes with zero visible
# warning - confirmed live (quota exhaustion on a trial project surfaced
# it, but it would have silently tripled node cost on a real account too).
# Single-zone is the right default for this tier; multi-zone HA is a
# deliberate upgrade a real deployment should opt into, not inherit free.
locals {
  zone = "${var.region}-a"
}

resource "google_service_account" "node" {
  account_id   = "${var.name}-gke-node"
  display_name = "GKE nodes for ${var.name}"
}

resource "google_project_iam_member" "node" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/artifactregistry.reader",
  ])
  project = data.google_client_config.this.project
  role    = each.value
  member  = "serviceAccount:${google_service_account.node.email}"
}

# initial_node_count = 0, remove_default_node_pool left at its false
# default: with 0, GKE never creates a default pool in the first place
# (confirmed live - remove_default_node_pool = true here 404s trying to
# delete a pool that was never created), so there's nothing to remove.
# The "this" pool below is defined separately either way, to control its
# machine type/count/service account instead of inheriting GKE's defaults.
resource "google_container_cluster" "this" {
  name     = var.name
  location = local.zone

  network    = var.network_id
  subnetwork = var.private_subnet_ids[0]

  initial_node_count = 0

  # POC default, same documented posture as database/gcp's Cloud SQL
  # instance: a real deployment should drop this and let destroys be
  # deliberate. Without it the provider's own default (true, as of recent
  # versions) blocks any replace/destroy - confirmed live.
  deletion_protection = false

  min_master_version = var.kubernetes_version == "latest" ? null : var.kubernetes_version

  networking_mode = "VPC_NATIVE"
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false # keep the control-plane API reachable from this Terraform run / CI, same posture as the AWS module
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  workload_identity_config {
    workload_pool = "${data.google_client_config.this.project}.svc.id.goog"
  }
}

resource "google_container_node_pool" "this" {
  name     = "${var.name}-default"
  cluster  = google_container_cluster.this.id
  location = local.zone

  node_count = var.node_count

  node_config {
    machine_type    = var.node_type
    service_account = google_service_account.node.email
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }
}
