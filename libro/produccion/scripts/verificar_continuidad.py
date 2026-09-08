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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Continuity audit failed: {message}")


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    pages = plan["pages"]
    require(len(pages) == 90, "expected 90 pages")
    require(
        "continuidad no depende de adjuntar una página anterior" in plan["state_continuity_policy"],
        "missing plan state-continuity policy",
    )
    require(
        "Opcional y desactivada por defecto" in plan["previous_page_reference_policy"],
        "previous-page reference must be optional and disabled by default",
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
        64: "EL MATRAZ SIGUE VACÍO",
        66: "CONJURO: la transformación ocurre",
    }
    for page_number, phrase in phase_locks.items():
        require(phrase in pages[page_number - 1]["state_lock"], f"page {page_number:02d} missing phase lock")

    audit_pages = [
        int(number)
        for number in re.findall(r"^## (\d{2})\.", AUDIT_REPORT.read_text(encoding="utf-8"), re.MULTILINE)
    ]
    require(audit_pages == list(range(90, 0, -1)), "retrograde report must list pages 90 through 01")

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
    require(
        all("POSE Y ANATOMÍA (OBLIGATORIO)" in prompt for prompt in prompt_texts),
        "every prompt needs positive pose controls",
    )
    require(
        all("PROMPT NEGATIVO — EVITAR ESTRICTAMENTE" in prompt for prompt in prompt_texts),
        "every prompt needs negative anatomy controls",
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
    print("Continuity, voice, anatomy and v2 character-sheet audit passed: 90→01 report, state locks, page 01–03 transitions, Hassan's narrative interiority, 90 pose controls, dark brown eyes and primary v2-sheet authority.")


if __name__ == "__main__":
    main()
