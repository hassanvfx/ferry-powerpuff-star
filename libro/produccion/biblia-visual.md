# Biblia visual de continuidad

Esta guía acompaña cada prompt de Kie. Su propósito no es copiar una foto literal en cada panel, sino mantener reconocible a cada protagonista y coherente el universo del libro.

El [tratamiento visual 2:3](tratamiento-visual-2-3.md) es la guía de puesta en escena, expresividad, color y simplificación chibi; esta biblia conserva la continuidad específica de personajes, objetos y arcos.

## Lenguaje de ilustración aprobado como dirección

- **Base:** superhéroe semi-chibi retro original: adultos de silueta madura y atlética, piernas largas legibles, cabeza expresiva pero no extrema, ojos grandes y equilibrados con el rostro, nariz y boca simples, contorno negro definido y color plano con cel shading mínimo.
- **No es una copia:** no usar nombres, logotipos, siluetas, vestuario, paletas de identidad ni personajes de ninguna franquicia. La referencia compartida orienta proporción, energía, líneas y ritmo; Ferry y Hassan siguen siendo diseños originales adultos.
- **Referencia de estilo aprobada:** [`chibi-superhero-comic-style-reference.png`](../arte/referencias/chibi-superhero-comic-style-reference.png) se adjunta a toda generación. Sólo guía el acabado: contorno negro grueso, color plano brillante, cel shading mínimo, fondos gráficos y acción legible. No se copian sus personajes, texto, composición, símbolos ni paletas específicas.
- **Color:** rosa/coral/oro para Ferry y la magia; azul tinta/blanco acero para Hassan y el laboratorio; hilo rojo y estrella rosa-dorada son los puentes de ambos mundos.
- **Texto y globos:** usar sólo los diálogos, cartelas y SFX declarados para cada celda en el [guion técnico](../manuscrito/08-guion-tecnico-90-paginas.md). En el prompt, sólo el valor de `Texto impreso exacto` aparece en el arte y siempre va entre comillas dobles; etiquetas como `CELDA`, `Tipo de lettering` o `Posición de lettering` son instrucciones que nunca se imprimen. No añadir, alterar, traducir ni inventar otras letras; la nota sí conserva trazos enumerados ilegibles.
- **Objetos:** ingredientes, matraces y símbolos no reciben caras ni personalidad de mascota. Sólo Ferry, Hassan y los animales nombrados pueden tener rostro.

## Hojas de personaje

El autor aprobó [`ferry-character-sheet-v2.png`](../arte/referencias/ferry-character-sheet-v2.png) y [`hassan-character-sheet-v2.png`](../arte/referencias/hassan-character-sheet-v2.png) como **autoridad visual primaria** para la producción futura. Si un resumen heredado discrepa, gana el rasgo visible de la hoja v2: rostro, ojos, piel, cabello, barba, silueta, paleta, vestuario base y accesorios. El guion de página sólo tiene prioridad sobre utilería que aún no existe, acción y vestuario específicamente requerido por la escena. El ejecutor añade la hoja aprobada correspondiente cuando una página nombra a Ferry o Hassan; las fotos privadas autorizadas se conservan sólo como referencia facial. Los prompts v1 quedan como historial en `plan-de-personajes.json`; el brief reproducible v2 vive en `plan-de-personajes-v2.json`. El modo `--approved-references-only` adjunta exclusivamente la referencia de estilo y estas hojas, sin leer fotos privadas.

## Hassan

- **Ojos canónicos:** café oscuro, profundos y expresivos; nunca azul, cian, rosa, magenta, verde ni de otro color.

- Científico sensible y meticuloso, nunca un científico loco ni una caricatura. Su sheet fija cabello corto oscuro, cejas oscuras, barba completa cuidada y piel cálida.
- La referencia facial es la fotografía privada indicada en `referencias.local.json`.
- En la realidad viste de forma sobria, con siluetas limpias y colores fríos; en el sueño recibe reflejos rosas y dorados, pero sigue siendo reconocible.
- Sus gestos narrativos son: ordenar, observar, dudar, cuidar un objeto con ambas manos y finalmente maravillarse.
- El vestuario aprobado v2 incluye bata blanca sobre camiseta azul marino, pantalón carbón y tenis azul marino; look casual con sobrecamisa índigo, chaqueta azul de campo con mochila y traje azul noche con detalle dorado. Elegir el look que sostenga la escena.

## Ferry

- **Ojos canónicos:** café oscuro, profundos y expresivos; nunca azul, cian, rosa, magenta, verde ni de otro color.

- Heroína pop original, amorosa, atlética, curiosa y protectora; no una versión de un personaje existente. Su sheet fija piel cálida, cabello largo ondulado castaño con mechas doradas, cejas oscuras y silueta adulta esbelta.
- Las referencias faciales son las dos fotografías privadas configuradas localmente.
- En el sueño puede llevar elementos de porrista y energía pop, pero el vestuario debe ser original, sin emblemas, logotipos ni uniformes reconocibles.
- Su poder se expresa como calma, luz y cuidado: nunca como dominación o como objeto producido por Hassan.
- Su silueta aprobada v2 es adulta y atlética. El tratamiento semi-chibi puede simplificarla, pero no convertirla en cuerpo bebé ni usar una cabeza extrema. Su vestuario incluye vestido coral plisado, chaqueta blanca corta, cinturón dorado y tenis blanco-oro; vestido de playa marfil, look de viaje azul/coral y traje heroico coral-oro. El dije de concha dorada, moño coral y cordón rojo son accesorios de sheet que sólo entran cuando el beat los permite; elegir el look que sostenga la escena.

## Motivos que deben repetirse

| Motivo | Primera aparición | Evolución | Resolución |
| --- | --- | --- | --- |
| Hilo rojo | 14 | Nota, ingredientes y tablero del coche | Se vuelve luz sobre la arena en 90. |
| Matraz | 01 | Recibe luz en 64 y se llena en 66–78 | Libera la estrella en 84. |
| Estrella rosa-dorada | 01 | Se insinúa en sueño, café y conjuro | Permanece en el cielo final (90). |
| Ondas binaurales | 06 | Conducen el sueño | Regresan como magia ordenada en 80–81. |
| Concha dorada | 57 y 71 | Se integra a la receta | Hassan la reconoce en la playa (90). |

## Continuidad entre páginas

- La página 01 establece el canon y no recibe una página narrativa previa.
- Desde la página 02, se adjunta **sólo** la página anterior que haya sido revisada y guardada en `arte-aprobado/`.
- La referencia previa conserva identidad, escala, paleta, línea, luz, vestuario y evolución de motivos; nunca se usa para repetir encuadre, retícula, pose, expresión, acción, diálogo, SFX, objetos, fondo o composición.
- El brief de la página actual siempre tiene prioridad. Si el arte anterior contradice el prompt actual, se corrige la continuidad en el arte nuevo sin copiar el plano anterior.
- La [auditoría de estados](continuidad-de-estados.md) gobierna el inventario y las transiciones: una referencia previa conserva apariencia, pero no autoriza que aparezcan objetos futuros. El estado por celda del prompt tiene prioridad para monitor, matraz, hilo, nota, lupa, carrete, concha y estrella.
- La [auditoría retrospectiva 90→01](auditoria-retroactiva-90.md) es la lectura de control antes de aprobar arte: cada página debe poder justificarse con el estado de su predecesora, sin adelantar su siguiente beat.

## Paleta por acto

- **Páginas 01–10:** blanco frío, azul gris y acero; rosa muy escaso.
- **Páginas 11–35:** rosa satinado, coral, oro y carmesí; el sueño domina.
- **Páginas 36–65:** realidad azul con intrusiones rosas; café y ámbar como puente.
- **Páginas 66–83:** cada ingrediente suma color; el laboratorio se vuelve un arcoíris contenido.
- **Páginas 84–90:** rosa-dorado como luz principal, coral de amanecer y azul marino de costa.

## Control de viñetas

- Respetar el número de paneles definido para cada id en `plan-de-imagenes-90.json`.
- Cada página debe tener de 2 a 6 viñetas y una acción clara por viñeta.
- En páginas de 5 o 6 paneles, cada panel debe contener un solo objeto o microacción; no mezclar ingredientes ni personajes sin una razón narrativa.
- Los divisores deben ser limpios, consistentes y de contraste suficiente para seguir impresos a 6×9.

## Revisión humana antes de aprobar una imagen

1. ¿Se reconoce al personaje correcto a partir de la referencia autorizada?
2. ¿El número de viñetas y la acción coinciden con el guion de página?
3. ¿Cada texto coincide exactamente con el guion técnico, no hay letras adicionales, logotipos ni elementos que copien una franquicia?
4. ¿Los rostros, manos y objetos clave respetan el margen seguro del 10%?
5. ¿La paleta corresponde al acto y hay continuidad con la página anterior y la siguiente?
6. ¿Cada prop respeta su estado canónico por celda —incluidas ausencias— según la [auditoría de estados](continuidad-de-estados.md)?
