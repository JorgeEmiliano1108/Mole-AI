import uuid
import pytest
from unittest.mock import patch
from apps.core.models import AIDiagnostic, User, Device

@pytest.fixture
def high_urgency_diagnostic(db):
    user = User.objects.create_user(username='high_user', password='pw')
    Device.objects.create(name='dev', auth_token='tok', owner=user)
    with patch('apps.core.models.send_reminder'):
        diag = AIDiagnostic.objects.create(
            user=user,
            plant_id=uuid.uuid4(),
            diagnosis_label='mildiu',
            confidence_score=0.9,
            metadata={'urgency': 'HIGH', 'severity': 'high'},
        )
    return diag

@patch('apps.core.models.send_reminder')
def test_high_urgency_triggers_send_reminder(mock_reminder, high_urgency_diagnostic):
    # The AIDiagnostic creation fires post_save; the mock should capture the call
    user = high_urgency_diagnostic.user
    with patch('apps.core.models.send_reminder', mock_reminder):
        AIDiagnostic.objects.create(
            user=user,
            plant_id=uuid.uuid4(),
            diagnosis_label='roya',
            confidence_score=0.8,
            metadata={'urgency': 'HIGH', 'severity': 'high'},
        )
    assert mock_reminder.delay.called
    assert mock_reminder.delay.call_count == 1
    # First argument is recipient id as string, second is message containing the diagnostic id
    recipient, message = mock_reminder.delay.call_args[0]
    assert recipient == str(user.id)
    assert "Urgent diagnostic" in message
