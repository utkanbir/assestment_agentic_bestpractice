from typing_extensions import TypedDict


class CopilotState(TypedDict):
    # Input
    proposal_text: str          # natural language ontology proposal
    submitted_by: str           # keycloak user sub

    # Derived
    candidate_triples: list[dict]   # [{subject, predicate, object}]
    sparql_insert: str              # generated SPARQL INSERT for candidate graph
    validation_errors: list[str]    # SHACL violations if any

    # Human review
    human_review_required: bool
    reviewer_decision: str | None   # "approved" | "rejected"
    reviewer_note: str | None

    # Output
    published_uri: str | None       # Fuseki URI after approval
    status: str                     # pending | approved | rejected | failed
