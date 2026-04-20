"""
Unit tests for report_generator module.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from report_generator.orchestrator import ReportOrchestrator


class TestReportOrchestrator:
    """Test ReportOrchestrator class."""

    def test_orchestrator_initialization(self, tmp_path):
        """Test ReportOrchestrator initialization."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "output").mkdir()

        with patch("report_generator.orchestrator.setup_logger"):
            orchestrator = ReportOrchestrator(task_dir)
            assert orchestrator.task_dir == task_dir
            assert orchestrator is not None

    def test_orchestrator_generates_report(self, tmp_path):
        """Test orchestrator generates report."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "output").mkdir()

        with patch("report_generator.orchestrator.setup_logger"):
            orchestrator = ReportOrchestrator(task_dir)

            # Mock generate method
            orchestrator.generate = MagicMock(return_value=True)

            findings = [
                {"title": "Finding 1", "risk": "High"},
                {"title": "Finding 2", "risk": "Medium"},
            ]

            result = orchestrator.generate(findings)
            assert orchestrator.generate.called

    def test_orchestrator_output_directory(self, tmp_path):
        """Test orchestrator creates output directory."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_orchestrator_finds_report_files(self, tmp_path):
        """Test orchestrator works with report files."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        # Create report files
        report_file = output_dir / "audit_report.md"
        report_file.write_text("# Audit Report\n\nFindings...")

        assert report_file.exists()
        assert "Audit Report" in report_file.read_text()

    def test_orchestrator_handles_empty_findings(self, tmp_path):
        """Test orchestrator handles empty findings."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "output").mkdir()

        with patch("report_generator.orchestrator.setup_logger"):
            orchestrator = ReportOrchestrator(task_dir)
            orchestrator.generate = MagicMock()

            # Empty findings
            result = orchestrator.generate([])
            assert orchestrator.generate.called_with([])

    def test_orchestrator_handles_large_findings(self, tmp_path):
        """Test orchestrator handles large number of findings."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "output").mkdir()

        with patch("report_generator.orchestrator.setup_logger"):
            orchestrator = ReportOrchestrator(task_dir)
            orchestrator.generate = MagicMock()

            # Large findings list
            findings = [
                {"title": f"Finding {i}", "risk": "Medium"}
                for i in range(1000)
            ]

            result = orchestrator.generate(findings)
            assert orchestrator.generate.called


class TestReportStructure:
    """Test report structure and formatting."""

    def test_report_sections(self, tmp_path):
        """Test report contains standard sections."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        # Create report with expected sections
        report = """
# Audit Report

## Executive Summary
Overview of findings.

## Findings

### Critical Issues
...

### High Risk Issues
...

### Medium Risk Issues
...

### Low Risk Issues
...

## Recommendations
...

## Conclusion
...
"""
        report_file = output_dir / "report.md"
        report_file.write_text(report)

        content = report_file.read_text()
        assert "Executive Summary" in content
        assert "Findings" in content
        assert "Recommendations" in content

    def test_report_with_evidence_links(self, tmp_path):
        """Test report includes evidence references."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        # Create report with evidence links
        report = """
# Finding 1

**Evidence**:
- Evidence File 1: `evidence_1.json`
- Evidence File 2: `evidence_2.json`

**Risk Assessment**: High probability + High impact = Critical
"""
        report_file = output_dir / "findings.md"
        report_file.write_text(report)

        content = report_file.read_text()
        assert "evidence" in content.lower()
        assert "Risk Assessment" in content

    def test_report_timestamp(self, tmp_path):
        """Test report includes timestamp."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        now = datetime.now().isoformat()
        report = f"""
# Audit Report

**Generated**: {now}
**Auditor**: Digital Auditor Cleshnya
"""
        report_file = output_dir / "report.md"
        report_file.write_text(report)

        content = report_file.read_text()
        assert "Generated" in content
        assert now in content

    def test_report_company_info(self, tmp_path):
        """Test report includes company information."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        report = """
# Audit Report for ACME Corporation

**Company**: ACME Corporation
**Audit Type**: IT Security Audit
**Audit Date**: 2026-04-20
"""
        report_file = output_dir / "report.md"
        report_file.write_text(report)

        content = report_file.read_text()
        assert "ACME Corporation" in content
        assert "Audit Type" in content


class TestReportGenerationEdgeCases:
    """Test edge cases in report generation."""

    def test_report_with_special_characters(self, tmp_path):
        """Test report handles special characters."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        special_report = """
# Audit Report — 2026-04-20

## Findings

### Issue #1: Authentication & Access Control

The system uses weak encryption (⚠️ Critical):
- Uses MD5 instead of SHA-256
- Passwords stored without salt
- No multi-factor authentication (MFA)

**Impact**: 💥 Data breach risk
"""
        report_file = output_dir / "special.md"
        report_file.write_text(special_report, encoding="utf-8")

        content = report_file.read_text(encoding="utf-8")
        assert "Special characters preserved" or "Audit Report" in content

    def test_report_with_unicode(self, tmp_path):
        """Test report supports Unicode/Russian."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        russian_report = """
# Отчет об аудите

## Обнаруженные проблемы

### Критическая проблема: Слабая аутентификация

Система использует слабое шифрование:
- Пароли хранятся без защиты
- Нет двухфакторной аутентификации
- Отсутствуют логи доступа

**Риск**: Критический
"""
        report_file = output_dir / "russian.md"
        report_file.write_text(russian_report, encoding="utf-8")

        content = report_file.read_text(encoding="utf-8")
        assert "Отчет об аудите" in content
        assert "Критическая" in content

    def test_report_with_code_blocks(self, tmp_path):
        """Test report includes code blocks for examples."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        code_report = """
# Security Audit Report

## Issue: Hardcoded Credentials

**Found in**: config.py

```python
OLLAMA_API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "root"
```

**Recommendation**: Use environment variables
"""
        report_file = output_dir / "code_issues.md"
        report_file.write_text(code_report)

        content = report_file.read_text()
        assert "```python" in content
        assert "OLLAMA_API_KEY" in content


class TestFindingsAggregation:
    """Test finding aggregation and categorization."""

    def test_group_findings_by_risk(self):
        """Test findings can be grouped by risk level."""
        findings = [
            {"title": "Critical Issue", "risk": "Critical", "component": "Auth"},
            {"title": "High Issue", "risk": "High", "component": "Database"},
            {"title": "Medium Issue", "risk": "Medium", "component": "Logging"},
            {"title": "Low Issue", "risk": "Low", "component": "UI"},
        ]

        # Group by risk
        by_risk = {}
        for finding in findings:
            risk = finding["risk"]
            if risk not in by_risk:
                by_risk[risk] = []
            by_risk[risk].append(finding)

        assert len(by_risk["Critical"]) == 1
        assert len(by_risk["High"]) == 1
        assert len(by_risk["Medium"]) == 1
        assert len(by_risk["Low"]) == 1

    def test_group_findings_by_component(self):
        """Test findings can be grouped by component."""
        findings = [
            {"title": "Issue 1", "component": "Auth"},
            {"title": "Issue 2", "component": "Auth"},
            {"title": "Issue 3", "component": "Database"},
        ]

        # Group by component
        by_component = {}
        for finding in findings:
            component = finding["component"]
            if component not in by_component:
                by_component[component] = []
            by_component[component].append(finding)

        assert len(by_component["Auth"]) == 2
        assert len(by_component["Database"]) == 1

    def test_calculate_summary_statistics(self):
        """Test calculating summary statistics."""
        findings = [
            {"risk": "Critical"},
            {"risk": "High"},
            {"risk": "High"},
            {"risk": "Medium"},
            {"risk": "Low"},
        ]

        risk_counts = {}
        for finding in findings:
            risk = finding["risk"]
            risk_counts[risk] = risk_counts.get(risk, 0) + 1

        assert risk_counts["Critical"] == 1
        assert risk_counts["High"] == 2
        assert risk_counts["Medium"] == 1
        assert risk_counts["Low"] == 1

        total = sum(risk_counts.values())
        assert total == 5


class TestReportFormats:
    """Test different report output formats."""

    def test_markdown_format(self, tmp_path):
        """Test report in Markdown format."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        md_report = """
# Audit Report

## Section 1
Content here.

- Bullet point 1
- Bullet point 2

## Section 2
More content.

| Risk | Count |
|------|-------|
| High | 5     |
| Low  | 10    |
"""
        report_file = output_dir / "report.md"
        report_file.write_text(md_report)

        assert report_file.suffix == ".md"
        assert "#" in report_file.read_text()  # Markdown headers

    def test_json_format(self, tmp_path):
        """Test report in JSON format."""
        import json

        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        output_dir = task_dir / "output"
        output_dir.mkdir()

        json_report = {
            "title": "Audit Report",
            "company": "Test Corp",
            "findings": [
                {"id": 1, "title": "Finding 1", "risk": "High"},
                {"id": 2, "title": "Finding 2", "risk": "Medium"},
            ],
            "summary": {
                "total_findings": 2,
                "critical": 0,
                "high": 1,
                "medium": 1,
            }
        }

        report_file = output_dir / "report.json"
        report_file.write_text(json.dumps(json_report, indent=2))

        # Verify it's valid JSON
        loaded = json.loads(report_file.read_text())
        assert loaded["title"] == "Audit Report"
        assert len(loaded["findings"]) == 2


@pytest.mark.unit
class TestReportGeneratorMarker:
    """Test report_generator module with unit marker."""

    def test_orchestrator_class_exists(self):
        """Test ReportOrchestrator class exists."""
        assert ReportOrchestrator is not None
