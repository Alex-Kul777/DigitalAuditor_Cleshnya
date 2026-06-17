# Model Routing Rules — DigitalAuditor_Cleshnya

Правила выбора LLM модели в зависимости от типа задачи.

## Routing Table

| Задача | Модель | Переменная .env | Причина |
|--------|--------|-----------------|---------|
| Архитектурные решения, полные audit отчёты, compliance reasoning, сложный анализ | **GigaChat-2-Max** | `GIGACHAT_MODEL=giga-2-max` | Высокое качество рассуждений, поддержка русского языка |
| Поиск по коду, простые правки, написание тестов, быстрые аналитические запросы | **GigaChat-2-Lite** или **Claude Haiku** | `GIGACHAT_MODEL=giga-2-lite` | Скорость, экономия токенов |
| Черновики, отладка, примеры, офлайн-работа (без интернета) | **Ollama (digital-auditor-cisa)** | `OLLAMA_MODEL=digital-auditor-cisa` | Локально, бесплатно, нет задержек |

## Fallback Chain

Если модель недоступна:

```
GigaChat-2-Max → GigaChat-2-Lite → Claude Haiku → Ollama (local)
```

## Current Status

- **GigaChat integration**: ⚠️ **В разработке** (`core/gigachat_client.py` — unfixed issues)  
  - Fallback: используется Ollama (`digital-auditor-cisa`)
- **Ollama**: ✅ Работает  
- **Claude Haiku**: ✅ Доступен через Claude Code

## Usage

**При запуске audit:**

```bash
# Используется текущая конфигурация .env
python main.py run --task <task_name>

# Для явного выбора модели (будущее):
# OLLAMA_MODEL=digital-auditor-cisa python main.py run --task <task_name>
```

**При работе с Claude Code:**

- Для сложных архитектурных решений: переключитесь на GigaChat-2-Max (когда будет готово)
- Для быстрого поиска по коду: используйте Haiku текущего сеанса
- Для отладки: локальный Ollama

## Notes

- В `core/config.py` хранится текущая конфигурация LLM
- В `.env` переменные: `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `GIGACHAT_API_KEY`, `GIGACHAT_MODEL`
- Выбор модели в приложении управляется файлом конфигурации, а не environment переменными
