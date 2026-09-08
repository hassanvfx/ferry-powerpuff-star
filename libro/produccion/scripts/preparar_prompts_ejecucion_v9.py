#!/usr/bin/env python3
"""Prepare reviewed, bounded V9 execution prompts without changing sources.

The command copies each fully materialized guide/final prompt into a V9 output
folder.  When a guide is longer than Kie's 20,000-character limit, it creates
a conservative execution rewrite that removes only repeated review notes while
preserving the source, cell actions, camera, identity and continuity controls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import mantener_cola_paralela_v9_referencias as v9


MAX_CHARACTERS = 20_000


def compact_guide(text: str) -> str:
    """Remove duplicate per-cell review prose from an over-limit guide prompt."""
    marker = "# Prompt de storyboard"
    if marker not in text:
        raise SystemExit("Guide source does not contain its storyboard heading.")
    prefix, body = text.split(marker, 1)
    body = marker + body
    body = body.split("\n## Chequeo de aprobación", 1)[0]
    omitted_prefixes = (
        "- Notas de continuidad por dimensión",
        "- Marcador visual de lettering",
        "- Estado que debe respetarse:",
        "- Anotaciones gráficas obligatorias:",
    )
    compact_body = "\n".join(
        line for line in body.splitlines()
        if not line.startswith(omitted_prefixes)
    ).rstrip() + "\n"
    notice = (
        "EJECUCIÓN COMPACTA — LÍMITE KIE: máximo 20,000 caracteres. "
        "Esta versión elimina notas de revisión repetidas; conserva la fuente, "
        "retícula, acciones, identidad, continuidad y controles de seguridad.\n\n"
    )
    return prefix + notice + compact_body


def load_manifest(path: Path) -> dict:
    if not path.is_file():
        return {"schema_version": 1, "limit_characters": MAX_CHARACTERS, "prompts": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def prepare(config: dict, wanted: list[str], replace: bool, rewrite: bool, dry_run: bool) -> dict:
    plan = v9.validated_plan(config)
    pages = v9.queue.selected_pages(plan, wanted)
    storage = {key: v9.queue.repo_path(value) for key, value in config["storage"].items()}
    root = storage["prepared_prompt_dir"]
    manifest_path = root / "revision.json"
    manifest = load_manifest(manifest_path)
    manifest["source_prompt_digest"] = v9.queue.prompt_digest(plan)
    prepared: list[dict] = []
    for page in pages:
        assets = v9.declared_assets(page, include_candidates=True)
        for phase in ("guide", "final"):
            guide = storage["guide_output_dir"] / f"{page['id']}.png" if phase == "final" else None
            original = v9.materialized_prompt(page, phase, assets, guide)
            ready = original
            rewritten = False
            if len(ready) > MAX_CHARACTERS:
                if phase != "guide" or not rewrite:
                    raise SystemExit(f"{phase}:{page['id']} has {len(ready)} characters; needs a reviewed rewrite before Kie.")
                ready = compact_guide(original)
                rewritten = True
            if len(ready) > MAX_CHARACTERS:
                raise SystemExit(f"Compacted {phase}:{page['id']} still exceeds {MAX_CHARACTERS} characters ({len(ready)}).")
            original_path = root / "originales" / ("guias" if phase == "guide" else "finales") / f"{page['id']}.txt"
            ready_path = root / ("guias" if phase == "guide" else "finales") / f"{page['id']}.txt"
            if ready_path.exists() and not replace and ready_path.read_text(encoding="utf-8") != ready:
                raise SystemExit(f"Prepared prompt exists and differs: {ready_path}. Re-run with --replace to regenerate it.")
            key = f"{phase}:{page['id']}"
            prepared.append({"phase": phase, "page": page["id"], "original_characters": len(original),
                             "final_characters": len(ready), "rewritten": rewritten, "path": str(ready_path)})
            if not dry_run:
                original_path.parent.mkdir(parents=True, exist_ok=True)
                ready_path.parent.mkdir(parents=True, exist_ok=True)
                original_path.write_text(original, encoding="utf-8")
                ready_path.write_text(ready, encoding="utf-8")
                manifest["prompts"][key] = {
                    "source": page["production_guide"] if phase == "guide" else page["prompt"],
                    "original_path": str(original_path), "prepared_path": str(ready_path),
                    "original_characters": len(original), "final_characters": len(ready),
                    "rewritten_for_limit": rewritten, "limit_characters": MAX_CHARACTERS,
                    "attached_reference_ids": [asset["id"] for asset in assets] + ([f"guia-{page['id']}"] if phase == "final" else []),
                }
    if not dry_run:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"action": "prepare_preview" if dry_run else "prepared", "pages": len(pages),
            "limit_characters": MAX_CHARACTERS, "rewritten": [item for item in prepared if item["rewritten"]],
            "prepared": prepared}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create reviewed, bounded V9 execution prompts.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--page", action="append", default=[], help="Prepare only exact page ids; omit for all 90.")
    parser.add_argument("--replace", action="store_true", help="Replace a prepared version when regenerating it.")
    parser.add_argument("--no-rewrite-over-limit", action="store_true", help="Report over-limit prompts instead of compacting their guide version.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = v9.queue.load(args.config)
    result = prepare(config, args.page, args.replace, not args.no_rewrite_over_limit, args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
