import sys
import signal
import threading
from agent.config import AgentConfig
from agent.logger import setup_logger
from agent.register import register_agent
from agent.heartbeat import heartbeat_loop
from agent.collector import resource_loop, config_loop
from agent.task_runner import task_loop

logger = setup_logger("main")

stop_event = threading.Event()


def signal_handler(sig, frame):
    logger.info("Received signal %s, shutting down...", sig)
    stop_event.set()


def self_check(config):
    """Basic self-check: verify connectivity and config."""
    logger.info("Running self-check...")
    import requests
    try:
        resp = requests.get(f"{config.center_url}/api/health", timeout=10)
        if resp.status_code == 200:
            logger.info("Center server reachable: %s", resp.json())
        else:
            logger.warning("Center server returned status %d", resp.status_code)
    except requests.RequestException as e:
        logger.error("Cannot reach center server: %s", e)
        return False

    if not config.machine_code:
        logger.error("machine_code not configured in config.yaml")
        return False

    logger.info("Self-check passed")
    return True


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    config = AgentConfig(config_path)

    logger.info("OpenClaw Center Agent starting...")
    logger.info("Center URL: %s", config.center_url)
    logger.info("Machine code: %s", config.machine_code)

    if not self_check(config):
        logger.error("Self-check failed, exiting")
        sys.exit(1)

    if not register_agent(config):
        logger.error("Registration failed, exiting")
        sys.exit(1)

    # Start background threads
    threads = [
        threading.Thread(target=heartbeat_loop, args=(config, stop_event), name="heartbeat", daemon=True),
        threading.Thread(target=resource_loop, args=(config, stop_event), name="resource", daemon=True),
        threading.Thread(target=config_loop, args=(config, stop_event), name="config", daemon=True),
        threading.Thread(target=task_loop, args=(config, stop_event), name="task", daemon=True),
    ]

    for t in threads:
        t.start()
        logger.info("Started thread: %s", t.name)

    logger.info("Agent is running. Press Ctrl+C to stop.")

    # Wait for stop signal
    stop_event.wait()
    logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
