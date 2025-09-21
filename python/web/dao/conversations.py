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
