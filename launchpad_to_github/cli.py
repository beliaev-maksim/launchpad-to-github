import os

from github import Github
from launchpadlib.launchpad import Launchpad

cachedir = "~/.launchpadlib/cache/"

launchpad = Launchpad.login_anonymously("migration lp-gh", "production", cachedir, version="devel")
github = Github(os.getenv("GH_TOKEN"))
