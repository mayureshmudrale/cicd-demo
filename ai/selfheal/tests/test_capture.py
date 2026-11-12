from ai.selfheal.capture import extract_implicated_files

RUFF_OUTPUT = "app/backend/main.py:10:5: F401 'os' imported but unused"
TRACEBACK_OUTPUT = """Traceback (most recent call last):
  File "/repo/app/backend/tests/test_main.py", line 7, in test_x
    assert add(1, 2) == 4
AssertionError
"""


def test_finds_linter_style_file(tmp_path):
    (tmp_path / "app" / "backend").mkdir(parents=True)
    (tmp_path / "app" / "backend" / "main.py").write_text("import os\n")

    files = extract_implicated_files(RUFF_OUTPUT, repo_root=tmp_path, search_root=tmp_path)
    assert "app/backend/main.py" in files
    assert files["app/backend/main.py"] == "import os\n"


def test_finds_ruff_full_format_arrow_style_file(tmp_path):
    (tmp_path / "a.py").write_text("import os\n")
    output = f" --> {tmp_path / 'a.py'}:1:8\n  |\n1 | import os\n"

    files = extract_implicated_files(output, repo_root=tmp_path, search_root=tmp_path)
    assert "a.py" in files


def test_finds_traceback_style_file(tmp_path):
    (tmp_path / "app" / "backend" / "tests").mkdir(parents=True)
    test_file = tmp_path / "app" / "backend" / "tests" / "test_main.py"
    test_file.write_text("def test_x(): pass\n")

    output = TRACEBACK_OUTPUT.replace("/repo/app", str(tmp_path / "app"))
    files = extract_implicated_files(output, repo_root=tmp_path, search_root=tmp_path)
    assert "app/backend/tests/test_main.py" in files


def test_ignores_paths_outside_repo_root(tmp_path, monkeypatch):
    outside = tmp_path.parent / "outside.py"
    outside.write_text("x = 1\n")
    output = f'File "{outside}", line 1'

    files = extract_implicated_files(output, repo_root=tmp_path, search_root=tmp_path)
    assert files == {}


def test_nonexistent_file_is_skipped(tmp_path):
    files = extract_implicated_files(RUFF_OUTPUT, repo_root=tmp_path, search_root=tmp_path)
    assert files == {}
