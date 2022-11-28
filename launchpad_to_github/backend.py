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
)


def get_lp_bug(launchpad, bug_number):
    """Make sure the bug ID exists, return bug
    :param launchpad:
    """
    try:
        return launchpad.bugs[bug_number]
    except KeyError:
        print("Couldn't find the Launchpad bug {}".format(bug_number))


def add_comment_to_lp_bug(lp_bug, comment):
    lp_bug.newMessage(content=comment)


def close_lp_bug_task(task, status):
    task.status = status
    task.lp_save()


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
        yield bug


def check_labels(repo: Repository):
    labels = [label.name for label in repo.get_labels()]
    if "bug" not in labels:
        repo.create_label("bug", color="d73a4a")

    if "Security" not in labels:
        repo.create_label("Security", color="ed2226")

    if "Importance: Critical" not in labels:
        repo.create_label("Importance: Critical", color="f95770")

    if "Importance: High" not in labels:
        repo.create_label("Importance: High", color="dd4995")

    if "FromLaunchpad" not in labels:
        repo.create_label("Critical", color="00ffff")


def create_gh_issue(repo: Repository, bug: Bug, apply_labels: bool = False, issue_titles=list[str]):
    attachments = "\n".join([f"[{att.name}]({att.url})" for att in bug.attachments])

    lp_bug_number = bug.web_link.split("/")[-1]
    title = f"LP{lp_bug_number}: {bug.title}"
    if any([f"LP{lp_bug_number}" in title for title in issue_titles]):
        print(f"Bug with number LP{lp_bug_number} is already added.")
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
        if bug.importance.lower() == "critical":
            labels.append("Importance: Critical")

        if bug.importance.lower() == "high":
            labels.append("Importance: High")

        if bug.security_related:
            labels.append("Security")

        labels.append("FromLaunchpad")
        labels.append("bug")

    issue = repo.create_issue(title, body=body, labels=labels)
    print(f"Issue #{issue.number} was created")

    if len(bug.messages) >= 2:
        body = ""

        for msg in bug.messages[1:]:
            if not msg.content:
                continue

            date = msg.date_created.strftime("%Y-%m-%d %H:%M:%S")
            body += f"##### https://launchpad.net/~{msg.author} wrote on {date}:\n{msg.content}\n\n"

        if not body:
            return issue

        body = "This thread was migrated from launchpad.net\n" + body

        issue.create_comment(body=body)

    return issue
