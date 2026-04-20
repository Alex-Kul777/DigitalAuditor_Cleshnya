#!/usr/bin/env python3
import click
from pathlib import Path
from datetime import datetime
import yaml

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
    task_dir = Path(f"tasks/instances/{task}")
    if not task_dir.exists():
        click.echo(f"[-] Задача '{task}' не найдена")
        return
    from tasks.base_task import AuditTask
    audit_task = AuditTask(task_dir)
    audit_task.execute()
    click.echo(f"[+] Аудит завершен. Отчет в {task_dir}/output/")

@cli.command()
def list_tasks():
    instances_dir = Path("tasks/instances")
    if instances_dir.exists():
        for d in instances_dir.iterdir():
            if d.is_dir():
                click.echo(f"  - {d.name}")

if __name__ == "__main__":
    cli()

@cli.command()
@click.option('--task', default='ms_copilot_audit', help='Название задачи')
def audit_ms(task: str):
    """Запустить специализированный аудит Microsoft Copilot Chat"""
    import subprocess
    subprocess.run([sys.executable, "run_ms_audit.py"])
