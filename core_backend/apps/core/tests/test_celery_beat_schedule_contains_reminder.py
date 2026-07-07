import pytest
from django.conf import settings

# Import the task to obtain its declared name
from microservices.mole_report.infrastructure.workers.tasks import send_reminder

def test_celery_beat_has_reminder_daily():
    schedule = getattr(settings, 'CELERY_BEAT_SCHEDULE', {})
    assert 'reminder-daily' in schedule, "reminder-daily entry missing"
    entry = schedule['reminder-daily']
    # The entry must contain a 'task' key
    assert 'task' in entry, "reminder-daily entry does not define a task"
    # The task name must match the name declared on the send_reminder task
    expected_name = send_reminder.name
    assert entry['task'] == expected_name, f"Expected task name {expected_name}, got {entry['task']}"
