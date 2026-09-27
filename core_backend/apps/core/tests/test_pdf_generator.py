from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import AIDiagnostic
from apps.core.services.pdf_generator import (
    _kv_table,
    generate_diagnostic_pdf,
    request_summary,
)


class PdfGeneratorTests(TestCase):
    def test_kv_table_shape(self):
        t = _kv_table([('a', 'b')])
        self.assertIsNotNone(t)

    def test_request_summary_fallback_offline(self):
        with patch('apps.core.services.pdf_generator.httpx.post',
                   side_effect=Exception('down')):
            out = request_summary({'x': 1})
            self.assertIn('No fue posible', out)

    def test_generate_pdf_bytes(self):
        import uuid
        User = get_user_model()
        u = User.objects.create_user(username='pdf', password='x')
        d = AIDiagnostic.objects.create(user=u, plant_id=uuid.uuid4(),
                                        diagnosis_label='Mildiu')
        pdf = generate_diagnostic_pdf(d.id)
        self.assertTrue(pdf.startswith(b'%PDF'))
        with self.assertRaises(AIDiagnostic.DoesNotExist):
            generate_diagnostic_pdf('00000000-0000-0000-0000-000000000000')
