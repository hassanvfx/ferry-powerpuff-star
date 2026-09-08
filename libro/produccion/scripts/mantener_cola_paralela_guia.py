#!/usr/bin/env python3
"""Run a two-stage Kie queue: storyboard guide first, final page second.

Each final page receives its own completed guide PNG as an additional local
reference. The run never attaches a prior story page and keeps all guide and
final state separate from other runs.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PRODUCTION = Path(__file__).resolve().parents[1]
REPO = PRODUCTION.parents[1]
KIE = Path("/Users/hassan/repos/kie-api/.venv/bin/kie-cli")
STYLE = REPO / "libro/arte/referencias/chibi-superhero-comic-style-reference.png"
SHEETS = {
    "ferry": REPO / "libro/arte/referencias/ferry-character-sheet-v2.png",
    "hassan": REPO / "libro/arte/referencias/hassan-character-sheet-v2.png",
}
NO_CREDIT_MARKERS = ("no credit", "insufficient credit", "insufficient balance", "out of credits", "saldo insuficiente", "sin créditos", "sin creditos")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now() -> datetime:
    return datetime.now(timezone.utc)


def repo_path(value: str) -> Path:
    return (REPO / value).resolve()


def production_path(value: str) -> Path:
    return (PRODUCTION / value).resolve()


def is_png(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def no_credits(text: str) -> bool:
    folded = text.casefold()
    return any(marker in folded for marker in NO_CREDIT_MARKERS)


def prompt_digest(plan: dict) -> str:
    digest = hashlib.sha256()
    for page in plan["pages"]:
        digest.update(page["id"].encode())
        digest.update(b"\0")
        for key in ("prompt", "production_guide"):
            source = production_path(page[key])
            if not source.is_file():
                raise SystemExit(f"Missing {key}: {source}")
            digest.update(source.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def validated_plan(config: dict) -> dict:
    if config.get("schema_version") != 1 or config.get("status") != "ready":
        raise SystemExit("Unsupported or inactive guide run configuration.")
    generation = config["generation"]
    if generation != {"model": "gpt-image-2", "aspect_ratio": "2:3", "resolution": "2K", "approved_references_only": True}:
        raise SystemExit("Guide and final phases require approved gpt-image-2 at 2K in 2:3.")
    operation = config["operation"]
    if operation.get("previous_page_reference") != "never_attached" or operation.get("stop_on_no_credits") is not True:
        raise SystemExit("Guide run requires no previous-page attachment and a credit stop.")
    if not isinstance(operation.get("max_active"), int) or operation["max_active"] < 1:
        raise SystemExit("Guide run requires max_active >= 1.")
    plan = load(repo_path(config["source_plan"]))
    if len(plan.get("pages", [])) != 90 or len({page.get("id") for page in plan["pages"]}) != 90:
        raise SystemExit("Guide run requires exactly 90 unique pages.")
    if any(page.get("previous_page_reference", {}).get("attached") for page in plan["pages"]):
        raise SystemExit("Plan contains a forbidden previous-page attachment.")
    if any(not page.get("production_guide") or not page.get("prompt") for page in plan["pages"]):
        raise SystemExit("Every page requires both a final prompt and a production guide.")
    if config.get("prompt_lock", {}).get("sha256") != prompt_digest(plan):
        raise SystemExit("Guide prompt lock does not match the source prompts.")
    return plan


def lock_for(state_file: Path):
    lock_file = state_file.with_suffix(state_file.suffix + ".lock")
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_file.open("w", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None
    return handle


def unlock(handle) -> None:
    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    handle.close()


def due(state: dict, key: str) -> bool:
    value = state.setdefault("not_before", {}).get(key)
    return not value or now() >= datetime.fromisoformat(value)


def schedule_retry(state: dict, key: str, reason: str, retries: int, base_seconds: int) -> None:
    attempts = state.setdefault("attempts", {}).get(key, 0) + 1
    state["attempts"][key] = attempts
    if attempts > retries:
        state.setdefault("failed", {})[key] = {"reason": reason, "attempts": attempts, "at": now().isoformat()}
        return
    state.setdefault("not_before", {})[key] = (now() + timedelta(seconds=base_seconds * 2 ** (attempts - 1))).isoformat()


def status(job_id: str) -> tuple[dict | None, str]:
    result = subprocess.run([str(KIE), "job-status", job_id, "--model", "gpt-image-2-image-to-image", "--json"], text=True, capture_output=True)
    stdout = result.stdout.strip()
    try:
        item = json.loads(stdout) if stdout else None
    except json.JSONDecodeError:
        item = None
    if isinstance(item, dict) and item.get("status"):
        return item, ""
    return None, "\n".join(part for part in (stdout, result.stderr.strip()) if part) or "Kie status response did not include a status."


def archive(receipt: Path, retries: Path) -> None:
    retries.mkdir(parents=True, exist_ok=True)
    job_id = load(receipt).get("jobId", "unknown")
    receipt.replace(retries / f"{receipt.stem}--{job_id}.json")


def references(page: dict, guide: Path | None = None) -> list[Path]:
    paths = [STYLE, *(SHEETS[person] for person in page.get("references", []) if person in SHEETS)]
    if guide is not None:
        paths.append(guide)
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("Approved reference(s) missing: " + ", ".join(map(str, missing)))
    return paths


def submit(config: dict, storage: dict[str, Path], page: dict, phase: str) -> tuple[bool, str]:
    generation = config["generation"]
    source_key = "production_guide" if phase == "guide" else "prompt"
    prompt = production_path(page[source_key]).read_text(encoding="utf-8")
    prompt_dir = storage[f"{phase}_prompt_snapshot_dir"]
    job_dir = storage[f"{phase}_jobs_dir"]
    prompt_dir.mkdir(parents=True, exist_ok=True)
    job_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = prompt_dir / f"{page['id']}.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    guide = storage["guide_output_dir"] / f"{page['id']}.png" if phase == "final" else None
    if guide is not None and not is_png(guide):
        return False, "Final phase requires its completed guide PNG."
    command = [str(KIE), "image", generation["model"], "--prompt-file", str(prompt_file),
               "--aspect-ratio", generation["aspect_ratio"], "--resolution", generation["resolution"], "--json"]
    for image in references(page, guide):
        command.extend(["--image", str(image)])
    command.extend(["--save-job", str(job_dir / f"{page['id']}.json")])
    result = subprocess.run(command, text=True, capture_output=True)
    detail = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    return result.returncode == 0, detail


def poll(config: dict, storage: dict[str, Path], state: dict, page: dict, phase: str, active: list[str], downloaded: list[str], checked: list[dict]) -> bool:
    page_id = page["id"]
    receipt = storage[f"{phase}_jobs_dir"] / f"{page_id}.json"
    if not receipt.is_file():
        return False
    item, error = status(load(receipt)["jobId"])
    key = f"{phase}:{page_id}"
    if item is None:
        if no_credits(error):
            state["halted"] = {"reason": "no_credits", "at": now().isoformat(), "detail": error}
            return True
        checked.append({"phase": phase, "page": page_id, "status": "status_error", "detail": error})
        active.append(key)
        return False
    job_status = item["status"]
    checked_item = {"phase": phase, "page": page_id, "status": job_status}
    if item.get("error"):
        checked_item["error"] = item["error"]
    checked.append(checked_item)
    provider_detail = json.dumps(item.get("error", {}), ensure_ascii=False)
    if no_credits(provider_detail):
        state["halted"] = {"reason": "no_credits", "at": now().isoformat(), "detail": provider_detail}
        return True
    if job_status in {"queued", "running"}:
        active.append(key)
        return False
    if job_status == "succeeded" and item.get("outputUrl"):
        output = storage[f"{phase}_output_dir"] / f"{page_id}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(["curl", "-L", "--fail", "--output", str(output), item["outputUrl"]], text=True, capture_output=True)
        if result.returncode == 0 and is_png(output):
            downloaded.append(key)
            return False
        active.append(key)
        return False
    archive(receipt, storage[f"{phase}_jobs_dir"] / "retries")
    schedule_retry(state, key, f"Kie status={job_status!r}; detail={item.get('error')!r}", config["operation"]["max_retries"], config["operation"]["retry_base_seconds"])
    return False


def selected_pages(plan: dict, wanted: list[str]) -> list[dict]:
    if not wanted:
        return plan["pages"]
    index = {page["id"]: page for page in plan["pages"]}
    missing = [page_id for page_id in wanted if page_id not in index]
    if missing:
        raise SystemExit("Unknown page id(s): " + ", ".join(missing))
    return [index[page_id] for page_id in wanted]


def cycle(config: dict, wanted: list[str]) -> dict:
    plan = validated_plan(config)
    pages = selected_pages(plan, wanted)
    storage = {key: repo_path(value) for key, value in config["storage"].items()}
    state_file = storage["state_file"]
    state = load(state_file) if state_file.is_file() else {"attempts": {}, "not_before": {}, "failed": {}}
    if state.get("halted", {}).get("reason") == "no_credits":
        return {"action": "no_credits", "detail": state["halted"]["detail"]}
    active: list[str] = []
    downloaded: list[str] = []
    checked: list[dict] = []
    for page in pages:
        final_output = storage["final_output_dir"] / f"{page['id']}.png"
        if is_png(final_output):
            continue
        final_receipt = storage["final_jobs_dir"] / f"{page['id']}.json"
        if final_receipt.is_file():
            if poll(config, storage, state, page, "final", active, downloaded, checked):
                save(state_file, state)
                return {"action": "no_credits", "detail": state["halted"]["detail"]}
            continue
        guide_receipt = storage["guide_jobs_dir"] / f"{page['id']}.json"
        if guide_receipt.is_file():
            if poll(config, storage, state, page, "guide", active, downloaded, checked):
                save(state_file, state)
                return {"action": "no_credits", "detail": state["halted"]["detail"]}
    candidates: list[tuple[str, dict]] = []
    for phase in ("final", "guide"):
        for page in pages:
            page_id = page["id"]
            key = f"{phase}:{page_id}"
            if key in state.get("failed", {}) or not due(state, key):
                continue
            final_output = storage["final_output_dir"] / f"{page_id}.png"
            guide_output = storage["guide_output_dir"] / f"{page_id}.png"
            receipt = storage[f"{phase}_jobs_dir"] / f"{page_id}.json"
            if is_png(final_output) or receipt.is_file():
                continue
            if phase == "final" and is_png(guide_output):
                candidates.append((phase, page))
            if phase == "guide" and not is_png(guide_output):
                candidates.append((phase, page))
    while len(active) < config["operation"]["max_active"] and candidates:
        phase, page = candidates.pop(0)
        key = f"{phase}:{page['id']}"
        ok, detail = submit(config, storage, page, phase)
        if not ok:
            if no_credits(detail):
                state["halted"] = {"reason": "no_credits", "at": now().isoformat(), "detail": detail}
                save(state_file, state)
                return {"action": "no_credits", "detail": detail}
            schedule_retry(state, key, detail or "Kie submission failed", config["operation"]["max_retries"], config["operation"]["retry_base_seconds"])
            save(state_file, state)
            return {"action": "retry_scheduled", "phase": phase, "page": page["id"], "attempt": state["attempts"][key]}
        active.append(key)
        state.setdefault("not_before", {}).pop(key, None)
        if candidates and len(active) < config["operation"]["max_active"]:
            time.sleep(config["operation"]["submission_pause_seconds"])
    save(state_file, state)
    complete = all(is_png(storage["final_output_dir"] / f"{page['id']}.png") or f"guide:{page['id']}" in state.get("failed", {}) or f"final:{page['id']}" in state.get("failed", {}) for page in pages)
    finals = sum(is_png(storage["final_output_dir"] / f"{page['id']}.png") for page in pages)
    guides = sum(is_png(storage["guide_output_dir"] / f"{page['id']}.png") for page in pages)
    return {"action": "complete" if complete else "maintained", "active": active, "guide_completed": guides,
            "final_completed": finals, "checked_jobs": checked, "downloaded": downloaded,
            "failed": sorted(state.get("failed", {}))}


def dry_run(config: dict, wanted: list[str]) -> dict:
    plan = validated_plan(config)
    pages = selected_pages(plan, wanted)
    storage = {key: repo_path(value) for key, value in config["storage"].items()}
    phases = []
    for page in pages:
        guide = storage["guide_output_dir"] / f"{page['id']}.png"
        final = storage["final_output_dir"] / f"{page['id']}.png"
        phase = "complete" if is_png(final) else "final_requires_guide" if is_png(guide) else "guide"
        phases.append({"page": page["id"], "next_phase": phase,
                       "final_reference": str(guide) if phase == "final_requires_guide" else None})
    return {"action": "dry_run", "pages": len(pages), "max_active": config["operation"]["max_active"], "phases": phases[:config["operation"]["max_active"]]}


def run_once(config: dict, wanted: list[str], live: bool) -> dict:
    if not live:
        return dry_run(config, wanted)
    state_file = repo_path(config["storage"]["state_file"])
    handle = lock_for(state_file)
    if handle is None:
        return {"action": "busy", "detail": "Another guide queue cycle is already running."}
    try:
        return cycle(config, wanted)
    finally:
        unlock(handle)


def watch(config: dict, wanted: list[str], live: bool, interval_seconds: int, max_cycles: int) -> None:
    """Keep advancing guide→final dependencies and print a readable result per cycle."""
    count = 0
    while max_cycles == 0 or count < max_cycles:
        count += 1
        started = time.monotonic()
        try:
            result = run_once(config, wanted, live)
        except Exception as error:
            result = {"action": "error", "detail": f"{type(error).__name__}: {error}"}
        print(json.dumps({"event": "cycle", "cycle": count, "at": now().isoformat(), "result": result}, ensure_ascii=False,
                         indent=2, sort_keys=True), flush=True)
        if result["action"] in {"complete", "no_credits"}:
            return
        if max_cycles and count >= max_cycles:
            return
        time.sleep(max(0, interval_seconds - (time.monotonic() - started)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Maintain a guide-to-final dependent Kie queue.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--page", action="append", default=[], help="Limit a cycle to one or more exact page ids.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    parser.add_argument("--watch", action="store_true", help="Keep polling until interrupted, completion, or insufficient credits.")
    parser.add_argument("--interval-seconds", type=int, default=60, help="Seconds between watch cycles (default: 60).")
    parser.add_argument("--max-cycles", type=int, default=0, help="Stop watch after this many cycles; 0 means unlimited.")
    args = parser.parse_args()
    if args.interval_seconds <= 0:
        parser.error("--interval-seconds must be positive")
    if args.max_cycles < 0:
        parser.error("--max-cycles cannot be negative")
    config = load(args.config)
    if args.watch:
        watch(config, args.page, args.live, args.interval_seconds, args.max_cycles)
    else:
        print(json.dumps(run_once(config, args.page, args.live), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
