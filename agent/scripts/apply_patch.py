#!/usr/bin/env python3
"""staging で生成した diff を runtime に適用するための雛形スクリプト。"""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def apply_patch(patch_path: Path) -> int:
    cmd = ["git", "apply", str(patch_path)]
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="パッチ適用ツール")
    parser.add_argument("patch", type=Path, help="適用する diff ファイル")
    args = parser.parse_args()

    code = apply_patch(args.patch)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
