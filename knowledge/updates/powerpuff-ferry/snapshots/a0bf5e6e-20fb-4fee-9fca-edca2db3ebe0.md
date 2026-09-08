---
type: Engineering Journal
title: "PowerPuff Ferry \u2014 conciliaci\u00f3n con character sheets v2"
description: "Inspeccionar las hojas v2 de Ferry y Hassan, hacerlas la autoridad visual primaria y corregir los prompts frente a datos obsoletos."
tags: [engineering]
status: stable
author:
  id: t-0e3938282b92b9ed23e44b822569ea4a
clineflow:
  schema: 3
  topic: powerpuff-ferry
  stream: 55a2154d-fcc4-4b6a-a596-0f5ea575976f
generated:
  by: clineflow/3
  at: 2026-09-08T09:22:50Z
---

# Goal

Conciliar los prompts de las 90 páginas con las hojas de personaje v2 aprobadas, que son la autoridad visual primaria.

# Task Contract

- Intended outcome: transcribir al compilador los rasgos realmente visibles en los sheets v2 y eliminar jerarquías que los subordinen a texto obsoleto.
- Observable success criteria: los 90 prompts declaran la autoridad de las hojas v2, sus rasgos visibles coinciden y el verificador impide regresar a proporciones extremas o colores de iris incompatibles.
- Constraints and non-goals: conservar la historia, texto, estados por celda y los PNG de character sheet; no generar ni modificar arte.
- Open questions and assumptions: la cronología narrativa conserva prioridad únicamente sobre presencia temporal de utilería y vestuario de escena, no sobre identidad física.

# Execution Boundaries

- Authorized scope and exclusions: compilador, prompts derivados, guía visual, biblia, plan y verificador; se excluyen assets PNG, fotos privadas y generación externa.
- Affected interfaces, owners, and relevant side effects: futuras corridas usarán la proporción semi-chibi adulta y los looks visibles en las hojas v2.
- Escalate before changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria: no aplica; el usuario determinó explícitamente la fuente de verdad visual.
- Delegation integrator and remaining integration checks, when applicable: una sola integración local del agente principal.

# Handoff Topology

- Selection: un único corte, porque una fuente central compila todos los prompts.
- Parent integrator and final end-to-end acceptance, when applicable: agente principal; inspección visual directa de ambos sheets más recompilación y auditoría.
- Milestones: inventariar rasgos visibles; establecer jerarquía de autoridad; recompilar; probar ausencia de datos desactualizados.

# Existing Approaches

- Relevant project patterns or established approaches considered: sheets v2 aprobados, plan v2 y compilador único de las 90 páginas.
- Why the selected approach fits, or why a novel approach is necessary: especificar los datos de la hoja en el compilador evita que cada prompt los reinterprete o que un resumen antiguo gane prioridad.

# Planned Proof

- Deterministic checks to run and the rules they enforce: compilación, auditoría de continuidad, cobertura de bloque de authority y búsqueda de jerarquías y proporciones obsoletas.
- Integration checks to run: inspección visual manual de ambas hojas y muestreo de prompts de inicio, sueño y llegada de Ferry.
- Remaining judgment or coverage limits: los checks no evalúan píxeles de futuros renders; cada página nueva continúa requiriendo revisión humana contra sus hojas adjuntas.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

- Se inspeccionaron directamente `ferry-character-sheet-v2.png` y `hassan-character-sheet-v2.png`.
- Las hojas confirman para Ferry: piel cálida, ojos café oscuro, cabello largo ondulado castaño con mechas doradas, vestido coral plisado, chaqueta blanca corta, detalles dorados, tenis blanco-oro, dije de concha, moño coral y cordón rojo.
- Las hojas confirman para Hassan: piel cálida, ojos café oscuro, cabello corto oscuro, cejas oscuras, barba completa, bata blanca con camiseta azul marino, pantalón carbón y tenis azul marino; además de sus tres looks alternos y utilería científica.
- Se detectaron dos datos de producción incompatibles: la jerarquía previa subordinaba los sheets al texto y la guía definía una cabeza extrema de 45–50% que no corresponde al turnaround semi-chibi adulto v2.
- Se sustituyó esa jerarquía por un bloque de autoridad visual primaria, se actualizó la guía/biblia/plan y se recompilaron los 90 prompts.
- Se preparó el cambio completo para un único commit: corpus, compilador, prompts derivados, guía de producción, auditorías y registros OKF.

# Decisions

- Las hojas v2 aprobadas prevalecen sobre cualquier resumen textual heredado para identidad física, silueta, rostro, ojos, cabello, barba, paleta, vestuario base y accesorios.
- La cronología por página y celda mantiene prioridad sólo para objetos que aún no existen, acción y vestuario expresamente requerido por el beat.
- La proporción final es semi-chibi adulta: rostro y ojos expresivos, pero silueta madura, piernas largas legibles y cabeza no extrema.

# Verification Results

Record commands run and their factual outcomes separately from planned proof, including failures and gaps.

- Inspección visual directa de ambos PNG v2: los rasgos anteriores se observaron en sus turnarounds, expresiones, looks y bandejas de accesorios.
- `python3 -m py_compile libro/produccion/scripts/compilar_prompts_desde_corpus.py libro/produccion/scripts/verificar_continuidad.py`: correcto.
- `python3 libro/produccion/scripts/compilar_prompts_desde_corpus.py`: recompiló 90 prompts locales, el plan y el dossier técnico.
- `python3 libro/produccion/scripts/verificar_continuidad.py`: correcto; comprobó los 90 bloques de autoridad v2, ojos café oscuro y proporción semi-chibi adulta.
- Búsqueda de frases de jerarquía y proporción obsoletas fuera de archivos históricos y del propio test: sin coincidencias.

# Open Issues

- Las muestras PNG narrativas ya generadas no se alteraron. Deben regenerarse y revisarse frente a la autoridad v2 antes de aprobarlas para producción.
- Próximo paso seguro: regenerar una muestra secuencial usando los prompts revisados y revisar sus píxeles contra los sheets v2 antes de una corrida completa.

# References

- [Sheet v2 de Ferry](../../../libro/arte/referencias/ferry-character-sheet-v2.png)
- [Sheet v2 de Hassan](../../../libro/arte/referencias/hassan-character-sheet-v2.png)
- [Compilador](../../../libro/produccion/scripts/compilar_prompts_desde_corpus.py)
- [Tratamiento visual](../../../libro/produccion/tratamiento-visual-2-3.md)
- [Biblia visual](../../../libro/produccion/biblia-visual.md)
