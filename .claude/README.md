# Claude Code Context & Token Optimization System

Этот файл описывает систему сохранения контекста между сессиями и оптимизации использования токенов для проекта DigitalAuditor_Cleshnya.

## Что это?

Система из трёх **Claude Code hooks** (автоматические скрипты, запускаемые в критических точках сессии):

1. **SessionStart** (`.claude/hooks/session_start.py`) — при старте сессии загружает сохранённый контекст
2. **Stop** (`.claude/hooks/stop.py`) — при завершении сессии пишет timestamp checkpoint
3. **PreCompact** (`.claude/hooks/pre_compact.py`) — перед автосуммаризацией сохраняет снимок токенов

## Структура каталогов

```
.claude/
├── hooks/                          # Скрипты хуков
│   ├── session_start.py           # Инжектирует контекст при старте
│   ├── stop.py                    # Пишет checkpoint при остановке
│   └── pre_compact.py             # Снимок перед компакцией
├── memory/                         # Внешняя память (gitignored)
│   ├── project_context.md         # Ручная + авто-память
│   └── compact_snapshot.md        # Снимок токенов и состояния
├── rules/
│   └── model_routing.md           # Правила выбора LLM модели
└── settings.json                  # Конфигурация хуков
```

## Как это работает?

### При старте новой сессии (SessionStart)

1. Хук `session_start.py` читает `.claude/memory/project_context.md`
2. Содержимое оборачивается в `<audit-project-context>` тег
3. Контекст инжектируется в начало сессии Claude
4. Claude автоматически знает о прошлой работе, открытых вопросах и решениях

### Во время работы

Вы **вручную** обновляете `.claude/memory/project_context.md` в конце рабочего блока:

```markdown
# Контекст проекта DigitalAuditor_Cleshnya

## Текущая задача
- Реализация системы хуков для сохранения контекста

## Решения, принятые
- SessionStart хук загружает контекст из .claude/memory/project_context.md
- model_routing.md определяет правила выбора модели

## Открытые вопросы
- Нужна ли поддержка GigaChat (в разработке)
- Как оптимизировать размер project_context.md

---
_Сессия завершена: 2026-04-21 15:30_
```

### При завершении сессии (Stop)

1. Хук `stop.py` добавляет timestamp marker в конец `project_context.md`
2. Файл обрезается до 8000 символов (rolling window — новое в начале, старое в конце удаляется)
3. Это служит как напоминание о времени последнего обновления

### Перед компакцией контекста (PreCompact)

1. Хук `pre_compact.py` сохраняет в `compact_snapshot.md`:
   - Сколько токенов использовано из лимита
   - Триггер компакции
   - Timestamp снимка
2. Если сессия перезагружена после compaction — быстро можно вспомнить состояние

## Coexistence с OMC (oh-my-claudecode)

**OMC уже установлен** и имеет собственные SessionStart, Stop, PreCompact хуки глобально. Наша система:

- **Не конфликтует**: OMC пишет в `.omc/notepad.md`, мы — в `.claude/memory/project_context.md`
- **Инжектирует разные теги**: OMC использует `<project-memory-context>`, мы — `<audit-project-context>`
- **Дополняет**: OMC handles project metadata, мы сохраняем audit-специфичный контекст

Обе системы работают параллельно без проблем.

## Token Optimization

### Текущие настройки (глобальные)

```json
{
  "contextWindow": 80000,          // Максимум токенов на сессию
  "maxOutputTokens": 4000,         // Максимум вывода за ответ
  "autoCompactEnabled": true       // Автосуммаризация при заполнении
}
```

### Стратегия

1. **Priority Context** в project_context.md должен быть **<500 символов** — только самое важное
2. **Compact snapshots** сохраняют метаданные, если сессия сжата
3. **mgrep алиас** сокращает время поиска по коду (в ~/.zshrc)

## mgrep алиас

Для быстрого форматированного поиска по коду:

```bash
alias mgrep='grep --color=always -n -r --include="*.py" --include="*.md" --include="*.yaml" --include="*.json"'
```

**Использование:**
```bash
mgrep "AuditTask" .          # Поиск AuditTask во всех python/md/yaml/json файлах
mgrep "report_generator" .   # Все упоминания report_generator
```

## Manual Workflow

### Конец рабочей сессии

1. Обновите `.claude/memory/project_context.md`:
   ```
   ## Текущая задача
   [описание того, что делалось]
   
   ## Решения
   [что решили]
   
   ## TODO
   [что ещё нужно сделать]
   ```

2. Сохраните файл (Stop hook добавит timestamp автоматически)

3. Завершите сессию

### Начало новой сессии

1. Откройте Claude Code в проекте
2. SessionStart хук автоматически загрузит контекст в `<audit-project-context>`
3. Claude будет помнить всю прошлую работу

## Troubleshooting

### Хуки не запускаются

1. Проверьте что все скрипты исполняемы:
   ```bash
   ls -la .claude/hooks/*.py
   # Должны быть: -rwxr-xr-x
   ```

2. Проверьте что hooks зарегистрированы в `.claude/settings.json`:
   ```bash
   grep -A 20 '"hooks"' .claude/settings.json
   ```

3. В Claude Code введите `/hooks` — покажет все активные хуки

### project_context.md не загружается

- Убедитесь что файл существует: `.claude/memory/project_context.md`
- Проверьте размер: не более 4-5 KB (иначе займет весь контекст)
- Скопируйте часть контекста в другой файл, если слишком большой

### Как отключить хуки временно

Добавьте в `.claude/settings.json`:
```json
"disableAllHooks": true
```

Или удалите секцию `"hooks"` полностью.

## Best Practices

1. **Будьте лаконичны** — project_context.md это не лог, а краткая справка
2. **Обновляйте регулярно** — после важных решений, не в конце недели
3. **Используйте разделы** — Текущая задача / Решения / Открытые вопросы
4. **Trim старое** — Stop hook сохраняет только последние 8KB истории
5. **model_routing.md** — обновляйте правила при изменении доступных моделей

## See Also

- `CLAUDE.md` — основная документация проекта и его архитектура
- `.claude/rules/model_routing.md` — правила выбора LLM модели
- `.omc/notepad.md` — общепроектная память (OMC система)
