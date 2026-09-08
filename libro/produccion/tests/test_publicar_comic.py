from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from PIL import Image


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publicar_comic.py"
SPEC = importlib.util.spec_from_file_location("publicar_comic", SCRIPT)
assert SPEC and SPEC.loader
publisher = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = publisher
SPEC.loader.exec_module(publisher)


def make_image(path: Path, color: str = "#f75bab") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (120, 180), color).save(path)


def make_run(root: Path, run_id: str, count: int) -> Path:
    finales = root / run_id / "finales"
    for number in range(1, count + 1):
        make_image(finales / f"{number:02d}-page.png", "#bde5ff")
    return finales


class ComicPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cover = self.root / "cover.png"
        self.back_cover = self.root / "back-cover.png"
        make_image(self.cover, "#ffc653")
        make_image(self.back_cover, "#ffd7eb")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_build_site_creates_a_static_webp_edition(self) -> None:
        finales = make_run(self.root / "salidas", "v7", 2)
        output = self.root / "docs"

        publisher.build_site("v7", publisher.collect_pages(finales), self.cover, self.back_cover, output)

        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("v7", manifest["edition"])
        self.assertEqual(2, manifest["pageCount"])
        self.assertTrue((output / "index.html").is_file())
        self.assertTrue((output / ".nojekyll").is_file())
        self.assertTrue((output / manifest["cover"]["large"]).is_file())
        self.assertTrue((output / manifest["backCover"]["large"]).is_file())
        self.assertFalse(list(output.rglob("*.png")))

    def test_collect_pages_rejects_a_gap_and_an_odd_interior(self) -> None:
        finales = self.root / "gap" / "finales"
        make_image(finales / "01-page.png")
        make_image(finales / "03-page.png")
        with self.assertRaisesRegex(publisher.PublicationError, "consecutivas"):
            publisher.collect_pages(finales)

        odd_finales = make_run(self.root / "odd", "v7", 3)
        with self.assertRaisesRegex(publisher.PublicationError, "par"):
            publisher.collect_pages(odd_finales)

    def test_latest_uses_the_newest_valid_run(self) -> None:
        outputs = self.root / "salidas"
        older = make_run(outputs, "older", 2)
        time.sleep(0.01)
        newest = make_run(outputs, "newest", 2)
        os.utime(older / "01-page.png", (1, 1))

        run_id, pages = publisher.resolve_run(outputs, None, latest=True)

        self.assertEqual("newest", run_id)
        self.assertEqual([1, 2], [page.number for page in pages])

    def test_missing_back_cover_does_not_replace_existing_docs(self) -> None:
        finales = make_run(self.root / "salidas", "v7", 2)
        output = self.root / "docs"
        output.mkdir()
        (output / "keep.txt").write_text("preserve", encoding="utf-8")

        with self.assertRaisesRegex(publisher.PublicationError, "contracubierta"):
            publisher.build_site("v7", publisher.collect_pages(finales), self.cover, self.root / "missing.png", output)

        self.assertEqual("preserve", (output / "keep.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
