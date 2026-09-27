# Generated manually for Hito 4 — append-only guarantee at database level.
# ruff: noqa: I001, RUF012
from django.db import connection, migrations


_TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION audit_logs_prevent_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'AuditLog is append-only: % on audit_logs is forbidden.', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_logs_immutable_trigger ON audit_logs;
CREATE TRIGGER audit_logs_immutable_trigger
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION audit_logs_prevent_mutation();
"""

_DROP_SQL = """
DROP TRIGGER IF EXISTS audit_logs_immutable_trigger ON audit_logs;
DROP FUNCTION IF EXISTS audit_logs_prevent_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0015_aidiagnostic_pvu_reason'),
    ]

    operations = [
        migrations.RunSQL(
            sql=_TRIGGER_SQL if connection.vendor == 'postgresql' else '',
            reverse_sql=_DROP_SQL if connection.vendor == 'postgresql' else '',
        ),
    ]
