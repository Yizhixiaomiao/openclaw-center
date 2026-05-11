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


def install_service():
    """Install the service using pywin32 HandleCommandLine mechanism.

    After pywin32 registers the service, we update the binPath to include
    --service so that SCM launches the exe with the service flag.
    """
    exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
    result = subprocess.run(
        [exe_path, "--service", "install"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Service install failed: {result.stderr.strip() or result.stdout.strip()}"
        )

    # Update binPath to include --service flag so SCM passes it when starting
    subprocess.run(
        ["sc", "config", SERVICE_NAME, f"binPath= \"{exe_path}\" --service"],
        capture_output=True, text=True, timeout=30,
    )


def start_service():
    subprocess.run(
        ["sc", "start", SERVICE_NAME],
        capture_output=True, text=True, timeout=30,
    )


def remove_service():
    exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
    subprocess.run(
        [exe_path, "--service", "remove"],
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

    # Remove --service from argv so HandleCommandLine sees only its own args
    # e.g. "exe --service install" → HandleCommandLine sees "exe install"
    sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:] if a != "--service"]

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
            # In service mode, config must already be configured (no interactive input)
            if not config.center_url or not config.machine_code:
                logger.error("Center URL or machine code not configured. Run the agent interactively first.")
                return

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
