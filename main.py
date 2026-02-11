from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from lumenguard.runner import run_forever, run_once_file_state


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LUMENGUARD monitor")
    parser.add_argument("--once", action="store_true", help="Виконати один цикл і завершити")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if args.once:
        run_once_file_state()
    else:
        run_forever()
