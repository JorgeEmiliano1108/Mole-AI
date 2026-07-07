import pytest
from django.core.management import call_command
from django.db import connection
from apps.core.models import Device

@pytest.mark.django_db
def test_is_active_field_exists():
    # Verify that the column exists in the DB after migrations
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='devices' AND column_name='is_active';")
        rows = cursor.fetchall()
    assert rows, "is_active column not created by migration"
    # Verify default value on a fresh object
    d = Device.objects.create(name='test-device', auth_token='test-token')
    assert d.is_active is True
