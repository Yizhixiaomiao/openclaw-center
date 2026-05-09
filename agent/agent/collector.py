import os
import json
import platform
import subprocess
import requests
from agent.logger import setup_logger

logger = setup_logger("collector")


def get_system_info():
    """Collect CPU, memory, disk usage."""
    info = {"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0}
    try:
        import psutil
        info["cpu_usage"] = round(psutil.cpu_percent(interval=1), 2)
        mem = psutil.virtual_memory()
        info["memory_usage"] = round(mem.percent, 2)
        disk = psutil.disk_usage("C:\\")
        info["disk_usage"] = round(disk.percent, 2)
    except ImportError:
        logger.debug("psutil not available, using fallback")
        try:
            result = subprocess.run(
                ["wmic", "OS", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/format:list"],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.strip().split("\n")
            total = free = 0
            for line in lines:
                if line.startswith("TotalVisibleMemorySize="):
                    total = int(line.split("=")[1])
                elif line.startswith("FreePhysicalMemory="):
                    free = int(line.split("=")[1])
            if total > 0:
                info["memory_usage"] = round((1 - free / total) * 100, 2)
        except Exception as e:
            logger.warning("Fallback memory collection failed: %s", e)
    return info


def get_openclaw_config(config):
    """Read OpenClaw configuration summary."""
    result = {
        "openclaw_config_hash": "",
        "model_provider": "",
        "model_name": "",
        "skills": "[]",
        "prompt_versions": "{}",
    }
    config_path = config.openclaw_config_path
    if not config_path or not os.path.exists(config_path):
        return result
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        import hashlib
        result["openclaw_config_hash"] = hashlib.md5(content.encode()).hexdigest()
        # Try to parse as JSON or YAML for model info
        try:
            data = json.loads(content)
            result["model_provider"] = data.get("model_provider", data.get("provider", ""))
            result["model_name"] = data.get("model_name", data.get("model", ""))
        except json.JSONDecodeError:
            pass
    except Exception as e:
        logger.warning("Failed to read OpenClaw config: %s", e)
    return result


def get_installed_skills(config):
    """Scan skills directory for installed skills."""
    skills = []
    skills_dir = config.openclaw_skills_dir
    if not skills_dir or not os.path.isdir(skills_dir):
        return skills
    try:
        for name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, name)
            if os.path.isdir(skill_path):
                version = ""
                manifest = os.path.join(skill_path, "manifest.json")
                if os.path.exists(manifest):
                    try:
                        with open(manifest, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            version = data.get("version", "")
                    except Exception:
                        pass
                skills.append({"code": name, "version": version})
    except Exception as e:
        logger.warning("Failed to scan skills: %s", e)
    return skills


def report_resources(config):
    """Report system resources to center."""
    url = f"{config.center_url}/api/agent/heartbeat"
    info = get_system_info()
    payload = {
        "machine_code": config.machine_code,
        "status": "online",
        "cpu_usage": info["cpu_usage"],
        "memory_usage": info["memory_usage"],
        "disk_usage": info["disk_usage"],
        "service_status": "running",
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Resource report sent: cpu=%.1f%% mem=%.1f%% disk=%.1f%%",
                     info["cpu_usage"], info["memory_usage"], info["disk_usage"])
    except requests.RequestException as e:
        logger.warning("Resource report failed: %s", e)


def report_config(config):
    """Report OpenClaw config and skills to center."""
    url = f"{config.center_url}/api/agent/config/report"
    oc_config = get_openclaw_config(config)
    skills = get_installed_skills(config)
    payload = {
        "machine_code": config.machine_code,
        "openclaw_config_hash": oc_config["openclaw_config_hash"],
        "model_provider": oc_config["model_provider"],
        "model_name": oc_config["model_name"],
        "skills": json.dumps(skills),
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Config report sent: %d skills found", len(skills))
    except requests.RequestException as e:
        logger.warning("Config report failed: %s", e)


def resource_loop(config, stop_event):
    """Periodically report system resources."""
    while not stop_event.is_set():
        report_resources(config)
        stop_event.wait(config.resource_interval)


def config_loop(config, stop_event):
    """Periodically report OpenClaw config and skills."""
    while not stop_event.is_set():
        report_config(config)
        stop_event.wait(config.config_interval)
