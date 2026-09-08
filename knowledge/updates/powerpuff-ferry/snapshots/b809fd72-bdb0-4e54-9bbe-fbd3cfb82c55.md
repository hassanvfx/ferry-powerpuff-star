---
type: Engineering Journal
title: "Biblia de continuidad de criaturas y lugares"
description: "Inventariar las criaturas y locaciones recurrentes, generar fichas visuales independientes y adjuntar s\u00f3lo las referencias pertinentes a cada p\u00e1gina de la cola."
tags: [engineering]
status: draft
author:
  id: t-0e3938282b92b9ed23e44b822569ea4a
clineflow:
  schema: 3
  topic: powerpuff-ferry
  stream: 3b2c03f5-62b0-4ee5-85a4-837fd3edb70f
generated:
  by: clineflow/3
  at: 2026-09-08T19:02:00Z
---

# Goal

Crear una biblia de continuidad que permita a la producción adjuntar las mismas fichas de criaturas y lugares pertinentes en cada página, además de las hojas v2 de Hassan y Ferry.

# Task Contract

- Intended outcome: inventariar los cuatro seres recurrentes y cinco entornos del cómic, generar una ficha visual independiente por identidad y conectar un índice de referencias con las 90 páginas y el ejecutor local.
- Observable success criteria: el catálogo define propósito, estado, ruta y páginas para Zeus, Yohi, los dos caracoles, la araña, laboratorio/oficina, casa, escenario onírico, jardín protector de Ferry y costa; cada página declara los assets que necesita; una ejecución en seco muestra sólo sus referencias aprobadas; y las nuevas fichas quedan en el workspace para revisión humana.
- Constraints and non-goals: conservar sin cambios las hojas v2 aprobadas de Hassan y Ferry, no subir fotos privadas ni ejecutar Kie, no declarar automáticamente aprobada una imagen nueva y no incorporar los 29 ingredientes como personajes persistentes.
- Open questions and assumptions: “oficina” se modela como el área de trabajo dentro del laboratorio de Hassan; el “lugar especial de Ferry” es el jardín protector del sueño. Las fichas generadas se marcarán como candidatas hasta una revisión humana explícita.

# Execution Boundaries

- Authorized scope and exclusions: catálogo de continuidad, planes/prompt compilados, validador y ejecutor local, más PNG nuevos bajo `libro/arte/referencias/`. Quedan excluidos Kie, créditos, fotos privadas, aprobación automática de arte y las corridas existentes del autor.
- Affected interfaces, owners, and relevant side effects: `plan-de-imagenes-90.json` ganará ids de referencias de continuidad; `generar_paginas.py` resolverá el catálogo y podrá incluir candidatos sólo con una opción explícita. Hassan conserva la aprobación creativa de cada ficha.
- Escalate before changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria: pedir dirección antes de tratar una ficha candidata como aprobada por defecto, alterar especie/raza canónica o añadir una criatura/lugar no sustentado por el guion.
- Delegation integrator and remaining integration checks, when applicable: no hay delegación; Codex integra catálogo, compilador, ejecutor, assets y pruebas.

# Handoff Topology

- Selection: cadena de tres hitos: inventario, assets, y conexión de ejecución. Las salidas se consumen en ese orden y cada una tiene una prueba local distinta.
- Parent integrator and final end-to-end acceptance, when applicable: Codex integra; la aceptación final compone catálogo válido, imágenes presentes, prompts regenerados y dry-run. Hassan revisa visualmente y decide qué assets promover a aprobados.
- Milestones: (1) inventario: corpus y plan actuales → catálogo con asignaciones; prueba: cobertura de 90 páginas. (2) fichas: catálogo → nueve PNG candidatos; prueba: rutas y dimensiones. (3) integración: catálogo y PNG → referencias por página en el plan y payload seco; prueba: compilación, auditoría y selección de adjuntos. Si un asset no se genera, se mantiene como candidato faltante y el modo de sólo aprobados sigue funcional.

# Existing Approaches

- Relevant project patterns or established approaches considered: las hojas v2 se listan por `references` en el plan, el compilador tiene bloque de especies y el ejecutor adjunta imágenes aprobadas de forma determinista.
- Why the selected approach fits, or why a novel approach is necessary: un catálogo versionado evita dejar rutas y reglas repartidas entre prompts y código, y conserva la regla existente de que los assets sin revisión humana no se adjuntan por defecto.

# Planned Proof

- Deterministic checks to run and the rules they enforce: validar JSON, 90 páginas, existencia y dimensiones de assets, ausencia de adjuntos candidatos en modo estricto y presencia sólo donde el catálogo los ordena.
- Integration checks to run: recompilar los prompts, ejecutar `verificar_continuidad.py` y un dry-run representativo de criatura, jardín, laboratorio y playa.
- Remaining judgment or coverage limits: las especies y entornos pueden comprobarse textualmente, pero la fidelidad artística de cada nueva ficha requiere la revisión humana de Hassan antes de la producción definitiva.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

- Se inventariaron cuatro criaturas persistentes (Zeus, Yohi, dos caracoles y una araña) y cinco lugares recurrentes (laboratorio/oficina, casa, escenario onírico, jardín protector de Ferry y costa). Los 29 ingredientes se mantuvieron como utilería, no como personajes.
- Se crearon nueve fichas candidatas bajo `libro/arte/referencias/`, tomando exclusivamente como referencias de estilo y layout las hojas v2 de Hassan, Ferry y la lámina de tratamiento. Zeus se regeneró como v3 con la retícula común, collar azul marino y placa `Zeus`.
- Se creó `libro/produccion/indice-de-continuidad.json` como fuente única de rutas, descripciones, estado de revisión y páginas aplicables. El ejecutor ahora materializa una sección `REFERENCIAS VISUALES ADJUNTAS` que identifica cada lámina enviada y su uso de continuidad.

# Decisions

- Las fichas nuevas permanecen con `status: candidate`; sólo se adjuntan con `--include-candidate-continuity-assets`. Esta barrera conserva la aprobación humana antes de cualquier envío real a Kie.
- Las tres imágenes suministradas por el autor se usan exclusivamente como estilo y estructura de lámina al generar criaturas y lugares; no se copian identidades, rostros, vestuario ni contenido narrativo.

# Verification Results

Record commands run and their factual outcomes separately from planned proof, including failures and gaps.

- `python3 -m py_compile` de `generar_paginas.py` y `verificar_continuidad.py`: correcto.
- `python3 libro/produccion/scripts/verificar_continuidad.py`: correcto; comprueba rutas, estados, asignaciones representativas y que Zeus use la ficha v3.
- Prueba de materialización sin Kie: las páginas 01, 16 y 90 enumeraron respectivamente laboratorio/oficina, Zeus+jardín y costa; la página 16 omitió Zeus cuando no se solicitó incluir candidatos.
- `jq empty libro/produccion/indice-de-continuidad.json` y `git diff --check` sobre los archivos de este cambio: correctos.

# Open Issues

- Hassan debe revisar visualmente las nueve fichas y decidir cuáles promover de `candidate` a `approved` antes de usarlas por defecto en una corrida real.

# References

- [Índice de continuidad](../../../libro/produccion/indice-de-continuidad.json)
- [Ejecutor](../../../libro/produccion/scripts/generar_paginas.py)
- [Verificador](../../../libro/produccion/scripts/verificar_continuidad.py)
