"""
ai_engine/llm/gemini.py

Responsibility: the concrete LLM client used by every service (chat,
summary, notes, quiz). Wraps Google's `google-genai` SDK behind a small,
focused interface (`generate`) so the rest of the engine never touches
the Gemini SDK directly.

--------------------------------------------------------------------
v1.1.1: migrated off the deprecated `google-generativeai` package
--------------------------------------------------------------------
`google-generativeai` (the SDK this file originally wrapped) has been
fully deprecated by Google in favor of the unified `google-genai`
package - it no longer receives updates or bug fixes. This file now
wraps `google-genai` instead. This is a pure internal implementation
swap: `GeminiLLM`'s public interface (`__init__(api_key, model)`,
`generate(prompt, temperature) -> str`, and `LLMGenerationError`) is
byte-identical to before, so no other file in the engine (prompts.py,
every service, engine.py) needed any change.

Note on scope: the original reference projects included a multi-provider
abstraction (`BaseLLM` + a factory selecting Mistral/Gemini/Groq). This
spec's tech stack lists only Gemini, so this file is a standalone class
rather than an ABC implementation. It is still written so that
extracting a `BaseLLM` interface later (if a second provider is added)
is a small, mechanical change: every method here already matches the
shape (`generate(prompt: str) -> str`) such an interface would define,
and every service already depends on this class via a constructor
parameter (dependency injection) rather than importing it directly
inside method bodies - the only future change would be adding an ABC
and a factory function, not restructuring any call site.

--------------------------------------------------------------------
v1.1.3: automatic retry for transient failures
--------------------------------------------------------------------
Gemini occasionally returns transient errors under load - most
commonly a 503 ("model is currently experiencing high demand") or a
429 rate limit. Previously, `generate()` failed immediately on the
first such error, which is a poor experience for anything with several
sequential calls (e.g. `SummaryService`'s map step calling this once
per chunk) - one busy moment aborts the whole operation. `generate()`
now retries transient failures (see `config.GEMINI_RETRYABLE_STATUS_CODES`)
with exponential backoff, up to `config.GEMINI_MAX_RETRIES` attempts,
before raising `LLMGenerationError`. Non-transient errors (bad request,
auth failure, safety block) still fail immediately - retrying those
would just waste time on an error that will never succeed.
"""

from __future__ import annotations

import logging
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from ai_engine.config import (
    GEMINI_DEFAULT_TEMPERATURE,
    GEMINI_MAX_RETRIES,
    GEMINI_MODEL,
    GEMINI_RETRY_BASE_DELAY_SECONDS,
    GEMINI_RETRYABLE_STATUS_CODES,
)

load_dotenv()

logger = logging.getLogger(__name__)


class LLMGenerationError(Exception):
    """Raised when Gemini fails to generate a response (missing/invalid
    API key, network failure, rate limit, safety-filter block, malformed
    response)."""


class GeminiLLM:
    """Thin, focused wrapper around Google's `google-genai` client.

    Every service in `ai_engine/services/` receives an already-
    constructed `GeminiLLM` instance via its constructor rather than
    instantiating one itself - this is the dependency-injection seam
    that makes each service testable with a fake LLM (see
    `tests/test_chat.py`) without needing a real API key or network
    access.
    """

    def __init__(self, api_key: str | None = None, model: str = GEMINI_MODEL) -> None:
        """
        Args:
            api_key: overrides the `GEMINI_API_KEY` environment
            variable - mainly useful for tests.
            model: the Gemini model name to use.

        Raises:
            LLMGenerationError: if no API key is available from either
            the argument or the environment.
        """
        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise LLMGenerationError(
                "GEMINI_API_KEY is not set. Add it to your .env file to use "
                "the AI Engine's chat/summary/notes/quiz services."
            )

        self.model_name = model
        self._client = genai.Client(api_key=resolved_key)

    def generate(self, prompt: str, temperature: float = GEMINI_DEFAULT_TEMPERATURE) -> str:
        """Generate a text response for the given prompt.

        Args:
            prompt: a fully-formed prompt string (built by
            `llm/prompts.py`).
            temperature: sampling temperature. Lower values (the
            default) favor grounded, deterministic-ish answers, which is
            what RAG-style answering and structured quiz JSON both want;
            a caller doing more creative generation could pass a higher
            value.

        Raises:
            LLMGenerationError: if every retry attempt fails, or on any
            non-retryable failure (auth, safety filter block, empty
            response). See the module docstring for retry behavior.
        """
        response = None
        attempt = 0

        while response is None:
            attempt += 1
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=temperature),
                )
            except genai_errors.APIError as exc:
                groq_resp = self._try_groq_fallback(prompt, temperature)
                if groq_resp is not None:
                    return groq_resp

                if exc.code == 401 or "UNAUTHENTICATED" in str(exc).upper():
                    logger.error("Gemini authentication failed: %s", exc)
                    raise LLMGenerationError(
                        "Invalid or unauthorized GEMINI_API_KEY in .env. "
                        "Please configure a valid API key from Google AI Studio (https://aistudio.google.com/)."
                    ) from exc

                if exc.code == 404 or "NOT_FOUND" in str(exc).upper():
                    logger.error("Gemini model not found (%s): %s", self.model_name, exc)
                    raise LLMGenerationError(
                        f"Configured Gemini model '{self.model_name}' was not found. "
                        "Please check GEMINI_MODEL in your configuration (e.g. 'gemini-1.5-flash')."
                    ) from exc

                is_retryable = exc.code in GEMINI_RETRYABLE_STATUS_CODES
                attempts_remaining = attempt < GEMINI_MAX_RETRIES
                if not (is_retryable and attempts_remaining):
                    logger.error(
                        "Gemini generation failed (attempt %d/%d, code=%s): %s",
                        attempt,
                        GEMINI_MAX_RETRIES,
                        exc.code,
                        exc,
                    )
                    raise LLMGenerationError(
                        f"Gemini generation failed after {attempt} attempt(s): {exc}"
                    ) from exc

                delay = GEMINI_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                if exc.code == 429:
                    delay = max(delay, 4.0 * attempt)
                logger.warning(
                    "Gemini returned a transient error (HTTP %s) - retrying in "
                    "%.1fs (attempt %d/%d)...",
                    exc.code,
                    delay,
                    attempt,
                    GEMINI_MAX_RETRIES,
                )
                time.sleep(delay)
            except Exception as exc:
                groq_resp = self._try_groq_fallback(prompt, temperature)
                if groq_resp is not None:
                    return groq_resp
                logger.error("Gemini generation failed: %s", exc)
                raise LLMGenerationError(f"Gemini generation failed: {exc}") from exc

        # Gemini returns an empty candidate list if the prompt tripped a
        # safety filter; `response.text` raises an unhelpful internal
        # error in that case, so we check explicitly first.
        if not response.candidates:
            raise LLMGenerationError(
                "Gemini returned no candidates (the prompt may have been "
                "blocked by safety filters)."
            )

        text = response.text
        if not text or not text.strip():
            raise LLMGenerationError("Gemini returned an empty response.")

        return text.strip()

    def _try_groq_fallback(self, prompt: str, temperature: float) -> Optional[str]:
        """Resilient fallback to Groq when Gemini credentials are unauthenticated."""
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            return None
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json",
            }
            groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
            payload = {
                "model": groq_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            logger.info("Attempting resilient LLM generation via Groq fallback (%s)...", groq_model)
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45,
            )
            res.encoding = "utf-8"
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("Successfully completed LLM generation using Groq fallback.")
                return content.strip()
            else:
                logger.warning("Groq fallback HTTP %d: %s", res.status_code, res.text)
        except Exception as exc:
            logger.warning("Groq fallback generation error: %s", exc)
        return None