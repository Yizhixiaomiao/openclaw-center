import platform
import socket
import requests
from agent.logger import setup_logger

logger = setup_logger("register")


def register_agent(config):
    """Register this agent with the center server."""
    url = f"{config.center_url}/api/agent/register"
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        ip = "127.0.0.1"

    payload = {
        "machine_code": config.machine_code,
        "hostname": hostname,
        "ip": ip,
        "os": f"{platform.system()} {platform.release()}",
        "agent_version": "1.0.0",
    }

    for attempt in range(1, config.max_retries + 1):
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            logger.info("Agent registered successfully: %s", resp.json())
            return True
        except requests.RequestException as e:
            logger.warning("Register attempt %d/%d failed: %s", attempt, config.max_retries, e)
            if attempt < config.max_retries:
                import time
                time.sleep(config.retry_delay)
    logger.error("Failed to register agent after %d attempts", config.max_retries)
    return False
