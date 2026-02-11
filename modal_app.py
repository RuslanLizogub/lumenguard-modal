from __future__ import annotations

import sys
from pathlib import Path
import tomllib

import modal

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lumenguard.config import load_runtime_config
from lumenguard.runner import coerce_state, run_cycle

DEFAULT_DEPENDENCIES = [
    "httpx>=0.27,<1.0",
    "modal>=1.0,<2.0",
    "pydantic>=2.8,<3.0",
    "python-dotenv>=1.0,<2.0",
]


def _project_dependencies() -> list[str]:
    pyproject_path = ROOT_DIR / "pyproject.toml"
    if not pyproject_path.exists():
        return DEFAULT_DEPENDENCIES

    with pyproject_path.open("rb") as fp:
        data = tomllib.load(fp)
    dependencies = data.get("project", {}).get("dependencies")
    if isinstance(dependencies, list) and dependencies:
        return [str(item) for item in dependencies]
    return DEFAULT_DEPENDENCIES


app = modal.App("lumenguard-modal")
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(*_project_dependencies())
    .add_local_dir("src", "/root/src", copy=True)
)
config_secret = modal.Secret.from_name(
    "lumenguard-config",
    required_keys=["TELEGRAM_BOT_TOKEN", "MONITOR_CONFIG"],
)
state_dict = modal.Dict.from_name("lumenguard-state", create_if_missing=True)


@app.function(
    image=image,
    schedule=modal.Cron("*/5 * * * *"),
    secrets=[config_secret],
)
def monitor_with_modal() -> None:
    """Modal cron entrypoint: every 5 minutes."""
    config = load_runtime_config()

    raw_state = state_dict.get("state")
    state = coerce_state(raw_state)

    state, has_state_update = run_cycle(config, state)
    if has_state_update:
        state_dict["state"] = state
