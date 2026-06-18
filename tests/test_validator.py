import sys
from pathlib import Path

# Ensure project root is on sys.path for imports when running pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validator import validate_rfp_markdown


def test_validator_missing_sections():
    md = """
# Introduction
This is an intro.

# Scope
Scope here.

"""
    valid, missing = validate_rfp_markdown(md)
    assert not valid
    assert "Deliverables" in missing
    assert "Evaluation Criteria" in missing
    assert "Submission Instructions" in missing


def test_validator_all_sections_present():
    md = """
# Introduction
Intro text

# Scope
Scope

# Deliverables
Some deliverables

# Evaluation Criteria
Criteria table

# Submission Instructions
Send to procurement
"""
    valid, missing = validate_rfp_markdown(md)
    assert valid
    assert missing == []
