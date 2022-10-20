from launchpadlib.launchpad import Launchpad

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


def get_lp_bug(bug_number):
    """Make sure the bug ID exists, return bug"""
    try:
        return launchpad.bugs[bug_number]
    except KeyError:
        print("Couldn't find the Launchpad bug {}".format(bug_number))


def get_lp_project_bug_tasks(project_name, statuses=LP_STATUSES, tags=(), reporter=""):
    lp_project = launchpad.projects[project_name]
    bug_reporter = f"https://api.launchpad.net/devel/~{reporter}" if reporter else None
    project_bug_tasks = lp_project.searchTasks(status=list(statuses), tags=list(tags), bug_reporter=bug_reporter)

    return project_bug_tasks


def construct_bugs_from_tasks(lp_tasks):
    bugs = []
    for task in lp_tasks:
        lp_bug = get_lp_bug(int(task.web_link.split("/")[-1]))
        attachments_collection = lp_bug.attachments
        attachments = [Attachment(name=att.title, url=att.data_link) for att in attachments_collection]
        messages = [Message(author=m.owner_link, content=m.content) for m in lp_bug.messages]
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
        )
        bugs.append(bug)

    return bugs


if __name__ == "__main__":
    bug_tasks = get_lp_project_bug_tasks("checkbox-project", statuses=("New",))
    for i in construct_bugs_from_tasks(bug_tasks):
        print(i)
        # print(bug.title)
    # bug = get_lp_bug(1974197)
    # bug = get_lp_bug(830949)
    # print(bug.bug_reporter)
