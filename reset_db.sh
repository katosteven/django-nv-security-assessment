#!/bin/bash
set -e
[ -d .venv ] && . .venv/bin/activate
export DEBUG="${DEBUG:-True}"
rm -f db.sqlite3
python manage.py migrate
python manage.py loaddata \
    fixtures/users.json \
    fixtures/usersProfiles.json \
    fixtures/taskManagerProjects.json \
    fixtures/taskManagerTasks.json \
    fixtures/taskManagerNotes.json

