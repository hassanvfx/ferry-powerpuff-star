---
type: Engineering Journal
title: "PowerPuff Ferry \u2014 corpus narrativo y prompts de c\u00f3mic"
description: "Desarrollar las 32 p\u00e1ginas 6\u00d79 como c\u00f3mic de 2 a 6 vi\u00f1etas y traducir el corpus narrativo a prompts por p\u00e1gina."
tags: [engineering]
status: draft
author:
  id: t-0e3938282b92b9ed23e44b822569ea4a
clineflow:
  schema: 3
  topic: powerpuff-ferry
  stream: 2b28abab-d596-4e5f-8e63-395e04eaeef1
generated:
  by: clineflow/3
  at: 2026-09-08T07:44:02Z
---

# Goal

Crear el corpus narrativo de producción para las 90 páginas interiores y convertirlo en prompts de imagen de una página cada uno.

# Task Contract

- Intended outcome: un corpus panel a panel y una cola de prompts sincronizada para un cómic vertical 6×9 de 90 páginas, con entre 2 y 6 viñetas por página.
- Observable success criteria: las 90 páginas tienen de 2 a 6 viñetas; el corpus conserva la historia original de laboratorio, sueño, receta, revelación y playa; los 29 ingredientes siguen teniendo una viñeta trazable; cada prompt describe el mismo número de viñetas y los mismos beats.
- Constraints and non-goals: mantener diseños chibi-superhero originales de adultos y lenguaje de cómic puramente visual (sin globos ni texto legible), con las referencias privadas sólo como mecanismo local ya configurado. No generar imágenes, no subir fotos, no consumir créditos, no maquetar ni imprimir.
- Open questions and assumptions: se conservan 32 páginas y la dirección de personaje vigente. La revisión humana seguirá decidiendo si el generador reproduce correctamente los diálogos y si alguna página requiere una segunda pasada de dirección de arte.

# Execution Boundaries

- Authorized scope and exclusions: actualizar documentación editorial, plan local y prompts locales. Se excluyen servicios externos, las fotos privadas, arte generado y PDF.
- Affected interfaces, owners, and relevant side effects: sólo `libro/manuscrito/`, `libro/produccion/` y conocimiento persistente; Hassan mantiene la aprobación creativa final.
- Escalate before changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria: el autor autorizó explícitamente el cambio de 32 a 90 páginas; pedir dirección antes de alterar el reparto, el uso de fotos o la producción externa.
- Delegation integrator and remaining integration checks, when applicable: no hay delegación; Codex integra corpus, mapa y prompts.

# Handoff Topology

- Selection: un solo hito cohesivo: el corpus es la fuente de verdad y los prompts son su traducción directa.
- Parent integrator and final end-to-end acceptance, when applicable: Codex comprobará conteos, ids, ingredientes y correspondencia; el autor aprobará el resultado visual cuando se generen pilotos.
- Milestones: no aplica.

# Existing Approaches

- Relevant project patterns or established approaches considered: el guion visual de 32 páginas y la cola de prompts ya existentes; la página a sangre y los montajes de 7–9 viñetas.
- Why the selected approach fits, or why a novel approach is necessary: un corpus separado evita que el prompt sea la única especificación narrativa. La expansión a 90 páginas descomprime los momentos del relato original para que cada gesto se lea a 6×9 sin recurrir a páginas de una viñeta ni a montajes de 7–9.

# Planned Proof

- Deterministic checks to run and the rules they enforce: comprobar JSON, 90 ids únicos, 2–6 viñetas por página, 29 ingredientes una vez cada uno, existencia de 90 prompts y validadores OKF.
- Integration checks to run: contrastar corpus, mapa de ingredientes, plan y prompts para que el orden y continuidad concuerden.
- Remaining judgment or coverage limits: sólo una imagen piloto puede confirmar si la composición, texto y rostros resultan legibles y atractivos a tamaño impreso.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

- Se recuperó el contrato vigente: 32 páginas verticales 6×9, personajes adultos originales y 29 cualidades obligatorias.
- El autor pidió desarrollar todas las páginas como cómic legible de entre 2 y 6 viñetas y establecer el corpus antes de reformular los prompts.
- El autor amplió explícitamente la extensión a 90 páginas y confirmó que el formato es un cómic puramente visual con divisiones de viñeta, contado por imagen.
- Se escribió `libro/manuscrito/06-corpus-narrativo-90-paginas.md` como fuente de verdad: define formato, estilo, arco y beats de las 90 páginas.
- Se añadió el mapa de 29 ingredientes para las páginas 66–77 y se actualizó el brief, la biblia visual y la navegación para señalar los archivos de 32 páginas como antecedentes.
- Se creó `compilar_prompts_desde_corpus.py`, que generó `plan-de-imagenes-90.json` y 90 prompts locales bajo `libro/produccion/prompts-90/`.

# Decisions

- Las páginas anteriormente compuestas por una viñeta se resuelven en dos beats; los bloques de 7 y 9 viñetas se redistribuyen para que el rango sea siempre 2–6.
- La nueva extensión es de 90 páginas. Las 29 cualidades se muestran una por viñeta en una secuencia larga de preparación, no comprimida en cinco páginas.
- La última dirección del autor sustituye el diálogo por narrativa visual: no habrá globos, cartelas ni texto legible dentro de las imágenes; la nota de la receta permanece deliberadamente ilegible.
- El plan anterior de 32 páginas se preserva como antecedente, pero el corpus y el plan de 90 páginas son las únicas fuentes de producción vigentes.

# Verification Results

Record commands run and their factual outcomes separately from planned proof, including failures and gaps.

- `python3 libro/produccion/scripts/compilar_prompts_desde_corpus.py`: compiló 90 prompts locales desde el corpus sin acceder a red ni a servicios de imagen.
- Validación local de `plan-de-imagenes-90.json`: 90 ids consecutivos, 90 prompts existentes y cada página tiene entre 2 y 6 beats/viñetas.
- Validación local de corpus y mapa: 90 encabezados de página y 29 filas de ingrediente.
- `git diff --check`: sin errores de espacios.

# Open Issues

- La calidad de composición, legibilidad a 6×9 y coherencia de personajes necesita un piloto visual aprobado antes de cualquier cola externa.
- El ejecutor de generación existente aún apunta al plan de 32 páginas; deberá configurarse o ampliarse explícitamente para consumir `plan-de-imagenes-90.json` sólo tras la aprobación de producción externa.

# References
