from google.api_core.exceptions import ResourceExhausted
from huggingface_hub.errors import HfHubHTTPError
from tenacity import retry, retry_if_exception, retry_if_exception_type, stop_after_attempt, wait_exponential


def with_gemini_retry(func):
    """
    Retries a Gemini API call (used for embeddings) on rate-limit
    (429/ResourceExhausted) errors with exponential backoff: waits 5s, then
    15s, then 45s before giving up.

    Only helps with brief per-minute rate limiting. If your daily quota is
    fully exhausted, this won't help - wait for the reset or upgrade your
    plan.
    """
    return retry(
        retry=retry_if_exception_type(ResourceExhausted),
        wait=wait_exponential(multiplier=5, min=5, max=45),
        stop=stop_after_attempt(3),
        reraise=True,
    )(func)


def _is_hf_rate_limited(exc: BaseException) -> bool:
    if isinstance(exc, HfHubHTTPError):
        response = getattr(exc, "response", None)
        return response is not None and response.status_code == 429
    return False


def with_hf_retry(func):
    """
    Retries a Hugging Face Inference API call (used for chat/generation) on
    429 rate-limit errors with exponential backoff: waits 5s, then 15s, then
    45s before giving up.

    Only helps with brief per-minute rate limiting. If your account's
    monthly/daily quota is fully exhausted, this won't help - check
    https://huggingface.co/settings/billing for your usage.
    """
    return retry(
        retry=retry_if_exception(_is_hf_rate_limited),
        wait=wait_exponential(multiplier=5, min=5, max=45),
        stop=stop_after_attempt(3),
        reraise=True,
    )(func)
