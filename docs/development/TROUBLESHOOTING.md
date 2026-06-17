# Troubleshooting Guide

Solutions for common operational issues in DigitalAuditor Cleshnya.

## Ollama Issues

### Ollama Not Available

**Error:**
```
Ollama is unavailable at http://localhost:11434
```

**Causes:**
- Ollama not installed
- Ollama not running
- Wrong base URL configured
- Network connectivity issues

**Solutions:**

1. **Install Ollama**:
   ```bash
   # macOS / Linux
   curl https://ollama.ai/install.sh | sh
   
   # Or download from https://ollama.ai
   ```

2. **Start Ollama**:
   ```bash
   ollama serve
   ```

3. **Verify Ollama is Running**:
   ```bash
   curl http://localhost:11434/api/tags
   # Should return JSON with available models
   ```

4. **Check Configuration**:
   ```bash
   echo $OLLAMA_BASE_URL
   # Should be http://localhost:11434
   ```

5. **Try Custom URL**:
   ```bash
   export OLLAMA_BASE_URL=http://your-server:11434
   python main.py run --task your_task
   ```

### Model Not Found

**Error:**
```
Model digital-auditor-cisa not found
```

**Solutions:**

1. **Pull the Model**:
   ```bash
   ollama pull digital-auditor-cisa
   ```

2. **List Available Models**:
   ```bash
   ollama list
   ```

3. **Check Model is Available**:
   ```bash
   curl http://localhost:11434/api/tags | jq '.models[] | .name'
   ```

4. **Use Alternative Model**:
   ```bash
   export OLLAMA_MODEL=mistral
   # or
   export OLLAMA_MODEL=neural-chat
   ```

### Ollama Timeout

**Error:**
```
Ollama request timed out (>30s)
```

**Causes:**
- Ollama server is slow
- Network latency
- Model is large
- System resources exhausted

**Solutions:**

1. **Increase Timeout**:
   ```bash
   export OLLAMA_TIMEOUT=60
   python main.py run --task your_task
   ```

2. **Check System Resources**:
   ```bash
   # Check memory usage
   free -h
   # Check GPU (if available)
   nvidia-smi
   ```

3. **Restart Ollama**:
   ```bash
   # Kill existing process
   pkill ollama
   
   # Wait a moment
   sleep 2
   
   # Restart
   ollama serve
   ```

4. **Use Smaller Model**:
   ```bash
   export OLLAMA_MODEL=phi
   # phi is much faster than larger models
   ```

## ChromaDB Issues

### ChromaDB Initialization Error

**Error:**
```
Failed to initialize vector store
```

**Solutions:**

1. **Clear Vector Store**:
   ```bash
   rm -rf chroma_db/
   rm -rf .chroma_test_db/
   ```

2. **Check Directory Permissions**:
   ```bash
   ls -la chroma_db/
   chmod 755 chroma_db/
   ```

3. **Rebuild Index**:
   ```bash
   python -c "
   from knowledge.indexer import VectorIndexer
   from pathlib import Path
   
   indexer = VectorIndexer()
   indexer.create_collection()
   print('Index rebuilt')
   "
   ```

4. **Check Disk Space**:
   ```bash
   df -h | grep /
   # Ensure enough space for embeddings
   ```

### Embedding Generation Fails

**Error:**
```
Embedding model load failed
```

**Solutions:**

1. **Download Embedding Model**:
   ```bash
   python -c "
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
   print('Model downloaded')
   "
   ```

2. **Check Memory**:
   ```bash
   # Embedder needs ~1GB RAM
   free -h
   ```

3. **Use Lighter Model**:
   ```bash
   # Edit core/config.py
   # Change EMBEDDING_MODEL to:
   # "sentence-transformers/all-MiniLM-L6-v2"
   ```

## Configuration Issues

### Invalid Configuration

**Error:**
```
Configuration error: Required field 'name' is missing
```

**Solutions:**

1. **Verify Environment Variables**:
   ```bash
   env | grep -i audit
   env | grep -i ollama
   env | grep -i log
   ```

2. **Check .env File**:
   ```bash
   cat .env | grep -v "^#" | grep -v "^$"
   ```

3. **Validate Configuration**:
   ```python
   from core.config import get_config
   config = get_config()
   if not config.validate():
       print("Invalid configuration")
   ```

4. **Reset to Defaults**:
   ```bash
   rm .env
   cp .env.example .env
   ```

### Wrong Profile Loading

**Error:**
```
Unexpected logging level or LLM configuration
```

**Solutions:**

1. **Check Current Profile**:
   ```bash
   echo $AUDIT_PROFILE
   # Should be: testing, production, or development
   ```

2. **Set Correct Profile**:
   ```bash
   export AUDIT_PROFILE=production
   ```

3. **View Profile Configuration**:
   ```python
   from core.config import create_config
   config = create_config("development")
   print(f"Profile: {config.profile}")
   print(f"Log Level: {config.logging.log_level}")
   print(f"Ollama URL: {config.ollama.base_url}")
   ```

## Logging Issues

### Logs Not Appearing

**Error:**
```
No output in audit.log or console
```

**Solutions:**

1. **Check Log Level**:
   ```bash
   export LOG_LEVEL=INFO
   ```

2. **Verify Log File Path**:
   ```bash
   cat $LOG_FILE
   # or
   tail -f audit.log
   ```

3. **Create Logs Directory**:
   ```bash
   mkdir -p logs/
   chmod 755 logs/
   ```

4. **Check Permissions**:
   ```bash
   ls -la audit.log
   # Should be writable by current user
   ```

### JSON Logs Not Generated

**Error:**
```
logs/audit.json not created
```

**Solutions:**

1. **Enable JSON Output**:
   ```bash
   export LOG_JSON=true
   ```

2. **Check Directory**:
   ```bash
   mkdir -p logs/
   ls -la logs/
   ```

3. **Verify Configuration**:
   ```python
   from core.config import get_config
   config = get_config("development")
   print(config.logging.json_output)
   print(config.logging.json_file)
   ```

## Task Execution Issues

### Task Not Found

**Error:**
```
Audit task 'my_audit' not found
```

**Solutions:**

1. **List Available Tasks**:
   ```bash
   python main.py list-tasks
   ```

2. **Create Task**:
   ```bash
   python main.py create \
     --name my_audit \
     --company "My Company" \
     --audit-type it
   ```

3. **Check Directory**:
   ```bash
   ls -la tasks/instances/
   ```

### Task Fails During Execution

**Error:**
```
Task execution failed: [details]
```

**Solutions:**

1. **Check Task Configuration**:
   ```bash
   cat tasks/instances/my_audit/config.yaml
   ```

2. **Verify Sources**:
   ```bash
   # Ensure all sources are valid
   ls -la tasks/instances/my_audit/
   ```

3. **Run with Debug Logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   python main.py run --task my_audit
   ```

4. **Check for Validation Errors**:
   ```python
   from core.validator import InputValidator
   import yaml
   
   config = yaml.safe_load(
       open("tasks/instances/my_audit/config.yaml")
   )
   result = InputValidator.validate_task_config(config)
   for error in result.errors:
       print(f"{error.field}: {error.message}")
   ```

## Import Errors

### ModuleNotFoundError

**Error:**
```
ModuleNotFoundError: No module named 'core'
```

**Causes:**
- Package not installed
- Virtual environment not activated
- PYTHONPATH not set

**Solutions:**

1. **Install Package**:
   ```bash
   pip install -e .
   ```

2. **Activate Virtual Environment**:
   ```bash
   source .venv/bin/activate
   ```

3. **Check Python Path**:
   ```bash
   python -c "import sys; print('\n'.join(sys.path))"
   ```

4. **Verify Installation**:
   ```bash
   python -c "import core; print(core.__file__)"
   ```

### Circular Imports

**Error:**
```
ImportError: cannot import name 'X' from partially initialized module 'Y'
```

**Solutions:**

1. **Check for Circular Dependencies**:
   ```bash
   grep -r "from core" core/
   grep -r "from agents" agents/
   ```

2. **Use Late Imports**:
   ```python
   # ❌ Problematic
   from agents.cisa_auditor import CisaAuditor
   
   # ✅ Better
   def my_function():
       from agents.cisa_auditor import CisaAuditor
       return CisaAuditor()
   ```

## Testing Issues

### Tests Fail Locally but Pass in CI

**Causes:**
- Different Python versions
- Different dependency versions
- Environment-specific issues
- Timing-dependent tests

**Solutions:**

1. **Match CI Environment**:
   ```bash
   python --version  # Check Python 3.12
   pip list | grep pytest  # Check versions
   ```

2. **Run Tests in Verbose Mode**:
   ```bash
   pytest -v --tb=short tests/
   ```

3. **Check for Timing Issues**:
   ```python
   import time
   
   @pytest.mark.timeout(10)
   def test_timing_sensitive():
       start = time.time()
       # Test code
       assert time.time() - start < 5
   ```

### Fixture Not Found

**Error:**
```
fixture 'mock_ollama_llm' not found
```

**Solutions:**

1. **Verify conftest.py Location**:
   ```bash
   ls tests/conftest.py
   ```

2. **Check Fixture Definition**:
   ```bash
   grep -n "def mock_ollama_llm" tests/conftest.py
   ```

3. **List Available Fixtures**:
   ```bash
   pytest --fixtures tests/ | grep mock_
   ```

## Performance Issues

### Slow Audit Execution

**Causes:**
- Large document corpus
- Slow Ollama responses
- Network latency
- System resource constraints

**Solutions:**

1. **Profile Execution**:
   ```bash
   export LOG_JSON=true
   # Run audit
   python main.py run --task my_audit
   # Analyze timing
   python -c "
   import json
   with open('logs/audit.json') as f:
       for line in f:
           log = json.loads(line)
           if 'duration_ms' in log:
               print(f'{log[\"stage\"]}: {log[\"duration_ms\"]}ms')
   "
   ```

2. **Reduce Document Corpus**:
   ```bash
   # Create smaller task
   python main.py create --name small_audit --company Test --audit-type it
   # Add fewer documents
   ```

3. **Optimize Configuration**:
   ```bash
   # Use faster model
   export OLLAMA_MODEL=phi
   
   # Reduce chunk size
   # Edit core/config.py: chunk_size=250
   ```

4. **Check System Resources**:
   ```bash
   top
   # or
   htop
   ```

## Security Issues

### Sensitive Data in Logs

**Problem:**
```
API keys or passwords appearing in audit.log
```

**Solutions:**

1. **Check Log Contents**:
   ```bash
   grep -i "key\|password\|token" audit.log
   ```

2. **Sanitize Logging**:
   ```python
   # ❌ Bad
   logger.info(f"Ollama URL: {OLLAMA_BASE_URL}")
   
   # ✅ Good
   logger.info("Ollama configured")
   logger.debug(f"Base URL: {OLLAMA_BASE_URL.split('://')[0]}://...")
   ```

3. **Rotate Logs**:
   ```bash
   # Archive old logs
   mv audit.log audit.log.$(date +%Y%m%d)
   gzip audit.log.*
   ```

## Getting Help

### Collect Debug Information

When reporting issues, include:

```bash
# Python and package versions
python --version
pip list | grep -E "pytest|ollama|langchain|chromadb"

# Environment variables
env | grep -E "AUDIT|OLLAMA|LOG"

# Log contents
head -100 audit.log
head -20 logs/audit.json

# Task configuration
cat tasks/instances/your_task/config.yaml

# System info
uname -a
free -h
```

### Report Issues

1. **Check Existing Issues**: https://github.com/your-org/DigitalAuditor_Cleshnya/issues
2. **Create New Issue** with:
   - Clear error message
   - Steps to reproduce
   - Debug information collected above
   - Expected vs actual behavior

### Seek Help

- **Documentation**: Read [README.md](../../README.md) and [CLAUDE.md](../../CLAUDE.md)
- **Logging Guide**: See [LOGGING_GUIDE.md](LOGGING_GUIDE.md)
- **Testing Guide**: See [TESTING.md](TESTING.md)
- **Email**: support@your-org.com

---

**Last Updated**: 2026-04-20
