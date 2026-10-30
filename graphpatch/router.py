"""Two-tier LLM routing module powered by NVIDIA Nemotron on Nebius Token Factory."""

import os
import re
from openai import OpenAI

try:
    from .config import (
        NEBIUS_API_KEY,
        NEBIUS_BASE_URL,
        TIER_FAST_ID as TIER_FAST,
        TIER_REASONING_ID as TIER_REASONING,
        TIMEOUT_SECONDS,
    )
except (ImportError, ValueError):
    NEBIUS_API_KEY = os.environ.get("NEBIUS_API_KEY", "")
    NEBIUS_BASE_URL = os.environ.get(
        "NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1"
    )
    TIER_FAST = "nebius/nvidia/Nemotron-3_5-Lightning"
    TIER_REASONING = "nebius/nvidia/Nemotron-3-Ultra-550b-a55b"
    TIMEOUT_SECONDS = 30


USAGE = {"prompt_tokens": 0, "completion_tokens": 0}


def reset_usage() -> None:
    """Reset accumulated token usage metrics."""
    USAGE["prompt_tokens"] = 0
    USAGE["completion_tokens"] = 0


def get_usage() -> dict[str, int]:
    """Retrieve accumulated token usage metrics."""
    return dict(USAGE)


def get_client(api_key: str | None = None, base_url: str | None = None) -> OpenAI:
    """Instantiate an OpenAI-compatible client for Nebius Token Factory."""
    key = api_key or os.environ.get("NEBIUS_API_KEY", "") or "dummy_key"
    url = (
        base_url
        or os.environ.get("NEBIUS_BASE_URL")
        or "https://api.tokenfactory.nebius.com/v1"
    )
    return OpenAI(api_key=key, base_url=url)


def diagnose_bug(
    isolated_code: str,
    error_info: str,
    search_context: str | None = None,
    client: OpenAI | None = None,
) -> str:
    """Call TIER_FAST to produce a 2-sentence explanation of what broke and the exact intended fix."""
    if client is None:
        client = get_client()

    system_prompt = (
        "You are an expert systems debugging assistant. Analyze the failing code, "
        "error information, and any provided search context. Produce exactly a 2-sentence "
        "explanation: the first sentence explaining what broke and why, and the second "
        "sentence stating the exact intended fix."
    )

    user_content = (
        f"### Code Context:\n{isolated_code}\n\n"
        f"### Error Information:\n{error_info}\n"
    )
    if search_context:
        user_content += f"\n### External Documentation / Search Context:\n{search_context}\n"

    response = client.chat.completions.create(
        model=TIER_FAST,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    if hasattr(response, "usage") and response.usage:
        USAGE["prompt_tokens"] += getattr(response.usage, "prompt_tokens", 0) or 0
        USAGE["completion_tokens"] += (
            getattr(response.usage, "completion_tokens", 0) or 0
        )
    return response.choices[0].message.content.strip()


def generate_patch(
    isolated_code: str,
    file_path: str,
    diagnosis: str,
    client: OpenAI | None = None,
) -> str:
    """Call TIER_REASONING to generate a valid, git-compatible unified diff."""
    if client is None:
        client = get_client()

    # Normalize relative path for unified diff header
    norm_path = file_path.replace("\\", "/").lstrip("./")

    system_prompt = (
        "You are an automated software repair engine. You must output ONLY a valid, "
        "git-compatible unified diff (.patch format) that fixes the bug described in the diagnosis.\n"
        "Strict rules:\n"
        "- Do NOT output any markdown formatting, conversational text, explanations, or code fences.\n"
        f"- The patch MUST start directly with '--- a/{norm_path}' and '+++ b/{norm_path}'.\n"
        "- Include standard unified diff hunk headers (e.g. @@ -start,len +start,len @@) and context lines.\n"
        "- Ensure the patch applies cleanly to the target file."
    )

    user_content = (
        f"### Target File:\n{norm_path}\n\n"
        f"### Diagnosis:\n{diagnosis}\n\n"
        f"### Target Code Context:\n{isolated_code}\n\n"
        "Generate the unified diff patch now:"
    )

    response = client.chat.completions.create(
        model=TIER_REASONING,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.0,
    )
    if hasattr(response, "usage") and response.usage:
        USAGE["prompt_tokens"] += getattr(response.usage, "prompt_tokens", 0) or 0
        USAGE["completion_tokens"] += (
            getattr(response.usage, "completion_tokens", 0) or 0
        )

    raw_patch = response.choices[0].message.content.strip()

    # Strip any accidental markdown fences
    if raw_patch.startswith("```"):
        raw_patch = re.sub(r"^```[a-zA-Z]*\n?", "", raw_patch)
        raw_patch = re.sub(r"\n?```$", "", raw_patch).strip()

    return raw_patch
