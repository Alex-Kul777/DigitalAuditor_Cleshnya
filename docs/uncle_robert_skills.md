# uncle_Robert Skill Tree — Brink's Modern Internal Auditing

**Источник**: Brink's Modern Internal Auditing, 7th Edition — Robert R. Moeller (2009)  
**Pipeline**: cangjie / book2skill  
**Статус**: Stage 0–4 завершены ✅  
**Расположение**: `.omc/skills/uncle_robert/`

---

## Зачем два слоя: `personas/` vs `.omc/skills/`?

Это принципиальное архитектурное решение, а не дублирование.

### `personas/uncle_Robert/` — Python runtime

```
personas/uncle_Robert/
├── config.yaml          # RAG-параметры: chunk_size, filter, req_level
├── persona_prompt.md    # System prompt для UncleRobertAgent (Python)
├── persona_context.md   # Контекст для агента
└── raw/                 # Brink's PDF + Markdown чанки → ChromaDB
```

**Потребитель**: `agents/uncle_robert.py` → `UncleRobertAgent` → `python main.py run --auditor uncle_robert`

**Механизм**: similarity search по ChromaDB — "найди релевантные чанки из Brink's по запросу". Работает в **production audit pipeline** во время выполнения задачи.

### `.omc/skills/uncle_robert/` — Claude Code IDE layer

```
.omc/skills/uncle_robert/
├── BOOK_OVERVIEW.md     # Adler Stage 0: структурный разбор книги
├── verified.md          # Stage 1.5: 50 verified / 11 rejected кандидатов
├── INDEX.md             # Zettelkasten: граф связей, режимы использования
├── test-prompts.json    # Stage 4: 51 pressure test кейс
├── test-results.md      # Stage 4: 51/51 pass (100%)
└── skills/              # 8 SKILL.md файлов с R/I/A1/A2/E/B структурой
```

**Потребитель**: Claude Code (IDE) — читает skills при написании/рецензировании отчётов **в диалоге с разработчиком**. Активируется при `/uncle_robert` или автоматически по языковым триггерам.

**Механизм**: структурированная методология с verbatim цитатами, шагами выполнения и границами применения. Работает **без ChromaDB** — знание уже закодировано в Markdown.

### Итог

| | `personas/uncle_Robert/` | `.omc/skills/uncle_robert/` |
|--|--------------------------|------------------------------|
| Потребитель | Python agent (UncleRobertAgent) | Claude Code (IDE assistant) |
| Триггер | `--auditor uncle_robert` CLI | языковые сигналы / `/uncle_robert` |
| Механизм | similarity search (ChromaDB) | структурированные SKILL.md |
| Контекст | production audit task execution | IDE-сессия разработки/рецензирования |
| Обновление | rebuild ChromaDB index | редактировать SKILL.md |

Один источник (Brink's PDF) → два слоя знаний → два разных потребителя. Не дублирование — дополнение.

---

## Структура skill tree

### Pipeline (cangjie / book2skill)

```
Stage 0 — Adler reading    → BOOK_OVERVIEW.md
Stage 1 — 5 extractors     → candidates/ (127 кандидатов)
  ├── frameworks.md   (20)
  ├── principles.md   (41)
  ├── cases.md        (28)
  ├── counter-examples.md (19)
  └── glossary.md     (19)
Stage 1.5 — Triple verify  → verified.md (50 pass) + rejected/ (11)
Stage 2 — RIA++ SKILL.md   → skills/ (8 навыков)
Stage 3 — Zettelkasten     → INDEX.md (12 связей)
Stage 4 — Pressure test    → test-prompts.json + test-results.md (51/51)
```

### Навыки (8 SKILL.md)

Каждый навык содержит разделы: **R** (цитата ≤150 символов) / **I** (интерпретация) / **A1** (применение в книге) / **A2** (когда активировать ★) / **E** (шаги выполнения) / **B** (границы).

#### Группа: Планирование и полевая работа

| Навык | Файл | Brink's | Ключевые концепции |
|-------|------|---------|-------------------|
| `risk-based-audit-planning` | `skills/risk-based-audit-planning.md` | Ch.8, 10, 15 | Audit universe, risk matrix (likelihood × impact), IIA Std 2010, Audit Committee approval |
| `fieldwork-methodology` | `skills/fieldwork-methodology.md` | Ch.7, 8 | Engagement letter, field survey (5 элементов), 3 типа программ, fraud exception, field closeout |

#### Группа: Ядро наблюдения (CCCE)

| Навык | Файл | Brink's | Ключевые концепции |
|-------|------|---------|-------------------|
| `ccce-finding-format` | `skills/ccce-finding-format.md` | Ch.16, 17 | 6-компонентная структура: Condition / Criteria / Cause / Effect + Recommendation + Risk Rating |
| `iia-criteria-reference` | `skills/iia-criteria-reference.md` | Ch.8, 17 | L1/L2/L3 иерархия критериев; таблица: тема finding → номер IIA Std / COSO / CobiT |
| `evidence-hierarchy` | `skills/evidence-hierarchy.md` | Ch.7 | 7-уровневая иерархия (Exhibit 7.8) + SRRU тест (Sufficient/Reliable/Relevant/Useful) |

#### Группа: Рабочая документация

| Навык | Файл | Brink's | Ключевые концепции |
|-------|------|---------|-------------------|
| `workpaper-standards` | `skills/workpaper-standards.md` | Ch.16 | 3 типа файлов, 6 критериев качества, supervisory review, 7-летний retention (IIA Std 2330) |

#### Группа: Коммуникация и отчётность

| Навык | Файл | Brink's | Ключевые концепции |
|-------|------|---------|-------------------|
| `constructive-reporting-tone` | `skills/constructive-reporting-tone.md` | Ch.17 | Exhibit 17.4 (accusatory → constructive); 6 техник балансировки; fraud exception |
| `draft-report-cycle` | `skills/draft-report-cycle.md` | Ch.17 | 6-фазный Exhibit 17.6; 14-дней на ответ; management response дословно; IIA Std 2421 correction |

---

## Граф связей (Zettelkasten)

```
risk-based-audit-planning ──composes-with──→ fieldwork-methodology
risk-based-audit-planning ──composes-with──→ iia-criteria-reference
fieldwork-methodology ──composes-with──→ evidence-hierarchy
fieldwork-methodology ──composes-with──→ workpaper-standards
fieldwork-methodology ──composes-with──→ ccce-finding-format
evidence-hierarchy ──depends-on──→ ccce-finding-format
iia-criteria-reference ──depends-on──→ ccce-finding-format
workpaper-standards ──composes-with──→ ccce-finding-format
ccce-finding-format ──depends-on──→ constructive-reporting-tone
ccce-finding-format ──depends-on──→ draft-report-cycle
evidence-hierarchy ──composes-with──→ workpaper-standards
iia-criteria-reference ──contrasts-with──→ evidence-hierarchy
```

**12 связей** между 8 навыками.

---

## Режимы использования

### PLAN mode — подготовка аудита
```
1. risk-based-audit-planning  → universe + приоритеты
2. fieldwork-methodology      → engagement letter + программа
```

### WRITE mode — написание наблюдения
```
1. fieldwork-methodology      → убедиться, что field survey завершён
2. evidence-hierarchy         → выбрать тип доказательств (SRRU)
3. ccce-finding-format        → структурировать по 6 компонентам
4. iia-criteria-reference     → заполнить Criteria L1/L2/L3
5. workpaper-standards        → оформить с cross-ref
6. constructive-reporting-tone → проверить тон
```

### REPORT mode — выпуск отчёта
```
1. constructive-reporting-tone → тон всего отчёта
2. draft-report-cycle          → 6-фазный цикл согласования
```

### REVIEW mode — рецензирование
```
1. ccce-finding-format         → S1: есть ли 6 компонентов?
2. iia-criteria-reference      → S2: критерии авторитетны?
3. evidence-hierarchy          → S2: SRRU соблюдён?
4. workpaper-standards         → S2: cross-reference есть?
5. constructive-reporting-tone → S2: тон конструктивный?
6. draft-report-cycle          → S2: цикл согласован?
```

---

## Pressure test (Stage 4)

**51 тест-кейс** на 8 навыков: 27 should_trigger / 16 should_not_trigger / 8 edge_case.

**Результат**: 51/51 = 100% — все навыки приняты.

Файлы: [`test-prompts.json`](../.omc/skills/uncle_robert/test-prompts.json) · [`test-results.md`](../.omc/skills/uncle_robert/test-results.md)

---

## Planned (Stage 2, следующая итерация)

| Приоритет | Slug | Источник Brink's |
|-----------|------|-----------------|
| 🟡 Средний | `iia-independence-rules` | p12, p13 — IIA Std 1100, 1130 |
| 🟡 Средний | `audit-report-distribution` | p39–p41 — distribution list, Std 2060 |
| 🟠 Низкий | `coso-internal-control` | FW-01 — 5 компонентов COSO IC |
| 🟠 Низкий | `coso-erm` | FW-02 — 8 компонентов COSO ERM |
| 🟠 Низкий | `fraud-detection` | FW-13 — fraud risk indicators |

---

## Python интеграция (опционально)

Добавить uncle_Robert как рецензент в production pipeline:

```python
# report_generator/orchestrator.py (~строка 45)
REVIEWERS = {
    "uncle_kahneman": "agents.uncle_kahneman.UncleKahneman",
    "uncle_robert":   "agents.uncle_robert_reviewer.UncleRobertReviewer",  # новый
}
```

Новый класс `agents/uncle_robert_reviewer.py`:
- Наследует `ReviewerAgent` из `agents/reviewer_base.py`
- `_s1_prompt()` → проверяет CCCE структуру по `skills/ccce-finding-format.md`
- `_s2_prompt()` → проверяет соответствие главам Brink's по INDEX.md

```bash
python main.py run --task <task_name> --reviewer uncle_robert
```

---

## Связанные файлы

| Файл | Назначение |
|------|-----------|
| `.omc/skills/uncle_robert/INDEX.md` | Zettelkasten-карта навыков |
| `.omc/skills/uncle_robert/BOOK_OVERVIEW.md` | Stage 0 Adler-разбор Brink's |
| `.omc/skills/uncle_robert/verified.md` | Stage 1.5: список верифицированных кандидатов |
| `personas/uncle_Robert/config.yaml` | RAG-конфиг Python-агента |
| `personas/uncle_Robert/persona_prompt.md` | System prompt Python-агента |
| `agents/uncle_robert.py` | UncleRobertAgent (production) |
| `report_generator/ccce_formatter.py` | CCCE findings formatter |
| `.omc/skills/uncle_robert_persona/SKILL.md` | Персона-обёртка для Claude Code |
