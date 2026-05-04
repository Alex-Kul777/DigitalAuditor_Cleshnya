import pytest
import re
from unittest.mock import MagicMock, patch


class TestValidateCitations:
    """Test citation validation logic."""

    def test_validate_citations_with_evidence_tables(self):
        """Verify citations regex matches evidence tables."""
        findings = """
### Наблюдение 1: Test

**Источники:**
| Тип | Документ | Стр. | Цитата |
|-----|----------|------|--------|
| Evidence | file.txt | 1 | "quote" |

### Наблюдение 2: Test 2

**Источники:**
| Evidence | file.txt | 2 | "quote2" |
"""
        findings_count = findings.count("### Наблюдение")
        citations_count = len(re.findall(r"\| Evidence \|", findings))

        assert findings_count == 2
        assert citations_count == 2
        assert citations_count / findings_count >= 0.8

    def test_validate_citations_partial(self):
        """Verify partial citation detection."""
        findings = """
### Наблюдение 1
| Evidence | file | 1 | "q" |

### Наблюдение 2
No citation

### Наблюдение 3
| Evidence | file | 2 | "q2" |

### Наблюдение 4
No citation
"""
        findings_count = findings.count("### Наблюдение")
        citations_count = len(re.findall(r"\| Evidence \|", findings))

        ratio = citations_count / findings_count if findings_count > 0 else 1
        assert findings_count == 4
        assert citations_count == 2
        assert ratio == 0.5
        assert ratio < 0.8  # Below 80% threshold, should fail validation

    def test_validate_citations_no_findings(self):
        """Verify validation passes with no findings."""
        text = "No findings."
        findings_count = text.count("### Наблюдение")
        assert findings_count == 0


class TestBuildFindingsPrompt:
    """Test prompt building with context."""

    def test_prompt_structure(self):
        """Verify prompt includes required sections."""
        prompt = """
КОНТЕКСТ ИЗ ИСТОЧНИКА (Evidence):
Test evidence context

ПРИМЕНИМЫЕ ТРЕБОВАНИЯ (L1/L2/L3):
Test criteria context

**Источники:**
| Тип | Документ | Стр. | Цитата |
| Evidence | file | 1 | "q" |
"""
        assert "КОНТЕКСТ ИЗ ИСТОЧНИКА" in prompt
        assert "ПРИМЕНИМЫЕ ТРЕБОВАНИЯ" in prompt
        assert "| Evidence |" in prompt
        assert "Источники:" in prompt

    def test_prompt_includes_ccce_format(self):
        """Verify prompt instructs CCCE format."""
        prompt = """
### Наблюдение [номер]: [заголовок]

**Состояние (Condition):** [текст]
**Критерий (Criteria):** [текст]
**Причина (Cause):** [текст]
**Последствия (Impact):** [текст]
"""
        assert "Condition" in prompt
        assert "Criteria" in prompt
        assert "Cause" in prompt
        assert "Impact" in prompt


@patch('report_generator.orchestrator.Retriever')
@patch('report_generator.orchestrator.CisaAuditor')
class TestOrchestratorIntegration:
    """Test orchestrator method calls."""

    def test_orchestrator_methods_exist(self, mock_auditor, mock_retriever):
        """Verify orchestrator has required methods."""
        from report_generator.orchestrator import ReportOrchestrator

        assert hasattr(ReportOrchestrator, '_build_findings_prompt')
        assert hasattr(ReportOrchestrator, '_validate_citations')
        assert hasattr(ReportOrchestrator, '_get_criteria_context')
        assert hasattr(ReportOrchestrator, '_get_context')

    def test_validate_citations_method(self, mock_auditor, mock_retriever):
        """Test _validate_citations method logic."""
        from report_generator.orchestrator import ReportOrchestrator
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            (task_dir / 'output').mkdir(parents=True, exist_ok=True)
            (task_dir / 'config.yaml').write_text('name: test\ncompany: Test\n')

            orch = ReportOrchestrator(task_dir)

            # Test with citations
            text_with = "### Наблюдение 1\n| Evidence | f | 1 | q |\n### Наблюдение 2\n| Evidence | f | 2 | q |"
            assert orch._validate_citations(text_with) is True

            # Test without citations
            text_without = "### Наблюдение 1\nNo table\n### Наблюдение 2\nNo table"
            assert orch._validate_citations(text_without) is False

            # Test empty
            assert orch._validate_citations("No findings") is True
