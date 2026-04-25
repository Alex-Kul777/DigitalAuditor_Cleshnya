#!/usr/bin/env python3
import click
import shutil
from pathlib import Path
from datetime import datetime
import yaml

from core.validator import InputValidator
from core.exceptions import (
    AuditError,
    TaskNotFoundError,
    ConfigurationError,
    OllamaUnavailableError,
)
from core.config import OLLAMA_BASE_URL
from core.logger import setup_logger
from tools.file_downloader import download_file

logger = setup_logger("main")


@click.group()
def cli():
    """DigitalAuditor Cleshnya - ИИ-аудитор CISA/CIA"""
    pass

@cli.command()
@click.option('--name', required=True, help='Название задачи')
@click.option('--company', required=True, help='Название компании')
@click.option('--sources', multiple=True, help='Источники (файлы, URL, текстовые запросы)')
@click.option('--audit-type', default='it', help='Тип аудита')
@click.option('--reviewer', default=None, help='Рецензент для отчёта (uncle_kahneman)')
def create(name: str, company: str, sources: tuple, audit_type: str, reviewer: str):
    """Create a new audit task with optional evidence sources."""
    task_dir = Path(f"tasks/instances/{name}")
    task_dir.mkdir(parents=True, exist_ok=True)

    evidence_dir = task_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    (task_dir / "drafts").mkdir(exist_ok=True)
    (task_dir / "output").mkdir(exist_ok=True)

    # Process sources: copy files, download URLs, save text queries
    text_sources = []
    for source in sources:
        src_path = Path(source)
        if src_path.exists() and src_path.is_file():
            # Local file — copy to evidence/
            dest = evidence_dir / src_path.name
            shutil.copy2(src_path, dest)
            click.echo(f"[+] Скопирован: {src_path.name}")
        elif source.startswith(("http://", "https://")):
            # URL — download to evidence/
            try:
                dest = download_file(source, evidence_dir)
                click.echo(f"[+] Скачан: {dest.name}")
            except Exception as e:
                click.echo(f"[-] Ошибка скачивания {source}: {e}")
        else:
            # Text query — save to sources.txt
            text_sources.append(source)

    # Save text queries if any
    if text_sources:
        sources_txt = evidence_dir / "sources.txt"
        sources_txt.write_text("\n".join(text_sources), encoding="utf-8")
        click.echo(f"[+] Текстовые запросы сохранены в sources.txt")

    config = {
        "name": name,
        "company": company,
        "audit_type": audit_type,
        "sources": list(sources),
        "created": datetime.now().isoformat()
    }
    if reviewer:
        config["reviewer"] = reviewer
    (task_dir / "config.yaml").write_text(yaml.dump(config), encoding='utf-8')
    click.echo(f"[+] Задача '{name}' создана в {task_dir}")

@cli.command()
@click.option('--task', required=True, help='Название задачи')
@click.option('--auditor', default='cisa', type=click.Choice(['cisa', 'uncle_robert']),
              help='Тип аудитора (default: cisa)')
@click.option('--llm-provider', default=None, help='LLM провайдер (ollama, gigachat, anthropic, openai)')
@click.option('--llm-model', default=None, help='Модель LLM')
@click.option('--reviewer', default=None, help='Переопределить рецензента (uncle_kahneman)')
@click.option('--debug-level', type=int, default=None, help='Уровень отладки (0-3)')
def run(task: str, auditor: str, llm_provider: str, llm_model: str, reviewer: str, debug_level: int):
    """Run an audit task with validation and error handling."""
    try:
        import os

        task_dir = Path(f"tasks/instances/{task}")

        # Check if task exists
        if not task_dir.exists():
            logger.error(f"Task directory not found: {task_dir}")
            raise TaskNotFoundError(task)

        # Apply CLI overrides to environment
        if llm_provider:
            os.environ['LLM_PROVIDER'] = llm_provider
        if llm_model:
            os.environ['OLLAMA_MODEL'] = llm_model
            os.environ['GIGACHAT_MODEL'] = llm_model
        if reviewer:
            os.environ['DA_REVIEWER_OVERRIDE'] = reviewer
        if debug_level is not None:
            if debug_level == 0:
                os.environ['LOG_LEVEL'] = 'CRITICAL'
            elif debug_level == 1:
                os.environ['LOG_LEVEL'] = 'ERROR'
            elif debug_level == 2:
                os.environ['LOG_LEVEL'] = 'INFO'
            elif debug_level >= 3:
                os.environ['LOG_LEVEL'] = 'DEBUG'

        # Pre-flight checks
        logger.info("Running pre-flight checks...")

        # Check Ollama connectivity (skip for GigaChat provider)
        if not llm_provider or llm_provider.lower() != 'gigachat':
            ollama_check = InputValidator.check_ollama_connection(OLLAMA_BASE_URL)
            if not ollama_check.is_valid:
                logger.error("Ollama connectivity check failed")
                for error in ollama_check.errors:
                    logger.error(f"  [{error.error_code}] {error.message}")
                raise OllamaUnavailableError(OLLAMA_BASE_URL)
            logger.info("✓ Ollama is accessible")

        # Set auditor in task config
        import yaml
        config_path = task_dir / "config.yaml"
        if config_path.exists():
            config = yaml.safe_load(config_path.read_text(encoding='utf-8')) or {}
        else:
            config = {}
        config['auditor'] = auditor
        config_path.write_text(yaml.dump(config), encoding='utf-8')
        logger.info(f"Using auditor: {auditor}")

        # Run the audit task
        from tasks.base_task import AuditTask
        audit_task = AuditTask(task_dir)
        audit_task.execute()

        click.echo(f"[+] Аудит завершен. Отчет в {task_dir}/output/")
        logger.info(f"Task '{task}' completed successfully")

    except TaskNotFoundError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except OllamaUnavailableError as e:
        click.echo(f"[-] {str(e)}", err=True)
        click.echo("   Убедитесь, что Ollama запущен и доступен по адресу:", err=True)
        click.echo(f"   {OLLAMA_BASE_URL}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except ConfigurationError as e:
        click.echo(f"[-] Configuration error: {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except AuditError as e:
        click.echo(f"[-] Audit error: {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"[-] Unexpected error: {str(e)}", err=True)
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise SystemExit(1)

@cli.command()
def list_tasks():
    instances_dir = Path("tasks/instances")
    if instances_dir.exists():
        for d in instances_dir.iterdir():
            if d.is_dir():
                click.echo(f"  - {d.name}")

@cli.command(name='audit-ms')
def audit_ms():
    """Запустить аудит Microsoft Copilot Chat"""
    import subprocess
    import sys
    subprocess.run([sys.executable, "run_ms_audit.py"])

@cli.command(name='build-persona')
@click.argument('name')
@click.option('--corpus', help='Path to corpus directory to ingest')
def build_persona(name: str, corpus: str = None):
    """Create and scaffold a new persona.

    Args:
        name: Persona name (e.g., uncle_kahneman)
        --corpus: Optional path to document corpus to ingest
    """
    try:
        from knowledge.persona_indexer import PersonaIndexer

        persona_indexer = PersonaIndexer()

        # Scaffold persona directory structure
        logger.info(f"Scaffolding persona: {name}")
        persona_dir = persona_indexer.scaffold(name)
        click.echo(f"[+] Persona '{name}' scaffolded at: {persona_dir}")

        # Ingest corpus if provided, or auto-ingest for uncle_robert
        if corpus:
            corpus_path = Path(corpus)
            if not corpus_path.exists():
                raise FileNotFoundError(f"Corpus path not found: {corpus_path}")

            logger.info(f"Ingesting corpus from {corpus_path} for persona '{name}'")
            chunk_count = persona_indexer.ingest_corpus(name, str(corpus_path))
            click.echo(f"[+] Indexed {chunk_count} chunks for persona '{name}'")
        elif name == "uncle_robert":
            # Auto-ingest Brink's PDF for uncle_robert
            logger.info(f"Auto-ingesting Brink's corpus for persona '{name}'")
            try:
                chunk_count = persona_indexer.ingest_corpus(name)
                if chunk_count > 0:
                    click.echo(f"[+] Indexed {chunk_count} chunks for persona '{name}'")
                else:
                    click.echo(f"[!] No chunks indexed for persona '{name}' (Brink's PDF not found or empty)", err=True)
            except Exception as e:
                logger.warning(f"Auto-indexing failed for uncle_robert: {e}")
                click.echo(f"[!] Corpus ingestion optional: {str(e)}", err=True)

        # List available personas
        personas = persona_indexer.list_personas()
        click.echo(f"[+] Available personas: {', '.join(personas)}")

        logger.info(f"Persona '{name}' built successfully")

    except FileNotFoundError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"[-] Error building persona: {str(e)}", err=True)
        logger.error(f"Error building persona '{name}': {str(e)}", exc_info=True)
        raise SystemExit(1)

@cli.command(name='add-requirement')
@click.option('--level', required=True, type=click.Choice(['1', '2', '3']),
              help='1=regulatory, 2=audit standard, 3=local policy')
@click.option('--file', 'file_path', required=True, help='Path to requirement document')
@click.option('--authority', default=None, help='Authority (ISO, ISACA, FSTEC, Brink\'s, internal, user_defined)')
def add_requirement(level: str, file_path: str, authority: str):
    """Add requirement document to L1/L2/L3 library."""
    try:
        from knowledge.requirements_indexer import RequirementsIndexer

        ri = RequirementsIndexer()
        chunks = ri.add_requirement(file_path, int(level), authority)

        level_names = {
            "1": "Regulatory (L1)",
            "2": "Audit Standard (L2)",
            "3": "Local Policy (L3)"
        }

        click.echo(f"[+] Added {level_names[level]} requirement: {Path(file_path).name}")
        click.echo(f"[+] Indexed {chunks} chunks")

        # List all requirements by level
        reqs = ri.list_requirements()
        click.echo("\n[=] Requirements Library:")
        for lvl, files in reqs.items():
            file_list = ", ".join(files) if files else "(empty)"
            click.echo(f"    L{lvl}: {file_list}")

    except FileNotFoundError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except ValueError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"[-] Error adding requirement: {str(e)}", err=True)
        logger.error(f"Error adding requirement: {str(e)}", exc_info=True)
        raise SystemExit(1)

@cli.command(name='export-docx')
@click.option('--task', required=True, help='Название задачи')
def export_docx(task: str):
    """Export audit report to DOCX with reviewer comments."""
    try:
        from report_generator.docx import DocxExporter, VersionManager

        task_dir = Path(f"tasks/instances/{task}")
        if not task_dir.exists():
            raise TaskNotFoundError(task)

        # Load markdown report
        md_path = task_dir / "output" / "Audit_Report.md"
        if not md_path.exists():
            raise FileNotFoundError(f"Audit report not found: {md_path}. Run audit first.")

        # Export to DOCX
        exporter = DocxExporter()
        vm = VersionManager(task_dir)
        next_version = vm.next_version()

        docx_path = task_dir / "output" / "Audit_Report.docx"
        exporter.export(md_path, docx_path)

        # Save to version archive
        md_content = md_path.read_text(encoding='utf-8')
        vm.save(next_version, md_content, docx_path)

        click.echo(f"[+] Exported to DOCX: {docx_path}")
        click.echo(f"[+] Saved as version {next_version}")
        logger.info(f"Export complete: {docx_path}")

    except FileNotFoundError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except TaskNotFoundError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"[-] Error exporting DOCX: {str(e)}", err=True)
        logger.error(f"Error exporting DOCX: {str(e)}", exc_info=True)
        raise SystemExit(1)

@cli.command(name='revise')
@click.option('--task', required=True, help='Название задачи')
@click.option('--max-iterations', default=1, type=int, help='Max revision iterations')
def revise(task: str, max_iterations: int):
    """Apply feedback from reviewed DOCX and generate revised version."""
    try:
        from agents.revision_agent import RevisionAgent

        task_dir = Path(f"tasks/instances/{task}")
        if not task_dir.exists():
            raise TaskNotFoundError(task)

        # Load latest DOCX
        from report_generator.docx import VersionManager
        vm = VersionManager(task_dir)
        latest_docx = vm.latest()

        if not latest_docx:
            raise FileNotFoundError(f"No DOCX found for task: {task}. Run export-docx first.")

        # Revise via agent
        agent = RevisionAgent(temperature=0.3)
        revised_docx = agent.revise(task_dir)

        click.echo(f"[+] Revision applied: {revised_docx}")
        logger.info(f"Revision complete: {revised_docx}")

    except FileNotFoundError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except TaskNotFoundError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"[-] Error revising: {str(e)}", err=True)
        logger.error(f"Error revising: {str(e)}", exc_info=True)
        raise SystemExit(1)

if __name__ == "__main__":
    cli()
