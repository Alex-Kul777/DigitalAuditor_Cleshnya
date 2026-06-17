"""CCCE Formatter for Uncle Robert audit findings (Condition/Criteria/Cause/Effect)."""


class CCCEFormatter:
    """Format observations using CCCE structure (Brink's Chapter 17)."""

    def __init__(self):
        """Initialize CCCE formatter with template."""
        self.template = """### Observation {number}: {title}

**Condition:**
{condition}

**Criteria:**
- **L1 (Regulatory):** {criteria_l1}
- **L2 (Audit Standard):** {criteria_l2}
- **L3 (Local Policy):** {criteria_l3}

**Cause:**
{cause}

**Effect:**
{effect}

**Risk Rating:** {risk_rating}

**Recommendation:**
{recommendation}

**Management Response:** (to be completed during review)

**Sources:**
| Type | Document | Page | Quote |
|------|----------|------|-------|
| Evidence | {evidence_source} | {page} | "{evidence_quote}" |
| L1 | {l1_source} | {l1_page} | "{l1_quote}" |
| L2 | {l2_source} | {l2_page} | "{l2_quote}" |
| L3 | {l3_source} | {l3_page} | "{l3_quote}" |
"""

    def format_observation(self, observation: dict) -> str:
        """Convert observation dict to formatted markdown.

        Args:
            observation: dict with keys for all template placeholders

        Returns:
            Formatted markdown string
        """
        # Provide defaults for optional fields
        defaults = {
            'title': 'Untitled Observation',
            'number': 1,
            'condition': 'Not provided',
            'criteria_l1': 'Not applicable',
            'criteria_l2': 'Not provided',
            'criteria_l3': 'Not applicable',
            'cause': 'Not provided',
            'effect': 'Not provided',
            'risk_rating': 'Medium',
            'recommendation': 'Not provided',
            'evidence_source': 'N/A',
            'page': 'N/A',
            'evidence_quote': 'N/A',
            'l1_source': 'N/A',
            'l1_page': 'N/A',
            'l1_quote': 'N/A',
            'l2_source': 'N/A',
            'l2_page': 'N/A',
            'l2_quote': 'N/A',
            'l3_source': 'N/A',
            'l3_page': 'N/A',
            'l3_quote': 'N/A',
        }

        # Merge provided values with defaults
        formatted_obs = {**defaults, **observation}

        return self.template.format(**formatted_obs)

    def format_report(self, observations: list) -> str:
        """Format complete findings section from list of observations.

        Args:
            observations: List of observation dicts

        Returns:
            Formatted findings section markdown
        """
        findings_md = "## Audit Findings\n\n"
        for i, obs in enumerate(observations, 1):
            findings_md += self.format_observation({**obs, "number": i})
            findings_md += "\n\n"
        return findings_md

    def validate_observation(self, observation: dict) -> tuple[bool, list]:
        """Validate observation has required CCCE fields.

        Args:
            observation: Observation dict to validate

        Returns:
            (is_valid, list of missing fields)
        """
        required_fields = ['title', 'condition', 'criteria', 'cause', 'effect', 'risk_rating']
        missing = [f for f in required_fields if f not in observation or not observation[f]]
        return len(missing) == 0, missing
