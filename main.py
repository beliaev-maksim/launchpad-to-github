from launchpadlib.launchpad import Launchpad

cachedir = "~/.launchpadlib/cache/"
launchpad = Launchpad.login_anonymously("just testing", "production", cachedir, version="devel")
bugs = launchpad.bugs
# lp_project = launchpad.projects["alsa"]
# bugss = lp_project.searchTasks(tags="Ubuntu")

tasks = bugs.searchTasks(
    tags=["juju"],
    status=[
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
    ],
)

for i, bug in enumerate(tasks):
    print(bug.title)
    if i > 10:
        break
