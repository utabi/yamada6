"""Runtime エージェントのエントリーポイント。
現時点では最小ループのみを提供し、将来的に PDCA / ドライブ連携を組み込む。"""

from __future__ import annotations

import asyncio
import os
from contextlib import AsyncExitStack

from loguru import logger

from agent.runtime.app import RuntimeApp, RuntimeConfig


async def _run() -> None:
    """ランタイムメインループ。"""
    config = RuntimeConfig.from_env(os.environ)
    async with AsyncExitStack() as stack:
        app = RuntimeApp(config=config)
        await stack.enter_async_context(app.lifecycle())
        await app.run_forever()


def main() -> None:
    """同期エントリーポイント。"""
    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        logger.info("Runtime stopped by user")


if __name__ == "__main__":
    main()
