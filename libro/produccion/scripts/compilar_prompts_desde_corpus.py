#!/usr/bin/env python3
"""Compila el corpus editorial de 90 páginas en prompts locales de producción.

No llama a APIs ni transmite referencias. Sólo deriva JSON y archivos de texto
para que corpus, conteo de viñetas y prompts no se separen con el tiempo.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "manuscrito" / "06-corpus-narrativo-90-paginas.md"
PLAN = ROOT / "produccion" / "plan-de-imagenes-90.json"
PROMPTS = ROOT / "produccion" / "prompts-90"
DOSSIER = ROOT / "manuscrito" / "08-guion-tecnico-90-paginas.md"
PAGE = re.compile(r"^### (\d{2})\. (.+?) — (\d+) viñetas$")
BULLET = re.compile(r"^\d+\. (.+)$")

# Una entrada por página y una instrucción de texto por celda.  SILENCIO es una
# elección consciente: no se permite que el modelo invente letras para llenarlo.
TEXT_TRACKS = [
    ["CARTELA: «23:48. Otra jornada.»", "GLOBO DE HASSAN: «Una última medición.»", "SFX: «bip»"],
    ["GLOBO DE HASSAN: «Precisión antes de descanso.»", "SFX: «clic»", "CARTELA: «Por hoy, basta.»"],
    ["GLOBO DE HASSAN: «Mañana sigo.»", "SFX: «clac»"],
    ["SFX: «tap»", "SFX: «toc… toc…»", "CARTELA: «El laboratorio guarda el silencio.»"],
    ["GLOBO DE HASSAN: «Sólo una copa.»", "SFX: «clin»", "GLOBO DE HASSAN: «Música, y a dormir.»"],
    ["GLOBO DE HASSAN: «Frecuencia estable.»", "SFX: «mmmm»", "SFX: «mmmm»", "CARTELA: «Respira.»"],
    ["GLOBO DE HASSAN: «Respira.»", "SFX: «hummm»", "SILENCIO"],
    ["CARTELA: «El sueño toma aire.»", "SFX: «hummm»"],
    ["SFX: «shhh»", "SFX: «tinnn»", "GLOBO DE HASSAN: «¿Qué es eso?»"],
    ["SFX: «whooosh»", "GLOBO DE HASSAN: «Voy…»"],
    ["SFX: «ta-dá»", "SFX: «aplausos lejanos»", "GLOBO DE HASSAN: «¿Dónde estoy?»"],
    ["SFX: «tap»", "SFX: «fwoosh»", "CARTELA: «Una luz toma forma.»"],
    ["SFX: «FWOOSH»", "SFX: «vrrr»", "GLOBO DE HASSAN: «Ferry…»", "SFX: «TÁ!»"],
    ["CARTELA: «La chica de sus sueños.»", "GLOBO DE FERRY: «Hola, Hassan.»", "SFX: «tinnn»"],
    ["GLOBO DE FERRY: «Ven.»", "GLOBO DE HASSAN: «Voy.»"],
    ["GLOBO DE FERRY: «Zeus.»", "GLOBO DE FERRY: «Tranquilo, grandote.»", "SFX: «wuf»"],
    ["SFX: «thump»", "GLOBO DE FERRY: «Buen chico.»", "SFX: «tinnn»"],
    ["GLOBO DE FERRY: «Déjame ver.»", "SFX: «zap»"],
    ["SFX: «plop»", "GLOBO DE FERRY: «Aquí estás.»", "SFX: «fiuu»"],
    ["GLOBO DE FERRY: «Buenos días, Yohi.»", "SFX: «crisp»", "SILENCIO"],
    ["SFX: «toc… toc…»", "GLOBO DE FERRY: «Sin prisa.»"],
    ["SFX: «ñam»", "GLOBO DE FERRY: «Todo a tu tiempo.»", "GLOBO DE HASSAN: «Qué paciencia…»"],
    ["GLOBO DE FERRY: «Tu casa está lista.»", "SFX: «tinnn»"],
    ["SFX: «slip»", "GLOBO DE FERRY: «Cuidado.»", "SFX: «tap»"],
    ["SFX: «slip… slip…»", "CARTELA: «Un camino seguro.»"],
    ["SFX: «frrr»", "GLOBO DE FERRY: «No tengas miedo.»", "SFX: «tinnn»"],
    ["SFX: «tac tac»", "GLOBO DE HASSAN: «Todo ser importa.»"],
    ["SILENCIO", "SILENCIO", "SILENCIO", "CARTELA: «Cuidar también es un poder.»"],
    ["GLOBO DE FERRY: «Hassan.»", "GLOBO DE FERRY: «Me alegra que estés aquí.»", "GLOBO DE HASSAN: «No quiero despertar.»"],
    ["SFX: «tinnn»", "GLOBO DE FERRY: «Sígueme.»"],
    ["SFX: «fwoosh»", "GLOBO DE HASSAN: «¡Ferry, espera!»", "SFX: «tinnn»"],
    ["SFX: «flap»", "CARTELA: «Una lista imposible.»", "SFX: «fiuu»"],
    ["SFX: «whoop»", "SFX: «tap»"],
    ["GLOBO DE HASSAN: «No puedo leerlo.»", "CARTELA: «Cristal. Nube. Estrella.»", "GLOBO DE HASSAN: «Pero puedo encontrarlo.»"],
    ["CARTELA: «Y el sueño se cerró.»", "SFX: «shhh…»"],
    ["SFX: «gasp»", "GLOBO DE HASSAN: «Fue un sueño…»", "SFX: «tinnn»"],
    ["SFX: «clic»", "GLOBO DE HASSAN: «¿Qué dejó aquí?»"],
    ["SFX: «tap»", "SFX: «tac»", "CARTELA: «La mañana ya no es igual.»"],
    ["SFX: «grrr»", "SFX: «blup»", "SFX: «pssshh»"],
    ["GLOBO DE HASSAN: «Mi café…»", "SFX: «tinnn»", "GLOBO DE HASSAN: «La nota.»"],
    ["SFX: «peel»", "GLOBO DE HASSAN: «Es real.»"],
    ["GLOBO DE HASSAN: «Necesito comprobarlo.»", "SFX: «tap»", "GLOBO DE HASSAN: «Al laboratorio.»"],
    ["SFX: «clac»", "SFX: «swish»", "CARTELA: «Una pregunta merece método.»"],
    ["SFX: «zoom»", "CARTELA: «Sinceridad.»", "GLOBO DE HASSAN: «Primer ingrediente.»"],
    ["CARTELA: «Empatía.»", "CARTELA: «Inteligencia.»", "CARTELA: «Curiosidad.»", "GLOBO DE HASSAN: «Una receta de ella.»"],
    ["SFX: «fwoom»", "CARTELA: «No son palabras. Son pistas.»", "GLOBO DE HASSAN: «Las reuniré.»"],
    ["GLOBO DE HASSAN: «Cocina. Sala. Patio.»", "SFX: «tinnn»"],
    ["SFX: «clac»", "GLOBO DE HASSAN: «Aquí empieza.»", "SFX: «fiuu»"],
    ["SFX: «crash»", "GLOBO DE HASSAN: «¡No, no, no!»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «La búsqueda comenzó.»", "SFX: «tinnn»"],
    ["CARTELA: «Talento que da calor.»", "SFX: «fwoom»", "GLOBO DE HASSAN: «Canela.»"],
    ["SFX: «rustle»", "GLOBO DE HASSAN: «Vainilla.»", "SFX: «tinnn»"],
    ["SFX: «tinnn»", "GLOBO DE HASSAN: «Una cuchara también puede ser magia.»"],
    ["SFX: «scrape»", "GLOBO DE HASSAN: «¿Una moneda?»", "SFX: «vrrr»"],
    ["GLOBO DE HASSAN: «Trabajo y paciencia.»", "SFX: «clic clic»"],
    ["SFX: «fiuu»", "GLOBO DE HASSAN: «El mismo hilo.»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «El mar estaba aquí.»", "SFX: «swish»", "CARTELA: «Una gota de horizonte.»"],
    ["SFX: «scrape»", "GLOBO DE HASSAN: «Resistir y florecer.»", "SFX: «crack»"],
    ["GLOBO DE HASSAN: «Cariño que abriga.»", "SFX: «poof»"],
    ["SFX: «clink»", "GLOBO DE HASSAN: «Confianza.»", "SFX: «tinnn»"],
    ["SFX: «poof»", "GLOBO DE HASSAN: «Espera, nube.»", "SFX: «pop»"],
    ["SFX: «clink»", "SFX: «fiuu»", "GLOBO DE HASSAN: «Casi lo tengo.»"],
    ["GLOBO DE HASSAN: «Cada cosa tiene su lugar.»", "SFX: «tinnn»", "CARTELA: «La fórmula empieza a mirar de vuelta.»"],
    ["SFX: «clac»", "SFX: «beeeep»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «Faltan piezas.»", "SFX: «fwoom»"],
    ["CARTELA: «Sinceridad: luz que no esconde nada.»", "GLOBO DE HASSAN: «Que nada se oculte.»", "CARTELA: «Empatía: abrazar sin invadir.»", "SFX: «fwoom»"],
    ["CARTELA: «Inteligencia: entender para cuidar.»", "SFX: «tinnn»", "CARTELA: «Curiosidad: preguntar sin miedo.»", "SFX: «fwoom»"],
    ["CARTELA: «Sonrisa: alegría que enciende.»", "SFX: «tinnn»", "CARTELA: «Pasión: fuego que protege.»", "SFX: «fwoosh»"],
    ["CARTELA: «Ternura: hacer hogar.»", "CARTELA: «Cuidar es recordar.»", "CARTELA: «Valentía: proteger sin cerrar.»", "SFX: «clang»"],
    ["CARTELA: «Trabajo: construir cada día.»", "GLOBO DE HASSAN: «Con cuidado.»", "CARTELA: «Esperanza: una luz que insiste.»", "SFX: «tinnn»"],
    ["CARTELA: «Dulzura: una chispa basta.»", "SFX: «plop»", "CARTELA: «Hermosura: el mar cabe en una concha.»", "SFX: «swish»"],
    ["CARTELA: «Resiliencia: florecer después de la piedra.»", "SFX: «crack»", "CARTELA: «Talento: dar sabor al mundo.»", "SFX: «fwoom»", "CARTELA: «Orden: hacer espacio para la magia.»", "SFX: «tinnn»"],
    ["CARTELA: «Alegría: sonar como el sol.»", "SFX: «cling cling»", "CARTELA: «Paciencia: dejar llegar lo importante.»", "GLOBO DE HASSAN: «Espero.»", "CARTELA: «Cariño: abrigar sin retener.»", "SFX: «poof»"],
    ["CARTELA: «Mensajes: decir amor sin ruido.»", "SFX: «flap»", "CARTELA: «Consideración: tender un puente.»", "SFX: «fiuu»", "CARTELA: «Atrevimiento: saltar y volver.»", "SFX: «zap»"],
    ["CARTELA: «Fortaleza: moverse con gracia.»", "SFX: «fwoosh»", "CARTELA: «Nutrición: sostener todo lo vivo.»", "SFX: «glow»", "CARTELA: «Confianza: abrir sin forzar.»", "SFX: «clic»"],
    ["CARTELA: «Lealtad: quedarse libremente.»", "GLOBO DE HASSAN: «Sin cadenas.»", "CARTELA: «Conexión: encontrarse.»", "SFX: «fiuu»", "CARTELA: «Dulzura y fuego: dos fuerzas en una.»", "SFX: «fwoom»"],
    ["CARTELA: «Curiosidad: seguir la luz.»", "GLOBO DE HASSAN: «No se quedan quietas.»", "SFX: «tinnn»", "CARTELA: «Creatividad: imaginar lo imposible.»", "SFX: «shraaa»"],
    ["CARTELA: «Veintinueve razones.»", "GLOBO DE HASSAN: «Todas llevan a ti.»", "GLOBO DE HASSAN: «Con respeto.»", "SFX: «fwoom»"],
    ["SFX: «clic»", "CARTELA: «La receta ya no necesita palabras.»", "SFX: «fiuu»", "GLOBO DE HASSAN: «Ahora.»"],
    ["SFX: «KRAK»", "SFX: «hummm»", "SFX: «FWOOM»"],
    ["SFX: «vrrr»", "SFX: «tinnn»", "GLOBO DE HASSAN: «Funciona.»", "SFX: «shraaa»"],
    ["GLOBO DE HASSAN: «Despacio.»", "CARTELA: «El sueño también tiene memoria.»", "GLOBO DE HASSAN: «La magia también es método.»"],
    ["SFX: «vrrr»", "SFX: «fiuu»", "SFX: «crack»"],
    ["SFX: «tinnn»", "SFX: «FWOOM»", "CARTELA: «Una estrella aprende a nacer.»"],
    ["GLOBO DE HASSAN: «Ferry…»", "CARTELA: «Todas sus luces estaban ahí.»"],
    ["SFX: «shraaa»", "SFX: «tinnn»", "GLOBO DE HASSAN: «No te hice. Te encontré.»"],
    ["SFX: «tap»", "GLOBO DE FERRY: «Llegué.»", "SILENCIO"],
    ["GLOBO DE FERRY: «¿Vamos?»", "GLOBO DE FERRY: «A donde el mar nos alcance.»", "GLOBO DE HASSAN: «Juntos.»"],
    ["SFX: «swish»", "SFX: «clic»", "SFX: «clac»", "SFX: «vrrum»", "CARTELA: «Hacia la costa.»"],
    ["SFX: «shhh»", "GLOBO DE HASSAN: «La concha.»", "CARTELA: «Y la fórmula siguió brillando.»"],
]


def plain(value: str) -> str:
    return re.sub(r"\*\*(.*?)\*\*", r"\1", value).strip()


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value


def references(page: int) -> list[str]:
    if page <= 10:
        return ["hassan"]
    if page <= 35:
        return ["hassan", "ferry"]
    if page <= 83:
        return ["hassan"]
    if page == 84 or page == 85:
        return ["hassan"]
    return ["hassan", "ferry"]


def layout_for(page: int, panels: int) -> tuple[str, list[str]]:
    """Return an explicit production reticle and the placement of every cell."""
    variants = {
        2: [
            ("dos franjas horizontales: superior 58%, inferior 42%", ["franja superior a sangre", "franja inferior a sangre"]),
            ("dos celdas verticales: izquierda 42%, derecha 58%", ["celda izquierda alta", "celda derecha dominante"]),
        ],
        3: [
            ("una viñeta superior de 48%; dos viñetas inferiores iguales", ["superior panorámica", "inferior izquierda", "inferior derecha"]),
            ("dos viñetas superiores iguales; una viñeta inferior de ancho completo", ["superior izquierda", "superior derecha", "inferior panorámica"]),
        ],
        4: [
            ("cuadrícula 2×2, con la lectura en zigzag de arriba a abajo", ["superior izquierda", "superior derecha", "inferior izquierda", "inferior derecha"]),
            ("tira superior de ancho completo y tres celdas inferiores: izquierda, centro, derecha", ["superior panorámica", "inferior izquierda", "inferior central", "inferior derecha"]),
        ],
        5: [
            ("viñeta superior de ancho completo 36%; dos celdas centrales y dos inferiores", ["superior panorámica", "centro izquierda", "centro derecha", "inferior izquierda", "inferior derecha"]),
        ],
        6: [
            ("cuadrícula regular de 2 columnas × 3 filas", ["fila 1 izquierda", "fila 1 derecha", "fila 2 izquierda", "fila 2 derecha", "fila 3 izquierda", "fila 3 derecha"]),
        ],
    }
    return variants[panels][page % len(variants[panels])]


def camera_for(action: str, index: int, panels: int) -> str:
    lower = action.lower()
    if any(word in lower for word in ("detalle", "mano", "ojos", "lupa", "llave", "concha", "moneda", "nota")):
        return "plano detalle, foco nítido en el objeto y profundidad de campo suave"
    if any(word in lower for word in ("vista cenital", "desde abajo", "fachada", "interior amplio", "panorámica", "campo", "mar", "carretera")):
        return "plano general cinematográfico, profundidad visible y lectura de ambiente"
    if index == 1:
        return "plano de establecimiento, composición clara y aire alrededor del sujeto"
    if index == panels:
        return "primer plano emocional o plano de cierre; dirigir la mirada hacia la siguiente página"
    return "plano medio dinámico, gesto y acción perfectamente legibles"


def literal_text(value: str) -> str:
    """The brief requires English-style double quotes around literal text."""
    return value.replace("«", '"').replace("»", '"')


def lettering_for(cue: str, index: int, panels: int) -> tuple[str, str, str]:
    """Separate technical metadata from the only text that may appear in art."""
    cue = literal_text(cue)
    if cue == "SILENCIO":
        return ("silencio", "sin lettering, globo ni SFX", "SILENCIO")
    label, printed = cue.split(": ", 1)
    if label.startswith("CARTELA"):
        return (
            "cartela",
            "esquina superior izquierda de la celda, caja crema de borde negro; no cubrir rostro ni acción",
            printed,
        )
    if label.startswith("GLOBO DE"):
        side = "superior izquierda" if index % 2 else "superior derecha"
        return (
            "globo de diálogo",
            f"{side} de la celda, junto a la cabeza del hablante; cola clara al personaje, máximo 18% del área de la celda",
            printed,
        )
    return (
        "efecto sonoro integrado",
        "junto a la línea de acción, detrás del foco narrativo; letras expresivas sin cubrir cara, manos ni objeto clave",
        printed,
    )


def parse() -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for raw in CORPUS.read_text(encoding="utf-8").splitlines():
        found = PAGE.match(raw)
        if found:
            if current:
                pages.append(current)
            number, title, panels = found.groups()
            current = {
                "number": int(number),
                "title": title,
                "panels": int(panels),
                "beats": [],
            }
            continue
        if current:
            beat = BULLET.match(raw)
            if beat:
                current["beats"].append(plain(beat.group(1)))
    if current:
        pages.append(current)
    return pages


def cells_for(page: dict[str, object]) -> tuple[str, list[dict[str, str]]]:
    number = page["number"]
    panels = page["panels"]
    layout, placements = layout_for(number, panels)
    text_track = TEXT_TRACKS[number - 1]
    if len(text_track) != panels:
        raise ValueError(f"Page {number:02d} has {len(text_track)} text cues for {panels} panels.")
    cells = []
    for index, (action, placement, cue) in enumerate(zip(page["beats"], placements, text_track), 1):
        lettering_type, lettering_placement, printed_text = lettering_for(cue, index, panels)
        cells.append(
            {
                "cell": str(index),
                "placement": placement,
                "camera": camera_for(action, index, panels),
                "action": action,
                "lettering_type": lettering_type,
                "lettering_placement": lettering_placement,
                "printed_text": printed_text,
            }
        )
    return layout, cells


def prompt_for(page: dict[str, object], layout: str, cells: list[dict[str, str]]) -> str:
    number = page["number"]
    title = page["title"]
    panels = page["panels"]
    scene = "\n".join(
        f"CELDA {cell['cell']} — posición: {cell['placement']}; cámara: {cell['camera']}.\n"
        f"Acción y arte: {cell['action']}\n"
        f"Tipo de lettering: {cell['lettering_type']}. Posición de lettering: {cell['lettering_placement']}.\n"
        f"Texto impreso exacto: {cell['printed_text']}"
        for cell in cells
    )
    return f"""Create one original vertical 6x9 comic-book page in a 2:3 aspect ratio.
Use exactly {panels} distinct comic panels separated by clean, consistent gutters; do not make a collage or a poster.
Exact page reticle: {layout}. Read from upper left to lower right.
The only letters permitted in the art are the phrases after “Texto impreso exacto:”. Render each phrase character for character, including accents and punctuation, using the double quotes shown. “CELDA”, “Tipo de lettering”, “Posición de lettering” and every other label are production instructions only: never render those labels in the image. Place the lettering exactly as specified per cell. If “Texto impreso exacto” says SILENCIO, draw no bubble and no letters in that cell. Do not add, alter, translate or invent any other text, number, logo or watermark. The recipe note, when present, must show only deliberately illegible numbered-looking strokes.
Original retro chibi-superhero graphic novel: adult characters with compact proportions, expressive round faces, crisp black ink lines, flat color with restrained cel shading, cinematic framing and readable action. Hassan is a gentle, meticulous adult scientist with dark hair and a full beard. Ferry is an original adult pop heroine: warm, athletic and protective, with long brown hair; never portray her as created, owned or controlled by Hassan.
Cool white, steel and blue-gray laboratory reality; dream and magic in warm pink, coral, gold and carmine. Repeat the red thread, empty-to-full flask and pink-gold star only when the beats call for them. Keep faces, hands and focal objects at least 10% inside every edge.

Page {number:02d} — {title}
{scene}
"""


def dossier_for(pages: list[dict[str, object]]) -> str:
    entries = [
        "# Guion técnico — 90 páginas con diálogo\n",
        "\n",
        "Este dossier es la especificación de producción. Cada página define retícula, orden de lectura, cámara, acción y el único texto permitido. Todo texto literal va entre comillas dobles. Las etiquetas técnicas no se imprimen: sólo se imprime el valor de `Texto impreso exacto`. `SILENCIO` significa que no puede aparecer ningún globo ni letra en esa celda.\n",
    ]
    for page in pages:
        layout, cells = cells_for(page)
        entries.append(f"\n## {page['number']:02d}. {page['title']} — {page['panels']} celdas\n\n")
        entries.append(f"**Retícula:** {layout}.\n\n")
        for cell in cells:
            entries.append(
                f"{cell['cell']}. **{cell['placement']} — {cell['camera']}.** "
                f"{cell['action']}\n"
                f"   **Lettering:** {cell['lettering_type']}; {cell['lettering_placement']}.\n"
                f"   **Texto impreso exacto:** {cell['printed_text']}\n"
            )
    return "".join(entries)


def main() -> None:
    pages = parse()
    errors: list[str] = []
    if len(pages) != 90:
        errors.append(f"Expected 90 pages, found {len(pages)}.")
    numbers = [page["number"] for page in pages]
    if numbers != list(range(1, 91)):
        errors.append("Page numbers must be consecutive from 01 to 90.")
    for page in pages:
        if not 2 <= page["panels"] <= 6:
            errors.append(f"Page {page['number']:02d} has invalid panel count.")
        if len(page["beats"]) != page["panels"]:
            errors.append(
                f"Page {page['number']:02d} has {len(page['beats'])} beats for {page['panels']} panels."
            )
        if len(TEXT_TRACKS[page["number"] - 1]) != page["panels"]:
            errors.append(f"Page {page['number']:02d} has an invalid dialogue/SFX track.")
    if errors:
        raise SystemExit("\n".join(errors))

    PROMPTS.mkdir(parents=True, exist_ok=True)
    plan_pages = []
    for page in pages:
        identifier = f"{page['number']:02d}-{slug(page['title'])}"
        layout, cells = cells_for(page)
        prompt = prompt_for(page, layout, cells)
        (PROMPTS / f"{identifier}.txt").write_text(prompt, encoding="utf-8")
        plan_pages.append(
            {
                "id": identifier,
                "panels": page["panels"],
                "layout": layout,
                "references": references(page["number"]),
                "title": page["title"],
                "beats": page["beats"],
                "cells": cells,
                "prompt": f"prompts-90/{identifier}.txt",
            }
        )
    DOSSIER.write_text(dossier_for(pages), encoding="utf-8")
    PLAN.write_text(
        json.dumps(
            {
                "project": "PowerPuff Ferry — corpus visual de 90 páginas",
                "source": "../manuscrito/06-corpus-narrativo-90-paginas.md",
                "aspect_ratio": "2:3",
                "trim_size": "6x9 in",
                "model": "gpt-image-2",
                "resolution": "2K",
                "print_page_count": 90,
                "visual_storytelling_only": False,
                "text_policy": "Sólo el diálogo, cartelas y efectos declarados por celda; el texto literal usa comillas dobles.",
                "pages": plan_pages,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Compiled {len(plan_pages)} local prompts in {PROMPTS}.")


if __name__ == "__main__":
    main()
