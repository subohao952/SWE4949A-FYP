const runBtn = document.getElementById("runBtn");
const promptInput = document.getElementById("prompt");
const statusText = document.getElementById("status");
const scheduleResultBox = document.getElementById("scheduleResult");
const marketingResultBox = document.getElementById("marketingResult");
const documentResultBox = document.getElementById("documentResult");

function normalizeToLines(value) {
  if (Array.isArray(value)) return value.map(String).filter(Boolean);
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return [];
    const lines = value
      .split(/\r?\n/)
      .map((x) => x.trim())
      .filter((x) => x.length > 0);
    return lines.length ? lines : [trimmed];
  }
  return [];
}

function isDraftHeaderLine(line) {
  const cleaned = line.replace(/^\*\*|\*\*$/g, "").trim();
  return /^tweet drafts?\b/i.test(cleaned) || /^marketing drafts?\b/i.test(cleaned);
}

function renderSchedule(schedule) {
  const participants = Array.isArray(schedule.participants)
    ? schedule.participants.join(", ")
    : schedule.participants
      ? String(schedule.participants)
      : "-";
  scheduleResultBox.innerHTML = `
    <div><b>Title:</b> ${schedule.meeting_title || "-"}</div>
    <div><b>Recommended:</b> ${schedule.recommended_date_long || schedule.recommended_date || "-"} ${schedule.recommended_time || ""}</div>
    <div><b>Participants:</b> ${participants}</div>
  `;
}

function renderMarketing(marketing) {
  const tweets = normalizeToLines(marketing.tweet_drafts).filter((line) => !isDraftHeaderLine(line));
  marketingResultBox.innerHTML = `
    <div><b>Channel:</b> ${marketing.channel || "-"}</div>
    <div><b>Campaign theme:</b> ${marketing.campaign_theme || "-"}</div>
    <div style="margin-top:6px;"><b>Drafts:</b></div>
    ${
      tweets.length
        ? `<ol class="draft-list">${tweets.map((x) => `<li>${x}</li>`).join("")}</ol>`
        : "-"
    }
  `;
}

function renderDocument(documentPayload) {
  const emailHtml = documentPayload.announcement_email
    ? `<pre class="email-pre">${documentPayload.announcement_email}</pre>`
    : "-";
  documentResultBox.innerHTML = emailHtml;
}

const WORKFLOW_TIMEOUT_MS = 6 * 60 * 1000;

runBtn.addEventListener("click", async () => {
  const userInput = promptInput.value.trim();
  if (!userInput) {
    statusText.textContent = "Please enter a business request.";
    return;
  }

  runBtn.disabled = true;
  const startedAt = Date.now();
  const tickStatus = () => {
    const sec = Math.floor((Date.now() - startedAt) / 1000);
    statusText.textContent = `Running workflow... ${sec}s (Schedule, Marketing, Document)`;
  };
  tickStatus();
  const statusTimer = setInterval(tickStatus, 1000);

  scheduleResultBox.textContent = "Running...";
  marketingResultBox.textContent = "Waiting...";
  documentResultBox.textContent = "Waiting...";

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), WORKFLOW_TIMEOUT_MS);

  try {
    const response = await fetch("/api/workflow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_input: userInput }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Unknown error");
    }

    const data = await response.json();
    const elapsedSec = Math.round((Date.now() - startedAt) / 1000);
    statusText.textContent = `Workflow completed. Time: ${elapsedSec}s`;

    const tasks = Array.isArray(data.tasks) ? data.tasks : [];
    const byName = {};
    for (const t of tasks) byName[t.agent_name] = t;

    const hasSchedule = Object.prototype.hasOwnProperty.call(byName, "schedule_agent");
    const hasMarketing = Object.prototype.hasOwnProperty.call(byName, "marketing_agent");
    const hasDocument = Object.prototype.hasOwnProperty.call(byName, "document_agent");

    if (!hasSchedule) {
      scheduleResultBox.textContent = "Not requested in this input.";
    } else {
      renderSchedule(byName["schedule_agent"]?.output_payload || {});
    }

    if (!hasMarketing) {
      marketingResultBox.textContent = "Not requested in this input.";
    } else {
      renderMarketing(byName["marketing_agent"]?.output_payload || {});
    }

    if (!hasDocument) {
      documentResultBox.textContent = "Not requested in this input.";
    } else {
      renderDocument(byName["document_agent"]?.output_payload || {});
    }
  } catch (error) {
    statusText.textContent = "Workflow failed.";
    let message = String(error);
    if (error.name === "AbortError") {
      message =
        "Request timed out (6 min). Check Ollama is running, or set LLM_PROVIDER=mock for a quick test.";
    } else if (message.includes("Failed to fetch")) {
      message =
        "Cannot reach server. Start the app (uvicorn) and open http://127.0.0.1:8000";
    }
    scheduleResultBox.textContent = message;
    marketingResultBox.textContent = message;
    documentResultBox.textContent = message;
  } finally {
    clearInterval(statusTimer);
    clearTimeout(timeoutId);
    runBtn.disabled = false;
  }
});
