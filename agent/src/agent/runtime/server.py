"""Runtime API サーバの生成ヘルパー。"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import List

from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from agent.runtime.app import PendingPatch, RuntimeApp


class PatchPayload(BaseModel):
    patch_id: str = Field(..., description="staging で発行されたパッチ ID")
    summary: str
    author: str
    created_at: str
    artifact_uri: str = Field(..., description="パッチファイルの URI (volume/S3 など)")
    test_report_uri: str | None = Field(None, description="テストレポートへのリンク")
    notes: str | None = Field(None, description="補足メモ")


class PatchResponse(BaseModel):
    patch_id: str
    summary: str
    author: str
    created_at: str
    artifact_uri: str
    test_report_uri: str | None = None
    notes: str | None = None


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

    @app.get("/patches", response_model=List[PatchResponse])
    async def list_patches() -> List[PatchResponse]:
        return [PatchResponse(**asdict(patch)) for patch in runtime.list_patches()]

    @app.get("/patches/{patch_id}", response_model=PatchResponse)
    async def get_patch(patch_id: str) -> PatchResponse:
        patch = runtime.get_patch(patch_id)
        if patch is None:
            raise HTTPException(status_code=404, detail="Patch not found")
        return PatchResponse(**asdict(patch))

    @app.get("/patches/applied", response_model=List[PatchResponse])
    async def list_applied() -> List[PatchResponse]:
        return [PatchResponse(**asdict(patch)) for patch in runtime.list_applied_patches()]

    @app.get("/patches/audit", response_model=List[dict])
    async def audit_log() -> List[dict]:
        return runtime.iter_audit_log()

    @app.post("/control/pause", status_code=202)
    async def pause() -> dict[str, str]:
        runtime.pause()
        return {"status": "paused"}

    @app.post("/control/resume", status_code=202)
    async def resume() -> dict[str, str]:
        runtime.resume()
        return {"status": "running"}

    @app.post("/patches", status_code=202)
    async def receive_patch(payload: PatchPayload) -> dict[str, str]:
        if not runtime.is_paused():
            raise HTTPException(status_code=409, detail="Runtime must be paused before queuing patches")
        if runtime.has_patch(payload.patch_id):
            raise HTTPException(status_code=409, detail="Patch already queued")

        runtime.enqueue_patch(
            PendingPatch(
                patch_id=payload.patch_id,
                summary=payload.summary,
                author=payload.author,
                created_at=payload.created_at,
                artifact_uri=payload.artifact_uri,
                test_report_uri=payload.test_report_uri,
                notes=payload.notes,
            )
        )
        return {"status": "queued"}

    @app.post("/patches/{patch_id}/apply", status_code=202)
    async def apply_patch(patch_id: str) -> dict[str, str]:
        if not runtime.is_paused():
            raise HTTPException(status_code=409, detail="Pause runtime before applying patches")

        patch = runtime.pop_patch(patch_id)
        if patch is None:
            raise HTTPException(status_code=404, detail="Patch not found")

        # TODO: 実際の git apply / テスト実行をここで実装
        runtime.mark_applied(patch)
        logger.info("Apply patch requested: %s", patch.patch_id)
        return {"status": "apply_requested", "patch_id": patch.patch_id}

    return app
