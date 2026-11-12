from ai.gatekeeper.migration_risk import analyze


def test_not_null_without_default_is_flagged():
    sql = "ALTER TABLE ideas ADD COLUMN urgent boolean NOT NULL;"
    findings = analyze(sql)
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert "urgent" in findings[0].location


def test_not_null_with_default_is_safe():
    sql = "ALTER TABLE ideas ADD COLUMN urgent boolean NOT NULL DEFAULT false;"
    assert analyze(sql) == []


def test_create_index_without_concurrently_is_flagged():
    sql = "CREATE INDEX idx_ideas_votes ON ideas (votes);"
    findings = analyze(sql)
    assert any(f.severity == "medium" for f in findings)


def test_create_index_concurrently_is_safe():
    sql = "CREATE INDEX CONCURRENTLY idx_ideas_votes ON ideas (votes);"
    assert analyze(sql) == []


def test_foreign_key_without_index_is_flagged():
    sql = "ALTER TABLE comments ADD COLUMN idea_id integer REFERENCES ideas(id);"
    findings = analyze(sql)
    assert any(f.severity == "low" and "idea_id" in f.location for f in findings)


def test_foreign_key_with_index_is_safe():
    sql = (
        "ALTER TABLE comments ADD COLUMN idea_id integer REFERENCES ideas(id);\n"
        "CREATE INDEX CONCURRENTLY idx_comments_idea_id ON comments (idea_id);"
    )
    findings = analyze(sql)
    assert not any("no supporting index" in f.reason for f in findings)
