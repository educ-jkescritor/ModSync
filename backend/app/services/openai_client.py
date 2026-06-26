from __future__ import annotations

import json
import os
import random
import time
from typing import Any


def get_openai_client() -> Any:
    use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() != "false"
    if use_local_llm:
        from openai import OpenAI
        base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
        api_key = os.getenv("LOCAL_LLM_API_KEY", "local")
        return OpenAI(base_url=base_url, api_key=api_key)

    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        from openai import OpenAI

        return OpenAI(api_key=api_key)
    if os.getenv("GEMINI_API_KEY"):
        return None
    raise ValueError(
        "OPENAI_API_KEY, GEMINI_API_KEY or USE_LOCAL_LLM is not set in backend/.env. Please configure one to run the AI agents."
    )


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def get_ai_model() -> str:
    use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() != "false"
    if use_local_llm:
        return get_openai_model()
    if os.getenv("OPENAI_API_KEY"):
        return get_openai_model()
    return get_gemini_model()


def get_openai_model() -> str:
    use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() != "false"
    if use_local_llm:
        return os.getenv("LOCAL_LLM_TEXT_MODEL", os.getenv("LOCAL_LLM_MODEL", "gpt-oss"))
    return os.getenv("OPENAI_MODEL", "gpt-4o")


def get_vision_model() -> str:
    use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() != "false"
    if use_local_llm:
        return os.getenv("LOCAL_LLM_VISION_MODEL", os.getenv("LOCAL_LLM_MODEL", "llava"))
    if os.getenv("OPENAI_API_KEY"):
        return get_openai_model()
    return get_gemini_model()


def get_review_model() -> str:
    use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() != "false"
    if use_local_llm:
        return os.getenv("LOCAL_LLM_MODEL", "qwen")
    if os.getenv("OPENAI_API_KEY"):
        return get_openai_model()
    return get_gemini_model()


def _gemini_available() -> bool:
    use_local_llm = os.getenv("USE_LOCAL_LLM", "true").lower() != "false"
    if use_local_llm:
        return False
    return bool(os.getenv("GEMINI_API_KEY"))


def _extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text", "")))
    return "\n".join(part for part in parts if part)


def _extract_image_data_from_content(content: Any) -> list[dict[str, str]]:
    if not isinstance(content, list):
        return []
    images: list[dict[str, str]] = []
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "image_url":
            continue
        image_url = item.get("image_url", {})
        url = image_url.get("url", "") if isinstance(image_url, dict) else ""
        marker = "base64,"
        if marker not in url:
            continue
        mime_type = url.split(";", 1)[0].replace("data:", "") or "image/png"
        images.append({"mime_type": mime_type, "data": url.split(marker, 1)[1]})
    return images


def _messages_to_gemini_request(messages: list[dict[str, Any]]) -> tuple[str | None, list[Any]]:
    import base64
    from google.genai import types

    system_parts: list[str] = []
    contents: list[Any] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        text = _extract_text_from_content(content)
        if role == "system":
            if text:
                system_parts.append(text)
            continue
        if text:
            contents.append(text)
        for image in _extract_image_data_from_content(content):
            contents.append(
                types.Part.from_bytes(
                    data=base64.b64decode(image["data"]),
                    mime_type=image["mime_type"],
                )
            )
    return "\n\n".join(system_parts) or None, contents


def _generate_json_with_gemini(
    messages: list[dict[str, Any]],
    temperature: float,
) -> dict[str, Any]:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set in backend/.env. Cannot use Gemini fallback."
        )
    system_instruction, contents = _messages_to_gemini_request(messages)
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=get_gemini_model(),
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=temperature,
        ),
    )
    return json.loads(response.text or "{}")


def _openai_error_details(exc: Exception) -> str:
    details: dict[str, Any] = {
        "status_code": getattr(exc, "status_code", None),
        "code": getattr(exc, "code", None),
        "type": getattr(exc, "type", None),
        "message": str(exc),
    }
    body = getattr(exc, "body", None)
    if body:
        details["body"] = body
    response = getattr(exc, "response", None)
    if response is not None:
        request_id = getattr(response, "headers", {}).get("x-request-id")
        if request_id:
            details["request_id"] = request_id
    return json.dumps({key: value for key, value in details.items() if value}, default=str)


def _retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {}) if response is not None else {}
    retry_after = headers.get("retry-after") if headers else None
    if not retry_after:
        return None
    try:
        return float(retry_after)
    except ValueError:
        return None


def _is_non_retryable_429(exc: Exception) -> bool:
    body = getattr(exc, "body", None)
    code = getattr(exc, "code", None)
    text = f"{code} {body} {exc}".lower()
    return any(
        marker in text
        for marker in (
            "insufficient_quota",
            "billing",
            "exceeded your current quota",
            "check your plan and billing",
        )
    )


def generate_json_with_retry(
    client: Any,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.1,
    max_retries: int = 2,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    Calls OpenAI chat completions with JSON output and retries transient failures.
    """
    delay = initial_delay
    last_exception: Exception | None = None

    if timeout is None:
        timeout = 180.0

    if client is None:
        print(f"[Gemini API] Using Gemini ({get_gemini_model()}) because OPENAI_API_KEY is not configured.")
        return _generate_json_with_gemini(messages, temperature)

    for attempt in range(max_retries):
        try:
            from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=temperature,
                timeout=timeout,
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except (RateLimitError, APITimeoutError, APIConnectionError, APIError) as exc:
            last_exception = exc
            status_code = getattr(exc, "status_code", None)
            if status_code and status_code not in {429, 500, 502, 503, 504}:
                if _gemini_available():
                    print(
                        f"[OpenAI API] Failed with non-retryable error; falling back to Gemini "
                        f"({get_gemini_model()}): {_openai_error_details(exc)}"
                    )
                    return _generate_json_with_gemini(messages, temperature)
                raise
            if status_code == 429 and _is_non_retryable_429(exc):
                print(f"[OpenAI API] Non-retryable 429: {_openai_error_details(exc)}")
                if _gemini_available():
                    print(f"[Gemini API] Falling back to Gemini ({get_gemini_model()}).")
                    return _generate_json_with_gemini(messages, temperature)
                raise
            if attempt == max_retries - 1:
                break
            retry_after = _retry_after_seconds(exc)
            sleep_time = max(delay, retry_after or 0) + random.uniform(0.1, 1.0)
            print(
                f"[OpenAI API] Request failed ({status_code or 'transient error'}): "
                f"{_openai_error_details(exc)}. "
                f"Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s..."
            )
            time.sleep(sleep_time)
            delay *= backoff_factor
        except Exception as exc:
            last_exception = exc
            if attempt == max_retries - 1:
                break
            sleep_time = delay + random.uniform(0.1, 1.0)
            print(
                f"[OpenAI Client] Unexpected exception: {exc}. "
                f"Retrying attempt {attempt + 1}/{max_retries} in {sleep_time:.2f}s..."
            )
            time.sleep(sleep_time)
            delay *= backoff_factor

    if last_exception:
        if _gemini_available():
            print(
                f"[OpenAI API] Exhausted retries; falling back to Gemini "
                f"({get_gemini_model()}): {_openai_error_details(last_exception)}"
            )
            return _generate_json_with_gemini(messages, temperature)
        raise last_exception
    return {}
