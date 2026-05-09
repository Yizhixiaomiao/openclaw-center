import os
import yaml

DEFAULT_CONFIG_PATH = r"C:\ProgramData\OpenClawCenterAgent\config.yaml"
DEFAULT_LOG_DIR = r"C:\ProgramData\OpenClawCenterAgent\logs"
DEFAULT_CACHE_DIR = r"C:\ProgramData\OpenClawCenterAgent\cache"
DEFAULT_BACKUP_DIR = r"C:\ProgramData\OpenClawCenterAgent\backup"
DEFAULT_PACKAGES_DIR = r"C:\ProgramData\OpenClawCenterAgent\packages"
DEFAULT_SCRIPTS_DIR = r"C:\ProgramData\OpenClawCenterAgent\scripts"


class AgentConfig:
    def __init__(self, config_path=None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._data = {}
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [DEFAULT_LOG_DIR, DEFAULT_CACHE_DIR, DEFAULT_BACKUP_DIR, DEFAULT_PACKAGES_DIR, DEFAULT_SCRIPTS_DIR]:
            os.makedirs(d, exist_ok=True)

    @property
    def center_url(self):
        return self._data.get("center_url", "http://localhost:8000")

    @property
    def machine_code(self):
        return self._data.get("machine_code", "")

    @property
    def token(self):
        return self._data.get("token", "")

    @property
    def heartbeat_interval(self):
        return self._data.get("heartbeat_interval", 60)

    @property
    def resource_interval(self):
        return self._data.get("resource_interval", 300)

    @property
    def config_interval(self):
        return self._data.get("config_interval", 600)

    @property
    def task_interval(self):
        return self._data.get("task_interval", 60)

    @property
    def openclaw_config_path(self):
        return self._data.get("openclaw_config_path", "")

    @property
    def openclaw_skills_dir(self):
        return self._data.get("openclaw_skills_dir", "")

    @property
    def openclaw_prompts_dir(self):
        return self._data.get("openclaw_prompts_dir", "")

    @property
    def log_max_bytes(self):
        return self._data.get("log_max_bytes", 10 * 1024 * 1024)

    @property
    def log_backup_count(self):
        return self._data.get("log_backup_count", 5)

    @property
    def max_retries(self):
        return self._data.get("max_retries", 3)

    @property
    def retry_delay(self):
        return self._data.get("retry_delay", 10)
