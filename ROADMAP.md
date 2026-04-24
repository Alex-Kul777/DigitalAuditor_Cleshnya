# Roadmap — DigitalAuditor Cleshnya

> Current sprint tracked in [.omc/notepad.md](.omc/notepad.md) (auto-loaded each session).

## Current Focus
**M_Evidence — Evidence Traceability & Requirements Hierarchy** OR **M_Robert — uncle_Robert Primary Auditor** — both planned (parallel, next after M1)

## Milestones

### M1 — Persona Infrastructure 🔴

**Why M1?**

Currently all knowledge lives in one ChromaDB: audit documents, evidence, etc. When we add reviewer-personas (e.g., Uncle Kahneman), their corpus also goes into ChromaDB. Problem: **CisaAuditor retrieves persona-knowledge by accident**, contaminating audit findings with reviewer's cognitive biases.

Solution: Metadata-based filtering. Index all documents together (efficient), but:
- CisaAuditor calls `retrieve(query, exclude_personas=["uncle_kahneman", ...])` → audit-docs only
- UncleKahneman calls `retrieve(query, filter={"persona":"uncle_kahneman"})` → own corpus only
- Audit trail stays clean; reviewer comments are separate document

Result: Multi-persona framework without mixing concerns. Scale from one auditor to N reviewers.

**Tasks:**
- [x] `knowledge/retriever.py` — `filter` + `exclude_personas` post-filter
- [x] `knowledge/indexer.py` — `index_documents(docs: list[Document])`
- [x] `knowledge/persona_indexer.py` (NEW) — CLI фасад, `scaffold()`, `ingest_corpus()`
- [x] `knowledge/persona_registry.py` (NEW) — `list_personas()`
- [x] `personas/_templates/` + `personas/uncle_kahneman/` — scaffolding + 9 tests (Task 5 DONE)
- [x] `report_generator/orchestrator.py:28` — `exclude_personas` в `_get_context` + 6 tests (Task 6 DONE)
- [x] `main.py` — команда `build-persona` + 5 tests (Task 7 DONE)
- [x] `tests/knowledge/test_persona_filter.py` — 40 tests total (19+9+6+5) ✅ M1 COMPLETE

### M_Robert — uncle_Robert Primary Auditor 🟢 IN PROGRESS

**Why M_Robert?** Альтернативный ведущий аудитор на основе IIA Professional Practices Framework и Brink's Modern Internal Auditing methodology. Активируется через `--auditor uncle_robert` флаг в CLI. Использует CCCE format (Condition/Criteria/Cause/Effect) для наблюдений и Draft→Final two-stage pipeline.

**Plan:** [.claude/plans/uncle-robert-auditor.md](.claude/plans/uncle-robert-auditor.md)

**Tasks:**
- [x] `personas/uncle_robert/config.yaml` + `persona_prompt.md` + `persona_context.md` — scaffolding + configuration (Task 1)
- [ ] `python main.py build-persona uncle_robert` — ingest PDF corpus в ChromaDB (Task 2)
- [x] `agents/uncle_robert.py` (NEW) — UncleRobertAgent с Brink's RAG retrieval (Task 3)
- [x] `report_generator/ccce_formatter.py` (NEW) — CCCE findings format (Task 4)
- [x] `report_generator/orchestrator.py` — auditor dispatcher (Task 5)
- [x] `main.py` — `--auditor` флаг в `run` команде (Task 6)
- [x] `tests/agents/test_uncle_robert.py` — 14 unit tests (Task 7)
- [x] `core/config.py` — BRINKS_CHUNK_SIZE constants
- [x] `knowledge/brinks_chapters.json` — chapter metadata with RAG flags

### M_Evidence — Evidence Traceability & Requirements Hierarchy 🔴

**Why M_Evidence?** Отчёты не содержат ссылок на анализируемые документы. RAG-запросы захардкожены, `evidence/` никогда не индексируется. Каждое наблюдение должно ссылаться на источник (Evidence) и применимые требования (L1 Регулятор / L2 Аудит / L3 Локальный). Система 3-уровневых требований: глобальная ChromaDB с metadata-фильтром (как persona-система, но по `req_level` и `task_name`).

**Tasks:**
- [ ] Task 1: `knowledge/indexer.py` — metadata schema (doc_type, req_level, page_number, task_name)
- [ ] Task 2: `knowledge/requirements_indexer.py` (NEW) — L1/L2/L3 requirement library management
- [ ] Task 3: `knowledge/evidence_indexer.py` (NEW) — SHA-256 incremental indexing per task
- [ ] Task 4: `main.py create` — copy/download sources → evidence/ (local files, URLs, text queries)
- [ ] Task 5: `main.py add-requirement` (NEW) — CLI для управления L1/L2/L3
- [ ] Task 6: `tasks/base_task.py execute()` — sync evidence before report generation
- [ ] Task 7: `report_generator/orchestrator.py` — source-aware prompts + citation enforcement
- [ ] Task 8: tests — 24 тестов (evidence collection, requirements indexer, citations)

### M2 — Reviewer Agent (UncleKahneman) 🔴
- [ ] `core/llm.py` — `LLMFactory.get_llm(mode="default"|"cheap"|"deep")`
- [ ] `agents/reviewer_base.py` (NEW) — абстрактный `ReviewerAgent`
- [ ] `agents/uncle_kahneman.py` (NEW) — S1+S2 two-pass review
- [ ] `personas/uncle_kahneman/persona_prompt.md`
- [ ] `tests/agents/test_uncle_kahneman.py`

### M3 — Integration 🟠
- [ ] `report_generator/orchestrator.py` — reviewer hook после строки 139
- [ ] `main.py` — `--reviewer` в `run` и `create`
- [ ] `core/validator.py` — soft warning для unknown reviewer
- [ ] `tests/integration/test_reviewer_hook.py`

### M4 — DOCX Export + Revision Cycle 🟡
- [ ] `report_generator/docx/backends.py` (NEW) — adapter для 3 библиотек
- [ ] `report_generator/docx/exporter.py` (NEW) — MD→DOCX+comments
- [ ] `report_generator/docx/importer.py` (NEW) — DOCX→Feedback
- [ ] `report_generator/docx/version_manager.py` (NEW) — versions/ + manifest
- [ ] `agents/revision_agent.py` (NEW) — revision loop
- [ ] `main.py` — команды `export-docx`, `revise`
- [ ] `requirements.txt` — python-docx, docx-editor, docx-revisions

### M5 — Personalization 🟢
- [ ] `core/preferences.py` (NEW) — hybrid store global + per-task
- [ ] `agents/preference_learner.py` (NEW) — Track Changes → term substitutions
- [ ] `config/user_preferences.yaml.example`

---

## Backlog

- [ ] Process Mining Logging Tests — unit+integration для `ProcessMiningLogger` 🟢
- [ ] GigaChat Auto-Recovery — retry + auto-fallback на Ollama 🟢
- [ ] project_context.md size check перед Stop hook 🟢
- [ ] OpenClaw SKILL.md adaptation (заморожено до M3) 🟢

---

## Done ✅

- [x] Phase 1 — Foundation: setup.py, pytest, logging, validation (250+ tests)
- [x] Phase 2 — Quality: config refactor, CI/CD, coverage 40%+
- [x] Phase 3 — Polish: dev guides (1100 lines), 300+ tests, 54% coverage
- [x] Context persistence system: SessionStart/Stop/PreCompact hooks
- [x] GigaChat client MVP (core/gigachat_client.py — fallback на Ollama)

---

## See Also

- [Detailed plan M1-M5](.claude/plans/bright-wondering-crayon.md) — сигнатуры, алгоритмы, edge cases
- [GAP Analysis](docs/GAP_ANALYSIS.md) — архитектурные решения Phase 1-3
