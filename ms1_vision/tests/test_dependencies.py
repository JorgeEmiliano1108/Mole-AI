from app.dependencies import get_redis_publisher, get_django_patch_client

def test_redis_publisher_instance():
    pub = get_redis_publisher()
    assert pub is not None
    assert hasattr(pub, "publish_diagnostic")

def test_django_patch_client_instance():
    client = get_django_patch_client()
    assert client is not None
    assert hasattr(client, "patch")
