import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from apps.core.models import Device

User = get_user_model()


@pytest.mark.django_db
def test_is_active_field_exists():
    # Verify that the column exists in the DB after migrations (portable:
    # introspection works on SQLite and PostgreSQL, unlike information_schema)
    columns = [c.name for c in connection.introspection.get_table_description(connection.cursor(), "devices")]
    assert "is_active" in columns, "is_active column not created by migration"
    assert "auth_token_expires_at" in columns, "auth_token_expires_at column not created by migration"
    # Verify default value on a fresh object
    owner = User.objects.create_user(username="active_check", password="x")
    d = Device.objects.create(owner=owner, name='test-device', auth_token='test-token')
    assert d.is_active is True
