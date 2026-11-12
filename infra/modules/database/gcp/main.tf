# Cloud SQL private IP requires a reserved CIDR range peered into the VPC
# — the GCP equivalent of RDS' db subnet group, though the mechanism
# (service networking peering, not subnet membership) is quite different.
resource "google_compute_global_address" "private_ip" {
  name          = "${var.name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.network_id
}

resource "google_service_networking_connection" "this" {
  network                 = var.network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip.name]
}

resource "random_password" "master" {
  length  = 32
  special = false
}

resource "google_sql_database_instance" "this" {
  name             = var.name
  database_version = var.database_version
  region           = var.region

  settings {
    tier              = var.db_class
    availability_type = var.ha ? "REGIONAL" : "ZONAL"
    disk_size         = var.storage_gb

    ip_configuration {
      ipv4_enabled    = false # database_never_public: no public IP at all, not just a closed firewall
      private_network = var.network_id
    }
  }

  deletion_protection = false # POC default; a real deployment should drop this

  depends_on = [google_service_networking_connection.this]
}

resource "google_sql_database" "this" {
  name     = "ideaboard"
  instance = google_sql_database_instance.this.name
}

resource "google_sql_user" "this" {
  name     = "ideaboard"
  instance = google_sql_database_instance.this.name
  password = random_password.master.result
}
