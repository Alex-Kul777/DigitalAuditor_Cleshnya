#!/usr/bin/env python3
"""
Process Mining Logger - AI Agent Work Tracking System

Система логирования процессов AI агента в соответствии с принципами Process Mining.
Поддерживает экспорт в форматы JSON, plain text и CSV для последующего анализа.

Основные компоненты:
- ProcessEvent: Базовый класс для события процесса
- ProcessMiningLogger: Основной класс для логирования и экспорта

Форматы экспорта:
- JSON: Структурированные данные с метаинформацией
- Plain Text: Человекочитаемые логи с разделителями
- CSV: Табличные данные для анализа в Excel/Python

Пример использования:
    from process_mining_logger import ProcessMiningLogger
    
    logger = ProcessMiningLogger()
    
    # Логирование процесса
    start_event = logger.log_process_start("My_Process")
    # ... выполнение работы ...
    end_event = logger.log_process_end("My_Process", start_event)
    
    # Экспорт во все форматы
    files = logger.save_all_formats()
    
Автор: AI Agent Lisa
Дата: 2026-04-20
Версия: 1.0
"""

from .process_mining_logger import ProcessEvent, ProcessMiningLogger

__version__ = "1.0.0"
__author__ = "AI Agent Lisa"
__description__ = "Process Mining Logger для отслеживания работы AI агента"

__all__ = [
    'ProcessEvent',
    'ProcessMiningLogger'
]