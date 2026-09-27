import os
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.ai_models.tasks import cleanup_temp_files
from apps.authentication.tasks import (
    send_password_reset_email_task,
    send_verification_email_task,
    verify_email_task,
)


class MaintenanceTasksTests(TestCase):
    def test_cleanup_missing_dir(self):
        with override_settings(MEDIA_ROOT='/tmp/mole_noexiste_xyz'):
            self.assertIn('does not exist', cleanup_temp_files())

    def test_cleanup_old_files(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = os.path.join(d, 'temp')
            os.makedirs(tmp)
            old = os.path.join(tmp, 'a.jpg')
            with open(old, 'wb') as f:
                f.write(b'x')
            ancient = __import__('time').time() - 100000
            os.utime(old, (ancient, ancient))
            with override_settings(MEDIA_ROOT=d):
                out = cleanup_temp_files()
            self.assertIn('Deleted 1', out)
            self.assertFalse(os.path.exists(old))


class MailTasksTests(TestCase):
    def test_verification_flow_offline(self):
        User = get_user_model()
        u = User.objects.create_user(username='mail', password='x',
                                     email='m@x.io')
        out = send_verification_email_task(u.id, 'm@x.io', 'mail')
        # Sin SMTP en tests: falla agraciada con token persistido.
        self.assertTrue(out.startswith(('Verification email sent',
                                        'Failed to send email')))
        u.refresh_from_db()
        self.assertIsNotNone(u.email_verification_token)

    def test_verify_unknown_token(self):
        self.assertEqual(verify_email_task('noexiste'),
                         {"status": "invalid_token"})

    def test_reset_unknown_user(self):
        out = send_password_reset_email_task(999999, 'a@x.io', 'a')
        self.assertIn('User not found', out)
