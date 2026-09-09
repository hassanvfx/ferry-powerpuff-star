---
type: Engineering Journal
title: "Bloqueo temporal de lanzamiento"
description: "Mostrar un overlay de cuenta regresiva antes del 10 de septiembre de 2026, con una hora artificial opt-in para pruebas."
tags: [engineering]
status: draft
author:
  id: t-0e3938282b92b9ed23e44b822569ea4a
clineflow:
  schema: 3
  topic: powerpuff-ferry
  stream: fe23bab4-b7ad-4139-b09a-d1f550120b4e
generated:
  by: clineflow/3
  at: 2026-09-09T01:00:00Z
---

# Goal

Bloquear toda interacción con el lector antes de la fecha de lanzamiento mediante un overlay autónomo con su cuenta regresiva.

# Task Contract

- Intended outcome: mostrar una capa fullscreen antes del 10 de septiembre de 2026 a las 00:00 en Ciudad de México, con contracubierta a la izquierda, portada a la derecha y una cuenta regresiva humana.
- Observable success criteria: sin query el overlay depende del reloj real; `?bypass-wait=true` inyecta una hora previa artificial para forzarlo; al alcanzar la fecha se elimina sin cambiar la lógica del player.
- Constraints and non-goals: HTML/CSS/JS plano; el lock es un módulo aislado que no modifica navegación, localStorage, guías, lightbox ni el manifest; los dos artes son sólo decorativos y no interactivos.
- Open questions and assumptions: la fecha de lanzamiento confirmada es 2026-09-10 00:00 America/Mexico_City; CDMX se expresa con offset UTC−06:00.

# Execution Boundaries

- Authorized scope and exclusions: un módulo nuevo de lock, `index.html`, estilos, publicador, pruebas, guía de operación, `docs/` generado y knowledge; se excluyen manuscrito, arte narrativo, prompts y workflow de Pages.
- Affected interfaces, owners, and relevant side effects: `docs/` incluye el módulo; el query `bypass-wait=true` sólo ajusta el reloj efectivo dentro de la capa para test.
- Escalate before changing requirements, external behavior, authority, ownership, dependencies, or acceptance criteria: cambiar la fecha o zona de lanzamiento, exponer interacciones en la capa o persistir el bypass.
- Delegation integrator and remaining integration checks, when applicable: sin delegación; Codex integra la capa, artifact y comprobación en ambos breakpoints.

# Handoff Topology

- Selection: un único handoff porque el módulo autónomo, su overlay y el artifact estático forman un cambio cohesivo.
- Parent integrator and final end-to-end acceptance, when applicable: Codex comprueba modo real/bypass, desktop/móvil y el workflow de Pages.
- Milestones: no aplica; el módulo se retira por sí solo en la fecha y no tiene consumidores fuera del documento publicado.

# Existing Approaches

- Relevant project patterns or established approaches considered: el player ya consume `manifest.json` con rutas relativas; `docs/` se publica como output estático y el publicador copia una lista explícita de archivos fuente.
- Why the selected approach fits, or why a novel approach is necessary: un módulo paralelo carga sólo los dos assets de cubierta y marca el player como inerte; así se encapsula sin introducir estados condicionales en `app.js`.

# Planned Proof

- Deterministic checks to run and the rules they enforce: sintaxis JS, pruebas del publicador que exigen el nuevo módulo, manifest/asset checks, `git diff --check` y validadores OKF.
- Integration checks to run: navegador local normal antes de la fecha con capa y cuenta real; `?bypass-wait=true` con una hora artificial, contador, orden de cubiertas y player no interactivo; validar desktop y móvil.
- Remaining judgment or coverage limits: la cuenta termina cuando el navegador llega al instante configurado; no se simulará esperar hasta la liberación en tiempo real.

# Status

- [x] Planned
- [x] In progress
- [x] Complete

# Work Log

- Se añadió `release-lock.js` como módulo independiente: obtiene portada y contraportada del manifest, marca el player inerte mientras falte tiempo y se elimina al llegar a la fecha.
- El publicador copia explícitamente el módulo junto con el player, por lo que `docs/` conserva el artifact estático y no incorpora nueva lógica de generación.
- Se regeneró `docs/` con la edición V11 de 90 páginas.

# Decisions

- `bypass-wait=true` ancla el reloj de prueba una hora antes de la liberación y después avanza al mismo ritmo que el reloj real; no toca fecha de sistema ni persiste estado.

# Verification Results

Record commands run and their factual outcomes separately from planned proof, including failures and gaps.

- `python3 -m unittest libro.produccion.tests.test_publicar_comic.py`: 7 pruebas correctas.
- Se validó sintaxis con `node --check` para `release-lock.js` y `app.js`; se comprobó que el artifact contiene `release-lock.js`, fecha `2026-09-10T00:00:00-06:00`, manifest V11 de 90 páginas y cero PNG publicados.
- Navegador local: sin query mostró el lock y una cuenta real hasta el 10 de septiembre; con `?bypass-wait=true` mostró una cuenta artificial de una hora. En escritorio se verificó contracubierta izquierda, portada derecha y contador; en viewport móvil la capa ocupó el viewport. La accesibilidad sólo expuso el contenedor de cuenta regresiva y el player quedó inerte.
- `git diff --check`: correcto.

# Open Issues

# References

- [Player fuente](../../../libro/produccion/player/)
- [Guía de publicación](../../../libro/produccion/publicar-comic.md)
