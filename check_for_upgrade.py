#!/usr/bin/env python3
# Copyright 2020-2023 Sn0cr
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
from typing import Optional
from pydantic import BaseModel
import semver
import os
from todoist_api_python.api import TodoistAPI
import platform
from datetime import datetime
from most_recent_tag import most_recent_tag

VERSION = semver.version.Version.parse("1.0.0")
REMINDER_LOCATION = Path("./reminder.json")
DOCKER_IMAGE = "gitlab/gitlab-ce"
MESSAGE_TEMPLATE = """Upgrade Gitlab on {hostname} from {current_gitlab_version} to {most_recent_gitlab_version}"""
TODOIST_DUE = "today"
TODOIST_PROJECT_ID = os.getenv("TODOIST_PROJECT_ID")
TODOIST_TOKEN = os.getenv("TODOIST_API_TOKEN")


class Reminder(BaseModel):
    last_checked: Optional[datetime] = None
    last_version: Optional[str] = None
    last_id: Optional[str] = None


def get_last_reminder() -> Reminder:
    if REMINDER_LOCATION.exists():
        return Reminder.parse_file(REMINDER_LOCATION)
    else:
        return Reminder()


def get_gitlab_version() -> str:
    result = subprocess.run(
        ["sudo", "/usr/local/bin/gitlab-version"],
        stdout=subprocess.PIPE,
    )
    print(result)
    result_stdout = result.stdout.decode("utf8").strip()
    version = result_stdout.split(":")[1]
    return version


def create_task(
    current_gitlab_version: str,
    most_recent_gitlab_version: str,
    last_reminder: Reminder,
    todoist_token: str,
) -> str:
    api = TodoistAPI(todoist_token)
    text = MESSAGE_TEMPLATE.format(
        most_recent_gitlab_version=most_recent_gitlab_version,
        current_gitlab_version=current_gitlab_version,
        hostname=platform.node(),
    )
    reminder_id = last_reminder.last_id
    if reminder_id:
        last_item = api.get_task(task_id=reminder_id)
        if last_item.is_completed == True:
            api.update_task(
                task_id=reminder_id,
                due_string=TODOIST_DUE,
                content="Update Gitlab",
                description=text,
            )
            return reminder_id

    # create new task if it is checked (ie > 0) or not existent
    task = api.add_task(
        content="Update Gitlab",
        description=text,
        due_string=TODOIST_DUE,
        due_lang="en",
        priority=1,
        project_id=TODOIST_PROJECT_ID,
    )
    return task.id


if __name__ == "__main__":
    current_gitlab_version = semver.version.Version.parse(get_gitlab_version())
    most_recent_gitlab_version = semver.version.Version.parse(
        most_recent_tag(DOCKER_IMAGE)
    )
    last_reminder = get_last_reminder()
    if not TODOIST_TOKEN:
        exit(1)
    if current_gitlab_version < most_recent_gitlab_version:
        print("Upgrade Gitlab!")
        last_reminder.last_checked = datetime.now()
        last_reminder.last_version = current_gitlab_version
        last_reminder.last_id = create_task(
            current_gitlab_version,
            most_recent_gitlab_version,
            last_reminder,
            TODOIST_TOKEN,
        )
        REMINDER_LOCATION.write_text(last_reminder.json())
