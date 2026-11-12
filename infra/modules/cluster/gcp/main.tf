data "google_client_config" "this" {}

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

# node_config/remove_default_node_pool: GKE always creates a default pool
# alongside the cluster resource itself; removing it and defining the
# "this" pool below separately is the standard way to control its machine
# type/count/service account instead of inheriting GKE's own defaults.
resource "google_container_cluster" "this" {
  name     = var.name
  location = var.region

  network    = var.network_id
  subnetwork = var.private_subnet_ids[0]

  remove_default_node_pool = true
  initial_node_count       = 0 # GKE's current guidance: 0 avoids even transiently creating the default pool we're about to remove

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
  location = var.region

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
