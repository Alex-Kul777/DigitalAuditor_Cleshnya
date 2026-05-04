# DigitalAuditor Cleshnya — AI-агент аудита

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


[Полный список в CHANGELOG.md](CHANGELOG.md)

## 📁 Структура проекта

```

**core/**
- `__init__/`
- `config.py`
- `exceptions.py`
- `gigachat_client.py`
- `gigachat_validator.py`
- `llm.py`
- `logger.py`
- `logging_utils.py`
- `preferences.py`
- `token_counter.py`

**agents/**
- `__init__/`
- `base.py`
- `cisa_auditor.py`
- `preference_learner.py`
- `prompts.py`
- `reviewer_base.py`
- `revision_agent.py`
- `uncle_kahneman.py`
- `uncle_robert.py`

**knowledge/**
- `__init__/`
- `brinks_indexer.py`
- `embedder.py`
- `evidence_indexer.py`
- `fetcher.py`
- `indexer.py`
- `persona_indexer.py`
- `raw_docs.py`
- `requirements.py`
- `requirements_indexer.py`

**report_generator/**
- `__init__/`
- `assembler.py`
- `ccce_formatter.py`
- `chapters.py`
- `docx.py`
- `orchestrator.py`
- `orchestrator_ms.py`
- `templates.py`

**tools/**
- `__init__/`
- `docling_worker.py`
- `document_converter.py`
- `evidence_tracker.py`
- `file_downloader.py`
- `risk_matrix.py`
- `web_search.py`

**tasks/**
- `__init__/`
- `base_task.py`
- `instances.py`
- `ms_copilot_audit.py`

**presentation/**
- `data.py`
- `generate.py`
- `output.py`
- `slides.py`

**process_mining/**
- `__init__/`
- `process_mining_logger.py`
```

## 🧪 Покрытие тестами

- **Всего тестов:** 510+ unit + интеграционных тестов
- **Покрытие:** 54% (цель Phase 3 достигнута ✅)
- **Файлы тестов:** tests/unit/, tests/integration/, tests/smoke/

## ⚡ Быстрый старт

```bash
# Клонирование и настройка
git clone https://github.com/Alex-Kul777/DigitalAuditor_Cleshnya
cd DigitalAuditor_Cleshnya

# Создание виртуального окружения
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

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

---

**Статус:** Production-ready (v2.0.0) | Все 5 основных вех (M1-M5) завершены ✅
