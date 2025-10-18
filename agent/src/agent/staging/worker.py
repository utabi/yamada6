"""Simple staging worker that generates a demo patch and applies it via the runtime API."""

from __future__ import annotations

import argparse
import difflib
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx


def build_patch(target: Path, patch_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).isoformat()
    original = target.read_text(encoding="utf-8").splitlines()
    addition = f"- staging worker note {timestamp}"
    modified = original + [addition]

    patch_text = "".join(
        difflib.unified_diff(
            original,
            modified,
            fromfile=f"a/{target.name}",
            tofile=f"b/{target.name}",
            lineterm="\n",
        )
    )
    tmp_dir = Path(tempfile.mkdtemp())
    patch_file = tmp_dir / f"{patch_id}.diff"
    patch_file.write_text(patch_text, encoding="utf-8")
    return patch_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a demo staging worker")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080", help="Runtime API base URL")
    parser.add_argument(
        "--target",
        default=Path(__file__).resolve().parents[3] / "docs" / "OVERVIEW.md",
        type=Path,
        help="Target file to modify",
    )
    parser.add_argument("--author", default="staging-worker")
    parser.add_argument("--notes", default="auto-generated")
    parser.add_argument("--resume", action="store_true", help="Resume runtime loop after apply")
    args = parser.parse_args()

    patch_id = f"auto-{int(datetime.now(timezone.utc).timestamp())}"
    patch_file = build_patch(args.target, patch_id)
    patch_text = patch_file.read_text(encoding="utf-8")

    payload: dict[str, Any] = {
        "patch_id": patch_id,
        "summary": f"Auto note {patch_id}",
        "author": args.author,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_uri": f"file://{patch_file}",
        "notes": args.notes,
        "diff_preview": patch_text,
    }

    with httpx.Client(timeout=10) as client:
        client.post(f"{args.base_url}/control/pause", timeout=5)
        resp = client.post(f"{args.base_url}/patches", json=payload)
        resp.raise_for_status()
        apply_resp = client.post(f"{args.base_url}/patches/{patch_id}/apply")
        apply_resp.raise_for_status()
        if args.resume:
            client.post(f"{args.base_url}/control/resume")

    print(f"Patch {patch_id} applied: {apply_resp.json().get('status')}")


if __name__ == "__main__":
    main()
