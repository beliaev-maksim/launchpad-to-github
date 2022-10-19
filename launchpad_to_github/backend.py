from launchpadlib.launchpad import Launchpad

cachedir = "~/.launchpadlib/cache/"
launchpad = Launchpad.login_anonymously("just testing", "production", cachedir, version="devel")
bugs = launchpad.bugs
lp_project = launchpad.projects["ubuntu"]
project_bugs = lp_project.searchTasks(status=["New"], bug_reporter="https://api.launchpad.net/devel/~beliaev-maksim")

# launchpad.bugs[1652611].messages_collection_link
# launchpad.bugs[1652611].messages[5].content


# tasks = bugs.searchTasks(
#     tags=["juju"],
#     status=[
#         "New",
#         "Incomplete",
#         "Opinion",
#         "Invalid",
#         "Won't Fix",
#         "Expired",
#         "Confirmed",
#         "Triaged",
#         "In Progress",
#         "Fix Committed",
#         "Fix Released",
#         "Does Not Exist",
#         "Incomplete (with response)",
#         "Incomplete (without response)",
#     ],
# )

for i, bug in enumerate(project_bugs):
    print(bug.title)
    if i > 20:
        break
