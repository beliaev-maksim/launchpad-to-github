import os

from github import Github
from launchpadlib.launchpad import Launchpad

from launchpad_to_github.gh_issue_template import gh_issue_template
from launchpad_to_github.models import Attachment
from launchpad_to_github.models import Bug
from launchpad_to_github.models import Message

cachedir = "~/.launchpadlib/cache/"

LP_STATUSES = (
    "New",
    "Incomplete",
    "Opinion",
    "Invalid",
    "Won't Fix",
    "Expired",
    "Confirmed",
    "Triaged",
    "In Progress",
    "Fix Committed",
    "Fix Released",
    "Does Not Exist",
    "Incomplete (with response)",
    "Incomplete (without response)",
)

launchpad = Launchpad.login_anonymously("migration lp-gh", "production", cachedir, version="devel")
github = Github(os.getenv("GH_TOKEN"))


def get_lp_bug(bug_number):
    """Make sure the bug ID exists, return bug"""
    try:
        return launchpad.bugs[bug_number]
    except KeyError:
        print("Couldn't find the Launchpad bug {}".format(bug_number))


def get_lp_project_bug_tasks(project_name, statuses=LP_STATUSES, tags=(), reporter=""):
    if not_allowed := set(statuses) - set(LP_STATUSES):
        raise ValueError(f"Following statuses are not allowed: {not_allowed}. Please choose from {LP_STATUSES}")

    lp_project = launchpad.projects[project_name]
    bug_reporter = f"https://api.launchpad.net/devel/~{reporter}" if reporter else None
    project_bug_tasks = lp_project.searchTasks(status=list(statuses), tags=list(tags), bug_reporter=bug_reporter)

    return project_bug_tasks


def construct_bugs_from_tasks(lp_tasks):
    bugs = []
    for task in lp_tasks:
        lp_bug = launchpad.load(task.bug_link)
        attachments_collection = lp_bug.attachments
        attachments = [Attachment(name=att.title, url=att.data_link) for att in attachments_collection]
        messages = [
            Message(author=m.owner_link, content=m.content, date_created=m.date_created) for m in lp_bug.messages
        ]
        bug = Bug(
            assignee_link=task.assignee_link,
            attachments=attachments,
            attachments_collection=attachments_collection,
            date_created=task.date_created,
            description=lp_bug.description,
            heat=lp_bug.heat,
            importance=task.importance,
            messages=messages,
            owner_link=lp_bug.owner_link,
            security_related=lp_bug.security_related,
            status=task.status,
            tags=lp_bug.tags,
            title=lp_bug.title,
            web_link=task.web_link,
            original_task=task,
            original_bug=lp_bug,
        )
        create_gh_issue(bug, "beliaev-maksim/test_repo_for_issues")
        bugs.append(bug)

    return bugs


def create_gh_issue(bug: Bug, repo_name):
    repo = github.get_repo(repo_name)
    attachments = "\n".join([f"[{att.name}]({att.url})" for att in bug.attachments])

    title = f"LP{bug.web_link.split('/')[-1]}: {bug.title}"
    body = gh_issue_template.format(
        status=bug.status,
        created_on=bug.date_created.strftime("%Y-%m-%d %H:%M:%S"),
        heat=bug.heat,
        importance=bug.importance,
        security=bug.security_related,
        description=bug.description,
        attachments=attachments or "No attachments",
        tags=bug.tags,
        bug_link=bug.web_link,
    )
    issue = repo.create_issue(title, body=body)

    if len(bug.messages) >= 2:
        body = "This thread was migrated from launchpad.net\n"

        for m in bug.messages[1:]:
            if not m.content:
                continue

            body += f"##### {m.author} wrote on {m.date_created.strftime('%Y-%m-%d %H:%M:%S')}:\n{m.content}\n\n"

        issue.create_comment(body=body)


if __name__ == "__main__":
    bug_tasks = get_lp_project_bug_tasks("checkbox-project", statuses=("Opinion",))
    for i in construct_bugs_from_tasks(bug_tasks):
        print(i)
