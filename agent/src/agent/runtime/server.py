"""Runtime API サーバの生成ヘルパー。"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent.runtime.app import RuntimeApp


def create_app(runtime: RuntimeApp) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        async with runtime.lifecycle():
            loop_task = asyncio.create_task(runtime.run_forever())
            try:
                yield
            finally:
                runtime.stop()
                await loop_task

    app = FastAPI(lifespan=lifespan)

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/status")
    async def status() -> dict:
        return runtime.snapshot()

    return app
