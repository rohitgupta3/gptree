import os
from unittest.mock import Mock, patch

import pytest
from database import seed
from database.database import create_all_tables
from fastapi.testclient import TestClient
from models.turn import Turn
from models.user import User
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine, select
from web.dao import conversations

# TODO: DRY with other test files

DATABASE_URL = os.environ["TEST_DATABASE_URL"]

# Fix for PostgreSQL URLs from Heroku
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

create_all_tables(engine)


@pytest.fixture(name="db_session")
def db_session_fixture():
    """
    A transactional fixture that yields a database session and
    rolls back the transaction after the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


def test_separable_conversation(db_session: Session):
    user = User(uid="test_uid_123", email="test@example.com")
    db_session.add(user)
    db_session.commit()

    seed.seed_turns(db_session, user.id)
    separable_conversations = conversations.get_separable_conversations(
        db_session, user.id
    )
    assert len(separable_conversations) == 3

    # TODO: hardcoded to same text in seed, a bit brittle
    texts = [
        "Can you explain to me the BJT (semiconductor)?",
        "Can you explain to me the basics of semiconductors first?",
        "Why does the depletion region create an electric field?",
    ]
    stmt = select(Turn).where(Turn.human_text.in_(texts))
    expected_ids = [row.id for row in db_session.exec(stmt).all()]
    assert sorted(expected_ids) == sorted(
        [conversation.id for conversation in separable_conversations]
    )


def test_full_conversation_from_identifying_turn_id(db_session: Session):
    user = User(uid="test_uid_123", email="test@example.com")
    db_session.add(user)
    db_session.commit()

    seed.seed_turns(db_session, user.id)

    # Grab the turn whose human_text is the identifying input
    stmt = select(Turn).where(
        Turn.human_text == "Can you explain to me the basics of semiconductors first?"
    )
    identifying_turn = db_session.exec(stmt).one()

    # Import function under test

    full_convo = conversations.get_full_conversation_from_turn_id(
        db_session, identifying_turn.id, user.id
    )

    # Assert expected sequence
    expected_texts = [
        "Can you explain to me the BJT (semiconductor)?",
        "Can you explain to me the basics of semiconductors first?",
        "Can you explain the p-n junction?",
        "What’s the difference between “p-side” and “p-terminal”?",
    ]

    assert [turn.human_text for turn in full_convo] == expected_texts


def test_reply_to_turn(db_session: Session):
    # Create user
    user = User(uid="reply_test_uid", email="reply@test.com")
    db_session.add(user)
    db_session.commit()

    # Create original turn
    prev_turn = Turn(
        user_id=user.id,
        human_text="What is a semiconductor?",
        bot_text="A semiconductor is a material with conductivity between conductors and insulators.",
        model="gemini-2.5-flash",
        title="Semiconductors",
    )
    db_session.add(prev_turn)
    db_session.commit()
    db_session.refresh(prev_turn)

    # Import and call function under test

    new_turn = conversations.reply_to_turn(
        session=db_session,
        user_id=user.id,
        parent_turn_id=prev_turn.id,
        text="Why are semiconductors useful?",
    )

    # Reload both turns
    updated_prev = db_session.get(Turn, prev_turn.id)
    updated_new = db_session.get(Turn, new_turn.id)

    # Assertions
    assert updated_new.parent_id == updated_prev.id
    assert updated_prev.primary_child_id == updated_new.id
    assert updated_new.human_text == "Why are semiconductors useful?"


def test_branch_reply_to_turn(db_session: Session):
    # Create user
    user = User(uid="reply_test_uid", email="reply@test.com")
    db_session.add(user)
    db_session.commit()

    # Create original turn
    prev_turn = Turn(
        user_id=user.id,
        human_text="What is a semiconductor?",
        bot_text="A semiconductor is a material with conductivity between conductors and insulators.",
        model="gemini-2.5-flash",
        title="Semiconductors",
    )
    db_session.add(prev_turn)
    db_session.commit()
    db_session.refresh(prev_turn)

    # Import and call function under test

    new_turn = conversations.branch_reply_to_turn(
        session=db_session,
        user_id=user.id,
        parent_turn_id=prev_turn.id,
        text="What does conductivity mean?",
    )

    # Reload both turns
    updated_prev = db_session.get(Turn, prev_turn.id)
    updated_new = db_session.get(Turn, new_turn.id)

    # Assertions
    assert updated_new.parent_id == updated_prev.id
    assert updated_prev.primary_child_id is None
    assert updated_prev.branched_child_ids == [updated_new.id]
    assert updated_new.human_text == "What does conductivity mean?"
