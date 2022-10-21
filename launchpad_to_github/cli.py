import click
from github import Github
from launchpadlib.launchpad import Launchpad

from launchpad_to_github.backend import LP_STATUSES
from launchpad_to_github.backend import add_comment_to_lp_bug
from launchpad_to_github.backend import close_lp_bug_task
from launchpad_to_github.backend import construct_bugs_from_tasks
from launchpad_to_github.backend import create_gh_issue
from launchpad_to_github.backend import get_lp_project_bug_tasks

cachedir = "~/.launchpadlib/cache/"


@click.command()
@click.option("--gh-repo-name", required=True, help="Name of the GitHub repo '<owner>/<repo>'")
@click.option("--labels", is_flag=True, help="Apply labels to the issues in GH")
@click.option("--lp-project-name", required=True, help="Name of the launchpad project")
@click.option(
    "--change-lp-status",
    required=True,
    help="Set launchpad bug status to TEXT. Set value to 'null' to keep unchanged.",
)
@click.option(
    "--filter-status",
    "-s",
    help="Filter bugs by status. Default: all. Repeat for multiple '-s New -s Expired'",
    multiple=True,
    default=LP_STATUSES,
)
@click.option(
    "--filter-tag",
    "-t",
    help=(
        "Filter bugs by tag. "
        "Find bugs where one of the tags is specified (OR logic). "
        "Repeat for multiple '-t tag1 -t tag2'"
    ),
    multiple=True,
)
@click.option(
    "--filter-reporter",
    help="Filter bugs by reporter username.",
)
@click.option("--gh-token", envvar="GH_TOKEN", help="GitHub API token")
def migrate_bugs(
    gh_repo_name,
    labels,
    lp_project_name,
    change_lp_status,
    filter_status,
    filter_tag,
    filter_reporter,
    gh_token,
):
    if not gh_token:
        raise EnvironmentError(
            "Provide GitHub API token via --gh-token or GH_TOKEN environment variable"
        )

    if change_lp_status != "null" and change_lp_status not in LP_STATUSES:
        raise ValueError(
            f"--change-lp-status is wrong, must be 'null' or one of {', '.join(LP_STATUSES)}"
        )

    github = Github(gh_token)
    launchpad = Launchpad.login_with("migration lp-gh", "production", cachedir, version="devel")
    repo = github.get_repo(gh_repo_name)

    project_bug_tasks = get_lp_project_bug_tasks(
        launchpad,
        project_name=lp_project_name,
        statuses=filter_status,
        tags=filter_tag,
        reporter=filter_reporter,
    )

    bugs = construct_bugs_from_tasks(launchpad, project_bug_tasks)

    issue_titles = [i.title for i in repo.get_issues()]
    for bug in bugs:
        issue = create_gh_issue(repo, bug, apply_labels=labels, issue_titles=issue_titles)
        if issue:
            comment = (
                f"Bug was migrated to GitHub: {issue.html_url}.\nBug is no more monitored here."
            )
            add_comment_to_lp_bug(bug.original_bug, comment)
            if change_lp_status != "null":
                close_lp_bug_task(bug.original_task, change_lp_status)


if __name__ == "__main__":
    migrate_bugs()
