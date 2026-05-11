import os
import sys
import subprocess
import threading

SERVICE_NAME = "OpenClawCenterAgent"
SERVICE_DISPLAY = "OpenClaw Center Agent"


def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def is_service_installed():
    try:
        result = subprocess.run(
            ["sc", "query", SERVICE_NAME],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def install_service(exe_path):
    bin_path = f'"{exe_path}" --service'
    cmd = [
        "sc", "create", SERVICE_NAME,
        f"binPath= {bin_path}",
        "start=", "auto",
        f"DisplayName= {SERVICE_DISPLAY}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"sc create failed: {result.stderr.strip() or result.stdout.strip()}")

    subprocess.run(
        ["sc", "description", SERVICE_NAME,
         "OpenClaw Center Agent - heartbeat, config sync, task execution"],
        capture_output=True, text=True, timeout=10,
    )


def start_service():
    subprocess.run(
        ["sc", "start", SERVICE_NAME],
        capture_output=True, text=True, timeout=30,
    )


def run_as_service():
    """Entry point when running as Windows service via pywin32."""
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager
    except ImportError:
        print("ERROR: pywin32 is required for Windows service mode.")
        print("Install it with: pip install pywin32")
        sys.exit(1)

    import signal
    from agent.config import AgentConfig
    from agent.logger import setup_logger
    from agent.register import register_agent
    from agent.heartbeat import heartbeat_loop
    from agent.collector import resource_loop, config_loop, skills_loop
    from agent.task_runner import task_loop

    class AgentService(win32serviceutil.ServiceFramework):
        _svc_name_ = SERVICE_NAME
        _svc_display_name_ = SERVICE_DISPLAY
        _svc_description_ = "OpenClaw Center Agent - heartbeat, config sync, task execution"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.stop_event = threading.Event()

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self.stop_event.set()
            win32event.SetEvent(self.hWaitStop)

        def SvcDoRun(self):
            logger = setup_logger("service")
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )

            config = AgentConfig()
            config.ensure_center_url()
            config.ensure_machine_code()

            if not register_agent(config):
                logger.error("Registration failed in service mode")
                return

            threads = [
                threading.Thread(target=heartbeat_loop, args=(config, self.stop_event), daemon=True),
                threading.Thread(target=resource_loop, args=(config, self.stop_event), daemon=True),
                threading.Thread(target=config_loop, args=(config, self.stop_event), daemon=True),
                threading.Thread(target=skills_loop, args=(config, self.stop_event), daemon=True),
                threading.Thread(target=task_loop, args=(config, self.stop_event), daemon=True),
            ]
            for t in threads:
                t.start()

            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            logger.info("Service stopping...")

    win32serviceutil.HandleCommandLine(AgentService)
