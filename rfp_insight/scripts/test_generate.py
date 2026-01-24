import os
from google import genai

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set env GOOGLE_API_KEY dulu")

    client = genai.Client(api_key=api_key)

    model_name = "models/gemini-2.5-flash"  # pakai persis seperti ListModels
    resp = client.models.generate_content(
        model=model_name,
        contents="Balas singkat: OK"
    )
    print("SUCCESS")
    print(resp.text)

if __name__ == "__main__":
    main()