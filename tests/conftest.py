import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db


@pytest.fixture(scope="session")
def db_engine():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a database session for each test"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client with a database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_csv_departments():
    """Sample CSV data for departments"""
    return b"1,Engineering\n2,Sales\n3,Marketing"


@pytest.fixture
def sample_csv_jobs():
    """Sample CSV data for jobs"""
    return b"1,Software Engineer\n2,Data Analyst\n3,Product Manager"


@pytest.fixture
def sample_csv_employees():
    """Sample CSV data for employees"""
    return b"1,John Doe,2021-01-15T09:00:00,1,1\n2,Jane Smith,2021-02-20T10:30:00,2,2"
