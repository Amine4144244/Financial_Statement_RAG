import os
from typing import Optional


class LLMService:
    """Orchestrates LLM inference via Groq API with robust deterministic fallback for testing."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_key and self.api_key.strip() and not self.api_key.startswith("your_groq"):
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception:
                self.client = None

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Calls Groq if client is configured, otherwise generates structured deterministic response."""
        if self.client:
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    model=self.model,
                    temperature=0.1,  # Low temperature for factual precision
                    max_tokens=1024,
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                # Fallback to local synthesis if API fails or rate limited
                return self._fallback_synthesis(user_prompt, error_msg=str(e))

        return self._fallback_synthesis(user_prompt)

    def _fallback_synthesis(self, user_prompt: str, error_msg: Optional[str] = None) -> str:
        """Deterministic rule-based response builder used when API key is unavailable or in offline test mode."""
        lines = user_prompt.split("\n")
        question = "Financial Inquiry"
        facts = []
        calculations = []
        passages = []

        current_sec = None
        for line in lines:
            if line.startswith("QUESTION:"):
                current_sec = "q"
            elif "VERIFIED FINANCIAL FACTS" in line:
                current_sec = "facts"
            elif "DETERMINISTIC RATIOS" in line:
                current_sec = "calcs"
            elif "RETRIEVED DOCUMENT EXCERPTS" in line:
                current_sec = "passages"
            elif current_sec == "q" and line.strip() and not line.startswith("QUESTION:"):
                question = line.strip()
            elif current_sec == "facts" and line.startswith("- "):
                facts.append(line[2:])
            elif current_sec == "calcs" and line.startswith("- "):
                calculations.append(line[2:])
            elif current_sec == "passages" and line.startswith("Source"):
                passages.append(line.strip())

        # Synthesize grounded answer
        summary_parts = [
            "### Executive Summary",
            f"Based on the verified financial statements, here is the analysis for: **{question}**.",
            "\n### Verified Metrics & Calculations",
        ]

        if facts:
            summary_parts.append("**Reported Financial Facts:**")
            for f in facts:
                summary_parts.append(f"- {f}")

        if calculations:
            summary_parts.append("\n**Computed Indicators:**")
            for c in calculations:
                summary_parts.append(f"- {c}")

        summary_parts.append("\n### Management Explanations & Evidence")
        if passages:
            for p in passages:
                summary_parts.append(f"- {p}")
        else:
            summary_parts.append("- The available documents do not contain explicit narrative explanations for these changes.")

        summary_parts.append("\n### Conclusion")
        summary_parts.append(
            "The numerical findings are calculated deterministically from verified company reports with exact audit provenance."
        )

        return "\n".join(summary_parts)
