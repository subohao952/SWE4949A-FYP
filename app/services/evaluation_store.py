from __future__ import annotations

import csv
import io
import json
import sqlite3
from pathlib import Path

from app.models import WorkflowResponse


class EvaluationStore:
    def __init__(self, db_path: str = "app_data.db") -> None:
        self.db_path = Path(db_path)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    request_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    success_rate REAL NOT NULL,
                    total_latency_ms INTEGER NOT NULL,
                    fallback_triggered INTEGER NOT NULL,
                    task_count INTEGER NOT NULL,
                    llm_provider TEXT NOT NULL DEFAULT 'mock',
                    router_model TEXT NOT NULL DEFAULT 'rule-based',
                    generation_model TEXT NOT NULL DEFAULT 'template-engine',
                    estimated_cost_usd REAL NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    task_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    input_payload TEXT NOT NULL,
                    output_payload TEXT NOT NULL,
                    error_message TEXT,
                    FOREIGN KEY (request_id) REFERENCES workflow_runs(request_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pending_reviews (
                    task_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    approved INTEGER,
                    reviewer_comment TEXT
                )
                """
            )
            # Backward-compatible migration for existing databases.
            for ddl in [
                "ALTER TABLE workflow_runs ADD COLUMN llm_provider TEXT NOT NULL DEFAULT 'mock'",
                "ALTER TABLE workflow_runs ADD COLUMN router_model TEXT NOT NULL DEFAULT 'rule-based'",
                "ALTER TABLE workflow_runs ADD COLUMN generation_model TEXT NOT NULL DEFAULT 'template-engine'",
                "ALTER TABLE workflow_runs ADD COLUMN estimated_cost_usd REAL NOT NULL DEFAULT 0",
            ]:
                try:
                    conn.execute(ddl)
                except sqlite3.OperationalError:
                    pass

    def save_workflow(self, workflow: WorkflowResponse) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_runs (
                    request_id, created_at, summary, success_rate,
                    total_latency_ms, fallback_triggered, task_count,
                    llm_provider, router_model, generation_model, estimated_cost_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow.request_id,
                    workflow.created_at.isoformat(),
                    workflow.summary,
                    workflow.success_rate,
                    workflow.total_latency_ms,
                    int(workflow.fallback_triggered),
                    len(workflow.tasks),
                    workflow.llm_provider,
                    workflow.router_model,
                    workflow.generation_model,
                    workflow.estimated_cost_usd,
                ),
            )

            for task in workflow.tasks:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO agent_tasks (
                        task_id, request_id, agent_name, status, confidence, latency_ms,
                        input_payload, output_payload, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.task_id,
                        workflow.request_id,
                        task.agent_name,
                        task.status.value,
                        task.confidence,
                        task.latency_ms,
                        json.dumps(task.input_payload, ensure_ascii=False),
                        json.dumps(task.output_payload, ensure_ascii=False),
                        task.error_message,
                    ),
                )
                if task.status.value in {"human_review", "failed"}:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO pending_reviews (
                            task_id, request_id, agent_name, reason, resolved
                        ) VALUES (?, ?, ?, ?, 0)
                        """,
                        (
                            task.task_id,
                            workflow.request_id,
                            task.agent_name,
                            task.error_message or "Low confidence output requires human review.",
                        ),
                    )

    def summary(self) -> dict:
        with self._get_conn() as conn:
            run_row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_runs,
                    COALESCE(AVG(success_rate), 0) AS avg_success_rate,
                    COALESCE(AVG(total_latency_ms), 0) AS avg_latency_ms,
                    COALESCE(SUM(fallback_triggered), 0) AS fallback_count,
                    COALESCE(SUM(estimated_cost_usd), 0) AS total_cost_usd,
                    COALESCE(AVG(estimated_cost_usd), 0) AS avg_cost_usd
                FROM workflow_runs
                """
            ).fetchone()
            task_row = conn.execute(
                """
                SELECT
                    COALESCE(AVG(confidence), 0) AS avg_confidence,
                    COALESCE(AVG(latency_ms), 0) AS avg_task_latency_ms
                FROM agent_tasks
                """
            ).fetchone()

        total_runs = int(run_row[0] or 0)
        fallback_count = int(run_row[3] or 0)
        fallback_rate = round((fallback_count / total_runs), 4) if total_runs else 0.0
        return {
            "total_runs": total_runs,
            "avg_success_rate": round(float(run_row[1] or 0), 4),
            "avg_latency_ms": round(float(run_row[2] or 0), 2),
            "fallback_count": fallback_count,
            "fallback_rate": fallback_rate,
            "avg_task_confidence": round(float(task_row[0] or 0), 4),
            "avg_task_latency_ms": round(float(task_row[1] or 0), 2),
            "total_estimated_cost_usd": round(float(run_row[4] or 0), 6),
            "avg_estimated_cost_usd": round(float(run_row[5] or 0), 6),
        }

    def export_runs_csv(self) -> str:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    request_id, created_at, summary, success_rate,
                    total_latency_ms, fallback_triggered, task_count,
                    llm_provider, router_model, generation_model, estimated_cost_usd
                FROM workflow_runs
                ORDER BY created_at DESC
                """
            ).fetchall()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "request_id",
                "created_at",
                "summary",
                "success_rate",
                "total_latency_ms",
                "fallback_triggered",
                "task_count",
                "llm_provider",
                "router_model",
                "generation_model",
                "estimated_cost_usd",
            ]
        )
        writer.writerows(rows)
        return output.getvalue()

    def recent_runs(self, limit: int = 20) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    request_id, created_at, summary, success_rate,
                    total_latency_ms, fallback_triggered, task_count, estimated_cost_usd
                FROM workflow_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {
                "request_id": row[0],
                "created_at": row[1],
                "summary": row[2],
                "success_rate": row[3],
                "total_latency_ms": row[4],
                "fallback_triggered": bool(row[5]),
                "task_count": row[6],
                "estimated_cost_usd": row[7],
            }
            for row in rows
        ]

    def pending_reviews(self) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT task_id, request_id, agent_name, reason, created_at
                FROM pending_reviews
                WHERE resolved = 0
                ORDER BY created_at ASC
                """
            ).fetchall()
        return [
            {
                "task_id": r[0],
                "request_id": r[1],
                "agent_name": r[2],
                "reason": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

    def resolve_review(self, task_id: str, approved: bool, reviewer_comment: str) -> bool:
        with self._get_conn() as conn:
            exists = conn.execute(
                "SELECT task_id FROM pending_reviews WHERE task_id = ? AND resolved = 0",
                (task_id,),
            ).fetchone()
            if not exists:
                return False
            conn.execute(
                """
                UPDATE pending_reviews
                SET resolved = 1, approved = ?, reviewer_comment = ?
                WHERE task_id = ?
                """,
                (int(approved), reviewer_comment, task_id),
            )
            conn.execute(
                "UPDATE agent_tasks SET status = ?, error_message = ? WHERE task_id = ?",
                ("success" if approved else "failed", reviewer_comment, task_id),
            )
        return True

