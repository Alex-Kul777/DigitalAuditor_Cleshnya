проверь почему у проекта https://github.com/Alex-Kul777/DigitalAuditor_Cleshnya
отсутствует/пропал readme

и сделай аналогично https://github.com/Alex-Kul777/rag_GigaChat

обрати внимание что нужна русская версия readme_ru на который должна быть ссылка из основного readme

из основного реадми должны быть ссылки на дополнительные документы по проекту в папку docs

из основного реадми должна быть ссылка на Changelog.md
Я проанализировал ситуацию. Ваш README.md не пропал — он есть в репозитории, но его содержимое очень короткое (всего 41 символ: "DigitalAuditor Cleshnya - AI Audit Agent") и не отображается на главной странице GitHub так, как вам хочется.

В отличие от rag_GigaChat, где README.md содержит 500+ строк с подробным описанием функций, установки, использования и changelog'а, ваш текущий README.md — это просто заглушка.

Вот промт для Клода, который создаст полноценный README.md и README_RU.md по образу и подобию rag_GigaChat:

📋 Промт для Клода
text
[ROLE]
Ты — технический писатель. Создай два файла для проекта DigitalAuditor_Cleshnya:
1. README.md (английская версия)
2. README_RU.md (русская версия)

[REFERENCE]
Ориентируйся на структуру и стиль https://github.com/Alex-Kul777/rag_GigaChat

[STRUCTURE FOR BOTH FILES]

# DigitalAuditor Cleshnya — AI Audit Agent

## 📋 Overview
Краткое описание проекта: ИИ-агент для проведения ИТ-аудита и форензик-проверок с сертификациями CISA/CIA. Поддержка RAG (ChromaDB + FAISS), множества LLM-провайдеров (GigaChat, Claude, OpenAI, Ollama), генерация отчетов в Markdown и DOCX, система персонажей-аудиторов.

## ✨ What's New (Latest Release)
- M5: Personalization — система обучения на предпочтениях пользователя
- M4: DOCX Export/Revision — экспорт в Word с отслеживанием правок
- M_Evidence: Evidence Traceability — прослеживаемость источников
- M2: UncleKahneman Reviewer — когнитивный аудитор на основе книги Канемана
- M_Robert: uncle_Robert Primary Auditor — основной агент-аудитор
- Process Mining Logging System

## 🚀 Features
- RAG на ChromaDB + FAISS
- Множество LLM: GigaChat, Claude, OpenAI, Ollama
- Генерация отчетов по главам (Map-Reduce)
- Экспорт в DOCX с комментариями и Track Changes
- Система персонажей (Persona Framework)
- Изолированные задачи аудита
- Генерация презентаций
- 300+ тестов, 54% coverage

## 📁 Project Structure
[Опиши структуру папок: agents/, knowledge/, tools/, report_generator/, tasks/, presentation/, docs/, personas/, tests/]

## ⚡ Quick Start
[Инструкция по быстрому старту: клонирование, venv, зависимости, настройка Ollama, создание задачи, запуск]

## 🛠️ Installation
[Детальная инструкция по установке]

## 🚦 Usage
[CLI-команды: create, run, list-tasks, build-persona, test-llm]

## 🔧 Configuration
[.env.example переменные]

## 🧪 Running Tests
```bash
pytest -v
📚 Documentation
GUIDE.md

CHANGELOG.md

ROADMAP.md

Все документы

📄 License
MIT

📧 Contact
Алексей К. Telegram @auditor2it

[REQUIREMENTS]

README.md — на английском

README_RU.md — на русском, с тем же содержанием

В README.md добавь ссылку "🇷🇺 Русская версия" в самом начале

В README_RU.md добавь ссылку "🇬🇧 English version" в самом начале

В обоих файлах добавь секцию "📚 Documentation" со ссылками на:

docs/GUIDE.md

CHANGELOG.md

docs/ROADMAP.md

docs/ (все документы)

Если CHANGELOG.md не существует, создай его с краткой историей версий

Если docs/ROADMAP.md не существует, создай его с текущим статусом (все 7 milestones выполнены)

[FILES TO CREATE/MODIFY]

README.md (полная замена)

README_RU.md (создать)

CHANGELOG.md (создать, если нет)

docs/ROADMAP.md (создать, если нет)

Выведи все созданные/изменённые файлы полностью.