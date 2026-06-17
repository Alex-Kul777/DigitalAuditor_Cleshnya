# GAP-анализ: DigitalAuditor_Cleshnya vs rag_GigaChat

**Дата:** 20.04.2026  
**Обновлено:** 20.04.2026 (уточнения после сессии Q&A)  
**Автор:** Технический архитектор (Claude Sonnet 4.6)  
**Эталонный проект:** `projects/rag_GigaChat`  
**Цель:** Roadmap развития проекта до production-ready уровня

---

## Принятые архитектурные решения

Решения приняты в ходе обсуждения и фиксируются здесь как constraints для реализации:

| # | Решение | Обоснование |
|---|---------|-------------|
| 1 | **Phase 1 начинается с тестов**, логирование — второй шаг | Тесты — страховочная сетка перед любыми изменениями кодовой базы |
| 2 | **Два слоя тестов**: unit (mock Ollama) + integration (реальный Ollama, только локально) | CI не имеет доступа к Ollama; integration тесты запускаются через `make test-integration` |
| 3 | **Полная валидация** — `ValidationResult` dataclass, error codes, warnings, batch validation | Соответствует уровню rag_GigaChat; переписывать потом дороже |
| 4 | **Coverage threshold 40%** в Phase 2, затем повышение до 54% | Реалистичная цель на старте; 54% — ориентир Phase 3 |
| 5 | **Профили конфигурации** нужны: `testing` (mock LLM для CI), `production` (реальный Ollama) | `AUDIT_PROFILE=testing` в GitHub Actions автоматически подставляет mock |
| 6 | **`setup.py` в Phase 1** вместе с тестами | Устраняет `sys.path` хаки в тестах; чистые импорты сразу |
| 7 | **Сроки абстрактные** — важен порядок задач, не даты | Темп работы непредсказуем |

---

## 1. Логирование

### Текущее состояние (DigitalAuditor)
- `core/logger.py` — 22 строки, минимальная обёртка над stdlib `logging`
- Один формат: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Один JSON-лог в `process_mining/process_mining_logger.py` (отдельный, не интегрирован в основную систему)
- Нет трейсинга `class.method`, нет stage-маркеров, нет метрик в логах
- Нет context manager'а для измерения этапов

### Целевое состояние (rag_GigaChat)
- `logging_utils.py` — 4 ключевых класса:
  - `ContextualFormatter` — формат `timestamp | LEVEL | module.Class.method | message`
  - `JSONFormatter` — структурированный JSON для process mining (с полями `stage`, `metrics`, `class`, `lineno`)
  - `DualLogHandler` — одновременно: text в консоль + JSON в файл
  - `LogContext` — context manager с `[STAGE START]` / `[STAGE END]` + `duration=Xms`
- Дополнительно: `PipelineTimer`, `MemoryTracker`, `BottleneckAnalyzer`, `MetricsExporter`
- `docs/development/LOGGING_GUIDE.md` — 442 строки документации

### Конкретный план действий

| # | Файл | Действие |
|---|------|----------|
| 1 | `core/logging_utils.py` | Создать: `ContextualFormatter`, `JSONFormatter`, `DualLogHandler`, `LogContext` |
| 2 | `core/logger.py` | Переписать — использовать `DualLogHandler` вместо ручной настройки handlers |
| 3 | `core/config.py` | Добавить `LOG_JSON_FILE = "logs/audit.json"`, `LOG_DIR` |
| 4 | `logs/` | Создать директорию + добавить в `.gitignore` |
| 5 | Все модули | Заменить `print()` на логирование; в `AuditTask.execute()` обернуть шаги в `LogContext` |
| 6 | `docs/development/LOGGING_GUIDE.md` | Создать: стандарт именования логгеров, примеры использования `LogContext` |

**Приоритет: 🔴 Critical**

---

## 2. Тестирование

### Текущее состояние (DigitalAuditor)
- `tests/test_retriever.py` — 1 тест: только `assert retriever is not None`
- `tests/test_risk_matrix.py` — 2 теста: `calculate_risk_level('High','High')` и `('Low','Low')`
- Нет `pytest.ini`, нет `conftest.py`, нет fixtures
- Нет мокирования внешних зависимостей (Ollama, ChromaDB)
- Нет категоризации тестов (unit / integration / smoke)
- Нет `Makefile`

### Целевое состояние (rag_GigaChat)
- 158+ тестов в 4 слоях: `tests/unit/`, `tests/integration/`, `tests/performance/`, `tests/debug/`
- `conftest.py` с fixtures: `mock_embeddings`, `mock_gigachat`, `sample_documents`
- `pytest.ini` с markers, coverage threshold ≥54%, `--tb=short`
- `Makefile` с 6 targets: `test`, `test-cov`, `test-unit`, `test-smoke`, `test-integration`, `clean`
- GitHub Actions автоматически запускает тесты при push/PR

### Конкретный план действий

| # | Файл | Действие |
|---|------|----------|
| 1 | `pytest.ini` | Создать: markers (unit/integration/smoke), `--cov=.` (без порога в Phase 1; порог 40% вводится в Phase 2 вместе с CI) |
| 2 | `tests/conftest.py` | Создать: `mock_ollama_llm`, `mock_chroma_db`, `sample_audit_config`, `tmp_task_dir` |
| 3 | `tests/unit/test_config.py` | Тесты: загрузка конфига, значения по умолчанию, env override |
| 4 | `tests/unit/test_logger.py` | Тесты: инициализация логгера, форматирование, JSON output |
| 5 | `tests/unit/test_validator.py` | Тесты: после создания `core/validator.py` |
| 6 | `tests/unit/test_cisa_auditor.py` | Тесты с моком LLM: `execute()`, `generate_section()` |
| 7 | `tests/unit/test_risk_matrix.py` | Перенести из root tests/, расширить coverage |
| 8 | `tests/unit/test_evidence_tracker.py` | Тесты `tools/evidence_tracker.py` |
| 9 | `tests/smoke/test_smoke.py` | Импорты всех модулей, `python main.py --help` |
| 10 | `tests/integration/test_audit_task.py` | Создание + выполнение задачи с мок-LLM |
| 11 | `Makefile` | Создать с targets: test, test-cov, test-unit, test-smoke, clean |
| 12 | `.coveragerc` | Exclude: `.venv/`, `tests/`, `setup_project.sh` |

**Приоритет: 🔴 Critical**

---

## 3. Структура проекта

### Текущее состояние (DigitalAuditor)
- Flat layout: `core/`, `agents/`, `knowledge/`, `tasks/`, `tools/`, `report_generator/` — все на корне
- Нет `setup.py` / `pyproject.toml` (пакет нельзя установить через pip)
- Нет `__main__.py` (нет `python -m digital_auditor`)
- Нет `src/` изоляции

### Целевое состояние (rag_GigaChat)
- src-layout: `src/rag_gigachat/` с суб-пакетами `core/`, `data/`, `reporting/`, `ui/`, `utils/`
- `setup.py` для `pip install -e .`
- `__main__.py` для `python -m rag_gigachat`
- `utils/` sub-package: `text_utils.py`, `debug_context.py`, `event_log.py`

### Рекомендация

Полная миграция на src-layout сейчас нецелесообразна. Проект активно разрабатывается; ломающий рефакторинг импортов затормозит delivery. Поэтапный подход:

| # | Файл | Действие |
|---|------|----------|
| 1 | `setup.py` | Создать: `pip install -e .` для корректного импорта в тестах |
| 2 | `__main__.py` | Создать: делегирует в `main.py` |
| 3 | `core/utils.py` | Создать: вынести вспомогательные функции из разных модулей |
| 4 | `src/` migration | **Phase 3 only** — отдельная задача после стабилизации API |

**Приоритет: 🟢 Low**

---

## 4. Документация

### Текущее состояние (DigitalAuditor)
- `README.md` — 2 строки ("DigitalAuditor Cleshnya - AI Audit Agent")
- `docs/GUIDE.md` — 174 строки (есть, но изолированный)
- `CLAUDE.md` — подробный (создан 20.04.2026)
- Нет `CHANGELOG.md`
- Нет `docs/development/` структуры

### Целевое состояние (rag_GigaChat)
- `README.md` — ~500 строк: архитектура, примеры, установка, конфигурация
- `README_RU.md` — аналог на русском
- `CHANGELOG.md` — полная история версий
- `docs/components/` — architecture.md, overview.md, quick-start.md
- `docs/development/` — LOGGING_GUIDE.md (442 строки), TESTING.md (261 строка), TROUBLESHOOTING.md

### Конкретный план действий

| # | Файл | Действие |
|---|------|----------|
| 1 | `README.md` | Переписать: описание, архитектурная схема, быстрый старт, конфигурация, примеры |
| 2 | `CHANGELOG.md` | Создать с v1.0 (текущий функционал) |
| 3 | `docs/development/TESTING.md` | Создать: как запускать тесты, структура, как писать моки |
| 4 | `docs/development/LOGGING_GUIDE.md` | Создать: после реализации `logging_utils.py` |
| 5 | `docs/development/TROUBLESHOOTING.md` | Создать: Ollama недоступен, ChromaDB ошибки |
| 6 | `docs/GUIDE.md` | Переместить в `docs/components/` структуру |

**Приоритет: 🟠 Medium**

---

## 5. Обработка ошибок и валидация

### Текущее состояние (DigitalAuditor)
- `tasks/base_task.py` — `execute()` без try/except; ошибка Ollama упадёт без объяснения
- `main.py` — CLI не проверяет доступность Ollama перед запуском
- Нет кастомных exceptions (`AuditError`, `TaskNotFoundError`, etc.)
- Нет предварительной проверки входных данных

### Целевое состояние (rag_GigaChat)
- `validator.py` с `InputValidator` — 7 методов валидации
- `ValidationResult` dataclass: `is_valid`, `errors: List[ValidationError]`, `warnings: List[str]`
- Кастомные error codes: `EMPTY`, `TOO_SHORT`, `NOT_FOUND`, `UNSUPPORTED_FORMAT`, `MISSING_API_KEY`
- `check_gigachat_connection()` — реальный ping API перед запуском

### Конкретный план действий

| # | Файл | Действие |
|---|------|----------|
| 1 | `core/exceptions.py` | Создать: `AuditError`, `TaskNotFoundError`, `OllamaUnavailableError`, `ValidationError`, `KnowledgeIndexError` |
| 2 | `core/validator.py` | Создать: `InputValidator` с `validate_task_config()`, `validate_evidence_file()`, `check_ollama_connection()` |
| 3 | `tasks/base_task.py` | Обернуть `execute()` в try/except; кидать `AuditError` с понятным сообщением |
| 4 | `main.py` | Добавить pre-flight check: валидировать config + ping Ollama перед `run` |
| 5 | `core/config.py` | Добавить метод `validate()` — проверять обязательные поля |

**Приоритет: 🔴 High**

---

## 6. CI/CD и автоматизация

### Текущее состояние (DigitalAuditor)
- Нет `.github/workflows/`
- Нет `Makefile`
- Нет `pytest.ini` / `.coveragerc`
- Ручной запуск всего

### Целевое состояние (rag_GigaChat)
- `.github/workflows/tests.yml`: push/PR → Python 3.12 → pip install → pytest → Codecov
- Coverage threshold: `--cov-fail-under=54`
- `Makefile`: 6 targets
- `.coveragerc`: настройка исключений

### Конкретный план действий

| # | Файл | Действие |
|---|------|----------|
| 1 | `Makefile` | Создать: `test`, `test-cov`, `test-unit`, `test-smoke`, `clean`, `setup` |
| 2 | `.github/workflows/tests.yml` | Создать: trigger push/PR main, Python 3.12, unit+smoke (без Ollama в CI) |
| 3 | `.coveragerc` | Создать: exclude `.venv/`, `tests/`, `setup_project.sh`, `process_logs/` |
| 4 | `pytest.ini` | Создать: markers, coverage, timeouts |

> **Важно:** В CI нет Ollama. Все тесты, требующие LLM, обязаны использовать mock. Integration тесты с реальным Ollama — только локально через `make test-integration`.

**Приоритет: 🟠 High**

---

## 7. Управление конфигурацией

### Текущее состояние (DigitalAuditor)
- `core/config.py` — 18 строк, простые переменные без типизации
- Нет dataclasses, нет профилей для разных сред
- `.env.example` минимальный (5 строк без комментариев)

### Целевое состояние (rag_GigaChat)
- Dataclass-based конфиг с несколькими объектами: `GigaChatConfig`, `ModelConfig`
- Профили моделей: `production`, `quality`, `testing`, `ci` — выбор через `RAG_MODEL_PROFILE`
- Singleton instances для удобного импорта
- Интеграция с `validator.py`

### Конкретный план действий

| # | Файл | Действие |
|---|------|----------|
| 1 | `core/config.py` | Рефакторинг: добавить `OllamaConfig`, `AuditConfig`, `KnowledgeConfig`, `LoggingConfig` как dataclasses |
| 2 | `core/config.py` | Добавить профили: `AUDIT_PROFILE=development/production/testing` |
| 3 | `.env.example` | Расширить: документированные поля с комментариями |

**Приоритет: 🟡 Medium**

---

# Итоговый Roadmap

## Phase 1 — Foundation (🔴 Критическое)
**Цель:** Производственная надёжность — тесты, валидация, логирование

> Порядок внутри фазы зафиксирован: сначала тесты как страховочная сетка, потом всё остальное.

| Шаг | Задача | Файлы | Зависимости |
|-----|--------|-------|-------------|
| 1 | `setup.py` — чистые импорты в тестах | `setup.py` | — |
| 2 | pytest инфраструктура | `pytest.ini`, `.coveragerc` (baseline) | setup.py |
| 3 | conftest + fixtures | `tests/conftest.py` | pytest.ini |
| 4 | Unit тесты core/ | `tests/unit/test_config.py`, `test_risk_matrix.py` | conftest |
| 5 | Makefile | `Makefile` | pytest.ini |
| 6 | Exceptions | `core/exceptions.py` | — |
| 7 | Validator (полный) | `core/validator.py` | exceptions |
| 8 | Error handling | `tasks/base_task.py`, `main.py` | validator, exceptions |
| 9 | Unit тест валидатора | `tests/unit/test_validator.py` | validator |
| 10 | Logging v2 | `core/logging_utils.py`, `core/logger.py` | — |
| 11 | Unit тест логгера | `tests/unit/test_logger.py` | logging_utils |
| 12 | Smoke тесты | `tests/smoke/test_smoke.py` | все выше |

**Критерий готовности:** `make test` проходит; `python main.py run --task X` с недоступным Ollama выдаёт понятную ошибку вместо traceback.

---

## Phase 2 — Quality (🟠 Высокий)
**Цель:** Автоматизация, расширенное покрытие тестами, типизированный конфиг

| Шаг | Задача | Файлы | Зависимости |
|-----|--------|-------|-------------|
| 1 | Config v2 с профилями | `core/config.py` — dataclasses + `testing`/`production` профили | Phase 1 |
| 2 | mock_ollama fixture | `tests/conftest.py` — добавить `mock_ollama_llm` | config v2 |
| 3 | Unit тесты agents/ | `tests/unit/test_cisa_auditor.py`, `test_agent_base.py` | mock_ollama |
| 4 | Unit тесты tools/ | `tests/unit/test_evidence_tracker.py` | conftest |
| 5 | Integration тесты | `tests/integration/test_audit_task.py` | mock_ollama, validator |
| 6 | CI/CD | `.github/workflows/tests.yml` (`AUDIT_PROFILE=testing`), `.coveragerc` (≥40%) | Phase 1 тесты |
| 7 | README | `README.md` полный | — |
| 8 | CHANGELOG | `CHANGELOG.md` с v1.0 | — |

> **CI запускает:** unit + smoke тесты с `AUDIT_PROFILE=testing`.  
> **Локально:** `make test-integration` запускает integration тесты с реальным Ollama.

**Критерий готовности:** CI зелёный на GitHub; coverage ≥40%; README понятен без контекста.

---

## Phase 3 — Polish (🟡 Medium/Low)
**Цель:** Профессиональный уровень документации; coverage до 54%; src-layout опционально

| Шаг | Задача | Файлы | Зависимости |
|-----|--------|-------|-------------|
| 1 | LOGGING_GUIDE | `docs/development/LOGGING_GUIDE.md` | logging_utils (Phase 1) |
| 2 | TESTING guide | `docs/development/TESTING.md` | Phase 2 тесты |
| 3 | TROUBLESHOOTING | `docs/development/TROUBLESHOOTING.md` | — |
| 4 | Coverage до 54% | Расширить тесты knowledge/, report_generator/ | Phase 2 |
| 5 | src-layout (optional) | `src/digital_auditor/` — только если нужна публикация как пакета | Всё Phase 1+2 |

**Критерий готовности:** Новый разработчик за 30 минут устанавливает проект, запускает тесты и понимает архитектуру.

---

## Сводная таблица

| Категория | Текущий уровень | Целевой уровень | Приоритет | Phase |
|-----------|----------------|----------------|-----------|-------|
| Тестирование | 3 теста | 50+ тестов, coverage ≥40% → 54% | 🔴 Critical | 1 → 2 → 3 |
| Логирование | 22 строки | ContextualFormatter + JSON + LogContext | 🔴 Critical | 1 |
| Валидация / Ошибки | Отсутствует | Полный InputValidator + exceptions | 🔴 High | 1 |
| Структура (setup.py) | Нет pip-пакета | `setup.py` + `pip install -e .` | 🔴 High | 1 |
| CI/CD | Отсутствует | GitHub Actions (`AUDIT_PROFILE=testing`) + Makefile | 🟠 High | 2 |
| Конфигурация | Простые переменные | Dataclasses + профили `testing`/`production` | 🟠 Medium | 2 |
| Документация | 2 строки README | Полный README + docs/development/ | 🟠 Medium | 2 + 3 |
| src-layout | Flat layout | Опционально, только при публикации как пакета | 🟢 Low | 3 |
