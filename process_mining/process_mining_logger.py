#!/usr/bin/env python3
"""
Process Mining Logger для отслеживания работы AI агента
Ведет логи в форматах JSON и plain text
"""

import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid


class ProcessEvent:
    """Базовый класс для события процесса"""
    
    def __init__(self, 
                 process_name: str,
                 stage: str,
                 start_time: datetime,
                 end_time: Optional[datetime] = None,
                 duration: Optional[timedelta] = None,
                 author: str = "AI_Agent_Lisa",
                 character: str = "DigitalAuditor",
                 data: Optional[Dict[str, Any]] = None,
                 event_id: Optional[str] = None):
        
        self.event_id = event_id or str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.process_name = process_name
        self.stage = stage
        self.start_time = start_time
        self.end_time = end_time or datetime.now()
        self.duration = duration or (self.end_time - self.start_time)
        self.author = author
        self.character = character
        self.data = data or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует событие в словарь для JSON"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "date": self.timestamp.strftime("%Y-%m-%d"),
            "time": self.timestamp.strftime("%H:%M:%S"),
            "process_name": self.process_name,
            "stage": self.stage,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration.total_seconds(),
            "duration_formatted": str(self.duration),
            "author": self.author,
            "character": self.character,
            "additional_data": self.data
        }
    
    def to_text_line(self) -> str:
        """Преобразует событие в строку для plain text лога"""
        return (f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"{self.process_name} | "
                f"{self.stage} | "
                f"{self.start_time.strftime('%H:%M:%S')} - {self.end_time.strftime('%H:%M:%S')} | "
                f"{self.duration} | "
                f"{self.author} | "
                f"{self.character} | "
                f"{self.data}")


class ProcessMiningLogger:
    """Основной класс для логирования процессов"""
    
    def __init__(self, log_dir: str = "process_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.events: List[ProcessEvent] = []
        
        # Файлы для логов
        self.json_log_file = self.log_dir / "process_mining_log.json"
        self.text_log_file = self.log_dir / "process_mining_log.txt"
        self.csv_log_file = self.log_dir / "process_mining_log.csv"
        
    def log_event(self, 
                  process_name: str,
                  stage: str,
                  start_time: datetime,
                  end_time: Optional[datetime] = None,
                  author: str = "AI_Agent_Lisa",
                  character: str = "DigitalAuditor",
                  data: Optional[Dict[str, Any]] = None) -> ProcessEvent:
        
        """Добавляет событие в лог"""
        event = ProcessEvent(
            process_name=process_name,
            stage=stage,
            start_time=start_time,
            end_time=end_time,
            author=author,
            character=character,
            data=data
        )
        
        self.events.append(event)
        return event
    
    def log_process_start(self, 
                          process_name: str,
                          author: str = "AI_Agent_Lisa",
                          character: str = "DigitalAuditor",
                          data: Optional[Dict[str, Any]] = None) -> ProcessEvent:
        
        """Логирует начало процесса"""
        return self.log_event(
            process_name=process_name,
            stage="START",
            start_time=datetime.now(),
            author=author,
            character=character,
            data=data
        )
    
    def log_process_end(self,
                        process_name: str,
                        start_event: ProcessEvent,
                        author: str = "AI_Agent_Lisa",
                        character: str = "DigitalAuditor",
                        data: Optional[Dict[str, Any]] = None) -> ProcessEvent:
        
        """Логирует завершение процесса"""
        return self.log_event(
            process_name=process_name,
            stage="END",
            start_time=start_event.start_time,
            end_time=datetime.now(),
            author=author,
            character=character,
            data=data
        )
    
    def save_to_json(self):
        """Сохраняет логи в JSON формате"""
        events_data = [event.to_dict() for event in self.events]
        
        log_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_events": len(self.events),
                "log_version": "1.0",
                "format": "process_mining_json"
            },
            "events": events_data
        }
        
        with open(self.json_log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    def save_to_text(self):
        """Сохраняет логи в plain text формате"""
        with open(self.text_log_file, 'w', encoding='utf-8') as f:
            f.write("PROCESS MINING LOG - AI AGENT WORK TRACKING\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Events: {len(self.events)}\n")
            f.write("=" * 60 + "\n\n")
            
            for event in self.events:
                f.write(event.to_text_line() + "\n")
    
    def save_to_csv(self):
        """Сохраняет логи в CSV формате для анализа"""
        with open(self.csv_log_file, 'w', newline='', encoding='utf-8') as f:
            if self.events:
                fieldnames = [
                    'event_id', 'timestamp', 'date', 'time',
                    'process_name', 'stage', 'start_time', 'end_time',
                    'duration_seconds', 'duration_formatted', 'author', 'character',
                    'additional_data'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for event in self.events:
                    event_dict = event.to_dict()
                    event_dict['additional_data'] = json.dumps(event_dict.get('additional_data', {}))
                    writer.writerow(event_dict)
    
    def save_all_formats(self):
        """Сохраняет логи во всех форматах"""
        self.save_to_json()
        self.save_to_text()
        self.save_to_csv()
        
        return {
            "json_file": str(self.json_log_file),
            "text_file": str(self.text_log_file),
            "csv_file": str(self.csv_log_file),
            "events_count": len(self.events)
        }
    
    def get_process_summary(self) -> Dict[str, Any]:
        """Возвращает сводку по процессам"""
        process_counts = {}
        total_duration = timedelta(0)
        
        for event in self.events:
            process_counts[event.process_name] = process_counts.get(event.process_name, 0) + 1
            total_duration += event.duration
        
        return {
            "total_events": len(self.events),
            "unique_processes": len(process_counts),
            "process_counts": process_counts,
            "total_duration": str(total_duration),
            "average_event_duration": str(total_duration / len(self.events)) if self.events else "0:00:00"
        }


# Пример использования
if __name__ == "__main__":
    # Создаем логгер
    logger = ProcessMiningLogger()
    
    # Логируем создание GitHub репозитория
    repo_start = logger.log_process_start(
        process_name="GitHub_Repository_Creation",
        data={"repository_name": "DigitalAuditor_Cleshnya", "task_type": "Public repository creation"}
    )
    
    # Логируем промежуточные этапы
    logger.log_event(
        process_name="GitHub_Repository_Creation",
        stage="Local_Repository_Setup",
        start_time=repo_start.start_time,
        end_time=datetime.now(),
        data={"status": "completed", "files_created": ["README.md", ".git/"]}
    )
    
    repo_end = logger.log_process_end(
        process_name="GitHub_Repository_Creation",
        start_event=repo_start,
        data={"status": "ready_for_publication", "missing_auth": True}
    )
    
    # Логируем создание Process Mining системы
    pm_start = logger.log_process_start(
        process_name="Process_Mining_System_Creation",
        data={"system_type": "AI_agent_logging", "formats": ["JSON", "Text", "CSV"]}
    )
    
    # Сохраняем все логи
    files_info = logger.save_all_formats()
    summary = logger.get_process_summary()
    
    print("✅ Process Mining система создана!")
    print(f"📊 Всего событий: {summary['total_events']}")
    print(f"📁 Файлы созданы: {files_info}")
    print(f"⏱️ Общая продолжительность: {summary['total_duration']}")