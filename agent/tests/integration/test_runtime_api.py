from fastapi.testclient import TestClient

from agent.runtime.app import RuntimeApp, RuntimeConfig
from agent.runtime.server import create_app


def test_runtime_api_health_and_status():
    config = RuntimeConfig(loop_interval_seconds=0.01)
    runtime = RuntimeApp(config=config)
    app = create_app(runtime)

    with TestClient(app) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        status = client.get("/status")
        assert status.status_code == 200
        payload = status.json()
        assert payload["loop_interval_seconds"] == config.loop_interval_seconds
        assert "last_plan" in payload
