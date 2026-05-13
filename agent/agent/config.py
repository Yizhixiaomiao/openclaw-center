import os
import sys
import uuid
import socket
import yaml

_DEFAULT_VERSION = "1.0.0"


def _detect_agent_version():
    """Detect version from version.txt: next to exe, config dir, or fallback."""
    search_dirs = []
    if getattr(sys, 'frozen', False):
        search_dirs.append(os.path.dirname(sys.executable))
    search_dirs.append(os.path.dirname(os.path.abspath(__file__)))
    search_dirs.append(r"C:\ProgramData\OpenClawCenterAgent")

    for d in search_dirs:
        try:
            vf = os.path.join(d, "version.txt")
            if os.path.isfile(vf):
                with open(vf, "r") as f:
                    v = f.read().strip()
                    if v:
                        return v
        except Exception:
            pass
    return _DEFAULT_VERSION


AGENT_VERSION = _detect_agent_version()

DEFAULT_CONFIG_PATH = r"C:\ProgramData\OpenClawCenterAgent\config.yaml"
DEFAULT_LOG_DIR = r"C:\ProgramData\OpenClawCenterAgent\logs"
DEFAULT_CACHE_DIR = r"C:\ProgramData\OpenClawCenterAgent\cache"
DEFAULT_BACKUP_DIR = r"C:\ProgramData\OpenClawCenterAgent\backup"
DEFAULT_PACKAGES_DIR = r"C:\ProgramData\OpenClawCenterAgent\packages"
DEFAULT_SCRIPTS_DIR = r"C:\ProgramData\OpenClawCenterAgent\scripts"

DEFAULT_CONFIG_TEMPLATE = """\
# OpenClaw Center Agent Configuration

# Center server URL
center_url: ""

# Machine unique code (auto-generated if empty)
machine_code: ""

# Authentication token (optional)
token: ""

# Heartbeat interval in seconds
heartbeat_interval: 60

# Resource collection interval in seconds
resource_interval: 300

# Config and skills collection interval in seconds
config_interval: 600

# Task pull interval in seconds
task_interval: 60

# OpenClaw configuration file path (optional)
openclaw_config_path: ''

# OpenClaw skills directory (optional)
openclaw_skills_dir: ''

# OpenClaw prompts directory (optional)
openclaw_prompts_dir: ''

# OpenClaw profiles directory containing USER.md and IDENTITY.md (optional)
openclaw_profiles_dir: ''

# Log settings
log_max_bytes: 10485760
log_backup_count: 5

# Retry settings
max_retries: 3
retry_delay: 10
"""


def _generate_machine_code():
    hostname = socket.gethostname().upper().replace("-", "").replace("_", "")
    short = hostname[:12] if len(hostname) > 12 else hostname
    suffix = uuid.uuid4().hex[:4].upper()
    return f"OC-{short}-{suffix}"


class AgentConfig:
    def __init__(self, config_path=None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self._data = {}
        self._init_config()
        self.load()

    def _init_config(self):
        """Create default config file if it doesn't exist."""
        self._ensure_dirs()
        if not os.path.exists(self.config_path):
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(DEFAULT_CONFIG_TEMPLATE)

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
        self._ensure_dirs()

    def reload(self):
        """Reload config from disk (e.g. after remote update)."""
        self.load()

    def _ensure_dirs(self):
        for d in [DEFAULT_LOG_DIR, DEFAULT_CACHE_DIR, DEFAULT_BACKUP_DIR, DEFAULT_PACKAGES_DIR, DEFAULT_SCRIPTS_DIR]:
            os.makedirs(d, exist_ok=True)

    def _save(self):
        """Write current _data back to config file."""
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def ensure_center_url(self):
        """Prompt for center_url if not configured."""
        url = self._data.get("center_url", "")
        if not url:
            print("\n" + "=" * 50)
            print("OpenClaw Center Agent - 首次配置")
            print("=" * 50)
            url = input("请输入控制中心URL (例如 http://10.10.3.233:8000): ").strip()
            if not url:
                url = "http://localhost:8000"
            if not url.startswith("http"):
                url = "http://" + url
            self._data["center_url"] = url
            self._save()
            print(f"控制中心URL已保存: {url}\n")

    def ensure_machine_code(self):
        """Generate machine_code if not configured."""
        code = self._data.get("machine_code", "")
        if not code:
            code = _generate_machine_code()
            self._data["machine_code"] = code
            self._save()
            print(f"机器码已自动生成: {code}")

    @property
    def center_url(self):
        return self._data.get("center_url", "")

    @property
    def agent_version_display(self):
        return AGENT_VERSION

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
    def current_user(self):
        try:
            return os.getlogin()
        except Exception:
            import getpass
            return getpass.getuser()

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
    def openclaw_profiles_dir(self):
        return self._data.get("openclaw_profiles_dir", "")

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

    @property
    def agent_config_content(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    @property
    def agent_config_path(self):
        return self.config_path
