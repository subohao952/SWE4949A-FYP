from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    HUMAN_REVIEW = "human_review"


class AgentTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    latency_ms: int = 0
    status: TaskStatus = TaskStatus.PENDING
    error_message: str | None = None


class WorkflowRequest(BaseModel):
    user_input: str = Field(min_length=5, max_length=1000)


class WorkflowResponse(BaseModel):
    request_id: str
    created_at: datetime
    summary: str
    success_rate: float
    total_latency_ms: int
    fallback_triggered: bool
    llm_provider: str = "mock"
    router_model: str = "rule-based"
    generation_model: str = "template-engine"
    estimated_cost_usd: float = 0.0
    tasks: list[AgentTask]


class BatchExperimentRequest(BaseModel):
    prompts: list[str] = Field(min_length=1, max_length=50)


class BatchExperimentResponse(BaseModel):
    total_requests: int
    processed_requests: int
    avg_success_rate: float
    avg_latency_ms: float
    fallback_rate: float
    request_ids: list[str]


class PresetExperimentRequest(BaseModel):
    preset_name: str = Field(min_length=1, max_length=30)


class ReportGenerationResponse(BaseModel):
    output_path: str
    generated_at: datetime
    included_runs: int


class HumanReviewActionRequest(BaseModel):
    task_id: str = Field(min_length=3)
    approved: bool
    reviewer_comment: str = Field(default="", max_length=500)

