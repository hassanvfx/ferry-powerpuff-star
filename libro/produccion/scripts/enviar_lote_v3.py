#!/usr/bin/env python3
"""Submit the next independent V3 batch, with no previous-page image attached."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PRODUCTION = Path(__file__).resolve().parents[1]
REPO = PRODUCTION.parents[1]
RUNNER = PRODUCTION / "scripts" / "generar_paginas.py"
KIE = Path("/Users/hassan/repos/kie-api/.venv/bin/kie-cli")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(value: str) -> Path:
    return (REPO / value).resolve()


def status(job_id: str) -> dict:
    result = subprocess.run([str(KIE), "job-status", job_id, "--model", "gpt-image-2-image-to-image", "--json"], text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "Kie status check failed.")
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    config = load(args.config)
    if config.get("status") != "ready":
        raise SystemExit("V3 is not ready; review the cleaned prompt lock first.")
    if not args.live:
        raise SystemExit("Use --live only after reviewing the batch.")
    generation, storage = config["generation"], {key: repo_path(value) for key, value in config["storage"].items()}
    plan = load(repo_path(config["source_plan"]))
    batch_size = config["operation"]["batch_size"]
    batch = next((group for group in (plan["pages"][offset:offset + batch_size] for offset in range(0, len(plan["pages"]), batch_size))
                  if not all((storage["output_dir"] / f"{page['id']}.png").is_file() for page in group)), None)
    if batch is None:
        print(json.dumps({"action": "complete", "pages": len(plan["pages"])})); return
    if any(page.get("previous_page_reference", {}).get("attached") for page in batch):
        raise SystemExit("V3 forbids previous-page attachments.")
    receipts = [storage["jobs_dir"] / f"{page['id']}.json" for page in batch]
    existing = [(page, receipt) for page, receipt in zip(batch, receipts) if receipt.is_file()]
    if existing:
        states = [status(load(receipt)["jobId"]) for _, receipt in existing]
        if any(item.get("status") in {"queued", "running"} for item in states):
            print(json.dumps({"action": "waiting_batch", "pages": [page["id"] for page in batch]})); return
        failed = [item for item in states if item.get("status") != "succeeded" or not item.get("outputUrl")]
        if failed:
            raise SystemExit("Kie reported a failed V3 batch job.")
        storage["output_dir"].mkdir(parents=True, exist_ok=True)
        for (page, _), item in zip(existing, states):
            output = storage["output_dir"] / f"{page['id']}.png"
            if not output.is_file():
                result = subprocess.run(["curl", "-L", "--fail", "--output", str(output), item["outputUrl"]], text=True)
                if result.returncode:
                    raise SystemExit(f"Could not download {page['id']}.")
        if len(existing) == len(batch):
            print(json.dumps({"action": "downloaded_batch", "pages": [page["id"] for page in batch]})); return
        batch = [page for page, receipt in zip(batch, receipts) if not receipt.is_file()]
    command = [sys.executable, str(RUNNER), "--plan", str(repo_path(config["source_plan"])), "--approved-references-only", "--live",
               "--model", generation["model"], "--aspect-ratio", generation["aspect_ratio"], "--resolution", generation["resolution"],
               "--jobs-dir", str(storage["jobs_dir"]), "--prompt-output-dir", str(storage["prompt_snapshot_dir"]),
               "--delay-between-pages", str(config["operation"].get("delay_between_submissions_seconds", 0))]
    for page in batch:
        command.extend(["--page", page["id"]])
    result = subprocess.run(command, text=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    print(json.dumps({"action": "submitted_batch", "pages": [page["id"] for page in batch]}))


if __name__ == "__main__":
    main()
