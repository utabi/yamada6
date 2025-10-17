"""Runtime アプリケーションの骨格。"""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import shutil
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import AsyncIterator, Dict, List, Mapping, Optional
from urllib.parse import urlparse

from loguru import logger

from agent.executor import Executor
from agent.executor import ExecutionResult
from agent.planner import Plan, Planner
from agent.scheduler import ScheduledTask, Scheduler
from agent.runtime.patch_executor import ApplyResult, PatchExecutor


@dataclass(slots=True)
class RuntimeConfig:
    """ランタイム設定のプレースホルダ。

    必要に応じて APIエンドポイントやストレージパスを追加していく。
    """

    loop_interval_seconds: float = 10.0
    patch_storage_dir: Path = Path("state/patches")

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "RuntimeConfig":
        try:
            interval = float(env.get("YAMADA_LOOP_INTERVAL", 10))
        except ValueError:
            interval = 10.0
        patch_dir = Path(env.get("PATCH_STORAGE_DIR", "state/patches")).expanduser()
        if not patch_dir.is_absolute():
            patch_dir = Path.cwd() / patch_dir
        return cls(loop_interval_seconds=interval, patch_storage_dir=patch_dir)


@dataclass(slots=True)
class PendingPatch:
    """staging から受け取ったパッチメタデータ。"""

    patch_id: str
    summary: str
    author: str
    created_at: str
    artifact_uri: str
    test_report_uri: Optional[str] = None
    notes: Optional[str] = None
    artifact_local_path: Optional[str] = None


class RuntimeApp:
    """Planner / Executor / Scheduler を束ねる最小実装。"""

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._planner = Planner()
        self._executor = Executor()
        self._scheduler = Scheduler()
        self._running = False
        self._paused = False
        self._loop_count = 0
        self._last_plan: Optional[Plan] = None
        self._last_task: Optional[ScheduledTask] = None
        self._last_execution: Optional[ExecutionResult] = None
        self._pending_patches: Dict[str, PendingPatch] = {}
        self._patch_storage_dir = self._config.patch_storage_dir
        self._patch_storage_dir.mkdir(parents=True, exist_ok=True)
        self._audit_log_path = self._patch_storage_dir / "audit.log"
        workspace = Path(os.environ.get("PATCH_WORKSPACE", Path.cwd()))
        self._patch_executor = PatchExecutor(workspace=workspace)
        self._reload_patches()

    @asynccontextmanager
    async def lifecycle(self) -> AsyncIterator[None]:
        logger.info("RuntimeApp lifecycle start")
        self._running = True
        try:
            yield
        finally:
            self._running = False
            logger.info("RuntimeApp lifecycle end")

    async def run_forever(self) -> None:
        logger.info("Runtime loop start (interval=%ss)", self._config.loop_interval_seconds)
        while self._running:
            if self._paused:
                await asyncio.sleep(self._config.loop_interval_seconds)
                continue
            plan = await self._planner.plan()
            self._last_plan = plan

            task = await self._scheduler.schedule(plan)
            self._last_task = task

            execution = await self._executor.execute(task.plan)
            self._last_execution = execution

            self._loop_count += 1
            await asyncio.sleep(self._config.loop_interval_seconds)

        logger.info("Runtime loop stop")

    @property
    def planner(self) -> Planner:
        return self._planner

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def scheduler(self) -> Scheduler:
        return self._scheduler

    def stop(self) -> None:
        self._running = False

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def is_paused(self) -> bool:
        return self._paused

    def snapshot(self) -> dict:
        def plan_payload(plan: Optional[Plan]) -> Optional[dict]:
            if plan is None:
                return None
            return {
                "summary": plan.summary,
                "created_at": plan.created_at.isoformat(),
            }

        task = self._last_task
        execution = self._last_execution
        return {
            "loop_interval_seconds": self._config.loop_interval_seconds,
            "loop_count": self._loop_count,
            "paused": self._paused,
            "last_plan": plan_payload(self._last_plan),
            "last_scheduled": None
            if task is None
            else {
                "priority": task.priority,
            },
            "last_execution": None
            if execution is None
            else {
                "status": execution.status,
                "detail": execution.detail,
                "completed_at": execution.completed_at.isoformat(),
            },
            "pending_patches": [asdict(patch) for patch in self._pending_patches.values()],
            "applied_patches": [asdict(patch) for patch in self._applied_patches],
            "patch_storage_dir": str(self._patch_storage_dir),
        }

    def enqueue_patch(self, patch: PendingPatch) -> None:
        self._pending_patches[patch.patch_id] = patch
        self._write_patch_file(patch)
        self._write_audit_log(patch, status="queued", extra={"artifact_uri": patch.artifact_uri})

    def has_patch(self, patch_id: str) -> bool:
        return patch_id in self._pending_patches

    def pop_patch(self, patch_id: str) -> Optional[PendingPatch]:
        patch = self._pending_patches.pop(patch_id, None)
        if patch is not None:
            self._delete_patch_file(patch.patch_id)
        return patch

    def get_patch(self, patch_id: str) -> Optional[PendingPatch]:
        return self._pending_patches.get(patch_id)

    def list_patches(self) -> List[PendingPatch]:
        return list(self._pending_patches.values())

    def fetch_patch_artifact(self, patch: PendingPatch) -> Path:
        parsed = urlparse(patch.artifact_uri)
        if parsed.scheme == "file":
            source = Path(parsed.path)
            if not source.exists():
                raise FileNotFoundError(source)
            destination = self._patch_storage_dir / f"{patch.patch_id}.artifact"
            shutil.copy2(source, destination)
            patch.artifact_local_path = str(destination)
            self._write_audit_log(
                patch,
                status="artifact_copied",
                extra={"source": patch.artifact_uri, "destination": str(destination)},
            )
            self._write_patch_file(patch)
            return destination
        raise ValueError(f"Unsupported artifact URI scheme: {parsed.scheme or 'missing'}")

    def apply_patch(self, patch_id: str) -> ApplyResult:
        patch = self.get_patch(patch_id)
        if patch is None:
            raise KeyError(patch_id)

        artifact_path = self.fetch_patch_artifact(patch)
        result = self._patch_executor.apply(artifact_path)
        if result.ok:
            self.pop_patch(patch_id)
            self._applied_patches.append(patch)
            self._write_audit_log(
                patch,
                status="apply_success",
                extra={
                    "artifact_local_path": patch.artifact_local_path,
                    "detail": result.detail,
                    "command": result.command,
                },
            )
        else:
            self._write_audit_log(
                patch,
                status="apply_failed",
                extra={
                    "detail": result.detail,
                    "command": result.command,
                },
            )
        return result

    def list_applied_patches(self) -> List[PendingPatch]:
        return list(self._applied_patches)

    def iter_audit_log(self) -> List[dict]:
        if not self._audit_log_path.exists():
            return []
        entries: List[dict] = []
        for line in self._audit_log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                logger.error("Invalid audit line: %s", exc)
        return entries

    def _write_patch_file(self, patch: PendingPatch) -> None:
        path = self._patch_storage_dir / f"{patch.patch_id}.json"
        path.write_text(json.dumps(asdict(patch), ensure_ascii=False, indent=2), encoding="utf-8")

    def _delete_patch_file(self, patch_id: str) -> None:
        path = self._patch_storage_dir / f"{patch_id}.json"
        if path.exists():
            path.unlink()

    def _write_audit_log(self, patch: PendingPatch, status: str, extra: Optional[dict] = None) -> None:
        record = {
            "patch_id": patch.patch_id,
            "status": status,
            "timestamp": dt.datetime.utcnow().isoformat() + "Z",
            "summary": patch.summary,
        }
        if extra:
            record.update(extra)
        with self._audit_log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _reload_patches(self) -> None:
        self._applied_patches: List[PendingPatch] = []
        for file in self._patch_storage_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                patch = PendingPatch(**data)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to load patch metadata %s: %s", file, exc)
            else:
                self._pending_patches[patch.patch_id] = patch
        # 過去に適用済みのレコードは audit log から再構築可能だが、ここでは起動時に空とする
