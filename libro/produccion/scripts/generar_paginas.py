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
    return STYLE_LOCK.format(panels=page["panels"], layout=page["layout"]) + "\nScene:\n" + page["scene"] + "\n"
def choose(plan: dict, wanted: list[str], all_pages: bool) -> list[dict]:
    if all_pages: return plan["pages"]
    index = {page["id"]: page for page in plan["pages"]}
    missing = [item for item in wanted if item not in index]
    if missing: raise SystemExit("Unknown page id(s): " + ", ".join(missing))
    return [index[item] for item in wanted]
def refs(page: dict, reference_map: dict) -> list[str]:
    paths = [path for person in page.get("references", []) for path in reference_map.get(person, [])]
    for person in page.get("references", []):
        sheet = APPROVED_CHARACTER_SHEETS.get(person)
        if sheet:
            paths.append(str(sheet))
    missing = [path for path in paths if not Path(path).is_file()]
    if missing: raise SystemExit("Reference image(s) not found:\n" + "\n".join(missing))
    return paths
def submit(page: dict, plan: dict, reference_map: dict, live: bool) -> None:
    prompts, jobs = ROOT / "prompts", ROOT / "jobs"; prompts.mkdir(parents=True, exist_ok=True); jobs.mkdir(parents=True, exist_ok=True)
    prompt_path = prompts / f"{page['id']}.txt"; prompt_path.write_text(prompt(page), encoding="utf-8")
    command = [cli(), "image", plan["model"], "--prompt-file", str(prompt_path), "--aspect-ratio", plan["aspect_ratio"], "--resolution", plan["resolution"], "--json"]
    for image in refs(page, reference_map): command.extend(["--image", image])
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
    parser.add_argument("--live", action="store_true", help="Submit real KIE jobs and upload personal references.")
    args = parser.parse_args()
    if not args.all and not args.page: parser.error("Choose --page ID or --all.")
    if args.live and not os.environ.get("KIE_API_KEY") and not Path("/Users/hassan/repos/kie-api/.env").is_file(): parser.error("KIE_API_KEY is required for --live; keep it only in KIE's local .env.")
    plan, reference_map = load(args.plan), load(args.references)
    for page in choose(plan, args.page, args.all): submit(page, plan, reference_map, args.live)
if __name__ == "__main__": main()
