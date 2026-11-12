output "network_id" {
  value = google_compute_network.this.id
}

# GCP subnets aren't carved per-AZ the way AWS's are — one regional
# subnetwork spans all zones in the region, so there's exactly one id
# here. The contract just asks for a list; a single-element one still
# satisfies any `for_each`/`count` on the consumer side.
output "private_subnet_ids" {
  value = [google_compute_subnetwork.this.id]
}
