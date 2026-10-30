from unittest.mock import MagicMock
import os
from router import (
    TIER_FAST,
    TIER_REASONING,
    get_client,
    diagnose_bug,
    generate_patch,
)


def test_model_tiers_and_client_defaults(monkeypatch):
    assert TIER_FAST == "nebius/nvidia/Nemotron-3_5-Lightning"
    assert TIER_REASONING == "nebius/nvidia/Nemotron-3-Ultra-550b-a55b"

    monkeypatch.setenv("NEBIUS_API_KEY", "test-token-123")
    monkeypatch.delenv("NEBIUS_BASE_URL", raising=False)

    client = get_client()
    assert client.api_key == "test-token-123"
    assert str(client.base_url).rstrip("/") == "https://api.tokenfactory.nebius.com/v1"


def test_diagnose_bug_calls_tier_fast():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="The function fails because of a division by zero when denominator is 0. "
                "Update the calculation to check for zero before dividing."
            )
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response

    code = "def divide(a, b):\n    return a / b\n"
    error_info = "ZeroDivisionError: division by zero"
    search_context = "Division by zero guard in Python"

    explanation = diagnose_bug(code, error_info, search_context, client=mock_client)

    assert "division by zero" in explanation
    mock_client.chat.completions.create.assert_called_once()
    kwargs = mock_client.chat.completions.create.call_args.kwargs

    assert kwargs["model"] == TIER_FAST
    assert kwargs["temperature"] == 0.2
    messages = kwargs["messages"]
    assert any("2-sentence explanation" in m["content"] for m in messages if m["role"] == "system")
    assert any("ZeroDivisionError" in m["content"] for m in messages if m["role"] == "user")
    assert any("Division by zero guard" in m["content"] for m in messages if m["role"] == "user")


def test_generate_patch_calls_tier_reasoning_and_cleans_diff():
    mock_client = MagicMock()
    mock_diff = """--- a/src/calc.py
+++ b/src/calc.py
@@ -1,2 +1,4 @@
 def divide(a, b):
+    if b == 0:
+        return 0
     return a / b
"""
    # Test wrapped in markdown diff fence
    wrapped_diff = f"```diff\n{mock_diff}\n```"

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=wrapped_diff))]
    mock_client.chat.completions.create.return_value = mock_response

    patch = generate_patch(
        isolated_code="def divide(a, b):\n    return a / b",
        file_path="src/calc.py",
        diagnosis="Zero division bug. Add zero check.",
        client=mock_client,
    )

    mock_client.chat.completions.create.assert_called_once()
    kwargs = mock_client.chat.completions.create.call_args.kwargs

    assert kwargs["model"] == TIER_REASONING
    assert kwargs["temperature"] == 0.0

    # Ensure clean patch starting with ---
    assert patch.startswith("--- a/src/calc.py")
    assert "+++ b/src/calc.py" in patch
    assert "```" not in patch
