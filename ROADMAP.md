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

### M_Robert — uncle_Robert Primary Auditor 🟡 COMPLETE (9/9 tasks ✅)

**Why M_Robert?** Альтернативный ведущий аудитор на основе IIA Professional Practices Framework и Brink's Modern Internal Auditing methodology. Активируется через `--auditor uncle_robert` флаг в CLI. Использует CCCE format (Condition/Criteria/Cause/Effect) для наблюдений и Draft→Final two-stage pipeline.

**Plan:** [.claude/plans/uncle-robert-auditor.md](.claude/plans/uncle-robert-auditor.md)

**Tasks:**
- [x] `personas/uncle_robert/config.yaml` + `persona_prompt.md` + `persona_context.md` — scaffolding + configuration (Task 1)
- [x] `python main.py build-persona uncle_robert` — ingest PDF corpus с chapter filtering (Task 2) ✅
- [x] `agents/uncle_robert.py` (NEW) — UncleRobertAgent с Brink's RAG retrieval (Task 3)
- [x] `report_generator/ccce_formatter.py` (NEW) — CCCE findings format (Task 4)
- [x] `report_generator/orchestrator.py` — auditor dispatcher (Task 5)
- [x] `main.py` — `--auditor` флаг в `run` команде (Task 6)
- [x] `tests/agents/test_uncle_robert.py` — 14 unit tests (Task 7)
- [x] `knowledge/brinks_indexer.py` (NEW) — BrinksIndexer with chapter-based filtering + 13 tests
- [x] `core/config.py` — BRINKS_CHUNK_SIZE constants
- [x] `knowledge/brinks_chapters.json` — chapter metadata (26 indexed + 7 excluded)
- [ ] `personas/uncle_Robert/raw/` — Brink's PDF → markdown EN + RU (chunked translation, Task 9) 🔄 IN PROGRESS

### M_Evidence — Evidence Traceability & Requirements Hierarchy 🟢 COMPLETE (8/8 tasks ✅)

**Why M_Evidence?** Отчёты не содержат ссылок на анализируемые документы. RAG-запросы захардкожены, `evidence/` никогда не индексируется. Каждое наблюдение должно ссылаться на источник (Evidence) и применимые требования (L1 Регулятор / L2 Аудит / L3 Локальный). Система 3-уровневых требований: глобальная ChromaDB с metadata-фильтром (как persona-система, но по `req_level` и `task_name`).

**Tasks:**
- [x] Task 1: `knowledge/indexer.py` — metadata schema (doc_type, req_level, page_number, task_name)
- [x] Task 2: `knowledge/requirements_indexer.py` (NEW) — L1/L2/L3 requirement library management
- [x] Task 3: `knowledge/evidence_indexer.py` (NEW) — SHA-256 incremental indexing per task
- [x] Task 4: `main.py create` — copy/download sources → evidence/ (local files, URLs, text queries)
- [x] Task 5: `main.py add-requirement` (NEW) — CLI для управления L1/L2/L3
- [x] Task 6: `tasks/base_task.py execute()` — sync evidence before report generation
- [x] Task 7: `report_generator/orchestrator.py` — source-aware prompts + citation enforcement
- [x] Task 8: tests — 41 интеграционных тестов (evidence collection, requirements indexer, citations)

### M2 — Reviewer Agent (UncleKahneman) 🟢 COMPLETE (5/5 tasks ✅)
- [x] `core/llm.py` — `LLMFactory.get_llm(mode="default"|"cheap"|"deep")`
- [x] `agents/reviewer_base.py` (NEW) — абстрактный `ReviewerAgent` с S1/S2 алгоритмом
- [x] `agents/uncle_kahneman.py` (NEW) — S1+S2 two-pass review
- [x] `personas/uncle_kahneman/persona_prompt.md` + persona scaffold
- [x] `tests/agents/test_uncle_kahneman.py` — 18 unit tests

### M3 — Integration 🟢 COMPLETE (4/4 tasks ✅)
- [x] `report_generator/orchestrator.py` — reviewer_hook после строки 139
- [x] `main.py` — `--reviewer` в `run` и `create` командах
- [x] `core/validator.py` — soft warning для unknown reviewer
- [x] `tests/integration/test_reviewer_hook.py` — 7 integration tests

### M4 — DOCX Export + Revision Cycle 🟢 COMPLETE (6/6 tasks ✅)
- [x] `report_generator/docx/backends.py` (NEW) — adapter для 3 библиотек (PythonDocx, DocxEditor, DocxRevisions)
- [x] `report_generator/docx/exporter.py` (NEW) — MD→DOCX+comments extraction
- [x] `report_generator/docx/importer.py` (NEW) — DOCX→Feedback с comment separation
- [x] `report_generator/docx/version_manager.py` (NEW) — versions/ + manifest tracking
- [x] `agents/revision_agent.py` (NEW) — LLM-guided revision loop
- [x] `main.py` — команды `export-docx`, `revise` + `tests/integration/test_docx_cycle.py` (9 tests)

### M5 — Personalization 🟢 COMPLETE (6/6 tasks ✅)
- [x] `core/preferences.py` (NEW) — PreferencesStore + UserPreferences dataclass (4 categories)
- [x] `agents/preference_learner.py` (NEW) — Track Changes → term substitutions (MIN_FREQUENCY=2)
- [x] `agents/revision_agent.py` integration — auto-learn after revise()
- [x] `report_generator/orchestrator.py` integration — load + apply preferences in prompts
- [x] `config/user_preferences.yaml.example` — example with all options
- [x] `tests/test_preferences.py` — 19 unit tests

### M6 — README Maintenance Automation 🟢 COMPLETE (5/5 tasks ✅)

**Why M6?** Features ship faster than README updates. Auto-sync README (EN + RU), CHANGELOG, project structure, test counts from code state + PR metadata. No manual README maintenance.

**Plan:** [.omc/plans/readme_maintenance_strategy.md](.omc/plans/readme_maintenance_strategy.md)

**Tasks:**
- [x] Task 1: Create `CHANGELOG.md` (Keep a Changelog format) with M1-M5 entries
- [x] Task 2: Build `.github/scripts/generate_readme.py` (parse CHANGELOG, scan dirs, count tests, auto-translate EN→RU)
- [x] Task 3: Generate `README.md` + `README_RU.md` (auto-gen + manual sections)
- [x] Task 4: Create GitHub Actions workflows (validate on PR, auto-commit on merge, CHANGELOG auto-gen)
- [x] Task 5: Write 27 tests for auto-gen logic + workflow execution + translation accuracy (100% pass rate)

### M7 — Unified Logging System 🟢 COMPLETE (5/5 tasks ✅)

**Why M7?** Logging is fragmented: `audit.log` (text), `process_logs/process_mining_log.txt` (separate format). No unified way to trace LLM calls, retriever operations, internal steps. Multiple formats require separate parsers.

Solution: Single ProcessMiningLogger writing to 3 formats (TXT + CSV + JSON) with 6 configurable detail levels (ERROR/WARNING/INFO/DEBUG-1/2/3), auto-extracting call stack (module/method/line) via inspect.

**Plan:** [.claude/plans/m7-unified-logging.md](.claude/plans/m7-unified-logging.md)

**Tasks:**
- [x] Task 1: `core/unified_logger.py` — UnifiedLogger + TxtWriter/CsvWriter/JsonWriter classes (300+ lines)
- [x] Task 2: `core/logger.py` — refactor to use UnifiedLogger (backward compat with old setup_logger)
- [x] Task 3: Update all modules (agents/, knowledge/, report_generator/, core/llm.py, tasks/) to use structured logging
- [x] Task 4: `main.py` — add `--log-level` CLI flag (ERROR/WARNING/INFO/DEBUG-1/2/3)
- [x] Task 5: `tests/test_unified_logging.py` — 28 tests (writers, call stack, level filtering, formats, integration, backward compat) ✅ ALL PASS

### M_Cangjie — uncle_Robert как исполняемый навык (book2skill) 🟢 COMPLETE (5/5 tasks ✅)

**Why?** uncle_Robert уже имеет RAG (ChromaDB), но только для поиска по тексту. cangjie-skill (`book2skill`) извлекает методологии из Brink's 7th Edition в структурированные SKILL.md с разделами R/I/A1/A2/E/B — это даёт Claude проактивный доступ к конкретным методикам без similarity search.

**Docs:** [docs/uncle_robert_skills.md](docs/uncle_robert_skills.md)  
**Plan:** [.claude/plans/tingly-stirring-pancake.md](.claude/plans/tingly-stirring-pancake.md)

**Completed:**
- [x] Task 1: Установить cangjie-skill → `.omc/skills/cangjie/` (SKILL.md + methodology/ + extractors/ + templates/)
- [x] Task 2: Stage 0–1.5 — Adler разбор + 5 параллельных экстракторов + тройная верификация → 127 кандидатов, 50 верифицированы, 11 отклонены
- [x] Task 3: Stage 2–3 — 8 SKILL.md (CCCE, evidence, workpaper, tone, criteria, fieldwork, draft-report, risk-planning) + Zettelkasten INDEX с 12 связями
- [x] Task 4: Stage 4 — Pressure testing: 51 тест-кейс, 100% pass rate (`test-prompts.json` + `test-results.md`)
- [x] Task 5: Персона-навык `.omc/skills/uncle_robert_persona/SKILL.md` (WRITE + REVIEW режимы)

**Planned (следующая итерация):**
- [ ] Task 6: `iia-independence-rules` + `audit-report-distribution` (🟡 средний приоритет)
- [ ] Task 7: `agents/uncle_robert_reviewer.py` + `orchestrator.py:~45` REVIEWERS dict (Python интеграция)
- [ ] Task 8: `coso-internal-control`, `coso-erm`, `fraud-detection` (🟠 низкий приоритет)

### M_Kahneman — uncle_kahneman Persona Build (book2skill) 🟢 COMPLETE (8/8 tasks ✅)

**Why?** uncle_kahneman Python-агент (S1/S2 pipeline) готов, но `corpus/` пустой — агент работает без знания Канемана. Наполнены оба слоя: `.omc/skills/uncle_kahneman/` (IDE каталог смещений) + `personas/uncle_kahneman/corpus/` (RAG-чанки для Python агента).

**Plan:** [.claude/plans/uncle-kahneman-persona.md](.claude/plans/uncle-kahneman-persona.md)  
**Sources:** TF&S EN (3.6MB → 1148 KB md) + «Думай медленно» RU (3.7MB → 1922 KB md)

**Tasks:**
- [x] Task 0: PDF → markdown extraction (`tfs_en.md` 531 стр. + `tfs_ru.md` 377 стр.) via PyMuPDF
- [x] Task 1: Stage 0 — `BOOK_OVERVIEW.md` (Adler 4-шаговый разбор, 5 частей, 38 глав, приоритеты)
- [x] Task 2: Stage 1 — `candidates/biases.md` (20 смещений Tier1/2/3) + `s1s2-methodology.md`
- [x] Task 3: Stage 2 — `rejected/` (peak-end-rule, bernoulli — неаудит-релевантные)
- [x] Task 4: Stage 3 — 15×SKILL.md (halo, wysiati, anchoring, availability, affect, substitution, cognitive-ease, representativeness, narrative-fallacy, overconfidence, planning-fallacy, framing-effect, loss-aversion, sunk-cost, inside-view) + `INDEX.md` (Zettelkasten 15 связей)
- [x] Task 5: Stage 4 — `test-prompts.json` (46 кейсов) + `test-results.md` (46/46 = 100% pass, 0 cross-triggers)
- [x] Task 6: Персона-навык `.omc/skills/uncle_kahneman_persona/SKILL.md` (REVIEW only, S1+S2 workflow)
- [x] Task 7: `corpus/` — 42 markdown-чанка (TF&S Ch.1-34 + Appendix A) для Python S1/S2 RAG

---

## Backlog

- [x] Process Mining Logging Tests — unit+integration для `ProcessMiningLogger` (33 tests ✅) 🟢
- [x] Console output for UnifiedLogger — ConsoleWriter (stdout) + tests ✅ 🟢
- [ ] M_Converter — PDF Translation & Markdown Conversion ⬜
  - [ ] `tools/document_converter.py` — `translate_pdf()` + `convert_pdf_to_markdown()` + CLI
  - [ ] `main.py convert` command
  - [ ] `.gitignore` — exclude `personas/*/raw/*.pdf`
  - [ ] `requirements.txt` — add `pdf2zh`, `docling`
  - [ ] `docs/document_converter.md` — full reference with examples
  - [ ] Test on `personas/CISA/raw/CISA Review Manual.pdf`
- [ ] Enhanced GigaChat timeout logging — timing details + prompt context + retry info 🟡
- [ ] GigaChat Auto-Recovery — retry + auto-fallback на Ollama 🟢
- [ ] project_context.md size check перед Stop hook 🟢
- [ ] OpenClaw SKILL.md adaptation (заморожено до M3) 🟢
- [ ] M_CitationFix — Evidence citation context loss 🔴
  - [ ] `report_generator/orchestrator.py:74` — добавить `[Source: filename, p.N]` перед каждым чанком в `_get_context()`
  - [ ] `report_generator/orchestrator.py:93` — то же для `_get_criteria_context()`
  - [ ] `tasks/instances/gogol_audit/config.yaml` — заполнить `sources: [gogol_dead_souls.txt]`
  - [ ] `orchestrator.py:117` — query через stem файла (`gogol dead souls`) вместо `gogol_dead_souls.txt`
  - [ ] (опционально) `tasks/base_task.py` — авто-заполнение `sources` из `evidence/` если список пуст
  - [ ] Re-run gogol_audit и проверить `| Evidence | gogol_dead_souls.txt |` в отчёте

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
