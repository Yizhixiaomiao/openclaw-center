import json
import requests
from agent.logger import setup_logger
from agent.prompt_sync import sync_prompt

logger = setup_logger("task_runner")


def pull_tasks(config):
    """Pull pending tasks from center server."""
    url = f"{config.center_url}/api/agent/tasks/pull"
    params = {"machine_code": config.machine_code}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        tasks = data.get("tasks", [])
        if tasks:
            logger.info("Pulled %d task(s)", len(tasks))
        return tasks
    except requests.RequestException as e:
        logger.warning("Pull tasks failed: %s", e)
        return []


def execute_task(config, task):
    """Execute a single task and report result."""
    task_item_id = task["task_item_id"]
    task_type = task["task_type"]
    payload = task.get("payload", "{}")

    logger.info("Executing task item %d (type=%s)", task_item_id, task_type)

    try:
        if task_type == "prompt":
            success, message = sync_prompt(config, payload)
        elif task_type == "config":
            payload_data = json.loads(payload) if isinstance(payload, str) else payload
            if payload_data.get("sync_only"):
                # Trigger immediate config + skills sync
                from agent.collector import report_config, sync_skills
                report_config(config)
                sync_skills(config)
                success, message = True, "Config and skills sync triggered"
            else:
                # Write config file
                target_path = payload_data.get("target_path", "")
                content = payload_data.get("content", "")
                if target_path and content:
                    import os
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    if os.path.normpath(target_path) == os.path.normpath(config.agent_config_path):
                        config.reload()
                        message = f"Agent config written and reloaded: {target_path}"
                    else:
                        message = f"Config written to {target_path}"
                    success = True
                else:
                    success, message = False, "No target_path or content in config payload"
        elif task_type == "skill":
            # Skill sync - download and install skill package
            payload_data = json.loads(payload) if isinstance(payload, str) else payload
            package_url = payload_data.get("package_url", "")
            install_path = payload_data.get("install_path", "")
            skill_code = payload_data.get("skill_code", "")
            checksum = payload_data.get("checksum", "")
            if package_url and install_path:
                import os
                import hashlib
                full_url = package_url if package_url.startswith("http") else f"{config.center_url}{package_url}"
                resp = requests.get(full_url, timeout=120)
                resp.raise_for_status()
                if checksum:
                    actual = hashlib.sha256(resp.content).hexdigest()
                    if actual != checksum:
                        success, message = False, f"Checksum mismatch: expected {checksum}, got {actual}"
                        report_task_result(config, task_item_id, "failed", message)
                        return
                import zipfile, io
                # Extract into install_path/skill_code/ so skill lives in its own folder
                target_dir = os.path.join(install_path, skill_code) if skill_code else install_path
                os.makedirs(target_dir, exist_ok=True)
                # Backup existing
                from agent.prompt_sync import DEFAULT_BACKUP_DIR
                os.makedirs(DEFAULT_BACKUP_DIR, exist_ok=True)
                # Extract
                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    zf.extractall(target_dir)
                success, message = True, f"Skill installed to {target_dir}"
            else:
                success, message = False, "No package_url or install_path in skill payload"
        elif task_type == "skill_remove":
            # Skill removal - delete local skill directory
            payload_data = json.loads(payload) if isinstance(payload, str) else payload
            skill_code = payload_data.get("skill_code", "")
            install_path = payload_data.get("install_path", "") or config.openclaw_skills_dir
            if skill_code:
                import os
                import shutil
                target_dir = os.path.join(install_path, skill_code)
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                    success, message = True, f"Skill directory removed: {target_dir}"
                else:
                    success, message = True, f"Skill directory not found (already removed): {target_dir}"
            else:
                success, message = False, "No skill_code in skill_remove payload"
        elif task_type == "model_config":
            # Model config update
            payload_data = json.loads(payload) if isinstance(payload, str) else payload
            target_path = payload_data.get("target_path", "")
            content = payload_data.get("content", "")
            if target_path and content:
                import os
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(json.loads(content) if isinstance(content, str) else content, f, indent=2, ensure_ascii=False)
                success, message = True, f"Model config written to {target_path}"
            else:
                success, message = False, "No target_path or content in model_config payload"
        else:
            success, message = False, f"Unknown task type: {task_type}"
    except Exception as e:
        logger.error("Task %d execution failed: %s", task_item_id, e)
        success, message = False, str(e)

    report_task_result(config, task_item_id, "success" if success else "failed", message)

    # Trigger immediate heartbeat so center updates status right away
    from agent.heartbeat import send_heartbeat
    send_heartbeat(config)


def report_task_result(config, task_item_id, status, message=""):
    """Report task execution result to center."""
    url = f"{config.center_url}/api/agent/tasks/report"
    payload = {
        "task_item_id": task_item_id,
        "status": status,
        "message": message,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Task result reported: item=%d status=%s", task_item_id, status)
    except requests.RequestException as e:
        logger.warning("Report task result failed: %s", e)


def task_loop(config, stop_event):
    """Periodically pull and execute tasks."""
    while not stop_event.is_set():
        tasks = pull_tasks(config)
        for task in tasks:
            execute_task(config, task)
        stop_event.wait(config.task_interval)
