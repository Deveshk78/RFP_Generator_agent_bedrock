from __future__ import annotations

from typing import Any, Tuple, List

from .validator import validate_rfp_markdown


def generate_rfp_with_validation(agent: Any, domain: Any, body: Any, max_attempts: int = 2) -> Tuple[str, List[str]]:
    """Generate an RFP via the agent and validate it; allow limited reruns.

    Returns (content, missing_sections_list).
    """
    attempts = 0
    content = ""
    missing_after: List[str] = []
    while attempts < max_attempts:
        attempts += 1
        content = agent.generate_rfp_document(
            title=body.title,
            domain_label=domain.label,
            domain_category=domain.category,
            domain_description=domain.description,
            compliance=domain.compliance,
            typical_systems=domain.typical_systems,
            project_summary=body.project_summary,
            budget_range=body.budget_range,
            timeline=body.timeline,
            organization=body.organization,
        )
        valid, missing = validate_rfp_markdown(content)
        if valid:
            return content, []
        missing_after = missing
    return content, missing_after
