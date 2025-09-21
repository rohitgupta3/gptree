from sqlmodel import Session, select, delete
from uuid import uuid4, UUID
from models.user import User
from models.turn import Turn  # Adjust if Turn is elsewhere
from datetime import datetime
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
    )
    purple_2 = (
        "Is there any usage of BJT amplifiers besides audio amplification?",
        None,
    )
    blue_1 = (
        "Can you explain to me the basics of semiconductors first?",
        "Sure! Let’s start with the basics of semiconductors, which are materials...",
    )
    blue_2 = (
        "Can you explain the p-n junction?",
        "A p-n junction is the basic building block of semiconductor devices, such as diodes",
    )
    blue_3 = (
        "What’s the difference between “p-side” and “p-terminal”?",
        "The terms p-side and p-terminal refer to different aspects of a semiconductor...",
    )
    green_1 = (
        "Why does the depletion region create an electric field?",
        "The depletion region in a p-n junction creates an electric field due to...",
    )

    purple_1_turn = Turn(
        user_id=user_id,
        human_text=purple_1[0],
        bot_text=purple_1[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
    )
    purple_2_turn = Turn(
        user_id=user_id,
        human_text=purple_2[0],
        bot_text=purple_2[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
    )
    blue_1_turn = Turn(
        user_id=user_id,
        human_text=blue_1[0],
        bot_text=blue_1[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
    )
    blue_2_turn = Turn(
        user_id=user_id,
        human_text=blue_2[0],
        bot_text=blue_2[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
    )
    blue_3_turn = Turn(
        user_id=user_id,
        human_text=blue_3[0],
        bot_text=blue_3[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
    )
    green_1_turn = Turn(
        user_id=user_id,
        human_text=green_1[0],
        bot_text=green_1[1],
        model="gemini-2.5-flash",
        parent_id=None,
        primary_child_id=None,
        branched_child_ids=[],
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


# TODO: vet this
def seed_turns_broken(session: Session, user_id: UUID | None = None) -> bool:
    # Each item is a column (linear chain). Each entry is a (human_text, bot_text) pair.
    conversations = [
        [  # Column 1 (purple)
            (
                "Can you explain to me the BJT (semiconductor)?",
                "A BJT (Bipolar Junction Transistor) is a type of semiconductor device that can amplify or switch electrical signals",
            ),
            ("Is there any usage of BJT amplifiers besides audio amplification?", None),
        ],
        [  # Column 2 (blue)
            (
                "Can you explain to me the basics of semiconductors first?",
                "Sure! Let’s start with the basics of semiconductors, which are materials...",
            ),
            (
                "Can you explain the p-n junction?",
                "A p-n junction is the basic building block of semiconductor devices, such as diodes",
            ),
            (
                "What’s the difference between “p-side” and “p-terminal”?",
                "The terms p-side and p-terminal refer to different aspects of a semiconductor...",
            ),
        ],
        [  # Column 3 (green, branches off after "Can you explain the p-n junction?")
            (
                "Why does the depletion region create an electric field?",
                "The depletion region in a p-n junction creates an electric field due to...",
            ),
        ],
    ]

    prev_turn_by_column: dict[int, Turn] = {}

    for col_idx, column in enumerate(conversations):
        for idx, (human_text, bot_text) in enumerate(column):
            turn = Turn(
                id=uuid4(),
                user_id=user_id,
                human_text=human_text,
                bot_text=bot_text,
                model="gemini-2.5-flash",
                parent_id=None,
                primary_child_id=None,
                branched_child_ids=[],
            )

            # Link to previous turn in the column
            if idx > 0:
                parent = prev_turn_by_column[col_idx]
                turn.parent_id = parent.id
                parent.primary_child_id = turn.id
                session.add(parent)  # Update parent with primary_child_id
            elif col_idx > 0 and col_idx == 2:
                # This is the green column, which is a branch off blue's second turn
                branching_parent = prev_turn_by_column[
                    1
                ]  # "Can you explain the p-n junction?"
                turn.parent_id = branching_parent.id
                branching_parent.branched_child_ids.append(turn.id)
                session.add(branching_parent)

            session.add(turn)
            prev_turn_by_column[col_idx] = turn

    session.commit()
    return True


if __name__ == "__main__":
    from database.database import engine

    with Session(engine) as session:
        seed_turns(session)
