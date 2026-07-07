import pytest
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_prometheus_metrics_endpoint():
    client = APIClient()
    response = client.get('/metrics/')
    assert response.status_code == 200
    # Assert that a common prometheus metric is present in the response body
    assert b'process_cpu_seconds_total' in response.content
