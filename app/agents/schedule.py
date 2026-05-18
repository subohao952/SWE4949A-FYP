from __future__ import annotations

import json
import re

from datetime import date

from app.agents.base import BaseAgent
from app.models import AgentTask
from app.services.llm_service import LLMService
from app.services.schedule_tool import ScheduleTool, format_date_long, resolve_next_weekday_date


class ScheduleAgent(BaseAgent):
    name = "schedule_agent"
    _json_block_re = re.compile(r"\{[\s\S]*\}")

    def __init__(self) -> None:
        self.schedule_tool = ScheduleTool()
        self.llm = LLMService()

    def _parse_schedule_llm_json(self, text: str) -> dict:
        if not text or text.startswith("[Local LLM") or text.startswith("[Mock LLM"):
            return {}
        match = self._json_block_re.search(text)
        if not match:
            return {}
        try:
            payload = json.loads(match.group(0))
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _fallback_title(self, data: dict) -> str:
        raw = str(data.get("user_input") or data.get("goal") or "").lower()
        if "kickoff" in raw:
            return "Product Launch Kickoff Planning Meeting"
        if "launch" in raw:
            return "Product Launch Preparation Meeting"
        return "Team Planning Meeting"

    def _fallback_participants(self, data: dict) -> list[str]:
        hinted = data.get("participants_hint")
        if isinstance(hinted, list) and hinted:
            return [str(p).strip() for p in hinted if str(p).strip()][:6]
        raw = str(data.get("user_input") or "").lower()
        found: list[str] = []
        if "marketing lead" in raw:
            found.append("Marketing Lead")
        if "product manager" in raw:
            found.append("Product Manager")
        if "operations" in raw:
            found.append("Operations Coordinator")
        return found or ["Marketing Lead", "Team Leads"]

    def run(self, payload: dict) -> AgentTask:
        def executor(data: dict):
            meeting_day = data.get("meeting_day", "Tuesday")
            meeting_date_iso = data.get("meeting_date_iso")
            meeting_date_long = data.get("meeting_date_long", "")
            meeting_time_display = data.get("meeting_time_display")
            user_input = data.get("user_input") or data.get("goal", "")

            meeting_date = (
                date.fromisoformat(meeting_date_iso)
                if meeting_date_iso
                else resolve_next_weekday_date(meeting_day)
            )
            if not meeting_date_long:
                meeting_date_long = format_date_long(meeting_date)

            prompt = (
                "You are a scheduling assistant. Read the business request and propose meeting metadata.\n"
                f"Business request:\n{user_input}\n\n"
                "Use these exact calendar facts from the server clock. Do NOT change the meeting date.\n"
                f"- Meeting day: {meeting_day}\n"
                f"- Meeting date: {meeting_date_long} (ISO {meeting_date.isoformat()})\n"
            )
            if meeting_time_display:
                prompt += (
                    f"- The user requested this time: {meeting_time_display}. "
                    "Use this exact time range in meeting_time.\n"
                )
            else:
                prompt += "- No specific time was parsed; suggest a reasonable 1-hour slot.\n"

            prompt += (
                "\nReturn ONLY valid JSON with exactly these keys:\n"
                '{"meeting_title": "...", "participants": ["Role A", "Role B"], '
                '"meeting_time": "HH:MM AM/PM - HH:MM AM/PM"}\n'
                "Rules: English only; 2-5 participants as role titles; "
                "title should reflect the request (e.g. kickoff, launch prep); "
                "no emojis or hashtags."
            )

            text, model_used, estimated_cost = self.llm.generate_text(prompt, max_tokens=160)
            parsed = self._parse_schedule_llm_json(text)

            meeting_title = str(parsed.get("meeting_title") or "").strip() or self._fallback_title(data)
            participants_raw = parsed.get("participants")
            if isinstance(participants_raw, list):
                participants = [str(p).strip() for p in participants_raw if str(p).strip()][:6]
            elif isinstance(participants_raw, str) and participants_raw.strip():
                participants = [p.strip() for p in re.split(r",|;", participants_raw) if p.strip()]
            else:
                participants = self._fallback_participants(data)

            llm_time = str(parsed.get("meeting_time") or "").strip()
            recommended_time = meeting_time_display or llm_time or "10:00 - 11:00"

            output = self.schedule_tool.plan_meeting(
                meeting_day,
                meeting_date=meeting_date,
                meeting_title=meeting_title,
                recommended_time=recommended_time,
                participants=participants,
            )
            output["llm_model_used"] = model_used
            output["llm_estimated_cost_usd"] = estimated_cost
            confidence = 0.87 if meeting_time_display else 0.78
            return output, confidence

        return self._wrap_run(payload, executor)
