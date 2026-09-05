"""公开测试版运行配置。"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


APP_VERSION = "4.8"
LOCAL_ENV = "local"
CLOUD_ENV = "community_cloud"


def detect_environment(environ: dict[str, str] | None = None) -> str:
    values = environ if environ is not None else os.environ
    explicit = values.get("DIANZHENTONG_ENV", "").strip().lower()
    aliases = {
        "local": LOCAL_ENV,
        "community_cloud": CLOUD_ENV,
        "cloud": CLOUD_ENV,
        "streamlit_cloud": CLOUD_ENV,
    }
    if explicit:
        return aliases.get(explicit, LOCAL_ENV)
    cloud_signals = ("STREAMLIT_SHARING_MODE", "STREAMLIT_CLOUD", "IS_STREAMLIT_CLOUD")
    return CLOUD_ENV if any(values.get(key) for key in cloud_signals) else LOCAL_ENV


def valid_issues_url(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    parsed = urlparse(candidate)
    if parsed.scheme != "https" or parsed.hostname != "github.com" or parsed.username:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[2] != "issues":
        return None
    return candidate


@dataclass(frozen=True)
class AppConfig:
    environment: str
    storage_path: Path
    storage_is_temporary: bool
    issues_url: str | None
    version: str = APP_VERSION

    @property
    def is_cloud(self) -> bool:
        return self.environment == CLOUD_ENV


def load_config(environ: dict[str, str] | None = None) -> AppConfig:
    values = environ if environ is not None else os.environ
    environment = detect_environment(values)
    configured_path = values.get("DIANZHENTONG_DB_PATH", "").strip()
    if configured_path:
        path = Path(configured_path).expanduser()
        temporary = False
    elif environment == CLOUD_ENV:
        path = Path(tempfile.gettempdir()) / "dianzhentong" / "practice.db"
        temporary = True
    else:
        path = Path(__file__).resolve().parent.parent / "data" / "practice.db"
        temporary = False
    return AppConfig(
        environment=environment,
        storage_path=path,
        storage_is_temporary=temporary,
        issues_url=valid_issues_url(values.get("DIANZHENTONG_ISSUES_URL")),
    )
