import subprocess
import sys

import pytest

from ai.selfheal.apply import apply_and_verify
from ai.selfheal.schemas import FileEdit, PatchProposal

CHECK_NO_BROKEN = [
    sys.executable,
    "-c",
    "import sys; sys.exit(1 if 'BROKEN' in open('a.py').read() else 0)",
]


@pytest.fixture
def repo(tmp_path):
    """A tiny real git repo with one committed file containing 'BROKEN' —
    isolated to tmp_path, never the real project repo."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.local"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    (tmp_path / "a.py").write_text("x = BROKEN\n")
    subprocess.run(["git", "add", "a.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=tmp_path, check=True)
    return tmp_path


def test_verified_fix_reports_healed(repo):
    proposal = PatchProposal(explanation="fix it", edits=[FileEdit(path="a.py", new_content="x = 1\n")])
    result = apply_and_verify(repo, proposal, fix_command=CHECK_NO_BROKEN, safety_command=None, cwd_relative=".")
    assert result.healed
    assert result.edits == proposal.edits


def test_bad_fix_is_not_reported_as_healed(repo):
    proposal = PatchProposal(explanation="oops", edits=[FileEdit(path="a.py", new_content="x = BROKEN still\n")])
    result = apply_and_verify(repo, proposal, fix_command=CHECK_NO_BROKEN, safety_command=None, cwd_relative=".")
    assert not result.healed
    assert result.edits == []


def test_fix_that_breaks_safety_net_is_not_healed(repo):
    break_safety = [sys.executable, "-c", "import sys; sys.exit(1)"]
    proposal = PatchProposal(explanation="fix it", edits=[FileEdit(path="a.py", new_content="x = 1\n")])
    result = apply_and_verify(
        repo, proposal, fix_command=CHECK_NO_BROKEN, safety_command=break_safety, cwd_relative="."
    )
    assert result.fixed
    assert not result.safety_passed
    assert not result.healed
    assert result.edits == []


def test_live_repo_is_never_modified(repo):
    before = (repo / "a.py").read_text()
    proposal = PatchProposal(explanation="fix it", edits=[FileEdit(path="a.py", new_content="x = 1\n")])
    apply_and_verify(repo, proposal, fix_command=CHECK_NO_BROKEN, safety_command=None, cwd_relative=".")
    after = (repo / "a.py").read_text()
    assert before == after
