import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # Ensures all model tables are registered.
from app.auth import require_api_key
from app.database import Base, get_db
from app.main import app

@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, connection_record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    TestSession = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_db():
        with TestSession() as db:
            yield db

    def override_auth():
        # Workflow tests intentionally bypass authentication.
        # Authentication has a separate test.
        return None

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_api_key] = override_auth

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
