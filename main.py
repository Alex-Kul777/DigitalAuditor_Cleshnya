#!/usr/bin/env python3
import click
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

logger = setup_logger("main")


@click.group()
def cli():
    """DigitalAuditor Cleshnya - ИИ-аудитор CISA/CIA"""
    pass

@cli.command()
@click.option('--name', required=True, help='Название задачи')
@click.option('--company', required=True, help='Название компании')
@click.option('--sources', multiple=True, help='Источники')
@click.option('--audit-type', default='it', help='Тип аудита')
def create(name: str, company: str, sources: tuple, audit_type: str):
    task_dir = Path(f"tasks/instances/{name}")
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "evidence").mkdir(exist_ok=True)
    (task_dir / "drafts").mkdir(exist_ok=True)
    (task_dir / "output").mkdir(exist_ok=True)
    (task_dir / "evidence/.gitkeep").touch()
    
    config = {
        "name": name,
        "company": company,
        "audit_type": audit_type,
        "sources": list(sources),
        "created": datetime.now().isoformat()
    }
    (task_dir / "config.yaml").write_text(yaml.dump(config), encoding='utf-8')
    click.echo(f"[+] Задача '{name}' создана в {task_dir}")

@cli.command()
@click.option('--task', required=True, help='Название задачи')
def run(task: str):
    """Run an audit task with validation and error handling."""
    try:
        task_dir = Path(f"tasks/instances/{task}")

        # Check if task exists
        if not task_dir.exists():
            logger.error(f"Task directory not found: {task_dir}")
            raise TaskNotFoundError(task)

        # Pre-flight checks
        logger.info("Running pre-flight checks...")

        # Check Ollama connectivity
        ollama_check = InputValidator.check_ollama_connection(OLLAMA_BASE_URL)
        if not ollama_check.is_valid:
            logger.error("Ollama connectivity check failed")
            for error in ollama_check.errors:
                logger.error(f"  [{error.error_code}] {error.message}")
            raise OllamaUnavailableError(OLLAMA_BASE_URL)

        logger.info("✓ Ollama is accessible")

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

if __name__ == "__main__":
    cli()
