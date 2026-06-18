from __future__ import annotations

import re
from typing import List, Tuple

from jsonschema import Draft7Validator, validate

# Minimal JSON Schema for required RFP sections. This schema expects
# a simple mapping where keys are section headings discovered in the markdown.
RFP_SCHEMA = {
    "type": "object",
    "properties": {
        "Introduction": {"type": "string"},
        "Scope": {"type": "string"},
        "Deliverables": {"type": "string"},
        "Evaluation Criteria": {"type": "string"},
        "Submission Instructions": {"type": "string"},
    },
    "required": [
        "Introduction",
        "Scope",
        "Deliverables",
        "Evaluation Criteria",
        "Submission Instructions",
    ],
}


def extract_headings(markdown: str) -> List[str]:
    """Extract top-level and second-level headings from Markdown text."""
    headings = []
    for line in markdown.splitlines():
        m = re.match(r"^#{1,3}\s+(.*)", line)
        if m:
            headings.append(m.group(1).strip())
    return headings


def rfp_to_doc_structure(markdown: str) -> dict:
    """Create a simple dict mapping heading -> text for schema validation.

    This is intentionally lightweight: it maps the first occurrence of a
    required heading to a non-empty string if present.
    """
    lines = markdown.splitlines()
    structure = {}
    current = None
    buffer = []
    for line in lines:
        m = re.match(r"^#{1,3}\s+(.*)", line)
        if m:
            if current and buffer:
                structure[current] = "\n".join(buffer).strip()
            current = m.group(1).strip()
            buffer = []
        else:
            if current:
                buffer.append(line)
    if current and buffer:
        structure[current] = "\n".join(buffer).strip()
    return structure


def validate_rfp_markdown(markdown: str) -> Tuple[bool, List[str]]:
    """Validate the RFP markdown against a simple schema.

    Returns (is_valid, missing_items).
    """
    structure = rfp_to_doc_structure(markdown)
    validator = Draft7Validator(RFP_SCHEMA)
    errors = list(validator.iter_errors(structure))
    missing = []
    if errors:
        for err in errors:
            if err.validator == "required":
                for missing_key in err.message.split("\'"):
                    if missing_key in RFP_SCHEMA["properties"]:
                        missing.append(missing_key)
    return (len(missing) == 0, missing)


def minimal_headings_ok(markdown: str, required: List[str]) -> bool:
    headings = extract_headings(markdown)
    found = {h.lower() for h in headings}
    return all(r.lower() in found for r in required)
