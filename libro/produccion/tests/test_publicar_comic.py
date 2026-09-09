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
    guias = root / run_id / "guias"
    for number in range(1, count + 1):
        make_image(finales / f"{number:02d}-page.png", "#bde5ff")
        make_image(guias / f"{number:02d}-page.png", "#ffd7eb")
    return finales


class ComicPublisherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cover = self.root / "cover.png"
        self.back_cover = self.root / "back-cover.png"
        self.avatar = self.root / "avatar.png"
        self.home_avatar = self.root / "home-avatar.png"
        make_image(self.cover, "#ffc653")
        make_image(self.back_cover, "#ffd7eb")
        make_image(self.avatar, "#15122b")
        make_image(self.home_avatar, "#f75bab")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_build_site_creates_a_static_webp_edition(self) -> None:
        finales = make_run(self.root / "salidas", "v7", 2)
        output = self.root / "docs"

        publisher.build_site(
            "v7", publisher.collect_pages(finales), self.cover, self.back_cover, self.avatar, self.home_avatar, output
        )

        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("v7", manifest["edition"])
        self.assertEqual(2, manifest["pageCount"])
        self.assertTrue((output / "index.html").is_file())
        self.assertTrue((output / ".nojekyll").is_file())
        self.assertTrue((output / manifest["cover"]["large"]).is_file())
        self.assertTrue((output / manifest["backCover"]["large"]).is_file())
        self.assertTrue((output / manifest["guideAvatar"]["src"]).is_file())
        self.assertEqual(160, manifest["guideAvatar"]["width"])
        self.assertTrue((output / manifest["homeAvatar"]["src"]).is_file())
        self.assertEqual(160, manifest["homeAvatar"]["width"])
        self.assertTrue((output / manifest["pages"][0]["guide"]["small"]).is_file())
        self.assertEqual(180, manifest["pages"][0]["largeHeight"])
        self.assertTrue((output / "vendor/photoswipe/photoswipe.css").is_file())
        self.assertTrue((output / "vendor/photoswipe/photoswipe-lightbox.esm.js").is_file())
        self.assertFalse(list(output.rglob("*.png")))

    def test_collect_pages_rejects_a_gap_and_an_odd_interior(self) -> None:
        finales = self.root / "gap" / "finales"
        make_image(finales / "01-page.png")
        make_image(finales / "03-page.png")
        make_image(finales.parent / "guias" / "01-page.png")
        make_image(finales.parent / "guias" / "03-page.png")
        with self.assertRaisesRegex(publisher.PublicationError, "consecutivas"):
            publisher.collect_pages(finales)

        odd_finales = make_run(self.root / "odd", "v7", 3)
        with self.assertRaisesRegex(publisher.PublicationError, "par"):
            publisher.collect_pages(odd_finales)

    def test_collect_pages_allows_explicit_sparse_even_edition(self) -> None:
        finales = self.root / "sparse" / "finales"
        for number in (1, 3):
            make_image(finales / f"{number:02d}-page.png")
            make_image(finales.parent / "guias" / f"{number:02d}-page.png")

        pages = publisher.collect_pages(finales, allow_gaps=True)

        self.assertEqual([1, 3], [page.number for page in pages])

    def test_latest_uses_the_newest_valid_run(self) -> None:
        outputs = self.root / "salidas"
        older = make_run(outputs, "older", 2)
        time.sleep(0.01)
        newest = make_run(outputs, "newest", 2)
        os.utime(older / "01-page.png", (1, 1))

        run_id, pages = publisher.resolve_run(outputs, None, latest=True)

        self.assertEqual("newest", run_id)
        self.assertEqual([1, 2], [page.number for page in pages])

    def test_run_prefers_patched_then_4k_then_2k_then_guide_per_page(self) -> None:
        run = self.root / "salidas" / "v11"
        for number in (1, 2, 3, 4):
            make_image(run / "finales-2k" / f"{number:02d}-page.png", "#bde5ff")
        for number in (1, 2, 3, 4, 5, 6):
            make_image(run / "guias" / f"{number:02d}-page.png", "#ffd7eb")
        for number in (2, 3):
            make_image(run / "finales-4k" / f"{number:02d}-page.png", "#ffc653")
        make_image(run / "final-patched" / "03-page.png", "#f75bab")

        pages = publisher.collect_run_pages(run)

        self.assertEqual([1, 2, 3, 4, 5, 6], [page.number for page in pages])
        self.assertEqual("finales-2k", pages[0].source.parent.name)
        self.assertEqual("finales-4k", pages[1].source.parent.name)
        self.assertEqual("final-patched", pages[2].source.parent.name)
        self.assertEqual("finales-2k", pages[3].source.parent.name)
        self.assertEqual("guias", pages[4].source.parent.name)
        self.assertEqual("guias", pages[5].source.parent.name)

    def test_missing_back_cover_does_not_replace_existing_docs(self) -> None:
        finales = make_run(self.root / "salidas", "v7", 2)
        output = self.root / "docs"
        output.mkdir()
        (output / "keep.txt").write_text("preserve", encoding="utf-8")

        with self.assertRaisesRegex(publisher.PublicationError, "contracubierta"):
            publisher.build_site(
                "v7", publisher.collect_pages(finales), self.cover, self.root / "missing.png", self.avatar, self.home_avatar, output
            )

        self.assertEqual("preserve", (output / "keep.txt").read_text(encoding="utf-8"))

    def test_missing_guide_does_not_replace_existing_docs(self) -> None:
        finales = make_run(self.root / "salidas", "v7", 2)
        (finales.parent / "guias" / "02-page.png").unlink()
        output = self.root / "docs"
        output.mkdir()
        (output / "keep.txt").write_text("preserve", encoding="utf-8")

        with self.assertRaisesRegex(publisher.PublicationError, "guía correspondiente"):
            publisher.collect_pages(finales)

        self.assertEqual("preserve", (output / "keep.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
