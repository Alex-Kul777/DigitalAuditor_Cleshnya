# Notepad
<!-- Auto-managed by OMC. Manual edits preserved in MANUAL section. -->

## Priority Context
<!-- ALWAYS loaded. Keep under 500 chars. Critical discoveries only. -->

## Working Memory
<!-- Session notes. Auto-pruned after 7 days. -->

## MANUAL
<!-- User content. Never auto-pruned. -->

### Current Focus
**M1 — Persona Infrastructure** (5/8 complete, blocker для M2-M5)
- [x] `knowledge/retriever.py` — `filter` + `exclude_personas` post-filter
- [x] `knowledge/indexer.py` — `index_documents(docs: list[Document])`
- [x] `knowledge/persona_indexer.py` (NEW) — CLI фасад, `scaffold()`, `ingest_corpus()`
- [x] `knowledge/persona_registry.py` (NEW) — `list_personas()` (in PersonaIndexer)
- [ ] `personas/_templates/` + `personas/uncle_kahneman/` — scaffolding
- [ ] `report_generator/orchestrator.py:28` — `exclude_personas` в `_get_context`
- [ ] `main.py` — команда `build-persona`
- [x] `tests/knowledge/test_persona_filter.py` — 19 unit tests (ALL PASSED)

Full backlog → [ROADMAP.md](../ROADMAP.md)

### 2026-04-22 05:58
### 2026-04-22 06:17
### 2026-04-22 09:04
## Plan: Adapt DigitalAuditor as OpenClaw Skill

**Status:** Planned, not started
**Plan file:** /home/kap/.claude/plans/bright-wondering-crayon.md
**TaskList IDs:** #3, #4, #5, #6, #7

**Decisions:**
- Deployment: bare metal (python main.py directly, no Docker)
- Path: .claw/skills/digitalauditor/SKILL.md (OpenClaw format for LizaClaw)
- Claude fallback chain: claude-opus-4-7 → claude-sonnet-4-6 → claude-haiku-4-5-20251001
- Ollama fallback: digital-auditor-cisa → qwen2.5:0.5b-instruct
- Smart model selection with auto-probe via helper script

**Deliverables:**
1. .claw/skills/digitalauditor/SKILL.md (Russian, OpenClaw format)
2. scripts/check_model_availability.py (helper for LLM availability check)
3. Optional: .claw/skills/digitalauditor/README.md

**Output path:** tasks/instances/{task_name}/output/Audit_Report.md (deterministic)


## 2026-04-22 05:58
### 2026-04-22 06:17
## ToDo: Process Mining Logging Tests

**Priority:** Low

**Description:** Add unit and integration tests for ProcessMiningLogger integration in AuditTask. Verify that:
- Events are logged correctly at each stage (start, validation, generation, end)
- Formats are correct (CSV, JSON, TXT) with proper structure
- File creation and writing works as expected
- Error cases are handled (process_end on failures)
- save_all_formats() produces valid output

**Related Files:**
- tasks/base_task.py (integration)
- process_mining/process_mining_logger.py (core)
- tests/test_process_logging.py (new test file needed)

**Status:** Not started - deferred to backlog


## 2026-04-22 05:58
## Future Enhancement: GigaChat Auto-Recovery with Ollama Fallback

**Priority:** Low
**Status:** Backlog

Improve fallback mechanism:
1. GigaChat retry logic (currently 3 attempts, exponential backoff)
2. On persistent failure → auto-launch Ollama
3. Continue audit with Ollama (no user intervention)

**Open Questions:**
- Retry count (3 vs more)?
- Ollama deployment (Docker vs local binary)?
- Timeout for Ollama startup (30/60 sec)?
- Auto-continue vs notify user?

**Related Files:**
- core/gigachat_client.py (circuit breaker, retries)
- core/llm.py (fallback logic)
- tests/integration/test_gigachat.py (test coverage needed)


