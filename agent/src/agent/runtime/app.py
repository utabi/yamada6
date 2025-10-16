"""Runtime アプリケーションの骨格。"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from typing import AsyncIterator, Dict, List, Mapping, Optional

from loguru import logger

from agent.executor import Executor
from agent.executor import ExecutionResult
from agent.planner import Plan, Planner
from agent.scheduler import ScheduledTask, Scheduler


@dataclass(slots=True)
class RuntimeConfig:
    """ランタイム設定のプレースホルダ。

    必要に応じて APIエンドポイントやストレージパスを追加していく。
    """

    loop_interval_seconds: float = 10.0

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "RuntimeConfig":
        try:
            interval = float(env.get("YAMADA_LOOP_INTERVAL", 10))
        except ValueError:
            interval = 10.0
        return cls(loop_interval_seconds=interval)


@dataclass(slots=True)
class PendingPatch:
    """staging から受け取ったパッチメタデータ。"""

    patch_id: str
    summary: str
    author: str
    created_at: str


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
        }

    def enqueue_patch(self, patch: PendingPatch) -> None:
        self._pending_patches[patch.patch_id] = patch

    def has_patch(self, patch_id: str) -> bool:
        return patch_id in self._pending_patches

    def pop_patch(self, patch_id: str) -> Optional[PendingPatch]:
        return self._pending_patches.pop(patch_id, None)
