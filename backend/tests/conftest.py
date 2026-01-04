import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config.database import Base, get_db
from src.main import app
from fastapi.testclient import TestClient
from src.config import settings

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Create a session factory for testing
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def test_db():
    """
    Create a test database and tables before the tests, and drop them after
    """
    # Create the tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_db):
    """
    Create a database session for each test function
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    """
    Create a test client for the FastAPI application
    """
    with TestClient(app) as c:
        yield c

# Override the dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
