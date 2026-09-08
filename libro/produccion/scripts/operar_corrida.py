#!/usr/bin/env python3
"""Operate one resumable, sequential image-production run at a time.

This program never starts work unless both the run is marked ready and --live is
provided.  A scheduler should call --once at most once per heartbeat.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PRODUCTION = Path(__file__).resolve().parents[1]
REPO = PRODUCTION.parents[1]
KIE = Path("/Users/hassan/repos/kie-api/.venv/bin/kie-cli")
RUNNER = PRODUCTION / "scripts" / "generar_paginas.py"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def path(value: str) -> Path:
    return (REPO / value).resolve()


def production_path(value: str) -> Path:
    return (PRODUCTION / value).resolve()


def prompt_digest(plan: dict) -> str:
    digest = hashlib.sha256()
    for page in plan["pages"]:
        prompt = production_path(page["prompt"])
        digest.update(page["id"].encode())
        digest.update(b"\0")
        digest.update(prompt.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def preflight(config: dict) -> tuple[dict, dict[str, Path]]:
    if config.get("schema_version") != 1:
        raise SystemExit("Unsupported run schema.")
    generation = config["generation"]
    if generation.get("aspect_ratio") != "2:3" or generation.get("resolution") != "4K":
        raise SystemExit("This full-production operator requires 2:3 at 4K.")
    if not generation.get("approved_references_only"):
        raise SystemExit("Only approved references are permitted for this run.")
    plan = read(path(config["source_plan"]))
    pages = plan.get("pages", [])
    if len(pages) != 90 or len({item["id"] for item in pages}) != 90:
        raise SystemExit("Expected exactly 90 unique pages.")
    if any(not production_path(item["prompt"]).is_file() for item in pages):
        raise SystemExit("A required prompt file is missing.")
    storage = {name: path(value) for name, value in config["storage"].items()}
    return plan, storage


def state_for(storage: dict[str, Path]) -> dict:
    state_path = storage["state_file"]
    return read(state_path) if state_path.is_file() else {"completed": {}, "failed": None}


def job_status(job_id: str) -> dict:
    result = subprocess.run([str(KIE), "job-status", job_id, "--model", "gpt-image-2-image-to-image", "--json"], text=True, capture_output=True)
    if result.returncode:
        raise SystemExit(result.stderr.strip() or "Kie status check failed.")
    return json.loads(result.stdout)


def submit(config_path: Path, config: dict, storage: dict[str, Path], page_id: str) -> None:
    generation = config["generation"]
    command = [sys.executable, str(RUNNER), "--plan", str(path(config["source_plan"])), "--page", page_id,
               "--approved-references-only", "--continuity-preview-dir", str(storage["output_dir"]), "--live",
               "--model", generation["model"], "--aspect-ratio", generation["aspect_ratio"], "--resolution", generation["resolution"],
               "--jobs-dir", str(storage["jobs_dir"]), "--prompt-output-dir", str(storage["prompt_snapshot_dir"])]
    result = subprocess.run(command, text=True)
    if result.returncode:
        raise SystemExit(result.returncode)


def advance(config_path: Path, config: dict) -> None:
    plan, storage = preflight(config)
    expected = config["prompt_lock"].get("sha256")
    actual = prompt_digest(plan)
    if config.get("status") != "ready" or not expected or expected != actual:
        raise SystemExit("Run is not ready or the prompt lock does not match; freeze and review prompts first.")
    for page in plan["pages"]:
        page_id = page["id"]
        output = storage["output_dir"] / f"{page_id}.png"
        job = storage["jobs_dir"] / f"{page_id}.json"
        if output.is_file():
            continue
        if not job.is_file():
            submit(config_path, config, storage, page_id)
            print(json.dumps({"action": "submitted", "page": page_id}))
            return
        receipt = read(job)
        status = job_status(receipt["jobId"])
        if status.get("status") in {"queued", "running"}:
            print(json.dumps({"action": "waiting", "page": page_id, "status": status["status"]}))
            return
        if status.get("status") != "succeeded" or not status.get("outputUrl"):
            raise SystemExit(f"{page_id}: Kie job {receipt['jobId']} failed or has no output URL.")
        storage["output_dir"].mkdir(parents=True, exist_ok=True)
        result = subprocess.run(["curl", "-L", "--fail", "--output", str(output), status["outputUrl"]], text=True)
        if result.returncode:
            raise SystemExit(f"{page_id}: could not download completed output.")
        print(json.dumps({"action": "downloaded", "page": page_id, "path": str(output)}))
        return
    print(json.dumps({"action": "complete", "pages": 90}))


def main() -> None:
    parser = argparse.ArgumentParser(description="Advance one approved full-production run by at most one state transition.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--print-prompt-lock", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if sum((args.preflight, args.print_prompt_lock, args.once)) != 1:
        parser.error("Choose exactly one action.")
    config = read(args.config)
    plan, _ = preflight(config)
    if args.print_prompt_lock:
        print(prompt_digest(plan)); return
    if args.preflight:
        print(json.dumps({"ok": True, "pages": len(plan["pages"]), "prompt_sha256": prompt_digest(plan)})); return
    if not args.live:
        parser.error("--once requires --live; production submission is an explicit action.")
    advance(args.config, config)


if __name__ == "__main__":
    main()
