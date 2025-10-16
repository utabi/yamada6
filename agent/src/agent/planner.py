"""Planner モジュールの最小実装。"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(slots=True)
class Plan:
    """生成されたプランの抽象化。"""

    created_at: dt.datetime
    summary: str


class Planner:
    """将来、PDCA/ミッション管理に置き換える。その骨組み。"""

    async def plan(self) -> Plan:
        now = dt.datetime.utcnow()
        summary = "最小プラン: 状態監視とログ保存の準備を続ける"
        return Plan(created_at=now, summary=summary)
