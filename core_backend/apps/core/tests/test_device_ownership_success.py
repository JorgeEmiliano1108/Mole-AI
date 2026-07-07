import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def owner_user_with_device(db):
    user = User.objects.create_user(username='owner', password='pw')
    from apps.core.models import Device
    device = Device.objects.create(name='Dev', auth_token='token123', owner=user)
    return user, device

@pytest.mark.django_db
def test_device_owner_success(owner_user_with_device):
    user, device = owner_user_with_device
    client = APIClient()
    client.force_authenticate(user=user)
    # Verify the FK works
    assert device.owner == user
    # Revoke endpoint should succeed (204)
    url = reverse('device_revoke', kwargs={'id': device.id})
    response = client.delete(url)
    assert response.status_code == 204
