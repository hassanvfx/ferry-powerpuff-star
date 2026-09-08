#!/usr/bin/env python3
"""Run V9 guide→final jobs with per-page declared visual references.

V9 is deliberately separate from previous runs.  Its source of truth is the
``REFERENCIAS DECLARADAS PARA ESTA PÁGINA`` block in each final prompt.  It
records a ``REFERENCIAS VISUALES ADJUNTAS`` block in every snapshot so the
prompt and the image payload can be audited together.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import mantener_cola_paralela_guia as queue


PRODUCTION = queue.PRODUCTION
REPO = queue.REPO
DECLARATION_HEADING = "REFERENCIAS DECLARADAS PARA ESTA PÁGINA"
DECLARATION_PREFIX = "- ["
_INCLUDE_CANDIDATES = True


def declared_assets(page: dict, include_candidates: bool) -> list[dict]:
    """Read the execution declarations in the final-prompt source verbatim."""
    source = queue.production_path(page["prompt"])
    text = source.read_text(encoding="utf-8")
    if DECLARATION_HEADING not in text:
        raise SystemExit(f"Missing declared visual references in {source}")
    block = text.split(DECLARATION_HEADING, 1)[1].splitlines()
    parsed: list[dict] = []
    started = False
    seen_paths: set[Path] = set()
    for line in block:
        if line.startswith(DECLARATION_PREFIX):
            started = True
            try:
                label, description = line[2:].split("): ", 1)
                header, source_path = label.rsplit(" (", 1)
                status_and_type, identifier = header.split("] ", 1)
                status, asset_type = status_and_type.removeprefix("[").split("; ", 1)
            except ValueError as error:
                raise SystemExit(f"Invalid declared visual reference in {source}: {line}") from error
            if status not in {"approved", "candidate"} or not identifier or not asset_type:
                raise SystemExit(f"Invalid declared visual reference in {source}: {line}")
            asset = (PRODUCTION / source_path).resolve()
            try:
                asset.relative_to(REPO)
            except ValueError as error:
                raise SystemExit(f"Declared reference leaves repository in {source}: {source_path}") from error
            if not asset.is_file() or asset.stat().st_size == 0:
                raise SystemExit(f"Declared reference is missing or empty in {source}: {asset}")
            if asset in seen_paths:
                raise SystemExit(f"Duplicate declared reference in {source}: {asset}")
            seen_paths.add(asset)
            parsed.append({
                "status": status,
                "type": asset_type,
                "id": identifier,
                "declared_path": source_path,
                "path": asset,
                "description": description,
            })
            continue
        if started:
            break
    if not parsed:
        raise SystemExit(f"No declared visual references found in {source}")
    return [asset for asset in parsed if asset["status"] == "approved" or include_candidates]


def attached_block(assets: list[dict], guide: Path | None = None) -> str:
    """Describe exactly the image files that will follow as Kie attachments."""
    lines = [
        "REFERENCIAS VISUALES ADJUNTAS — USO OBLIGATORIO:",
        "Estas y sólo estas imágenes se adjuntan en este payload. Úsalas para identidad o lugar; no copies su composición, poses ni paneles.",
    ]
    for asset in assets:
        lines.append(
            f"- [{asset['status']}; {asset['type']}] {asset['id']} "
            f"({asset['declared_path']}): {asset['description']}"
        )
    if guide is not None:
        lines.append(
            f"- [generated; guide] guia-{guide.stem} ({guide}): "
            "Previsualización de esta misma página; conserva su continuidad, no copies sus anotaciones técnicas."
        )
    return "\n".join(lines) + "\n\n"


def materialized_prompt(page: dict, phase: str, assets: list[dict], guide: Path | None = None) -> str:
    source_key = "production_guide" if phase == "guide" else "prompt"
    source = queue.production_path(page[source_key])
    return attached_block(assets, guide) + source.read_text(encoding="utf-8")


def prepared_prompt(storage: dict[str, Path], page: dict, phase: str, assets: list[dict], guide: Path | None = None) -> str:
    """Prefer a reviewed execution copy; use the immutable source only before preparation."""
    prepared_dir = storage.get("prepared_prompt_dir")
    if prepared_dir is not None:
        candidate = prepared_dir / "finales" / f"{page['id']}.txt" if phase == "final" else prepared_dir / "guias" / f"{page['id']}.txt"
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8")
            if len(text) > 20_000:
                raise SystemExit(f"Prepared prompt exceeds Kie's 20,000-character limit: {candidate}")
            return text
    return materialized_prompt(page, phase, assets, guide)


def submit(config: dict, storage: dict[str, Path], page: dict, phase: str) -> tuple[bool, str]:
    """Create a phase snapshot and submit exactly its declared image payload."""
    generation = config["generation"]
    assets = declared_assets(page, _INCLUDE_CANDIDATES)
    guide = storage["guide_output_dir"] / f"{page['id']}.png" if phase == "final" else None
    if guide is not None and not queue.is_png(guide):
        return False, "Final phase requires its completed guide PNG."
    prompt_dir = storage[f"{phase}_prompt_snapshot_dir"]
    job_dir = storage[f"{phase}_jobs_dir"]
    prompt_dir.mkdir(parents=True, exist_ok=True)
    job_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = prompt_dir / f"{page['id']}.txt"
    prompt_file.write_text(prepared_prompt(storage, page, phase, assets, guide), encoding="utf-8")
    command = [
        str(queue.KIE), "image", generation["model"], "--prompt-file", str(prompt_file),
        "--aspect-ratio", generation["aspect_ratio"], "--resolution", generation["resolution"], "--json",
    ]
    for asset in assets:
        command.extend(["--image", str(asset["path"])])
    if guide is not None:
        command.extend(["--image", str(guide)])
    command.extend(["--save-job", str(job_dir / f"{page['id']}.json")])
    result = subprocess.run(command, text=True, capture_output=True)
    detail = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    return result.returncode == 0, detail


def validated_plan(config: dict) -> dict:
    plan = _BASE_VALIDATED_PLAN(config)
    contract = config.get("reference_contract")
    if contract != {
        "source": "per-page declared prompt references",
        "candidate_assets": "enabled by default",
        "snapshot_heading": "REFERENCIAS VISUALES ADJUNTAS",
    }:
        raise SystemExit("V9 requires its declared-reference contract in the configuration.")
    if not config.get("storage", {}).get("prepared_prompt_dir"):
        raise SystemExit("V9 requires a prepared_prompt_dir for reviewed execution prompts.")
    for page in plan["pages"]:
        declared_assets(page, include_candidates=True)
    return plan


def dry_run(config: dict, wanted: list[str]) -> dict:
    plan = validated_plan(config)
    pages = queue.selected_pages(plan, wanted)
    storage = {key: queue.repo_path(value) for key, value in config["storage"].items()}
    phases = []
    for page in pages:
        guide = storage["guide_output_dir"] / f"{page['id']}.png"
        final = storage["final_output_dir"] / f"{page['id']}.png"
        phase = "complete" if queue.is_png(final) else "final_requires_guide" if queue.is_png(guide) else "guide"
        assets = declared_assets(page, _INCLUDE_CANDIDATES)
        phases.append({
            "page": page["id"],
            "next_phase": phase,
            "attached_references": [asset["id"] for asset in assets] + ([f"guia-{page['id']}"] if phase == "final_requires_guide" else []),
            "final_reference": str(guide) if phase == "final_requires_guide" else None,
        })
    return {
        "action": "dry_run",
        "pages": len(pages),
        "max_active": config["operation"]["max_active"],
        "candidate_continuity_assets": _INCLUDE_CANDIDATES,
        "phases": phases[:config["operation"]["max_active"]],
    }


def failed_keys(config: dict, wanted: list[str]) -> list[str]:
    """Return failed phase keys limited to the requested page ids."""
    plan = validated_plan(config)
    pages = queue.selected_pages(plan, wanted)
    state_file = queue.repo_path(config["storage"]["state_file"])
    state = queue.load(state_file) if state_file.is_file() else {"failed": {}}
    allowed = {page["id"] for page in pages}
    return sorted(
        key for key in state.get("failed", {})
        if key.partition(":")[2] in allowed
    )


def rearm_failed(config: dict, wanted: list[str]) -> list[str]:
    """Clear only terminal failure bookkeeping; completed PNGs stay untouched."""
    state_file = queue.repo_path(config["storage"]["state_file"])
    handle = queue.lock_for(state_file)
    if handle is None:
        raise SystemExit("Another V9 queue cycle is running; retry after it stops.")
    try:
        keys = failed_keys(config, wanted)
        state = queue.load(state_file) if state_file.is_file() else {"attempts": {}, "not_before": {}, "failed": {}}
        for key in keys:
            state.setdefault("failed", {}).pop(key, None)
            state.setdefault("attempts", {}).pop(key, None)
            state.setdefault("not_before", {}).pop(key, None)
        queue.save(state_file, state)
        return keys
    finally:
        queue.unlock(handle)


_BASE_VALIDATED_PLAN = queue.validated_plan
queue.validated_plan = validated_plan
queue.submit = submit
queue.dry_run = dry_run


def main() -> None:
    global _INCLUDE_CANDIDATES
    parser = argparse.ArgumentParser(description="Maintain V9 declared-reference guide-to-final Kie queue.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--page", action="append", default=[], help="Limit a cycle to one or more exact page ids.")
    parser.add_argument("--include-candidate-continuity-assets", action="store_true",
                        help="Compatibility flag; candidate assets are enabled by default in V9.")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Rearm terminal failures for the selected pages before this run; omit --page to rearm all.")
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
    _INCLUDE_CANDIDATES = True
    config = queue.load(args.config)
    if args.retry_failed:
        if args.dry_run:
            print(json.dumps({"action": "retry_preview", "rearm": failed_keys(config, args.page)}, ensure_ascii=False, indent=2, sort_keys=True))
            return
        rearmed = rearm_failed(config, args.page)
        print(json.dumps({"event": "retry_rearmed", "phases": rearmed}, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
    if args.watch:
        queue.watch(config, args.page, args.live, args.interval_seconds, args.max_cycles)
    else:
        print(json.dumps(queue.run_once(config, args.page, args.live), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
