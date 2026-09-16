# T0 the branch-debt signals: a repo is a finding when work lives in only one place, and never
# otherwise. Zero-token, runs in verify-fast.
#
# The silences are the design, and one of them was wrong. A repo sitting on its own base has
# nothing open — that silence holds. A repo with **no** base branch was silent too, on the reading
# that it had nowhere to promote to and so no action was available; an audit on 2026-08-31 found
# code/obra sitting exactly there, 42 files on a lone feature branch with no remote, reporting
# clean. The action was always available and is the obvious one: give it a base. Silence about a
# repo that cannot promote is not the absence of debt, it is the absence of a question.
from branch_debt import (merged_local_branches, merged_remote_branches, unmerged_branches,
                         unpushed_work)

from vcs_repos import cloned, commit, git, repo  # noqa: F401 — pytest fixtures


def test_a_branch_ahead_of_its_base_is_a_finding(repo):
	git(repo, 'checkout', '-q', '-b', 'feature/x')
	commit(repo, 'work.txt')
	signal, = unmerged_branches(repo)
	assert 'feature/x' in signal and '1 ahead of main' in signal, signal


def test_a_branch_level_with_its_base_is_not(repo):
	"""Ahead-by-zero is the whole test — the same one `git branch -d` applies before refusing."""
	git(repo, 'checkout', '-q', '-b', 'feature/merged')
	assert unmerged_branches(repo) == []


def test_a_repo_on_its_own_base_is_not(repo):
	assert unmerged_branches(repo) == []


def test_master_counts_as_a_base(repo):
	"""branches/instituto is on master, and its branches deserve the same question."""
	git(repo, 'branch', '-m', 'main', 'master')
	git(repo, 'checkout', '-q', '-b', 'feature/y')
	commit(repo, 'work.txt')
	signal, = unmerged_branches(repo)
	assert 'ahead of master' in signal, signal


def test_a_repo_with_no_base_branch_is_the_finding(repo):
	"""The repo that cannot promote is the one most worth naming, not the one to stay quiet about."""
	git(repo, 'checkout', '-q', '-b', 'feature/z')
	commit(repo, 'work.txt')
	git(repo, 'branch', '-D', 'main')
	signal, = unmerged_branches(repo)
	assert 'no main/master/develop' in signal, signal


def test_a_remote_branch_already_in_base_is_offered_for_deletion(cloned):
	git(cloned, 'push', '-q', 'origin', 'main:refs/heads/feature/done')
	git(cloned, 'fetch', '-q', 'origin')
	signal, = merged_remote_branches(cloned)
	# The line must be the runnable action, not a description of one.
	assert 'push origin --delete feature/done' in signal, signal


def test_a_remote_branch_carrying_unmerged_work_is_left_alone(cloned):
	git(cloned, 'checkout', '-q', '-b', 'feature/live')
	commit(cloned, 'work.txt')
	git(cloned, 'push', '-q', 'origin', 'feature/live')
	git(cloned, 'fetch', '-q', 'origin')
	assert merged_remote_branches(cloned) == []


def test_a_repo_with_no_remote_is_silent(repo):
	"""Deleting nothing is not an action; a repo with no origin has nothing to offer."""
	assert merged_remote_branches(repo) == []


def test_a_repo_with_no_remote_holds_work_nowhere_else(repo):
	"""The push policy's own sentence, as a number — code/SPECS-git.md § Push policy."""
	signal, = unpushed_work(repo)
	assert 'no remote' in signal, signal


def test_a_branch_ahead_of_its_remote_is_unpushed(cloned):
	commit(cloned, 'work.txt')
	signal, = unpushed_work(cloned)
	assert '1 ahead of origin/main' in signal, signal


def test_a_clone_with_nothing_of_its_own_is_silent(cloned):
	assert unpushed_work(cloned) == []


def test_a_merged_local_branch_is_offered_for_deletion(cloned):
	git(cloned, 'branch', 'feature/done')
	signal, = merged_local_branches(cloned)
	# The line must be the runnable action, not a description of one.
	assert 'branch -d feature/done' in signal, signal


def test_the_branch_a_worktree_holds_is_never_offered(cloned):
	"""`git branch -d` refuses a checked-out branch, so offering it emits a command that fails."""
	git(cloned, 'checkout', '-q', '-b', 'feature/here')
	assert merged_local_branches(cloned) == []
