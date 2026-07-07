import pytest
from unittest.mock import patch
from apps.core.models import AIDiagnostic, User, Device

@pytest.fixture
def low_urgency_diagnostic(db):
    user = User.objects.create_user(username='low_user', password='pw')
    device = Device.objects.create(name='dev', auth_token='tok', owner=user)
    diag = AIDiagnostic.objects.create(
        user=user,
        plant_id='plant-2',
        diagnostic_type='disease',
        condition_name='cond_low',
        condition_description='desc_low',
        severity='low',
        ai_model_used='model_low',
        confidence_score=0.5,
        metadata={'urgency': 'LOW'},
        treatment_protocol='treat_low',
    )
    return diag

@patch('core_backend.apps.core.models.send_reminder.delay')
def test_low_urgency_does_not_trigger(mock_delay, low_urgency_diagnostic):
    # Creation of diagnostic fires post_save; for low urgency we expect no call.
    assert not mock_delay.called
