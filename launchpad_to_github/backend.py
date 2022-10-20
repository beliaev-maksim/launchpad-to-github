import click
from github.Repository import Repository

from launchpad_to_github.gh_issue_template import gh_issue_template
from launchpad_to_github.models import Attachment
from launchpad_to_github.models import Bug
from launchpad_to_github.models import Message

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


def get_lp_bug(launchpad, bug_number):
    """Make sure the bug ID exists, return bug
    :param launchpad:
    """
    try:
        return launchpad.bugs[bug_number]
    except KeyError:
        print("Couldn't find the Launchpad bug {}".format(bug_number))


def get_lp_project_bug_tasks(launchpad, project_name, statuses=LP_STATUSES, tags=(), reporter=""):
    if not_allowed := set(statuses) - set(LP_STATUSES):
        raise ValueError(
            f"Following statuses are not allowed: {not_allowed}. Please choose from {LP_STATUSES}"
        )

    lp_project = launchpad.projects[project_name]
    bug_reporter = f"https://api.launchpad.net/devel/~{reporter}" if reporter else None
    project_bug_tasks = lp_project.searchTasks(
        status=list(statuses), tags=list(tags), bug_reporter=bug_reporter
    )

    return project_bug_tasks


def construct_bugs_from_tasks(launchpad, lp_tasks):
    bugs = []
    for task in lp_tasks:
        lp_bug = launchpad.load(task.bug_link)
        attachments_collection = lp_bug.attachments
        attachments = [
            Attachment(name=att.title, url=att.data_link) for att in attachments_collection
        ]
        messages = [
            Message(
                author_link=msg.owner_link,
                author=msg.owner_link.split("~")[-1],
                content=msg.content,
                date_created=msg.date_created,
            )
            for msg in lp_bug.messages
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
        bugs.append(bug)

    return bugs


def check_labels(repo: Repository):
    labels = repo.get_labels()
    if "Important" not in labels:
        raise ValueError("Please add label 'Important' to repository")

    if "Security" not in labels:
        raise ValueError("Please add label 'Security' to repository")

    if "FromLaunchpad" not in labels:
        raise ValueError("Please add label 'FromLaunchpad' to repository")


def create_gh_issue(repo: Repository, bug: Bug, apply_labels: bool = False, issue_titles=list[str]):
    attachments = "\n".join([f"[{att.name}]({att.url})" for att in bug.attachments])

    lp_bug_number = bug.web_link.split("/")[-1]
    title = f"LP{lp_bug_number}: {bug.title}"
    if any([f"LP{lp_bug_number}" in title for title in issue_titles]):
        click.echo(f"Bug with number LP{lp_bug_number} is already added.")
        return

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

    labels = []
    if apply_labels:
        check_labels(repo)
        if bug.importance.lower() in ["high", "critical"]:
            labels.append("Important")

        if bug.security_related:
            labels.append("Security")

        labels.append("FromLaunchpad")

    issue = repo.create_issue(title, body=body, labels=labels)

    if len(bug.messages) >= 2:
        body = "This thread was migrated from launchpad.net\n"

        for msg in bug.messages[1:]:
            if not msg.content:
                continue

            date = msg.date_created.strftime("%Y-%m-%d %H:%M:%S")
            body += f"##### https://launchpad.net/~{msg.author} wrote on {date}:\n{msg.content}\n\n"

        issue.create_comment(body=body)
