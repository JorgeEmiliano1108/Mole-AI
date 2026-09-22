import uuid
import pytest
from unittest.mock import patch
from apps.core.models import AIDiagnostic, User, Device

@pytest.fixture
def low_urgency_setup(db):
    user = User.objects.create_user(username='low_user', password='pw')
    Device.objects.create(name='dev', auth_token='tok', owner=user)
    return user

@patch('apps.core.models.send_reminder')
def test_low_urgency_does_not_trigger(mock_reminder, low_urgency_setup):
    # Creation of diagnostic fires post_save; for low urgency we expect no call.
    AIDiagnostic.objects.create(
        user=low_urgency_setup,
        plant_id=uuid.uuid4(),
        diagnosis_label='sano',
        confidence_score=0.5,
        metadata={'urgency': 'LOW', 'severity': 'low'},
    )
    assert not mock_reminder.delay.called
