#!/usr/bin/env python3
"""Assemble approved 2:3 comic pages into a full-bleed Lulu 6x9 interior PDF."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]; PT = 72; BLEED = 0.125 * PT
PAGE_W, PAGE_H = 6 * PT + 2 * BLEED, 9 * PT + 2 * BLEED  # 6.25 x 9.25 in
MIN_WIDTH = 1875
def art_path(directory: Path, page_id: str) -> Path:
    for extension in (".png", ".jpg", ".jpeg"):
        candidate = directory / f"{page_id}{extension}"
        if candidate.is_file(): return candidate
    raise FileNotFoundError(f"Missing approved art for {page_id} in {directory}")
def verify(path: Path) -> None:
    with Image.open(path) as image: width, height = image.size
    if width < MIN_WIDTH: raise ValueError(f"{path.name} is {width}px wide; need at least {MIN_WIDTH}px for 300 ppi.")
    if abs(width / height - 2 / 3) > 0.03: raise ValueError(f"{path.name} is {width}x{height}, not a 2:3 portrait page.")
def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--plan", type=Path, default=ROOT / "plan-de-imagenes.json")
    parser.add_argument("--art", type=Path, default=ROOT / "arte-aprobado")
    parser.add_argument("--output", type=Path, default=ROOT / "salida" / "powerpuff-ferry-interior-6x9.pdf")
    args = parser.parse_args(); plan = json.loads(args.plan.read_text(encoding="utf-8"))
    pages = [(entry["id"], art_path(args.art, entry["id"])) for entry in plan["pages"]]
    expected_count = plan.get("print_page_count", len(pages))
    if len(pages) != expected_count: raise ValueError(f"Plan has {len(pages)} pages but print_page_count is {expected_count}.")
    for _, image in pages: verify(image)
    args.output.parent.mkdir(parents=True, exist_ok=True); pdf = canvas.Canvas(str(args.output), pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    # A 2:3 source fills the slightly wider 6.25x9.25 in bleed page with only 0.0625 in cropped from top and bottom.
    page_art_h, y = PAGE_W * 3 / 2, (PAGE_H - PAGE_W * 3 / 2) / 2
    for _, image in pages:
        pdf.drawImage(ImageReader(str(image)), 0, y, width=PAGE_W, height=page_art_h, mask="auto"); pdf.showPage()
    pdf.save(); print(f"Created {args.output} with {len(pages)} single-page 6.25x9.25 in PDF pages.")
if __name__ == "__main__": main()
