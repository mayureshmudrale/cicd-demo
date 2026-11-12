import os

# Must happen before anything imports config/db/main, so the real engine
# this process builds points at a throwaway sqlite file, not Postgres.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ideaboard.db")
os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
