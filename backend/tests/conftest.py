import pytest
from django_redis import get_redis_connection


@pytest.fixture
def redis_client():
    return get_redis_connection("default")