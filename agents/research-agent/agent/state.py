from typing_extensions import TypedDict


class ResearchAgentState(TypedDict):
    # Input
    topic: str                      # research topic/question
    domain: str                     # e.g. "data_governance", "cloud_strategy"
    submitted_by: str

    # Research outputs
    web_results: list[dict]         # [{title, url, snippet}]
    synthesized_summary: str        # LLM synthesis of web results
    candidate_triples: list[dict]   # [{subject, predicate, object}]
    sparql_insert: str              # INSERT for candidate graph

    # Human review (S5-AA-007)
    human_review_required: bool
    reviewer_decision: str | None
    reviewer_note: str | None

    # Status
    status: str                     # researching | pending | approved | rejected | published | failed
    published_uri: str | None
