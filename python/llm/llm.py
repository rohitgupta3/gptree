import os
from uuid import UUID

from google import genai
from models.turn import Turn
from sqlmodel import Session
from web.dao import conversations

client = genai.Client()  # will read GEMINI_API_KEY automatically

# TODO: abstract the model
MODEL = "gemini-2.5-flash-lite"

USE_GEMINI = os.environ.get("USE_GEMINI", "0") == "1"


def gemini_with_fallback(
    session: Session, turn_id: UUID, *, create_title: bool = False
) -> None:
    """
    Stub function for Gemini API interaction.
    In the real implementation, this would call the actual Gemini API.
    """
    if USE_GEMINI:
        return gemini_with_history(session, turn_id, create_title=create_title)
    else:
        return gemini_fallback(session, turn_id, create_title=create_title)


def gemini_with_history(
    session: Session, turn_id: UUID, *, create_title: bool = False
) -> None:
    turn = session.get(Turn, turn_id)
    if not turn:
        raise ValueError(f"Turn {turn_id} not found")

    prev_conversation = conversations.get_full_conversation_from_turn_id(
        session, turn_id, turn.user_id
    )

    history = []

    for turn in prev_conversation:
        if turn.human_text:
            history.append(
                {
                    "role": "user",
                    "parts": [{"text": turn.human_text}],
                }
            )
        if turn.bot_text:
            history.append(
                {
                    "role": "model",
                    "parts": [{"text": turn.bot_text}],
                }
            )

    chat = client.chats.create(model=MODEL, history=history)
    response = chat.send_message(turn.human_text)
    turn.bot_text = response.text
    # Don't think we need `add`
    session.add(turn)
    session.commit()

    try:
        chat_for_title = client.chats.create(model=MODEL, history=history)
        response = chat_for_title.send_message(
            "Make a very short title for this chat, i.e. summarize the point of it in two or three words, no formatting at all"
        )
        turn.title = response.text[:50]
        session.add(turn)
        session.commit()
    except Exception as e:
        print(e)


def gemini_fallback(
    session: Session, turn_id: UUID, *, create_title: bool = False
) -> None:
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
    turn = session.get(Turn, turn_id)
    if not turn:
        raise ValueError(f"Turn {turn_id} not found")

    resp = client.models.generate_content(
        model=MODEL,
        contents=turn.human_text,
    )

    # Update the turn with the bot response
    turn.bot_text = resp.text
    session.add(turn)
    session.commit()
