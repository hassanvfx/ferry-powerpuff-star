# Biblia visual de continuidad

Esta guía acompaña cada prompt de Kie. Su propósito no es copiar una foto literal en cada panel, sino mantener reconocible a cada protagonista y coherente el universo del libro.

## Lenguaje de ilustración aprobado como dirección

- **Base:** superhéroe chibi retro original: cuerpos compactos de adultos, rostros redondeados, ojos grandes y expresivos, nariz y boca simples, contorno negro definido y color plano con cel shading mínimo.
- **No es una copia:** no usar nombres, logotipos, siluetas, vestuario, paletas de identidad ni personajes de ninguna franquicia. La referencia compartida orienta proporción, energía, líneas y ritmo; Ferry y Hassan siguen siendo diseños originales adultos.
- **Color:** rosa/coral/oro para Ferry y la magia; azul tinta/blanco acero para Hassan y el laboratorio; hilo rojo y estrella rosa-dorada son los puentes de ambos mundos.
- **Texto y globos:** usar sólo los diálogos, cartelas y SFX declarados para cada celda en el [guion técnico](../manuscrito/08-guion-tecnico-90-paginas.md). En el prompt, sólo el valor de `Texto impreso exacto` aparece en el arte y siempre va entre comillas dobles; etiquetas como `CELDA`, `Tipo de lettering` o `Posición de lettering` son instrucciones que nunca se imprimen. No añadir, alterar, traducir ni inventar otras letras; la nota sí conserva trazos enumerados ilegibles.
- **Objetos:** ingredientes, matraces y símbolos no reciben caras ni personalidad de mascota. Sólo Ferry, Hassan y los animales nombrados pueden tener rostro.

## Hojas de personaje

El autor aprobó [`ferry-character-sheet-v2.png`](../arte/referencias/ferry-character-sheet-v2.png) y [`hassan-character-sheet-v2.png`](../arte/referencias/hassan-character-sheet-v2.png) como fuente de continuidad visual para la producción futura. El ejecutor añade la hoja aprobada correspondiente cuando una página nombra a Ferry o Hassan; las fotos privadas autorizadas se conservan sólo como referencia facial. Los prompts v1 quedan como historial en `plan-de-personajes.json`; el brief reproducible v2 vive en `plan-de-personajes-v2.json`.

## Hassan

- Científico sensible y meticuloso, nunca un científico loco ni una caricatura.
- La referencia facial es la fotografía privada indicada en `referencias.local.json`.
- En la realidad viste de forma sobria, con siluetas limpias y colores fríos; en el sueño recibe reflejos rosas y dorados, pero sigue siendo reconocible.
- Sus gestos narrativos son: ordenar, observar, dudar, cuidar un objeto con ambas manos y finalmente maravillarse.
- El vestuario aprobado v2 incluye bata minimalista, look casual índigo, abrigo de investigación de campo y blazer azul noche; elegir el look que sostenga la escena.

## Ferry

- Heroína pop original, amorosa, atlética, curiosa y protectora; no una versión de un personaje existente.
- Las referencias faciales son las dos fotografías privadas configuradas localmente.
- En el sueño puede llevar elementos de porrista y energía pop, pero el vestuario debe ser original, sin emblemas, logotipos ni uniformes reconocibles.
- Su poder se expresa como calma, luz y cuidado: nunca como dominación o como objeto producido por Hassan.
- Su silueta aprobada v2 es adulta, delgada y atlética, con piernas largas. Su vestuario incluye vestido coral y chaqueta blanca, vestido de playa marfil, look de viaje azul/coral y traje heroico coral-oro; elegir el look que sostenga la escena.

## Motivos que deben repetirse

| Motivo | Primera aparición | Evolución | Resolución |
| --- | --- | --- | --- |
| Hilo rojo | 14 | Nota, ingredientes y tablero del coche | Se vuelve luz sobre la arena en 90. |
| Matraz | 01 | Recibe luz en 64 y se llena en 66–78 | Libera la estrella en 84. |
| Estrella rosa-dorada | 01 | Se insinúa en sueño, café y conjuro | Permanece en el cielo final (90). |
| Ondas binaurales | 06 | Conducen el sueño | Regresan como magia ordenada en 80–81. |
| Concha dorada | 57 y 71 | Se integra a la receta | Hassan la reconoce en la playa (90). |

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
