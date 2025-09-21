import os
from uuid import UUID

from sqlmodel import Session
from google import genai

from models.turn import Turn
from web.dao import conversations

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
        # return gemini(session, turn_id)
        return gemini_with_history(session, turn_id)
    else:
        return gemini_fallback(session, turn_id)


def gemini_with_history(session: Session, turn_id: UUID) -> None:
    # for item in history:
    #     if item["role"] == "user":
    #         user_symbol = "👤 You"
    #     elif item["role"] == "model":
    #         user_symbol = "🤖 Bot"
    #     print(f"\n{user_symbol}: {item['parts'][0]['text']}")

    # # Initialize the client and chat
    # client = genai.Client()
    # # chat = client.chats.create(model="gemini-2.5-flash", history=history)
    # chat = client.chats.create(model="gemini-2.5-flash", history=history)

    # Get the turn to access the human text
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
    session.add(turn)
    session.commit()


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
