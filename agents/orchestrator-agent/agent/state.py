from typing import Annotated, Any
from langgraph.graph.message import add_messages
from pydantic import BaseModel


class OrchestratorState(BaseModel):
    assessment_id: str = ""
    messages: Annotated[list, add_messages] = []

    # Task completion tracking (S4-AA-002)
    all_tasks: list[dict] = []
    completed_tasks: list[str] = []
    pending_tasks: list[str] = []

    # Cross-task analysis (S4-AA-003)
    cross_task_dependencies: list[dict] = []
    shared_risk_areas: list[dict] = []

    # Conflict detection (S4-AA-004)
    conflicts: list[dict] = []          # findings with contradictory severity
    conflicts_pending_review: list[str] = []  # conflict IDs awaiting human decision

    # Risk consolidation (S4-AA-005)
    risk_heatmap: list[dict] = []       # [{capability_area, severity, count, workstreams}]
    consolidated_risks: list[dict] = []
    propagated_risks: list[dict] = []   # Rule 6 inferred

    # Outputs (S4-AA-006, S4-AA-007)
    executive_summary: str = ""
    consolidated_roadmap: list[dict] = []

    # Control flags
    human_review_required: bool = False
    rule6_executed: bool = False
