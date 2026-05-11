import os
import sys
import subprocess

TASK_NAME = "OpenClawCenterAgent"


def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def is_task_installed():
    """Check if the scheduled task exists."""
    result = subprocess.run(
        ["schtasks", "/query", "/tn", TASK_NAME],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0


def install_task():
    """Register a scheduled task that runs the agent at logon and on startup.

    Uses schtasks.exe which is available on all Windows versions and does
    not require pywin32 or interaction with the Service Control Manager.
    This avoids the incompatibility between PyInstaller --onefile and
    Windows services (SCM timeout, error 87, error 1053).
    """
    exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]

    # Create task: run at system startup, with highest privileges, no window
    cmd = [
        "schtasks", "/create",
        "/tn", TASK_NAME,
        "/tr", f'"{exe_path}"',
        "/sc", "onstart",       # at system startup
        "/ru", "SYSTEM",
        "/rl", "HIGHEST",       # run with highest privileges
        "/f",                   # force overwrite if exists
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(
            f"schtasks create failed: {result.stderr.strip() or result.stdout.strip()}"
        )

    # Also add a logon trigger so it starts when a user logs in
    subprocess.run(
        ["schtasks", "/create",
         "/tn", f"{TASK_NAME}_Logon",
         "/tr", f'"{exe_path}"',
         "/sc", "onlogon",
         "/rl", "HIGHEST",
         "/f"],
        capture_output=True, text=True, timeout=30,
    )


def start_task():
    """Manually run the scheduled task."""
    subprocess.run(
        ["schtasks", "/run", "/tn", TASK_NAME],
        capture_output=True, text=True, timeout=30,
    )


def remove_task():
    """Remove the scheduled tasks."""
    subprocess.run(
        ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
        capture_output=True, text=True, timeout=10,
    )
    subprocess.run(
        ["schtasks", "/delete", "/tn", f"{TASK_NAME}_Logon", "/f"],
        capture_output=True, text=True, timeout=10,
    )
