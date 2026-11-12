.PHONY: apply-local destroy-local fmt smoke-ai

CLOUD ?= local

apply-local:
	touch infra/live/local/.kubeconfig-cloud-a infra/live/local/.kubeconfig-cloud-b
	chmod 600 infra/live/local/.kubeconfig-cloud-a infra/live/local/.kubeconfig-cloud-b
	terraform -chdir=infra/live/local init
	# Phase 1: clusters only, so the kubernetes/kubectl provider aliases are
	# absent from this apply's graph and never get configured against the
	# still-empty placeholder kubeconfig files.
	terraform -chdir=infra/live/local apply \
		-target=module.cluster_a -target=module.cluster_b
	# kind (re)writes these with default (world-readable) permissions; they
	# hold cluster-admin client certs, so lock them down immediately after.
	chmod 600 infra/live/local/.kubeconfig-cloud-a infra/live/local/.kubeconfig-cloud-b
	# Phase 2: everything else, now that the kubeconfig files hold real
	# content from before this second apply even starts.
	terraform -chdir=infra/live/local apply

destroy-local:
	terraform -chdir=infra/live/local destroy

fmt:
	terraform fmt -recursive infra/

smoke-ai:
	python -m ai.smoke_test
