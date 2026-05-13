import os
import sys
import signal
import threading
from agent.config import AgentConfig
from agent.logger import setup_logger
from agent.register import register_agent
from agent.heartbeat import heartbeat_loop
from agent.collector import resource_loop, config_loop, skills_loop
from agent.task_runner import task_loop

logger = setup_logger("main")

stop_event = threading.Event()


def signal_handler(sig, frame):
    logger.info("Received signal %s, shutting down...", sig)
    stop_event.set()


def self_check(config):
    """Basic self-check: verify connectivity."""
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

    logger.info("Self-check passed")
    return True


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    config_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    config = AgentConfig(config_path)

    # First-run setup: ensure center_url and machine_code are configured
    config.ensure_center_url()
    config.ensure_machine_code()

    logger.info("OpenClaw Center Agent starting...")
    logger.info("Center URL: %s", config.center_url)
    logger.info("Machine code: %s", config.machine_code)
    logger.info("Agent version: %s", config.agent_version_display)

    if not self_check(config):
        logger.error("Self-check failed, exiting")
        sys.exit(1)

    if not register_agent(config):
        logger.error("Registration failed, exiting")
        sys.exit(1)

    # Ensure scheduled task is registered (for auto-start on boot/login)
    from agent.service import ensure_scheduled_task
    ensure_scheduled_task()

    # Start background threads
    threads = [
        threading.Thread(target=heartbeat_loop, args=(config, stop_event), name="heartbeat", daemon=True),
        threading.Thread(target=resource_loop, args=(config, stop_event), name="resource", daemon=True),
        threading.Thread(target=config_loop, args=(config, stop_event), name="config", daemon=True),
        threading.Thread(target=skills_loop, args=(config, stop_event), name="skills", daemon=True),
        threading.Thread(target=task_loop, args=(config, stop_event), name="task", daemon=True),
    ]

    for t in threads:
        t.start()
        logger.info("Started thread: %s", t.name)

    logger.info("Agent is running.")

    # Block forever until stop signal
    stop_event.wait()
    logger.info("Agent stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"FATAL ERROR: {e}")
        traceback.print_exc(file=sys.stderr)
        try:
            os.makedirs(r"C:\ProgramData\OpenClawCenterAgent\logs", exist_ok=True)
            with open(r"C:\ProgramData\OpenClawCenterAgent\logs\error.log", "w", encoding="utf-8") as f:
                f.write(f"FATAL ERROR: {e}\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        sys.exit(1)
