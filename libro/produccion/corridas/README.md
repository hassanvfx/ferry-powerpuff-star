# Corridas de producción

Cada corrida se define por un JSON autocontenido: modelo, relación, resolución, fuente de prompts, referencias permitidas, carpeta de trabajos y carpeta de salidas. Las plantillas `corrida-90-2k-2-3.template.json` y `corrida-90-4k-2-3.template.json` conservan corridas independientes con la misma relación vertical 2:3.

Antes de activar una corrida se crea una copia sin `.template`, se fija `prompt_lock.sha256` con los hashes de los 90 prompts terminados y se ejecuta el preflight local. Las salidas viven en `libro/arte/salidas/<id>/`; son candidatas, nunca arte aprobado automáticamente.

El operador programado consulta una sola página por ciclo. Si ya existe su trabajo, sólo lee su estado; si terminó, descarga y valida el PNG; sólo entonces envía la siguiente. Un error detiene la corrida y requiere revisión humana.
