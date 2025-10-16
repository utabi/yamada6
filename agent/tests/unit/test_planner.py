import asyncio

from agent.planner import Planner


def test_plan_returns_plan():
    planner = Planner()
    plan = asyncio.run(planner.plan())
    assert plan.summary
