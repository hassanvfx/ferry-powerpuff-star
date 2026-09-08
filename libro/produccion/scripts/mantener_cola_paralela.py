#!/usr/bin/env python3
"""Maintain a bounded Kie image queue for an approved independent run.

The runner never attaches a prior page.  It is safe to invoke repeatedly: each
cycle polls existing receipts, downloads completed PNGs, retries failed jobs
with exponential backoff, and fills only the available queue slots.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PRODUCTION = Path(__file__).resolve().parents[1]
REPO = PRODUCTION.parents[1]
KIE = Path("/Users/hassan/repos/kie-api/.venv/bin/kie-cli")
RUNNER = PRODUCTION / "scripts" / "generar_paginas.py"
NO_CREDIT_MARKERS = ("no credit", "insufficient credit", "insufficient balance", "out of credits", "saldo insuficiente", "sin créditos", "sin creditos")


class QueueBusyError(RuntimeError):
    """Raised when another invocation is already mutating this run's state."""


def load(file: Path) -> dict:
    return json.loads(file.read_text(encoding="utf-8"))


def save(file: Path, value: dict) -> None:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def repo_path(value: str) -> Path:
    return (REPO / value).resolve()


def prompt_path(value: str) -> Path:
    return (PRODUCTION / value).resolve()


def prompt_digest(plan: dict) -> str:
    """Hash the exact ordered source prompts that a queue cycle will submit."""
    digest = hashlib.sha256()
    for page in plan["pages"]:
        source = prompt_path(page["prompt"])
        if not source.is_file():
            raise SystemExit(f"Prompt file not found: {source}")
        digest.update(page["id"].encode())
        digest.update(b"\0")
        digest.update(source.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def validated_plan(config: dict) -> dict:
    """Reject a queue whose page set, attachments, or locked prompts drifted."""
    if config.get("schema_version") != 1:
        raise SystemExit("Unsupported run schema.")
    if config.get("status") != "ready":
        raise SystemExit("Run is not ready.")
    generation = config["generation"]
    if generation.get("model") != "gpt-image-2" or generation.get("aspect_ratio") != "2:3" or generation.get("resolution") != "2K":
        raise SystemExit("This queue requires gpt-image-2 at 2K in 2:3.")
    if not generation.get("approved_references_only"):
        raise SystemExit("This queue requires approved references only.")
    if config["operation"].get("previous_page_reference") != "never_attached":
        raise SystemExit("This queue requires previous_page_reference=never_attached.")
    if config["operation"].get("stop_on_no_credits") is not True:
        raise SystemExit("This queue requires stop_on_no_credits=true.")
    if config["operation"].get("queued_timeout_seconds") != 300:
        raise SystemExit("This queue requires queued_timeout_seconds=300.")
    plan = load(repo_path(config["source_plan"]))
    if len(plan.get("pages", [])) != 90 or len({page.get("id") for page in plan["pages"]}) != 90:
        raise SystemExit("This queue requires exactly 90 unique pages.")
    if any(page.get("previous_page_reference", {}).get("attached") for page in plan["pages"]):
        raise SystemExit("Plan contains a forbidden previous-page attachment.")
    expected = config.get("prompt_lock", {}).get("sha256")
    actual = prompt_digest(plan)
    if not expected or expected != actual:
        raise SystemExit("Prompt lock does not match the source prompts; review and explicitly re-lock before running.")
    return plan


def now() -> datetime:
    return datetime.now(timezone.utc)


def no_credits(text: str) -> bool:
    folded = text.casefold()
    return any(marker in folded for marker in NO_CREDIT_MARKERS)


def lock_for(state_file: Path):
    """Hold an advisory lock only for the duration of one queue cycle."""
    lock_file = state_file.with_suffix(state_file.suffix + ".lock")
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_file.open("w", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        handle.close()
        raise QueueBusyError("Another queue cycle is already running for this configuration.") from error
    return handle


def unlock(handle) -> None:
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    handle.close()


def halt_for_no_credits(state: dict, detail: str) -> None:
    state["halted"] = {"reason": "no_credits", "at": now().isoformat(), "detail": detail}


def due(value: str | None) -> bool:
    return not value or now() >= datetime.fromisoformat(value)


def queued_age_seconds(receipt: Path) -> float | None:
    """Return receipt age only when Kie's submission time is trustworthy."""
    submitted_at = load(receipt).get("submittedAt")
    if not isinstance(submitted_at, str):
        return None
    try:
        submitted = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0, (now() - submitted).total_seconds())


def status(job_id: str) -> tuple[dict | None, str]:
    result = subprocess.run([str(KIE), "job-status", job_id, "--model", "gpt-image-2-image-to-image", "--json"], text=True, capture_output=True)
    stdout = result.stdout.strip()
    try:
        item = json.loads(stdout) if stdout else None
    except json.JSONDecodeError:
        item = None
    # kie-cli returns a non-zero exit status for a provider-declared failed job,
    # while still supplying the authoritative JSON status on stdout.
    if isinstance(item, dict) and item.get("status"):
        return item, ""
    if result.returncode:
        return None, "\n".join(part for part in (stdout, result.stderr.strip()) if part) or "Kie status check failed."
    return None, "Kie status response did not include a status."


def archive(receipt: Path, retries: Path) -> None:
    retries.mkdir(parents=True, exist_ok=True)
    job_id = load(receipt).get("jobId", "unknown")
    receipt.replace(retries / f"{receipt.stem}--{job_id}.json")


def schedule_retry(state: dict, page_id: str, reason: str, retries: int, base_seconds: int) -> bool:
    attempts = state.setdefault("attempts", {}).get(page_id, 0) + 1
    state["attempts"][page_id] = attempts
    if attempts > retries:
        state.setdefault("failed", {})[page_id] = {"reason": reason, "attempts": attempts, "at": now().isoformat()}
        return False
    delay = base_seconds * (2 ** (attempts - 1))
    state.setdefault("not_before", {})[page_id] = (now() + timedelta(seconds=delay)).isoformat()
    return True


def has_cached_output(output: Path) -> bool:
    """Only a non-empty local PNG is authoritative evidence of completion."""
    return output.is_file() and output.stat().st_size > 0


def refresh_completed_cache(plan: dict, storage: dict[str, Path], state: dict) -> tuple[set[str], bool]:
    """Synchronize persisted completion metadata from the local output directory."""
    completed = state.setdefault("completed", {})
    on_disk = {
        page["id"] for page in plan["pages"]
        if has_cached_output(storage["output_dir"] / f"{page['id']}.png")
    }
    changed = False
    for page_id in on_disk:
        if page_id not in completed:
            completed[page_id] = {"source": "output_cache", "at": now().isoformat()}
            changed = True
    for page_id in list(completed):
        if page_id not in on_disk:
            completed.pop(page_id)
            changed = True
    return on_disk, changed


def submit(config: dict, storage: dict[str, Path], page_id: str) -> tuple[bool, str]:
    generation = config["generation"]
    command = [sys.executable, str(RUNNER), "--plan", str(repo_path(config["source_plan"])), "--page", page_id,
               "--approved-references-only", "--live", "--model", generation["model"], "--aspect-ratio", generation["aspect_ratio"],
               "--resolution", generation["resolution"], "--jobs-dir", str(storage["jobs_dir"]), "--prompt-output-dir", str(storage["prompt_snapshot_dir"])]
    result = subprocess.run(command, text=True, capture_output=True)
    detail = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    return result.returncode == 0, detail


def cycle(config: dict) -> dict:
    op = config["operation"]
    plan = validated_plan(config)
    storage = {key: repo_path(value) for key, value in config["storage"].items()}
    state_file = storage["state_file"]
    state = load(state_file) if state_file.is_file() else {"attempts": {}, "not_before": {}, "failed": {}}
    completed_on_disk, cache_changed = refresh_completed_cache(plan, storage, state)
    if state.get("halted", {}).get("reason") == "no_credits":
        if cache_changed:
            save(state_file, state)
        return {"action": "no_credits", "detail": state["halted"].get("detail", "Kie reported insufficient credits."),
                "completed": len(completed_on_disk)}
    active: list[str] = []
    downloaded: list[str] = []
    submitted: list[str] = []
    checked_jobs: list[dict] = []
    queued_timeouts: list[dict] = []
    status_errors: list[dict] = []
    for page in plan["pages"]:
        page_id = page["id"]
        receipt = storage["jobs_dir"] / f"{page_id}.json"
        output = storage["output_dir"] / f"{page_id}.png"
        if has_cached_output(output) or not receipt.is_file():
            continue
        item, error = status(load(receipt)["jobId"])
        if item is None:
            if no_credits(error):
                halt_for_no_credits(state, error)
                save(state_file, state); return {"action": "no_credits", "detail": error}
            status_errors.append({"page": page_id, "detail": error})
            active.append(page_id)
            continue
        job_status = item.get("status")
        checked = {"page": page_id, "status": job_status}
        if item.get("error"):
            checked["error"] = item["error"]
        checked_jobs.append(checked)
        if job_status == "queued":
            age_seconds = queued_age_seconds(receipt)
            if age_seconds is not None and age_seconds > op["queued_timeout_seconds"]:
                archive(receipt, storage["jobs_dir"] / "retries")
                schedule_retry(state, page_id, "Kie queued timeout after 300 seconds", op["max_retries"], op["retry_base_seconds"])
                queued_timeouts.append({"page": page_id, "age_seconds": round(age_seconds),
                                        "attempt": state["attempts"][page_id]})
                continue
            active.append(page_id); continue
        if job_status == "running":
            active.append(page_id); continue
        if job_status == "succeeded" and item.get("outputUrl"):
            storage["output_dir"].mkdir(parents=True, exist_ok=True)
            result = subprocess.run(["curl", "-L", "--fail", "--output", str(output), item["outputUrl"]], text=True, capture_output=True)
            if result.returncode:
                active.append(page_id); continue
            downloaded.append(page_id)
            completed_on_disk.add(page_id)
            state.setdefault("completed", {})[page_id] = {"source": "output_cache", "at": now().isoformat()}
            continue
        archive(receipt, storage["jobs_dir"] / "retries")
        schedule_retry(state, page_id, f"Kie status={job_status!r}; detail={item.get('error')!r}", op["max_retries"], op["retry_base_seconds"])
    candidates = [page["id"] for page in plan["pages"] if page["id"] not in state.get("failed", {})
                  and page["id"] not in completed_on_disk
                  and not (storage["jobs_dir"] / f"{page['id']}.json").is_file()
                  and due(state.get("not_before", {}).get(page["id"]))]
    while len(active) < op["max_active"] and candidates:
        page_id = candidates.pop(0)
        ok, error = submit(config, storage, page_id)
        if not ok:
            if no_credits(error):
                halt_for_no_credits(state, error)
                save(state_file, state); return {"action": "no_credits", "detail": error}
            schedule_retry(state, page_id, error or "submission failed", op["max_retries"], op["retry_base_seconds"])
            save(state_file, state)
            return {"action": "retry_scheduled", "page": page_id, "attempt": state["attempts"][page_id]}
        elif (storage["jobs_dir"] / f"{page_id}.json").is_file():
            active.append(page_id)
            submitted.append(page_id)
            state.setdefault("not_before", {}).pop(page_id, None)
        else:
            schedule_retry(state, page_id, "Kie accepted no job receipt", op["max_retries"], op["retry_base_seconds"])
            save(state_file, state)
            return {"action": "retry_scheduled", "page": page_id, "attempt": state["attempts"][page_id]}
        if candidates and len(active) < op["max_active"]:
            time.sleep(op["submission_pause_seconds"])
    save(state_file, state)
    complete = all(page["id"] in completed_on_disk or page["id"] in state.get("failed", {}) for page in plan["pages"])
    completed = len(completed_on_disk)
    return {"action": "complete" if complete else "maintained", "active": active, "active_count": len(active),
            "completed": completed, "remaining": len(plan["pages"]) - completed, "downloaded": downloaded,
            "submitted": submitted, "checked_jobs": checked_jobs, "queued_timeouts": queued_timeouts,
            "status_errors": status_errors, "failed": sorted(state.get("failed", {}))}


def locked_cycle(config: dict) -> dict:
    """Run one mutation-safe cycle; a concurrent runner simply reports busy."""
    state_file = repo_path(config["storage"]["state_file"])
    try:
        handle = lock_for(state_file)
    except QueueBusyError:
        return {"action": "busy", "detail": "Another V5 queue cycle is running."}
    try:
        return cycle(config)
    finally:
        unlock(handle)


def dry_run(config: dict) -> dict:
    plan = validated_plan(config)
    storage = {key: repo_path(value) for key, value in config["storage"].items()}
    next_pages = [page["id"] for page in plan["pages"] if not has_cached_output(storage["output_dir"] / f"{page['id']}.png")
                  and not (storage["jobs_dir"] / f"{page['id']}.json").is_file()]
    return {"action": "dry_run", "pages": 90, "max_active": config["operation"]["max_active"],
            "submission_pause_seconds": config["operation"]["submission_pause_seconds"],
            "next_pages": next_pages[:config["operation"]["max_active"]]}


def watch(config: dict, *, live: bool, interval_seconds: int, max_cycles: int) -> None:
    """Continuously run resumable cycles and emit one detailed status per check."""
    count = 0
    while max_cycles == 0 or count < max_cycles:
        count += 1
        started = time.monotonic()
        checked_at = now().isoformat()
        try:
            result = locked_cycle(config) if live else dry_run(config)
        except Exception as error:  # Keep a long-running operator alive after transient local failures.
            result = {"action": "error", "detail": f"{type(error).__name__}: {error}"}
        print(json.dumps({"event": "cycle", "cycle": count, "at": checked_at, "result": result}, ensure_ascii=False,
                         indent=2, sort_keys=True), flush=True)
        if result["action"] in {"complete", "no_credits"}:
            return
        if max_cycles and count >= max_cycles:
            return
        time.sleep(max(0, interval_seconds - (time.monotonic() - started)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--watch", action="store_true", help="Keep polling and maintaining the queue until interrupted, complete, or out of credits.")
    parser.add_argument("--interval-seconds", type=int, default=60, help="Seconds between watch cycles (default: 60).")
    parser.add_argument("--max-cycles", type=int, default=0, help="Stop watch after this many cycles; 0 means unlimited.")
    args = parser.parse_args()
    if args.interval_seconds <= 0:
        parser.error("--interval-seconds must be positive")
    if args.max_cycles < 0:
        parser.error("--max-cycles cannot be negative")
    config = load(args.config)
    if args.watch:
        watch(config, live=args.live, interval_seconds=args.interval_seconds, max_cycles=args.max_cycles)
    else:
        print(json.dumps(dry_run(config) if args.dry_run else locked_cycle(config), ensure_ascii=False,
                         indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
