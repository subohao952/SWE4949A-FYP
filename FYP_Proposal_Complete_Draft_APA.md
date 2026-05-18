# Front Page (APA Style Template)

**Enterprise Agentic Automation: A Multi-Agent System for Marketing, Scheduling, and Document Generation**

SU BOHAO  
218549  
Bachelor of Software Engineering  
Department of Software Engineering and Information Systems (SEIS)  
Universiti Putra Malaysia

Course: Final Year Project Proposal  
Supervisor: [Supervisor Name]  
Submission Date: [Date]

---

# Table of Contents

1. Introduction  
2. Problem Statement  
3. Objectives  
4. Scope of the Study  
5. Literature Review  
6. Methodology (Concise)  
7. Return on Investment (ROI) / Return on Value (ROV)  
8. Project Planning  
9. Conclusion  
10. References  
11. Appendices  

---

# 1. Introduction

## 1.1 Background and Need
Recent advances in large language models (LLMs) enable systems to move beyond chat-style Q&A into agentic workflows. In practice, business tasks such as scheduling, marketing drafting, and document preparation are still fragmented across separate tools. This creates repeated manual work and inconsistent outputs.

## 1.2 Project Overview
This project proposes a web-based Multi-Agent System (MAS) with:
- one Orchestrator Agent,
- one Schedule Agent,
- one Marketing Agent,
- one Document Agent.

The system accepts one natural-language request, routes tasks to specialized agents, and returns structured outputs in separate UI sections.

## 1.3 Unique Value Proposition
Compared with general chatbots, this proposal focuses on structured multi-step workflow execution with traceable outputs, reliability control (including HITL), and thesis-ready evaluation artifacts.

---

# 2. Problem Statement

## 2.1 Problem Identification
Current business automation is often tool-specific. Teams switch between calendar, writing, and communication platforms, which increases effort and inconsistency. Existing chatbot systems mainly produce text responses and do not reliably coordinate multi-step workflows.

## 2.2 Problem Justification
A multi-agent orchestration approach is suitable because business tasks:
- span different domains (planning, content, documentation),
- require structured and consistent outputs,
- need fallback and review mechanisms,
- and must be measurable in performance.

## 2.3 Impact of the Problem
If unresolved, the problem can cause:
- repeated manual effort,
- delayed campaign preparation,
- inconsistent cross-team communication,
- reduced operational productivity.

This proposal expects improvement in workflow efficiency; exact time-saving values will be validated later through market evidence collection (interviews/survey).

## 2.4 Competitors and Existing Systems (Brief)
- General chatbots: strong in Q&A, weak in structured workflow orchestration.
- Single-domain tools: useful per domain, but fragmented across end-to-end tasks.
- Automation suites: strong integration but not focused on this project's academic MAS evaluation path.

---

# 3. Objectives

## 3.1 General Objective
To design, implement, and evaluate a web-based multi-agent automation prototype that handles scheduling, marketing draft generation, and document drafting from natural-language requests.

## 3.2 Specific Objectives
1. Build an orchestrated architecture with one Orchestrator Agent and three specialized agents.  
2. Implement reliability mechanisms (intent gating, confidence-aware handling, HITL review queue).  
3. Evaluate performance using measurable metrics (success rate, latency, fallback rate, estimated cost).  
4. Run simple/medium/stress scenarios and produce thesis-ready evidence (CSV and results report).  

---

# 4. Scope of the Study

## 4.1 System Scope
Included:
- web-based prototype,
- multi-agent orchestration and routing,
- schedule/marketing/document generation,
- local model integration via Ollama,
- evaluation and batch experiment features,
- HITL review queue and approval flow.

Excluded:
- full enterprise production deployment,
- advanced security hardening and SSO,
- full multi-tenant architecture,
- complete production integration for all external APIs.

## 4.2 User Scope
Primary users:
- small business operators,
- project coordinators,
- marketing teams.

Key stakeholders:
- FYP evaluators and research supervisors.

The prototype is intended for desktop web use in controlled evaluation settings.

## 4.3 Data Scope
This study uses scenario-based prompts and generated outputs rather than a fixed public dataset. Data sources include:
- curated prompts (simple/medium/stress),
- runtime logs,
- per-agent outputs,
- HITL review decisions.

No sensitive personal data is required for core evaluation.

---

# 5. Literature Review

## 5.1 Related Works
Prior studies show that LLM-based agents can improve planning and tool use, but reliability and control remain major concerns. Representative works include ReAct (Yao et al., 2023), Toolformer (Schick et al., 2023), AutoGen (Wu et al., 2023), and recent LLM agent surveys (Wang et al., 2024).

## 5.2 Theoretical Basis
The proposal is grounded in:
- Multi-Agent System architecture,
- task decomposition and orchestration,
- human-in-the-loop safety concept,
- software quality attributes (reliability, efficiency, usability).

## 5.3 Research Gap
Many demos prioritize capability over measurable reliability, provide limited reproducible outputs, and depend heavily on paid cloud APIs. This project addresses that gap with:
- orchestrated multi-agent design,
- local-model-first deployment,
- HITL queue mechanism,
- quantitative reporting for FYP assessment.

---

# 6. Methodology (Concise)

## 6.1 Approach
This project uses a design-and-evaluate prototype approach with iterative implementation and review.

## 6.2 Development Process
Agile incremental development is used with regular supervisor check-ins:
- Sprint 1: architecture and core workflow,
- Sprint 2: agent capabilities and local model support,
- Sprint 3: evaluation and batch experiments,
- Sprint 4: reliability features (HITL) and report consolidation.

## 6.3 Verification and Evaluation
Evaluation uses scenario-based testing and system records:
- task success rate,
- end-to-end latency,
- fallback rate,
- per-agent confidence and latency,
- estimated cost per run.

Outputs are exported as CSV and summarized in `results.md`.

---

# 7. Return on Investment (ROI) / Return on Value (ROV)

## 7.1 Cost-Benefit (Prototype Context)
Costs are mainly development time, with minimal infrastructure cost in local mode (local machine + electricity + Ollama free serving).

Benefits include reduced repeated effort, faster workflow preparation, and better output consistency.

## 7.2 Expected Benefits
Tangible:
- time savings in scheduling and drafting,
- faster preparation cycle,
- fewer operational bottlenecks.

Intangible:
- improved process consistency,
- improved documentation quality,
- stronger confidence through traceable workflow outputs.

## 7.3 Value to Stakeholders
- Students/Researchers: practical MAS engineering and evaluation experience.
- Supervisors/Lecturers: measurable, defensible FYP outcomes.
- Business users: workflow automation potential and better decision support.
- University: alignment with AI-driven software engineering practice.

---

# 8. Project Planning

## 8.1 Work Breakdown Structure (WBS)
| WBS ID | Work Package | Deliverable |
|---|---|---|
| 1.0 | Requirements and Scope | Approved proposal scope |
| 2.0 | Architecture Design | MAS design and flow |
| 3.0 | Core Prototype | Running web prototype |
| 4.0 | Reliability Features | HITL and fallback flow |
| 5.0 | Evaluation Layer | Metrics + CSV export |
| 6.0 | Experiment Runs | Preset scenario outcomes |
| 7.0 | Thesis Writing | Draft chapters and analysis |
| 8.0 | Final Submission | Final document and demo |

## 8.2 Timeframe (Text Plan)
| Week | Main Activities |
|---|---|
| 1-2 | Proposal finalization and architecture confirmation |
| 3-4 | Core workflow implementation |
| 5-6 | Agent integration and local model support |
| 7-8 | Reliability features and supervisor review |
| 9-10 | Experiments and data collection |
| 11 | Report writing and evidence consolidation |
| 12 | Final revision and submission |

## 8.3 Market Analysis Plan (Data Pending)
Market analysis data is not finalized yet and will be collected in the next phase through:
- 3-5 structured interviews, or
- a short questionnaire (10-20 responses).

Final report will include one summary table and one chart from collected data.

---

# 9. Conclusion

## 9.1 Summary of Proposal
This proposal presents a practical, cost-aware multi-agent automation prototype for business workflow tasks. It combines implementation, reliability control, and measurable evaluation suitable for a Software Engineering FYP.

## 9.2 Expected Contributions
- A functional multi-agent prototype.
- A local-first deployment approach with optional cloud extension.
- A measurable reliability/evaluation framework.
- Reproducible reporting artifacts for academic assessment.

---

# 10. References (APA Style, Recent Works)

Schick, T., Dwivedi-Yu, J., et al. (2023). *Toolformer: Language models can teach themselves to use tools*. arXiv. https://arxiv.org/abs/2302.04761

Wang, L., Ma, C., et al. (2024). *A survey on large language model based autonomous agents*. Frontiers of Computer Science. https://arxiv.org/abs/2308.11432

Wu, Q., Bansal, G., Zhang, J., et al. (2023). *AutoGen: Enabling next-gen LLM applications via multi-agent conversation*. arXiv. https://arxiv.org/abs/2308.08155

Yao, S., Zhao, J., Yu, D., et al. (2023). *ReAct: Synergizing reasoning and acting in language models*. arXiv. https://arxiv.org/abs/2210.03629

Qwen Team. (2024). *Qwen2.5 technical report* (model documentation). https://qwenlm.github.io/

---

# 11. Appendices

## A. Interview / Survey Draft Questions
1. Which output type is most useful: schedule, marketing, or document?  
2. Is the generated output clear enough for practical use?  
3. Is response speed acceptable for your workflow?  
4. When should human confirmation be required?  
5. What additional task should be automated next?  

## B. Recommended Diagrams
- System architecture diagram (orchestrator + 3 agents)
- Workflow sequence diagram
- HITL fallback flow diagram

