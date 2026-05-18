from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from uuid import uuid4

from app.agents.document import DocumentAgent
from app.agents.marketing import MarketingAgent
from app.agents.schedule import ScheduleAgent
from app.models import TaskStatus, WorkflowResponse
from app.services.llm_service import LLMService
from app.services.schedule_tool import format_date_long, resolve_next_weekday_date


class OrchestratorService:
    SCHEDULE_KEYWORDS = [
        "schedule",
        "meeting",
        "calendar",
        "reschedule",
        "arrange",
        "sync",
        "book",
        "booking",
        "appointment",
        "timeslot",
        "time slot",
        "availability",
        "available",
        "invite",
        "set up",
        "set-up",
        "standup",
        "stand-up",
        "call",
        "zoom",
        "teams meeting",
        "session",
        "agenda meeting",
        "appointment request",
        "book a meeting",
        "book meeting",
        "set meeting",
        "set a meeting",
        "planning meeting",
        "kickoff meeting",
        "review meeting",
        "follow-up meeting",
        "daily sync",
        "weekly sync",
        "check-in",
        "touch base",
        "coordinate schedule",
        "coordinate calendar",
        "find a time",
        "pick a time",
        "meeting slot",
        "time window",
        "calendar invite",
        "meeting invite",
        "meeting request",
        "confirm availability",
        "meeting coordination",
    ]

    MARKETING_KEYWORDS = [
        "tweet",
        "twitter",
        "linkedin",
        "social media",
        "post",
        "campaign",
        "promo",
        "promotion",
        "promotional",
        "marketing copy",
        "caption",
        "hashtag",
        "x post",
        "instagram",
        "facebook",
        "thread",
        "ads",
        "ad copy",
        "slogan",
        "tagline",
        "launch post",
        "announcement post",
        "marketing",
        "social copy",
        "social caption",
        "content calendar",
        "content plan",
        "content strategy",
        "campaign copy",
        "brand post",
        "launch campaign",
        "go-to-market",
        "gtm",
        "community post",
        "promote",
        "publicize",
        "awareness",
        "engagement",
        "marketing message",
        "cta",
        "call to action",
        "newsletter blurb",
        "ad text",
        "product announcement",
    ]

    DOCUMENT_KEYWORDS = [
        "email",
        "proposal",
        "report",
        "slides",
        "document",
        "outline",
        "internal",
        "announcement email",
        "announcement",
        "memo",
        "brief",
        "summary",
        "minutes",
        "meeting minutes",
        "draft letter",
        "letter",
        "press release",
        "one-pager",
        "spec",
        "documentation",
        "write-up",
        "plan document",
        "business case",
        "note",
        "policy",
        "guideline",
        "doc",
        "doc draft",
        "specification",
        "requirements",
        "project brief",
        "executive summary",
        "status update",
        "update email",
        "announcement memo",
        "internal memo",
        "meeting notes",
        "recap",
        "report draft",
        "slide deck",
        "presentation deck",
        "proposal draft",
    ]

    ACTION_KEYWORDS = [
        "schedule",
        "meeting",
        "draft",
        "create",
        "generate",
        "plan",
        "prepare",
        "post",
        "email",
        "proposal",
        "campaign",
        "launch",
        "tweet",
        "document",
        "write",
        "compose",
        "organize",
        "arrange",
        "summarize",
        "produce",
        "make",
        "build",
        "draft up",
        "send",
        "prepare draft",
        "put together",
        "come up with",
        "design",
        "craft",
        "finalize",
        "deliver",
        "develop",
        "assemble",
        "outline",
        "document",
        "organise",
        "prioritize",
    ]

    def __init__(self) -> None:
        self.marketing_agent = MarketingAgent()
        self.schedule_agent = ScheduleAgent()
        self.document_agent = DocumentAgent()
        self.llm = LLMService()

    def _parse_meeting_time(self, lowered: str) -> tuple[str | None, str | None]:
        """Parse 'at 2pm' / 'at 14:30' into display and ISO-ish range strings."""
        match = re.search(
            r"\b(?:at|@)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",
            lowered,
        )
        if not match:
            return None, None
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        meridiem = (match.group(3) or "").lower()
        if meridiem == "pm" and hour < 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        elif not meridiem and hour <= 7:
            hour += 12
        start = datetime(2000, 1, 1, hour, minute)
        end = start + timedelta(hours=1)
        display = (
            f"{start.strftime('%I').lstrip('0') or '12'}:{start.strftime('%M')} "
            f"{start.strftime('%p')} - "
            f"{end.strftime('%I').lstrip('0') or '12'}:{end.strftime('%M')} "
            f"{end.strftime('%p')}"
        )
        iso_range = f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"
        return display, iso_range

    def _extract_launch_weekday(self, lowered: str) -> str:
        if re.search(r"\bnext\s+friday\b", lowered):
            return "Friday"
        launch_day_match = re.search(
            r"(?:launch|product launch)[^.]*?\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            lowered,
        )
        if launch_day_match:
            return launch_day_match.group(1).capitalize()
        return "Friday"

    def _extract_meeting_weekday(self, lowered: str) -> str:
        meeting_day_match = re.search(
            r"(?:meeting|schedule)[^.]*?\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            lowered,
        )
        if meeting_day_match:
            return meeting_day_match.group(1).capitalize()
        generic = re.search(
            r"\bfor\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            lowered,
        )
        if generic:
            return generic.group(1).capitalize()
        return "Tuesday"

    def _extract_participants_hint(self, lowered: str) -> list[str]:
        hints: list[str] = []
        if "marketing lead" in lowered:
            hints.append("Marketing Lead")
        if "product manager" in lowered:
            hints.append("Product Manager")
        if "operations coordinator" in lowered or "operations" in lowered:
            hints.append("Operations Coordinator")
        return hints

    def _extract_context(self, user_input: str) -> dict:
        text = user_input.strip()
        lowered = text.lower()
        today = date.today()

        meeting_day = self._extract_meeting_weekday(lowered)
        launch_day = self._extract_launch_weekday(lowered)
        meeting_date = resolve_next_weekday_date(meeting_day, from_date=today)
        launch_date = resolve_next_weekday_date(launch_day, from_date=today)

        meeting_time_display, meeting_time_iso_range = self._parse_meeting_time(lowered)
        participants_hint = self._extract_participants_hint(lowered)

        goal = text if len(text) <= 240 else f"{text[:237]}..."
        launch_date_long = format_date_long(launch_date)
        campaign_summary = f"Product launch on {launch_date_long}"

        return {
            "user_input": text,
            "goal": goal,
            "meeting_day": meeting_day,
            "launch_date": launch_date_long,
            "launch_date_iso": launch_date.isoformat(),
            "launch_date_long": launch_date_long,
            "meeting_date_iso": meeting_date.isoformat(),
            "meeting_date_long": format_date_long(meeting_date),
            "meeting_time_display": meeting_time_display,
            "meeting_time_iso_range": meeting_time_iso_range,
            "participants_hint": participants_hint,
            "campaign_summary": campaign_summary,
            "server_date_iso": today.isoformat(),
            "server_date_long": format_date_long(today),
        }

    def _is_chitchat(self, lowered_input: str) -> bool:
        chitchat_patterns = [
            r"^who are you\??$",
            r"^hello$",
            r"^hi$",
            r"^what can you do\??$",
            r"^are you (an )?ai\??$",
        ]
        return any(re.search(pattern, lowered_input) for pattern in chitchat_patterns)

    def _is_business_automation_request(self, lowered_input: str) -> bool:
        all_keywords = set(self.ACTION_KEYWORDS) | set(self.SCHEDULE_KEYWORDS) | set(
            self.MARKETING_KEYWORDS
        ) | set(self.DOCUMENT_KEYWORDS)
        return any(keyword in lowered_input for keyword in all_keywords)

    def _decide_requested_agents(self, lowered_input: str) -> dict[str, bool]:
        want_schedule = any(k in lowered_input for k in self.SCHEDULE_KEYWORDS)
        want_marketing = any(k in lowered_input for k in self.MARKETING_KEYWORDS)
        want_document = any(k in lowered_input for k in self.DOCUMENT_KEYWORDS)
        return {
            "schedule": want_schedule,
            "marketing": want_marketing,
            "document": want_document,
        }

    # Debug/testing helper for keyword routing visualization.
    def debug_keyword_match(self, user_input: str) -> dict:
        lowered_input = user_input.strip().lower()
        matched_schedule = [k for k in self.SCHEDULE_KEYWORDS if k in lowered_input]
        matched_marketing = [k for k in self.MARKETING_KEYWORDS if k in lowered_input]
        matched_document = [k for k in self.DOCUMENT_KEYWORDS if k in lowered_input]
        matched_action = [k for k in self.ACTION_KEYWORDS if k in lowered_input]

        is_chitchat = self._is_chitchat(lowered_input)
        is_business = self._is_business_automation_request(lowered_input)
        requested = self._decide_requested_agents(lowered_input)

        return {
            "input": user_input,
            "is_chitchat": is_chitchat,
            "is_business_automation_request": is_business,
            "matched_keywords": {
                "action": matched_action,
                "schedule": matched_schedule,
                "marketing": matched_marketing,
                "document": matched_document,
            },
            "requested_agents": requested,
        }

    def execute_workflow(self, user_input: str) -> WorkflowResponse:
        lowered_input = user_input.strip().lower()
        provider = self.llm.provider()
        router_model, generation_model = self.llm.route_models(user_input)

        if self._is_chitchat(lowered_input):
            return WorkflowResponse(
                request_id=str(uuid4()),
                created_at=datetime.utcnow(),
                summary=(
                    "This system is a multi-agent business automation prototype. "
                    "Try a task request like: 'Schedule a meeting for Tuesday and create 3 tweet drafts.'"
                ),
                success_rate=0.0,
                total_latency_ms=0,
                fallback_triggered=False,
                llm_provider=provider,
                router_model=router_model,
                generation_model=generation_model,
                estimated_cost_usd=0.0,
                tasks=[],
            )

        if not self._is_business_automation_request(lowered_input):
            return WorkflowResponse(
                request_id=str(uuid4()),
                created_at=datetime.utcnow(),
                summary=(
                    "Input recognized, but it is not a business workflow request. "
                    "Please include at least one actionable business task (schedule/draft/create/generate)."
                ),
                success_rate=0.0,
                total_latency_ms=0,
                fallback_triggered=False,
                llm_provider=provider,
                router_model=router_model,
                generation_model=generation_model,
                estimated_cost_usd=0.0,
                tasks=[],
            )

        context = self._extract_context(user_input)
        requested = self._decide_requested_agents(lowered_input)
        context["want_proposal_outline"] = any(
            k in lowered_input for k in ["proposal", "report", "slides", "outline", "thesis"]
        )

        tasks: list = []
        if requested["schedule"]:
            tasks.append(self.schedule_agent.run(context))
        if requested["marketing"]:
            tasks.append(self.marketing_agent.run(context))
        if requested["document"]:
            tasks.append(self.document_agent.run(context))

        # Safety fallback: if the input is business-related but keywords didn't map cleanly,
        # run all three agents so the prototype still produces a full workflow.
        if not tasks:
            tasks = [
                self.schedule_agent.run(context),
                self.marketing_agent.run(context),
                self.document_agent.run(context),
            ]

        total_latency = sum(task.latency_ms for task in tasks)
        success_count = sum(1 for task in tasks if task.status == TaskStatus.SUCCESS)
        fallback_triggered = any(task.status == TaskStatus.HUMAN_REVIEW for task in tasks)
        success_rate = round(success_count / len(tasks), 2)
        estimated_cost = round(
            sum(float(task.output_payload.get("llm_estimated_cost_usd", 0.0)) for task in tasks),
            6,
        )

        summary = (
            f"Processed {len(tasks)} agent(s) with success rate {int(success_rate * 100)}%. "
            f"{'Human review required for at least one task.' if fallback_triggered else 'No fallback required.'}"
        )

        return WorkflowResponse(
            request_id=str(uuid4()),
            created_at=datetime.utcnow(),
            summary=summary,
            success_rate=success_rate,
            total_latency_ms=total_latency,
            fallback_triggered=fallback_triggered,
            llm_provider=provider,
            router_model=router_model,
            generation_model=generation_model,
            estimated_cost_usd=estimated_cost,
            tasks=tasks,
        )

