from sqlmodel import Session, select, delete
from uuid import uuid4, UUID
from models.user import User
from models.turn import Turn  # Adjust if Turn is elsewhere
import datetime
from typing import Optional


def seed_turns(session: Session, user_id: UUID | None = None) -> bool:
    session.exec(delete(Turn))
    session.commit()

    if user_id is None:
        user = session.scalars(select(User).where(User.email == "test@test.com")).one()
        user_id = user.id

    purple_1 = (
        "Can you explain to me the BJT (semiconductor)?",
        "A BJT (Bipolar Junction Transistor) is a type of semiconductor device that can amplify or switch electrical signals",
        "Purple",
    )
    purple_2 = (
        "Is there any usage of BJT amplifiers besides audio amplification?",
        None,
        "Purple",
    )
    blue_1 = (
        "Can you explain to me the basics of semiconductors first?",
        "Sure! Let’s start with the basics of semiconductors, which are materials...",
        "Blue",  # TODO: "BJT / semiconductors" or something
    )
    blue_2 = (
        "Can you explain the p-n junction?",
        "A p-n junction is the basic building block of semiconductor devices, such as diodes",
        "Blue",
    )
    blue_3 = (
        "What’s the difference between “p-side” and “p-terminal”?",
        "The terms p-side and p-terminal refer to different aspects of a semiconductor...",
        "Blue",
    )
    green_1 = (
        "Why does the depletion region create an electric field?",
        "The depletion region in a p-n junction creates an electric field due to...",
        "Green",  # TODO: something else
    )

    purple_1_turn = Turn(
        user_id=user_id,
        title=purple_1[2],
        human_text=purple_1[0],
        bot_text=purple_1[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
        created_at=datetime.datetime.now(datetime.UTC),
    )
    purple_2_turn = Turn(
        user_id=user_id,
        title=purple_2[2],
        human_text=purple_2[0],
        bot_text=purple_2[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
        created_at=datetime.datetime.now(datetime.UTC),
    )
    blue_1_turn = Turn(
        user_id=user_id,
        title=blue_1[2],
        human_text=blue_1[0],
        bot_text=blue_1[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
        created_at=datetime.datetime.now(datetime.UTC),
    )
    blue_2_turn = Turn(
        user_id=user_id,
        title=blue_2[2],
        human_text=blue_2[0],
        bot_text=blue_2[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
        created_at=datetime.datetime.now(datetime.UTC),
    )
    blue_3_turn = Turn(
        user_id=user_id,
        title=blue_3[2],
        human_text=blue_3[0],
        bot_text=blue_3[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
        created_at=datetime.datetime.now(datetime.UTC),
    )
    green_1_turn = Turn(
        user_id=user_id,
        title=green_1[2],
        human_text=green_1[0],
        bot_text=green_1[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
        created_at=datetime.datetime.now(datetime.UTC),
    )
    session.add_all(
        [
            purple_1_turn,
            purple_2_turn,
            blue_1_turn,
            blue_2_turn,
            blue_3_turn,
            green_1_turn,
        ]
    )
    session.commit()

    purple_1_turn.primary_child_id = purple_2_turn.id
    purple_2_turn.parent_id = purple_1_turn.id

    purple_1_turn.branched_child_ids = [blue_1_turn.id]
    blue_1_turn.parent_id = purple_1_turn.id

    blue_1_turn.primary_child_id = blue_2_turn.id
    blue_2_turn.parent_id = blue_1_turn.id

    blue_2_turn.primary_child_id = blue_3_turn.id
    blue_3_turn.parent_id = blue_2_turn.id

    blue_2_turn.branched_child_ids = [green_1_turn.id]
    green_1_turn.parent_id = blue_2_turn.id

    session.commit()

    return True


if __name__ == "__main__":
    from database.database import engine

    with Session(engine) as session:
        seed_turns(session)
