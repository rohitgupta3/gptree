import importlib
import pkgutil
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, select
from sqlalchemy.pool import StaticPool

from web.app import app, get_session, get_current_user, CurrentUser
from models.metadata import MAIN
from models.user import User
from models.turn import Turn

# SQLite test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Override the get_session dependency
def override_get_session():
    """Provides a mocked database session for testing."""
    with Session(engine) as session:
        yield session


# Define a mock for the current user to bypass the authentication dependency
class MockCurrentUser:
    def __init__(self, uid: str):
        self.uid = uid


def override_get_current_user():
    """Provides a mocked current user for testing."""
    return MockCurrentUser(uid="test_uid_123")


app.dependency_overrides[get_session] = override_get_session
app.dependency_overrides[get_current_user] = override_get_current_user

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
    with Session(engine) as session:
        user = session.exec(select(User).where(User.uid == "test_uid_123")).first()
        assert user is not None
        assert user.email == "test@example.com"


@patch("web.app._stub_gemini")
def test_create_conversation(mock_stub_gemini: Mock):
    """
    Tests the create_conversation endpoint and verifies a Turn is created.
    Uses mock.patch to simulate the gemini stub call.
    """
    # Create a user in the test database since the endpoint requires it.
    # The uid must match the one returned by the mocked get_current_user.
    with Session(engine) as session:
        user = User(uid="test_uid_123", email="test@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)

    # Define the behavior of the mock stub
    # It should modify the bot_text field of the Turn object
    def side_effect(session, turn_id):
        turn = session.exec(select(Turn).where(Turn.id == turn_id)).one()
        turn.bot_text = "Mocked bot response."
        session.add(turn)
        session.commit()

    mock_stub_gemini.side_effect = side_effect

    # Define the request payload
    payload = {"text": "Hello, Gemini!"}

    # Make the POST request to create a conversation
    response = client.post("/api/conversation/create", json=payload)

    # Assert the status code is 200
    assert response.status_code == 200

    # Assert the response contains the turn_id
    response_data = response.json()
    assert "turn_id" in response_data
    turn_id = response_data["turn_id"]

    # Verify that the Turn was created in the database
    with Session(engine) as session:
        db_turn = session.exec(select(Turn).where(Turn.id == turn_id)).one()
        assert db_turn is not None
        assert db_turn.human_text == "Hello, Gemini!"
        assert db_turn.user_id == user.id
        assert db_turn.parent_turn_id is None
        # Verify that the mock successfully mutated the Turn's bot_text
        assert db_turn.bot_text == "Mocked bot response."

    # Verify that the mocked stub was called with the correct arguments
    # with a MockSession, which should be fine.
    mock_stub_gemini.assert_called_once()
