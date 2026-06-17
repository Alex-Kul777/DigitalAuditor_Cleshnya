"""
Unit tests for tools.risk_matrix module.
"""
import pytest
from tools.risk_matrix import calculate_risk_level


class TestRiskMatrixBasic:
    """Test basic risk matrix calculations."""

    def test_critical_risk_high_high(self):
        """Test High probability + High impact = Critical."""
        assert calculate_risk_level("High", "High") == "Critical"

    def test_low_risk_low_low(self):
        """Test Low probability + Low impact = Low."""
        assert calculate_risk_level("Low", "Low") == "Low"


class TestRiskMatrixHighProbability:
    """Test all High probability combinations."""

    def test_high_prob_high_impact(self):
        """High probability + High impact = Critical."""
        assert calculate_risk_level("High", "High") == "Critical"

    def test_high_prob_medium_impact(self):
        """High probability + Medium impact = High."""
        assert calculate_risk_level("High", "Medium") == "High"

    def test_high_prob_low_impact(self):
        """High probability + Low impact = Medium."""
        assert calculate_risk_level("High", "Low") == "Medium"


class TestRiskMatrixMediumProbability:
    """Test all Medium probability combinations."""

    def test_medium_prob_high_impact(self):
        """Medium probability + High impact = High."""
        assert calculate_risk_level("Medium", "High") == "High"

    def test_medium_prob_medium_impact(self):
        """Medium probability + Medium impact = Medium."""
        assert calculate_risk_level("Medium", "Medium") == "Medium"

    def test_medium_prob_low_impact(self):
        """Medium probability + Low impact = Low."""
        assert calculate_risk_level("Medium", "Low") == "Low"


class TestRiskMatrixLowProbability:
    """Test all Low probability combinations."""

    def test_low_prob_high_impact(self):
        """Low probability + High impact = Medium."""
        assert calculate_risk_level("Low", "High") == "Medium"

    def test_low_prob_medium_impact(self):
        """Low probability + Medium impact = Low."""
        assert calculate_risk_level("Low", "Medium") == "Low"

    def test_low_prob_low_impact(self):
        """Low probability + Low impact = Low."""
        assert calculate_risk_level("Low", "Low") == "Low"


class TestRiskMatrixEdgeCases:
    """Test edge cases and invalid inputs."""

    def test_invalid_probability(self):
        """Test invalid probability defaults to Medium."""
        assert calculate_risk_level("Unknown", "High") == "Medium"

    def test_invalid_impact(self):
        """Test invalid impact defaults to Medium."""
        assert calculate_risk_level("High", "Unknown") == "Medium"

    def test_invalid_both(self):
        """Test both invalid inputs default to Medium."""
        assert calculate_risk_level("Unknown", "Invalid") == "Medium"

    def test_empty_strings(self):
        """Test empty strings default to Medium."""
        assert calculate_risk_level("", "") == "Medium"

    def test_case_sensitivity(self):
        """Test that function is case-sensitive."""
        # The function expects exact case matches
        result = calculate_risk_level("high", "high")
        assert result == "Medium"  # Should not match "High"

    def test_whitespace_handling(self):
        """Test that function doesn't handle whitespace."""
        result = calculate_risk_level(" High ", "High")
        assert result == "Medium"  # Should not match with spaces


class TestRiskMatrixCompleteness:
    """Test that all valid combinations are covered."""

    @pytest.mark.parametrize(
        "probability,impact,expected",
        [
            ("High", "High", "Critical"),
            ("High", "Medium", "High"),
            ("High", "Low", "Medium"),
            ("Medium", "High", "High"),
            ("Medium", "Medium", "Medium"),
            ("Medium", "Low", "Low"),
            ("Low", "High", "Medium"),
            ("Low", "Medium", "Low"),
            ("Low", "Low", "Low"),
        ],
    )
    def test_all_combinations(self, probability, impact, expected):
        """Test all valid probability/impact combinations."""
        assert calculate_risk_level(probability, impact) == expected


@pytest.mark.unit
def test_risk_level_type():
    """Test that risk level is always a string."""
    result = calculate_risk_level("High", "High")
    assert isinstance(result, str)
    assert len(result) > 0
