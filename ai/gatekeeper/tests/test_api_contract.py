from ai.gatekeeper.api_contract import analyze

BEFORE = {
    "paths": {
        "/ideas": {"get": {}, "post": {}},
        "/ideas/{id}/upvote": {"post": {}},
    },
    "components": {
        "schemas": {
            "IdeaOut": {
                "properties": {"id": {}, "text": {}, "votes": {}},
                "required": ["id", "text"],
            }
        }
    },
}


def test_identical_schema_has_no_findings():
    assert analyze(BEFORE, BEFORE) == []


def test_removed_route_is_flagged():
    after = {**BEFORE, "paths": {"/ideas": {"get": {}, "post": {}}}}
    findings = analyze(BEFORE, after)
    assert any(f.location == "POST /ideas/{id}/upvote" for f in findings)
    assert all(f.severity == "high" for f in findings if f.source == "api_contract")


def test_removed_field_is_flagged():
    after = {
        **BEFORE,
        "components": {
            "schemas": {
                "IdeaOut": {
                    "properties": {"id": {}, "text": {}},
                    "required": ["id", "text"],
                }
            }
        },
    }
    findings = analyze(BEFORE, after)
    assert any(f.location == "IdeaOut.votes" and f.severity == "high" for f in findings)


def test_newly_required_field_is_flagged():
    after = {
        **BEFORE,
        "components": {
            "schemas": {
                "IdeaOut": {
                    "properties": {"id": {}, "text": {}, "votes": {}},
                    "required": ["id", "text", "votes"],
                }
            }
        },
    }
    findings = analyze(BEFORE, after)
    assert any(f.location == "IdeaOut.votes" and f.severity == "medium" for f in findings)
