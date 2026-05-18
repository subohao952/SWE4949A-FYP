from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class LLMService:
    def __init__(self) -> None:
        self.provider_mode = os.getenv("LLM_PROVIDER", "auto").strip().lower()
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.router_model = os.getenv("ROUTER_MODEL", "gpt-4.1-nano")
        self.generator_model = os.getenv("GENERATOR_MODEL", "gpt-4.1-mini")
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    def provider(self) -> str:
        if self.provider_mode == "local":
            return "local"
        if self.provider_mode == "openai":
            return "openai" if self.api_key else "mock"
        if self.api_key:
            return "openai"
        return "mock"

    def route_models(self, user_input: str) -> tuple[str, str]:
        provider = self.provider()
        if len(user_input) > 120 or " and " in user_input.lower():
            if provider == "local":
                return ("local-router", self.ollama_model)
            return (self.router_model, self.generator_model)
        if provider == "local":
            return ("rule-based", self.ollama_model)
        return ("rule-based", self.generator_model if provider == "openai" else "template-engine")

    def generate_text(self, prompt: str, max_tokens: int = 240) -> tuple[str, str, float]:
        provider = self.provider()
        if provider == "local":
            return self._generate_local(prompt, max_tokens)
        if provider == "openai":
            return self._generate_openai(prompt, max_tokens)
        return (f"[Mock LLM Output] {prompt[:180]}", "template-engine", 0.0)

    def _generate_local(self, prompt: str, max_tokens: int) -> tuple[str, str, float]:
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": max_tokens},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
            text = body.get("response", "").strip()
            if not text:
                text = f"[Local LLM Empty Response Fallback] {prompt[:180]}"
            return (text, self.ollama_model, 0.0)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return (f"[Local LLM Unavailable Fallback] {prompt[:180]}", "local-fallback", 0.0)

    def _generate_openai(self, prompt: str, max_tokens: int) -> tuple[str, str, float]:
        payload = {
            "model": self.generator_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.openai_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"].strip()
            usage = body.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            # Approx estimate for mini-tier pricing (can be adjusted in thesis).
            estimated_cost = round((input_tokens * 0.00000015) + (output_tokens * 0.0000006), 6)
            return (text, self.generator_model, estimated_cost)
        except (urllib.error.URLError, KeyError, IndexError, TimeoutError):
            return (f"[LLM Fallback Output] {prompt[:180]}", "openai-fallback", 0.0)

