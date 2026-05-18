from __future__ import annotations

import re

from app.agents.base import BaseAgent, sanitize_document_text
from app.models import AgentTask
from app.services.llm_service import LLMService


class DocumentAgent(BaseAgent):
    name = "document_agent"
    _cjk_pattern = re.compile(r"[\u4e00-\u9fff]")

    def __init__(self) -> None:
        self.llm = LLMService()

    def run(self, payload: dict) -> AgentTask:
        def executor(data: dict):
            goal = data.get("goal", "our upcoming launch")
            launch_date_long = data.get("launch_date_long") or data.get("launch_date", "next Friday")
            meeting_date_long = data.get("meeting_date_long", "")
            meeting_time_display = data.get("meeting_time_display")
            want_outline = bool(data.get("want_proposal_outline", False))
            meeting_line = ""
            if meeting_date_long:
                meeting_line = f"Team meeting: {meeting_date_long}"
                if meeting_time_display:
                    meeting_line += f" at {meeting_time_display}"
                meeting_line += ". Use these exact times in the email.\n"
            email_prompt = (
                f"Write one concise internal announcement email for: {goal}\n"
                f"Product launch: {launch_date_long}.\n"
                f"{meeting_line}"
                "Output must be English only, plain text. "
                "Do not use emojis, icons, symbols, or hashtags (no # tags). "
                "Do not use placeholders like [Date]."
            )
            email, model_used_email, cost_email = self.llm.generate_text(email_prompt, max_tokens=220)
            if not email or email.startswith("[Local LLM") or email.startswith("[Mock LLM"):
                email = ""
            if self._cjk_pattern.search(email):
                email = ""
            if not email.strip():
                email = (
                    "Subject: Internal Announcement\n\n"
                    f"Team,\n\nWe are preparing for our launch on {launch_date_long}. "
                    f"{meeting_line}"
                    "Please review the current tasks and align on next actions.\n\n"
                    "Regards,\nProject Coordinator"
                )
            email = sanitize_document_text(email)

            proposal_outline: list[str] = []
            llm_model_used = model_used_email
            llm_estimated_total_cost = cost_email

            if want_outline:
                outline_prompt = (
                    f"Provide 5 bullet points for a proposal outline about this goal: {goal}. "
                    "English only, plain text, no emojis or hashtags."
                )
                outline_text, model_used_outline, cost_outline = self.llm.generate_text(
                    outline_prompt, max_tokens=120
                )
                proposal_outline = [
                    sanitize_document_text(line.strip("- ").strip())
                    for line in outline_text.splitlines()
                    if line.strip()
                ]
                proposal_outline = [line for line in proposal_outline if line]
                if len(proposal_outline) < 5:
                    proposal_outline = [
                        "Launch Overview",
                        "Target Audience and Positioning",
                        "Marketing Timeline",
                        "Resource Allocation",
                        "Success Metrics",
                    ]

                llm_estimated_total_cost = round(cost_email + cost_outline, 6)
                llm_model_used = model_used_outline or model_used_email

            output = {
                "announcement_email": email,
                "proposal_outline": proposal_outline[:5],
                "llm_model_used": llm_model_used,
                "llm_estimated_cost_usd": llm_estimated_total_cost,
            }
            confidence = 0.84 if len(goal) > 20 and "?" not in goal else 0.57
            return output, confidence

        return self._wrap_run(payload, executor)

