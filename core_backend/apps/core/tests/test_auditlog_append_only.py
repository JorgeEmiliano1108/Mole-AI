import pytest
from django.db import connection
from django.db.utils import InternalError

from apps.core.models import AuditLog


@pytest.mark.django_db
class TestAuditLogAppendOnly:
    """AuditLog debe ser inmutable: solo inserciones permitidas."""

    def _create(self):
        return AuditLog.objects.create(
            user_id=1,
            action="TEST_EVENT",
            details="detalle de prueba",
        )

    def test_insert_is_allowed(self):
        log = self._create()
        assert log.pk is not None
        assert AuditLog.objects.filter(pk=log.pk).exists()

    def test_instance_delete_raises(self):
        log = self._create()
        with pytest.raises(PermissionError):
            log.delete()

    def test_instance_save_with_pk_raises(self):
        log = self._create()
        log.details = "modificado"
        with pytest.raises(PermissionError):
            log.save()

    def test_queryset_update_raises(self):
        self._create()
        with pytest.raises(PermissionError):
            AuditLog.objects.update(action="HACKED")

    def test_queryset_delete_raises(self):
        self._create()
        with pytest.raises(PermissionError):
            AuditLog.objects.all().delete()

    def test_bulk_update_raises(self):
        log = self._create()
        log.action = "HACKED"
        with pytest.raises(PermissionError):
            AuditLog.objects.bulk_update([log], ["action"])

    def test_database_trigger_blocks_raw_update(self):
        log = self._create()
        with (
            pytest.raises(InternalError),
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "UPDATE audit_logs SET action = %s WHERE id = %s",
                ["HACKED", log.pk],
            )

    def test_database_trigger_blocks_raw_delete(self):
        log = self._create()
        with (
            pytest.raises(InternalError),
            connection.cursor() as cursor,
        ):
            cursor.execute("DELETE FROM audit_logs WHERE id = %s", [log.pk])
