import sys
from pathlib import Path

# Ensure project root is on sys.path for imports when running pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types

from src.generation import generate_rfp_with_validation
import src.domains as domains


class DummyAgent:
    def __init__(self):
        self.calls = 0

    def generate_rfp_document(self, **kwargs):
        self.calls += 1
        # First call returns incomplete content, second returns complete
        if self.calls == 1:
            return "# Introduction\nIntro\n\n# Scope\nScope\n"
        return "# Introduction\nIntro\n\n# Scope\nScope\n\n# Deliverables\nItems\n\n# Evaluation Criteria\nCriteria\n\n# Submission Instructions\nSubmit here\n"


class DummyStore:
    def __init__(self):
        self._marked = None

    def create_rfp(self, **kwargs):
        return {"rfp_id": "test-id", "title": kwargs.get("title"), "content": kwargs.get("content"), "has_docx": False}

    def set_docx_ready(self, rfp_id, path):
        pass

    def mark_needs_review(self, rfp_id, reason=None):
        self._marked = (rfp_id, reason)


def test_generate_rerun_and_validation(monkeypatch):
    dummy_agent = DummyAgent()
    dummy_store = DummyStore()

    # Use the generation helper directly to test rerun logic
    domain = domains.DOMAIN_BY_ID["solar"]

    class Req:
        title = "Test RFP"
        organization = "Org"
        project_summary = "Project"
        budget_range = "TBD"
        timeline = "6 months"

    content, missing = generate_rfp_with_validation(dummy_agent, domain, Req, max_attempts=2)
    assert dummy_agent.calls == 2
    assert "Introduction" in content
    # Second attempt should have returned full content so missing is empty
    assert missing == []
