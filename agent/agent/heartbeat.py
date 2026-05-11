import time
import threading
import requests
from agent.config import AGENT_VERSION
from agent.logger import setup_logger

logger = setup_logger("heartbeat")


def send_heartbeat(config):
    """Send heartbeat to center server."""
    url = f"{config.center_url}/api/agent/heartbeat"
    payload = {
        "machine_code": config.machine_code,
        "status": "online",
        "service_status": "running",
        "agent_version": AGENT_VERSION,
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.debug("Heartbeat sent successfully")
        return resp.json()
    except requests.RequestException as e:
        logger.warning("Heartbeat failed: %s", e)
        return None


def heartbeat_loop(config, stop_event):
    """Run heartbeat in a loop with configurable interval."""
    while not stop_event.is_set():
        data = send_heartbeat(config)
        if data and data.get("upgrade"):
            from agent.updater import handle_upgrade
            handle_upgrade(config, data["upgrade"])
        stop_event.wait(config.heartbeat_interval)
