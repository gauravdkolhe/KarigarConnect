
import time

import litellm

from backend.app.config import settings


def main():
    print("Testing Gemini through LiteLLM...", flush=True)
    start = time.time()

    try:
        response = litellm.completion(
            model="gemini/gemini-3.8-flash",
            api_key=settings.GEMINI_API_KEY,
            messages=[
                {
                    "role": "user",
                    "content": "Reply with exactly: LITELLM_OK",
                }
            ],
            timeout=30,
            num_retries=0,
        )

        print("Response:", response.choices[0].message.content)
        print(f"Elapsed: {time.time() - start:.1f} seconds")

    except Exception as error:
        print(f"Error: {type(error).__name__}: {error}")
        print(f"Elapsed: {time.time() - start:.1f} seconds")


if __name__ == "__main__":
    main()
