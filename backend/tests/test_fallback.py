import os
from dotenv import load_dotenv
load_dotenv()
from google import genai
from google.genai import types
import json

c = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
models_to_try = ["gemini-3.1-pro-preview", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]

for model_name in models_to_try:
    try:
        print(f"\n--- Trying {model_name}... ---")
        response = c.models.generate_content(
            model=model_name,
            contents="Hello",
            config=types.GenerateContentConfig(
                temperature=0.1
            ),
        )
        print(f"Success ({model_name}):", response.text)
        break
    except Exception as e:
        print(f"Failed {model_name} with exception: {repr(e)}")
        error_msg = str(e).lower()
        if any(err in error_msg for err in ["429", "quota", "exhausted", "404", "400", "not_found", "403", "503", "unavailable"]):
            print(f"Model {model_name} failed, trying next...")
        else:
            print(f"Fatal error for {model_name}, breaking out.")
            break
