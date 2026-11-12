from ai.reviewmem.diffsplit import split_into_hunks

SAMPLE_DIFF = """diff --git a/app/backend/main.py b/app/backend/main.py
index 1111111..2222222 100644
--- a/app/backend/main.py
+++ b/app/backend/main.py
@@ -10,3 +10,5 @@ def healthz():
     return {"status": "ok"}
+
+def new_route():
+    pass
diff --git a/app/backend/faults.py b/app/backend/faults.py
index 3333333..4444444 100644
--- a/app/backend/faults.py
+++ b/app/backend/faults.py
@@ -5,2 +5,2 @@ def _fault_none():
-    pass
+    return None
"""


def test_splits_two_hunks_across_two_files():
    hunks = split_into_hunks(SAMPLE_DIFF)
    assert len(hunks) == 2
    assert hunks[0][0].startswith("app/backend/main.py")
    assert hunks[1][0].startswith("app/backend/faults.py")


def test_hunk_body_contains_added_lines():
    hunks = split_into_hunks(SAMPLE_DIFF)
    assert "def new_route():" in hunks[0][1]


def test_empty_diff_produces_no_hunks():
    assert split_into_hunks("") == []
