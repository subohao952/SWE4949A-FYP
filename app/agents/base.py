from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from typing import Any

from app.models import AgentTask, TaskStatus

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)
_HASHTAG_PATTERN = re.compile(r"#\w+")
_MULTI_SPACE_PATTERN = re.compile(r"\s{2,}")


def strip_emojis(text: str) -> str:
    return _EMOJI_PATTERN.sub("", text).strip()


def strip_hashtags(text: str) -> str:
    cleaned = _HASHTAG_PATTERN.sub("", text)
    return _MULTI_SPACE_PATTERN.sub(" ", cleaned).strip()


def sanitize_social_draft(text: str) -> str:
    return strip_hashtags(strip_emojis(text))


def sanitize_document_text(text: str) -> str:
    """Remove emojis/hashtags from multi-line email or memo text."""
    lines = [sanitize_social_draft(line) for line in text.splitlines()]
    return "\n".join(line for line in lines if line is not None).strip()


class BaseAgent(ABC):
    name: str

    @abstractmethod
    def run(self, payload: dict[str, Any]) -> AgentTask:
        raise NotImplementedError

    def _wrap_run(self, payload: dict[str, Any], executor) -> AgentTask:
        task = AgentTask(agent_name=self.name, input_payload=payload)
        start = time.perf_counter()
        try:
            output, confidence = executor(payload)
            task.output_payload = output
            task.confidence = confidence
            task.status = TaskStatus.SUCCESS if confidence >= 0.6 else TaskStatus.HUMAN_REVIEW
        except Exception as exc:
            task.status = TaskStatus.FAILED
            task.error_message = str(exc)
        finally:
            task.latency_ms = max(1, int((time.perf_counter() - start) * 1000))
        return task

