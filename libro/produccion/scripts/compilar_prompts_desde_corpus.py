#!/usr/bin/env python3
"""Compila el corpus editorial de 90 páginas en prompts locales de producción.

No llama a APIs ni transmite referencias. Sólo deriva JSON y archivos de texto
para que corpus, conteo de viñetas y prompts no se separen con el tiempo.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "manuscrito" / "06-corpus-narrativo-90-paginas.md"
PLAN = ROOT / "produccion" / "plan-de-imagenes-90.json"
CONTINUITY_INDEX = ROOT / "produccion" / "indice-de-continuidad.json"
PROMPTS = ROOT / "produccion" / "prompts-90"
GUIDES = ROOT / "produccion" / "prompts-guia-90"
DOSSIER = ROOT / "manuscrito" / "08-guion-tecnico-90-paginas.md"
TREATMENT = ROOT / "produccion" / "tratamiento-visual-2-3.md"
AUDIT_REPORT = ROOT / "produccion" / "auditoria-retroactiva-90.md"
DIALOGUE_LEDGER = ROOT / "produccion" / "dialogos-y-texto-visible-90.md"
CREATURE_AUDIT = ROOT / "produccion" / "auditoria-de-especies-90.md"
PAGE = re.compile(r"^### (\d{2})\. (.+?) — (\d+) viñetas$")
BULLET = re.compile(r"^\d+\. (.+)$")

TREATMENT_BASE = (
    "Original 2:3 portrait comic-book page, adult semi-chibi-superhero characters with large "
    "expressive dark-eyed faces, mature athletic silhouettes and long readable legs; never use an "
    "extreme baby-head proportion. Preserve the approved v2 character-sheet silhouette first. Clean bold black outer contours, flat saturated "
    "candy colors, restrained animation-cel shading, graphic silhouettes, simple geometric backgrounds, "
    "exaggerated readable action, crisp vector-like finish. Eyes first, face second, action third; "
    "backgrounds never compete with the face. Original designs only: no franchise likenesses, logos, "
    "photorealism, anime proportions, painterly texture, 3D rendering or realistic anatomy."
)

PREVIOUS_PAGE_CONTINUITY = """OPCIÓN ACTIVADA — REFERENCIA DE PÁGINA ANTERIOR: Se adjunta la página inmediatamente anterior ya aprobada. Lee únicamente su ÚLTIMA CELDA como estado de partida para esta página: personaje presente, vestuario, accesorios, pose final, dirección de la mirada, ubicación, hora y objetos que ya existen. Conserva esos elementos sólo cuando la celda 1 de esta página los continúe. NO copies ni repitas la composición, retícula, encuadre, pose, expresión, acción, diálogo, SFX, objetos, fondo o solución visual de la página adjunta. Esta página debe ser original y resolver exclusivamente las celdas de abajo. Las instrucciones y bloqueos de esta página tienen prioridad absoluta sobre la referencia adjunta."""

VOICE_DIRECTION = """VOCES Y RITMO: El NARRADOR OMNIPRESENTE aparece en cartelas breves, poéticas y concretas; da contexto sin explicar lo obvio. HASSAN habla y piensa como un hombre adulto que observa, duda y decide mientras intenta entender lo que siente. Usa español mexicano claro, cotidiano e íntimo: cada frase expresa un hecho, una pregunta, una decisión o un cariño específico. Evita metáforas vagas, frases de autoayuda, solemnidad y palabras que no diría en una conversación real. Sus reflexiones internas usan nube de pensamiento y suelen tener 6–18 palabras. FERRY habla como una adulta Gen Z cálida, segura, juguetona y espontánea: lenguaje actual ligero, afectuoso y claro, sin saturar de slang ni convertirla en caricatura. Alternar diálogo, pensamiento, cartela y silencio para que la página respire."""

POSE_ANATOMY_RULES = """POSE Y ANATOMÍA (OBLIGATORIO): Cada adulto semi-chibi conserva anatomía humana clara y natural: exactamente dos brazos, dos piernas, dos manos y una cabeza; hombros, codos y muñecas siguen una dirección posible, sin torsiones imposibles. Conserva la silueta madura, piernas largas y cabeza no extrema de la hoja v2. Cuando se vea una mano, dibuja cinco dedos separados y legibles, proporcionados al estilo semi-chibi. Cada celda tiene un solo gesto principal, con peso corporal, línea de hombros, pelvis y punto de apoyo comprensibles. La mano que usa un objeto debe sujetarlo o tocarlo de forma natural; el otro brazo tiene una posición visible y relajada. Prioriza plano medio o tres cuartos cuando el gesto de brazos y manos sea importante."""

NEGATIVE_ANATOMY_PROMPT = """PROMPT NEGATIVO — EVITAR ESTRICTAMENTE: dedos extra, dedos faltantes, dedos fusionados, manos deformes, manos duplicadas, brazos extra, piernas extra, miembros ausentes, muñecas rotas, codos invertidos, hombros dislocados, articulaciones dobladas en dirección imposible, brazos atravesando torso u objetos, extremidades cortadas accidentalmente, manos escondidas sin motivo, postura retorcida, perspectiva anatómica imposible, pose rígida de maniquí, cuerpo flotando sin apoyo, objetos atravesando manos, caras duplicadas, ojos desalineados, cabeza infantil desproporcionadamente enorme, proporción de bebé, anatomía realista o cuerpo infantil."""

CHARACTER_SHEET_AUTHORITY = """HOJAS DE PERSONAJE V2 — AUTORIDAD VISUAL PRIMARIA: Las hojas adjuntas de Ferry y Hassan son la fuente de verdad para su identidad física, silueta, peinado, rostro, ojos, paleta, vestuario base y accesorios. No las contradigas con resúmenes heredados. Ferry es adulta, de piel cálida, atlética y de silueta madura semi-chibi; tiene cabello largo ondulado castaño con mechas doradas, cejas oscuras y ojos café oscuro, profundos y expresivos (nunca azules, cian, rosa, magenta, verdes ni de otro color). Su look firma es vestido coral plisado, chaqueta blanca corta, cinturón dorado y tenis blanco-oro; la concha es un dije dorado, y el moño coral y el cordón rojo son accesorios que sólo aparecen si el beat los nombra. Hassan es adulto, de piel cálida, sensible y meticuloso; tiene cabello corto oscuro, cejas oscuras, barba completa cuidada y ojos café oscuro, profundos y expresivos (nunca azules, cian, rosa, magenta, verdes ni de otro color). Su look de laboratorio es bata blanca sobre camiseta azul marino, pantalón carbón y tenis azul marino; sus variaciones aprobadas son sobrecamisa índigo, chaqueta azul de campo y traje azul noche. Matraz, libreta azul de trabajo, libro rosa personal “Volver a mí” de Ferry Beltran, lupa de latón, audífonos negros, lente de microscopio, carrete de hilo rojo y estrella sólo aparecen cuando la cronología y el beat lo permitan. La celda actual gobierna utilería, acción y vestuario específico de escena; nunca modifica la identidad física definida por la hoja v2."""

CREATURE_IDENTITY_HEADING = "BIBLIA DE IDENTIDAD DE CRIATURAS — AUTORIDAD OBLIGATORIA"

CREATURE_SPECS = {
    "zeus": "Zeus — ROTTWEILER adulto negro y fuego: pelo corto negro, marcas fuego nítidas en cejas, hocico, pecho y patas, cabeza ancha/cuadrada, hocico fuerte, cuerpo musculoso y orejas triangulares naturales caídas; nunca golden retriever, labrador, perro dorado/crema, pelo largo ni perro genérico",
    "yohi": "Yohi — TORTUGA SULCATA BEBÉ (africana de espolones), terrestre: caparazón alto color arena con escudos definidos y patas gruesas escamosas; nunca tortuga acuática, tortuga de orejas rojas, galápago ni reptil genérico",
    "caracoles": "exactamente DOS CARACOLES TERRESTRES pequeños: cada uno con cuerpo húmedo gris, UNA concha espiral marrón/ámbar y cuatro tentáculos finos; nunca tortugas, babosas sin concha, insectos ni un número distinto de dos",
    "arana": "UNA ARAÑA TEJEDORA pequeña: abdomen ovalado y exactamente OCHO patas articuladas; nunca mariposa, escarabajo, insecto de seis patas ni criatura con más/menos de ocho patas",
}

CREATURE_NEGATIVES = {
    "zeus": "nunca golden retriever, labrador, perro dorado/crema, perro de pelo largo, cachorro genérico ni raza mixta",
    "yohi": "nunca tortuga acuática, tortuga de orejas rojas, galápago, reptil genérico ni caparazón liso",
    "caracoles": "nunca tortugas, babosas sin concha, insectos ni un número distinto de dos",
    "arana": "nunca mariposa, escarabajo, insecto de seis patas ni criatura de más/menos de ocho patas",
}

CREATURE_GUIDE_LABELS = {
    "zeus": "ZEUS — ROTTWEILER negro y fuego",
    "yohi": "YOHI — TORTUGA SULCATA bebé",
    "caracoles": "DOS CARACOLES TERRESTRES",
    "arana": "UNA ARAÑA TEJEDORA — 8 PATAS",
}

# Algunas acciones eliden al animal porque la página ya lo estableció. Este mapa
# evita que esa elipsis borre su identidad en el prompt de la celda.
CREATURE_CELL_OVERRIDES = {
    **{(16, cell): ("zeus",) for cell in range(1, 4)},
    **{(17, cell): ("zeus",) for cell in range(1, 4)},
    **{(18, cell): ("zeus",) for cell in range(1, 3)},
    (19, 3): ("zeus",),
    (20, 2): ("yohi",), (20, 3): ("yohi",),
    (21, 1): ("yohi",), (21, 2): ("yohi",),
    (22, 1): ("yohi",), (22, 2): ("yohi",),
    **{(23, cell): ("yohi",) for cell in range(1, 3)},
    **{(24, cell): ("caracoles",) for cell in range(1, 4)},
    **{(25, cell): ("caracoles",) for cell in range(1, 3)},
    **{(26, cell): ("arana",) for cell in range(1, 4)},
    (27, 1): ("arana",),
    (28, 1): ("zeus",), (28, 2): ("yohi",), (28, 3): ("caracoles",), (28, 4): ("arana",),
    (69, 2): ("zeus", "yohi", "caracoles", "arana"),
    (85, 2): ("zeus", "yohi", "caracoles", "arana"),
}

TIMELINE_RULE = """BLOQUEO DE CRONOLOGÍA: El estado canónico de esta página no autoriza objetos nuevos. Un prop, motivo o cambio de estado sólo puede aparecer si esta página y celda lo introducen explícitamente. No añadas como decoración presagios, accesorios, hilos, carretes, notas, llaves, lupas, conchas, estrellas o magia de una escena futura."""

# Estados con transición dentro de una misma celda. Se añaden al arte y al plan;
# no se dejan a la interpretación del modelo a partir de la página previa.
CELL_STATE_LOCKS = {
    (1, 1): "Fachada puramente realista nocturna: sin hilo rojo, carrete, nota, lupa, llave, concha, estrella ni destello mágico.",
    (1, 2): "El monitor de la derecha está ENCENDIDO y muestra gráficos abstractos azules. No hay hilo rojo, carrete, nota, lupa, llave, concha, estrella ni props mágicos.",
    (1, 3): "El matraz está completamente vacío y transparente. El único indicio permitido es un punto rosa-dorado microscópico de reflexión; NO dibujes hilo, curva roja, carrete, llave, estrella con puntas, nota ni emisión de magia.",
    (2, 1): "El mismo monitor está todavía ENCENDIDO y muestra gráficos abstractos azules. No hay hilo rojo, carrete, nota, lupa, llave, concha, estrella ni props mágicos.",
    (2, 2): "El mismo monitor inicia esta celda ENCENDIDO. Hassan pulsa su botón y sólo en esta celda pasa a pantalla negra/apagada; no adelantes ningún objeto de la receta.",
    (2, 3): "El mismo monitor ya está APAGADO con pantalla negra. No hay hilo rojo, carrete, nota, lupa, llave, concha, estrella ni props mágicos.",
    (3, 1): "Sólo el libro personal cerrado de Hassan: portada rosa intenso con texto perfectamente legible “Volver a mí” y debajo “Ferry Beltran”; sin diagramas, carrete, hilo rojo, estrella, llave, nota, lupa ni props futuros. Sus manos lo cierran de forma natural.",
    (3, 2): "Hassan está de pie en perfil de tres cuartos junto a la lámpara. Con un solo brazo relajado junto al torso, extiende el otro de forma natural: codo ligeramente flexionado y una mano de cinco dedos toca el interruptor. Ambos hombros, muñecas y codos son visibles, proporcionados y no se cruzan; sin props futuros.",
}

# Estas celdas contienen el único texto diegético permitido fuera de globos,
# cartelas y SFX: la portada recurrente del libro personal de Hassan.
BOOK_COVER_CELLS = {(3, 1), (4, 1), (5, 2), (6, 4), (7, 1), (8, 1), (82, 3)}
BOOK_COVER_TEXT = '"Volver a mí" — "Ferry Beltran"'

GUIDE_README = """# Prompts de storyboard anotado — 90 páginas

Cada archivo es un **prompt de imagen auxiliar** para generar una lámina de storyboard anotado antes de la página final. La lámina simula la retícula final, pero se dibuja como sketch técnico sobre papel: construcción en grafito/azul, flechas de mirada, movimiento y luz, líneas de fuga, iconos de props y siluetas vacías de lettering. No es arte acabado, no contiene diálogo literal y no autoriza añadir elementos fuera de los declarados.

## Uso

1. Generar primero la lámina guía con la retícula y las celdas exactas que declara su archivo.
2. Pasar la lámina guía al orquestador junto con el prompt final correspondiente; no sustituye las hojas de personaje v2.
3. Comprobar identidad, vestuario, accesorios, lugar, hora, objeto en mano, postura, mirada, fuente de luz y eje de cámara antes de generar arte final. Si aparece un animal, comprobar además su placa `ESPECIE/RAZA`: Zeus = Rottweiler negro y fuego; Yohi = tortuga sulcata bebé; dos caracoles terrestres; una araña tejedora de ocho patas.
4. Revisar el bloque `SALIDA` antes de aprobar: debe dejar el estado que iniciará la página siguiente.

Las hojas de personaje v2 son la autoridad visual primaria. El texto literal entre comillas dobles debe aparecer únicamente donde la guía lo declara.
"""

CELL_CAMERA_OVERRIDES = {
    (3, 2): "plano medio en tres cuartos: torso completo, ambos hombros, codos, muñecas y la lámpara visibles para comprobar una pose natural",
}

# Energías de arquetipo: siempre originales. Se describen como vestuario/actitud
# de Ferry, nunca como retrato, nombre o copia de la figura evocada.
INGREDIENT_CAMEOS = {
    (66, 1): "Ferry aparece al fondo como una heroína lectora original, con capa dorada-rosa y una rosa cristalina; energía de honestidad, sin parecerse a personaje existente.",
    (66, 3): "Ferry aparece como una heroína humanitaria original de blanco y azul suave, gesto compasivo y manos abiertas; energía de empatía, no retrato de persona real.",
    (67, 1): "Ferry aparece como investigadora pionera original, bata azul, vial luminoso y mirada curiosa; energía científica sin copiar a ninguna figura histórica.",
    (67, 3): "Ferry aparece como detective juvenil original, falda coral, abrigo corto y lupa plateada; energía investigadora sin vestuario reconocible.",
    (68, 1): "Ferry aparece como vigilante felina original de negro, rosa y oro, sonrisa segura y máscara abstracta no reconocible; energía de sensualidad natural.",
    (68, 3): "Ferry aparece como estrella pop original de escenario, capa carmesí geométrica y micrófono-linterna; energía de pasión sin imitar a una cantante real.",
    (69, 1): "Ferry aparece como guardiana de hogar original, chal rojo cálido, nido y huellas protegidas; energía maternal sin copiar personajes.",
    (69, 3): "Ferry aparece como guerrera de verdad original, armadura blanca y oro con escudo circular abstracto; energía valiente sin iconografía de franquicia.",
    (70, 1): "Ferry aparece como empresaria pop original, chaqueta miel, libreta de planes y engranes luminosos; energía de trabajo y emprendimiento.",
    (70, 3): "Ferry aparece como maga de esperanza original, vestido rosa de líneas simples y estrella flotante propia; energía luminosa sin copiar una bruja conocida.",
    (71, 1): "Ferry aparece como soñadora romántica original, vestido verde-rosa y flor en la mano; energía de inocencia curiosa, sin retrato cinematográfico.",
    (71, 3): "Ferry aparece como princesa marina original, capa turquesa, concha dorada y cabello movido por agua gráfica; energía oceánica sin cola ni diseño reconocible.",
    (72, 1): "Ferry aparece como guerrera resiliente original en rojo coral, raíz luminosa y postura firme; energía de perseverancia sin copiar heroínas existentes.",
    (72, 3): "Ferry aparece como chef heroína original, delantal coral, cuchara brillante y remolino de especias; energía culinaria sin uniforme reconocible.",
    (72, 5): "Ferry aparece como arquitecta del orden original, uniforme blanco-cian, prisma y gestos precisos; energía de armonía sin retrato de figura pública.",
    (73, 1): "Ferry aparece como aventurera solar original, vestido lavanda-oro, campanillas y sonrisa radiante; energía de alegría sin copiar princesas.",
    (73, 3): "Ferry aparece como escuchadora serena original, atuendo arena-azul y reloj de arena; energía paciente, paisaje minimalista de viento y agua.",
    (73, 5): "Ferry aparece como icono de cariño original, moño coral propio y manta blanca envolvente; energía de refugio, sin rasgos de personaje conocido.",
    (74, 1): "Ferry aparece como mensajera romántica original, capa vino-rosa y sobres perfumados; energía de amor escrito sin aludir a personajes literarios.",
    (74, 3): "Ferry aparece como constructora de puentes familiar original, vestido bordado coral y pétalos; energía de comprensión sin copiar personajes de cine.",
    (74, 5): "Ferry aparece como aventurera caótica original, mechón coral, chaqueta negra-rosa y chispa naranja; energía atrevida sin iconografía de antihéroes conocidos.",
    (75, 1): "Ferry aparece como atleta campeona original, uniforme coral-oro sin logos, pose de salto y trofeo abstracto; energía de fortaleza.",
    (75, 3): "Ferry aparece como guía de nutrición original, túnica verde-dorada, cáliz y gesto protector; energía que nutre cuerpo y esperanza.",
    (75, 5): "Ferry aparece como estudiosa confiable original, abrigo índigo, llave dorada y libro cerrado sin símbolos reconocibles; energía de confianza.",
    (76, 1): "Ferry aparece como viajera fiel original, anillo sobrio, abrigo marfil y mirada tranquila; energía de lealtad libre.",
    (76, 3): "Ferry aparece como heroína cósmica original, uniforme blanco-coral, hilo rojo orbital y estrella propia; energía de conexión eterna sin copiar diseños existentes.",
    (76, 5): "Ferry aparece como estrella pop coqueta original, moño rosa satinado, borde coral luminoso y pose segura; energía dulce y ardiente.",
    (77, 1): "Ferry aparece como exploradora lunar original, vestido violeta suave, luciérnagas y mirada curiosa; energía de preguntas inesperadas.",
    (77, 4): "Ferry aparece como creadora original, overol coral con manchas abstractas de pintura y pincel rosa-dorado; no evoca a una figura externa.",
}

# Una entrada por página y una instrucción de texto por celda.  SILENCIO es una
# elección consciente: no se permite que el modelo invente letras para llenarlo.
TEXT_TRACKS = [
    ["CARTELA: «9 de septiembre 2026. Una noche más...»", "GLOBO DE HASSAN: «Una última medición y ya. Necesito terminar por hoy.»", "SFX: «bip»"],
    ["GLOBO DE HASSAN: «Ya quedó. Lo demás puede esperar hasta mañana.»", "SFX: «clic»", "CARTELA: «Por hoy, basta.»"],
    ["GLOBO DE HASSAN: «Mañana sigo. Ahora necesito dormir un rato.»", "SFX: «clac»"],
    ["GLOBO DE HASSAN: «A esta hora el laboratorio se siente más grande.»", "GLOBO DE HASSAN: «Ya me voy. Sólo quiero llegar, bañarme y dormir.»", "CARTELA: «El laboratorio guarda el silencio.»"],
    ["GLOBO DE HASSAN: «Una copa y ya. Necesito bajarle un poco.»", "SFX: «clin»", "GLOBO DE HASSAN: «Pongo música. A ver si dejo de pensar.»"],
    ["GLOBO DE HASSAN: «La música está bien...»", "SFX: «mmmm»", "GLOBO DE HASSAN: «No tengo que resolver todo hoy.»", "CARTELA: «Respira.»"],
    ["GLOBO DE HASSAN: «Respira. Hoy hiciste lo que pudiste.»", "SFX: «hummm»", "GLOBO DE HASSAN: «Mañana veo las cosas con más calma.»"],
    ["CARTELA: «El sueño toma aire.»", "SFX: «hummm»"],
    ["SFX: «shhh»", "SFX: «tinnn»", "GLOBO DE HASSAN: «Esto no se siente como los otros sueños.»"],
    ["SFX: «whooosh»", "GLOBO DE HASSAN: «Si estoy soñando, prefiero no despertar todavía.»"],
    ["SFX: «ta-dá»", "SFX: «aplausos lejanos»", "GLOBO DE HASSAN: «¿Qué lugar es este? Siento que ya lo conozco.»"],
    ["SFX: «tap»", "SFX: «fwoosh»", "CARTELA: «Una luz toma forma.»"],
    ["SFX: «FWOOSH»", "SFX: «vrrr»", "GLOBO DE HASSAN: «Ferry… hasta dormido sigo pensando en ti.»", "SFX: «TÁ!»"],
    ["CARTELA: «La chica de sus sueños.»", "GLOBO DE FERRY: «Holi, Hassan. Llegaste justo a tiempo.»", "SFX: «tinnn»"],
    ["GLOBO DE FERRY: «Ven, te enseño el lugar donde cuido lo que amo.»", "GLOBO DE HASSAN: «Voy contigo. No sé a dónde, pero voy.»"],
    ["GLOBO DE FERRY: «Zeus.»", "GLOBO DE FERRY: «Todo bien, mi Pakito. Estoy aquí contigo.»", "SFX: «wuf»"],
    ["SFX: «thump»", "GLOBO DE FERRY: «Buen chico. Ya sabía que podías confiar en mí.»", "SFX: «tinnn»"],
    ["GLOBO DE FERRY: «Déjame ver. No quiero que te duela ni un poquito.»", "SFX: «zap»"],
    ["SFX: «plop»", "GLOBO DE FERRY: «Aquí estás. No te me escondas solito.»", "SFX: «fiuu»"],
    ["GLOBO DE FERRY: «Buenos días, Yohi. ¿Listo para tu hoja favorita?»", "SFX: «crisp»", "SILENCIO"],
    ["SFX: «toc… toc…»", "GLOBO DE FERRY: «Sin prisa. Tú marcas el paso.»"],
    ["SFX: «ñam»", "GLOBO DE FERRY: «Todo a tu tiempo. Aquí nadie tiene que correr.»", "GLOBO DE HASSAN: «Tienes una paciencia que yo todavía estoy aprendiendo a tener.»"],
    ["GLOBO DE FERRY: «Tu casa está lista. Ven, mira lo que hice.»", "SFX: «tinnn»"],
    ["SFX: «slip»", "GLOBO DE FERRY: «Cuidado. Vamos a cruzar sin lastimarnos.»", "SFX: «tap»"],
    ["SFX: «slip… slip…»", "CARTELA: «Un camino seguro.»"],
    ["SFX: «frrr»", "GLOBO DE FERRY: «Ey, tranqui. Ya pasó. Estoy contigo.»", "SFX: «tinnn»"],
    ["SFX: «tac tac»", "GLOBO DE HASSAN: «Tú sí te fijas en todo, hasta en lo que nadie ve.»"],
    ["SILENCIO", "SILENCIO", "SILENCIO", "CARTELA: «Cuidar también es un poder.»"],
    ["GLOBO DE FERRY: «Hassan.»", "GLOBO DE FERRY: «Qué bueno que llegaste hasta aquí.»", "GLOBO DE HASSAN: «No quiero despertar. Aquí todo se siente demasiado real.»"],
    ["SFX: «tinnn»", "GLOBO DE FERRY: «Ven, sígueme. Te falta ver una cosa.»"],
    ["SFX: «fwoosh»", "GLOBO DE HASSAN: «¡Ferry, espera! Quiero preguntarte algo.»", "SFX: «tinnn»"],
    ["SFX: «flap»", "CARTELA: «Una lista imposible.»", "SFX: «fiuu»"],
    ["SFX: «whoop»", "SFX: «tap»"],
    ["GLOBO DE HASSAN: «No entiendo la lista, pero siento que importa.»", "CARTELA: «Cristal. Nube. Estrella.»", "GLOBO DE HASSAN: «No sé qué es esto, pero voy a buscarlo.»"],
    ["CARTELA: «Y el sueño se cerró.»", "SFX: «shhh…»"],
    ["SFX: «gasp»", "GLOBO DE HASSAN: «Fue un sueño, pero no se me va de la cabeza.»", "SFX: «tinnn»"],
    ["SFX: «clic»", "GLOBO DE HASSAN: «¿Qué es esto? ¿Por qué me da tanta mala espina?»"],
    ["SFX: «tap»", "SFX: «tac»", "CARTELA: «La mañana ya no es igual.»"],
    ["SFX: «grrr»", "SFX: «blup»", "SFX: «pssshh»"],
    ["GLOBO DE HASSAN: «Eso rojo no estaba aquí ayer.»", "SFX: «tinnn»", "GLOBO DE HASSAN: «La nota… entonces no lo imaginé.»"],
    ["SFX: «peel»", "GLOBO DE HASSAN: «Es real. Todavía no sé cómo explicarlo.»"],
    ["GLOBO DE HASSAN: «Antes de hacerme historias, voy a revisarlo bien.»", "SFX: «tap»", "GLOBO DE HASSAN: «Voy al laboratorio. Ahí por lo menos puedo empezar.»"],
    ["GLOBO DE HASSAN: «Necesito ver esto con calma y sin inventar nada.»", "SFX: «swish»", "CARTELA: «Una pregunta merece método.»"],
    ["SFX: «zoom»", "CARTELA: «Sinceridad.»", "GLOBO DE HASSAN: «Primero: sinceridad. A ver qué me pide esta nota.»"],
    ["CARTELA: «Empatía.»", "CARTELA: «Inteligencia.»", "CARTELA: «Curiosidad.»", "GLOBO DE HASSAN: «¿Una receta de Ferry? Esto tiene que querer decir algo.»"],
    ["SFX: «fwoom»", "CARTELA: «No son palabras. Son pistas.»", "GLOBO DE HASSAN: «No son palabras al azar. Me están dejando pistas.»"],
    ["GLOBO DE HASSAN: «Cocina, sala, patio. Voy a revisar todo.»", "SFX: «tinnn»"],
    ["SFX: «clac»", "GLOBO DE HASSAN: «Empiezo por aquí. Algo de esto tiene que tener sentido.»", "SFX: «fiuu»"],
    ["SFX: «crash»", "GLOBO DE HASSAN: «No, no, no… bueno. Tal vez sí sirve.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «Ya empecé. Ahora quiero saber a dónde lleva esto.»", "SFX: «tinnn»"],
    ["CARTELA: «Talento que da calor.»", "SFX: «fwoom»", "GLOBO DE HASSAN: «Canela. Contigo hasta lo simple se siente especial.»"],
    ["SFX: «rustle»", "GLOBO DE HASSAN: «Vainilla. Suave, pero de las que se quedan.»", "SFX: «tinnn»"],
    ["SFX: «tinnn»", "GLOBO DE HASSAN: «Una cuchara. No parece importante, pero aquí está.»"],
    ["SFX: «scrape»", "GLOBO DE HASSAN: «¿Una moneda? Todo esto está más raro de lo que pensé.»", "SFX: «vrrr»"],
    ["GLOBO DE HASSAN: «Trabajo y paciencia. Así se hacen las cosas, supongo.»", "SFX: «clic clic»"],
    ["SFX: «fiuu»", "GLOBO DE HASSAN: «El hilo otra vez. Esto ya no puede ser coincidencia.»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «Una concha. ¿Por qué siento que ya la conozco?»", "SFX: «swish»", "CARTELA: «Una gota de horizonte.»"],
    ["SFX: «scrape»", "GLOBO DE HASSAN: «Resistir y volver a crecer. Eso sí te lo admiro.»", "SFX: «crack»"],
    ["GLOBO DE HASSAN: «Cariño que abriga. Sí, esa parte es muy tuya.»", "SFX: «poof»"],
    ["SFX: «clink»", "GLOBO DE HASSAN: «Confianza. Esa sí cuesta ganársela.»", "SFX: «tinnn»"],
    ["SFX: «poof»", "GLOBO DE HASSAN: «Tranquila, nube. No tengo que entenderte hoy.»", "SFX: «pop»"],
    ["SFX: «clink»", "SFX: «fiuu»", "GLOBO DE HASSAN: «Casi está todo. Sólo falta saber qué significa.»"],
    ["GLOBO DE HASSAN: «Todo tiene un lugar. Esta nota también.»", "SFX: «tinnn»", "CARTELA: «La fórmula empieza a mirar de vuelta.»"],
    ["GLOBO DE HASSAN: «No es una mezcla cualquiera. Algo está por pasar.»", "SFX: «beeeep»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «Faltan cosas. Seguro las últimas son las importantes.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «1. Cristales de sinceridad.»", "GLOBO DE HASSAN: «No esconder lo que siento. Esa parte me cuesta.»", "GLOBO DE HASSAN: «2. Nube tibia de empatía.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «3. Frasco de luz científica.»", "GLOBO DE HASSAN: «Entender para cuidar. Contigo todo se ve más claro.»", "GLOBO DE HASSAN: «4. Lupa de luna curiosa.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «5. Polvo de sonrisa encantada.»", "GLOBO DE HASSAN: «Cuando sonríes, se me cambia el día.»", "GLOBO DE HASSAN: «6. Llama de leona roja.»", "SFX: «fwoosh»"],
    ["GLOBO DE HASSAN: «7. Nido de ternura.»", "GLOBO DE HASSAN: «Siempre estás pendiente de todos. Eso no se te quita.»", "GLOBO DE HASSAN: «8. Escudo de oro valiente.»", "SFX: «clang»"],
    ["GLOBO DE HASSAN: «9. Monedas de miel y engranes.»", "GLOBO DE HASSAN: «Con cuidado. No quiero echar a perder nada.»", "GLOBO DE HASSAN: «10. Estrella de esperanza infinita.»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «11. Flor de inocencia.»", "GLOBO DE HASSAN: «A veces una cosa pequeña cambia todo.»", "GLOBO DE HASSAN: «12. Concha dorada del mar.»", "SFX: «swish»"],
    ["GLOBO DE HASSAN: «13. Raíz de perseverancia.»", "GLOBO DE HASSAN: «Sigues aunque estés cansada. Eso admiro de ti.»", "GLOBO DE HASSAN: «14. Cuchara de canela y vainilla.»", "GLOBO DE HASSAN: «Tu talento hace que hasta lo diario se sienta bonito.»", "GLOBO DE HASSAN: «15. Cristal de orden.»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «16. Campanillas de sol.»", "GLOBO DE HASSAN: «Cuando llegas contenta, se me contagia la alegría.»", "GLOBO DE HASSAN: «17. Reloj de arena sereno.»", "GLOBO DE HASSAN: «Esperar sin presionar también es querer.»", "GLOBO DE HASSAN: «18. Manta de algodón de cariño.»", "SFX: «poof»"],
    ["GLOBO DE HASSAN: «19. Sobres perfumados de amor.»", "GLOBO DE HASSAN: «Tus mensajes hacen que te sienta más cerca.»", "GLOBO DE HASSAN: «20. Puente de pétalos.»", "GLOBO DE HASSAN: «Hablar contigo aclara muchas cosas.»", "GLOBO DE HASSAN: «21. Chispa salvaje.»", "SFX: «zap»"],
    ["GLOBO DE HASSAN: «22. Trofeo de cuerpo en movimiento.»", "GLOBO DE HASSAN: «Tu fuerza se nota, aunque no hagas ruido.»", "GLOBO DE HASSAN: «23. Cáliz de nutrición sagrada.»", "GLOBO DE HASSAN: «Cuidar a alguien todos los días también es amor.»", "GLOBO DE HASSAN: «24. Llave de confianza.»", "SFX: «clic»"],
    ["GLOBO DE HASSAN: «25. Anillo de fidelidad.»", "GLOBO DE HASSAN: «Quedarse porque quieres, no porque tienes que hacerlo.»", "GLOBO DE HASSAN: «26. Hilo rojo del destino.»", "GLOBO DE HASSAN: «Este hilo siempre termina llevándome a ti.»", "GLOBO DE HASSAN: «27. Moño rosa con fuego.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «28. Luciérnagas de madrugada.»", "GLOBO DE HASSAN: «Siempre estás preguntando cosas. Por eso contigo nunca me aburro.»", "SFX: «tinnn»", "GLOBO DE HASSAN: «29. Pincel de creatividad infinita.»", "SFX: «shraaa»"],
    ["CARTELA: «Veintinueve razones.»", "GLOBO DE HASSAN: «Todas hablan de ti. Ninguna te pide que seas otra persona.»", "GLOBO DE HASSAN: «Quiero que estés porque quieres estar, no por esta fórmula.»", "SFX: «fwoom»"],
    ["SFX: «clic»", "CARTELA: «La receta ya no necesita palabras.»", "SFX: «fiuu»", "GLOBO DE HASSAN: «Ahora sí. Voy a hacerlo bien y con cuidado.»"],
    ["SFX: «KRAK»", "GLOBO DE HASSAN: «Si algo va a pasar, ya están listas las piezas.»", "SFX: «FWOOM»"],
    ["SFX: «vrrr»", "SFX: «tinnn»", "GLOBO DE HASSAN: «Está funcionando… y no sé si eso me da gusto o miedo.»", "SFX: «shraaa»"],
    ["GLOBO DE HASSAN: «Despacio. No quiero arruinarlo por irme de golpe.»", "CARTELA: «El sueño también tiene memoria.»", "GLOBO DE HASSAN: «La magia también necesita que uno haga las cosas bien.»"],
    ["SFX: «vrrr»", "GLOBO DE HASSAN: «Todavía puedo parar. Pero necesito ver qué es esto.»", "SFX: «crack»"],
    ["SFX: «tinnn»", "SFX: «FWOOM»", "CARTELA: «Una estrella aprende a nacer.»"],
    ["GLOBO DE HASSAN: «Ferry… te vi en sueños. Y ahora estás aquí.»", "CARTELA: «Todas sus luces estaban ahí.»"],
    ["SFX: «shraaa»", "SFX: «tinnn»", "GLOBO DE HASSAN: «No te inventé. Sólo te estaba buscando.»"],
    ["SFX: «tap»", "GLOBO DE FERRY: «Llegué. ¿Ves? Nunca estuve tan lejos.»", "SILENCIO"],
    ["GLOBO DE FERRY: «¿Nos vamos?»", "GLOBO DE FERRY: «Al mar, obvio. Quiero enseñarte algo.»", "GLOBO DE HASSAN: «Juntos. Sin prisa y sin complicarnos la vida.»"],
    ["SFX: «swish»", "SFX: «clic»", "SFX: «clac»", "SFX: «vrrum»", "CARTELA: «Hacia la costa.»"],
    ["SFX: «shhh»", "GLOBO DE HASSAN: «La concha… entonces el mar también era parte de esto.»", "CARTELA: «10 de septiembre 2026 -Happy Bday my Love.»"],
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


def continuity_asset_applies(asset: dict[str, object], page_number: int) -> bool:
    rules = asset.get("pages", {})
    if not isinstance(rules, dict):
        raise ValueError(f"Invalid pages declaration for continuity asset {asset.get('id')!r}")
    if rules.get("from_plan_references"):
        return asset.get("id") in references(page_number)
    values = rules.get("values", [])
    ranges = rules.get("ranges", [])
    return page_number in values or any(start <= page_number <= end for start, end in ranges)


def continuity_reference_manifest(page_number: int) -> str:
    """Declare every sheet planned for a page inside its source prompt."""
    index = json.loads(CONTINUITY_INDEX.read_text(encoding="utf-8"))
    assets = [
        asset for asset in index.get("assets", [])
        if continuity_asset_applies(asset, page_number)
    ]
    if not assets:
        raise ValueError(f"Page {page_number:02d} has no continuity reference assets")
    lines = [
        "REFERENCIAS DECLARADAS PARA ESTA PÁGINA — ARCHIVOS DE EJECUCIÓN:",
        "El ejecutor debe adjuntar las fichas aprobadas listadas abajo. Las fichas con estado `candidate` son referencias previstas y sólo se adjuntan con --include-candidate-continuity-assets hasta que una revisión humana las promueva. Úsalas para identidad o lugar, nunca para copiar su composición, poses ni paneles.",
    ]
    for asset in assets:
        lines.append(
            f"- [{asset['status']}; {asset['kind']}] {asset['id']} ({asset['path']}): {asset['description']}"
        )
    return "\n".join(lines)


def page_state_lock(page: int) -> str:
    """Return the phase-level inventory rules that avoid future-prop leakage."""
    rules = [TIMELINE_RULE]
    if 1 <= page <= 6:
        rules.append(
            "REALIDAD INICIAL: no existe hilo rojo, carrete, nota, lupa, llave, concha ni estrella como objeto; el laboratorio es frío y no emite magia."
        )
    elif page in (7, 8):
        rules.append(
            "ANTES DEL SUEÑO: no existe hilo rojo, carrete, nota, lupa, llave ni concha. Sólo se permiten las ondas binaurales y la minúscula partícula rosa que el beat nombre."
        )
    elif 36 <= page <= 39:
        rules.append(
            "REALIDAD AL DESPERTAR: el hilo rojo y la nota física todavía no han aparecido; no añadas carrete, lupa, llave o concha. La chispa es sólo el eco visual que el beat indique."
        )
    elif 40 <= page <= 43:
        rules.append(
            "LA NOTA FÍSICA YA EXISTE, pero el carrete, la lupa, la llave y la concha aún no. El hilo rojo sólo puede estar unido a la nota cuando el beat lo diga."
        )
    elif 44 <= page <= 55:
        rules.append(
            "LA LUPA YA ES HERRAMIENTA DE HASSAN. El carrete rojo no existe hasta la página 56 y la concha no existe hasta la página 57; no los adelantes."
        )
    elif 56 <= page <= 63:
        rules.append(
            "EL CARRETE Y LA CONCHA existen sólo después de sus beats de hallazgo. El matraz sigue vacío: no añadas líquido, vapor mágico ni una estrella física."
        )
    elif 64 <= page <= 65:
        rules.append(
            "EL MATRAZ SIGUE VACÍO. Sólo la chispa de fondo declarada en la página 64 puede aparecer; el primer líquido nace en la página 66."
        )
    elif 66 <= page <= 83:
        rules.append(
            "CONJURO: la transformación ocurre en el matraz paso a paso. No dibujes una estrella física completa ni Ferry materializada: la estrella nace en la página 84 y Ferry llega en la 87."
        )
    return " ".join(rules)


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


def creature_names_for_cell(page_number: int, cell_number: int, action: str) -> tuple[str, ...]:
    """Resolve the exact creature(s) that must retain identity in one cell."""
    lowered = action.lower()
    names = list(CREATURE_CELL_OVERRIDES.get((page_number, cell_number), ()))
    detected = (
        ("zeus", ("zeus", "rottweiler")),
        ("yohi", ("yohi", "tortuga", "sulcata")),
        ("caracoles", ("caracol",)),
        ("arana", ("araña", "telaraña")),
    )
    for name, markers in detected:
        if any(marker in lowered for marker in markers):
            names.append(name)
    return tuple(dict.fromkeys(names))


def creature_lock_for(page_number: int, cell_number: int, action: str) -> str:
    """Return a cell-local, explicit species/breed contract for art and guides."""
    names = creature_names_for_cell(page_number, cell_number, action)
    if not names:
        return "SIN CRIATURA EN CUADRO: no introducir animales de decoración ni una silueta animal fuera del beat."
    return "ESPECIE/RAZA BLOQUEADA PARA ESTA CELDA: " + " | ".join(CREATURE_SPECS[name] for name in names)


def creature_names_for_cells(cells: list[dict[str, str]]) -> tuple[str, ...]:
    """Return only the creatures that are actually active in this page's cells."""
    names: list[str] = []
    for cell in cells:
        action = cell["action"]
        lowered = action.lower()
        for name, marker in (
            ("zeus", "Zeus — ROTTWEILER"),
            ("yohi", "Yohi — TORTUGA SULCATA"),
            ("caracoles", "DOS CARACOLES TERRESTRES"),
            ("arana", "UNA ARAÑA TEJEDORA"),
        ):
            if marker.lower() in cell["creature_lock"].lower() or name in lowered:
                names.append(name)
    return tuple(dict.fromkeys(names))


def creature_bible_for_cells(cells: list[dict[str, str]]) -> str:
    names = creature_names_for_cells(cells)
    if not names:
        return f"{CREATURE_IDENTITY_HEADING}: esta página no tiene animales en cuadro; no dibujes animales de decoración."
    species = " | ".join(CREATURE_SPECS[name] for name in names)
    return (
        f"{CREATURE_IDENTITY_HEADING}: en esta página, las ÚNICAS criaturas autorizadas son: {species}. "
        "No dibujes ninguna otra especie, mascota genérica ni animal de fondo."
    )


def negative_creature_prompt_for_cells(cells: list[dict[str, str]]) -> str:
    names = creature_names_for_cells(cells)
    if not names:
        return "PROMPT NEGATIVO — ESPECIE/RAZA: animales de decoración, siluetas animales de fondo, especie no declarada."
    return "PROMPT NEGATIVO — ESPECIE/RAZA: " + "; ".join(CREATURE_NEGATIVES[name] for name in names) + "."


def guide_creature_legend(cells: list[dict[str, str]]) -> str:
    names = creature_names_for_cells(cells)
    if not names:
        return "Esta página no tiene animal visible: no dibujes icono, silueta ni prop de criatura."
    labels = " | ".join(CREATURE_GUIDE_LABELS[name] for name in names)
    return (
        f"Placa de especie para ESTA página: {labels}. Dibuja únicamente esas criaturas en las celdas que su bloqueo individual las autoriza; "
        "no uses iconos genéricos ni introduzcas las otras criaturas de la historia."
    )


def previous_page_reference(page: dict[str, object], attach: bool) -> dict[str, object]:
    number = page["number"]
    if number == 1 or not attach:
        return {"attached": False, "instruction": ""}
    return {
        "attached": True,
        "instruction": PREVIOUS_PAGE_CONTINUITY,
        "approved_page_id": None,
        "approved_art": None,
    }


def schematic_context(page_number: int) -> dict[str, str]:
    """Return the production-continuity context that every guide must expose."""
    if page_number <= 3:
        return {
            "time": "noche del 9 de septiembre de 2026; luz blanca fría de laboratorio",
            "location": "laboratorio minimalista de Hassan, acero, blanco y azul gris",
            "wardrobe": "Hassan: bata blanca sobre camiseta azul marino, pantalón carbón y tenis azul marino",
            "cast": "Hassan adulto; no aparece Ferry",
        }
    if page_number == 4:
        return {
            "time": "noche continua, al salir del laboratorio",
            "location": "pasillo y salida del laboratorio minimalista",
            "wardrobe": "Hassan: camiseta azul marino y pantalón carbón; la bata blanca va doblada sobre un brazo",
            "cast": "Hassan adulto; no aparece Ferry",
        }
    if 5 <= page_number <= 8:
        return {
            "time": "noche profunda, antes de dormir",
            "location": "habitación minimalista de Hassan, azul gris y luz baja",
            "wardrobe": "Hassan: camiseta azul marino y pantalón carbón cómodos; sin bata ni accesorios de laboratorio",
            "cast": "Hassan adulto; no aparece Ferry",
        }
    if 9 <= page_number <= 12:
        return {
            "time": "sueño nocturno, sin hora real",
            "location": "umbral de agua y escenario onírico coral, rosa y dorado",
            "wardrobe": "Hassan: atuendo nocturno azul marino simplificado, sin bata; Ferry aún no está materializada",
            "cast": "Hassan adulto; Ferry sólo puede aparecer como luz o silueta cuando el beat lo indique",
        }
    if 13 <= page_number <= 35:
        return {
            "time": "sueño continuo, de concurso luminoso a jardín protector",
            "location": "escenario y jardín onírico coral, rosa, oro y carmín",
            "wardrobe": "Hassan: atuendo nocturno azul marino sin bata. Ferry: vestido coral plisado, chaqueta blanca corta, cinturón dorado y tenis blanco-oro; concha, moño y cordón rojo sólo si el beat los nombra",
            "cast": "Hassan adulto y Ferry adulta; no enumerar animales de la historia en este bloque: cada celda define de forma exclusiva su criatura visible mediante ESPECIE/RAZA",
        }
    if 36 <= page_number <= 37:
        return {
            "time": "amanecer del 10 de septiembre de 2026",
            "location": "habitación minimalista de Hassan, ahora azul gris de mañana",
            "wardrobe": "Hassan: el mismo atuendo cómodo azul marino y carbón; sin bata",
            "cast": "Hassan adulto; Ferry no aparece físicamente",
        }
    if 38 <= page_number <= 42:
        return {
            "time": "mañana del 10 de septiembre de 2026",
            "location": "pasillo, cocina minimalista y umbral hacia el laboratorio",
            "wardrobe": "Hassan: bata ligera sobre camiseta azul marino y pantalón carbón; la nota sólo existe físicamente desde la página 40",
            "cast": "Hassan adulto; Ferry no aparece físicamente",
        }
    if 43 <= page_number <= 46:
        return {
            "time": "mañana continua, investigación inicial",
            "location": "laboratorio minimalista, mesa de trabajo limpia y lámparas blancas",
            "wardrobe": "Hassan: bata blanca sobre camiseta azul marino, pantalón carbón y tenis azul marino",
            "cast": "Hassan adulto; Ferry no aparece físicamente",
        }
    if 47 <= page_number <= 63:
        return {
            "time": "mañana y mediodía del 10 de septiembre; cambios de estancia mostrados por el beat",
            "location": "cocina, sala, patio y regreso gradual al laboratorio de Hassan",
            "wardrobe": "Hassan: camiseta azul marino, sobrecamisa índigo o bata sólo cuando regresa al laboratorio; conservar el look que la celda declare",
            "cast": "Hassan adulto; Ferry sólo puede aparecer en una evocación declarada por el beat, nunca físicamente",
        }
    if 64 <= page_number <= 83:
        return {
            "time": "tarde que avanza a noche del 10 de septiembre",
            "location": "laboratorio minimalista que cambia gradualmente por el conjuro",
            "wardrobe": "Hassan: bata blanca sobre azul marino y carbón. Ferry sólo existe como evocación arquetípica de ingrediente en 66–77, jamás como llegada física",
            "cast": "Hassan adulto; Ferry evocada sólo donde el beat lo indica",
        }
    if 84 <= page_number <= 88:
        return {
            "time": "noche mágica del 10 de septiembre",
            "location": "laboratorio transformado por rosa, coral y oro",
            "wardrobe": "Hassan conserva bata blanca/azul marino. Ferry, desde la 87: vestido coral plisado, chaqueta blanca corta, cinturón dorado y tenis blanco-oro",
            "cast": "Hassan adulto; Ferry se vuelve físicamente presente sólo desde la página 87 y conserva autonomía total",
        }
    return {
        "time": "amanecer y mañana del 10 de septiembre de 2026",
        "location": "salida del laboratorio, coche y playa abierta",
        "wardrobe": "Hassan: traje azul noche o chaqueta azul de campo. Ferry: look firma coral, blanco y oro",
        "cast": "Hassan adulto y Ferry adulta, juntos por elección propia",
    }


def guide_text(cell: dict[str, str]) -> str:
    printed = cell["printed_text"]
    if printed == "SILENCIO":
        return "Silencio: no hay globo, cartela ni SFX."
    kind = cell["lettering_type"]
    if "Hassan" in kind:
        speaker = "Hassan — pensamiento interior" if "pensamiento" in kind else "Hassan — diálogo"
    elif "Ferry" in kind:
        speaker = "Ferry — diálogo"
    elif "narrador" in kind:
        speaker = "Narrador omnipresente — cartela"
    else:
        speaker = "SFX / efecto visual"
    extra = f"; texto de portada permitido: {cell['permitted_diegetic_text']}" if cell["permitted_diegetic_text"] else ""
    return f"{speaker}: {printed}{extra}"


def composition_role(index: int, panels: int) -> str:
    if index == 1:
        return "ancla de entrada: establece el lugar, tiempo y eje espacial"
    if index == panels:
        return "cierre: deja una dirección, objeto o emoción que sostenga el siguiente corte"
    return "desarrollo: avanza una única acción sin cambiar de lugar ni de estado sin mostrar la causa"


def pose_blueprint(action: str) -> str:
    lower = action.lower()
    if any(word in lower for word in ("duerme", "recuesta", "cama", "acost")):
        return "cuerpo apoyado de manera creíble; hombros y cadera descansan en el colchón, brazos visibles sin torsión"
    if any(word in lower for word in ("camina", "cruza", "corre", "entra", "sale", "pasos")):
        return "desplazamiento claro: un pie recibe el peso, el otro inicia el paso; torso y mirada orientados hacia el destino"
    if any(word in lower for word in ("pulsa", "toca", "ajusta", "toma", "coloca", "sujeta", "cierra", "deja")):
        return "interacción natural: brazo que trabaja con codo suavemente flexionado y muñeca posible; mano libre relajada y visible"
    if any(word in lower for word in ("mira", "observa", "contempla", "enfoca", "descubre", "sonríe")):
        return "reacción legible: hombros orientados al foco, cabeza girada sólo lo necesario y ambos brazos en reposo natural"
    if any(word in lower for word in ("detalle", "matraz", "nota", "libro", "concha", "llave", "lupa", "moneda")):
        return "plano de objeto: no inventar extremidades; si entra una mano, mostrar una sola mano de cinco dedos con agarre posible"
    return "postura adulta semi-chibi equilibrada, apoyo corporal visible, hombros y pelvis alineados, dos brazos y dos manos naturales"


def gaze_blueprint(action: str, index: int, panels: int) -> str:
    lower = action.lower()
    if "primer plano de ferry" in lower or "ferry: adulta" in lower:
        return "Ferry mira hacia Hassan fuera de cuadro, con línea de ojos cálida y clara; nunca mira a cámara por accidente"
    if "primer plano de hassan" in lower or "hassan observa" in lower:
        return "Hassan mira al objeto, persona o fenómeno que la acción declara; no usar contacto a cámara gratuito"
    focal_words = (
        ("monitor", "al monitor"), ("nota", "a la nota"), ("matraz", "al matraz"),
        ("libro", "al libro"), ("ferry", "a Ferry"), ("zeus", "a Zeus"),
        ("yohi", "a Yohi"), ("tortuga", "a la tortuga"), ("caracol", "a los caracoles"),
        ("araña", "a la araña"), ("lupa", "a la lupa"), ("estrella", "a la estrella"),
    )
    for word, focus in focal_words:
        if word in lower:
            return f"mirada dirigida {focus}; no mirar a cámara salvo que la acción lo exija"
    if "detalle" in lower or any(word in lower for word in ("fachada", "onda", "luz", "chispa")):
        return "sin mirada de personaje obligatoria; el eje visual conduce al objeto o fenómeno descrito"
    if index == panels:
        return "mirada y líneas de acción orientadas hacia la salida narrativa de la página siguiente"
    return "mirada dirigida al foco de la acción de esta celda; no usar mirada perdida ni contacto a cámara gratuito"


def continuity_dimensions(cell: dict[str, str], context: dict[str, str], panels: int) -> str:
    """State every continuity dimension that a storyboard cell must carry forward."""
    index = int(cell["cell"])
    handoff = (
        "prepara el estado que recoge la siguiente página"
        if index == panels
        else "conserva el estado visible para la siguiente celda de esta página"
    )
    return (
        f"ID: {context['cast']}; "
        f"VEST: {context['wardrobe']}; "
        f"ESPECIE/RAZA: {cell['creature_lock']}; "
        f"ESP/TIEMPO: {context['location']}, {context['time']}; "
        f"CÁMARA/ESPACIO: {cell['camera']}, {cell['placement']}; "
        f"CUERPO/MIRADA: {pose_blueprint(cell['action'])}; {gaze_blueprint(cell['action'], index, panels)}; "
        f"PROP/ESTADO: {cell['state_lock'] or 'sin prop nuevo fuera de la acción declarada'}; "
        f"RELEVO: {handoff}."
    )


def guide_for(page: dict[str, object], layout: str, cells: list[dict[str, str]], pages: list[dict[str, object]]) -> str:
    number = page["number"]
    context = schematic_context(number)
    previous_exit = "No aplica: esta página establece la realidad inicial." if number == 1 else pages[number - 2]["beats"][-1]
    next_entry = "No aplica: esta página cierra la historia." if number == 90 else pages[number]["beats"][0]
    cell_sections = []
    for cell in cells:
        cell_sections.append(
            f"### Celda {cell['cell']} — {cell['placement']}\n"
            f"- Función en lectura: {composition_role(int(cell['cell']), page['panels'])}.\n"
            f"- Entorno y hora: {context['location']}; {context['time']}.\n"
            f"- Personajes y vestuario: {context['cast']}. {context['wardrobe']}.\n"
            f"- Cámara/composición: {cell['camera']}; posición en retícula: {cell['placement']}.\n"
            f"- Anotaciones gráficas obligatorias: esquina con código C{cell['cell']}; rectángulo de encuadre, línea de horizonte, flecha de cámara, flecha de mirada, flecha de luz, línea de acción y círculo rojo alrededor de la utilería crítica.\n"
            f"- Especie/raza bloqueada: {cell['creature_lock']}\n"
            f"- Notas de continuidad por dimensión (traducir a micro-iconos/códigos en la canaleta): {continuity_dimensions(cell, context, page['panels'])}\n"
            f"- Acción y utilería exacta: {cell['action']}\n"
            f"- Pose y apoyo corporal: {pose_blueprint(cell['action'])}.\n"
            f"- Mirada/eje de atención: {gaze_blueprint(cell['action'], int(cell['cell']), page['panels'])}.\n"
            f"- Guion de voz/efecto para el prompt final (NO renderizarlo en esta guía): {guide_text(cell)}\n"
            f"- Marcador visual de lettering: dibuja sólo la silueta vacía y ubicación de {cell['lettering_placement']}; usa un código corto de celda, nunca el diálogo literal.\n"
            f"- Estado que debe respetarse: {cell['state_lock'] or 'Mantener el estado canónico de página; no introducir utilería nueva.'}\n"
        )
    return (
        f"# Prompt de storyboard anotado {number:02d} — {page['title']}\n\n"
        f"Genera una sola LÁMINA DE PREVISUALIZACIÓN: storyboard anotado de dirección de arte para la página {number:02d}, formato vertical 2:3. Esto NO es una página final de cómic ni una ilustración terminada. Dibuja exactamente {page['panels']} celdas con la retícula indicada, en papel marfil de cuaderno de producción. Estética obligatoria: OUTLINE SKETCH DRAFT, líneas de construcción a lápiz grafito y azul, contornos negros deliberadamente incompletos, figuras en maniquí semi-chibi adulto con línea de acción visible, sombreados de trama muy ligeros, flechas de movimiento y mirada, horizonte y líneas de fuga, y bloques simples de valores. Usa acentos codificados: azul frío para arquitectura/luz nocturna, coral para Ferry o foco emocional, amarillo para fuente de luz, rojo para props o continuidad crítica.\n\nCada celda necesita una franja estrecha de anotaciones en su canaleta exterior: código C#, mini-icono de cámara, dirección de cámara, flecha de mirada, flecha de luz, línea de acción, horizonte y círculo rojo al prop crítico. Añade siete micro-notas de continuidad, preferentemente como iconos y códigos: ID (personaje), VEST (ropa/accesorios), ESP/T (lugar/hora), CAM (encuadre), CUERPO (pose/apoyo), PROP (estado de utilería) y RELEVO (qué estado sale a la próxima celda). Si aparece un animal, el campo ID debe llevar además una placa roja de ESPECIE/RAZA con su nombre literal y mini-estudio de silueta. No uses un icono genérico de perro, tortuga, caracol o insecto. Dentro de la viñeta debe verse el esqueleto gestual antes del volumen, tres capas de profundidad (frente/medio/fondo) y flechas que expliquen dónde se mueve o mira cada figura. Las anotaciones son gráficas, breves y funcionales; no son decoración.\n\n{guide_creature_legend(cells)}\n\nNO dibujes arte final, pintura digital pulida, cel shading terminado, superficies brillantes, 3D, fotorrealismo, fondos resueltos, globos de diálogo terminados, SFX terminados, cartelas acabadas, logos, letreros inventados ni texto literal. En su lugar, dentro de cada celda dibuja: encuadre de cámara, línea de horizonte/profundidad, silueta y esqueleto gestual, flecha de mirada, flecha de movimiento, fuente de luz, icono de prop y contorno vacío donde irá el lettering. El texto de abajo es información para orientar el sketch; sólo pueden aparecer marcas técnicas brevísimas como C1, H1, F1, N1 o SFX-1, nunca frases completas.\n\n"
        "## Formato de página\n\n"
        f"- Retícula: {layout}.\n"
        f"- Número de celdas: {page['panels']}. Lectura: arriba-izquierda a abajo-derecha.\n"
        "- Seguridad: rostros, manos, globos y objetos focales a mínimo 10% de cada borde; anatomía adulta semi-chibi, dos brazos, dos piernas y manos de cinco dedos.\n"
        "- Sistema gráfico visible en CADA celda: flecha de mirada + flecha de movimiento + flecha de luz + icono/círculo de prop + silueta de lettering vacía.\n\n"
        "## Estado de escena\n\n"
        f"- Tiempo/luz: {context['time']}.\n"
        f"- Lugar: {context['location']}.\n"
        f"- Personajes: {context['cast']}.\n"
        f"- Vestuario/accesorios: {context['wardrobe']}.\n"
        f"- Bloqueo de cronología: {page_state_lock(number)}\n\n"
        "## Continuidad de borde a borde\n\n"
        f"- ENTRADA — última acción/estado de la página previa: {previous_exit}\n"
        f"- SALIDA — primera acción/estado que debe poder sostener la página siguiente: {next_entry}\n"
        "- La primera celda debe continuar esa entrada o mostrar visualmente la transición. La última celda debe dejar la salida preparada; no copies composición de otra página.\n\n"
        "## Desglose por celda\n\n"
        + "\n".join(cell_sections)
        + "\n## Chequeo de aprobación\n\n"
        "- ¿Identidad, ojos café oscuro y silueta v2 de Hassan/Ferry son correctos?\n"
        "- ¿Cada animal respeta su placa de especie/raza, anatomía, color, cantidad y negativo específico?\n"
        "- ¿Las siete dimensiones de continuidad (ID, VEST, ESP/T, CAM, CUERPO, PROP y RELEVO) son visibles y congruentes?\n"
        "- ¿Vestuario, accesorios, manos, dirección de mirada y apoyo corporal coinciden con la celda?\n"
        "- ¿Cada objeto existe ya y ningún objeto futuro aparece de decoración?\n"
        "- ¿Globos, cartelas, SFX y texto de portada coinciden exactamente con la guía?\n"
    )


def lettering_for(page_number: int, cue: str, index: int, panels: int) -> tuple[str, str, str]:
    """Separate technical metadata from the only text that may appear in art."""
    cue = literal_text(cue)
    if cue == "SILENCIO":
        return ("silencio", "sin lettering, globo ni SFX", "SILENCIO")
    label, printed = cue.split(": ", 1)
    if label.startswith("CARTELA"):
        return (
            "cartela del narrador omnipresente",
            "esquina superior izquierda de la celda, caja crema de borde negro; no cubrir rostro ni acción",
            printed,
        )
    if label.startswith("GLOBO DE"):
        side = "superior izquierda" if index % 2 else "superior derecha"
        if label == "GLOBO DE HASSAN" and (page_number <= 10 or 36 <= page_number <= 83):
            return (
                "pensamiento interior de Hassan",
                f"{side} de la celda, nube de pensamiento compacta junto a Hassan; máximo 22% del área de la celda, dos líneas legibles como máximo",
                printed,
            )
        if label == "GLOBO DE HASSAN":
            return (
                "globo de diálogo de Hassan",
                f"{side} de la celda, globo redondeado junto a Hassan; cola clara dirigida a Hassan, máximo 18% del área de la celda",
                printed,
            )
        if label == "GLOBO DE FERRY":
            return (
                "globo de diálogo de Ferry",
                f"{side} de la celda, globo redondeado junto a Ferry; cola clara, máximo 18% del área de la celda",
                printed,
            )
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
        camera = CELL_CAMERA_OVERRIDES.get((number, index), camera_for(action, index, panels))
        cameo = INGREDIENT_CAMEOS.get((number, index))
        if cameo:
            action = f"{action} {cameo}"
        state_lock = CELL_STATE_LOCKS.get((number, index), "")
        if state_lock:
            action = f"{action} ESTADO CANÓNICO DE ESTA CELDA (OBLIGATORIO): {state_lock}"
        creature_lock = creature_lock_for(number, index, action)
        lettering_type, lettering_placement, printed_text = lettering_for(number, cue, index, panels)
        cells.append(
            {
                "cell": str(index),
                "placement": placement,
                "camera": camera,
                "action": action,
                "state_lock": state_lock,
                "creature_lock": creature_lock,
                "lettering_type": lettering_type,
                "lettering_placement": lettering_placement,
                "printed_text": printed_text,
                "permitted_diegetic_text": BOOK_COVER_TEXT if (number, index) in BOOK_COVER_CELLS else "",
            }
        )
    return layout, cells


def prompt_for(page: dict[str, object], layout: str, cells: list[dict[str, str]], continuity: dict[str, object]) -> str:
    number = page["number"]
    title = page["title"]
    panels = page["panels"]
    scene = "\n".join(
        f"CELDA {cell['cell']} — posición: {cell['placement']}; cámara: {cell['camera']}.\n"
        f"Acción y arte: {cell['action']}\n"
        f"Especie/raza bloqueada: {cell['creature_lock']}\n"
        f"Tipo de lettering: {cell['lettering_type']}. Posición de lettering: {cell['lettering_placement']}.\n"
        f"Texto impreso exacto: {cell['printed_text']}\n"
        f"Texto diegético permitido: {cell['permitted_diegetic_text'] or 'NINGUNO'}"
        for cell in cells
    )
    return f"""Create one original vertical 6x9 comic-book page in a 2:3 aspect ratio.
Use exactly {panels} distinct comic panels separated by clean, consistent gutters; do not make a collage or a poster.
Exact page reticle: {layout}. Read from upper left to lower right.
The only letters permitted in the art are the phrases after “Texto impreso exacto:” plus, only where declared, the exact cover text after “Texto diegético permitido:”. Render each permitted phrase character for character, including accents and punctuation, using the double quotes shown. “CELDA”, “Tipo de lettering”, “Posición de lettering”, “Texto diegético permitido” and every other label are production instructions only: never render those labels in the image. Place the lettering exactly as specified per cell. If “Texto impreso exacto” says SILENCIO, draw no bubble and no letters in that cell, except a cover text explicitly declared for that cell. Do not add, alter, translate or invent any other text, number, logo or watermark. The recipe note, when present, must show only deliberately illegible numbered-looking strokes.
{TREATMENT_BASE}
{continuity_reference_manifest(number)}
Hassan is a gentle, meticulous adult scientist; Ferry is an original adult pop heroine, warm, athletic and protective. Ferry is never created, owned or controlled by Hassan. Follow their attached approved v2 character sheets as the primary visual authority; use this page only for story-specific action, temporal props and scene wardrobe.
{CHARACTER_SHEET_AUTHORITY}
{creature_bible_for_cells(cells)}
{VOICE_DIRECTION}
{POSE_ANATOMY_RULES}
{NEGATIVE_ANATOMY_PROMPT}
{negative_creature_prompt_for_cells(cells)}
Cool white, steel and blue-gray laboratory reality; dream and magic in warm pink, coral, gold and carmine. Repeat the red thread, empty-to-full flask and pink-gold star only when the beats call for them. Keep faces, hands and focal objects at least 10% inside every edge.

{continuity['instruction']}

{page_state_lock(number)}

Page {number:02d} — {title}
{scene}
"""


def dossier_for(pages: list[dict[str, object]]) -> str:
    entries = [
        "# Guion técnico — 90 páginas con diálogo\n",
        "\n",
        "Este dossier es la especificación de producción. Cada página define retícula, orden de lectura, cámara, acción y el único texto permitido. Todo texto literal va entre comillas dobles. Las etiquetas técnicas no se imprimen: sólo se imprime el valor de `Texto impreso exacto`. `SILENCIO` significa que no puede aparecer ningún globo ni letra en esa celda. Las cartelas pertenecen al narrador omnipresente; las nubes son pensamientos interiores de Hassan; Ferry habla con una voz adulta Gen Z cálida y ligera. En las páginas 66–77 Hassan enumera en pantalla los ingredientes 1–29 y cada aparición arquetípica de Ferry es un diseño original, no una copia de una figura evocada.\n",
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
                f"   **Texto diegético permitido:** {cell['permitted_diegetic_text'] or 'NINGUNO'}\n"
            )
    return "".join(entries)


def dialogue_ledger_for(pages: list[dict[str, object]]) -> str:
    """List every visible text token with its page, cell and attribution."""
    entries = [
        "# Diálogos y texto visible — 90 páginas\n\n",
        "Índice de revisión editorial derivado de la misma fuente que los prompts. Incluye diálogo, pensamiento, cartela, SFX, silencio y texto diegético permitido. Todo texto entre comillas debe reproducirse literalmente en el arte.\n",
    ]
    for page in pages:
        _, cells = cells_for(page)
        entries.append(f"\n## {page['number']:02d}. {page['title']}\n\n")
        for cell in cells:
            text = guide_text(cell)
            entries.append(f"- **Celda {cell['cell']} — {cell['placement']}:** {text}\n")
    return "".join(entries)


def creature_audit_for(pages: list[dict[str, object]]) -> str:
    """Create a page/cell ledger of permitted creature identities and absences."""
    entries = [
        "# Auditoría de especies y razas — 90 páginas\n\n",
        "Esta auditoría se deriva de las mismas celdas que los prompts finales y las guías. "
        "Una criatura sólo puede aparecer en la celda cuyo bloqueo la autoriza; `SIN CRIATURA EN CUADRO` "
        "prohíbe mascotas, siluetas e iconos animales de fondo. Antes de aprobar arte, comprobar especie/raza, "
        "cantidad, rasgos y exclusiones de cada celda.\n",
    ]
    for page in pages:
        _, cells = cells_for(page)
        allowed = creature_names_for_cells(cells)
        summary = "ninguna criatura visible" if not allowed else ", ".join(CREATURE_GUIDE_LABELS[name] for name in allowed)
        entries.append(f"\n## {page['number']:02d}. {page['title']}\n\n")
        entries.append(f"- **Criaturas permitidas en la página:** {summary}.\n")
        for cell in cells:
            entries.append(f"- **Celda {cell['cell']}:** {cell['creature_lock']}\n")
    return "".join(entries)


def retrograde_audit_for(pages: list[dict[str, object]]) -> str:
    """Produce a human review ledger in the requested 90-to-01 order."""
    entries = [
        "# Auditoría retrospectiva de continuidad — 90 → 01\n\n",
        "Este reporte se lee de la última página a la primera. Para cada página, el revisor confirma que su estado, sus objetos y sus ausencias ya pueden sostenerse con la página anterior inmediata. `state_lock` no evalúa píxeles: convierte la continuidad en un criterio explícito de aprobación humana.\n",
    ]
    for index in range(len(pages) - 1, -1, -1):
        page = pages[index]
        _, cells = cells_for(page)
        predecessor = "No aplica: esta página establece el estado inicial." if index == 0 else (
            f"La página {pages[index - 1]['number']:02d} ({pages[index - 1]['title']}) debe sostener este estado antes de esta transición."
        )
        cell_locks = [
            f"{cell['cell']}: {cell['state_lock']}"
            for cell in cells
            if cell["state_lock"]
        ]
        cells = "; ".join(cell_locks) if cell_locks else "Sin transición interna adicional; mantener el bloqueo de página."
        story_state = " / ".join(page["beats"])
        entries.extend(
            [
                f"\n## {page['number']:02d}. {page['title']}\n\n",
                f"- **Estado narrativo que se reconcilia:** {story_state}\n",
                f"- **Estado de página:** {page_state_lock(page['number'])}\n",
                f"- **Verificación hacia atrás:** {predecessor}\n",
                f"- **Celdas con transición:** {cells}\n",
            ]
        )
    return "".join(entries)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compila los 90 prompts locales de cómic desde el corpus narrativo."
    )
    parser.add_argument(
        "--attach-previous-page-reference",
        action="store_true",
        help=(
            "Activa de forma explícita la referencia visual de la última celda de la página "
            "anterior para las páginas 02–90. Por defecto no se adjunta ninguna página anterior."
        ),
    )
    args = parser.parse_args()
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
    GUIDES.mkdir(parents=True, exist_ok=True)
    (GUIDES / "README.md").write_text(GUIDE_README, encoding="utf-8")
    plan_pages = []
    for page in pages:
        identifier = f"{page['number']:02d}-{slug(page['title'])}"
        layout, cells = cells_for(page)
        continuity = previous_page_reference(page, args.attach_previous_page_reference)
        if continuity["attached"]:
            preceding = plan_pages[-1]["id"]
            continuity["approved_page_id"] = preceding
            continuity["approved_art"] = f"arte-aprobado/{preceding}.png"
        prompt = prompt_for(page, layout, cells, continuity)
        (PROMPTS / f"{identifier}.txt").write_text(prompt, encoding="utf-8")
        (GUIDES / f"{identifier}.md").write_text(
            guide_for(page, layout, cells, pages), encoding="utf-8"
        )
        plan_pages.append(
            {
                "id": identifier,
                "panels": page["panels"],
                "layout": layout,
                "references": references(page["number"]),
                "title": page["title"],
                "beats": page["beats"],
                "cells": cells,
                "state_lock": page_state_lock(page["number"]),
                "previous_page_reference": continuity,
                "prompt": f"prompts-90/{identifier}.txt",
                "production_guide": f"prompts-guia-90/{identifier}.md",
            }
        )
    DOSSIER.write_text(dossier_for(pages), encoding="utf-8")
    AUDIT_REPORT.write_text(retrograde_audit_for(pages), encoding="utf-8")
    DIALOGUE_LEDGER.write_text(dialogue_ledger_for(pages), encoding="utf-8")
    CREATURE_AUDIT.write_text(creature_audit_for(pages), encoding="utf-8")
    PLAN.write_text(
        json.dumps(
            {
                "project": "PowerPuff Ferry — corpus visual de 90 páginas",
                "source": "../manuscrito/06-corpus-narrativo-90-paginas.md",
                "visual_treatment": "tratamiento-visual-2-3.md",
                "aspect_ratio": "2:3",
                "trim_size": "6x9 in",
                "model": "gpt-image-2",
                "resolution": "2K",
                "print_page_count": 90,
                "visual_storytelling_only": False,
                "text_policy": "Sólo el diálogo, cartelas y efectos declarados por celda; el texto literal usa comillas dobles.",
                "voice_policy": "Cartelas del narrador omnipresente; Hassan íntimo y directo en diálogo o pensamiento; Ferry adulta Gen Z cálida y ligera. Las páginas 66–77 enumeran los ingredientes 1–29 en la voz de Hassan.",
                "anatomy_policy": "Anatomía adulta semi-chibi clara y poses naturales: dos brazos, dos piernas, dos manos, cinco dedos visibles por mano, articulaciones posibles, silueta madura y cabeza no extrema; los prompts incluyen control negativo contra deformaciones.",
                "character_sheet_policy": "Las hojas v2 adjuntas de Ferry y Hassan son la autoridad visual primaria para identidad física, rostro, cabello, ojos café oscuro, silueta, paleta, vestuario base y accesorios. La cronología por celda sólo gobierna props, acción y vestuario específico de escena.",
                "previous_page_reference_policy": "Opcional y desactivada por defecto. Al compilar con --attach-previous-page-reference, sólo la última celda aprobada de la página previa fija el estado inicial; nunca autoriza copiar composición ni introducir objetos.",
                "state_continuity_policy": "Cada prop, ausencia y transición canónica se bloquea por página y, cuando corresponde, por celda; la continuidad no depende de adjuntar una página anterior.",
                "production_guide_policy": "Cada página tiene una guía esquemática de composición que explicita retícula, tiempo, lugar, personajes, vestuario, accesorios, poses, texto, efectos y continuidad de entrada/salida.",
                "creature_identity_policy": "La raza o especie se bloquea por celda con rasgos positivos y negativos. Cada prompt y guía sólo enumera las criaturas activas de su página; las demás se prohíben incluso como fondo, icono o decoración.",
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
