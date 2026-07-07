import pytest
from unittest.mock import patch
from apps.core.models import AIDiagnostic, User, Device

@pytest.fixture
def high_urgency_diagnostic(db):
    user = User.objects.create_user(username='high_user', password='pw')
    device = Device.objects.create(name='dev', auth_token='tok', owner=user)
    diag = AIDiagnostic.objects.create(
        user=user,
        plant_id='plant-1',
        diagnostic_type='disease',
        condition_name='cond',
        condition_description='desc',
        severity='high',
        ai_model_used='model',
        confidence_score=0.9,
        metadata={'urgency': 'HIGH'},
        treatment_protocol='treat',
    )
    return diag

@patch('core_backend.apps.core.models.send_reminder.delay')
def test_high_urgency_triggers_send_reminder(mock_delay, high_urgency_diagnostic):
    # The AIDiagnostic creation fires post_save; the mock should capture the call
    assert mock_delay.called
    assert mock_delay.call_count == 1
    # First argument is recipient id as string, second is message containing the diagnostic id
    recipient, message = mock_delay.call_args[0]
    assert recipient == str(high_urgency_diagnostic.user.id)
    assert str(high_urgency_diagnostic.id) in message
