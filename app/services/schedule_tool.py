from __future__ import annotations

import os
from datetime import date, timedelta


WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def resolve_next_weekday_date(weekday_name: str, *, from_date: date | None = None) -> date:
    """Return the next occurrence of weekday_name strictly after from_date (default today)."""
    today = from_date or date.today()
    desired = WEEKDAY_MAP.get(weekday_name.lower(), 1)
    delta = (desired - today.weekday()) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


def format_date_long(d: date) -> str:
    return d.strftime("%A, %B %d, %Y")


class ScheduleTool:
    def plan_meeting(
        self,
        meeting_day: str,
        *,
        meeting_date: date | None = None,
        meeting_title: str | None = None,
        recommended_time: str | None = None,
        participants: list[str] | None = None,
    ) -> dict:
        provider = os.getenv("SCHEDULE_PROVIDER", "mock").lower()
        if provider == "google":
            return self._plan_with_google_placeholder(
                meeting_day,
                meeting_date=meeting_date,
                meeting_title=meeting_title,
                recommended_time=recommended_time,
                participants=participants,
            )
        return self._plan_with_mock(
            meeting_day,
            meeting_date=meeting_date,
            meeting_title=meeting_title,
            recommended_time=recommended_time,
            participants=participants,
        )

    def _plan_with_mock(
        self,
        meeting_day: str,
        *,
        meeting_date: date | None = None,
        meeting_title: str | None = None,
        recommended_time: str | None = None,
        participants: list[str] | None = None,
    ) -> dict:
        resolved = meeting_date or resolve_next_weekday_date(meeting_day)
        return {
            "provider": "mock",
            "meeting_title": meeting_title or "Team Planning Meeting",
            "recommended_date": resolved.isoformat(),
            "recommended_date_long": format_date_long(resolved),
            "recommended_time": recommended_time or "10:00 - 11:00",
            "participants": participants
            or ["Marketing Lead", "Product Manager", "Operations Coordinator"],
        }

    def _plan_with_google_placeholder(
        self,
        meeting_day: str,
        *,
        meeting_date: date | None = None,
        meeting_title: str | None = None,
        recommended_time: str | None = None,
        participants: list[str] | None = None,
    ) -> dict:
        base = self._plan_with_mock(
            meeting_day,
            meeting_date=meeting_date,
            meeting_title=meeting_title,
            recommended_time=recommended_time,
            participants=participants,
        )
        base["provider"] = "google-placeholder"
        base["note"] = (
            "Google Calendar integration point is prepared. "
            "Add OAuth credentials and API call implementation in this method."
        )
        return base
