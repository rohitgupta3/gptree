import os
from uuid import UUID

from sqlmodel import Session
from google import genai

from models.turn import Turn


client = genai.Client()  # will read GEMINI_API_KEY automatically

# TODO: abstract
MODEL = "gemini-2.5-flash-lite"

USE_GEMINI = os.environ["USE_GEMINI"] == "1"


def gemini_with_fallback(session: Session, turn_id: UUID) -> None:
    """
    Stub function for Gemini API interaction.
    In the real implementation, this would call the actual Gemini API.
    """
    if USE_GEMINI:
        return gemini(session, turn_id)
    else:
        return gemini_fallback(session, turn_id)


def gemini_fallback(session: Session, turn_id: UUID) -> None:
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


def gemini(session: Session, turn_id: UUID) -> None:
    """
    Stub function for Gemini API interaction.
    In the real implementation, this would call the actual Gemini API.
    """
    # Get the turn to access the human text
    turn = session.get(Turn, turn_id)
    if not turn:
        raise ValueError(f"Turn {turn_id} not found")

    # Generate a simple response based on the human input
    # bot_response = f"I see that you said {turn.human_text}"

    resp = client.models.generate_content(
        model=MODEL,
        # contents="Write a concise checklist for preparing a coffee shop for opening.",
        contents=turn.human_text,
    )

    # # The SDK returns an object with .text (human text) and more metadata
    # print("=== GENERATED TEXT ===")
    # print(resp.text)

    # Update the turn with the bot response
    turn.bot_text = resp.text
    session.add(turn)
    session.commit()
