import logging.config
import os

import pytest
import pytest_asyncio
import yaml
from fastapi.testclient import TestClient
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport

import directories
from quant_api import database, models

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_logging_configs(request):
    """Cleanup a testing directory once we are finished."""
    with open(directories.logging, "r") as stream:
        config = yaml.load(stream, Loader=yaml.FullLoader)
        logging.config.dictConfig(config)


@pytest.fixture(scope="session", autouse=True)
def setup_lifecycle(request):
    def finalizer():
        logger.debug("Shutting down unittest session..")

    request.addfinalizer(finalizer)


@pytest.fixture(scope="session")
def client():
    from quant_api.apps.v1 import app

    yield TestClient(app)


@pytest_asyncio.fixture(scope="session")
async def async_client():
    from quant_api.apps.v1 import app

    async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        print("Creating a client..")
        yield ac


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_and_drop_all():
    print(os.getenv("env"))
    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        logger.debug("Database created.")
    yield
    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        logger.debug("Database dropped.")
