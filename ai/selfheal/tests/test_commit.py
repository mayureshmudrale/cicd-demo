import subprocess

import pytest

from ai.selfheal.commit import commit_to_branch
from ai.selfheal.schemas import FileEdit, HealResult


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.local"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "a.py").write_text("x = 0\n")
    subprocess.run(["git", "add", "a.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=tmp_path, check=True)
    return tmp_path


def _current_branch(repo_root):
    return subprocess.run(
        ["git", "branch", "--show-current"], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_creates_branch_with_commit(repo):
    result = HealResult(
        fixed=True, safety_passed=True, explanation="fix it", edits=[FileEdit(path="a.py", new_content="x = 1\n")]
    )
    commit_to_branch(repo, "heal/test-1", result)

    branches = subprocess.run(["git", "branch"], cwd=repo, capture_output=True, text=True, check=True).stdout
    assert "heal/test-1" in branches


def test_never_checks_out_the_new_branch_in_the_caller_repo(repo):
    starting_branch = _current_branch(repo)
    result = HealResult(
        fixed=True, safety_passed=True, explanation="fix it", edits=[FileEdit(path="a.py", new_content="x = 1\n")]
    )
    commit_to_branch(repo, "heal/test-2", result)
    assert _current_branch(repo) == starting_branch
    assert (repo / "a.py").read_text() == "x = 0\n"
