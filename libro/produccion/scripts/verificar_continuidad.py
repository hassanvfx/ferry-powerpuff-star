#!/usr/bin/env python3
"""Verifica los bloqueos de continuidad estructural del plan de 90 páginas.

No evalúa píxeles: comprueba que el compilador conservó los estados y las
ausencias que una revisión humana debe contrastar luego con el arte.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "produccion" / "plan-de-imagenes-90.json"
AUDIT_REPORT = ROOT / "produccion" / "auditoria-retroactiva-90.md"
PROMPTS = ROOT / "produccion" / "prompts-90"
GUIDES = ROOT / "produccion" / "prompts-guia-90"
CONTINUITY_INDEX = ROOT / "produccion" / "indice-de-continuidad.json"
CREATURE_AUDIT = ROOT / "produccion" / "auditoria-de-especies-90.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Continuity audit failed: {message}")


def asset_applies(asset: dict, page: dict) -> bool:
    rules = asset.get("pages", {})
    number = int(page["id"][:2])
    if rules.get("from_plan_references"):
        return asset["id"] in page.get("references", [])
    return number in rules.get("values", []) or any(
        start <= number <= end for start, end in rules.get("ranges", [])
    )


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    pages = plan["pages"]
    require(len(pages) == 90, "expected 90 pages")
    continuity_index = json.loads(CONTINUITY_INDEX.read_text(encoding="utf-8"))
    assets = continuity_index.get("assets", [])
    asset_ids = [asset.get("id") for asset in assets]
    required_asset_ids = {
        "style-reference", "hassan", "ferry", "zeus", "yohi", "caracoles", "arana",
        "laboratorio-oficina", "casa-de-hassan", "escenario-onirico",
        "jardin-protector-de-ferry", "costa",
    }
    require(len(asset_ids) == len(set(asset_ids)), "continuity index has duplicate asset ids")
    require(required_asset_ids <= set(asset_ids), "continuity index is missing a required creature or location asset")
    by_asset_id = {asset["id"]: asset for asset in assets}
    for asset in assets:
        require(asset.get("status") in {"approved", "candidate"}, f"unsupported asset status: {asset.get('id')}")
        require((CONTINUITY_INDEX.parent / asset["path"]).is_file(), f"missing continuity asset: {asset.get('id')}")
    require(by_asset_id["zeus"]["path"].endswith("zeus-character-sheet-v3.png"), "Zeus must use the unified v3 sheet")
    required_page_assets = {
        "01-el-laboratorio-al-anochecer": {"laboratorio-oficina"},
        "16-zeus-aparece": {"zeus", "jardin-protector-de-ferry"},
        "20-yohi-y-la-hoja-fresca": {"yohi", "jardin-protector-de-ferry"},
        "24-los-caracoles": {"caracoles", "jardin-protector-de-ferry"},
        "26-la-arana": {"arana", "jardin-protector-de-ferry"},
        "90-la-playa-abierta": {"costa"},
    }
    for page in pages:
        expected = required_page_assets.get(page["id"])
        if expected:
            attached = {asset["id"] for asset in assets if asset_applies(asset, page)}
            require(expected <= attached, f"{page['id']} is missing its continuity index assignment")
    require(
        "continuidad no depende de adjuntar una página anterior" in plan["state_continuity_policy"],
        "missing plan state-continuity policy",
    )
    require(
        "Opcional y desactivada por defecto" in plan["previous_page_reference_policy"],
        "previous-page reference must be optional and disabled by default",
    )
    require(
        "guía esquemática de composición" in plan["production_guide_policy"],
        "missing production-guide policy",
    )
    require(
        "raza, especie y género se bloquean por celda" in plan["creature_identity_policy"],
        "missing per-cell creature identity-and-gender policy",
    )
    require("cinco dedos visibles" in plan["anatomy_policy"], "missing plan anatomy policy")
    require(
        "autoridad visual primaria" in plan["character_sheet_policy"],
        "missing v2 character-sheet authority policy",
    )
    require(
        all(not page["previous_page_reference"]["attached"] for page in pages),
        "default plan must not attach a predecessor page",
    )
    phase_locks = {
        7: "ANTES DEL SUEÑO",
        36: "REALIDAD AL DESPERTAR",
        40: "LA NOTA FÍSICA YA EXISTE",
        44: "LA LUPA YA ES HERRAMIENTA",
        56: "EL CARRETE Y LA CONCHA existen",
        64: "EL MISMO MATRAZ contiene las once luces",
        66: "CONJURO: la transformación ocurre",
    }
    for page_number, phrase in phase_locks.items():
        require(phrase in pages[page_number - 1]["state_lock"], f"page {page_number:02d} missing phase lock")

    audit_pages = [
        int(number)
        for number in re.findall(r"^## (\d{2})\.", AUDIT_REPORT.read_text(encoding="utf-8"), re.MULTILINE)
    ]
    require(audit_pages == list(range(90, 0, -1)), "retrograde report must list pages 90 through 01")
    creature_audit_pages = [
        int(number)
        for number in re.findall(r"^## (\d{2})\.", CREATURE_AUDIT.read_text(encoding="utf-8"), re.MULTILINE)
    ]
    require(creature_audit_pages == list(range(1, 91)), "creature audit must list pages 01 through 90")

    page_one = pages[0]["cells"]
    page_two = pages[1]["cells"]
    require(
        page_one[0]["printed_text"] == '"9 de septiembre 2026. Una noche más..."',
        "page 01 opening date card is incorrect",
    )
    require(
        pages[-1]["cells"][-1]["printed_text"] == '"10 de septiembre 2026 -Happy Bday my Love."',
        "page 90 closing date card is incorrect",
    )
    required_locks = {
        "01/1": (page_one[0], "sin hilo rojo, carrete, nota, lupa, llave, concha, estrella"),
        "01/2": (page_one[1], "monitor de la derecha está ENCENDIDO"),
        "01/3": (page_one[2], "NO dibujes hilo, curva roja, carrete, llave, estrella"),
        "02/1": (page_two[0], "monitor está todavía ENCENDIDO"),
        "02/2": (page_two[1], "inicia esta celda ENCENDIDO"),
        "02/3": (page_two[2], "ya está APAGADO con pantalla negra"),
    }
    for cell_id, (cell, phrase) in required_locks.items():
        require(phrase in cell["state_lock"], f"{cell_id} missing state lock: {phrase}")

    require("sigue encendido" in pages[1]["beats"][0], "page 02 cell 1 must keep monitor on")
    require("se apaga en ese gesto" in pages[1]["beats"][1], "page 02 cell 2 must perform shutdown")
    require("ya negro" in pages[1]["beats"][2], "page 02 cell 3 must keep monitor off")

    page_three_second_cell = pages[2]["cells"][1]
    page_three_first_cell = pages[2]["cells"][0]
    require("plano medio en tres cuartos" in page_three_second_cell["camera"], "page 03/2 needs a three-quarter pose camera")
    require("cinco dedos" in page_three_second_cell["state_lock"], "page 03/2 needs explicit hand anatomy")
    book_cells = ((3, 1), (4, 1), (5, 2), (6, 4), (7, 1), (8, 1), (82, 3))
    for page_number, cell_number in book_cells:
        require(
            pages[page_number - 1]["cells"][cell_number - 1]["permitted_diegetic_text"]
            == '"Volver a mí" — "Ferry Beltran"',
            f"page {page_number:02d}/{cell_number} is missing the canonical book cover",
        )
    require("portada rosa intenso" in page_three_first_cell["state_lock"], "page 03/1 must establish the pink book")
    prompt_texts = [path.read_text(encoding="utf-8") for path in PROMPTS.glob("*.txt")]
    require(len(prompt_texts) == 90, "expected 90 generated prompts")
    max_prompt_characters = 19_000
    require(plan.get("max_prompt_characters") == max_prompt_characters, "plan must declare the 19,000-character prompt limit")
    require(all(len(prompt) <= max_prompt_characters for prompt in prompt_texts), "a final prompt exceeds 19,000 characters")
    require(
        all("REFERENCIAS DECLARADAS PARA ESTA PÁGINA — ARCHIVOS DE EJECUCIÓN:" in prompt for prompt in prompt_texts),
        "every source prompt must declare its execution reference sheets",
    )
    declared_prompt_assets = {
        "01-el-laboratorio-al-anochecer.txt": ("laboratorio-oficina",),
        "16-zeus-aparece.txt": ("zeus-character-sheet-v3.png", "jardin-protector-de-ferry"),
        "20-yohi-y-la-hoja-fresca.txt": ("yohi-character-sheet-v1.png", "jardin-protector-de-ferry"),
        "24-los-caracoles.txt": ("caracoles-character-sheet-v1.png",),
        "26-la-arana.txt": ("arana-character-sheet-v1.png",),
        "90-la-playa-abierta.txt": ("costa-environment-sheet-v1.png",),
    }
    for filename, required_assets in declared_prompt_assets.items():
        source_prompt = (PROMPTS / filename).read_text(encoding="utf-8")
        for asset in required_assets:
            require(asset in source_prompt, f"{filename} is missing its declared execution asset {asset}")
    require(
        all("POSE Y ANATOMÍA (OBLIGATORIO)" in prompt for prompt in prompt_texts),
        "every prompt needs positive pose controls",
    )
    require(
        all("PROMPT NEGATIVO — EVITAR ESTRICTAMENTE" in prompt for prompt in prompt_texts),
        "every prompt needs negative anatomy controls",
    )
    require(
        all("BIBLIA DE IDENTIDAD DE CRIATURAS — AUTORIDAD OBLIGATORIA" in prompt for prompt in prompt_texts),
        "every prompt needs creature identity authority",
    )
    require(
        all("PROMPT NEGATIVO — ESPECIE/RAZA" in prompt for prompt in prompt_texts),
        "every prompt needs negative species/breed controls",
    )
    require(
        all("MATRAZ CANÓNICO ÚNICO" in prompt for prompt in prompt_texts),
        "every prompt needs the single canonical flask continuity lock",
    )
    creature_cells = {
        (16, 1): "Zeus — niño, ROTTWEILER adulto macho negro y fuego",
        (19, 3): "Zeus — niño, ROTTWEILER adulto macho negro y fuego",
        (20, 2): "Yohi — niña, TORTUGA SULCATA BEBÉ hembra",
        (24, 1): "exactamente DOS CARACOLES TERRESTRES",
        (26, 1): "UNA ARAÑA TEJEDORA pequeña",
        (28, 1): "Zeus — niño, ROTTWEILER adulto macho negro y fuego",
        (28, 2): "Yohi — niña, TORTUGA SULCATA BEBÉ hembra",
        (28, 3): "exactamente DOS CARACOLES TERRESTRES",
        (28, 4): "UNA ARAÑA TEJEDORA pequeña",
    }
    for (page_number, cell_number), identity in creature_cells.items():
        cell = pages[page_number - 1]["cells"][cell_number - 1]
        require(identity in cell["creature_lock"], f"page {page_number:02d}/{cell_number} missing species lock: {identity}")
    page_19_prompt = (PROMPTS / "19-la-mano-protectora.txt").read_text(encoding="utf-8")
    require(
        "Zeus — niño, ROTTWEILER adulto macho negro y fuego" in page_19_prompt
        and "nunca golden retriever, labrador, perro dorado/crema" in page_19_prompt,
        "page 19 must explicitly prevent Zeus from becoming a golden retriever",
    )
    require(
        all("HOJAS DE PERSONAJE V2 — AUTORIDAD VISUAL PRIMARIA" in prompt for prompt in prompt_texts),
        "every prompt needs the v2 character-sheet authority",
    )
    require(
        all("silueta madura, piernas largas y cabeza no extrema de la hoja v2" in prompt for prompt in prompt_texts),
        "every prompt needs the approved adult semi-chibi proportion",
    )
    require(
        all("ojos café oscuro, profundos y expresivos" in prompt for prompt in prompt_texts),
        "every prompt needs dark brown eyes for both characters",
    )
    require(
        not any("deep blue-cyan eyes" in prompt or "warm pink-magenta eyes" in prompt for prompt in prompt_texts),
        "old blue/cyan or pink/magenta eye canon remains in prompts",
    )
    require(
        not any(
            "Preserve their approved character sheets only where they agree" in prompt
            or "enormous expressive oval eyes" in prompt
            or "adult chibi proportions" in prompt
            for prompt in prompt_texts
        ),
        "a stale character-sheet hierarchy or extreme chibi proportion remains in prompts",
    )
    require(
        all("Evita metáforas vagas, frases de autoayuda, solemnidad" in prompt for prompt in prompt_texts),
        "every prompt needs Hassan's natural-voice direction",
    )
    rejected_hassan_lines = (
        "Si cierro esto bien, quizá también cierre el ruido.",
        "Mañana seguirá aquí. Yo también necesito volver a mí.",
        "Que la música me desate el nudo de hoy.",
        "No es una mezcla. Es una pregunta tomando forma.",
    )
    require(
        not any(line in prompt for prompt in prompt_texts for line in rejected_hassan_lines),
        "a rejected, artificial Hassan line remains in active prompts",
    )

    thoughts = [
        cell["printed_text"].strip('"')
        for page in pages
        for cell in page["cells"]
        if cell["lettering_type"] == "pensamiento interior de Hassan"
    ]
    substantial_thoughts = [thought for thought in thoughts if not re.match(r"^\d+\.", thought)]
    require(len(thoughts) >= 70, "Hassan needs at least 70 inner thoughts")
    require(
        sum(len(thought.split()) >= 6 for thought in substantial_thoughts) / len(substantial_thoughts) >= 0.9,
        "at least 90% of Hassan non-enumeration thoughts need six or more words",
    )
    guide_paths = sorted(GUIDES.glob("[0-9][0-9]-*.md"))
    require((GUIDES / "README.md").is_file(), "production-guide README is missing")
    require(len(guide_paths) == 90, "expected 90 production guides")
    for page, guide_path in zip(pages, guide_paths):
        guide = guide_path.read_text(encoding="utf-8")
        require(len(guide) <= max_prompt_characters, f"{guide_path.name} exceeds 19,000 characters")
        require(guide.startswith(f"# Prompt de storyboard anotado {page['id'][:2]}"), f"bad guide title: {guide_path.name}")
        for heading in ("## Estado de escena", "## Continuidad de borde a borde", "## Desglose por celda", "## Chequeo de aprobación"):
            require(heading in guide, f"{guide_path.name} missing {heading}")
        require("Tiempo/luz:" in guide and "Vestuario/accesorios:" in guide, f"{guide_path.name} missing scene context")
        require(
            "Guion de voz/efecto para el prompt final" in guide
            and "Pose y apoyo corporal:" in guide
            and "Mirada/eje de atención:" in guide
            and "Entorno y hora:" in guide
            and "Notas de continuidad por dimensión" in guide
            and "Especie/raza bloqueada:" in guide,
            f"{guide_path.name} missing cell production details",
        )
        require(
            "NO dibujes arte final" in guide
            and "línea de acción visible" in guide
            and "Sistema gráfico visible en CADA celda" in guide
            and "ID (personaje)" in guide
            and "ESPECIE/RAZA" in guide,
            f"{guide_path.name} is not a technical annotated storyboard prompt",
        )
        prompt = (ROOT / "produccion" / page["prompt"]).read_text(encoding="utf-8")
        species_tokens = {
            "Zeus": "Zeus — niño, ROTTWEILER adulto macho negro y fuego",
            "Yohi": "Yohi — niña, TORTUGA SULCATA BEBÉ hembra",
            "caracoles": "exactamente DOS CARACOLES TERRESTRES",
            "araña": "UNA ARAÑA TEJEDORA pequeña",
        }
        locks = " ".join(cell["creature_lock"] for cell in page["cells"])
        for creature, token in species_tokens.items():
            expected = token in locks
            require(
                (token in prompt) == expected,
                f"page {page['id']} final prompt leaks or misses {creature}",
            )
            require(
                (token in guide) == expected,
                f"page {page['id']} guide leaks or misses {creature}",
            )
    page_19_guide = (GUIDES / "19-la-mano-protectora.md").read_text(encoding="utf-8")
    require(
        "Zeus — niño, ROTTWEILER adulto macho negro y fuego" in page_19_guide
        and "nunca golden retriever, labrador, perro dorado/crema" in page_19_guide,
        "page 19 guide must carry Zeus's full breed lock",
    )
    for page_number, cell_number in ((32, 1), (32, 2), (41, 1), (41, 2), (63, 2), (64, 3), (65, 1), (65, 2)):
        cell = pages[page_number - 1]["cells"][cell_number - 1]
        require(cell["permitted_diegetic_text"] == '"29 razones"', f"page {page_number:02d}/{cell_number} lost the canonical list heading")

    visible_cells = [cell for page in pages for cell in page["cells"]]
    numbered_positions = []
    for position, cell in enumerate(visible_cells):
        match = re.match(r'^"(\d+)\. ', cell["printed_text"])
        if match:
            numbered_positions.append((position, int(match.group(1))))
    require([number for _, number in numbered_positions] == list(range(1, 30)), "ingredients must be visibly counted once, continuously, from 1 to 29")
    for index, (position, number) in enumerate(numbered_positions):
        next_position = numbered_positions[index + 1][0] if index + 1 < len(numbered_positions) else len(visible_cells)
        memory_window = " ".join(cell["printed_text"] for cell in visible_cells[position + 1:next_position])
        require("Ferry" in memory_window, f"ingredient {number} needs Hassan's visible Ferry memory before the next count")
    page_18 = " ".join(cell["action"] for cell in pages[17]["cells"])
    page_19 = " ".join(cell["action"] for cell in pages[18]["cells"])
    page_24 = " ".join(cell["action"] for cell in pages[23]["cells"])
    page_37_text = " ".join(cell["printed_text"] for cell in pages[36]["cells"])
    require("no hay agua, gota" in page_18.lower() and "no hay gota" in page_19.lower(), "pages 18–19 must exclude the unexplained water-drop beat")
    require("exactamente dos" in page_24.lower() and "ramita" in page_24.lower(), "page 24 must make the two-snail dry crossing legible")
    require("¡Vamos, sin miedo a nada!" in page_37_text and "mala espina" not in page_37_text.lower(), "page 37 must play as courage and hope")
    print("Continuity, voice, anatomy and v2 character-sheet audit passed: 90→01 report, 19,000-character cap, one canonical flask, continuous 1–29 recipe count, species/gender locks, state locks, natural voice and primary v2-sheet authority.")


if __name__ == "__main__":
    main()
