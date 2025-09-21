from sqlmodel import select, or_, Session
from sqlalchemy import func
from sqlalchemy.orm import aliased
from models.turn import Turn  # Adjust import as needed


def get_separable_conversations(session: Session) -> list[Turn]:
    TurnAlias = aliased(Turn)

    # Subquery: joins each turn with its parent
    stmt = (
        select(Turn)
        .outerjoin(TurnAlias, Turn.parent_id == TurnAlias.id)
        .where(
            or_(
                Turn.parent_id == None,  # noqa: E711
                func.coalesce(TurnAlias.branched_child_ids, []).contains([Turn.id]),
            )
        )
        .order_by(Turn.created_at.desc())
    )

    return session.exec(stmt).all()
