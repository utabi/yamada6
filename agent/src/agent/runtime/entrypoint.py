"""Runtime エージェントのエントリーポイント。
現時点では最小ループのみを提供し、将来的に PDCA / ドライブ連携を組み込む。"""

from __future__ import annotations

import os

import uvicorn

from agent.runtime.app import RuntimeApp, RuntimeConfig
from agent.runtime.server import create_app


if __name__ == "__main__":
    config = RuntimeConfig.from_env(os.environ)
    runtime_app = RuntimeApp(config=config)
    app = create_app(runtime_app)

    port = int(os.environ.get("RUNTIME_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
