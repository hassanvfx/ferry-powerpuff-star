#!/usr/bin/env python3
"""Submit reproducible 6x9 portrait comic pages through the local KIE CLI.

Default mode is dry-run so no credit is spent and no personal photo is uploaded.
Pass --live only after reviewing the printed prompts.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KIE = Path("/Users/hassan/repos/kie-api/.venv/bin/kie-cli")
APPROVED_CHARACTER_SHEETS = {
    "ferry": ROOT.parent / "arte" / "referencias" / "ferry-character-sheet-v2.png",
    "hassan": ROOT.parent / "arte" / "referencias" / "hassan-character-sheet-v2.png",
}
APPROVED_STYLE_REFERENCE = ROOT.parent / "arte" / "referencias" / "chibi-superhero-comic-style-reference.png"
STYLE_LOCK = """Create one original vertical 6x9 comic-book page in a 2:3 aspect ratio, not a collage and not a poster.
Use exactly {panels} distinct panels separated by clean graphic gutters; layout: {layout}.
Original retro chibi-superhero cartoon: adult characters with round compact proportions, oversized expressive eyes,
small simple noses and mouths, bold clean black outlines, flat cel colors, simple 2D shapes, limited soft highlights,
and energetic diagonal motion. This is an original visual language, not a copy of any existing cartoon, character, logo, costume, or franchise.
Warm pink/coral/gold/red dream palette contrasts cool blue-white laboratory reality. No photorealism and no 3D rendering.
Render every Spanish caption and dialogue supplied in the scene exactly, with clear lettering inside comic captions or speech bubbles.
Do not invent extra text, numbers, logos, watermarks, copyrighted characters, or branded costumes.
Render magical ingredients as inanimate objects: never give them eyes, faces, mouths, limbs, or mascot personalities unless the scene explicitly names a living animal or protagonist.
Keep faces, hands, and every narrative focal point at least 10% inside every edge. Preserve character likenesses only from the supplied private references.
When a character-design sheet is supplied, treat it as the approved source of continuity for that character's silhouette, facial language, wardrobe, accessories, and color palette.
"""

def load(path: Path) -> dict: return json.loads(path.read_text(encoding="utf-8"))
def cli() -> str:
    if os.environ.get("KIE_CLI"): return os.environ["KIE_CLI"]
    if DEFAULT_KIE.is_file(): return str(DEFAULT_KIE)
    if shutil.which("kie-cli"): return str(shutil.which("kie-cli"))
    raise SystemExit("No encontre kie-cli. Define KIE_CLI o instala el CLI de KIE.")
def prompt(page: dict) -> str:
    if "prompt" in page:
        prompt_path = ROOT / page["prompt"]
        if not prompt_path.is_file():
            raise SystemExit(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")
    return STYLE_LOCK.format(panels=page["panels"], layout=page["layout"]) + "\nScene:\n" + page["scene"] + "\n"
def choose(plan: dict, wanted: list[str], all_pages: bool) -> list[dict]:
    if all_pages: return plan["pages"]
    index = {page["id"]: page for page in plan["pages"]}
    missing = [item for item in wanted if item not in index]
    if missing: raise SystemExit("Unknown page id(s): " + ", ".join(missing))
    return [index[item] for item in wanted]
def approved_previous_page(page: dict, require_approved: bool, preview_dir: Path | None) -> list[str]:
    continuity = page.get("previous_page_reference", {})
    if not continuity.get("attached"):
        return []
    relative = continuity.get("approved_art")
    if not relative:
        raise SystemExit(f"{page['id']}: previous-page continuity is enabled but has no approved_art path.")
    path = ROOT / relative
    preview_path = preview_dir / path.name if preview_dir else None
    if preview_path and preview_path.is_file():
        return [str(preview_path)]
    if require_approved and not path.is_file():
        previous_id = continuity.get("approved_page_id", "the immediately previous page")
        raise SystemExit(
            f"{page['id']}: requires approved predecessor {previous_id} at {path}. "
            "Review and place the predecessor in arte-aprobado/, or pass --continuity-preview-dir for a non-final sequential test."
        )
    return [str(path)] if path.is_file() else []

def refs(page: dict, reference_map: dict, include_private: bool, require_approved_previous: bool, preview_dir: Path | None) -> list[str]:
    paths = [str(APPROVED_STYLE_REFERENCE)]
    if include_private:
        paths.extend(path for person in page.get("references", []) for path in reference_map.get(person, []))
    for person in page.get("references", []):
        sheet = APPROVED_CHARACTER_SHEETS.get(person)
        if sheet:
            paths.append(str(sheet))
    paths.extend(approved_previous_page(page, require_approved_previous, preview_dir))
    missing = [path for path in paths if not Path(path).is_file()]
    if missing: raise SystemExit("Reference image(s) not found:\n" + "\n".join(missing))
    return paths
def submit(page: dict, plan: dict, reference_map: dict, live: bool, include_private: bool, preview_dir: Path | None, model: str, aspect_ratio: str, resolution: str, prompts: Path, jobs: Path) -> None:
    prompts.mkdir(parents=True, exist_ok=True); jobs.mkdir(parents=True, exist_ok=True)
    prompt_path = prompts / f"{page['id']}.txt"; prompt_path.write_text(prompt(page), encoding="utf-8")
    command = [cli(), "image", model, "--prompt-file", str(prompt_path), "--aspect-ratio", aspect_ratio, "--resolution", resolution, "--json"]
    for image in refs(page, reference_map, include_private, live, preview_dir): command.extend(["--image", image])
    command.extend(["--save-job", str(jobs / f"{page['id']}.json")] if live else ["--dry-run"])
    print("\n" + page["id"] + ": " + " ".join(command))
    result = subprocess.run(command, text=True, capture_output=True)
    if result.stdout: print(result.stdout.strip())
    if result.returncode:
        print(result.stderr.strip(), file=sys.stderr); raise SystemExit(result.returncode)
def main() -> None:
    parser = argparse.ArgumentParser(description="Generate or dry-run individual comic pages through KIE.")
    parser.add_argument("--plan", type=Path, default=ROOT / "plan-de-imagenes.json")
    parser.add_argument("--references", type=Path, default=ROOT / "referencias.local.json")
    parser.add_argument("--page", action="append", default=[]); parser.add_argument("--all", action="store_true")
    parser.add_argument("--approved-references-only", action="store_true", help="Use only the approved style and character sheets; never load private facial references.")
    parser.add_argument("--continuity-preview-dir", type=Path, help="Use prior generated previews from this directory for a sequential test; it never marks them as approved art.")
    parser.add_argument("--model", help="Override the model declared by the plan for a named production run.")
    parser.add_argument("--aspect-ratio", help="Override the plan aspect ratio for a named production run.")
    parser.add_argument("--resolution", help="Override the plan resolution for a named production run.")
    parser.add_argument("--jobs-dir", type=Path, help="Store job receipts in this run-specific directory.")
    parser.add_argument("--prompt-output-dir", type=Path, help="Store materialized prompt snapshots in this run-specific directory.")
    parser.add_argument("--live", action="store_true", help="Submit real KIE jobs and upload personal references.")
    args = parser.parse_args()
    if not args.all and not args.page: parser.error("Choose --page ID or --all.")
    if args.live and not os.environ.get("KIE_API_KEY") and not Path("/Users/hassan/repos/kie-api/.env").is_file(): parser.error("KIE_API_KEY is required for --live; keep it only in KIE's local .env.")
    plan = load(args.plan)
    reference_map = {} if args.approved_references_only else load(args.references)
    model = args.model or plan["model"]
    aspect_ratio = args.aspect_ratio or plan["aspect_ratio"]
    resolution = args.resolution or plan["resolution"]
    prompts = args.prompt_output_dir or ROOT / "prompts"
    jobs = args.jobs_dir or ROOT / "jobs"
    for page in choose(plan, args.page, args.all): submit(page, plan, reference_map, args.live, not args.approved_references_only, args.continuity_preview_dir, model, aspect_ratio, resolution, prompts, jobs)
if __name__ == "__main__": main()
