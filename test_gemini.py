import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from the .env file")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model=model,
        contents="Reply exactly with: Yuvraj Medical chatbot is working"
    )

    print(response.text)

except Exception as error:
    print("Gemini API error:")
    print(error)
