
from backend.app.config import settings
from google import genai


def main():
    if not settings.GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY is missing from .env")
        return

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents="Reply with exactly: KarigarConnect Gemini test successful",
        )
        print("Gemini API response received:")
        print(response.text)
    except Exception as error:
        print(f"Gemini test failed: {type(error).__name__}: {error}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
