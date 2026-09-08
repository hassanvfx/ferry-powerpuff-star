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
PROMPTS = ROOT / "produccion" / "prompts-90"
DOSSIER = ROOT / "manuscrito" / "08-guion-tecnico-90-paginas.md"
TREATMENT = ROOT / "produccion" / "tratamiento-visual-2-3.md"
AUDIT_REPORT = ROOT / "produccion" / "auditoria-retroactiva-90.md"
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
    ["GLOBO DE HASSAN: «A esta hora el laboratorio se siente más grande.»", "GLOBO DE HASSAN: «Ya voy. Sólo quiero llegar, bañarme y dormir.»", "CARTELA: «El laboratorio guarda el silencio.»"],
    ["GLOBO DE HASSAN: «Una copa y ya. Necesito bajar un poco.»", "SFX: «clin»", "GLOBO DE HASSAN: «Pongo música. A ver si dejo de pensar.»"],
    ["GLOBO DE HASSAN: «La frecuencia está bien. Ojalá mi cabeza también.»", "SFX: «mmmm»", "GLOBO DE HASSAN: «No tengo que resolver todo hoy.»", "CARTELA: «Respira.»"],
    ["GLOBO DE HASSAN: «Respira. Hoy hiciste lo que pudiste.»", "SFX: «hummm»", "GLOBO DE HASSAN: «Mañana veo las cosas con más calma.»"],
    ["CARTELA: «El sueño toma aire.»", "SFX: «hummm»"],
    ["SFX: «shhh»", "SFX: «tinnn»", "GLOBO DE HASSAN: «Esto no se siente como los otros sueños.»"],
    ["SFX: «whooosh»", "GLOBO DE HASSAN: «Si estoy soñando, prefiero no despertar todavía.»"],
    ["SFX: «ta-dá»", "SFX: «aplausos lejanos»", "GLOBO DE HASSAN: «¿Qué lugar es este? Siento que ya lo conozco.»"],
    ["SFX: «tap»", "SFX: «fwoosh»", "CARTELA: «Una luz toma forma.»"],
    ["SFX: «FWOOSH»", "SFX: «vrrr»", "GLOBO DE HASSAN: «Ferry… hasta dormido sigo pensando en ti.»", "SFX: «TÁ!»"],
    ["CARTELA: «La chica de sus sueños.»", "GLOBO DE FERRY: «Holi, Hassan. Llegaste justo a tiempo.»", "SFX: «tinnn»"],
    ["GLOBO DE FERRY: «Ven, te enseño el lugar donde cuido lo que amo.»", "GLOBO DE HASSAN: «Voy contigo. No sé a dónde, pero voy.»"],
    ["GLOBO DE FERRY: «Zeus.»", "GLOBO DE FERRY: «Todo bien, grandote. Estoy aquí contigo.»", "SFX: «wuf»"],
    ["SFX: «thump»", "GLOBO DE FERRY: «Buen chico. Sabía que podías confiar.»", "SFX: «tinnn»"],
    ["GLOBO DE FERRY: «Déjame ver. No quiero que te duela ni un poquito.»", "SFX: «zap»"],
    ["SFX: «plop»", "GLOBO DE FERRY: «Aquí estás. No te me escondas solito.»", "SFX: «fiuu»"],
    ["GLOBO DE FERRY: «Buenos días, Yohi. ¿Listo para tu hoja favorita?»", "SFX: «crisp»", "SILENCIO"],
    ["SFX: «toc… toc…»", "GLOBO DE FERRY: «Sin prisa. Tú marcas el paso.»"],
    ["SFX: «ñam»", "GLOBO DE FERRY: «Todo a tu tiempo. Aquí nadie tiene que correr.»", "GLOBO DE HASSAN: «Tienes una paciencia que yo todavía estoy aprendiendo.»"],
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
    ["GLOBO DE HASSAN: «Antes de hacerme historias, voy a revisarlo bien.»", "SFX: «tap»", "GLOBO DE HASSAN: «Al laboratorio. Ahí por lo menos puedo empezar.»"],
    ["GLOBO DE HASSAN: «Necesito ver esto con calma y sin inventar nada.»", "SFX: «swish»", "CARTELA: «Una pregunta merece método.»"],
    ["SFX: «zoom»", "CARTELA: «Sinceridad.»", "GLOBO DE HASSAN: «Primero: sinceridad. A ver qué me pide esta nota.»"],
    ["CARTELA: «Empatía.»", "CARTELA: «Inteligencia.»", "CARTELA: «Curiosidad.»", "GLOBO DE HASSAN: «¿Una receta de Ferry? Esto tiene que significar algo.»"],
    ["SFX: «fwoom»", "CARTELA: «No son palabras. Son pistas.»", "GLOBO DE HASSAN: «No son palabras al azar. Me están dejando pistas.»"],
    ["GLOBO DE HASSAN: «Cocina, sala, patio. Voy a revisar todo.»", "SFX: «tinnn»"],
    ["SFX: «clac»", "GLOBO DE HASSAN: «Empiezo por aquí. Algo tiene que hacer sentido.»", "SFX: «fiuu»"],
    ["SFX: «crash»", "GLOBO DE HASSAN: «No, no, no… bueno. Tal vez sí sirve.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «Ya empecé. Ahora quiero saber a dónde lleva esto.»", "SFX: «tinnn»"],
    ["CARTELA: «Talento que da calor.»", "SFX: «fwoom»", "GLOBO DE HASSAN: «Canela. Contigo hasta lo simple se siente especial.»"],
    ["SFX: «rustle»", "GLOBO DE HASSAN: «Vainilla. Suave, pero se queda.»", "SFX: «tinnn»"],
    ["SFX: «tinnn»", "GLOBO DE HASSAN: «Una cuchara. No parece importante, pero aquí está.»"],
    ["SFX: «scrape»", "GLOBO DE HASSAN: «¿Una moneda? Todo esto está más raro de lo que pensé.»", "SFX: «vrrr»"],
    ["GLOBO DE HASSAN: «Trabajo y paciencia. Supongo que así se hacen las cosas.»", "SFX: «clic clic»"],
    ["SFX: «fiuu»", "GLOBO DE HASSAN: «El hilo otra vez. Esto ya no puede ser coincidencia.»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «Una concha. ¿Por qué siento que la conozco?»", "SFX: «swish»", "CARTELA: «Una gota de horizonte.»"],
    ["SFX: «scrape»", "GLOBO DE HASSAN: «Resistir y volver a crecer. Eso sí te lo reconozco.»", "SFX: «crack»"],
    ["GLOBO DE HASSAN: «Cariño que abriga. Sí, esa parte es muy tuya.»", "SFX: «poof»"],
    ["SFX: «clink»", "GLOBO DE HASSAN: «Confianza. Esa sí cuesta encontrarla.»", "SFX: «tinnn»"],
    ["SFX: «poof»", "GLOBO DE HASSAN: «Tranquila, nube. No tengo que entenderte hoy.»", "SFX: «pop»"],
    ["SFX: «clink»", "SFX: «fiuu»", "GLOBO DE HASSAN: «Casi está todo. Sólo falta saber qué significa.»"],
    ["GLOBO DE HASSAN: «Todo tiene un lugar. Y esta nota también.»", "SFX: «tinnn»", "CARTELA: «La fórmula empieza a mirar de vuelta.»"],
    ["GLOBO DE HASSAN: «No es una mezcla cualquiera. Algo está por pasar.»", "SFX: «beeeep»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «Faltan cosas. Las últimas deben ser las importantes.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «1. Cristales de sinceridad.»", "GLOBO DE HASSAN: «No esconder lo que siento. Esa parte me cuesta.»", "GLOBO DE HASSAN: «2. Nube tibia de empatía.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «3. Frasco de luz científica.»", "GLOBO DE HASSAN: «Entender para cuidar. Contigo lo veo más claro.»", "GLOBO DE HASSAN: «4. Lupa de luna curiosa.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «5. Polvo de sonrisa encantada.»", "GLOBO DE HASSAN: «Cuando sonríes, se me cambia el día.»", "GLOBO DE HASSAN: «6. Llama de leona roja.»", "SFX: «fwoosh»"],
    ["GLOBO DE HASSAN: «7. Nido de ternura.»", "GLOBO DE HASSAN: «Siempre estás pendiente de todos. Eso no se te quita.»", "GLOBO DE HASSAN: «8. Escudo de oro valiente.»", "SFX: «clang»"],
    ["GLOBO DE HASSAN: «9. Monedas de miel y engranes.»", "GLOBO DE HASSAN: «Con cuidado. No quiero echar a perder nada.»", "GLOBO DE HASSAN: «10. Estrella de esperanza infinita.»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «11. Flor de inocencia.»", "GLOBO DE HASSAN: «A veces una cosa pequeña cambia todo.»", "GLOBO DE HASSAN: «12. Concha dorada del mar.»", "SFX: «swish»"],
    ["GLOBO DE HASSAN: «13. Raíz de perseverancia.»", "GLOBO DE HASSAN: «Sigues aunque estés cansada. Eso admiro de ti.»", "GLOBO DE HASSAN: «14. Cuchara de canela y vainilla.»", "GLOBO DE HASSAN: «Tu talento hace que hasta lo diario se sienta bonito.»", "GLOBO DE HASSAN: «15. Cristal de orden.»", "SFX: «tinnn»"],
    ["GLOBO DE HASSAN: «16. Campanillas de sol.»", "GLOBO DE HASSAN: «Cuando llegas contenta, se me contagia.»", "GLOBO DE HASSAN: «17. Reloj de arena sereno.»", "GLOBO DE HASSAN: «Esperar sin presionar también es querer.»", "GLOBO DE HASSAN: «18. Manta de algodón de cariño.»", "SFX: «poof»"],
    ["GLOBO DE HASSAN: «19. Sobres perfumados de amor.»", "GLOBO DE HASSAN: «Tus mensajes hacen que el día se sienta más cerca.»", "GLOBO DE HASSAN: «20. Puente de pétalos.»", "GLOBO DE HASSAN: «Hablar contigo aclara muchas cosas.»", "GLOBO DE HASSAN: «21. Chispa salvaje.»", "SFX: «zap»"],
    ["GLOBO DE HASSAN: «22. Trofeo de cuerpo en movimiento.»", "GLOBO DE HASSAN: «Tu fuerza se nota, aunque no hagas ruido.»", "GLOBO DE HASSAN: «23. Cáliz de nutrición sagrada.»", "GLOBO DE HASSAN: «Cuidar a alguien diario también es amor.»", "GLOBO DE HASSAN: «24. Llave de confianza.»", "SFX: «clic»"],
    ["GLOBO DE HASSAN: «25. Anillo de fidelidad.»", "GLOBO DE HASSAN: «Quedarse porque quieres, no porque tienes que hacerlo.»", "GLOBO DE HASSAN: «26. Hilo rojo del destino.»", "GLOBO DE HASSAN: «Este hilo siempre termina llevándome a ti.»", "GLOBO DE HASSAN: «27. Moño rosa con fuego.»", "SFX: «fwoom»"],
    ["GLOBO DE HASSAN: «28. Luciérnagas de madrugada.»", "GLOBO DE HASSAN: «Siempre estás preguntando cosas. Por eso nunca me aburro.»", "SFX: «tinnn»", "GLOBO DE HASSAN: «29. Pincel de creatividad infinita.»", "SFX: «shraaa»"],
    ["CARTELA: «Veintinueve razones.»", "GLOBO DE HASSAN: «Todas hablan de ti. Ninguna te pide que seas otra persona.»", "GLOBO DE HASSAN: «Quiero que estés porque quieres estar, no por esta fórmula.»", "SFX: «fwoom»"],
    ["SFX: «clic»", "CARTELA: «La receta ya no necesita palabras.»", "SFX: «fiuu»", "GLOBO DE HASSAN: «Ahora sí. Voy a hacerlo con cuidado.»"],
    ["SFX: «KRAK»", "GLOBO DE HASSAN: «Si algo va a pasar, las piezas ya están listas.»", "SFX: «FWOOM»"],
    ["SFX: «vrrr»", "SFX: «tinnn»", "GLOBO DE HASSAN: «Está funcionando… y no sé si debería asustarme.»", "SFX: «shraaa»"],
    ["GLOBO DE HASSAN: «Despacio. No quiero arruinarlo por querer correr.»", "CARTELA: «El sueño también tiene memoria.»", "GLOBO DE HASSAN: «La magia también necesita que uno haga las cosas bien.»"],
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
        lettering_type, lettering_placement, printed_text = lettering_for(number, cue, index, panels)
        cells.append(
            {
                "cell": str(index),
                "placement": placement,
                "camera": camera,
                "action": action,
                "state_lock": state_lock,
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
Hassan is a gentle, meticulous adult scientist; Ferry is an original adult pop heroine, warm, athletic and protective. Ferry is never created, owned or controlled by Hassan. Follow their attached approved v2 character sheets as the primary visual authority; use this page only for story-specific action, temporal props and scene wardrobe.
{CHARACTER_SHEET_AUTHORITY}
{VOICE_DIRECTION}
{POSE_ANATOMY_RULES}
{NEGATIVE_ANATOMY_PROMPT}
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
            }
        )
    DOSSIER.write_text(dossier_for(pages), encoding="utf-8")
    AUDIT_REPORT.write_text(retrograde_audit_for(pages), encoding="utf-8")
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
