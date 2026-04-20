#!/bin/bash
# setup_project.sh - Скрипт генерации структуры проекта DigitalAuditor_Cleshnya
# Запуск: chmod +x setup_project.sh && ./setup_project.sh

set -e

PROJECT_ROOT="DigitalAuditor_Cleshnya"

echo "========================================="
echo "DigitalAuditor Cleshnya - Project Setup"
echo "========================================="
echo "[*] Создание структуры в: $PROJECT_ROOT"
echo ""

# Создание корневой директории
mkdir -p "$PROJECT_ROOT"

# .env.example
cat > "$PROJECT_ROOT/.env.example" << 'ENVEOF'
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=digital-auditor-cisa
TAVILY_API_KEY=your_tavily_key_here
LOG_LEVEL=INFO
LOG_FILE=audit.log
ENVEOF

# .gitignore
cat > "$PROJECT_ROOT/.gitignore" << 'GITEOF'
.venv/
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.env
.env.local
.vscode/
.idea/
*.swp
*.swo
chroma_db/
vector_store/
outputs/
tasks/instances/*/output/
tasks/instances/*/drafts/
tasks/instances/*/evidence/*.json
!tasks/instances/*/evidence/.gitkeep
knowledge/raw_docs/*
!knowledge/raw_docs/.gitkeep
*.log
GITEOF

# requirements.txt
cat > "$PROJECT_ROOT/requirements.txt" << 'REQEOF'
click>=8.1.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pyyaml>=6.0
ollama>=0.4.0
langchain>=0.3.0
langchain-community>=0.3.0
chromadb>=0.5.0
sentence-transformers>=2.2.0
faiss-cpu>=1.8.0
requests>=2.31.0
beautifulsoup4>=4.12.0
tavily-python>=0.3.0
duckduckgo-search>=6.0.0
pypdf>=4.0.0
python-docx>=1.1.0
markdown>=3.5.0
pandas>=2.0.0
openpyxl>=3.1.0
pytest>=8.0.0
REQEOF

# README.md
cat > "$PROJECT_ROOT/README.md" << 'READMEEND'
DigitalAuditor Cleshnya - AI Audit Agent
READMEEND

# Создание директорий
mkdir -p "$PROJECT_ROOT/core"
mkdir -p "$PROJECT_ROOT/agents/prompts"
mkdir -p "$PROJECT_ROOT/knowledge/raw_docs"
mkdir -p "$PROJECT_ROOT/knowledge/vector_store"
mkdir -p "$PROJECT_ROOT/tools"
mkdir -p "$PROJECT_ROOT/report_generator/chapters"
mkdir -p "$PROJECT_ROOT/report_generator/templates"
mkdir -p "$PROJECT_ROOT/tasks/instances"
mkdir -p "$PROJECT_ROOT/tests/fixtures"
mkdir -p "$PROJECT_ROOT/scripts"

# core/__init__.py
touch "$PROJECT_ROOT/core/__init__.py"

# core/config.py
cat > "$PROJECT_ROOT/core/config.py" << 'CONFIGEOF'
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "digital-auditor-cisa")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "audit.log")

KNOWLEDGE_RAW_DOCS = PROJECT_ROOT / "knowledge" / "raw_docs"
CHROMA_DB_PATH = PROJECT_ROOT / "chroma_db"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
CONFIGEOF

# core/llm.py
cat > "$PROJECT_ROOT/core/llm.py" << 'LLMEOF'
from langchain_community.llms import Ollama
from core.config import OLLAMA_BASE_URL, OLLAMA_MODEL

def get_llm(temperature: float = 0.3):
    return Ollama(
        base_url=OLLAMA_BASE_URL,
        model=OLLAMA_MODEL,
        temperature=temperature,
        num_ctx=8192,
    )
LLMEOF

# core/logger.py
cat > "$PROJECT_ROOT/core/logger.py" << 'LOGEOF'
import logging
import sys
from core.config import LOG_LEVEL, LOG_FILE

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
LOGEOF

# agents/__init__.py
touch "$PROJECT_ROOT/agents/__init__.py"

# agents/base.py
cat > "$PROJECT_ROOT/agents/base.py" << 'BASEEOF'
from abc import ABC, abstractmethod
from core.llm import get_llm
from core.logger import setup_logger

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.llm = get_llm()
        self.logger = setup_logger(f"agent.{name}")
    
    @abstractmethod
    def execute(self, task: str) -> str:
        pass
BASEEOF

# agents/cisa_auditor.py
cat > "$PROJECT_ROOT/agents/cisa_auditor.py" << 'AUDITOREOF'
from agents.base import BaseAgent

SYSTEM_PROMPT = """Ты — старший ИТ-аудитор с сертификатами CISA и CIA.
Твоя задача — проводить аудит в соответствии с международными стандартами.
Отвечай на русском языке в официально-деловом стиле.
Обязательно ссылайся на источники и стандарты."""

class CisaAuditor(BaseAgent):
    def __init__(self):
        super().__init__("cisa_auditor")
    
    def execute(self, task: str) -> str:
        prompt = f"{SYSTEM_PROMPT}\n\nЗадача: {task}"
        return self.llm.invoke(prompt)
    
    def generate_section(self, prompt: str) -> str:
        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        return self.llm.invoke(full_prompt)
AUDITOREOF

# agents/prompts/auditor_system.txt
cat > "$PROJECT_ROOT/agents/prompts/auditor_system.txt" << 'PROMPTEOF'
Ты — старший ИТ-аудитор с сертификатами CISA и CIA.
Твоя задача — проводить аудит в соответствии с международными стандартами.
Ты обязан ссылаться на конкретные пункты стандартов и страницы источников.
Используй инструмент retrieve_context для поиска информации в базе знаний.
Используй search_internet для получения актуальных данных о компаниях.
Отвечай на русском языке в официально-деловом стиле.
PROMPTEOF

# agents/prompts/finding_template.txt
cat > "$PROJECT_ROOT/agents/prompts/finding_template.txt" << 'FINDEOF'
Сгенерируй наблюдение аудита в следующем формате:

### Наблюдение {номер}: {заголовок}

**Состояние (Condition):**
{описание текущей ситуации}

**Критерий (Criteria):**
{ссылка на стандарт или нормативный документ}

**Причина (Cause):**
{корневая причина проблемы}

**Последствия (Consequence/Impact):**
{влияние на бизнес или риски}

**Риск (Risk Assessment):**
- Вероятность: {High/Medium/Low}
- Существенность: {High/Medium/Low}
- Общий уровень риска: {High/Medium/Low}

**Рекомендация (Recommendation):**
{конкретное действие}

**Ответственное подразделение:** {владелец}
**Срок устранения:** {дата или период}
FINDEOF

# agents/prompts/executive_summary.txt
cat > "$PROJECT_ROOT/agents/prompts/executive_summary.txt" << 'EXECEOF'
Составь Executive Summary для отчета об аудите.

Включи:
1. Краткое описание объекта аудита
2. Ключевые выводы (3-5 пунктов)
3. Общую оценку контрольной среды (Эффективная / Требует улучшения / Неэффективная)
4. Топ-3 критических риска
5. Общие рекомендации для руководства

Объем: 2-3 страницы текста.
EXECEOF

# knowledge/__init__.py
touch "$PROJECT_ROOT/knowledge/__init__.py"

# knowledge/document_registry.json
cat > "$PROJECT_ROOT/knowledge/document_registry.json" << 'REGEOF'
{}
REGEOF

# knowledge/fetcher.py
cat > "$PROJECT_ROOT/knowledge/fetcher.py" << 'FETCHEOF'
import os
import json
import hashlib
from pathlib import Path
from typing import Optional
from core.logger import setup_logger

class DocumentFetcher:
    def __init__(self, registry_path: str = None):
        if registry_path is None:
            registry_path = Path(__file__).parent / "document_registry.json"
        self.registry_path = Path(registry_path)
        self.raw_docs_path = Path(__file__).parent / "raw_docs"
        self.raw_docs_path.mkdir(exist_ok=True)
        self.logger = setup_logger("fetcher")
        self.registry = self._load_registry()
    
    def _load_registry(self) -> dict:
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_registry(self):
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    def get_or_fetch(self, query: str, doc_type: str) -> Optional[Path]:
        cache_key = hashlib.md5(f"{query}_{doc_type}".encode()).hexdigest()
        if cache_key in self.registry:
            cached_path = Path(self.registry[cache_key])
            if cached_path.exists():
                self.logger.info(f"Cache hit: {cached_path}")
                return cached_path
        self.logger.info(f"Cache miss: {query}")
        return None
FETCHEOF

# knowledge/indexer.py
cat > "$PROJECT_ROOT/knowledge/indexer.py" << 'INDEXEOF'
from pathlib import Path
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from core.config import EMBEDDING_MODEL, CHROMA_DB_PATH
from core.logger import setup_logger

class VectorIndexer:
    def __init__(self):
        self.logger = setup_logger("indexer")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def index_file(self, file_path: Path) -> int:
        self.logger.info(f"Indexing: {file_path}")
        if file_path.suffix.lower() == '.pdf':
            loader = PyPDFLoader(str(file_path))
        else:
            loader = TextLoader(str(file_path), encoding='utf-8')
        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)
        Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(CHROMA_DB_PATH)
        )
        return len(chunks)
INDEXEOF

# knowledge/retriever.py
cat > "$PROJECT_ROOT/knowledge/retriever.py" << 'RETREOF'
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from core.config import EMBEDDING_MODEL, CHROMA_DB_PATH
from core.logger import setup_logger

class Retriever:
    def __init__(self):
        self.logger = setup_logger("retriever")
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_store = Chroma(
            persist_directory=str(CHROMA_DB_PATH),
            embedding_function=self.embeddings
        )
    
    def retrieve(self, query: str, k: int = 5) -> list:
        self.logger.info(f"Retrieving for: {query[:50]}...")
        docs = self.vector_store.similarity_search(query, k=k)
        return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
RETREOF

# knowledge/embedder.py
cat > "$PROJECT_ROOT/knowledge/embedder.py" << 'EMBEDEOF'
from langchain_community.embeddings import HuggingFaceEmbeddings
from core.config import EMBEDDING_MODEL

def get_embedder():
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
EMBEDEOF

# knowledge/raw_docs/.gitkeep
touch "$PROJECT_ROOT/knowledge/raw_docs/.gitkeep"

# tools/__init__.py
touch "$PROJECT_ROOT/tools/__init__.py"

# tools/web_search.py
cat > "$PROJECT_ROOT/tools/web_search.py" << 'SEARCHEOF'
from core.logger import setup_logger

logger = setup_logger("web_search")

def search_urls(query: str, max_results: int = 3) -> list:
    logger.info(f"Searching: {query}")
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [r['href'] for r in results]
    except ImportError:
        logger.warning("duckduckgo-search not installed")
        return []
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []
SEARCHEOF

# tools/file_downloader.py
cat > "$PROJECT_ROOT/tools/file_downloader.py" << 'DOWNLOADEOF'
import requests
from pathlib import Path
from urllib.parse import urlparse
from core.logger import setup_logger

logger = setup_logger("downloader")

def download_file(url: str, dest_dir: Path) -> Path:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    parsed = urlparse(url)
    filename = Path(parsed.path).name or "document.txt"
    file_path = dest_dir / filename
    file_path.write_bytes(response.content)
    logger.info(f"Downloaded: {file_path}")
    return file_path
DOWNLOADEOF

# tools/risk_matrix.py
cat > "$PROJECT_ROOT/tools/risk_matrix.py" << 'RISKEOF'
def calculate_risk_level(probability: str, impact: str) -> str:
    matrix = {
        ('High', 'High'): 'Critical',
        ('High', 'Medium'): 'High',
        ('High', 'Low'): 'Medium',
        ('Medium', 'High'): 'High',
        ('Medium', 'Medium'): 'Medium',
        ('Medium', 'Low'): 'Low',
        ('Low', 'High'): 'Medium',
        ('Low', 'Medium'): 'Low',
        ('Low', 'Low'): 'Low',
    }
    return matrix.get((probability, impact), 'Medium')
RISKEOF

# tools/evidence_tracker.py
cat > "$PROJECT_ROOT/tools/evidence_tracker.py" << 'EVIDEOF'
import json
from pathlib import Path
from datetime import datetime

class EvidenceTracker:
    def __init__(self, task_dir: Path):
        self.evidence_file = task_dir / "evidence" / "evidence_log.json"
        self.evidence = self._load()
    
    def _load(self) -> list:
        if self.evidence_file.exists():
            return json.loads(self.evidence_file.read_text())
        return []
    
    def _save(self):
        self.evidence_file.write_text(json.dumps(self.evidence, indent=2, ensure_ascii=False))
    
    def add(self, source: str, content: str, relevance: str):
        self.evidence.append({
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "content": content,
            "relevance": relevance
        })
        self._save()
EVIDEOF

# report_generator/__init__.py
touch "$PROJECT_ROOT/report_generator/__init__.py"

# report_generator/orchestrator.py
cat > "$PROJECT_ROOT/report_generator/orchestrator.py" << 'ORCHEOF'
from pathlib import Path
from agents.cisa_auditor import CisaAuditor
from knowledge.retriever import Retriever
from core.logger import setup_logger

class ReportOrchestrator:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.auditor = CisaAuditor()
        self.retriever = Retriever()
        self.logger = setup_logger("orchestrator")
        self.drafts_dir = task_dir / "drafts"
        self.drafts_dir.mkdir(exist_ok=True)
    
    def generate(self, findings: list) -> Path:
        self.logger.info("Starting report generation")
        output_path = self.task_dir / "output" / "Audit_Report.md"
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text("# Отчет об аудите\n\nВ процессе генерации...", encoding='utf-8')
        return output_path
ORCHEOF

# report_generator/assembler.py
cat > "$PROJECT_ROOT/report_generator/assembler.py" << 'ASSEMEOF'
from pathlib import Path

class ReportAssembler:
    def __init__(self, drafts_dir: Path):
        self.drafts_dir = drafts_dir
    
    def assemble(self, output_path: Path) -> Path:
        chapters = sorted(self.drafts_dir.glob("*.md"))
        content = []
        for chapter in chapters:
            content.append(chapter.read_text(encoding='utf-8'))
            content.append("\n\n---\n\n")
        output_path.write_text("".join(content), encoding='utf-8')
        return output_path
ASSEMEOF

# report_generator/chapters/__init__.py
touch "$PROJECT_ROOT/report_generator/chapters/__init__.py"

for i in 00 01 02 03 04 05; do
    touch "$PROJECT_ROOT/report_generator/chapters/chapter_${i}_"*.py 2>/dev/null || true
done

# report_generator/templates/finding_card.md
cat > "$PROJECT_ROOT/report_generator/templates/finding_card.md" << 'CARDEOD'
### Наблюдение {index}: {title}

**Состояние (Condition):**
{condition}

**Критерий (Criteria):**
{criteria}

**Причина (Cause):**
{cause}

**Последствия (Consequence/Impact):**
{impact}

**Риск (Risk Assessment):**
- Вероятность: {risk_probability}
- Существенность: {risk_impact}
- Общий уровень риска: **{risk_level}**

**Рекомендация (Recommendation):**
{recommendation}

**Ответственное подразделение:** {owner}
**Срок устранения:** {deadline}

---
*Источники: {sources}*
CARDEOD

# report_generator/templates/risk_table.md
cat > "$PROJECT_ROOT/report_generator/templates/risk_table.md" << 'TABLEEOF'
| № | Риск | Вероятность | Влияние | Уровень | Владелец |
|---|------|-------------|---------|---------|----------|
{rows}
TABLEEOF

# tasks/__init__.py
touch "$PROJECT_ROOT/tasks/__init__.py"

# tasks/base_task.py
cat > "$PROJECT_ROOT/tasks/base_task.py" << 'TASKEOF'
from pathlib import Path
import yaml
from core.logger import setup_logger
from knowledge.fetcher import DocumentFetcher
from knowledge.indexer import VectorIndexer
from report_generator.orchestrator import ReportOrchestrator

class AuditTask:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.logger = setup_logger(f"task.{task_dir.name}")
        self.config = self._load_config()
        self.fetcher = DocumentFetcher()
        self.indexer = VectorIndexer()
        self.orchestrator = ReportOrchestrator(task_dir)
    
    def _load_config(self) -> dict:
        config_path = self.task_dir / "config.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return {}
    
    def execute(self):
        self.logger.info(f"Executing task: {self.config.get('name', 'unknown')}")
        findings = []
        self.orchestrator.generate(findings)
        self.logger.info("Task completed")
TASKEOF

# main.py
cat > "$PROJECT_ROOT/main.py" << 'MAINEOF'
#!/usr/bin/env python3
import click
from pathlib import Path
from datetime import datetime
import yaml

@click.group()
def cli():
    """DigitalAuditor Cleshnya - ИИ-аудитор CISA/CIA"""
    pass

@cli.command()
@click.option('--name', required=True, help='Название задачи')
@click.option('--company', required=True, help='Название компании')
@click.option('--sources', multiple=True, help='Источники')
@click.option('--audit-type', default='it', help='Тип аудита')
def create(name: str, company: str, sources: tuple, audit_type: str):
    task_dir = Path(f"tasks/instances/{name}")
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "evidence").mkdir(exist_ok=True)
    (task_dir / "drafts").mkdir(exist_ok=True)
    (task_dir / "output").mkdir(exist_ok=True)
    (task_dir / "evidence/.gitkeep").touch()
    
    config = {
        "name": name,
        "company": company,
        "audit_type": audit_type,
        "sources": list(sources),
        "created": datetime.now().isoformat()
    }
    (task_dir / "config.yaml").write_text(yaml.dump(config), encoding='utf-8')
    click.echo(f"[+] Задача '{name}' создана в {task_dir}")

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

@cli.command()
def list_tasks():
    instances_dir = Path("tasks/instances")
    if instances_dir.exists():
        for d in instances_dir.iterdir():
            if d.is_dir():
                click.echo(f"  - {d.name}")

if __name__ == "__main__":
    cli()
MAINEOF

# tests/__init__.py
touch "$PROJECT_ROOT/tests/__init__.py"

# tests/test_retriever.py
cat > "$PROJECT_ROOT/tests/test_retriever.py" << 'TESTREOF'
import pytest
from knowledge.retriever import Retriever

def test_retriever_init():
    retriever = Retriever()
    assert retriever is not None
TESTREOF

# tests/test_risk_matrix.py
cat > "$PROJECT_ROOT/tests/test_risk_matrix.py" << 'TESTRISKEOF'
import pytest
from tools.risk_matrix import calculate_risk_level

def test_critical_risk():
    assert calculate_risk_level('High', 'High') == 'Critical'

def test_low_risk():
    assert calculate_risk_level('Low', 'Low') == 'Low'
TESTRISKEOF

# tests/fixtures/sample_gogol.txt
cat > "$PROJECT_ROOT/tests/fixtures/sample_gogol.txt" << 'GOGOLFIXEOF'
Н.В. Гоголь. Мёртвые души (фрагмент)

В ворота гостиницы губернского города NN въехала довольно красивая рессорная
небольшая бричка, в какой ездят холостяки: отставные подполковники,
штабс-капитаны, помещики, имеющие около сотни душ крестьян, — словом, все те,
которых называют господами средней руки.
GOGOLFIXEOF

# scripts/setup_ollama.sh
cat > "$PROJECT_ROOT/scripts/setup_ollama.sh" << 'OLLAMASETUPEOF'
#!/bin/bash
echo "[*] Проверка Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "[-] Ollama не установлен. Установите с https://ollama.com"
    exit 1
fi
echo "[*] Загрузка Qwen2.5-0.5B-Instruct..."
ollama pull qwen2.5:0.5b-instruct
echo "[*] Создание модели digital-auditor-cisa..."
ollama create digital-auditor-cisa -f - << 'EOF'
FROM qwen2.5:0.5b-instruct
SYSTEM "Ты — старший ИТ-аудитор с сертификатами CISA и CIA. Отвечай на русском языке в официально-деловом стиле. Обязательно ссылайся на источники и стандарты."
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
EOF
echo "[+] Модель digital-auditor-cisa создана"
OLLAMASETUPEOF

# scripts/rebuild_index.py
cat > "$PROJECT_ROOT/scripts/rebuild_index.py" << 'REBUILDEOF'
#!/usr/bin/env python3
from pathlib import Path
from knowledge.indexer import VectorIndexer

def main():
    indexer = VectorIndexer()
    raw_docs = Path("knowledge/raw_docs")
    for file_path in raw_docs.glob("*"):
        if file_path.is_file() and file_path.name != ".gitkeep":
            chunks = indexer.index_file(file_path)
            print(f"Indexed {file_path.name}: {chunks} chunks")

if __name__ == "__main__":
    main()
REBUILDEOF

chmod +x "$PROJECT_ROOT/scripts/setup_ollama.sh"
chmod +x "$PROJECT_ROOT/scripts/rebuild_index.py"

echo ""
echo "========================================="
echo "[+] Проект создан в: $PROJECT_ROOT"
echo "========================================="
echo ""
echo "Следующие шаги:"
echo "  cd $PROJECT_ROOT"
echo "  python -m venv .venv"
echo "  source .venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  bash scripts/setup_ollama.sh"
echo ""