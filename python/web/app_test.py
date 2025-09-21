import importlib
import pkgutil

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from web.app import app, get_session
from models.metadata import MAIN
from models.user import User

# SQLite test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_session dependency
def override_get_session():
    """Provides a mocked database session for testing."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_session] = override_get_session

# Create the test client after the dependency is overridden
client = TestClient(app)


# Create test database
# TODO: DRY this with everywhere else
def import_modules(package, recursive=True):
    """
    Import all submodules of a module, recursively, including subpackages.
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    for _, name, is_pkg in pkgutil.walk_packages(package.__path__):
        if "." in name:
            continue
        full_name = package.__name__ + "." + name
        importlib.import_module(full_name)
        if recursive and is_pkg:
            import_modules(full_name)


# Import all models recursively under python/models, this allows the DB reset to work
import_modules("models")
MAIN.create_all(bind=engine)


def test_create_user():
    """Tests the create_user endpoint."""
    # Define the payload
    payload = {"uid": "test_uid_123", "email": "test@example.com"}

    # Make the POST request
    response = client.post("/api/user", json=payload)

    # Assert the status code is 200 OK
    assert response.status_code == 200

    # Assert the response data is correct
    data = response.json()
    assert "user_id" in data

    # You can also verify the user was added to the mock database
    session = TestingSessionLocal()
    user = session.query(User).filter_by(uid="test_uid_123").first()
    assert user is not None
    assert user.email == "test@example.com"
