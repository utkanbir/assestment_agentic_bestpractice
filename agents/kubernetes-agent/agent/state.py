from typing import Annotated, Any
from uuid import UUID

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class KubernetesAgentState(TypedDict):
    # Identifiers
    assessment_id: str
    task_id: str
    interview_id: str

    # Interview context (loaded in PRE_INTERVIEW)
    task_scope: str
    covered_areas: list[str]
    existing_findings: list[dict]

    # Live interview state
    messages: Annotated[list, add_messages]   # LangChain message history
    current_question: str
    last_answer: str
    answer_count: int

    # Captured artifacts
    pending_evidence: list[dict]    # evidence not yet written to KG
    pending_findings: list[dict]    # findings pending human approval

    # Control flow
    phase: str                      # PRE_INTERVIEW | INTERVIEW_LOOP | POST_INTERVIEW | DONE
    should_end_interview: bool
    human_approval_required: bool
    approved_finding_ids: list[str]
    evidence_captured: bool         # S2-AA-003: set by evidence_capture, guards finding_detector

    # S2-AA-001: risks derived from approved findings
    generated_risks: list[dict]

    # S2-AA-002: confidence propagation results
    inference_results: dict       # rule_name → "ok" | "error: ..."
    low_confidence_gaps: list[dict]  # gaps below threshold after Rule 5

    # Output
    report_markdown: str
    error: str | None
