from click.testing import CliRunner

from launchpad_to_github.cli import migrate_bugs


def test_migrate_bugs():
    runner = CliRunner()
    result = runner.invoke(
        migrate_bugs,
        [
            "--gh-repo-name",
            "beliaev-maksim/test_repo_for_issues",
            "--labels",
            "--lp-project-name=lp-gh-tester",
            "-t",
            "tag1",
            "-t",
            "tag2",
            "--change-lp-status",
            "null",
        ],
    )
    assert result.exit_code == 0
