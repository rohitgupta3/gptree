from sqlmodel import Session, select
from uuid import uuid4, UUID
from models.user import User
from models.turn import Turn  # Adjust if Turn is elsewhere
from datetime import datetime
from typing import Optional


# TODO: vet this
def seed_turns(session: Session, user_id: UUID | None = None):
    if user_id is None:
        user = session.scalars(select(User).where(User.email == "test@test.com")).one()
        user_id = user.id
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

    all_turns: dict[str, Turn] = {}
    column_heads: list[Turn] = []
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


if __name__ == "__main__":
    from database.database import engine

    with Session(engine) as session:
        seed_turns(session)
