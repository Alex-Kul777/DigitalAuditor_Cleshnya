#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime

def generate_docs():
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    content = f'''# DigitalAuditor Cleshnya - Памятка по работе

**Версия:** 1.0
**Дата:** {datetime.now().strftime("%d.%m.%Y")}

---

## О проекте

DigitalAuditor Cleshnya - ИИ-агент для ИТ-аудита с сертификациями CISA/CIA.

### Возможности
- RAG на ChromaDB + FAISS
- Генерация отчетов по главам (Map-Reduce)
- Локальная LLM через Ollama (Qwen 2.5 0.5B)
- Поддержка GPU (CUDA)
- Изолированные задачи аудита
- Генерация презентаций

---

## Быстрый старт

Клонирование и установка:

    git clone git@github.com:Alex-Kul777/DigitalAuditor_Cleshnya.git
    cd DigitalAuditor_Cleshnya
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Настройка Ollama:

    ollama pull qwen2.5:0.5b-instruct
    ollama create digital-auditor-cisa -f Modelfile.auditor
    ollama serve

Создание и запуск задачи:

    python main.py create --name my_audit --company "Компания" --sources "источник"
    python main.py run --task my_audit

---

## Структура проекта

    DigitalAuditor_Cleshnya/
    ├── main.py                 # CLI
    ├── agents/                 # ИИ-агенты
    │   └── cisa_auditor.py     # Агент CISA/CIA
    ├── knowledge/              # RAG
    │   ├── raw_docs/           # Документы
    │   ├── fetcher.py          # Загрузка
    │   ├── indexer.py          # Индексация
    │   └── retriever.py        # Поиск
    ├── tools/                  # Инструменты
    │   ├── web_search.py       # Поиск в сети
    │   └── risk_matrix.py      # Оценка рисков
    ├── report_generator/       # Генератор отчетов
    │   └── orchestrator.py     # Map-Reduce
    ├── tasks/                  # Задачи аудита
    │   └── instances/          # Изолированные задачи
    ├── presentation/           # Презентации
    │   ├── slides/             # Слайды
    │   └── generate.py         # Генератор
    ├── docs/                   # Документация
    └── scripts/                # Скрипты

---

## Типовые сценарии

### Аудит ИТ-компании

    python main.py create --name t_tech --company "Т-Технологии" --audit-type it --sources "716-П" --sources "CISA"
    python main.py run --task t_tech

### Форензик-аудит (Мертвые души)

    cp gogol.txt knowledge/raw_docs/
    python scripts/rebuild_index.py
    python main.py create --name gogol --company "Чичиков" --audit-type forensic --sources "Мертвые души"
    python main.py run --task gogol

### Генерация презентации

    cd presentation
    python generate.py all

---

## Конфигурация

Файл .env:

    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL=digital-auditor-cisa
    LOG_LEVEL=INFO
    LOG_FILE=audit.log

Файл Modelfile.auditor:

    FROM qwen2.5:0.5b-instruct
    SYSTEM "Ты старший ИТ-аудитор CISA/CIA. Отвечай на русском."
    PARAMETER temperature 0.3
    PARAMETER num_ctx 8192

---

## Команды CLI

    python main.py create --name NAME --company COMPANY [--sources SRC] [--audit-type TYPE]
    python main.py run --task NAME
    python main.py list-tasks

---

## Мониторинг

Проверка GPU:

    nvidia-smi
    watch -n 1 nvidia-smi

Проверка Ollama:

    curl http://localhost:11434/api/tags
    ollama list

Логи:

    tail -f audit.log

Статус задач:

    python main.py list-tasks
    ls -la tasks/instances/

---

## Производительность

| Операция | CPU | GPU (GTX 1650) |
|----------|-----|----------------|
| Загрузка модели | 107 сек | 2.5 сек |
| Генерация отчета | 13 мин | 1-2 мин |
| Токенов/сек | 15-20 | 140-150 |

---

## Устранение неполадок

### Ollama не запускается
    pkill -9 ollama
    ollama serve &

### Ошибка CUDA
    export CUDA_VISIBLE_DEVICES=""
    ollama serve &

### Нет места в WSL
    wsl --shutdown
    diskpart
    select vdisk file="C:\\Users\\User\\AppData\\Local\\Packages\\...\\ext4.vhdx"
    compact vdisk

---

## Полезные ссылки

- Стандарты CISA: https://www.isaca.org
- Положение 716-П: https://cbr.ru
- Ollama: https://ollama.com
- LangChain: https://langchain.com
'''
    
    guide_path = docs_dir / "GUIDE.md"
    guide_path.write_text(content, encoding='utf-8')
    print(f"[+] Created: {guide_path}")

if __name__ == "__main__":
    generate_docs()
