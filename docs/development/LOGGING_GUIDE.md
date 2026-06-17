# Logging Guide

Comprehensive guide to structured logging in DigitalAuditor Cleshnya.

## Overview

The logging system provides structured output for both human consumption (console/files) and machine analysis (JSON for process mining).

### Key Features

- **Dual Output**: Text logs for humans, JSON for analysis
- **Contextual Information**: Module, class, method, line number
- **Stage Tracking**: [STAGE START] / [STAGE END] markers with duration
- **Performance Metrics**: Duration tracking, memory usage, bottleneck analysis
- **Process Mining**: JSON logs for audit trail and performance analysis

## Basic Usage

### Getting a Logger

```python
from core.logger import setup_logger

# Get logger for your module
logger = setup_logger("agents.cisa_auditor")

# Log messages
logger.info("Audit started")
logger.warning("Low memory available")
logger.error("Ollama unavailable", exc_info=True)
```

### Logger Naming Convention

Use dot-separated names following module hierarchy:

```python
# In agents/cisa_auditor.py
logger = setup_logger("agents.cisa_auditor")

# In tasks/base_task.py
logger = setup_logger("tasks.base_task")

# For instance tracking
logger = setup_logger(f"task.{task_name}")
```

## Advanced Features

### 1. Stage-Based Logging with LogContext

Track audit stages with automatic start/end logging and duration measurement:

```python
from core.logging_utils import LogContext
from core.logger import setup_logger

logger = setup_logger("audit.execution")

def execute_audit():
    # Document fetch stage
    with LogContext(logger, "document_fetch", source_count=5):
        # Fetch documents
        pass
    
    # Indexing stage
    with LogContext(logger, "vector_indexing", chunk_count=100):
        # Index documents
        pass
    
    # Analysis stage
    with LogContext(logger, "llm_analysis", model="digital-auditor-cisa"):
        # Run analysis
        pass
```

**Output:**
```
2026-04-20 15:30:45.123 | INFO | audit.execution.execute_audit | [STAGE START] document_fetch
2026-04-20 15:30:48.456 | INFO | audit.execution.execute_audit | [STAGE END] document_fetch - 3333ms
2026-04-20 15:30:48.457 | INFO | audit.execution.execute_audit | [STAGE START] vector_indexing
2026-04-20 15:30:52.789 | INFO | audit.execution.execute_audit | [STAGE END] vector_indexing - 4332ms
```

### 2. JSON Output for Process Mining

Enable JSON output for automated analysis:

```python
from core.logger import setup_logger

# Enable JSON output
logger = setup_logger("audit", json_output=True)

logger.info("Starting audit")
# Outputs to both:
# - audit.log (text format)
# - logs/audit.json (JSON format for analysis)
```

**JSON Output Sample:**
```json
{
  "timestamp": "2026-04-20T15:30:45.123000",
  "level": "INFO",
  "logger": "audit.execution",
  "message": "Starting audit",
  "module": "base_task",
  "function": "execute",
  "lineno": 42,
  "stage": "document_fetch",
  "duration_ms": 3333
}
```

### 3. Performance Tracking with PipelineTimer

Track execution time across multiple stages:

```python
from core.logging_utils import PipelineTimer
from core.logger import setup_logger

logger = setup_logger("performance")
timer = PipelineTimer()

# Track stages
timer.record("fetch", 1234)  # 1234ms
timer.record("index", 5678)  # 5678ms
timer.record("fetch", 1100)  # Second fetch

# Generate report
logger.info(timer.report())
```

**Output:**
```
Pipeline Timing Report:
==================================================
fetch                                    | count=2   | avg=1167.0ms | total=2334ms
index                                    | count=1   | avg=5678.0ms | total=5678ms
```

### 4. Memory Tracking

Monitor memory usage during audit:

```python
from core.logging_utils import MemoryTracker
from core.logger import setup_logger

logger = setup_logger("memory")
tracker = MemoryTracker(logger)

# Log memory at key points
tracker.log_memory_usage("before_indexing")

# ... perform indexing ...

tracker.log_memory_usage("after_indexing")
```

**Output:**
```
Memory usage before_indexing: 234.5MB (12.3%)
Memory usage after_indexing: 567.8MB (23.4%)
```

### 5. Bottleneck Analysis

Identify slowest stages:

```python
from core.logging_utils import PipelineTimer, BottleneckAnalyzer
from core.logger import setup_logger

logger = setup_logger("bottleneck")
timer = PipelineTimer()

# Record multiple stages...
timer.record("fetch", 100)
timer.record("index", 5000)
timer.record("analyze", 3000)

# Analyze bottlenecks
analyzer = BottleneckAnalyzer(timer)
logger.info(analyzer.report())
```

**Output:**
```
Performance Bottleneck Analysis:
==================================================
1. index                                  5000.0ms
2. analyze                                3000.0ms
3. fetch                                   100.0ms
```

### 6. Metrics Export

Export performance metrics for external analysis:

```python
from core.logging_utils import PipelineTimer, MetricsExporter

timer = PipelineTimer()
# Record stages...

exporter = MetricsExporter(timer)
exporter.export_json("metrics.json")      # JSON format
exporter.export_csv("metrics.csv")        # CSV format
```

**CSV Output:**
```
stage_name,count,total_ms,avg_ms,min_ms,max_ms
fetch,2,2334.0,1167.0,1100.0,1234.0
index,1,5678.0,5678.0,5678.0,5678.0
analyze,1,3000.0,3000.0,3000.0,3000.0
```

## Configuration

### Environment Variables

```bash
# Logging level
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Log file path
LOG_FILE=audit.log

# Enable JSON output
LOG_JSON=true

# Log file for JSON (auto-generated if LOG_JSON=true)
# logs/audit.json (by default)
```

### Profile-Based Logging

Logging behavior varies by profile:

| Profile | Level | JSON | Use Case |
|---------|-------|------|----------|
| **testing** | WARNING | No | Unit tests (minimal noise) |
| **development** | DEBUG | Yes | Local development (verbose) |
| **production** | INFO | No | Deployed audits (critical only) |

```python
from core.config import get_config

config = get_config("development")
# LOG_LEVEL=DEBUG, LOG_JSON=true
```

## Best Practices

### 1. Use Contextual Logger Names

❌ **Bad:**
```python
logger = setup_logger("log")
```

✅ **Good:**
```python
logger = setup_logger("agents.cisa_auditor")
```

### 2. Log at Appropriate Levels

```python
logger.debug("Detailed variable state")           # Debugging info
logger.info("Audit stage completed")              # Important events
logger.warning("Ollama response slow (5s)")       # Potential issues
logger.error("Failed to fetch documents", exc_info=True)  # Failures
```

### 3. Use LogContext for All Stages

```python
# ❌ Bad: No stage tracking
def execute():
    logger.info("Starting")
    fetch_documents()
    logger.info("Fetching done")

# ✅ Good: Clear stage boundaries
def execute():
    with LogContext(logger, "document_fetch"):
        fetch_documents()
```

### 4. Include Metrics in Context Manager

```python
# Pass relevant metrics to LogContext
with LogContext(logger, "vector_indexing", 
                chunk_size=500, 
                document_count=42):
    index_documents()
```

### 5. Don't Log Sensitive Data

```python
# ❌ Bad: Logs API keys
logger.info(f"Connecting to Ollama: {OLLAMA_BASE_URL}")

# ✅ Good: Safe logging
logger.info("Connecting to Ollama")
logger.debug(f"Base URL: {OLLAMA_BASE_URL.split('://')[0]}://...")
```

## Troubleshooting

### Logs Not Appearing

1. Check LOG_LEVEL environment variable:
```bash
export LOG_LEVEL=DEBUG
```

2. Verify logger is configured:
```python
from core.logger import setup_logger
logger = setup_logger("my_module")
logger.info("This should appear")
```

3. Check file permissions:
```bash
ls -la audit.log
tail -f audit.log
```

### JSON Logs Not Generated

1. Ensure LOG_JSON is enabled:
```bash
export LOG_JSON=true
```

2. Check logs directory exists:
```bash
mkdir -p logs/
```

3. Verify JSON file is created:
```bash
tail -f logs/audit.json
```

### Performance Analysis

1. Extract timing data from JSON logs:
```bash
cat logs/audit.json | grep "duration_ms"
```

2. Generate bottleneck report:
```python
from core.logging_utils import PipelineTimer, BottleneckAnalyzer
# Process JSON logs and build timer
analyzer = BottleneckAnalyzer(timer)
print(analyzer.report())
```

## Integration with Process Mining

JSON logs are designed for process mining tools:

1. **ELK Stack** (Elasticsearch, Logstash, Kibana):
   - Send JSON logs to Logstash
   - Index in Elasticsearch
   - Visualize in Kibana

2. **Splunk**:
   - Configure JSON input
   - Create searches for audit stages
   - Build dashboards

3. **Custom Analysis**:
   ```python
   import json
   
   with open("logs/audit.json") as f:
       for line in f:
           log = json.loads(line)
           if log.get("stage"):
               print(f"{log['stage']}: {log['duration_ms']}ms")
   ```

## Examples

### Complete Audit with Logging

```python
from core.logger import setup_logger
from core.logging_utils import LogContext, PipelineTimer
from tasks.base_task import AuditTask
from pathlib import Path

logger = setup_logger("audit.main")
timer = PipelineTimer()

def run_audit(task_name: str):
    logger.info(f"Starting audit: {task_name}")
    
    task_dir = Path(f"tasks/instances/{task_name}")
    
    try:
        with LogContext(logger, "audit_initialization", task=task_name):
            task = AuditTask(task_dir)
        
        with LogContext(logger, "audit_execution"):
            task.execute()
        
        logger.info(f"Audit completed: {task_name}")
        
    except Exception as e:
        logger.error(f"Audit failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_audit("security_audit_2026")
```

### Performance Report Generation

```python
from core.logging_utils import PipelineTimer, MetricsExporter
from core.logger import setup_logger

logger = setup_logger("metrics")
timer = PipelineTimer()

# Simulate audit stages
stages = [
    ("fetch", 1500),
    ("index", 4200),
    ("analyze", 8900),
    ("report", 2100),
]

for stage, duration in stages:
    timer.record(stage, duration)

# Generate reports
logger.info(timer.report())
logger.info("\n" + "="*50)

from core.logging_utils import BottleneckAnalyzer
analyzer = BottleneckAnalyzer(timer)
logger.info(analyzer.report())

# Export metrics
exporter = MetricsExporter(timer)
exporter.export_json("metrics.json")
exporter.export_csv("metrics.csv")
```

## API Reference

### setup_logger()

```python
def setup_logger(name: str, json_output: bool = False) -> logging.Logger
```

Initialize logger with dual handlers (text + optional JSON).

**Parameters:**
- `name` (str): Logger name (e.g., "agents.cisa_auditor")
- `json_output` (bool): Enable JSON file output for process mining

**Returns:**
- Configured `logging.Logger` instance

### LogContext

```python
with LogContext(logger, stage_name, **metrics):
    # Code to track
    pass
```

Context manager for stage tracking.

**Parameters:**
- `logger`: Logger instance
- `stage_name` (str): Audit stage name
- `**metrics`: Additional metrics (optional)

### PipelineTimer

```python
timer = PipelineTimer()
timer.record(stage_name, duration_ms)
stats = timer.get_stats(stage_name)
report = timer.report()
```

Track and report on stage execution times.

### MemoryTracker

```python
tracker = MemoryTracker(logger)
tracker.log_memory_usage(stage_name)
```

Monitor memory usage with automatic reporting.

### BottleneckAnalyzer

```python
analyzer = BottleneckAnalyzer(timer)
bottlenecks = analyzer.find_bottlenecks(top_n=5)
report = analyzer.report()
```

Identify slowest audit stages.

### MetricsExporter

```python
exporter = MetricsExporter(timer)
exporter.export_json(filepath)
exporter.export_csv(filepath)
```

Export performance metrics for external analysis.

## Related Documentation

- [CLAUDE.md](../../CLAUDE.md) — Project overview
- [README.md](../../README.md) — Quick start and API reference
- [TESTING.md](TESTING.md) — Test writing guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Operational issues

---

**Last Updated**: 2026-04-20
