from fastapi.testclient import TestClient
from http import HTTPStatus

from agent.runtime.app import RuntimeApp, RuntimeConfig
from agent.runtime.server import create_app


def test_runtime_api_health_and_status():
    config = RuntimeConfig(loop_interval_seconds=0.01)
    runtime = RuntimeApp(config=config)
    app = create_app(runtime)

    with TestClient(app) as client:
        health = client.get("/healthz")
        assert health.status_code == HTTPStatus.OK
        assert health.json() == {"status": "ok"}

        status = client.get("/status")
        assert status.status_code == HTTPStatus.OK
        payload = status.json()
        assert payload["loop_interval_seconds"] == config.loop_interval_seconds
        assert "last_plan" in payload
        assert payload["paused"] is False

        pause = client.post("/control/pause")
        assert pause.status_code == HTTPStatus.ACCEPTED
        assert runtime.is_paused()

        resume = client.post("/control/resume")
        assert resume.status_code == HTTPStatus.ACCEPTED
        assert runtime.is_paused() is False

        client.post("/control/pause")
        patch_resp = client.post(
            "/patches",
            json={
                "patch_id": "patch-1",
                "summary": "Fix test",
                "author": "staging",
                "created_at": "2025-10-16T00:00:00Z",
            },
        )
        assert patch_resp.status_code == HTTPStatus.ACCEPTED
        queued = runtime.snapshot()["pending_patches"]
        assert queued and queued[0]["patch_id"] == "patch-1"

        apply_resp = client.post("/patches/patch-1/apply")
        assert apply_resp.status_code == HTTPStatus.ACCEPTED
        assert runtime.snapshot()["pending_patches"] == []

        apply_missing = client.post("/patches/patch-1/apply")
        assert apply_missing.status_code == HTTPStatus.NOT_FOUND

        client.post("/control/resume")
        conflict = client.post(
            "/patches",
            json={
                "patch_id": "patch-2",
                "summary": "Should fail",
                "author": "staging",
                "created_at": "2025-10-16T00:00:01Z",
            },
        )
        assert conflict.status_code == HTTPStatus.CONFLICT

        not_found = client.post("/patches/patch-unknown/apply")
        assert not_found.status_code == HTTPStatus.CONFLICT
