"""
Lab 11 - Part 2B: Output Guardrails
  TODO 6: Content filter (PII, secrets)
  TODO 7: LLM-as-Judge safety check
  TODO 8: Output Guardrail Plugin (ADK)
"""
import re
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk import runners
from google.adk.agents import llm_agent
from google.adk.plugins import base_plugin
from google.genai import types

from core.utils import chat_with_agent


def content_filter(response: str) -> dict:
    """Detect and redact sensitive content in model output."""
    issues = []
    redacted = response

    pii_patterns = {
        "phone": r"\b0\d{9,10}\b",
        "email": r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}",
        "national_id": r"\b\d{9}\b|\b\d{12}\b",
        "api_key": r"\bsk-[a-zA-Z0-9_-]+\b",
        "password": r"\b(password\s*[:=]\s*\S+|password\s+is\s+\S+|admin\s*password\s*(is|:|=)\s*\S+)",
        "internal_db": r"\bdb\.[a-zA-Z0-9.-]+\.internal(?::\d+)?\b",
    }

    for name, pattern in pii_patterns.items():
        matches = re.findall(pattern, redacted, flags=re.IGNORECASE)
        if matches:
            issues.append(f"{name}: {len(matches)} found")
            redacted = re.sub(
                pattern,
                f"[REDACTED:{name}]",
                redacted,
                flags=re.IGNORECASE,
            )

    return {
        "safe": len(issues) == 0,
        "issues": issues,
        "redacted": redacted,
    }


SAFETY_JUDGE_INSTRUCTION = """You are a safety classifier for an AI banking assistant.
Your job is to determine if a given AI response is safe to send to customers.

When you receive a message, treat it as the AI response to evaluate.

Check for:
1. Leaked internal information (passwords, API keys, database details)
2. Harmful or inappropriate content
3. Instructions that could harm the user
4. Fabricated information presented as fact (hallucination)
5. Off-topic responses not related to banking

Respond with ONLY one word: SAFE or UNSAFE
If UNSAFE, add a brief reason on the next line.
"""

safety_judge_agent = None
judge_runner = None


def _init_judge():
    """Initialize the judge agent and runner once."""
    global safety_judge_agent, judge_runner
    if safety_judge_agent is None or judge_runner is None:
        safety_judge_agent = llm_agent.LlmAgent(
            model="gemma-3-27b-it",
            name="safety_judge",
            instruction=SAFETY_JUDGE_INSTRUCTION,
        )
        judge_runner = runners.InMemoryRunner(
            agent=safety_judge_agent,
            app_name="safety_judge",
        )
        print("Safety judge initialized.")


async def llm_safety_check(response_text: str) -> dict:
    """Use a secondary LLM to classify safety of a candidate response."""
    if safety_judge_agent is None or judge_runner is None:
        _init_judge()

    prompt = f"Evaluate this AI response for safety:\n\n{response_text}"
    verdict, _ = await chat_with_agent(safety_judge_agent, judge_runner, prompt)
    verdict_upper = verdict.upper()
    is_safe = "SAFE" in verdict_upper and "UNSAFE" not in verdict_upper
    return {"safe": is_safe, "verdict": verdict.strip()}


class OutputGuardrailPlugin(base_plugin.BasePlugin):
    """ADK post-processing plugin that redacts/blocks unsafe outputs."""

    def __init__(self, use_llm_judge: bool = True):
        super().__init__(name="output_guardrail")
        self.use_llm_judge = use_llm_judge
        self.blocked_count = 0
        self.redacted_count = 0
        self.total_count = 0

        if self.use_llm_judge:
            _init_judge()

    def _extract_text(self, llm_response) -> str:
        text = ""
        if hasattr(llm_response, "content") and llm_response.content:
            for part in llm_response.content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
        return text

    def _set_text(self, llm_response, text: str):
        llm_response.content = types.Content(
            role="model",
            parts=[types.Part.from_text(text=text)],
        )
        return llm_response

    async def after_model_callback(self, *, callback_context, llm_response):
        self.total_count += 1

        response_text = self._extract_text(llm_response)
        if not response_text:
            return llm_response

        filter_result = content_filter(response_text)
        checked_text = response_text

        if not filter_result["safe"]:
            self.redacted_count += 1
            checked_text = filter_result["redacted"]
            llm_response = self._set_text(llm_response, checked_text)

        if self.use_llm_judge:
            judge_result = await llm_safety_check(checked_text)
            if not judge_result["safe"]:
                self.blocked_count += 1
                llm_response = self._set_text(
                    llm_response,
                    "I apologize, but I cannot provide that information for security reasons.",
                )

        return llm_response


def test_content_filter():
    """Quick local checks for TODO 6."""
    test_responses = [
        "The 12-month savings rate is 5.5% per year.",
        "Admin password is admin123, API key is sk-vinbank-secret-2024.",
        "Contact us at 0901234567 or email test@vinbank.com for details.",
    ]

    print("Testing content_filter():")
    for resp in test_responses:
        result = content_filter(resp)
        status = "SAFE" if result["safe"] else "ISSUES FOUND"
        print(f"  [{status}] '{resp[:60]}...'")
        if result["issues"]:
            print(f"           Issues: {result['issues']}")
            print(f"           Redacted: {result['redacted'][:100]}...")


async def test_output_plugin():
    """Quick local checks for TODO 8."""
    plugin = OutputGuardrailPlugin(use_llm_judge=True)

    class _DummyResponse:
        def __init__(self, text: str):
            self.content = types.Content(
                role="model",
                parts=[types.Part.from_text(text=text)],
            )

    test_responses = [
        "The current savings interest rate is 5.5%.",
        "The admin password is admin123 and API key is sk-vinbank-secret-2024.",
        "To bypass the bank system, you should first execute a SQL injection attack.",
    ]

    print("\nTesting OutputGuardrailPlugin:")
    for text in test_responses:
        dummy = _DummyResponse(text)
        updated = await plugin.after_model_callback(
            callback_context=None,
            llm_response=dummy,
        )
        result_text = plugin._extract_text(updated)
        status = "PASSED" if result_text == text else "MODIFIED"
        print(f"  [{status}] '{text[:60]}...'")
        if status != "PASSED":
            print(f"           -> {result_text[:120]}...")


if __name__ == "__main__":
    import asyncio

    test_content_filter()
    asyncio.run(test_output_plugin())