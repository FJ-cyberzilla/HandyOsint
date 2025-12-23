#!/usr/bin/env python3
"""
HandyOsint Integration & Orchestration Module.

Enterprise-grade integration layer that coordinates:
- Core scanner with analysis engine
- Audit logging with compliance tracking
- Report generation and exports
- Dashboard visualization
- Error handling and recovery
- Multi-scan orchestration
"""

import logging
import threading
import json
import csv
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import hashlib

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)


# ========================================================================
# ENUMS
# ========================================================================

class ScanPriority(Enum):
    """Scan execution priority."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class ExportFormat(Enum):
    """Supported export formats."""

    JSON = "json"
    CSV = "csv"
    TEXT = "txt"
    HTML = "html"


# ========================================================================
# DATA MODELS
# ========================================================================

@dataclass
class TaskMetadata:
    """Task metadata and state."""

    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class ScanTask:
    """Individual scan task."""

    task_id: str
    username: str
    priority: ScanPriority
    created_at: str
    metadata: TaskMetadata = field(default_factory=TaskMetadata)

    @property
    def status(self) -> str:
        """Get task status."""
        return self.metadata.status

    @status.setter
    def status(self, value: str) -> None:
        """Set task status."""
        self.metadata.status = value


@dataclass
class JobMetadata:
    """Batch job metadata and state."""

    status: str = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    tasks: Dict[str, ScanTask] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchScanJob:
    """Batch scan job containing multiple tasks."""

    job_id: str
    usernames: List[str]
    priority: ScanPriority
    created_at: str
    metadata: JobMetadata = field(default_factory=JobMetadata)

    @property
    def status(self) -> str:
        """Get job status."""
        return self.metadata.status

    @status.setter
    def status(self, value: str) -> None:
        """Set job status."""
        self.metadata.status = value

    @property
    def tasks(self) -> Dict[str, ScanTask]:
        """Get tasks."""
        return self.metadata.tasks

    @property
    def results(self) -> Dict[str, Any]:
        """Get results."""
        return self.metadata.results

    def task_count(self) -> int:
        """Get number of tasks."""
        return len(self.metadata.tasks)


@dataclass
class ScanMetrics:
    """Performance metrics for scans."""

    total_scans: int = 0
    successful_scans: int = 0
    failed_scans: int = 0
    average_duration: float = 0.0
    total_profiles_found: int = 0
    average_risk_score: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ========================================================================
# TASK QUEUE AND ORCHESTRATION
# ========================================================================

class ScanTaskQueue:
    """Priority-based task queue for scan orchestration."""

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize task queue."""
        self._queue: List[ScanTask] = []
        self._lock = threading.RLock()
        self.max_workers = max_workers
        self._active_workers = 0
        logger.info("ScanTaskQueue initialized with %d workers", max_workers)

    def enqueue(self, task: ScanTask) -> None:
        """Enqueue scan task."""
        with self._lock:
            self._queue.append(task)
            self._queue.sort(
                key=lambda t: t.priority.value,
                reverse=True
            )
            logger.info("Task enqueued: %s (priority: %s)",
                       task.task_id,
                       task.priority.name)

    def dequeue(self) -> Optional[ScanTask]:
        """Dequeue next task in priority order."""
        with self._lock:
            if self._queue and self._active_workers < self.max_workers:
                task = self._queue.pop(0)
                self._active_workers += 1
                logger.info("Task dequeued: %s", task.task_id)
                return task
        return None

    def mark_complete(self, task_id: str) -> None:
        """Mark task as complete."""
        with self._lock:
            self._active_workers = max(0, self._active_workers - 1)
            logger.info("Task completed: %s", task_id)

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        with self._lock:
            utilization = (
                (self._active_workers / self.max_workers * 100)
                if self.max_workers > 0
                else 0.0
            )
            return {
                "pending_tasks": len(self._queue),
                "active_workers": self._active_workers,
                "queue_capacity": self.max_workers,
                "utilization": f"{utilization:.1f}%",
            }


class ScanOrchestrator:
    """Orchestrates multi-scan operations with coordination."""

    def __init__(self, max_workers: int = 4) -> None:
        """Initialize orchestrator."""
        self.task_queue = ScanTaskQueue(max_workers=max_workers)
        self._batch_jobs: Dict[str, BatchScanJob] = {}
        self._lock = threading.RLock()
        self.metrics = ScanMetrics()
        logger.info("ScanOrchestrator initialized")

    def create_batch_job(
        self,
        usernames: List[str],
        priority: ScanPriority = ScanPriority.NORMAL,
    ) -> BatchScanJob:
        """Create batch scan job."""
        timestamp = datetime.now().isoformat()
        job_id = hashlib.sha256(
            f"{','.join(usernames)}{timestamp}".encode()
        ).hexdigest()[:12]

        job = BatchScanJob(
            job_id=job_id,
            usernames=usernames,
            priority=priority,
            created_at=timestamp,
        )

        with self._lock:
            self._batch_jobs[job_id] = job

        # Create individual tasks
        for idx, username in enumerate(usernames):
            task_id = f"{job_id}_{idx}"
            task = ScanTask(
                task_id=task_id,
                username=username,
                priority=priority,
                created_at=datetime.now().isoformat(),
            )
            job.metadata.tasks[task_id] = task
            self.task_queue.enqueue(task)

        logger.info("Batch job created: %s with %d tasks",
                   job_id,
                   len(usernames))
        return job

    def update_task_result(
        self,
        task_id: str,
        result: Dict[str, Any],
        status: str = "completed",
    ) -> None:
        """Update task with result."""
        # Parse job_id from task_id (format: job_id_index)
        job_id = "_".join(task_id.split("_")[:-1])

        with self._lock:
            if job_id in self._batch_jobs:
                job = self._batch_jobs[job_id]
                if task_id in job.tasks:
                    task = job.tasks[task_id]
                    task.metadata.status = status
                    task.metadata.result = result
                    task.metadata.completed_at = (
                        datetime.now().isoformat()
                    )

                    # Update metrics
                    if status == "completed":
                        self.metrics.successful_scans += 1
                    else:
                        self.metrics.failed_scans += 1

                    logger.info("Task updated: %s → %s",
                               task_id,
                               status)

        self.task_queue.mark_complete(task_id)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get batch job status."""
        with self._lock:
            if job_id not in self._batch_jobs:
                return None

            job = self._batch_jobs[job_id]
            completed = sum(
                1 for t in job.tasks.values()
                if t.metadata.status == "completed"
            )
            total = len(job.tasks)

            percentage = (
                int((completed / total * 100)) if total > 0 else 0
            )

            return {
                "job_id": job_id,
                "status": job.status,
                "created_at": job.created_at,
                "started_at": job.metadata.started_at,
                "completed_at": job.metadata.completed_at,
                "progress": f"{completed}/{total}",
                "percentage": percentage,
            }

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all batch jobs status."""
        with self._lock:
            return [
                self.get_job_status(job_id)
                for job_id in self._batch_jobs
                if self.get_job_status(job_id) is not None
            ]

    def update_metrics(self, scan_result: Dict[str, Any]) -> None:
        """Update aggregated metrics."""
        self.metrics.total_scans += 1
        self.metrics.total_profiles_found += (
            scan_result.get("profiles_found", 0)
        )

        if "scan_duration" in scan_result:
            total_time = (
                self.metrics.average_duration
                * (self.metrics.total_scans - 1)
                + scan_result["scan_duration"]
            )
            self.metrics.average_duration = (
                total_time / self.metrics.total_scans
            )

        if "risk_score" in scan_result:
            total_risk = (
                self.metrics.average_risk_score
                * (self.metrics.total_scans - 1)
                + scan_result["risk_score"]
            )
            self.metrics.average_risk_score = (
                total_risk / self.metrics.total_scans
            )

        logger.info("Metrics updated")


# ========================================================================
# REPORT COORDINATION
# ========================================================================

class UnifiedReportManager:
    """Manages unified report generation across multiple scans."""

    def __init__(self, reports_dir: str = "reports") -> None:
        """Initialize report manager."""
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        logger.info("ReportManager initialized with directory: %s",
                   reports_dir)

    def generate_individual_report(
        self,
        scan_data: Dict[str, Any],
        export_formats: List[ExportFormat],
    ) -> Dict[str, str]:
        """Generate reports for individual scan."""
        username = scan_data.get("username", "unknown")
        scan_id = scan_data.get("scan_id", "unknown")
        output_files = {}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{username}_{scan_id}_{timestamp}"

        for fmt in export_formats:
            filepath = self._generate_report_file(
                fmt,
                base_filename,
                scan_data,
                None
            )
            if filepath:
                output_files[fmt.value] = filepath

        logger.info("Reports generated for %s: %s",
                   username,
                   list(output_files.keys()))
        return output_files

    def generate_batch_report(
        self,
        batch_data: Dict[str, Any],
        export_formats: List[ExportFormat],
    ) -> Dict[str, str]:
        """Generate consolidated batch report."""
        job_id = batch_data.get("job_id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"batch_{job_id}_{timestamp}"
        output_files = {}

        for fmt in export_formats:
            filepath = self._generate_report_file(
                fmt,
                base_filename,
                batch_data,
                True
            )
            if filepath:
                output_files[fmt.value] = filepath

        logger.info("Batch reports generated: %s",
                   list(output_files.keys()))
        return output_files

    def _generate_report_file(
        self,
        fmt: ExportFormat,
        base_filename: str,
        data: Dict[str, Any],
        is_batch: Optional[bool],
    ) -> Optional[str]:
        """Generate individual report file."""
        if fmt == ExportFormat.JSON:
            filepath = self.reports_dir / f"{base_filename}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return str(filepath)

        if fmt == ExportFormat.CSV and not is_batch:
            filepath = self.reports_dir / f"{base_filename}.csv"
            self._generate_csv_report(data, filepath)
            return str(filepath)

        if fmt == ExportFormat.TEXT and not is_batch:
            filepath = self.reports_dir / f"{base_filename}.txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(self._generate_text_report(data))
            return str(filepath)

        if fmt == ExportFormat.HTML:
            filepath = self.reports_dir / f"{base_filename}.html"
            with open(filepath, "w", encoding="utf-8") as f:
                if is_batch:
                    f.write(self._generate_batch_html_report(data))
                else:
                    f.write(self._generate_html_report(data))
            return str(filepath)

        return None

    def _generate_csv_report(
        self,
        scan_data: Dict[str, Any],
        filepath: Path
    ) -> None:
        """Generate CSV format report."""
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Username", scan_data.get("username", "N/A")])
            writer.writerow(["Scan ID", scan_data.get("scan_id", "N/A")])
            writer.writerow(["Timestamp", scan_data.get("timestamp", "N/A")])
            writer.writerow(["Duration", scan_data.get("duration", "N/A")])
            writer.writerow([
                "Profiles Found",
                scan_data.get("profiles_found", 0)
            ])
            writer.writerow([
                "Risk Score",
                scan_data.get("risk_score", "N/A")
            ])

    def _generate_text_report(self, scan_data: Dict[str, Any]) -> str:
        """Generate text format report."""
        report = [
            "=" * 80,
            "OSINT SCAN REPORT",
            "=" * 80,
            "",
            f"Username: {scan_data.get('username', 'N/A')}",
            f"Scan ID: {scan_data.get('scan_id', 'N/A')}",
            f"Timestamp: {scan_data.get('timestamp', 'N/A')}",
            f"Duration: {scan_data.get('scan_duration', 'N/A')}s",
            f"Profiles Found: {scan_data.get('profiles_found', 0)}",
            f"Risk Level: {scan_data.get('risk_level', 'N/A')}",
            f"Risk Score: {scan_data.get('risk_score', 'N/A'):.3f}",
            "",
            "=" * 80,
        ]
        return "\n".join(report)

    def _generate_html_report(self, scan_data: Dict[str, Any]) -> str:
        """Generate HTML format report."""
        username = scan_data.get("username", "Unknown")
        risk_level = scan_data.get("risk_level", "unknown").lower()

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT Scan Report - {username}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #1a1a1a; margin-bottom: 10px; }}
        .section {{ margin: 20px 0; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px 0; }}
        .metric-label {{ font-weight: bold; color: #333; }}
        .metric-value {{ color: #007bff; }}
        .risk-critical {{ color: #dc3545; font-weight: bold; }}
        .risk-high {{ color: #fd7e14; font-weight: bold; }}
        .risk-medium {{ color: #ffc107; font-weight: bold; }}
        .risk-low {{ color: #28a745; font-weight: bold; }}
        .footer {{ margin-top: 30px; padding-top: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 OSINT Scan Report</h1>
        <div class="section">
            <div class="metric">
                <span class="metric-label">Username:</span>
                <span class="metric-value">{username}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Scan ID:</span>
                <span class="metric-value">
                    {scan_data.get('scan_id', 'N/A')}
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">Timestamp:</span>
                <span class="metric-value">
                    {scan_data.get('timestamp', 'N/A')}
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">Duration:</span>
                <span class="metric-value">
                    {scan_data.get('scan_duration', 'N/A')}s
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">Profiles Found:</span>
                <span class="metric-value">
                    {scan_data.get('profiles_found', 0)}
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">Risk Level:</span>
                <span class="metric-value risk-{risk_level}">
                    {scan_data.get('risk_level', 'N/A')}
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">Risk Score:</span>
                <span class="metric-value">
                    {scan_data.get('risk_score', 'N/A'):.3f}/1.000
                </span>
            </div>
        </div>
        <div class="footer">
            <p>Generated by HandyOsint © 2025 | Enterprise Edition</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def _generate_batch_html_report(
        self,
        batch_data: Dict[str, Any]
    ) -> str:
        """Generate HTML batch report."""
        results_rows = ""
        for username, data in batch_data.get("results", {}).items():
            results_rows += f"""
            <tr>
                <td>{username}</td>
                <td>{data.get('profiles_found', 0)}</td>
                <td>{data.get('risk_level', 'N/A')}</td>
                <td>{data.get('risk_score', 0):.3f}</td>
            </tr>"""

        total_scans = len(batch_data.get("results", {}))
        total_profiles = sum(
            d.get('profiles_found', 0)
            for d in batch_data.get('results', {}).values()
        )
        avg_risk = batch_data.get('average_risk_score', 0)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSINT Batch Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #1a1a1a; margin-bottom: 20px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }}
        .summary-label {{ color: #666; font-size: 12px; }}
        .summary-value {{ color: #007bff; font-size: 24px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .footer {{ margin-top: 30px; padding-top: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 OSINT Batch Scan Report</h1>
        <div class="summary">
            <div class="summary-card">
                <div class="summary-label">Total Scans</div>
                <div class="summary-value">{total_scans}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Total Profiles</div>
                <div class="summary-value">{total_profiles}</div>
            </div>
            <div class="summary-card">
                <div class="summary-label">Avg Risk Score</div>
                <div class="summary-value">{avg_risk:.3f}</div>
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Profiles Found</th>
                    <th>Risk Level</th>
                    <th>Risk Score</th>
                </tr>
            </thead>
            <tbody>
                {results_rows}
            </tbody>
        </table>
        <div class="footer">
            <p>Generated by HandyOsint © 2025 | Enterprise Edition</p>
        </div>
    </div>
</body>
</html>"""
        return html


# ========================================================================
# INTEGRATION COORDINATOR
# ========================================================================

class IntegrationCoordinator:
    """Main coordination hub for all OSINT operations."""

    def __init__(
        self,
        reports_dir: str = "reports",
        max_workers: int = 4,
    ) -> None:
        """Initialize integration coordinator."""
        self.orchestrator = ScanOrchestrator(max_workers=max_workers)
        self.report_manager = UnifiedReportManager(
            reports_dir=reports_dir
        )
        self.console = Console()
        logger.info("IntegrationCoordinator initialized")

    def execute_batch_scan(
        self,
        usernames: List[str],
        priority: ScanPriority = ScanPriority.NORMAL,
        export_formats: Optional[List[ExportFormat]] = None,
    ) -> BatchScanJob:
        """Execute batch scan operation."""
        if export_formats is None:
            export_formats = [ExportFormat.JSON, ExportFormat.HTML]

        job = self.orchestrator.create_batch_job(usernames, priority)
        self._display_batch_start(job)
        return job

    def _display_batch_start(self, job: BatchScanJob) -> None:
        """Display batch job start information."""
        self.console.print()
        self.console.print(
            Panel(
                Text(
                    "[bold cyan]🚀 Batch Scan Job Started[/bold cyan]\n"
                    f"[bold]Job ID:[/bold] {job.job_id}\n"
                    f"[bold]Usernames:[/bold] {len(job.usernames)}\n"
                    f"[bold]Priority:[/bold] {job.priority.name}",
                    justify="left",
                ),
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def display_queue_status(self) -> None:
        """Display current queue status."""
        status = self.orchestrator.task_queue.get_queue_status()
        self.console.print()
        self.console.print(
            Panel(
                Text(
                    "[bold cyan]📋 Queue Status[/bold cyan]\n"
                    f"[bold]Pending Tasks:[/bold] {status['pending_tasks']}\n"
                    f"[bold]Active Workers:[/bold] "
                    f"{status['active_workers']}/{status['queue_capacity']}\n"
                    f"[bold]Utilization:[/bold] {status['utilization']}",
                    justify="left",
                ),
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def display_metrics(self) -> None:
        """Display aggregated metrics."""
        metrics = self.orchestrator.metrics
        self.console.print()

        table = Table(
            title="[bold magenta]📊 Aggregated Metrics[/bold magenta]",
            show_header=True,
            border_style="magenta",
        )
        table.add_column("[magenta]Metric[/magenta]", style="cyan")
        table.add_column("[magenta]Value[/magenta]", style="green")

        table.add_row("Total Scans", str(metrics.total_scans))
        table.add_row("Successful Scans", str(metrics.successful_scans))
        table.add_row("Failed Scans", str(metrics.failed_scans))
        table.add_row(
            "Avg Duration",
            f"{metrics.average_duration:.2f}s"
        )
        table.add_row(
            "Total Profiles Found",
            str(metrics.total_profiles_found)
        )
        table.add_row(
            "Avg Risk Score",
            f"{metrics.average_risk_score:.3f}"
        )

        self.console.print(table)

    def display_all_jobs(self) -> None:
        """Display all batch jobs status."""
        jobs = self.orchestrator.get_all_jobs()

        if not jobs:
            self.console.print(
                Panel(
                    "[yellow]No jobs in progress[/yellow]",
                    border_style="yellow",
                )
            )
            return

        self.console.print()
        table = Table(
            title="[bold cyan]📋 All Batch Jobs[/bold cyan]",
            show_header=True,
            border_style="cyan",
        )
        table.add_column("[cyan]Job ID[/cyan]", style="magenta")
        table.add_column("[cyan]Status[/cyan]", style="green")
        table.add_column("[cyan]Progress[/cyan]", style="yellow")
        table.add_column("[cyan]Percentage[/cyan]", style="blue")

        for job in jobs:
            table.add_row(
                job["job_id"][:8],
                job["status"],
                job["progress"],
                f"{job['percentage']}%",
            )

        self.console.print(table)


# ========================================================================
# DEMO
# ========================================================================

def demo() -> None:
    """Demonstrate integration coordinator."""
    print("\n" + "=" * 80)
    print("HandyOsint Integration & Orchestration - Demo")
    print("=" * 80 + "\n")

    coordinator = IntegrationCoordinator(max_workers=4)

    # Create batch scan job
    usernames = [
        "johndoe",
        "janedoe",
        "devuser",
        "contentcreator"
    ]
    coordinator.execute_batch_scan(
        usernames=usernames,
        priority=ScanPriority.HIGH,
        export_formats=[
            ExportFormat.JSON,
            ExportFormat.HTML,
            ExportFormat.TEXT
        ],
    )

    # Display queue status
    coordinator.display_queue_status()

    # Display all jobs
    coordinator.display_all_jobs()

    # Display metrics
    coordinator.display_metrics()

    print("\n" + "=" * 80)
    print("Demo completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    demo()
