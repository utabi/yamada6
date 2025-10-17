"""Utility for applying patch artifacts (stub implementation)."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ApplyResult:
    ok: bool
    detail: str
    artifact_path: Path
    command: str


class PatchExecutor:
    """Execute patch application logic (placeholder for future git worktree)."""

    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace

    def apply(self, artifact_path: Path) -> ApplyResult:
        hook = os.environ.get("PATCH_APPLY_HOOK")
        if hook:
            completed = subprocess.run(
                [hook, str(artifact_path)],
                cwd=self._workspace,
                capture_output=True,
                text=True,
            )
            detail = completed.stdout.strip() or completed.stderr.strip() or "hook executed"
            return ApplyResult(completed.returncode == 0, detail, artifact_path, command=hook)

        mode = os.environ.get("PATCH_APPLY_MODE", "noop").lower().strip()
        if mode == "fail":
            return ApplyResult(False, "Simulated failure (PATCH_APPLY_MODE=fail)", artifact_path, command="noop")
        return ApplyResult(True, "Simulated apply success", artifact_path, command="noop")
