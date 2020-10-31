#!/usr/bin/env python3
# Copyright 2020 Sn0cr
# MIT License

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import json
from pathlib import Path
import subprocess
import semver
import os
import todoist
import platform
from datetime import date, datetime
from most_recent_tag import most_recent_tag

VERSION = semver.VersionInfo.parse("1.0.0")
REMINDER_LOCATION = Path("./reminder.json")
DOCKER_IMAGE = "gitlab/gitlab-ce"
MESSAGE_TEMPLATE = """Upgrade Gitlab on {hostname} from {current_gitlab_version} to {most_recent_gitlab_version}"""
TODOIST_DUE = "today"
TODOIST_PROJECT_ID = os.getenv("TODOIST_PROJECT_ID")
TODOIST_TOKEN = os.getenv("TODOIST_API_TOKEN")


def get_last_reminder():
    if REMINDER_LOCATION.exists():
        with REMINDER_LOCATION.open(mode="r") as reminder_file:
            reminder = json.load(reminder_file)
            reminder["last_checked"] = datetime.fromisoformat(reminder["last_checked"])
        return reminder
    else:
        return {"last_checked": None, "last_version": None, "last_id": None}


def save_last_reminder(reminder):
    reminder['last_checked'] = reminder['last_checked'].isoformat()
    with REMINDER_LOCATION.open(mode="w") as reminder_file:
        json.dump(reminder, reminder_file)


def get_gitlab_version():
    result = subprocess.run(["sudo", "/usr/local/bin/gitlab-version"], stdout = subprocess.PIPE)
    print(result)
    result_stdout = result.stdout.decode("utf8").strip()
    version = result_stdout.split(":")[1]
    return version


def create_task(current_gitlab_version, most_recent_gitlab_version, last_reminder):
    api = todoist.TodoistAPI(TODOIST_TOKEN)
    text = MESSAGE_TEMPLATE.format(
        most_recent_gitlab_version=most_recent_gitlab_version,
        current_gitlab_version=current_gitlab_version,
        hostname=platform.node(),
    )
    if last_reminder["last_id"]:
        last_item = api.items.get_by_id(last_reminder["last_id"])
    else:
        last_item = None

    if last_item and last_item["checked"] == 0:
        last_item.update(content=text, due={"string": TODOIST_DUE})
        todoist_id = last_item["id"]
    else:
        # create new task if it is checked (ie > 0) or not existent
        item = api.items.add(
            text, project_id=TODOIST_PROJECT_ID, due={"string": TODOIST_DUE}
        )
        todoist_id = item["id"]
    api.commit()
    return todoist_id


if __name__ == "__main__":
    current_gitlab_version = get_gitlab_version()
    most_recent_gitlab_version = most_recent_tag(DOCKER_IMAGE)
    last_reminder = get_last_reminder()
    if semver.compare(current_gitlab_version, most_recent_gitlab_version) < 0:
        last_reminder["last_checked"] = datetime.now()
        last_reminder["last_version"] = current_gitlab_version
        last_reminder["last_id"] = create_task(
            current_gitlab_version, most_recent_gitlab_version, last_reminder
        )
        save_last_reminder(last_reminder)