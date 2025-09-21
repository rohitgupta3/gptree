#!/usr/bin/env python3
"""
Terminal Chatbot using Google Gemini AI
Run this script to start an interactive chat session in your terminal.
"""

import sys

from google import genai


def main():
    print("🤖 Terminal Chatbot - Powered by Gemini 2.5 Flash")
    print("=" * 50)
    print("Type 'quit', 'exit', or 'bye' to end the conversation")
    print("Type 'history' to see conversation history")
    print("Type 'clear' to start a new conversation")
    print("-" * 50)

    try:
        history = [
            {"role": "user", "parts": [{"text": "Who won the World Cup in 2018?"}]},
            {
                "role": "model",
                "parts": [{"text": "France won the 2018 FIFA World Cup."}],
            },
            {"role": "user", "parts": [{"text": "Who was the captain?"}]},
            {
                "role": "model",
                "parts": [{"text": "Hugo Lloris was the captain of the French team."}],
            },
        ]

        for item in history:
            if item["role"] == "user":
                user_symbol = "👤 You"
            elif item["role"] == "model":
                user_symbol = "🤖 Bot"
            print(f"\n{user_symbol}: {item['parts'][0]['text']}")

        # Initialize the client and chat
        client = genai.Client()
        chat = client.chats.create(model="gemini-2.5-flash", history=history)

        while True:
            # Get user input
            try:
                user_input = input("\n👤 You: ").strip()
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break

            # Handle special commands
            if user_input.lower() in ["quit", "exit", "bye"]:
                print("Goodbye! 👋")
                break

            elif user_input.lower() == "history":
                print("\n📚 Conversation History:")
                print("-" * 30)
                for i, message in enumerate(chat.get_history(), 1):
                    role_emoji = "👤" if message.role == "user" else "🤖"
                    print(
                        f"{i}. {role_emoji} {message.role.title()}: {message.parts[0].text}"
                    )
                continue

            elif user_input.lower() == "clear":
                # Start a new chat session
                chat = client.chats.create(model="gemini-2.5-flash")
                print("🔄 Conversation cleared. Starting fresh!")
                continue

            elif user_input == "":
                print("Please enter a message.")
                continue

            # Send message and get response
            try:
                print("🤖 Bot: ", end="", flush=True)
                response = chat.send_message(user_input)
                print(response.text)

            except Exception as e:
                print(f"❌ Error getting response: {e}")
                print("Please try again or type 'quit' to exit.")

    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        print("Please check your Google AI setup and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
