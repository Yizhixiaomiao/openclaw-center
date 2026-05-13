import os
import sys
import subprocess
import requests
from agent.config import AGENT_VERSION
from agent.logger import setup_logger

logger = setup_logger("updater")


def handle_upgrade(config, upgrade_info):
    """Download new version, replace current exe, restart via scheduled task."""
    new_version = upgrade_info.get("version", "")
    if not new_version:
        return

    if AGENT_VERSION == new_version:
        logger.info("Already at version %s, skipping upgrade", new_version)
        return

    logger.info("Upgrade available: %s -> %s", AGENT_VERSION, new_version)

    download_url = upgrade_info.get("download_url", "/api/agent/download")
    full_url = download_url if download_url.startswith("http") else f"{config.center_url}{download_url}"

    temp_dir = os.path.join(os.path.dirname(sys.executable), "_update")
    os.makedirs(temp_dir, exist_ok=True)
    new_exe = os.path.join(temp_dir, "OpenClawCenterAgent.exe")

    try:
        logger.info("Downloading new version from %s", full_url)
        resp = requests.get(full_url, timeout=120)
        resp.raise_for_status()
        with open(new_exe, "wb") as f:
            f.write(resp.content)
        logger.info("Download complete: %d bytes", len(resp.content))
    except Exception as e:
        logger.error("Download failed: %s", e)
        return

    current_exe = sys.executable
    current_dir = os.path.dirname(current_exe)
    bat_script = os.path.join(temp_dir, "_upgrade.bat")

    with open(bat_script, "w", encoding="gbk") as f:
        f.write(f'''@echo off
echo Upgrading OpenClawCenterAgent...
taskkill /f /im OpenClawCenterAgent.exe >nul 2>&1
timeout /t 2 /nobreak >nul
:retry
del /f "{current_exe}"
if exist "{current_exe}" (
    timeout /t 1 /nobreak >nul
    goto retry
)
copy /y "{new_exe}" "{current_exe}"
if errorlevel 1 (
    echo Upgrade failed!
    exit /b 1
)
del /f "{new_exe}" 2>nul
echo {new_version}> "{current_dir}\\version.txt"
echo Re-registering scheduled task...
schtasks /create /tn OpenClawCenterAgent /tr "{current_exe}" /sc onstart /ru SYSTEM /rl HIGHEST /f >nul 2>&1
schtasks /create /tn OpenClawCenterAgent_Logon /tr "{current_exe}" /sc onlogon /rl HIGHEST /f >nul 2>&1
echo Restarting agent...
timeout /t 1 /nobreak >nul
schtasks /run /tn OpenClawCenterAgent >nul 2>&1
if errorlevel 1 (
    schtasks /run /tn OpenClawCenterAgent_Logon >nul 2>&1
    if errorlevel 1 (
        start /min "" "{current_exe}"
    )
)
rd /q "{temp_dir}" 2>nul
''')

    logger.info("Starting upgrade script...")
    subprocess.Popen(
        ["cmd", "/c", bat_script],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    logger.info("Agent exiting for upgrade to %s", new_version)
    os._exit(0)
