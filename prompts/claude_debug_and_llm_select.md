cat > prompts/claude_debug_and_llm_select.md << 'EOF'
# Инструкция для Claude: Добавление выбора LLM и DEBUG-режима в CLI

**Дата:** 2026-04-21
**Приоритет:** High
**Затрагиваемые файлы:** 6

---

## Контекст

В проекте DigitalAuditor_Cleshnya нужно добавить возможность:
1. Выбирать LLM-провайдера и модель через CLI при запуске аудита
2. Включать DEBUG-режим с тремя уровнями детализации (1/2/3)
3. Интегрировать DEBUG-логи в существующую систему логирования

**Принятые решения:**
- Флаги: `--llm-provider`, `--llm-model`, `--debug-level`
- DEBUG встраивается в существующий `core/logger.py`
- Формат: структурированный с временными метками
- Тест: запуск существующей задачи `gogol_audit`

---

## Файл 1: `main.py` — добавить CLI-флаги

**Найти команду `run`:**
```python
@cli.command()
@click.option('--task', required=True, help='Название задачи')
def run(task: str):
    task_dir = Path(f"tasks/instances/{task}")
    if not task_dir.exists():
        click.echo(f"[-] Задача '{task}' не найдена")
        return
    from tasks.base_task import AuditTask
    audit_task = AuditTask(task_dir)
    audit_task.execute()
    click.echo(f"[+] Аудит завершен. Отчет в {task_dir}/output/")
Заменить на:

python
@cli.command()
@click.option('--task', required=True, help='Название задачи')
@click.option('--llm-provider', default=None, help='LLM провайдер: gigachat, ollama, anthropic, openai')
@click.option('--llm-model', default=None, help='Модель LLM (например, GigaChat-2-Max)')
@click.option('--debug-level', type=int, default=0, help='Уровень DEBUG: 1=базовый, 2=с токенами, 3=полный')
def run(task: str, llm_provider: str, llm_model: str, debug_level: int):
    task_dir = Path(f"tasks/instances/{task}")
    if not task_dir.exists():
        click.echo(f"[-] Задача '{task}' не найдена")
        return
    
    # Пробрасываем параметры в окружение
    if llm_provider:
        os.environ['LLM_PROVIDER'] = llm_provider
    if llm_model:
        os.environ['LLM_MODEL_OVERRIDE'] = llm_model
    if debug_level > 0:
        os.environ['DEBUG_LEVEL'] = str(debug_level)
    
    from tasks.base_task import AuditTask
    audit_task = AuditTask(task_dir, debug_level=debug_level)
    audit_task.execute()
    click.echo(f"[+] Аудит завершен. Отчет в {task_dir}/output/")
Файл 2: core/logger.py — добавить поддержку debug_level
Найти:

python
def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    ...
Заменить на:

python
def setup_logger(name: str, debug_level: int = 0) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Определяем уровень логирования
    if debug_level > 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

class DebugLogger:
    """Обёртка для детального DEBUG-логирования."""
    
    def __init__(self, logger: logging.Logger, level: int):
        self.logger = logger
        self.level = level
    
    def log_provider(self, provider: str, model: str, temperature: float):
        if self.level >= 1:
            self.logger.debug(f"[DEBUG-1] LLM Provider: {provider}")
            self.logger.debug(f"[DEBUG-1] LLM Model: {model}")
            self.logger.debug(f"[DEBUG-1] Temperature: {temperature}")
    
    def log_tokens(self, prompt_tokens: int, completion_tokens: int, duration: float):
        if self.level >= 2:
            self.logger.debug(f"[DEBUG-2] Prompt: {prompt_tokens} tokens | Completion: {completion_tokens} tokens | Time: {duration:.1f}s")
    
    def log_content(self, prompt: str, response: str):
        if self.level >= 3:
            self.logger.debug(f"[DEBUG-3] === PROMPT ===\n{prompt[:500]}...")
            self.logger.debug(f"[DEBUG-3] === RESPONSE ===\n{response[:500]}...")
Файл 3: core/llm.py — поддержка переопределения модели
Найти get_llm:

python
def get_llm(temperature: float = 0.3):
    return LLMFactory.get_llm(temperature)
Заменить на:

python
def get_llm(temperature: float = 0.3, provider: str = None, model: str = None):
    return LLMFactory.get_llm(temperature, provider, model)

# В классе LLMFactory обновить метод get_llm:
@classmethod
def get_llm(cls, temperature: float = 0.3, provider_override: str = None, model_override: str = None):
    provider = provider_override or os.getenv("LLM_PROVIDER", "hybrid").lower()
    model = model_override or os.getenv("LLM_MODEL_OVERRIDE")
    
    if provider == "hybrid":
        if cls._check_gigachat():
            provider = "gigachat"
        else:
            provider = "ollama"
    
    logger.info(f"Selected LLM provider: {provider}" + (f" / {model}" if model else ""))
    
    if provider == "gigachat":
        return cls._get_gigachat(temperature, model)
    elif provider == "anthropic":
        return cls._get_anthropic(temperature, model)
    elif provider == "openai":
        return cls._get_openai(temperature, model)
    else:
        return cls._get_ollama(temperature, model)
Файл 4: tasks/base_task.py — проброс debug_level
Найти __init__:

python
class AuditTask:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.logger = setup_logger(f"task.{task_dir.name}")
        ...
Заменить на:

python
class AuditTask:
    def __init__(self, task_dir: Path, debug_level: int = 0):
        self.task_dir = task_dir
        self.debug_level = debug_level
        self.logger = setup_logger(f"task.{task_dir.name}", debug_level)
        self.debug_logger = DebugLogger(self.logger, debug_level)
        ...
Файл 5: agents/cisa_auditor.py — логирование в DEBUG
Найти generate_section:

python
def generate_section(self, prompt: str) -> str:
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
    return self.llm.invoke(full_prompt)
Заменить на:

python
def generate_section(self, prompt: str) -> str:
    import time
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
    
    start_time = time.time()
    response = self.llm.invoke(full_prompt)
    duration = time.time() - start_time
    
    # DEBUG-логирование
    if hasattr(self, 'debug_logger') and self.debug_logger.level >= 1:
        provider = os.getenv('LLM_PROVIDER', 'unknown')
        model = os.getenv('LLM_MODEL_OVERRIDE', 'default')
        self.debug_logger.log_provider(provider, model, 0.3)
    
    if hasattr(self, 'debug_logger') and self.debug_logger.level >= 2:
        prompt_tokens = len(full_prompt.split()) // 2  # Примерная оценка
        completion_tokens = len(response.split()) // 2
        self.debug_logger.log_tokens(prompt_tokens, completion_tokens, duration)
    
    if hasattr(self, 'debug_logger') and self.debug_logger.level >= 3:
        self.debug_logger.log_content(full_prompt, response)
    
    return response
Файл 6: core/config.py — новые переменные
Добавить:

python
LLM_MODEL_OVERRIDE = os.getenv("LLM_MODEL_OVERRIDE", "")
DEBUG_LEVEL = int(os.getenv("DEBUG_LEVEL", "0"))
Тестовая команда
bash
python main.py run --task gogol_audit --llm-provider gigachat --llm-model GigaChat-2-Max --debug-level 3
Ожидаемый вывод:

text
2026-04-21 10:15:32 [DEBUG-1] LLM Provider: gigachat
2026-04-21 10:15:32 [DEBUG-1] LLM Model: GigaChat-2-Max
2026-04-21 10:15:32 [DEBUG-1] Temperature: 0.3
2026-04-21 10:15:35 [DEBUG-2] Prompt: 1240 tokens | Completion: 350 tokens | Time: 3.2s
2026-04-21 10:15:35 [DEBUG-3] === PROMPT ===
Ты — старший ИТ-аудитор...
2026-04-21 10:15:35 [DEBUG-3] === RESPONSE ===
Executive Summary: ...
Проверка изменений
bash
python main.py run --task gogol_audit --debug-level 1
python main.py run --task gogol_audit --llm-provider ollama --debug-level 2
python main.py run --task gogol_audit --llm-provider gigachat --llm-model GigaChat-2-Max --debug-level 3
EOF

echo "[+] Prompt saved to prompts/claude_debug_and_llm_select.md"