#!/usr/bin/env python3
#  python main.py run --task gogol_audit --llm-provider gigachat --llm-model GigaChat-2-Max --debug-level 3
# python test_giga.py    // test gigachat alive
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
@click.option('--log-level', default='INFO', type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG-1', 'DEBUG-2', 'DEBUG-3']),
              help='Уровень детализации логирования (default: INFO)')
def run(task: str, auditor: str, llm_provider: str, llm_model: str, reviewer: str, debug_level: int, log_level: str):
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

        # Set unified logger level
        from core.unified_logger import set_log_level
        set_log_level(log_level)

        # Pre-flight checks
        import uuid
        context_id = str(uuid.uuid4())[:8]
        logger.structured_log(
            "pre_flight", "checks_started",
            {"context_id": context_id},
            level="INFO"
        )

        # Check GigaChat availability first (if not explicitly requesting Ollama)
        if not llm_provider or llm_provider.lower() != 'ollama':
            from core.gigachat_validator import GigaChatValidator
            giga_validator = GigaChatValidator(context_id=context_id)
            giga_available = giga_validator.is_available(reason="pre_flight", context_id=context_id)

        # Check Ollama connectivity (skip for GigaChat provider)
        if not llm_provider or llm_provider.lower() != 'gigachat':
            ollama_check = InputValidator.check_ollama_connection(OLLAMA_BASE_URL)
            if not ollama_check.is_valid:
                logger.error("Ollama connectivity check failed")
                for error in ollama_check.errors:
                    logger.error(f"  [{error.error_code}] {error.message}")
                raise OllamaUnavailableError(OLLAMA_BASE_URL)
            logger.structured_log(
                "pre_flight", "ollama_available",
                {"context_id": context_id, "base_url": OLLAMA_BASE_URL},
                level="INFO"
            )

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

        # Log provider selection before running audit
        from core.llm import LLMFactory
        provider = os.getenv("LLM_PROVIDER", "hybrid").lower()
        if provider == "hybrid":
            from core.gigachat_validator import GigaChatValidator
            giga_validator = GigaChatValidator(context_id=context_id)
            if giga_validator.is_available(reason="pre_audit_check", context_id=context_id):
                selected_provider = "gigachat"
                fallback_reason = None
            else:
                selected_provider = "ollama"
                fallback_reason = "gigachat_unavailable"
        else:
            selected_provider = provider
            fallback_reason = None

        logger.structured_log(
            "pre_flight", "provider_selected",
            {
                "context_id": context_id,
                "provider": selected_provider,
                "fallback_reason": fallback_reason,
                "model": os.getenv("GIGACHAT_MODEL" if selected_provider == "gigachat" else "OLLAMA_MODEL", "default")
            },
            level="INFO"
        )
        click.echo(f"[=] Using LLM provider: {selected_provider}")
        if fallback_reason:
            click.echo(f"[=] (fallback reason: {fallback_reason})")

        # Run the audit task
        from tasks.base_task import AuditTask
        audit_task = AuditTask(task_dir)
        audit_task.execute()

        click.echo(f"[+] Аудит завершен. Отчет в {task_dir}/output/")
        logger.structured_log(
            "audit", "completed",
            {
                "context_id": context_id,
                "task": task,
                "provider": selected_provider
            },
            level="INFO"
        )

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

        # Load markdown report — discover any Audit_Report*.md (handles uncle_robert and other personas)
        output_dir = task_dir / "output"
        md_candidates = sorted(output_dir.glob("Audit_Report*.md"))
        if not md_candidates:
            raise FileNotFoundError(f"No Audit_Report*.md found in {output_dir}. Run audit first.")
        md_path = md_candidates[-1]  # Take latest alphabetically (uncle_robert sorts after plain)

        # Export to DOCX
        exporter = DocxExporter()
        vm = VersionManager(task_dir)
        next_version = vm.next_version()

        docx_path = task_dir / "output" / (md_path.stem + ".docx")
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

@cli.command(name='convert')
@click.option('--input', 'input_path', required=True, type=click.Path(exists=True),
              help='Path to input PDF file')
@click.option('--translate', is_flag=True, default=False,
              help='Translate PDF to target language')
@click.option('--lang', default='ru', show_default=True,
              help='Target language code for translation')
@click.option('--markdown', 'to_markdown', is_flag=True, default=False,
              help='Convert PDF(s) to Markdown')
@click.option('--chunk-size', 'chunk_size', default=None, type=int,
              help='Pages per translation batch for large PDFs')
@click.option('--pages', 'pages_str', default=None,
              help='Page range for markdown conversion (e.g. 1-20)')
def convert(input_path: str, translate: bool, lang: str, to_markdown: bool, chunk_size: int | None, pages_str: str | None):
    """Translate PDF and/or convert to Markdown.

    Examples:
        # Translate only
        python main.py convert --input input.pdf --translate --lang ru

        # Convert to Markdown only
        python main.py convert --input input.pdf --markdown

        # Both operations
        python main.py convert --input input.pdf --translate --lang ru --markdown
    """
    try:
        from tools.document_converter import translate_pdf, convert_pdf_to_markdown
        from pathlib import Path

        if not translate and not to_markdown:
            click.echo("Error: specify at least --translate or --markdown", err=True)
            raise SystemExit(1)

        input_path = Path(input_path)

        # Parse page range if provided
        page_range = None
        if pages_str:
            try:
                parts = pages_str.split("-")
                if len(parts) != 2:
                    raise ValueError("Invalid format, use: 1-20")
                start, end = int(parts[0]), int(parts[1])
                if start < 1 or end < start:
                    raise ValueError("Start must be >= 1 and <= end")
                page_range = (start, end)
            except ValueError as e:
                click.echo(f"Error: invalid --pages format: {e}", err=True)
                raise SystemExit(1)

        # Step 1: Translate if requested
        translated_path = None
        if translate:
            translated_path = translate_pdf(input_path, lang=lang, chunk_size=chunk_size)
            click.echo(f"[+] Translated: {translated_path}")

        # Step 2: Convert original to Markdown if requested
        if to_markdown:
            md_path = convert_pdf_to_markdown(input_path, page_range=page_range)
            click.echo(f"[+] Markdown: {md_path}")

            # Step 3: Convert translated to Markdown if translation exists
            if translated_path:
                md_translated = convert_pdf_to_markdown(translated_path, page_range=page_range)
                click.echo(f"[+] Markdown (translated): {md_translated}")

    except FileNotFoundError as e:
        click.echo(f"[-] {str(e)}", err=True)
        logger.error(str(e))
        raise SystemExit(1)
    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"[-] Error converting document: {str(e)}", err=True)
        logger.error(f"Error converting document: {str(e)}", exc_info=True)
        raise SystemExit(1)

if __name__ == "__main__":
    cli()
