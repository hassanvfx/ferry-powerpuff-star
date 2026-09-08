# Sistema de produccion

Este sistema convierte la historia en **90 páginas individuales de cómic vertical 6×9** y, una vez aprobadas, las ensambla como interior de Lulu de 6×9 pulgadas. El corpus y la cola local actuales viven en `../manuscrito/06-corpus-narrativo-90-paginas.md` y `plan-de-imagenes-90.json`.

El [tratamiento visual 2:3](tratamiento-visual-2-3.md) es obligatorio para todas las páginas: mantiene la lectura de ojos, silueta, color, acción y lettering sin copiar una franquicia.

## Fuente actual: corpus a prompts

Los 90 prompts de `prompts-90/` se generan localmente desde el corpus y el guion técnico; no activan Kie ni transmiten referencias. Cada prompt define la retícula, sus celdas, cámara, acción y una posición segura de lettering. Sólo el valor de `Texto impreso exacto` se dibuja entre comillas dobles: las etiquetas técnicas jamás son letras dentro de la viñeta. Si se cambia el corpus o el texto técnico, recompilar así:

```bash
python3 libro/produccion/scripts/compilar_prompts_desde_corpus.py
```

El plan y los prompts previos de 32 páginas se conservan sólo como antecedente. Antes de ejecutar cualquier generación externa, el ejecutor debe configurarse explícitamente para leer `plan-de-imagenes-90.json` y se requiere la autorización vigente para las fotos privadas.

## Continuidad secuencial

La página 01 no usa una página narrativa previa. De la página 02 en adelante, el prompt recibe la página anterior **aprobada** como referencia adicional. Esta referencia preserva diseño, paleta, luz, escala, vestuario y motivos; no autoriza repetir la composición, los paneles, poses, acción, diálogos, SFX, fondos u objetos. El brief de la página actual manda siempre.

En modo `--live`, el ejecutor bloquea cada página si no existe el archivo aprobado de su predecesora en `arte-aprobado/`. Por ello, la producción debe ser secuencial: generar → revisar → mover a `arte-aprobado/` → generar la página siguiente. Los dry runs no exigen esa imagen y nunca la transmiten.

La referencia visual no controla por sí sola el inventario de la historia. La [auditoría de estados](continuidad-de-estados.md) fija el origen, ausencia y transición de monitor, matraz, hilo, nota, lupa, carrete, concha y estrella. El compilador inserta sus bloqueos por página y por celda; antes de aprobar una imagen, revísala contra esa tabla.

La [auditoría retrospectiva 90→01](auditoria-retroactiva-90.md) recorre las 90 páginas en orden inverso y enlaza cada estado con su predecesora inmediata. Se regenera junto con los prompts y se comprueba sin llamar a ningún servicio externo:

```bash
python3 libro/produccion/scripts/verificar_continuidad.py
```

## Personajes y privacidad

`referencias.local.json` apunta a las tres fotos entregadas por el autor: una de Hassan y dos de Ferry. Está ignorado por Git; las fotos no se copian al repositorio. La referencia de estilo aprobada vive en `../arte/referencias/chibi-superhero-comic-style-reference.png` y se adjunta siempre; las hojas aprobadas de producción viven en `../arte/referencias/ferry-character-sheet-v2.png` y `../arte/referencias/hassan-character-sheet-v2.png`, y el ejecutor añade la correspondiente a cada personaje. Al ejecutar Kie en modo real, el CLI sube temporalmente sólo las referencias requeridas por cada página.

La [biblia visual](biblia-visual.md) fija la continuidad de personajes, color, objetos y revisión de cada página.

Para una prueba que no transmite fotografías privadas, añade `--approved-references-only`; entonces sólo se adjuntan la referencia de estilo y las hojas v2 aprobadas.

## Generar páginas con Kie

Por defecto se ejecuta una prueba que no gasta créditos ni sube fotos:

```bash
python3 libro/produccion/scripts/generar_paginas.py \
  --plan libro/produccion/plan-de-imagenes-90.json \
  --page 01-el-laboratorio-al-anochecer
```

### Primero: hojas de personaje

Las hojas v2 ya están aprobadas y son la referencia actual de producción. `plan-de-personajes.json` conserva los prompts v1; `plan-de-personajes-v2.json` conserva el brief y las rutas de las láminas finales.

```bash
python3 libro/produccion/scripts/generar_paginas.py \
  --plan libro/produccion/plan-de-imagenes-90.json \
  --page 01-el-laboratorio-al-anochecer
```

La [biblia visual](biblia-visual.md) define el estilo original de superhéroe chibi retro y cómo las hojas v2 aprobadas alimentan las páginas de historia.

Después de revisar el prompt impreso, el modo real envía el trabajo asíncrono y guarda el identificador en `libro/produccion/jobs/`:

```bash
python3 libro/produccion/scripts/generar_paginas.py \
  --plan libro/produccion/plan-de-imagenes-90.json \
  --page 13-salto-de-ferry \
  --live
```

Para generar toda la cola se usa `--all --live`. Cada página usa `gpt-image-2`, proporción vertical 2:3 (equivalente a 6×9) y resolución 2K. Kie recibe las referencias locales mediante `--image`; no guardes la clave de Kie en este proyecto.

Para esperar un trabajo y obtener su URL:

```bash
/Users/hassan/repos/kie-api/.venv/bin/kie-cli wait --job-file libro/produccion/jobs/07-ferry-porrista.json --json
```

Descarga el resultado aprobado como `arte-aprobado/07-ferry-porrista.png`. El ensamblador exige exactamente una imagen aprobada por cada id del plan.

## Adaptacion a Lulu 6×9

Cada imagen ya es una página vertical 2:3. El ensamblador la coloca a sangre en la página PDF de 6.25×9.25 in; el ajuste de sangrado recorta sólo 0.0625 in arriba y abajo, por eso todos los elementos importantes quedan a un 10% de los bordes.

- Tamaño final: 6×9 in; PDF con sangrado: 6.25×9.25 in, sin marcas de corte.
- Fuente mínima: 1,875 px de ancho, equivalente a 300 ppi a 6.25 in. El ensamblador rechaza fuentes menores.
- Las páginas se exportan individualmente, nunca como dobles páginas.

Cuando todas las placas estén aprobadas:

```bash
/Users/hassan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 libro/produccion/scripts/ensamblar_lulu.py
```

El PDF aparece en `libro/produccion/salida/`. Ese runtime ya incluye Pillow y ReportLab. La [guía de cubierta](cubierta-y-metadata.md) explica el paso final: Lulu necesita una plantilla cuyo lomo depende del número final de páginas, papel y encuadernación.

## Control de calidad

1. Revisar cada placa: rostros coherentes, paneles claros y texto en español idéntico al prompt, sin texto inventado.
2. Renderizar el PDF a PNG y comprobar que no haya recorte ni franjas blancas.
3. En Lulu, seleccionar interior vertical 6×9 y subir el PDF como páginas individuales.
4. Revisar la previsualización de Lulu antes de comprar.
