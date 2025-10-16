"""Runtime アプリケーションの骨格。"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Mapping

from loguru import logger

from agent.executor import Executor
from agent.planner import Planner
from agent.scheduler import Scheduler


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


class RuntimeApp:
    """Planner / Executor / Scheduler を束ねる最小実装。"""

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._planner = Planner()
        self._executor = Executor()
        self._scheduler = Scheduler()
        self._running = False

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
            plan = await self._planner.plan()
            task = await self._scheduler.schedule(plan)
            await self._executor.execute(task)
            await asyncio.sleep(self._config.loop_interval_seconds)

    @property
    def planner(self) -> Planner:
        return self._planner

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def scheduler(self) -> Scheduler:
        return self._scheduler
