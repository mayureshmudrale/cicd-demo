output "network_id" {
  value = aws_vpc.this.id
}

# Only private subnets are part of the cross-cloud contract. The cluster
# module places EKS (control plane ENIs + worker nodes) entirely in these —
# a private-only cluster is the secure default here, consistent with the
# database_never_public invariant; the public subnets above exist only for
# this module's own NAT gateway and are never exposed past it.
output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

# Not part of the cross-cloud contract (gcp/local have no equivalent) —
# exposed so the live/aws root can wire the database module's CIDR-based
# `allowed_from` without that module needing its own subnet-id variable.
output "private_subnet_cidrs" {
  value = aws_subnet.private[*].cidr_block
}
