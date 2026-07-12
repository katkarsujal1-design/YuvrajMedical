import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from the .env file")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents="Reply exactly with: Yuvraj Medical chatbot is working"
    )

    print(response.text)

except Exception as error:
    print("Gemini API error:")
    print(error)
