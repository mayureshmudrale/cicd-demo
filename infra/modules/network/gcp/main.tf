resource "google_compute_network" "this" {
  name                    = var.name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "this" {
  name          = var.name
  network       = google_compute_network.this.id
  region        = var.region
  ip_cidr_range = var.cidr

  # VPC-native (alias IP) GKE needs these named secondary ranges; the
  # cluster module references them by name, not by CIDR.
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }

  # GKE's control plane needs flow logs' worth of visibility into node
  # traffic for some features; harmless default, not strictly required.
  log_config {
    aggregation_interval = "INTERVAL_10_MIN"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# A custom-mode VPC has no implicit allow rules at all (unlike AWS'
# same-security-group default) — node-to-node and pod-to-pod traffic both
# need this explicitly, scoped to just this subnet's own ranges.
resource "google_compute_firewall" "internal" {
  name    = "${var.name}-allow-internal"
  network = google_compute_network.this.id

  allow {
    protocol = "all"
  }

  source_ranges = [var.cidr, var.pods_cidr, var.services_cidr]
}

resource "google_compute_router" "this" {
  name    = var.name
  network = google_compute_network.this.id
  region  = var.region
}

# GKE nodes here get no public IP (private cluster); Cloud NAT is their
# only path to the internet (image pulls, GCP API calls) — the GCP
# equivalent of the AWS module's single NAT gateway, same tradeoff.
resource "google_compute_router_nat" "this" {
  name                               = var.name
  router                             = google_compute_router.this.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}
