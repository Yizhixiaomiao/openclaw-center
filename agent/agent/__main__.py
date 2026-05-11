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

    # --service mode: delegate to pywin32 HandleCommandLine immediately
    # (install/remove/start/stop commands must not trigger interactive setup)
    if "--service" in sys.argv:
        from agent.service import run_as_service
        run_as_service()
        return

    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    config = AgentConfig(config_path)

    # First-run setup: ensure center_url and machine_code are configured
    config.ensure_center_url()
    config.ensure_machine_code()

    logger.info("OpenClaw Center Agent starting...")
    logger.info("Center URL: %s", config.center_url)
    logger.info("Machine code: %s", config.machine_code)

    if not self_check(config):
        logger.error("Self-check failed, exiting")
        sys.exit(1)

    if not register_agent(config):
        logger.error("Registration failed, exiting")
        sys.exit(1)

    # Auto-install as Windows service after first registration
    from agent.service import is_service_installed, install_service, start_service, is_admin
    if not is_service_installed():
        if is_admin():
            try:
                install_service()
                start_service()
                logger.info("Agent registered as Windows service. Starting service mode...")
                print("Agent 已注册为 Windows 服务并启动，本窗口将自动关闭。")
                return
            except Exception as e:
                logger.warning("Failed to install service: %s (will run in console mode)", e)
        else:
            logger.warning("Not running as admin - cannot install service. Run as administrator to enable auto-start.")
            print("提示：以管理员身份运行可自动注册为 Windows 服务，实现开机自启。")

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

    logger.info("Agent is running. Press Ctrl+C to stop.")

    # Wait for stop signal
    stop_event.wait()
    logger.info("Agent stopped.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback, os
        print(f"FATAL ERROR: {e}")
        traceback.print_exc(file=sys.stderr)
        try:
            os.makedirs(r"C:\ProgramData\OpenClawCenterAgent\logs", exist_ok=True)
            with open(r"C:\ProgramData\OpenClawCenterAgent\logs\error.log", "w", encoding="utf-8") as f:
                f.write(f"FATAL ERROR: {e}\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        input("Press Enter to exit...")
        sys.exit(1)
