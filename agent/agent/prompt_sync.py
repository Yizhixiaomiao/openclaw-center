import os
import json
import shutil
import requests
from datetime import datetime
from agent.logger import setup_logger

logger = setup_logger("prompt_sync")

DEFAULT_BACKUP_DIR = r"C:\ProgramData\OpenClawCenterAgent\backup"


def sync_prompt(config, payload):
    """Download and install a prompt file from center."""
    payload_data = json.loads(payload) if isinstance(payload, str) else payload
    file_url = payload_data.get("file_url", "")
    target_path = payload_data.get("target_path", "")
    content = payload_data.get("content", "")

    if not target_path:
        return False, "No target_path specified"

    # Backup existing file
    if os.path.exists(target_path):
        backup_dir = DEFAULT_BACKUP_DIR
        os.makedirs(backup_dir, exist_ok=True)
        basename = os.path.basename(target_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{basename}.{timestamp}.bak")
        try:
            shutil.copy2(target_path, backup_path)
            logger.info("Backed up %s to %s", target_path, backup_path)
        except Exception as e:
            logger.warning("Backup failed: %s", e)

    # Write content or download file
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if content:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif file_url:
            full_url = file_url if file_url.startswith("http") else f"{config.center_url}{file_url}"
            resp = requests.get(full_url, timeout=60)
            resp.raise_for_status()
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
        else:
            return False, "No content or file_url provided"
        logger.info("Prompt synced to %s", target_path)
        return True, f"Prompt written to {target_path}"
    except Exception as e:
        logger.error("Prompt sync failed: %s", e)
        return False, str(e)
