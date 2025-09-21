from uuid import UUID

from sqlmodel import Session

from models.turn import Turn


def _stub_gemini(session: Session, turn_id: UUID) -> None:
    """
    Stub function for Gemini API interaction.
    In the real implementation, this would call the actual Gemini API.
    """
    # Get the turn to access the human text
    turn = session.get(Turn, turn_id)
    if not turn:
        raise ValueError(f"Turn {turn_id} not found")

    # Generate a simple response based on the human input
    bot_response = f"I see that you said {turn.human_text}"

    # Update the turn with the bot response
    turn.bot_text = bot_response
    session.add(turn)
    session.commit()
