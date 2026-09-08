#!/usr/bin/env python3
"""Create a frozen V3 plan without previous-page language or attachments."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PRODUCTION = Path(__file__).resolve().parents[1]
REPO = PRODUCTION.parents[1]
BANNED = ("página anterior", "pagina anterior", "referencia anterior", "previous page")


def clean_prompt(source: str) -> str:
    lines: list[str] = []
    for line in source.splitlines():
        folded = line.casefold()
        if "continuidad con la página anterior" in folded or "punto de arranque de continuidad" in folded:
            continue
        line = re.sub(
            r"BLOQUEO DE CRONOLOGÍA:\s*La referencia anterior conserva apariencia, no autoriza objetos nuevos\.\s*",
            "BLOQUEO DE CRONOLOGÍA: ",
            line,
            flags=re.IGNORECASE,
        )
        if any(term in line.casefold() for term in BANNED):
            raise ValueError(f"Residual previous-page language: {line}")
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-plan", type=Path, default=PRODUCTION / "plan-de-imagenes-90.json")
    parser.add_argument("--run-id", default="corrida-90-2k-2-3-v3")
    args = parser.parse_args()
    prompt_dir = PRODUCTION / "prompts-corridas" / args.run_id
    plan_path = PRODUCTION / "corridas" / f"{args.run_id}.plan.json"
    source = json.loads(args.source_plan.read_text(encoding="utf-8"))
    pages = []
    for page in source["pages"]:
        original = PRODUCTION / page["prompt"]
        cleaned = clean_prompt(original.read_text(encoding="utf-8"))
        target = prompt_dir / original.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(cleaned, encoding="utf-8")
        derived = dict(page)
        derived["prompt"] = str(target.relative_to(PRODUCTION))
        derived["previous_page_reference"] = {"attached": False}
        pages.append(derived)
    plan = dict(source)
    plan["pages"] = pages
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"plan": str(plan_path), "prompts": str(prompt_dir), "pages": len(pages), "banned_terms": list(BANNED)}))


if __name__ == "__main__":
    main()
