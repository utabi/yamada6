"""Executor の骨格。"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from loguru import logger

from agent.planner import Plan


@dataclass(slots=True)
class ExecutionResult:
    """実行結果のサマリ。"""

    completed_at: dt.datetime
    status: str
    detail: str


class Executor:
    """プランに基づいてアクションを行う最小実装。"""

    async def execute(self, plan: Plan) -> ExecutionResult:
        logger.info("Executing plan: {}", plan.summary)
        now = dt.datetime.utcnow()
        return ExecutionResult(completed_at=now, status="noop", detail="まだ実処理は未実装")
