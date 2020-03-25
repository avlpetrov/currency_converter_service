import uuid

import aioredis
import docker as dockerlib
import pytest

REDIS_DOCKER_IMAGE = "redis:5-alpine"
EXPOSED_PORT = 6379
REDIS_TEST_SERVER_URI = f"redis://localhost:{EXPOSED_PORT}"


@pytest.fixture(scope="session")
def docker() -> dockerlib.APIClient:
    return dockerlib.APIClient(version="auto")


@pytest.fixture(scope="session", autouse=True)
def redis_server(docker: dockerlib.APIClient):

    docker.pull(REDIS_DOCKER_IMAGE)

    container = docker.create_container(
        image=REDIS_DOCKER_IMAGE,
        name=f"test-redis-{uuid.uuid4()}",
        detach=True,
        host_config=docker.create_host_config(port_bindings={6379: EXPOSED_PORT}),
    )
    docker.start(container=container["Id"])

    yield

    docker.kill(container["Id"])
    docker.remove_container(container["Id"])


@pytest.fixture
async def database():
    connection = await aioredis.create_redis(REDIS_TEST_SERVER_URI)

    yield connection
    await connection.flushdb()
    connection.close()
    await connection.wait_closed()
