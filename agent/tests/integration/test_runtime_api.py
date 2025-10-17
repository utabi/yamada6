from http import HTTPStatus
import os
from pathlib import Path

from fastapi.testclient import TestClient

from agent.runtime.app import PendingPatch, RuntimeApp, RuntimeConfig
from agent.runtime.server import create_app


def create_runtime(tmp_path, monkeypatch):
    patch_dir = tmp_path / "patches"
    monkeypatch.setenv("PATCH_STORAGE_DIR", str(patch_dir))
    config = RuntimeConfig.from_env(os.environ)
    runtime = RuntimeApp(config=config)
    return runtime, patch_dir, config


def test_runtime_api_health_and_status(tmp_path, monkeypatch):
    runtime, patch_dir, config = create_runtime(tmp_path, monkeypatch)
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
        artifact_src = tmp_path / "diff.patch"
        artifact_src.write_text("diff --git a b", encoding="utf-8")
        patch_resp = client.post(
            "/patches",
            json={
                "patch_id": "patch-1",
                "summary": "Fix test",
                "author": "staging",
                "created_at": "2025-10-16T00:00:00Z",
                "artifact_uri": artifact_src.as_uri(),
                "test_report_uri": "file:///workspace/report.json",
                "notes": "unit tests passed",
            },
        )
        assert patch_resp.status_code == HTTPStatus.ACCEPTED
        queued = runtime.snapshot()["pending_patches"]
        assert queued and queued[0]["patch_id"] == "patch-1"

        stored_file = Path(runtime.snapshot()["patch_storage_dir"]) / "patch-1.json"
        assert stored_file.exists()

        list_resp = client.get("/patches")
        assert list_resp.status_code == HTTPStatus.OK
        listed = list_resp.json()
        assert listed[0]["artifact_uri"] == artifact_src.as_uri()

        detail_resp = client.get("/patches/patch-1")
        assert detail_resp.status_code == HTTPStatus.OK
        assert detail_resp.json()["notes"] == "unit tests passed"

        apply_resp = client.post("/patches/patch-1/apply")
        assert apply_resp.status_code == HTTPStatus.ACCEPTED
        assert apply_resp.json()["status"] == "apply_success"
        assert runtime.snapshot()["pending_patches"] == []
        assert not stored_file.exists()
        copied_artifact = patch_dir / "patch-1.artifact"
        assert copied_artifact.exists()
        applied_list = client.get("/patches/applied")
        assert applied_list.status_code == HTTPStatus.OK
        assert applied_list.json()[0]["artifact_local_path"].endswith("patch-1.artifact")

        audit_resp = client.get("/patches/audit")
        assert audit_resp.status_code == HTTPStatus.OK
        audit_entries = audit_resp.json()
        statuses = {entry["status"] for entry in audit_entries}
        assert {"queued", "artifact_copied", "apply_success"}.issubset(statuses)

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
                "artifact_uri": artifact_src.as_uri(),
            },
        )
        assert conflict.status_code == HTTPStatus.CONFLICT

        not_found = client.post("/patches/patch-unknown/apply")
        assert not_found.status_code == HTTPStatus.CONFLICT


def test_restart_reload_pending_patches(tmp_path, monkeypatch):
    runtime, patch_dir, _ = create_runtime(tmp_path, monkeypatch)
    artifact_src = tmp_path / "persist.patch"
    artifact_src.write_text("diff --git c d", encoding="utf-8")
    runtime.enqueue_patch(
        PendingPatch(
            patch_id="persist-1",
            summary="Persisted patch",
            author="staging",
            created_at="2025-10-16T00:00:00Z",
            artifact_uri=artifact_src.as_uri(),
        )
    )

    # リスタートを模擬
    new_runtime, _, _ = create_runtime(tmp_path, monkeypatch)
    snapshot = new_runtime.snapshot()
    assert snapshot["pending_patches"]
    assert snapshot["pending_patches"][0]["patch_id"] == "persist-1"


def test_patch_apply_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("PATCH_APPLY_MODE", "fail")
    runtime, patch_dir, _ = create_runtime(tmp_path, monkeypatch)
    app = create_app(runtime)

    with TestClient(app) as client:
        client.post("/control/pause")
        artifact_src = tmp_path / "fail.patch"
        artifact_src.write_text("diff --git e f", encoding="utf-8")

        client.post(
            "/patches",
            json={
                "patch_id": "fail-1",
                "summary": "Should fail",
                "author": "staging",
                "created_at": "2025-10-16T00:00:00Z",
                "artifact_uri": artifact_src.as_uri(),
            },
        )

        response = client.post("/patches/fail-1/apply")
        assert response.status_code == HTTPStatus.ACCEPTED
        payload = response.json()
        assert payload["status"] == "apply_failed"
        assert runtime.snapshot()["pending_patches"]

        audit_entries = client.get("/patches/audit").json()
        statuses = {entry["status"] for entry in audit_entries}
        assert "apply_failed" in statuses

        # JSON メタデータが残っていること（再試行可能）
        stored_file = Path(runtime.snapshot()["patch_storage_dir"]) / "fail-1.json"
        assert stored_file.exists()

        rollback_resp = client.post("/patches/fail-1/rollback")
        assert rollback_resp.status_code == HTTPStatus.ACCEPTED
        assert rollback_resp.json()["status"] == "rollback_success"

        audit_entries = client.get("/patches/audit").json()
        statuses = {entry["status"] for entry in audit_entries}
        assert "rollback_success" in statuses

    monkeypatch.delenv("PATCH_APPLY_MODE", raising=False)
