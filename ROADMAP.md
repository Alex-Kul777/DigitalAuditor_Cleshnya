# Roadmap — DigitalAuditor Cleshnya

> Current sprint tracked in [.omc/notepad.md](.omc/notepad.md) (auto-loaded each session).

## Current Focus
**M1 — Persona Infrastructure** — в работе

## Milestones

### M1 — Persona Infrastructure 🔴
- [ ] `knowledge/retriever.py` — `filter` + `exclude_personas` post-filter
- [ ] `knowledge/indexer.py` — `index_documents(docs: list[Document])`
- [ ] `knowledge/persona_indexer.py` (NEW) — CLI фасад, `scaffold()`, `ingest_corpus()`
- [ ] `knowledge/persona_registry.py` (NEW) — `list_personas()`
- [ ] `personas/_templates/` + `personas/uncle_kahneman/` — scaffolding
- [ ] `report_generator/orchestrator.py:28` — `exclude_personas` в `_get_context`
- [ ] `main.py` — команда `build-persona`
- [ ] `tests/knowledge/test_persona_filter.py`

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
