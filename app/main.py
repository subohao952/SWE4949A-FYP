from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.models import (
    BatchExperimentRequest,
    BatchExperimentResponse,
    HumanReviewActionRequest,
    PresetExperimentRequest,
    ReportGenerationResponse,
    WorkflowRequest,
)
from app.services.evaluation_store import EvaluationStore
from app.services.orchestrator import OrchestratorService

app = FastAPI(title="Enterprise Agentic Automation MVP", version="0.1.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

orchestrator = OrchestratorService()
evaluation_store = EvaluationStore()

EXPERIMENT_PRESETS: dict[str, list[str]] = {
    "A_SIMPLE": [
        "Schedule a team meeting for Tuesday and draft an announcement email.",
        "Create 3 tweet drafts for product launch next Friday.",
        "Prepare a short proposal outline for campaign kickoff.",
    ],
    "B_MEDIUM": [
        "Prepare launch content for next Friday, schedule a review meeting for Wednesday, and draft one internal summary email.",
        "Create social media drafts for X and a proposal outline for stakeholders.",
        "Schedule cross-team sync for Thursday and generate talking points document.",
    ],
    "C_STRESS": [
        "We launch next week but date is uncertain, draft fallback campaign content and schedule meeting.",
        "Create announcement email and three social posts with minimal context.",
        "who are you",
        "Plan campaign assets and schedule a conflict-prone meeting for Friday.",
    ],
}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/workflow")
def run_workflow(payload: WorkflowRequest):
    try:
        workflow = orchestrator.execute_workflow(payload.user_input)
        evaluation_store.save_workflow(workflow)
        return workflow
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {exc}") from exc


@app.post("/api/debug/keyword-match")
def debug_keyword_match(payload: WorkflowRequest):
    return orchestrator.debug_keyword_match(payload.user_input)


@app.get("/api/metrics/summary")
def metrics_summary():
    return evaluation_store.summary()


@app.get("/api/hitl/pending")
def list_pending_reviews():
    return {"items": evaluation_store.pending_reviews()}


@app.post("/api/hitl/review")
def resolve_pending_review(payload: HumanReviewActionRequest):
    ok = evaluation_store.resolve_review(
        task_id=payload.task_id,
        approved=payload.approved,
        reviewer_comment=payload.reviewer_comment.strip(),
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Pending review task not found.")
    return {"ok": True, "task_id": payload.task_id, "approved": payload.approved}


@app.get("/api/metrics/export.csv")
def metrics_export_csv():
    csv_text = evaluation_store.export_runs_csv()
    headers = {"Content-Disposition": "attachment; filename=workflow_runs.csv"}
    return Response(content=csv_text, media_type="text/csv", headers=headers)


@app.post("/api/experiments/run", response_model=BatchExperimentResponse)
def run_batch_experiment(payload: BatchExperimentRequest):
    workflows = []
    for prompt in payload.prompts:
        workflow = orchestrator.execute_workflow(prompt)
        evaluation_store.save_workflow(workflow)
        workflows.append(workflow)

    if not workflows:
        return BatchExperimentResponse(
            total_requests=0,
            processed_requests=0,
            avg_success_rate=0.0,
            avg_latency_ms=0.0,
            fallback_rate=0.0,
            request_ids=[],
        )

    avg_success_rate = sum(w.success_rate for w in workflows) / len(workflows)
    avg_latency = sum(w.total_latency_ms for w in workflows) / len(workflows)
    fallback_count = sum(1 for w in workflows if w.fallback_triggered)
    fallback_rate = fallback_count / len(workflows)

    return BatchExperimentResponse(
        total_requests=len(payload.prompts),
        processed_requests=len(workflows),
        avg_success_rate=round(avg_success_rate, 4),
        avg_latency_ms=round(avg_latency, 2),
        fallback_rate=round(fallback_rate, 4),
        request_ids=[w.request_id for w in workflows],
    )


@app.get("/api/experiments/presets")
def list_experiment_presets():
    return {
        "presets": [
            {"name": key, "prompt_count": len(value)} for key, value in EXPERIMENT_PRESETS.items()
        ]
    }


@app.post("/api/experiments/run-preset", response_model=BatchExperimentResponse)
def run_preset_experiment(payload: PresetExperimentRequest):
    preset_name = payload.preset_name.strip().upper()
    prompts = EXPERIMENT_PRESETS.get(preset_name)
    if not prompts:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown preset '{payload.preset_name}'. Use /api/experiments/presets.",
        )
    return run_batch_experiment(BatchExperimentRequest(prompts=prompts))


@app.post("/api/reports/generate", response_model=ReportGenerationResponse)
def generate_results_report():
    summary = evaluation_store.summary()
    recent_runs = evaluation_store.recent_runs(limit=20)
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    output_path = docs_dir / "results.md"
    generated_at = datetime.utcnow()

    lines = [
        "# Experiment Results Snapshot",
        "",
        f"Generated at (UTC): {generated_at.isoformat()}",
        "",
        "## KPI Summary",
        "",
        f"- Total runs: {summary['total_runs']}",
        f"- Average success rate: {summary['avg_success_rate']}",
        f"- Average latency (ms): {summary['avg_latency_ms']}",
        f"- Fallback count: {summary['fallback_count']}",
        f"- Fallback rate: {summary['fallback_rate']}",
        f"- Total estimated cost (USD): {summary['total_estimated_cost_usd']}",
        f"- Average estimated cost per run (USD): {summary['avg_estimated_cost_usd']}",
        f"- Average task confidence: {summary['avg_task_confidence']}",
        f"- Average task latency (ms): {summary['avg_task_latency_ms']}",
        "",
        "## Recent Runs (up to 20)",
        "",
        "| request_id | created_at | success_rate | latency_ms | fallback | task_count | est_cost_usd |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for run in recent_runs:
        lines.append(
            f"| {run['request_id']} | {run['created_at']} | {run['success_rate']} | "
            f"{run['total_latency_ms']} | {int(run['fallback_triggered'])} | {run['task_count']} | {run['estimated_cost_usd']} |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- These values are generated from local SQLite records (`app_data.db`).",
        "- Use this file as direct input for thesis Chapter 5 (Evaluation).",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return ReportGenerationResponse(
        output_path=str(output_path),
        generated_at=generated_at,
        included_runs=len(recent_runs),
    )

