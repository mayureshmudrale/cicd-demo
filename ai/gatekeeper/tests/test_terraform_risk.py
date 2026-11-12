from ai.gatekeeper.terraform_risk import analyze


def _change(resource_type, address, actions, after=None, before=None):
    return {
        "address": address,
        "type": resource_type,
        "change": {"actions": actions, "after": after, "before": before},
    }


def test_no_op_produces_no_findings():
    plan = {"resource_changes": [_change("kind_cluster", "module.cluster_a.kind_cluster.this", ["no-op"])]}
    assert analyze(plan) == []


def test_plain_delete_on_stateful_resource_is_critical():
    # Mirrors this repo's own database/local/main.tf: a CNPG Cluster CRD
    # applied via the generic `kubectl_manifest` type — only the address
    # ("postgres_cluster") reveals what it actually manages.
    plan = {
        "resource_changes": [
            _change(
                "kubectl_manifest",
                "module.database_a.kubectl_manifest.postgres_cluster",
                ["delete"],
                before={"kind": "Cluster"},
            )
        ]
    }
    findings = analyze(plan)
    assert len(findings) == 1
    assert findings[0].severity == "critical"


def test_replace_on_non_stateful_resource_is_medium():
    plan = {
        "resource_changes": [
            _change(
                "kubernetes_config_map",
                "module.platform.kubernetes_config_map.settings",
                ["delete", "create"],
                after={},
            )
        ]
    }
    findings = analyze(plan)
    assert len(findings) == 1
    assert findings[0].severity == "medium"


def test_public_cidr_is_flagged():
    plan = {
        "resource_changes": [
            _change(
                "kubernetes_network_policy",
                "module.platform.netpol",
                ["create"],
                after={"spec": {"ingress": [{"from": [{"ipBlock": {"cidr": "0.0.0.0/0"}}]}]}},
            )
        ]
    }
    findings = analyze(plan)
    assert any("0.0.0.0/0" in f.reason for f in findings)


def test_wildcard_rbac_verb_is_flagged():
    plan = {
        "resource_changes": [
            _change(
                "kubernetes_role",
                "module.platform.role",
                ["create"],
                after={"rule": [{"verbs": "*", "resources": "pods"}]},
            )
        ]
    }
    findings = analyze(plan)
    assert any("wildcard" in f.reason for f in findings)
