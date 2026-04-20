# DigitalAuditor_Cleshnya

Тестовый проект

## 🔍 Process Mining Logger System

### Описание
Система логирования работы AI агента в соответствии с принципами **Process Mining** для анализа бизнес-процессов.

### 📊 Возможности

#### Поддерживаемые форматы экспорта:
- **JSON** - Структурированные данные с метаинформацией
- **Plain Text** - Человекочитаемые логи с разделителями
- **CSV** - Табличные данные для анализа в Excel/Python

#### Отслеживаемые поля:
- `event_id` - Уникальный идентификатор события
- `timestamp` - Временная метка создания события
- `date` - Дата в формате YYYY-MM-DD
- `time` - Время в формате HH:MM:SS
- `process_name` - Название процесса
- `stage` - Этап выполнения
- `start_time` - Время начала этапа
- `end_time` - Время завершения этапа
- `duration_seconds` - Продолжительность в секундах
- `duration_formatted` - Продолжительность в читаемом формате
- `author` - Автор процесса (AI_Agent_Lisa)
- `character` - Персонаж процесса (DigitalAuditor)
- `additional_data` - Дополнительные данные процесса

### 🚀 Быстрый старт

```python
from process_mining_logger import ProcessMiningLogger
from datetime import datetime

# Создание логгера
logger = ProcessMiningLogger()

# Логирование процесса
start_event = logger.log_process_start("My_Process", data={"user": "test"})

# Промежуточные этапы
logger.log_event("My_Process", "Processing", start_event.start_time, datetime.now())

# Завершение процесса
end_event = logger.log_process_end("My_Process", start_event, data={"status": "completed"})

# Экспорт во все форматы
files_info = logger.save_all_formats()
print(f"Файлы созданы: {files_info}")
```

### 📁 Структура проекта

```
DigitalAuditor_Cleshnya/
├── README.md                    # Этот файл
├── requirements.txt             # Зависимости проекта
├── process_mining/              # Основной модуль
│   ├── __init__.py             # Инициализация модуля
│   ├── process_mining_logger.py # Основной код системы
│   └── test_process_mining.py   # Unit тесты
├── process_logs/               # Логи процессов
│   ├── process_mining_log.json # JSON формат
│   ├── process_mining_log.txt  # Plain Text формат
│   └── process_mining_log.csv  # CSV формат
└── test_process_mining.py      # Внешние тесты
```

### 🧪 Тестирование

```bash
# Запуск unit тестов
python test_process_mining.py

# Импорт и ручное тестирование
python -c "from process_mining_logger import *; print('Import successful!')"
```

### 📈 Пример анализа

```python
# Получение сводки по процессам
summary = logger.get_process_summary()
print(f"Всего событий: {summary['total_events']}")
print(f"Уникальных процессов: {summary['unique_processes']}")
print(f"Общая продолжительность: {summary['total_duration']}")
```

### 🔧 Установка зависимостей

```bash
pip install -r requirements.txt
```

### 📊 Поддерживаемые процессы

Система создана для отслеживания работы AI агента Лиза:
- Создание GitHub репозиториев
- Разработка программных систем
- Выполнение unit тестов
- Process Mining анализ
- Автоматизация задач

### 💡 Применение

1. **Анализ эффективности** - Отслеживание времени выполнения процессов
2. **Выявление узких мест** - Анализ самых длительных этапов
3. **Оптимизация workflow** - Определение повторяющихся паттернов
4. **Аудит действий** - Полная трассировка работы системы
5. **Отчетность** - Автоматическая генерация отчетов

### 🤖 Автор

**AI Agent Lisa** (DigitalAuditor)
- Версия: 1.0
- Дата создания: 2026-04-20
- Принципы: Process Mining, Business Intelligence

---
*Создано с использованием принципов Process Mining для отслеживания и анализа AI процессов*