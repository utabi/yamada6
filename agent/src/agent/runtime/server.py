"""Runtime API サーバの生成ヘルパー。"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException

from agent.runtime.app import PendingPatch, RuntimeApp


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

    @app.post("/control/pause", status_code=202)
    async def pause() -> dict[str, str]:
        runtime.pause()
        return {"status": "paused"}

    @app.post("/control/resume", status_code=202)
    async def resume() -> dict[str, str]:
        runtime.resume()
        return {"status": "running"}

    class PatchPayload(BaseModel):
        patch_id: str = Field(..., description="staging で発行されたパッチ ID")
        summary: str
        author: str
        created_at: str

    @app.post("/patches", status_code=202)
    async def receive_patch(payload: PatchPayload) -> dict[str, str]:
        if runtime.is_paused():
            runtime.enqueue_patch(
                PendingPatch(
                    patch_id=payload.patch_id,
                    summary=payload.summary,
                    author=payload.author,
                    created_at=payload.created_at,
                )
            )
            return {"status": "queued"}
        raise HTTPException(status_code=409, detail="Runtime must be paused before queuing patches")

    return app
