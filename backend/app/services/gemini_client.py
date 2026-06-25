from __future__ import annotations

import os
import time
import random
from google import genai
from google.genai import types
from google.genai.errors import APIError

def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in backend/.env. Please add it to run the multimodal analysis.")
    return genai.Client(api_key=api_key)

def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def generate_content_with_retry(
    client: genai.Client,
    model: str,
    contents: any,
    config: types.GenerateContentConfig,
    max_retries: int = 5,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
) -> any:
    """
    Calls client.models.generate_content with exponential backoff and jitter
    to handle rate limits (429 / RESOURCE_EXHAUSTED) and temporary backend outages (503 / UNAVAILABLE).
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except APIError as exc:
            last_exception = exc
            err_str = str(exc)
            
            # Check for standard rate limiting or temporary server codes/messages
            status_code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
            is_transient = False
            
            if status_code in [429, 500, 503, 504]:
                is_transient = True
            elif any(msg in err_str for msg in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "quota"]):
                is_transient = True
                
            if not is_transient:
                # If it's a structural error (e.g. invalid arguments/schema/key), fail immediately
                raise exc
                
            if attempt == max_retries - 1:
                break
                
            sleep_time = delay + random.uniform(0.1, 1.0)
            print(f"[Gemini API] Request failed ({status_code or 'Transient Error'}). Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s...")
            time.sleep(sleep_time)
            delay *= backoff_factor
            
        except Exception as exc:
            # Catch other connection/HTTP library anomalies and retry
            last_exception = exc
            if attempt == max_retries - 1:
                break
            sleep_time = delay + random.uniform(0.1, 1.0)
            print(f"[Gemini Client] Unexpected exception: {exc}. Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s...")
            time.sleep(sleep_time)
            delay *= backoff_factor

    # If we exhausted all retries, raise the last encountered error
    if last_exception:
        raise last_exception
