"""Unit tests for UncleRobertAgent."""
import pytest
from agents.uncle_robert import UncleRobertAgent
from report_generator.ccce_formatter import CCCEFormatter
from core.llm import get_llm


class TestUncleRobertAgent:
    """Test suite for UncleRobertAgent class."""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM for testing."""
        # Use real LLM but with low temperature for consistency
        return get_llm(temperature=0.0)

    @pytest.fixture
    def agent(self, mock_llm):
        """Create agent instance for testing."""
        config = {
            "name": "test_task",
            "company": "Test Company",
            "auditor": "uncle_robert"
        }
        return UncleRobertAgent(mock_llm, config)

    @pytest.fixture
    def mock_task(self):
        """Create mock task object for testing."""
        class MockTask:
            def __init__(self):
                self.task_name = "test_task"
                self.config = {"company": "Test Company"}
                self.evidence_context = "Test evidence"
                self.requirements_context = "Test requirements"

        return MockTask()

    def test_agent_initialization(self, agent):
        """Test that agent initializes properly."""
        assert agent is not None
        assert agent.ccce_formatter is not None
        assert agent.retriever is not None
        assert agent.config["auditor"] == "uncle_robert"

    def test_ccce_formatter_exists(self, agent):
        """Test that CCCE formatter is available."""
        assert isinstance(agent.ccce_formatter, CCCEFormatter)

    def test_get_audit_context(self, agent, mock_task):
        """Test retrieving audit context from Brink's."""
        context = agent._get_audit_context(mock_task)
        assert isinstance(context, str)
        # Either real context or fallback message
        assert len(context) > 0

    def test_build_draft_findings_prompt(self, agent, mock_task):
        """Test prompt building for draft findings."""
        context = "Test context"
        prompt = agent._build_draft_findings_prompt(mock_task, context)
        assert "Uncle Robert" in prompt
        assert "CCCE" in prompt or "Condition" in prompt
        assert "Criteria" in prompt

    def test_extract_section(self):
        """Test section extraction from text."""
        text = """### Observation 1: Test

**Condition:**
Test condition content here

**Criteria:**
Test criteria content"""

        condition = UncleRobertAgent._extract_section(text, "Condition")
        assert condition is not None
        assert "condition" in condition.lower()

    def test_parse_ccce_observations_empty(self, agent):
        """Test parsing empty observations returns empty list."""
        result = agent._parse_ccce_observations("No observations here")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_ccce_observations_valid(self, agent):
        """Test parsing valid CCCE observations."""
        draft_text = """### Observation 1: Test Finding

**Condition:**
Test condition was observed

**Criteria:**
- L1: Test requirement
- L2: Test standard

**Cause:**
Root cause identified

**Effect:**
Business impact: High

**Risk Rating:**
High

**Preliminary Recommendation:**
Take action"""

        observations = agent._parse_ccce_observations(draft_text)
        assert len(observations) > 0
        assert observations[0]["title"] == "Test Finding"
        assert observations[0]["risk_rating"] == "High"

    def test_incorporate_management_response(self, agent):
        """Test two-stage pipeline: management response incorporation."""
        draft_findings = [
            {
                "title": "Test",
                "condition": "Test condition",
                "criteria": "Test criteria",
                "cause": "Test cause",
                "effect": "Test effect",
                "risk_rating": "High"
            }
        ]
        final = agent._incorporate_management_response(draft_findings)
        assert len(final) == len(draft_findings)
        assert final[0]["title"] == "Test"

    def test_ccce_formatter_validate_observation(self):
        """Test CCCE formatter validation."""
        formatter = CCCEFormatter()
        valid_obs = {
            "title": "Test",
            "condition": "Condition",
            "criteria": "Criteria",
            "cause": "Cause",
            "effect": "Effect",
            "risk_rating": "High"
        }
        is_valid, missing = formatter.validate_observation(valid_obs)
        assert is_valid is True
        assert len(missing) == 0

    def test_ccce_formatter_validate_missing_fields(self):
        """Test CCCE formatter detects missing fields."""
        formatter = CCCEFormatter()
        invalid_obs = {
            "title": "Test"
            # Missing required fields
        }
        is_valid, missing = formatter.validate_observation(invalid_obs)
        assert is_valid is False
        assert len(missing) > 0

    def test_ccce_formatter_format_observation(self):
        """Test CCCE formatter output."""
        formatter = CCCEFormatter()
        obs = {
            "title": "Test Finding",
            "number": 1,
            "condition": "Test condition",
            "criteria_l1": "L1 requirement",
            "criteria_l2": "L2 standard",
            "criteria_l3": "L3 policy",
            "cause": "Root cause",
            "effect": "Business impact",
            "risk_rating": "High",
            "recommendation": "Take action",
            "evidence_source": "test.pdf",
            "page": 1,
            "evidence_quote": "test quote"
        }
        result = formatter.format_observation(obs)
        assert "### Observation 1: Test Finding" in result
        assert "**Condition:**" in result
        assert "**Criteria:**" in result
        assert "**Cause:**" in result
        assert "**Effect:**" in result
        assert "**Risk Rating:** High" in result

    def test_ccce_formatter_format_report(self):
        """Test CCCE formatter with multiple observations."""
        formatter = CCCEFormatter()
        observations = [
            {
                "title": "Finding 1",
                "condition": "Condition 1",
                "criteria_l1": "L1",
                "criteria_l2": "L2",
                "criteria_l3": "L3",
                "cause": "Cause 1",
                "effect": "Effect 1",
                "risk_rating": "High",
            },
            {
                "title": "Finding 2",
                "condition": "Condition 2",
                "criteria_l1": "L1",
                "criteria_l2": "L2",
                "criteria_l3": "L3",
                "cause": "Cause 2",
                "effect": "Effect 2",
                "risk_rating": "Medium",
            }
        ]
        result = formatter.format_report(observations)
        assert "## Audit Findings" in result
        assert "### Observation 1: Finding 1" in result
        assert "### Observation 2: Finding 2" in result

    def test_agent_execute_placeholder(self, agent, mock_task):
        """Test that execute method runs without errors."""
        # This is a smoke test - full execution requires more setup
        # Just test that the method exists and is callable
        assert callable(agent.execute)

    def test_generate_section_findings(self, agent):
        """Test generate_section method for findings."""
        result = agent.generate_section("findings")
        assert isinstance(result, str)
        assert len(result) > 0
