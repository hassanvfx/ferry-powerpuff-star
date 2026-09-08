#!/usr/bin/env python3
"""Empaqueta una corrida de páginas finales como sitio estático en docs/."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError


PAGE_NAME = re.compile(r"^(?P<number>\d+)-.+\.png$", re.IGNORECASE)
DEFAULT_TITLE = "Ferry PowerPuff Star"
ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "docs"
DEFAULT_COVER = ROOT / "libro/arte/referencias/ferry-powerpuff-star-cover.png"
DEFAULT_BACK_COVER = ROOT / "libro/arte/referencias/ferry-powerpuff-star-back-cover.png"
PLAYER_SOURCE = ROOT / "libro/produccion/player"
OUTPUT_FILES = ("index.html", "styles.css", "app.js")


class PublicationError(ValueError):
    """Raised when a requested edition cannot safely be published."""


@dataclass(frozen=True)
class Page:
    number: int
    source: Path


def image_dimensions(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return image.size
    except (OSError, UnidentifiedImageError) as error:
        raise PublicationError(f"Imagen inválida: {path}") from error


def collect_pages(finales_dir: Path) -> list[Page]:
    if not finales_dir.is_dir():
        raise PublicationError(f"No existe el directorio de finales: {finales_dir}")
    pages: list[Page] = []
    seen: set[int] = set()
    ignored = [
        path.name
        for path in finales_dir.iterdir()
        if path.is_file() and not path.name.startswith(".") and path.suffix.lower() != ".png"
    ]
    if ignored:
        raise PublicationError(f"Finales contiene archivos no PNG: {', '.join(sorted(ignored))}")
    for path in sorted(finales_dir.glob("*.png")):
        match = PAGE_NAME.match(path.name)
        if not match:
            raise PublicationError(f"Nombre de página inválido: {path.name}")
        number = int(match.group("number"))
        if number in seen:
            raise PublicationError(f"Número de página duplicado: {number:02d}")
        image_dimensions(path)
        seen.add(number)
        pages.append(Page(number=number, source=path))
    pages.sort(key=lambda page: page.number)
    if not pages:
        raise PublicationError(f"No hay PNG finales en {finales_dir}")
    expected = list(range(1, len(pages) + 1))
    actual = [page.number for page in pages]
    if actual != expected:
        raise PublicationError(f"Las páginas deben ser consecutivas desde 01; se encontró {actual}")
    if len(pages) % 2:
        raise PublicationError("El interior debe tener un número par de páginas para formar dobles páginas.")
    return pages


def valid_run_candidates(outputs_root: Path) -> Iterable[tuple[float, str, Path]]:
    if not outputs_root.is_dir():
        raise PublicationError(f"No existe la raíz de salidas: {outputs_root}")
    for run_dir in outputs_root.iterdir():
        finales = run_dir / "finales"
        if not finales.is_dir():
            continue
        pngs = list(finales.glob("*.png"))
        if not pngs:
            continue
        try:
            collect_pages(finales)
        except PublicationError:
            continue
        yield (max(path.stat().st_mtime for path in pngs), run_dir.name, run_dir)


def resolve_run(outputs_root: Path, run_id: str | None, latest: bool) -> tuple[str, list[Page]]:
    if run_id:
        final_dir = outputs_root / run_id / "finales"
        return run_id, collect_pages(final_dir)
    candidates = sorted(valid_run_candidates(outputs_root), reverse=True)
    if not latest or not candidates:
        raise PublicationError("No se encontró una corrida válida para publicar.")
    _, run_name, run_dir = candidates[0]
    return run_name, collect_pages(run_dir / "finales")


def require_file(path: Path, label: str) -> tuple[int, int]:
    if not path.is_file():
        raise PublicationError(f"Falta {label}: {path}")
    return image_dimensions(path)


def save_webp(source: Path, destination: Path, max_width: int) -> tuple[int, int]:
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        if image.width > max_width:
            height = round(image.height * max_width / image.width)
            image = image.resize((max_width, height), Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, "WEBP", quality=85, method=6)
        return image.size


def asset_record(source: Path, directory: Path, stem: str) -> dict[str, object]:
    small_path = directory / f"{stem}-small.webp"
    large_path = directory / f"{stem}-large.webp"
    small_width, _ = save_webp(source, small_path, 780)
    large_width, _ = save_webp(source, large_path, 1440)
    return {
        "small": small_path.relative_to(directory.parents[1]).as_posix(),
        "smallWidth": small_width,
        "large": large_path.relative_to(directory.parents[1]).as_posix(),
        "largeWidth": large_width,
    }


def copy_player(destination: Path) -> None:
    for filename in OUTPUT_FILES:
        source = PLAYER_SOURCE / filename
        if not source.is_file():
            raise PublicationError(f"Falta el archivo fuente del player: {source}")
        shutil.copy2(source, destination / filename)


def build_site(
    run_id: str,
    pages: list[Page],
    cover: Path,
    back_cover: Path,
    output: Path,
    title: str = DEFAULT_TITLE,
) -> None:
    require_file(cover, "la portada")
    require_file(back_cover, "la contracubierta")
    output_parent = output.parent
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-staging-", dir=output_parent))
    try:
        copy_player(staging)
        assets = staging / "assets"
        cover_record = asset_record(cover, assets / "covers", "cover")
        back_cover_record = asset_record(back_cover, assets / "covers", "back-cover")
        page_records = []
        for page in pages:
            record = asset_record(page.source, assets / "pages", f"{page.number:02d}")
            page_records.append({"number": page.number, **record})
        manifest = {
            "title": title,
            "edition": run_id,
            "pageCount": len(pages),
            "generatedAt": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "cover": cover_record,
            "backCover": back_cover_record,
            "pages": page_records,
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (staging / ".nojekyll").touch()
        backup = output_parent / f".{output.name}-previous-{uuid4().hex}"
        if output.exists():
            os.replace(output, backup)
        try:
            os.replace(staging, output)
        except BaseException:
            if backup.exists():
                os.replace(backup, output)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--run", help="Id de corrida bajo libro/arte/salidas/.")
    selection.add_argument("--latest", action="store_true", help="Publica la corrida válida con finales más recientes.")
    parser.add_argument("--cover", type=Path, default=DEFAULT_COVER, help="PNG/JPG de portada.")
    parser.add_argument("--back-cover", type=Path, default=DEFAULT_BACK_COVER, help="PNG/JPG de contracubierta.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Directorio estático publicado.")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Título mostrado por el player.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_id, pages = resolve_run(ROOT / "libro/arte/salidas", args.run, args.latest)
        build_site(run_id, pages, args.cover.resolve(), args.back_cover.resolve(), args.output.resolve(), args.title)
    except PublicationError as error:
        print(f"Publicación detenida: {error}", file=sys.stderr)
        return 2
    print(f"Edición {run_id} publicada en {args.output} ({len(pages)} páginas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
