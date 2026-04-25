#!/usr/bin/env python3
"""
README Auto-Generation Script

Generates README.md and README_RU.md by syncing:
- Features list from CHANGELOG.md
- Latest Release section from CHANGELOG.md
- Project structure from actual directories
- Test counts from pytest --collect-only

Usage:
    python generate_readme.py --check     # Check if README is stale (exit 1 if mismatch)
    python generate_readme.py --update    # Update README.md and README_RU.md in-place
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ChangelogParser:
    """Parse Keep a Changelog format."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.content = Path(filepath).read_text(encoding='utf-8')

    def get_latest_release(self) -> Optional[str]:
        """Extract the latest release version section (first version, not Unreleased)."""
        # Pattern: ## [version] - date
        pattern = r'## \[([\d.]+)\][^\n]*\n(.*?)(?=## \[|$)'
        matches = re.finditer(pattern, self.content, re.DOTALL)

        for match in matches:
            version, section = match.groups()
            if version != 'Unreleased':
                return f"## [{version}]\n{section[:500]}..."  # Return first 500 chars
        return None

    def extract_features(self) -> List[str]:
        """Extract Added/Changed sections from latest release."""
        pattern = r'## \[([\d.]+)\][^\n]*\n(.*?)(?=## \[|$)'
        matches = list(re.finditer(pattern, self.content, re.DOTALL))

        features = []
        for match in matches:
            version, section = match.groups()
            if version == 'Unreleased':
                continue

            # Extract Added section
            added_match = re.search(r'### Added\n(.*?)(?=###|$)', section, re.DOTALL)
            if added_match:
                added_text = added_match.group(1)
                # Extract bullet points
                bullets = re.findall(r'^- (.+)$', added_text, re.MULTILINE)
                features.extend(bullets[:15])  # Limit to 15 features

            if features:
                break  # Only use latest version

        return features


class ProjectStructureScanner:
    """Scan project directories for structure."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def scan_dirs(self, dirs: List[str]) -> Dict[str, List[str]]:
        """Scan specified directories and list modules."""
        result = {}
        for dir_name in dirs:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                continue

            modules = []
            for item in dir_path.iterdir():
                if item.is_file() and item.suffix == '.py':
                    modules.append(item.stem)
                elif item.is_dir() and not item.name.startswith('_'):
                    modules.append(item.name)

            if modules:
                result[dir_name] = sorted(modules)

        return result

    def get_structure_markdown(self) -> str:
        """Generate markdown for project structure."""
        dirs = ['core', 'agents', 'knowledge', 'report_generator', 'tools', 'tasks', 'presentation', 'process_mining']
        structure = self.scan_dirs(dirs)

        lines = []
        for dir_name, modules in structure.items():
            lines.append(f"\n**{dir_name}/**")
            for module in modules[:10]:  # Limit to 10 per dir
                lines.append(f"- `{module}.py`" if not module.startswith('_') else f"- `{module}/`")

        return '\n'.join(lines) if lines else "*(Project structure scanning)*"


class TestCounter:
    """Count tests using pytest."""

    @staticmethod
    def count_tests() -> int:
        """Run pytest --collect-only and count tests."""
        try:
            result = subprocess.run(
                ['pytest', '--collect-only', '-q'],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).parent.parent.parent
            )

            # Parse output: "300 tests collected in X.XXs"
            match = re.search(r'(\d+) test', result.stdout)
            if match:
                return int(match.group(1))
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return 0


class Translator:
    """Simple auto-translator for common sections."""

    # Manual mappings for critical sections
    TRANSLATIONS = {
        "Features": "Функции",
        "Project Structure": "Структура проекта",
        "Test Coverage": "Покрытие тестами",
        "Quick Start": "Быстрый старт",
        "Installation": "Установка",
        "Usage": "Использование",
        "Configuration": "Конфигурация",
        "Running Tests": "Запуск тестов",
        "Documentation": "Документация",
        "License": "Лицензия",
        "Contact": "Контакты",
    }

    @staticmethod
    def translate_header(text: str) -> str:
        """Translate markdown headers."""
        for en, ru in Translator.TRANSLATIONS.items():
            text = text.replace(f"## {en}", f"## {ru}")
            text = text.replace(f"### {en}", f"### {ru}")
        return text

    @staticmethod
    def translate_bullet_list(bullets: List[str]) -> List[str]:
        """Simple approach: keep bullets as-is for auto-gen sections."""
        return bullets


class ReadmeGenerator:
    """Generate README from components."""

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.changelog = ChangelogParser(self.root_dir / 'CHANGELOG.md')
        self.scanner = ProjectStructureScanner(self.root_dir)
        self.test_count = TestCounter.count_tests()

    def generate_readme_en(self) -> str:
        """Generate English README.md."""
        features = self.changelog.extract_features()
        structure = self.scanner.get_structure_markdown()

        features_list = '\n'.join([f"- {f[:80]}" for f in features[:10]])

        readme = f"""# DigitalAuditor Cleshnya — AI Audit Agent

🇷🇺 [Русская версия](README_RU.md)

## 📋 Overview

AI-powered audit system for IT compliance audits following CISA (Certified Information Systems Auditor) and CIA (Certified Internal Auditor) standards.

**Key Features:**
- RAG on ChromaDB + FAISS for semantic document retrieval
- Multiple LLM support: GigaChat, Claude, OpenAI, Ollama (local)
- Multi-persona audit framework (CisaAuditor, uncle_Robert, uncle_Kahneman)
- DOCX export/import with Track Changes revision cycle
- Evidence traceability with 3-level requirements hierarchy
- User preference learning from revision feedback

## ✨ What's New (Latest Release)

{self.changelog.get_latest_release() or "See CHANGELOG.md for details"}

## 🚀 Features

Auto-generated from CHANGELOG:
{features_list}

[See CHANGELOG.md for complete list](CHANGELOG.md)

## 📁 Project Structure

```
{structure}
```

## 🧪 Test Coverage

- **Total Tests:** {self.test_count}+ unit + integration tests
- **Coverage:** 54% (Phase 3 target achieved ✅)
- **Test Files:** tests/unit/, tests/integration/, tests/smoke/

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/Alex-Kul777/DigitalAuditor_Cleshnya
cd DigitalAuditor_Cleshnya

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set:
# - OLLAMA_BASE_URL (default: http://localhost:11434)
# - OLLAMA_MODEL (default: digital-auditor-cisa)

# Ensure Ollama is running
# then create and run an audit task
python main.py create --name demo_audit --company DemoCompany --audit-type it
python main.py run --task demo_audit
```

## 🛠️ Installation

**Requirements:** Python 3.10+, Ollama (local)

[See docs/development/TROUBLESHOOTING.md for detailed setup](docs/development/TROUBLESHOOTING.md)

## 🚦 Usage

```bash
# Create audit task
python main.py create --name <task_name> --company <company> --audit-type <type>

# Run audit
python main.py run --task <task_name>

# List tasks
python main.py list-tasks

# Build auditor persona
python main.py build-persona <persona_name>

# Export to DOCX
python main.py export-docx --task <task_name>

# Revise report
python main.py revise --task <task_name> --feedback <feedback_file>

# Add requirements
python main.py add-requirement --level L1 --title "Requirement" --description "..."
```

## 🔧 Configuration

**Environment Variables** (see `.env.example`):
- `OLLAMA_BASE_URL` — Local Ollama endpoint
- `OLLAMA_MODEL` — Model name (default: digital-auditor-cisa)
- `CHROMA_DB_PATH` — Vector store location
- `TAVILY_API_KEY` — Web search API key (optional)
- `LOG_LEVEL` — Logging verbosity (INFO, DEBUG, WARNING, ERROR)

## 🧪 Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_agents.py

# With coverage
pytest --cov=src --cov-report=html

# Verbose output
pytest -v
```

## 📚 Documentation

- [Development Guide](docs/development/LOGGING_GUIDE.md) — Logging patterns, pipeline tracing
- [Testing Guide](docs/development/TESTING.md) — Test writing, fixtures, CI/CD
- [Troubleshooting](docs/development/TROUBLESHOOTING.md) — Common issues and solutions
- [ROADMAP](ROADMAP.md) — Milestones M1-M5, completed features
- [CHANGELOG](CHANGELOG.md) — Version history and release notes
- [Architecture](docs/GAP_ANALYSIS.md) — System design decisions

## 📄 License

MIT License — See LICENSE file

## 📧 Contact

- **Author:** Alexey K.
- **Telegram:** [@auditor2it](https://t.me/auditor2it)
- **Email:** dudered1917@gmail.com

---

**Status:** Production-ready (v2.0.0) | All 5 core milestones (M1-M5) complete ✅
"""

        return readme

    def generate_readme_ru(self) -> str:
        """Generate Russian README_RU.md (auto-translate sections, manual narrative)."""
        features = self.changelog.extract_features()
        structure = self.scanner.get_structure_markdown()

        features_list = '\n'.join([f"- {f[:80]}" for f in features[:10]])

        readme_ru = f"""# DigitalAuditor Cleshnya — AI-агент аудита

🇬🇧 [English version](README.md)

## 📋 Описание

AI-система для ИТ-аудитов и проверок соответствия стандартам CISA (Certified Information Systems Auditor) и CIA (Certified Internal Auditor).

**Ключевые возможности:**
- RAG на ChromaDB + FAISS для семантического поиска документов
- Поддержка нескольких LLM: GigaChat, Claude, OpenAI, Ollama (локально)
- Многоперсональный фреймворк аудита (CisaAuditor, uncle_Robert, uncle_Kahneman)
- Экспорт/импорт в DOCX с отслеживанием изменений (Track Changes)
- Прослеживаемость свидетельств с 3-уровневой иерархией требований
- Обучение предпочтениям пользователя из отзывов на изменения

## ✨ Что нового (последний релиз)

См. CHANGELOG.md для деталей

## 🚀 Функции

Автоматически созданный список из CHANGELOG:
{features_list}

[Полный список в CHANGELOG.md](CHANGELOG.md)

## 📁 Структура проекта

```
{structure}
```

## 🧪 Покрытие тестами

- **Всего тестов:** {self.test_count}+ unit + интеграционных тестов
- **Покрытие:** 54% (цель Phase 3 достигнута ✅)
- **Файлы тестов:** tests/unit/, tests/integration/, tests/smoke/

## ⚡ Быстрый старт

```bash
# Клонирование и настройка
git clone https://github.com/Alex-Kul777/DigitalAuditor_Cleshnya
cd DigitalAuditor_Cleshnya

# Создание виртуального окружения
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Установка зависимостей
pip install -r requirements.txt

# Конфигурация
cp .env.example .env
# Отредактировать .env:
# - OLLAMA_BASE_URL (по умолчанию: http://localhost:11434)
# - OLLAMA_MODEL (по умолчанию: digital-auditor-cisa)

# Убедитесь, что Ollama запущен
python main.py create --name demo_audit --company DemoCompany --audit-type it
python main.py run --task demo_audit
```

## 🛠️ Установка

**Требования:** Python 3.10+, Ollama (локально)

[Подробная инструкция в docs/development/TROUBLESHOOTING.md](docs/development/TROUBLESHOOTING.md)

## 🚦 Использование

```bash
# Создать задачу аудита
python main.py create --name <task_name> --company <company> --audit-type <type>

# Запустить аудит
python main.py run --task <task_name>

# Список задач
python main.py list-tasks

# Построить персону аудитора
python main.py build-persona <persona_name>

# Экспортировать в DOCX
python main.py export-docx --task <task_name>

# Пересмотреть отчет
python main.py revise --task <task_name> --feedback <feedback_file>

# Добавить требование
python main.py add-requirement --level L1 --title "Требование" --description "..."
```

## 🔧 Конфигурация

**Переменные окружения** (см. `.env.example`):
- `OLLAMA_BASE_URL` — Локальная конечная точка Ollama
- `OLLAMA_MODEL` — Название модели (по умолчанию: digital-auditor-cisa)
- `CHROMA_DB_PATH` — Расположение хранилища векторов
- `TAVILY_API_KEY` — Ключ API для поиска в сети (опционально)
- `LOG_LEVEL` — Уровень логирования (INFO, DEBUG, WARNING, ERROR)

## 🧪 Запуск тестов

```bash
# Все тесты
pytest

# Конкретный файл теста
pytest tests/unit/test_agents.py

# С покрытием
pytest --cov=src --cov-report=html

# Подробный вывод
pytest -v
```

## 📚 Документация

- [Руководство разработки](docs/development/LOGGING_GUIDE.md) — Логирование, трассировка
- [Руководство тестирования](docs/development/TESTING.md) — Написание тестов, фиксчуры
- [Решение проблем](docs/development/TROUBLESHOOTING.md) — Часто встречающиеся проблемы
- [ROADMAP](ROADMAP.md) — Вехи M1-M5, завершенные функции
- [CHANGELOG](CHANGELOG.md) — История версий
- [Архитектура](docs/GAP_ANALYSIS.md) — Решения проектирования системы

## 📄 Лицензия

MIT License — См. файл LICENSE

## 📧 Контакты

- **Автор:** Alexey K.
- **Telegram:** [@auditor2it](https://t.me/auditor2it)
- **Email:** dudered1917@gmail.com

---

**Статус:** Production-ready (v2.0.0) | Все 5 основных вех (M1-M5) завершены ✅
"""

        return readme_ru

    def write_readmes(self) -> None:
        """Write generated READMEs to disk."""
        readme_en = self.generate_readme_en()
        readme_ru = self.generate_readme_ru()

        (self.root_dir / 'README.md').write_text(readme_en, encoding='utf-8')
        (self.root_dir / 'README_RU.md').write_text(readme_ru, encoding='utf-8')

    def check_readmes(self) -> bool:
        """Check if current READMEs match generated versions."""
        current_en = (self.root_dir / 'README.md').read_text(encoding='utf-8') if (self.root_dir / 'README.md').exists() else ""
        current_ru = (self.root_dir / 'README_RU.md').read_text(encoding='utf-8') if (self.root_dir / 'README_RU.md').exists() else ""

        generated_en = self.generate_readme_en()
        generated_ru = self.generate_readme_ru()

        return current_en == generated_en and current_ru == generated_ru


def main():
    parser = argparse.ArgumentParser(description='Auto-generate README.md and README_RU.md')
    parser.add_argument('--check', action='store_true', help='Check if README is stale (exit 1 if mismatch)')
    parser.add_argument('--update', action='store_true', help='Update README.md and README_RU.md in-place')

    args = parser.parse_args()

    if not args.check and not args.update:
        parser.print_help()
        sys.exit(1)

    # Determine root directory (3 levels up from script)
    root_dir = Path(__file__).parent.parent.parent

    generator = ReadmeGenerator(str(root_dir))

    if args.check:
        if generator.check_readmes():
            print("✅ README.md and README_RU.md are up-to-date")
            sys.exit(0)
        else:
            print("❌ README.md or README_RU.md is out-of-date. Run with --update to fix.")
            sys.exit(1)

    elif args.update:
        generator.write_readmes()
        print("✅ Updated README.md and README_RU.md")
        sys.exit(0)


if __name__ == '__main__':
    main()
