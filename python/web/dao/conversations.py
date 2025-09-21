from uuid import UUID

from models.turn import Turn  # Adjust import as needed
from sqlalchemy import any_, func
from sqlalchemy.orm import aliased
from sqlmodel import Session, or_, select


def get_separable_conversations(session: Session, user_id: UUID) -> list[Turn]:
    TurnAlias = aliased(Turn)

    stmt = (
        select(Turn)
        .outerjoin(TurnAlias, Turn.parent_id == TurnAlias.id)
        .where(
            Turn.user_id == user_id,
            or_(
                Turn.parent_id == None,  # noqa: E711
                Turn.id == any_(TurnAlias.branched_child_ids),
            ),
        )
        .order_by(Turn.created_at.desc())
    )

    return session.exec(stmt).all()


def get_full_conversation_from_turn_id(
    session: Session, turn_id: UUID, user_id: UUID
) -> list[Turn]:
    # Traverse up to root
    current = session.get(Turn, turn_id)
    if current.user_id != user_id:
        raise ValueError("User is not authorized")

    if not current:
        return []

    earlier = [current]

    while current.parent_id:
        current = session.get(Turn, current.parent_id)
        earlier = [current, *earlier]

    # Traverse down primary_child_id path as long as it's part of the original lineage
    # TODO: this is inelegant
    current = session.get(Turn, turn_id)
    if not current.primary_child_id:
        return earlier
    current = session.get(Turn, current.primary_child_id)
    while current:
        earlier.append(current)
        if not current.primary_child_id:
            break
        next_turn = session.get(Turn, current.primary_child_id)
        current = next_turn

    return earlier


# Double-check that the last turn in a conversation is being returned, not the identifying
# turn ID for a conversation
def reply_to_turn(
    session: Session,
    user_id: UUID,
    parent_turn_id: UUID,
    text: str,
) -> Turn:
    prev_turn = session.get(Turn, parent_turn_id)

    if not prev_turn or prev_turn.user_id != user_id:
        raise ValueError("Invalid turn or unauthorized")

    # Create the reply turn
    new_turn = Turn(
        user_id=user_id,
        human_text=text,
        model="gemini-2.5-flash",
        title=prev_turn.title,
        parent_id=prev_turn.id,
        bot_text=None,
    )

    session.add(new_turn)
    session.commit()
    session.refresh(new_turn)

    # Update prev_turn to point to new_turn
    prev_turn.primary_child_id = new_turn.id
    session.add(prev_turn)
    session.commit()

    return new_turn


def branch_reply_to_turn(
    session: Session,
    user_id: UUID,
    parent_turn_id: UUID,
    text: str,
) -> Turn:
    parent = session.get(Turn, parent_turn_id)

    if not parent or parent.user_id != user_id:
        raise ValueError("Invalid parent or unauthorized")

    # Create a new Turn
    new_turn = Turn(
        user_id=user_id,
        human_text=text,
        model="gemini-2.5-flash",
        title=parent.title + " - branch",
        parent_id=parent.id,
        bot_text=None,
    )

    session.add(new_turn)
    session.commit()
    session.refresh(new_turn)

    # Update branched_child_ids
    parent.branched_child_ids = parent.branched_child_ids or []
    parent.branched_child_ids.append(new_turn.id)

    session.add(parent)
    session.commit()

    return new_turn
