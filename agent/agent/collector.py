import os
import json
import platform
import subprocess
import zipfile
import io
import base64
import hashlib
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


def _find_config_file(directory):
    """Find a JSON config file in the given directory."""
    priority_names = ["config.json", "settings.json", "openclaw.json", "appsettings.json"]
    for name in priority_names:
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            return path
    for fname in os.listdir(directory):
        if fname.endswith(".json"):
            path = os.path.join(directory, fname)
            if os.path.isfile(path):
                return path
    return None


def get_openclaw_config(config):
    """Read OpenClaw configuration summary."""
    result = {
        "openclaw_config_hash": "",
        "model_provider": "",
        "model_name": "",
        "skills": "[]",
        "prompt_versions": "{}",
        "config_content": "",
        "config_file_path": "",
    }
    config_path = config.openclaw_config_path
    if not config_path or not os.path.exists(config_path):
        return result
    actual_path = config_path
    if os.path.isdir(config_path):
        actual_path = _find_config_file(config_path)
        if not actual_path:
            logger.debug("No JSON config file found in directory: %s", config_path)
            return result
    try:
        with open(actual_path, "r", encoding="utf-8") as f:
            content = f.read()
        result["config_file_path"] = actual_path
        result["config_content"] = content
        result["openclaw_config_hash"] = hashlib.md5(content.encode()).hexdigest()
        try:
            data = json.loads(content)
            result["model_provider"] = data.get("model_provider", data.get("provider", ""))
            result["model_name"] = data.get("model_name", data.get("model", ""))
        except json.JSONDecodeError:
            pass
    except Exception as e:
        logger.warning("Failed to read OpenClaw config: %s", e)
    return result


def package_skill_folder(skill_path):
    """Package an entire skill folder into a base64-encoded zip."""
    zip_buffer = io.BytesIO()
    file_count = 0
    total_size = 0
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(skill_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, skill_path)
                zf.write(fpath, arcname)
                file_count += 1
                total_size += os.path.getsize(fpath)
    zip_data = zip_buffer.getvalue()
    return {
        "zip_base64": base64.b64encode(zip_data).decode("utf-8"),
        "checksum": hashlib.sha256(zip_data).hexdigest(),
        "file_count": file_count,
        "total_size": total_size,
    }


def _parse_skill_md_description(skill_path):
    """Extract description from SKILL.md YAML frontmatter."""
    skill_md = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md):
        return ""
    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.startswith("---"):
            return ""
        end = content.find("---", 3)
        if end == -1:
            return ""
        import yaml
        frontmatter = yaml.safe_load(content[3:end])
        if isinstance(frontmatter, dict):
            return frontmatter.get("description", "")
    except Exception:
        pass
    return ""


def get_installed_skills(config):
    """Scan skills directory and return full skill info with packaged content."""
    skills = []
    skills_dir = config.openclaw_skills_dir
    if not skills_dir or not os.path.isdir(skills_dir):
        return skills
    try:
        for name in os.listdir(skills_dir):
            skill_path = os.path.join(skills_dir, name)
            if os.path.isdir(skill_path):
                # Read manifest for metadata
                version = ""
                skill_name = name
                description = ""
                manifest = os.path.join(skill_path, "manifest.json")
                if os.path.exists(manifest):
                    try:
                        with open(manifest, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            skill_name = data.get("name", name)
                            version = data.get("version", "")
                            description = data.get("description", "")
                    except Exception:
                        pass

                # Fallback: extract description from SKILL.md frontmatter
                if not description:
                    description = _parse_skill_md_description(skill_path)

                # Package entire folder as base64 zip
                pkg = package_skill_folder(skill_path)
                skills.append({
                    "code": name,
                    "name": skill_name,
                    "version": version,
                    "description": description,
                    "file_count": pkg["file_count"],
                    "total_size": pkg["total_size"],
                    "zip_base64": pkg["zip_base64"],
                    "checksum": pkg["checksum"],
                })
    except Exception as e:
        logger.warning("Failed to scan skills: %s", e)
    return skills


def sync_skills(config):
    """Report full skill packages to center server."""
    skills = get_installed_skills(config)
    if not skills:
        logger.info("No skills found to sync")
        return
    # Skip metadata-only skills for the full sync
    pkg_skills = [s for s in skills if s.get("file_count", 0) > 0]
    if not pkg_skills:
        logger.info("No skill packages to sync (all empty)")
        return

    url = f"{config.center_url}/api/agent/skills/sync"
    payload = {
        "machine_code": config.machine_code,
        "skills": json.dumps(pkg_skills),
    }
    try:
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Skills synced: %d packages uploaded", data.get("uploaded", 0))
    except requests.RequestException as e:
        logger.warning("Skills sync failed: %s", e)


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
        "current_user": config.current_user,
        "agent_config_content": config.agent_config_content,
        "agent_config_path": config.agent_config_path,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Resource report sent: cpu=%.1f%% mem=%.1f%% disk=%.1f%%",
                     info["cpu_usage"], info["memory_usage"], info["disk_usage"])
    except requests.RequestException as e:
        logger.warning("Resource report failed: %s", e)


def report_config(config):
    """Report OpenClaw config and skills metadata to center."""
    url = f"{config.center_url}/api/agent/config/report"
    oc_config = get_openclaw_config(config)
    skills = get_installed_skills(config)
    # Send only lightweight metadata in config report
    meta_skills = [{"code": s["code"], "version": s.get("version", "")} for s in skills]
    payload = {
        "machine_code": config.machine_code,
        "openclaw_config_hash": oc_config["openclaw_config_hash"],
        "model_provider": oc_config["model_provider"],
        "model_name": oc_config["model_name"],
        "skills": json.dumps(meta_skills),
        "config_content": oc_config["config_content"],
        "config_file_path": oc_config["config_file_path"],
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
    """Periodically report OpenClaw config and skills metadata."""
    while not stop_event.is_set():
        report_config(config)
        stop_event.wait(config.config_interval)


def skills_loop(config, stop_event):
    """Periodically sync full skill packages to center."""
    while not stop_event.is_set():
        sync_skills(config)
        stop_event.wait(config.config_interval)
