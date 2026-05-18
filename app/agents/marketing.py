from __future__ import annotations

import re

from app.agents.base import BaseAgent, sanitize_social_draft
from app.models import AgentTask
from app.services.llm_service import LLMService


class MarketingAgent(BaseAgent):
    name = "marketing_agent"
    _cjk_pattern = re.compile(r"[\u4e00-\u9fff]")

    def __init__(self) -> None:
        self.llm = LLMService()

    def run(self, payload: dict) -> AgentTask:
        def executor(data: dict):
            goal = data.get("goal", "a product launch")
            channel = data.get("channel", "X (Twitter)")
            launch_long = data.get("launch_date_long") or data.get("launch_date", "soon")
            campaign = data.get("campaign_summary") or f"Product launch on {launch_long}"
            prompt = (
                f"Create exactly 3 short {channel} post drafts for: {campaign}. "
                f"Launch date: {launch_long}. "
                "English only, plain text only. "
                "Do not use emojis, icons, symbols, or hashtags (no # tags). "
                "Return plain sentences only, one draft per line."
            )
            text, model_used, estimated_cost = self.llm.generate_text(prompt, max_tokens=120)
            drafts = []
            for line in text.splitlines():
                cleaned = sanitize_social_draft(line.strip("- ").strip())
                cleaned = re.sub(r"^\d+\.\s*", "", cleaned).strip()
                if cleaned and not self._cjk_pattern.search(cleaned):
                    drafts.append(cleaned)
            if len(drafts) < 3:
                drafts = [
                    f"Excited for our product launch on {launch_long}. Stay tuned for more details.",
                    f"Our team is aligning on the launch plan for {campaign}.",
                    f"Countdown to launch day. We will share updates soon.",
                ]
            drafts = [sanitize_social_draft(d) for d in drafts[:3]]
            output = {
                "channel": channel,
                "tweet_drafts": drafts[:3],
                "campaign_theme": data.get("campaign_summary") or f"Product launch campaign",
                "llm_model_used": model_used,
                "llm_estimated_cost_usd": estimated_cost,
            }
            confidence = 0.82 if len(goal) > 20 and "?" not in goal else 0.58
            return output, confidence

        return self._wrap_run(payload, executor)

