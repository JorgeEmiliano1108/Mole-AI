import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def two_users_one_device(db):
    owner = User.objects.create_user(username='owner', password='pw')
    other = User.objects.create_user(username='other', password='pw')
    from apps.core.models import Device
    device = Device.objects.create(name='Dev', auth_token='token123', owner=owner)
    return owner, other, device

@pytest.mark.django_db
def test_device_owner_unauthorized(two_users_one_device):
    owner, other, device = two_users_one_device
    client = APIClient()
    client.force_authenticate(user=other)
    url = reverse('core:device_revoke', kwargs={'id': device.id})
    response = client.delete(url)
    # Autenticado pero no dueño ni staff → 403 (no 401: sí hay sesión)
    assert response.status_code == 403
    device.refresh_from_db()
    assert device.is_active is True
