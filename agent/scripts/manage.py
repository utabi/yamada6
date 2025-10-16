#!/usr/bin/env python3
"""エージェント管理スクリプトの雛形。"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def run_tests() -> int:
    result = subprocess.run([sys.executable, "-m", "pytest"], cwd=ROOT / "agent")
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Yamada6 agent 管理ツール")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("test", help="pytest を実行")
    args = parser.parse_args()

    if args.command == "test":
        raise SystemExit(run_tests())

    parser.print_help()


if __name__ == "__main__":
    main()
