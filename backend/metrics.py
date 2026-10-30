"""
metrics.py
----------
All Prometheus metrics for the SPECTRA backend.
Import and update these from app.py so the /metrics endpoint
reflects live detector state.
"""

import sys
import os
import threading

try:
    import resource
except ImportError:
    resource = None

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    CollectorRegistry,
    REGISTRY,
    make_asgi_app,
)

# ---------------------------------------------------------------------------
# Python runtime info (mirrors "Python Version" panel in Grafana)
# Note: prometheus_client automatically registers python_info with
# version and implementation labels in the default REGISTRY.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# HTTP instrumentation  (prometheus_fastapi_instrumentator also provides
# http_requests_total and http_request_duration_seconds, but we declare
# fallback counters here in case the instrumentator is not installed)
# ---------------------------------------------------------------------------
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "handler", "status_code"],
)

HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["handler"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)

# ---------------------------------------------------------------------------
# Process CPU (mirrors "Process CPU Usage" panel)
# ---------------------------------------------------------------------------
PROCESS_CPU = Counter(
    "spectra_process_cpu_seconds_total",
    "Total process CPU time spent in seconds",
)

# ---------------------------------------------------------------------------
# Process memory  (mirrors "Process Memory Usage" panels)
# ---------------------------------------------------------------------------
HEAP_USED = Gauge(
    "spectra_memory_heap_used_bytes",
    "Estimated Python heap used (RSS - stack estimate)",
)
HEAP_TOTAL = Gauge(
    "spectra_memory_heap_total_bytes",
    "Total virtual memory reported by the OS",
)
HEAP_AVAILABLE = Gauge(
    "spectra_memory_heap_available_bytes",
    "Available memory (VMS - RSS)",
)

# ---------------------------------------------------------------------------
# Drowsiness detector state  (mirrors the Drowsiness Detector panels)
# ---------------------------------------------------------------------------
DETECTOR_RUNNING = Gauge(
    "spectra_detector_running",
    "1 if the drowsiness detector thread is running, 0 otherwise",
)
DETECTOR_RESTARTS = Counter(
    "spectra_detector_restarts_total",
    "Number of times the detector thread has been (re)started",
)
ALERT_ACTIVE = Gauge(
    "spectra_alert_active",
    "1 if a drowsiness alert is currently active",
)
EAR_VALUE = Gauge(
    "spectra_ear_value",
    "Current Eye Aspect Ratio (EAR); NaN when no face is detected",
)
EYE_CLOSURE_DURATION = Gauge(
    "spectra_eye_closure_duration_seconds",
    "Cumulative seconds eyes have been continuously closed",
)

# ---------------------------------------------------------------------------
# Active threads  (mirrors "Active Handlers / Requests Total")
# ---------------------------------------------------------------------------
ACTIVE_DETECTOR_THREADS = Gauge(
    "spectra_active_detector_threads",
    "Number of active detector threads",
)


def update_memory_metrics() -> None:
    """Refresh heap gauges from /proc, resource module, or Windows ctypes."""
    rss = vms = 0
    try:
        # Linux: read /proc/self/status for an accurate picture
        if os.path.exists("/proc/self/status"):
            with open("/proc/self/status") as fh:
                for line in fh:
                    if line.startswith("VmRSS:"):
                        rss = int(line.split()[1]) * 1024
                    elif line.startswith("VmSize:"):
                        vms = int(line.split()[1]) * 1024
        elif resource is not None:
            # Unix / macOS fallback
            usage = resource.getrusage(resource.RUSAGE_SELF)
            rss = usage.ru_maxrss * 1024
            vms = rss  # best-effort
        elif sys.platform == "win32":
            # Windows fallback using psapi
            try:
                import ctypes
                from ctypes import wintypes

                class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                    _fields_ = [
                        ("cb", wintypes.DWORD),
                        ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t),
                    ]

                counters = PROCESS_MEMORY_COUNTERS()
                counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
                kernel32 = ctypes.windll.kernel32
                psapi = ctypes.windll.psapi
                kernel32.GetCurrentProcess.restype = wintypes.HANDLE
                psapi.GetProcessMemoryInfo.argtypes = [
                    wintypes.HANDLE,
                    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                    wintypes.DWORD,
                ]
                if psapi.GetProcessMemoryInfo(
                    kernel32.GetCurrentProcess(),
                    ctypes.byref(counters),
                    counters.cb,
                ):
                    rss = counters.WorkingSetSize
                    vms = counters.PagefileUsage
            except Exception:
                pass
    except Exception:
        rss = vms = 0

    HEAP_USED.set(rss)
    HEAP_TOTAL.set(vms)
    HEAP_AVAILABLE.set(max(0, vms - rss))


_last_cpu_time = 0.0

def update_detector_metrics(status: dict) -> None:
    """
    Called from the API status endpoint to push live detector state
    into Prometheus gauges.

    Parameters
    ----------
    status : dict
        A snapshot from ``get_status_snapshot()`` in app.py.
    """
    global _last_cpu_time
    try:
        now_cpu = time.process_time()
        diff = now_cpu - _last_cpu_time
        if diff > 0:
            PROCESS_CPU.inc(diff)
            _last_cpu_time = now_cpu
    except Exception:
        pass

    is_running = 1 if status.get("running") else 0
    DETECTOR_RUNNING.set(is_running)

    is_alert = 1 if status.get("alert") else 0
    ALERT_ACTIVE.set(is_alert)

    ear = status.get("ear")
    EAR_VALUE.set(ear if ear is not None else float("nan"))

    EYE_CLOSURE_DURATION.set(status.get("closure_duration", 0.0))

    # Count live detector threads
    detector_threads = sum(
        1
        for t in threading.enumerate()
        if "detector" in t.name.lower()
    )
    ACTIVE_DETECTOR_THREADS.set(detector_threads)

    update_memory_metrics()
