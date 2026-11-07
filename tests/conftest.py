import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.REST.data.database import SessionLocal, engine, get_db
import main
from main import app
from app.REST.model.products.product_history_orm import ProductHistoryORM
from app.REST.model.products.product_orm import ProductORM


@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection, join_transaction_mode="create_savepoint")
    baseline_counts = (
        session.scalar(select(func.count()).select_from(ProductORM)),
        session.scalar(select(func.count()).select_from(ProductHistoryORM)),
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

        with SessionLocal() as verification_session:
            final_counts = (
                verification_session.scalar(select(func.count()).select_from(ProductORM)),
                verification_session.scalar(select(func.count()).select_from(ProductHistoryORM)),
            )
        assert final_counts == baseline_counts, "Test left product or history rows in the database"


@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    monkeypatch.setattr(main, "run_worker", lambda: None)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
