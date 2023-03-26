# docker-upgrade-check

This collection of scripts does two things:
1. It checks if a Docker image has a newer [Semver](https://semver.org/)-versioned
    version on dockerhub
2. It creates a task in your todoist to upgrade the gitlab container if it is
    outdated (it's possible to change it in the script `check_for_upgrade`)

# Installation
1. Clone this repository:
    ```shell
    $ git clone https://github.com/sn0cr/docker-upgrade-check
    ```
1. Create Virtual Env / use direnv
    * Virtual Env (**On the server**):
        ```shell
        python -m venv docker-upgrade-check
        source docker-upgrade-check/bin/activate
        ```
    * direnv (**for development**):
        ```shell
        $ direnv allow .
        ```
1. Install all requirements with `pip`
    ```shell
    $ pip install -r requirements.txt
    ```
1. You might want to alter the python interpreter at the top of `check_for_upgrade.py`
    to use the pipenv installed python.
1. Create your service file in `$USER/.config/systemd/user/gitlab-version-check.service`
    ```ini
    [Unit]
    Description=Check if gitlab is recent

    [Service]
    ExecStart=<$REPO>docker-upgrade-check/bin/python <$REPO>/docker-upgrade-check/check_for_upgrade.py
    Environment="TODOIST_API_TOKEN='<your_todoist_token>'"
    Environment="TODOIST_PROJECT_ID='<your_project_id>'"
    Type=oneshot
    ```
1. Create your timer file in `$USER/.config/systemd/user/gitlab-version-check.timer`
    ```ini
    [Unit]
    Description=gitlab-version-check timer

    [Timer]
    Unit=gitlab-version-check.service
    OnCalendar=Weekly

    [Install]
    WantedBy=basic.target
    ```
1. Enable the timer with
    ```shell
    $ systemctl --user enable gitlab-version-check.timer
    ```
1. And try it once to see if it works:
    ```shell
    $ systemctl --user start gitlab-version-check.service
    ```
    Now you should see a new entry in your todoist task list (but obviously only
    if your gitlab was outdated at the time of testing ;))

1. If you want to see when the next check is run, use the following command:
    ```shell
    $ systemctl --user status "*timer"
    ```
