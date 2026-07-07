import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.core.models import Device, UserPlant
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def user_with_device(db):
    user = User.objects.create_user(username='testuser', password='testpass')
    device = Device.objects.create(
        name='TestDevice',
        auth_token='valid-token',
        owner=user  # assuming Device has a FK to auth user; if not, adjust accordingly
    )
    return user, device

@pytest.mark.django_db
def test_revocation_endpoint(user_with_device):
    user, device = user_with_device
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse('device_revoke', kwargs={'id': device.id})
    response = client.delete(url)
    assert response.status_code == 204
    device.refresh_from_db()
    assert device.is_active is False

@pytest.mark.django_db
def test_ingest_block_inactive(user_with_device):
    user, device = user_with_device
    client = APIClient()
    client.force_authenticate(user=user)
    # Revoke first
    revoke_url = reverse('device_revoke', kwargs={'id': device.id})
    client.delete(revoke_url)
    # Try ingest with token of revoked device
    ingest_url = reverse('edge_ingest_batch')
    payload = {
        'ts': 0,
        'a': {},
        's': []
    }
    client.credentials(HTTP_AUTHORIZATION='Bearer valid-token')
    response = client.post(ingest_url, data=payload, format='json')
    assert response.status_code == 401
