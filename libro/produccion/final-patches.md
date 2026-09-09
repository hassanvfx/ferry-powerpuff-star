---
type: Production Guide
---

# Parches finales de imagen

Los parches sirven para corregir una página final ya generada sin tocar su PNG
de origen, su guía ni sus prompts fuente. Son un **postpaso manual**: no están
conectados al gestor de colas, no crean cron ni heartbeat y sólo consumen
créditos con `--live`.

La fuente de intención es
[`corridas/final-patches.json`](corridas/final-patches.json). El operador es
[`scripts/parchear_finales.py`](scripts/parchear_finales.py).

## Contrato del payload

Cada solicitud adjunta exactamente una imagen: la final existente de la misma
página. No adjunta guía, fichas de personajes, estilos, referencias candidatas
ni el prompt narrativo fuente. Esos materiales pueden reintroducir instrucciones
que contradicen una corrección local.

El prompt de parche debe describir sólo el cambio solicitado y ordenar que se
conserve todo lo demás de la imagen: composición, viñetas, poses, personajes,
fondos, paleta y texto no afectado. El PNG de origen nunca se modifica.

## Manifiesto

El formato actual es:

```json
{
  "schema_version": 1,
  "patches": [
    {
      "run_id": "corrida-90-2k-2-3-v11-4k-opcional",
      "page_id": "20-yohi-y-la-hoja-fresca",
      "resolution": "2K",
      "enabled": true,
      "replace_existing": false,
      "instruction": "Describe con precisión el único cambio requerido."
    }
  ]
}
```

- `run_id`: nombre de la corrida cuya configuración declara las rutas.
- `page_id`: nombre de la página sin `.png`.
- `resolution`: `2K` abre `finales-2k/<page_id>.png`; `4K` abre
  `finales-4k/<page_id>.png`. La salida conserva esa resolución.
- `enabled`: sólo las entradas en `true` se procesan.
- `instruction`: corrección concreta, idealmente con el texto exacto que debe
  aparecer o desaparecer.
- `replace_existing`: permite sustituir explícitamente un PNG previo en
  `final-patched`. Nunca borra la final base; archiva el recibo anterior bajo
  `jobs/<corrida>/final-patched/retries/`.

Sólo puede haber un parche habilitado para una misma combinación de corrida y
página. Una final parcheada ya descargada con el mismo prompt y recibo se
considera completa incluso si `replace_existing` sigue en `true`; por tanto un
poll normal no la reenvía.

## Ejecutar y reanudar

Primero inspecciona el payload sin red ni escritura:

```bash
python3 libro/produccion/scripts/parchear_finales.py \
  --manifest libro/produccion/corridas/final-patches.json \
  --dry-run
```

Para enviar los parches habilitados:

```bash
python3 libro/produccion/scripts/parchear_finales.py \
  --manifest libro/produccion/corridas/final-patches.json \
  --live
```

Para consultar únicamente el recibo actual y descargar una salida ya
terminada, sin posibilidad de borrar, sobrescribir o enviar otro trabajo:

```bash
python3 libro/produccion/scripts/parchear_finales.py \
  --manifest libro/produccion/corridas/final-patches.json \
  --live --poll-only
```

`--wait --interval-seconds 30` permite que la misma invocación haga polling;
para una revisión cautelosa se recomienda ejecutar después `--poll-only`.

El modo puntual sin manifiesto acepta una ruta final directa. Por defecto exige
una ruta dentro de `finales-2k`; `--4k` exige `finales-4k`:

```bash
python3 libro/produccion/scripts/parchear_finales.py \
  --image libro/arte/salidas/<corrida>/finales-2k/<pagina>.png \
  --instruction "Corrección específica" \
  --live
```

Para reemplazar una derivada existente en este modo puntual hay que declarar
además `--replace-existing`.

## Salidas y publicación web

La derivada se guarda en:

```text
libro/arte/salidas/<corrida>/final-patched/<pagina>.png
```

`publicar_comic.py` selecciona una fuente por página, no por corrida completa,
en esta prioridad:

1. `final-patched/<pagina>.png`
2. `finales-4k/<pagina>.png`
3. `finales-2k/<pagina>.png`
4. `finales/<pagina>.png` sólo para corridas heredadas

Así una sola corrección aprobada puede publicarse junto con las demás finales
4K o 2K sin copiar archivos. El publicador conserva las validaciones de guías,
PNGs, secuencia de páginas y número par.

## Revisión editorial

Kie puede terminar un trabajo sin obedecer completamente el cambio. Antes de
publicar, inspecciona el PNG en `final-patched`, comprueba el literal corregido
cuando haya texto y confirma que no cambió ningún elemento relevante. Sólo la
revisión humana decide si ese archivo se conserva o se reemplaza con una nueva
corrección explícita.
