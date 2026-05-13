import os
import sys
import subprocess
import tempfile
import logging

TASK_NAME = "OpenClawCenterAgent"
TASK_NAME_LOGON = "OpenClawCenterAgent_Logon"

logger = logging.getLogger("agent.service")


def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _exe_path():
    """Get the current executable path."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


def is_task_installed():
    """Check if the scheduled task exists."""
    result = subprocess.run(
        ["schtasks", "/query", "/tn", TASK_NAME],
        capture_output=True, text=True, timeout=10,
    )
    return result.returncode == 0


def _create_task_xml(exe_path, trigger="onstart", user_id="S-1-5-18"):
    """Generate scheduled task XML with no execution time limit."""
    if trigger == "onstart":
        trigger_xml = "    <BootTrigger>\n      <Enabled>true</Enabled>\n    </BootTrigger>"
    else:
        trigger_xml = "    <LogonTrigger>\n      <Enabled>true</Enabled>\n    </LogonTrigger>"

    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>OpenClaw Center Agent - background service</Description>
  </RegistrationInfo>
  <Triggers>
{trigger_xml}
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{user_id}</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>false</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
    </Exec>
  </Actions>
</Task>"""


def _register_task_xml(task_name, xml_content):
    """Register a scheduled task from XML."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", encoding="utf-16", delete=False) as f:
        f.write(xml_content)
        xml_path = f.name
    try:
        result = subprocess.run(
            ["schtasks", "/create", "/tn", task_name, "/xml", xml_path, "/f"],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    finally:
        try:
            os.unlink(xml_path)
        except OSError:
            pass


def install_task():
    """Register both scheduled tasks (boot + logon) with no time limit."""
    exe_path = _exe_path()

    # Boot trigger, SYSTEM user — runs at startup, no console window
    xml_boot = _create_task_xml(exe_path, trigger="onstart", user_id="S-1-5-18")
    ok = _register_task_xml(TASK_NAME, xml_boot)
    if not ok:
        # Fallback to simple schtasks command
        result = subprocess.run(
            ["schtasks", "/create", "/tn", TASK_NAME, "/tr", f'"{exe_path}"',
             "/sc", "onstart", "/ru", "SYSTEM", "/rl", "HIGHEST", "/f"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            logger.error("Failed to create boot task: %s", result.stderr.strip())

    # Logon trigger, current user
    try:
        user = os.getlogin()
    except Exception:
        user = os.environ.get("USERNAME", "")
    if user:
        xml_logon = _create_task_xml(exe_path, trigger="onlogon", user_id=user)
        _register_task_xml(TASK_NAME_LOGON, xml_logon)


def ensure_scheduled_task():
    """Make sure scheduled task is registered and points to current exe.

    - If not installed: register and print hint
    - If installed but wrong path: re-register with current path
    - If installed and correct: do nothing
    """
    exe_path = os.path.normpath(_exe_path()).lower()

    if not is_task_installed():
        if is_admin():
            try:
                install_task()
                logger.info("Scheduled task registered for auto-start")
            except Exception as e:
                logger.warning("Failed to register scheduled task: %s", e)
        else:
            logger.warning("Not running as admin - cannot register scheduled task")
    else:
        # Check if path matches
        result = subprocess.run(
            ["schtasks", "/query", "/tn", TASK_NAME, "/v", "/fo", "list"],
            capture_output=True, text=True, timeout=10,
        )
        needs_update = True
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "Task To Run" in line:
                    task_exe = os.path.normpath(line.split(":", 1)[1].strip().strip('"')).lower()
                    if task_exe == exe_path:
                        needs_update = False
                    break

        if needs_update and is_admin():
            try:
                install_task()
                logger.info("Scheduled task path updated to: %s", exe_path)
            except Exception as e:
                logger.warning("Failed to update scheduled task: %s", e)


def start_task():
    """Manually run the scheduled task."""
    result = subprocess.run(
        ["schtasks", "/run", "/tn", TASK_NAME],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        subprocess.run(
            ["schtasks", "/run", "/tn", TASK_NAME_LOGON],
            capture_output=True, text=True, timeout=30,
        )


def remove_task():
    """Remove the scheduled tasks."""
    subprocess.run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"], capture_output=True, text=True, timeout=10)
    subprocess.run(["schtasks", "/delete", "/tn", TASK_NAME_LOGON, "/f"], capture_output=True, text=True, timeout=10)
