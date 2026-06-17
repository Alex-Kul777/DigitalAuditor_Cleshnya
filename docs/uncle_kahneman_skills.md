# uncle_kahneman Skill Tree — Thinking Fast and Slow

**Источник**: Thinking Fast and Slow — Daniel Kahneman (2011)  
**Pipeline**: cangjie / book2skill  
**Статус**: Stages 0–4 + corpus завершены ✅  
**Расположение**: `.omc/skills/uncle_kahneman/` + `personas/uncle_kahneman/corpus/`

---

## Роль персоны

uncle_kahneman — **рецензент**, не аудитор. Его задача: после того как uncle_Robert написал CCCE-наблюдение, uncle_kahneman проверяет текст на когнитивные смещения автора.

```
uncle_Robert writes CCCE finding
        ↓
uncle_kahneman reviews: "какое смещение здесь активно?"
        ↓
<!-- REVIEWER:uncle_kahneman:START -->
> Дядя Канеман замечает: эффект ореола (TF&S Ch.7)...
<!-- REVIEWER:uncle_kahneman:END -->
```

---

## Архитектура: два слоя

Та же двухслойная архитектура, что и у uncle_robert:

### `personas/uncle_kahneman/` — Python runtime

```
personas/uncle_kahneman/
├── config.yaml          # RAG: k_rag=3, corpus_format=markdown
├── persona_prompt.md    # System prompt: {s1_hint}, {rag_context}, {paragraph}
├── corpus/              # 42 markdown-чанка из TF&S (Ch.1–34 + Appendix A)
└── raw/
    ├── tfs_en.md        # TF&S EN извлечённый текст (531 стр., 1148 KB)
    ├── tfs_ru.md        # «Думай медленно» RU (377 стр., 1922 KB)
    └── *.pdf            # Исходные PDF
```

**Потребитель**: `agents/uncle_kahneman.py` → `UncleKahneman(ReviewerAgent)` — два прохода:
- **S1**: cheap LLM, JSON `{suspicious, hint}` — быстрый скан каждого параграфа
- **S2**: strong LLM + RAG из `corpus/` — глубокий анализ подозрительных параграфов

**Запуск**: `python main.py run --task <task_name> --reviewer uncle_kahneman`

### `.omc/skills/uncle_kahneman/` — Claude Code IDE layer

```
.omc/skills/uncle_kahneman/
├── BOOK_OVERVIEW.md     # Stage 0: Adler 4-шаговый разбор TF&S (5 частей, 38 глав)
├── INDEX.md             # Zettelkasten: 15 смещений, граф связей, режимы CCCE
├── candidates/          # Stage 1: biases.md (20 смещений Tier1/2/3) + s1s2-methodology.md
├── rejected/            # Stage 2: peak-end-rule, bernoulli (неаудит-релевантные)
├── skills/              # Stage 3: 15 SKILL.md с R/I/A1/A2/E/B структурой
├── test-prompts.json    # Stage 4: 46 тест-кейсов (15 навыков × 3 + 1 комбо)
└── test-results.md      # Stage 4: 46/46 pass (100%), 0 cross-triggers
```

**Потребитель**: Claude Code (IDE) — читает skills при рецензировании аудиторских текстов.  
**Активация**: `/uncle_kahneman`, «дядя канеман», «проверь на смещения», «система 1».

### Итог

| | `personas/uncle_kahneman/` | `.omc/skills/uncle_kahneman/` |
|--|---------------------------|-------------------------------|
| Потребитель | Python agent (UncleKahneman) | Claude Code (IDE) |
| Триггер | `--reviewer uncle_kahneman` CLI | языковые сигналы / `/uncle_kahneman` |
| Механизм | S1 (cheap LLM) + S2 (RAG из corpus/) | структурированные SKILL.md |
| Контекст | production pipeline выполнения задачи | IDE-сессия рецензирования |
| Данные | 42 markdown-чанка в corpus/ | 15 SKILL.md файлов |

Один источник (TF&S PDF) → два слоя → два потребителя. Не дублирование — дополнение.

---

## Каталог смещений (15 SKILL.md)

Каждый файл содержит разделы **R** (verbatim ≤150 chars) / **I** (интерпретация) / **A1** (пример) / **A2** (триггер) / **E** (E-шаги S2) / **B** (границы).

| # | Слаг | Смещение | Глава TF&S | Аудит-контекст |
|---|------|----------|-----------|----------------|
| 1 | `halo-effect` | Эффект ореола | Ch.7, p.82 | Репутация → оценка контроля |
| 2 | `wysiati` | Что видишь — то и есть | Ch.7-8, p.85 | Вывод без метрики покрытия |
| 3 | `anchoring` | Эффект якоря | Ch.11 | Число от аудируемой стороны как якорь |
| 4 | `availability-heuristic` | Эвристика доступности | Ch.12 | Медийный прецедент вместо статистики |
| 5 | `affect-heuristic` | Аффективная эвристика | Ch.12-13 | «Вызывает опасения» без данных |
| 6 | `substitution` | Подмена атрибута | Ch.9 | «Политика существует» ≠ «соответствие по существу» |
| 7 | `cognitive-ease` | Когнитивная лёгкость | Ch.5 | Форма документа ≠ содержание |
| 8 | `representativeness` | Репрезентативность | Ch.14-16 | Стереотип без базовых ставок |
| 9 | `narrative-fallacy` | Нарративная ошибка | Ch.19 | Ретроспективная история вместо данных |
| 10 | `overconfidence` | Самоуверенность | Ch.19-20 | «Несомненно» без выборки |
| 11 | `planning-fallacy` | Ошибка планирования | Ch.23 | Оптимистичный срок без reference class |
| 12 | `framing-effect` | Эффект обрамления | Ch.34 | «92% соответствия» скрывает «8% нарушений» |
| 13 | `loss-aversion` | Неприятие потерь | Ch.26 | Смягчённая рекомендация из-за стоимости |
| 14 | `sunk-cost` | Невозвратные затраты | Ch.32 | «Уже вложено 15 млн» как аргумент продолжения |
| 15 | `inside-view` | Внутренняя перспектива | Ch.23 | Только внутренние данные без бенчмарка |

---

## Zettelkasten-граф связей

```
wysiati ──triggers──► halo-effect, overconfidence
halo-effect ◄──mechanism── cognitive-ease
availability-heuristic ──mechanism──► substitution, affect-heuristic
narrative-fallacy ──overlaps──► overconfidence
overconfidence ──causes──► planning-fallacy
planning-fallacy ──instance-of──► inside-view
framing-effect ──contrasts──► loss-aversion
sunk-cost ──subtype-of──► loss-aversion
```

---

## Pipeline (cangjie / book2skill)

```
TF&S EN PDF (3.6 MB) + Думай медленно RU PDF (3.7 MB)
        │
        ▼ PyMuPDF extraction
personas/uncle_kahneman/raw/tfs_en.md (531 стр.)
personas/uncle_kahneman/raw/tfs_ru.md (377 стр.)
        │
        ├─── Stage 0 ──► BOOK_OVERVIEW.md (Adler 4-шаговый разбор)
        │
        ├─── Stage 1 ──► candidates/ (20 смещений Tier1/2/3)
        │
        ├─── Stage 2 ──► rejected/ (4 файла — неаудит-релевантные)
        │
        ├─── Stage 3 ──► skills/ (15 SKILL.md) + INDEX.md
        │
        ├─── Stage 4 ──► test-prompts.json (46 кейсов) → 46/46 pass ✅
        │
        ├─── Step 6 ───► .omc/skills/uncle_kahneman_persona/SKILL.md (wrapper)
        │
        └─── Step 7 ───► corpus/ (42 чанка → Python RAG)
```

---

## Отличия от uncle_robert

| Аспект | uncle_robert | uncle_kahneman |
|--------|-------------|----------------|
| Цель | WRITE + REVIEW CCCE-наблюдений | REVIEW только (обнаружение смещений) |
| Источник | Brink's 7th Ed. (методология аудита) | TF&S (когнитивная психология) |
| Навыков | 8 (методологические) | 15 (каталог смещений) |
| Python corpus | Не нужен (RAG через ChromaDB) | `corpus/` обязателен для S1/S2 |
| Python агент | Нет отдельного .py | `agents/uncle_kahneman.py` уже написан |
| Формат вывода | Markdown CCCE-блок | HTML comment markers |

---

## Использование

### Через Claude Code (IDE)

```
/uncle_kahneman review <параграф_наблюдения>
```

Или автоматически при наличии триггер-фраз: «проверь на смещения», «дядя канеман», «когнитивное смещение».

### Через Python CLI

```bash
# Рецензия конкретной задачи
python main.py run --task gogol_audit_v2 --reviewer uncle_kahneman

# После корпус уже проиндексирован — повторные запуски быстрее
```

### Прямое использование агента

```python
from agents.uncle_kahneman import UncleKahneman

reviewer = UncleKahneman()
comment = reviewer.review_paragraph("Система контроля надлежащим образом функционирует...")
# → <!-- REVIEWER:uncle_kahneman:START --> ... <!-- REVIEWER:uncle_kahneman:END -->
```

---

## Результаты pressure testing (Stage 4)

- **46 тест-кейсов**: 15 навыков × 3 (should_trigger / should_not_trigger / edge_case) + 1 комбо
- **Результат**: 46/46 pass (100%)
- **Cross-trigger**: 0 false positives — все смежные пары (halo/cognitive-ease, wysiati/overconfidence, availability/representativeness и др.) корректно разграничены

---

## Planned (следующая итерация)

| Навык | Приоритет | Глава TF&S |
|-------|-----------|-----------|
| `conjunction-fallacy` | MEDIUM | Ch.15 |
| `regression-to-mean` | MEDIUM | Ch.17 |
| `expert-intuition-conditions` | LOW | Ch.22 |
