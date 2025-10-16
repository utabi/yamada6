"""Scheduler モジュールの骨格。"""

from __future__ import annotations

from dataclasses import dataclass

from agent.planner import Plan


@dataclass(slots=True)
class ScheduledTask:
    """スケジューラが選択したタスクを表現。"""

    plan: Plan
    priority: int = 0


class Scheduler:
    """スケジューリングの最小実装。"""

    async def schedule(self, plan: Plan) -> ScheduledTask:
        return ScheduledTask(plan=plan, priority=0)
