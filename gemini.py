# simple_gemini_flash_lite.py

from google import genai

# Option A: rely on env var GEMINI_API_KEY
# export GEMINI_API_KEY="YOUR_API_KEY"
client = genai.Client()  # will read GEMINI_API_KEY automatically

MODEL = "gemini-2.5-flash-lite"

resp = client.models.generate_content(
    model=MODEL,
    contents="Write a concise checklist for preparing a coffee shop for opening."
)

# The SDK returns an object with .text (human text) and more metadata
print("=== GENERATED TEXT ===")
print(resp.text)

# If you want token counts or full response object:
# print(resp) 

