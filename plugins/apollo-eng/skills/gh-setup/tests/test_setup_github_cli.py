import setup_github_cli


def test_https_to_ssh_handles_github_remote():
    assert (
        setup_github_cli.https_to_ssh("https://github.com/apolloio/leadgenie.git")
        == "git@github.com:apolloio/leadgenie.git"
    )


def test_https_to_ssh_handles_url_without_git_suffix():
    assert (
        setup_github_cli.https_to_ssh("https://github.com/apolloio/leadgenie")
        == "git@github.com:apolloio/leadgenie.git"
    )


def test_https_to_ssh_ignores_non_github_urls():
    assert setup_github_cli.https_to_ssh("git@github.com:apolloio/leadgenie.git") == ""
    assert setup_github_cli.https_to_ssh("https://gitlab.com/apolloio/leadgenie.git") == ""


def test_render_report_nudges_ssh_and_gh_login():
    report = setup_github_cli.render_report(
        {
            "git_path": "/usr/bin/git",
            "gh_path": "",
            "gh_version": "",
            "gh_auth_ok": False,
            "gh_auth_detail": "not logged in",
            "user_name": "",
            "user_email": "dev@apollo.io",
            "default_branch": "",
            "pull_rebase": "",
            "ssh_keys": [],
            "https_remotes": [
                (
                    "origin",
                    "https://github.com/apolloio/leadgenie.git",
                    "git@github.com:apolloio/leadgenie.git",
                )
            ],
        }
    )

    assert "gh auth login --git-protocol ssh --web" in report
    assert "ssh-keygen -t ed25519 -C \"dev@apollo.io\"" in report
    assert "git remote set-url origin git@github.com:apolloio/leadgenie.git" in report


def test_set_git_config_if_needed_skips_matching_value(monkeypatch):
    calls = []

    monkeypatch.setattr(setup_github_cli, "git_config", lambda key: "main")
    monkeypatch.setattr(setup_github_cli, "run", lambda cmd, check=False: calls.append(cmd))

    changed, message = setup_github_cli.set_git_config_if_needed("init.defaultBranch", "main")

    assert changed is False
    assert message == "init.defaultBranch already main"
    assert calls == []


def test_set_git_config_if_needed_writes_different_value(monkeypatch):
    calls = []

    monkeypatch.setattr(setup_github_cli, "git_config", lambda key: "master")
    monkeypatch.setattr(setup_github_cli, "run", lambda cmd, check=False: calls.append((cmd, check)))

    changed, message = setup_github_cli.set_git_config_if_needed("init.defaultBranch", "main")

    assert changed is True
    assert message == "set init.defaultBranch"
    assert calls == [(["git", "config", "--global", "init.defaultBranch", "main"], True)]
