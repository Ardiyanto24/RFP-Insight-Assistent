import os
from google import genai

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Set env GOOGLE_API_KEY terlebih dahulu")

    client = genai.Client(api_key=api_key)

    print("=== Available Models ===")
    for m in client.models.list():
        methods = getattr(m, "supported_generation_methods", [])
        print(f"- {m.name} | methods: {methods}")

if __name__ == "__main__":
    main()