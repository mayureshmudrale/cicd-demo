import subprocess

import pytest

from ai.selfheal.commit import commit_to_branch
from ai.selfheal.schemas import FileEdit, HealResult


@pytest.fixture
def repo(tmp_path):
    # A real bare "origin" remote, not just a local repo: commit_to_branch
    # must push for real, since a CI runner's checkout is ephemeral and
    # gh pr create needs the branch to already exist on the remote.
    remote = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)

    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", str(work)], check=True)
    subprocess.run(["git", "config", "user.email", "t@t.local"], cwd=work, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=work, check=True)
    subprocess.run(["git", "remote", "add", "origin", str(remote)], cwd=work, check=True)
    (work / "a.py").write_text("x = 0\n")
    subprocess.run(["git", "add", "a.py"], cwd=work, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=work, check=True)
    subprocess.run(["git", "push", "-q", "origin", "HEAD:main"], cwd=work, check=True)
    return work


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


def test_pushes_branch_to_origin(repo):
    """A CI runner's checkout is ephemeral - the branch must exist on
    origin for `gh pr create --head` to find it afterward."""
    result = HealResult(
        fixed=True, safety_passed=True, explanation="fix it", edits=[FileEdit(path="a.py", new_content="x = 1\n")]
    )
    commit_to_branch(repo, "heal/test-3", result)

    remote_branches = subprocess.run(
        ["git", "ls-remote", "--heads", "origin"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    assert "heal/test-3" in remote_branches
