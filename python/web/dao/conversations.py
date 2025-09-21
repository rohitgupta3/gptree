from uuid import UUID

from sqlmodel import select, or_, Session
from sqlalchemy import func
from sqlalchemy.orm import aliased
from models.turn import Turn  # Adjust import as needed

from sqlalchemy import func, any_


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


def get_full_conversation_from_turn_id(session: Session, turn_id: UUID) -> list[Turn]:
    # Traverse up to root
    current = session.get(Turn, turn_id)
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
