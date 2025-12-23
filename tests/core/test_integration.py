# pylint: disable=redefined-outer-name, unused-argument
"""
Pytest unit tests for HandyOsint Integration & Orchestration Module.
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from core.integration import (
    ScanTaskQueue, ScanOrchestrator, UnifiedReportManager,
    ScanPriority, ExportFormat, ScanTask, BatchScanJob,
    IntegrationCoordinator
)

# Mock rich console for testing UI interactions
@pytest.fixture(autouse=True)
def mock_console():
    """Mock the rich.Console object to prevent actual printing during tests."""
    with patch('rich.console.Console', autospec=True) as mock_console_cls:
        yield mock_console_cls.return_value

@pytest.fixture
def scan_task_queue():
    """Fixture for ScanTaskQueue."""
    return ScanTaskQueue(max_workers=2)

@pytest.fixture
def scan_orchestrator():
    """Fixture for ScanOrchestrator."""
    return ScanOrchestrator(max_workers=2)

@pytest.fixture
def unified_report_manager(tmp_path):
    """Fixture for UnifiedReportManager."""
    return UnifiedReportManager(reports_dir=tmp_path)

@pytest.fixture
def integration_coordinator(tmp_path, mock_console):
    """Fixture for IntegrationCoordinator."""
    coordinator = IntegrationCoordinator(reports_dir=tmp_path, max_workers=2)
    coordinator.console = mock_console
    return coordinator

@pytest.fixture
def sample_scan_data():
    """Sample scan data for reports."""
    return {
        "username": "testuser",
        "scan_id": "12345abcdef",
        "timestamp": datetime.now().isoformat(),
        "scan_duration": 15.5,
        "profiles_found": 5,
        "risk_level": "High",
        "risk_score": 0.789,
        "results": {
            "platform_a": {"found": True, "url": "http://a.com/testuser"},
            "platform_b": {"found": False},
        }
    }

@pytest.fixture
def sample_batch_data():
    """Sample batch data for reports."""
    return {
        "job_id": "batch123",
        "timestamp": datetime.now().isoformat(),
        "total_tasks": 2,
        "results": {
            "user1": {
                "scan_id": "id1", "profiles_found": 3,
                "risk_level": "Medium", "risk_score": 0.5
            },
            "user2": {
                "scan_id": "id2", "profiles_found": 7,
                "risk_level": "High", "risk_score": 0.8
            },
        },
        "average_risk_score": 0.65
    }

# ======================================================================
# Test ScanTaskQueue
# ======================================================================

def test_scan_task_queue_enqueue_dequeue(scan_task_queue):
    """Test enqueuing and dequeuing tasks."""
    task1 = ScanTask("task1", "user1", ScanPriority.LOW, datetime.now().isoformat())
    task2 = ScanTask("task2", "user2", ScanPriority.HIGH, datetime.now().isoformat())
    task3 = ScanTask("task3", "user3", ScanPriority.NORMAL, datetime.now().isoformat())

    scan_task_queue.enqueue(task1)
    scan_task_queue.enqueue(task3)
    scan_task_queue.enqueue(task2)

    # High priority task should be dequeued first
    dequeued_task = scan_task_queue.dequeue()
    assert dequeued_task.task_id == "task2"
    assert scan_task_queue._active_workers == 1

    dequeued_task = scan_task_queue.dequeue()
    assert dequeued_task.task_id == "task3"
    assert scan_task_queue._active_workers == 2

    # Queue should be empty for new dequeues as max_workers reached
    assert scan_task_queue.dequeue() is None

    scan_task_queue.mark_complete("task2")
    assert scan_task_queue._active_workers == 1
    dequeued_task = scan_task_queue.dequeue()
    assert dequeued_task.task_id == "task1"

def test_scan_task_queue_get_status(scan_task_queue):
    """Test getting queue status."""
    task = ScanTask("task1", "user1", ScanPriority.NORMAL, datetime.now().isoformat())
    scan_task_queue.enqueue(task)
    status = scan_task_queue.get_queue_status()
    assert status["pending_tasks"] == 1
    assert status["active_workers"] == 0
    assert status["queue_capacity"] == 2

    scan_task_queue.dequeue()
    status = scan_task_queue.get_queue_status()
    assert status["pending_tasks"] == 0
    assert status["active_workers"] == 1

def test_scan_task_queue_empty(scan_task_queue):
    """Test queue behavior when empty."""
    assert scan_task_queue.dequeue() is None
    status = scan_task_queue.get_queue_status()
    assert status["pending_tasks"] == 0
    assert status["active_workers"] == 0

# ======================================================================
# Test ScanOrchestrator
# ======================================================================

def test_scan_orchestrator_create_batch_job(scan_orchestrator):
    """Test creating a batch job."""
    usernames = ["userA", "userB"]
    job = scan_orchestrator.create_batch_job(usernames, ScanPriority.HIGH)

    assert job.job_id in scan_orchestrator._batch_jobs
    assert job.priority == ScanPriority.HIGH
    assert len(job.tasks) == 2
    assert "userA" in job.tasks[f"{job.job_id}_0"].username
    assert job.tasks[f"{job.job_id}_0"].priority == ScanPriority.HIGH
    assert job.tasks[f"{job.job_id}_0"].status == "pending"

def test_scan_orchestrator_update_task_result(scan_orchestrator):
    """Test updating task results."""
    usernames = ["userA"]
    job = scan_orchestrator.create_batch_job(usernames)
    task_id = list(job.tasks.keys())[0]

    result = {"found_profiles": 3}
    scan_orchestrator.update_task_result(task_id, result, "completed")

    updated_task = job.tasks[task_id]
    assert updated_task.status == "completed"
    assert updated_task.metadata.result == result
    assert updated_task.metadata.completed_at is not None
    assert scan_orchestrator.metrics.successful_scans == 1

    # Test failed task
    job2 = scan_orchestrator.create_batch_job(["userC"])
    task_id2 = list(job2.tasks.keys())[0]
    scan_orchestrator.update_task_result(task_id2, {"error": "timeout"}, "failed")
    assert scan_orchestrator.metrics.failed_scans == 1

def test_scan_orchestrator_get_job_status(scan_orchestrator):
    """Test getting job status."""
    usernames = ["userA", "userB"]
    job = scan_orchestrator.create_batch_job(usernames)
    status = scan_orchestrator.get_job_status(job.job_id)

    assert status["job_id"] == job.job_id
    assert status["status"] == "pending" # Initial status of job is pending
    assert status["progress"] == "0/2"
    assert status["percentage"] == 0

    task_id1 = list(job.tasks.keys())[0]
    scan_orchestrator.update_task_result(task_id1, {"found": True}, "completed")

    status = scan_orchestrator.get_job_status(job.job_id)
    assert status["progress"] == "1/2"
    assert status["percentage"] == 50

    task_id2 = list(job.tasks.keys())[1]
    scan_orchestrator.update_task_result(task_id2, {"found": True}, "completed")

    status = scan_orchestrator.get_job_status(job.job_id)
    assert status["progress"] == "2/2"
    assert status["percentage"] == 100

def test_scan_orchestrator_metrics_update(scan_orchestrator):
    """Test metrics updates."""
    initial_metrics = scan_orchestrator.metrics
    assert initial_metrics.total_scans == 0

    scan_orchestrator.update_metrics({
        "profiles_found": 5,
        "scan_duration": 10.0,
        "risk_score": 0.8
    })
    assert scan_orchestrator.metrics.total_scans == 1
    assert scan_orchestrator.metrics.total_profiles_found == 5
    assert scan_orchestrator.metrics.average_duration == 10.0
    assert scan_orchestrator.metrics.average_risk_score == 0.8

    scan_orchestrator.update_metrics({
        "profiles_found": 3,
        "scan_duration": 20.0,
        "risk_score": 0.6
    })
    assert scan_orchestrator.metrics.total_scans == 2
    assert scan_orchestrator.metrics.total_profiles_found == 8
    assert scan_orchestrator.metrics.average_duration == 15.0
    assert scan_orchestrator.metrics.average_risk_score == 0.7

# ======================================================================
# Test UnifiedReportManager
# ======================================================================

def test_unified_report_manager_init(tmp_path):
    """Test initialization of report manager."""
    reports_dir = tmp_path / "custom_reports"
    manager = UnifiedReportManager(reports_dir=str(reports_dir))
    assert manager.reports_dir == reports_dir
    assert reports_dir.is_dir()

def test_generate_individual_json_report(unified_report_manager, sample_scan_data):
    """Test generating individual JSON report."""
    output_files = unified_report_manager.generate_individual_report(
        sample_scan_data, [ExportFormat.JSON]
    )
    assert "json" in output_files
    json_path = Path(output_files["json"])
    assert json_path.exists()
    assert json_path.suffix == ".json"

    with open(json_path, "r", encoding="utf-8") as f:
        content = json.load(f)
        assert content["username"] == sample_scan_data["username"]
        assert content["scan_id"] == sample_scan_data["scan_id"]

def test_generate_individual_csv_report(unified_report_manager, sample_scan_data):
    """Test generating individual CSV report."""
    output_files = unified_report_manager.generate_individual_report(
        sample_scan_data, [ExportFormat.CSV]
    )
    assert "csv" in output_files
    csv_path = Path(output_files["csv"])
    assert csv_path.exists()
    assert csv_path.suffix == ".csv"

    with open(csv_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Username,testuser" in content
        assert "Profiles Found,5" in content

def test_generate_individual_text_report(unified_report_manager, sample_scan_data):
    """Test generating individual TEXT report."""
    output_files = unified_report_manager.generate_individual_report(
        sample_scan_data, [ExportFormat.TEXT]
    )
    assert "txt" in output_files
    text_path = Path(output_files["txt"])
    assert text_path.exists()
    assert text_path.suffix == ".txt"

    with open(text_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "OSINT SCAN REPORT" in content
        assert "Username: testuser" in content

def test_generate_individual_html_report(unified_report_manager, sample_scan_data):
    """Test generating individual HTML report."""
    output_files = unified_report_manager.generate_individual_report(
        sample_scan_data, [ExportFormat.HTML]
    )
    assert "html" in output_files
    html_path = Path(output_files["html"])
    assert html_path.exists()
    assert html_path.suffix == ".html"

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "OSINT Scan Report - testuser" in content
        assert ("Profiles Found:</span>\n                <span class=\"metric-value\">\n"
                "                    5") in content

def test_generate_batch_html_report(unified_report_manager, sample_batch_data):
    """Test generating batch HTML report."""
    output_files = unified_report_manager.generate_batch_report(
        sample_batch_data, [ExportFormat.HTML]
    )
    assert "html" in output_files
    html_path = Path(output_files["html"])
    assert html_path.exists()
    assert html_path.suffix == ".html"

    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "OSINT Batch Scan Report" in content
        assert "Total Scans</div>\n                <div class=\"summary-value\">2</div>" in content
        assert "<td>user1</td>" in content
        assert "<td>user2</td>" in content

def test_generate_batch_json_report(unified_report_manager, sample_batch_data):
    """Test generating batch JSON report."""
    output_files = unified_report_manager.generate_batch_report(
        sample_batch_data, [ExportFormat.JSON]
    )
    assert "json" in output_files
    json_path = Path(output_files["json"])
    assert json_path.exists()
    assert json_path.suffix == ".json"

    with open(json_path, "r", encoding="utf-8") as f:
        content = json.load(f)
        assert content["job_id"] == sample_batch_data["job_id"]
        assert "user1" in content["results"]

def test_generate_batch_unsupported_formats(unified_report_manager, sample_batch_data):
    """Test generating batch reports for unsupported formats (CSV, TEXT)."""
    output_files = unified_report_manager.generate_batch_report(
        sample_batch_data, [ExportFormat.CSV, ExportFormat.TEXT]
    )
    assert "csv" not in output_files
    assert "txt" not in output_files

# ======================================================================
# Test IntegrationCoordinator
# ======================================================================

def test_integration_coordinator_init(integration_coordinator):
    """Test initialization."""
    assert isinstance(integration_coordinator.orchestrator, ScanOrchestrator)
    assert isinstance(integration_coordinator.report_manager, UnifiedReportManager)
    assert integration_coordinator.orchestrator.task_queue.max_workers == 2

def test_execute_batch_scan(integration_coordinator, mock_console):
    """Test executing a batch scan."""
    usernames = ["user1", "user2"]
    job = integration_coordinator.execute_batch_scan(
        usernames,
        export_formats=[ExportFormat.JSON]
    )

    assert isinstance(job, BatchScanJob)
    assert len(job.usernames) == 2
    mock_console.print.assert_called() # Should display batch start panel

def test_display_queue_status(integration_coordinator, mock_console):
    """Test displaying queue status."""
    integration_coordinator.display_queue_status()
    mock_console.print.assert_called() # Should display queue status panel

def test_display_metrics(integration_coordinator, mock_console):
    """Test displaying metrics."""
    integration_coordinator.display_metrics()
    mock_console.print.assert_called() # Should display metrics table

def test_display_all_jobs(integration_coordinator, mock_console):
    """Test displaying all jobs."""
    integration_coordinator.display_all_jobs()
    mock_console.print.assert_called() # Should display jobs table or "no jobs" panel

    usernames = ["user1"]
    integration_coordinator.orchestrator.create_batch_job(usernames)
    integration_coordinator.display_all_jobs()
    mock_console.print.assert_called() # Should display jobs table
