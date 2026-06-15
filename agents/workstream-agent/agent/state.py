from typing import Annotated

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class WorkstreamAgentState(TypedDict):
    # Identifiers
    assessment_id: str
    task_id: str
    interview_id: str
    workstream: str  # cloud_strategy | ingestion | teradata_dr | lakehouse | governance | data_product | cdp

    # Interview context
    task_scope: str
    covered_areas: list[str]
    existing_findings: list[dict]

    # Live interview state
    messages: Annotated[list, add_messages]
    current_question: str
    last_answer: str
    answer_count: int

    # Captured artifacts
    pending_evidence: list[dict]
    pending_findings: list[dict]

    # Control flow
    phase: str
    should_end_interview: bool
    human_approval_required: bool
    approved_finding_ids: list[str]
    evidence_captured: bool

    # Qdrant similar findings
    similar_findings: list[dict]

    # Derived risk and inference artifacts
    generated_risks: list[dict]
    inference_results: dict
    low_confidence_gaps: list[dict]

    # Output
    report_markdown: str
    error: str | None
