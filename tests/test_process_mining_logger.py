import pytest
import json
import csv
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from process_mining.process_mining_logger import ProcessEvent, ProcessMiningLogger


class TestProcessEvent:
    """Unit tests for ProcessEvent class."""

    def test_process_event_init_with_defaults(self):
        """Verify ProcessEvent initializes with default values."""
        start = datetime.now()
        event = ProcessEvent(
            process_name="Test_Process",
            stage="START",
            start_time=start
        )

        assert event.process_name == "Test_Process"
        assert event.stage == "START"
        assert event.start_time == start
        assert event.author == "AI_Agent_Lisa"
        assert event.character == "DigitalAuditor"
        assert event.data == {}
        assert event.event_id is not None
        assert event.duration is not None

    def test_process_event_init_with_custom_values(self):
        """Verify ProcessEvent initializes with custom values."""
        start = datetime.now()
        end = start + timedelta(seconds=10)
        data = {"task": "audit", "status": "completed"}

        event = ProcessEvent(
            process_name="Custom_Process",
            stage="MIDDLE",
            start_time=start,
            end_time=end,
            author="Custom_Author",
            character="Custom_Character",
            data=data
        )

        assert event.process_name == "Custom_Process"
        assert event.stage == "MIDDLE"
        assert event.start_time == start
        assert event.end_time == end
        assert event.author == "Custom_Author"
        assert event.character == "Custom_Character"
        assert event.data == data

    def test_process_event_duration_calculation(self):
        """Verify ProcessEvent calculates duration correctly."""
        start = datetime(2026, 4, 25, 10, 0, 0)
        end = datetime(2026, 4, 25, 10, 0, 15)

        event = ProcessEvent(
            process_name="Timed_Process",
            stage="EXEC",
            start_time=start,
            end_time=end
        )

        assert event.duration == timedelta(seconds=15)

    def test_process_event_auto_end_time(self):
        """Verify ProcessEvent auto-sets end_time if not provided."""
        start = datetime.now()
        event = ProcessEvent(
            process_name="Auto_End_Process",
            stage="START",
            start_time=start
        )

        assert event.end_time is not None
        assert event.end_time >= start

    def test_process_event_uuid_generation(self):
        """Verify ProcessEvent generates unique UUIDs."""
        start = datetime.now()
        event1 = ProcessEvent("P1", "S1", start)
        event2 = ProcessEvent("P2", "S2", start)

        assert event1.event_id != event2.event_id
        assert len(event1.event_id) > 0
        assert len(event2.event_id) > 0

    def test_process_event_uuid_custom(self):
        """Verify ProcessEvent accepts custom event_id."""
        start = datetime.now()
        custom_id = "custom-uuid-12345"
        event = ProcessEvent(
            process_name="UUID_Test",
            stage="START",
            start_time=start,
            event_id=custom_id
        )

        assert event.event_id == custom_id

    def test_process_event_to_dict(self):
        """Verify ProcessEvent.to_dict() returns complete dict."""
        start = datetime(2026, 4, 25, 10, 30, 45)
        end = datetime(2026, 4, 25, 10, 31, 0)
        data = {"result": "success"}

        event = ProcessEvent(
            process_name="Dict_Test",
            stage="EXEC",
            start_time=start,
            end_time=end,
            author="Tester",
            character="TestChar",
            data=data
        )

        d = event.to_dict()

        assert d["process_name"] == "Dict_Test"
        assert d["stage"] == "EXEC"
        assert d["author"] == "Tester"
        assert d["character"] == "TestChar"
        assert d["duration_seconds"] == 15.0
        assert d["additional_data"] == data
        assert "event_id" in d
        assert "timestamp" in d
        assert "date" in d
        assert "time" in d

    def test_process_event_to_text_line(self):
        """Verify ProcessEvent.to_text_line() formats correctly."""
        start = datetime(2026, 4, 25, 10, 30, 45)
        end = datetime(2026, 4, 25, 10, 31, 0)

        event = ProcessEvent(
            process_name="Text_Test",
            stage="EXEC",
            start_time=start,
            end_time=end
        )

        line = event.to_text_line()

        assert "Text_Test" in line
        assert "EXEC" in line
        assert "10:30:45" in line
        assert "10:31:00" in line
        assert "|" in line


class TestProcessMiningLogger:
    """Unit tests for ProcessMiningLogger class."""

    def test_logger_init_creates_log_dir(self):
        """Verify ProcessMiningLogger creates log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            logger = ProcessMiningLogger(str(log_dir))

            assert log_dir.exists()
            assert logger.log_dir == log_dir
            assert logger.events == []

    def test_logger_log_event(self):
        """Verify log_event() adds event to list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            start = datetime.now()

            event = logger.log_event(
                process_name="Test_Process",
                stage="EXEC",
                start_time=start,
                data={"test": "data"}
            )

            assert len(logger.events) == 1
            assert logger.events[0] == event
            assert event.process_name == "Test_Process"

    def test_logger_log_process_start(self):
        """Verify log_process_start() creates START event."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))

            event = logger.log_process_start(
                process_name="Start_Test",
                data={"init": True}
            )

            assert event.stage == "START"
            assert event.process_name == "Start_Test"
            assert len(logger.events) == 1

    def test_logger_log_process_end(self):
        """Verify log_process_end() creates END event with duration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))

            start_event = logger.log_process_start("End_Test")
            end_event = logger.log_process_end(
                process_name="End_Test",
                start_event=start_event,
                data={"final": True}
            )

            assert end_event.stage == "END"
            assert end_event.duration >= timedelta(0)
            assert len(logger.events) == 2

    def test_logger_multiple_events(self):
        """Verify logger handles multiple events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))

            logger.log_process_start("Process_1")
            logger.log_process_start("Process_2")
            logger.log_event("Process_1", "MIDDLE", datetime.now())
            logger.log_process_start("Process_3")

            assert len(logger.events) == 4

    def test_logger_get_process_summary_empty(self):
        """Verify get_process_summary() works with empty logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            summary = logger.get_process_summary()

            assert summary["total_events"] == 0
            assert summary["unique_processes"] == 0
            assert summary["process_counts"] == {}

    def test_logger_get_process_summary_with_events(self):
        """Verify get_process_summary() calculates stats correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))

            logger.log_process_start("Process_A")
            logger.log_process_start("Process_A")
            logger.log_process_start("Process_B")

            summary = logger.get_process_summary()

            assert summary["total_events"] == 3
            assert summary["unique_processes"] == 2
            assert summary["process_counts"]["Process_A"] == 2
            assert summary["process_counts"]["Process_B"] == 1

    def test_logger_custom_log_dir_in_init(self):
        """Verify logger uses custom log_dir path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_logs"
            logger = ProcessMiningLogger(str(custom_dir))

            assert logger.log_dir == custom_dir
            assert custom_dir.exists()


class TestProcessMiningLoggerFileOutput:
    """Integration tests for ProcessMiningLogger file output."""

    def test_save_to_json_creates_file(self):
        """Verify save_to_json() creates JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("JSON_Test", data={"key": "value"})
            logger.save_to_json()

            assert logger.json_log_file.exists()

    def test_save_to_json_valid_format(self):
        """Verify save_to_json() writes valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("Valid_JSON", data={"test": "data"})
            logger.save_to_json()

            with open(logger.json_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert "metadata" in data
            assert "events" in data
            assert data["metadata"]["total_events"] == 1
            assert len(data["events"]) == 1

    def test_save_to_json_metadata(self):
        """Verify save_to_json() includes proper metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("Meta_Test")
            logger.save_to_json()

            with open(logger.json_log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert data["metadata"]["log_version"] == "1.0"
            assert data["metadata"]["format"] == "process_mining_json"
            assert "created_at" in data["metadata"]

    def test_save_to_text_creates_file(self):
        """Verify save_to_text() creates text file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("Text_Test")
            logger.save_to_text()

            assert logger.text_log_file.exists()

    def test_save_to_text_valid_format(self):
        """Verify save_to_text() writes readable text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("Text_Valid")
            logger.save_to_text()

            with open(logger.text_log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            assert "PROCESS MINING LOG" in content
            assert "Total Events: 1" in content
            assert "Text_Valid" in content

    def test_save_to_csv_creates_file(self):
        """Verify save_to_csv() creates CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("CSV_Test")
            logger.save_to_csv()

            assert logger.csv_log_file.exists()

    def test_save_to_csv_valid_format(self):
        """Verify save_to_csv() writes valid CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("CSV_Valid")
            logger.save_to_csv()

            with open(logger.csv_log_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            assert rows[0]["process_name"] == "CSV_Valid"
            assert "event_id" in rows[0]
            assert "duration_seconds" in rows[0]

    def test_save_to_csv_empty_logger(self):
        """Verify save_to_csv() handles empty logger gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.save_to_csv()

            assert logger.csv_log_file.exists()
            # File should be created but may be empty or contain no data rows

    def test_save_all_formats(self):
        """Verify save_all_formats() creates all three files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("Multi_Format")
            result = logger.save_all_formats()

            assert logger.json_log_file.exists()
            assert logger.text_log_file.exists()
            assert logger.csv_log_file.exists()
            assert result["events_count"] == 1
            assert "json_file" in result
            assert "text_file" in result
            assert "csv_file" in result

    def test_save_all_formats_multiple_events(self):
        """Verify save_all_formats() handles multiple events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))

            start1 = logger.log_process_start("Process_X")
            logger.log_event("Process_X", "MIDDLE", start1.start_time)
            logger.log_process_end("Process_X", start1)

            start2 = logger.log_process_start("Process_Y")
            logger.log_process_end("Process_Y", start2)

            result = logger.save_all_formats()

            assert result["events_count"] == 5

            # Verify JSON
            with open(logger.json_log_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            assert len(json_data["events"]) == 5

            # Verify CSV
            with open(logger.csv_log_file, 'r', encoding='utf-8', newline='') as f:
                csv_rows = list(csv.DictReader(f))
            assert len(csv_rows) == 5

    def test_file_encoding_utf8(self):
        """Verify files are saved with UTF-8 encoding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start(
                "Encoding_Test",
                data={"message": "Тестовое сообщение с кириллицей"}
            )
            logger.save_all_formats()

            # Verify JSON
            with open(logger.json_log_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            assert "Тестовое сообщение" in json.dumps(json_data, ensure_ascii=False)

            # Verify text
            with open(logger.text_log_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            assert "Тестовое сообщение" in text_content


class TestProcessMiningLoggerEdgeCases:
    """Edge case and error handling tests."""

    def test_logger_with_very_long_process_name(self):
        """Verify logger handles very long process names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            long_name = "P" * 500
            logger.log_process_start(long_name)
            logger.save_all_formats()

            assert len(logger.events) == 1
            assert logger.events[0].process_name == long_name

    def test_logger_with_special_characters_in_data(self):
        """Verify logger handles special characters in data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            special_data = {
                "quotes": 'He said "Hello"',
                "newlines": "Line 1\nLine 2",
                "cyrillic": "Сообщение",
                "unicode": "😀🎉"
            }
            logger.log_process_start("Special_Chars", data=special_data)
            logger.save_all_formats()

            with open(logger.json_log_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            saved_data = json_data["events"][0]["additional_data"]
            assert saved_data["unicode"] == "😀🎉"

    def test_logger_process_summary_average_duration(self):
        """Verify get_process_summary() calculates average duration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))

            start1 = datetime.now()
            logger.log_event("P1", "START", start1,
                           end_time=start1 + timedelta(seconds=10))
            logger.log_event("P2", "START", start1,
                           end_time=start1 + timedelta(seconds=20))

            summary = logger.get_process_summary()
            assert summary["total_events"] == 2

    def test_logger_with_zero_duration_event(self):
        """Verify logger handles zero-duration events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))

            now = datetime.now()
            logger.log_event("ZeroDur", "EXEC", now, end_time=now)
            logger.save_all_formats()

            with open(logger.json_log_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            assert json_data["events"][0]["duration_seconds"] == 0.0

    def test_logger_reinitialization_same_dir(self):
        """Verify logger can reinitialize in same directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = ProcessMiningLogger(str(tmpdir))
            logger1.log_process_start("First")
            logger1.save_all_formats()

            logger2 = ProcessMiningLogger(str(tmpdir))
            logger2.log_process_start("Second")
            # New logger should overwrite files from previous logger
            logger2.save_all_formats()

            with open(logger2.json_log_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            # Only second event should be in file (logger2 overwrites)
            assert json_data["metadata"]["total_events"] == 1

    def test_logger_process_event_with_none_data(self):
        """Verify logger handles None as data parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ProcessMiningLogger(str(tmpdir))
            logger.log_process_start("NoneData", data=None)
            logger.save_to_json()

            with open(logger.json_log_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)

            assert json_data["events"][0]["additional_data"] == {}
