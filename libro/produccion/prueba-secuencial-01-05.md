# Prueba secuencial 01–05

Esta prueba genera las primeras cinco páginas en orden lineal, para comprobar continuidad visual sin convertir las imágenes de prueba en arte aprobado de producción.

| Página | Referencias adjuntas |
| --- | --- |
| 01 | Referencia de estilo aprobada + hoja v2 de Hassan |
| 02 | Referencia de estilo aprobada + hoja v2 de Hassan + resultado de 01 |
| 03 | Referencia de estilo aprobada + hoja v2 de Hassan + resultado de 02 |
| 04 | Referencia de estilo aprobada + hoja v2 de Hassan + resultado de 03 |
| 05 | Referencia de estilo aprobada + hoja v2 de Hassan + resultado de 04 |

La referencia de la página anterior sólo conserva identidad, vestuario, accesorios, paleta y ambiente. La composición, distribución de celdas, poses, acción y lettering los determina siempre el prompt de la página actual.

Usar `--continuity-preview-dir <carpeta>` hace que el generador tome el PNG previo de esa carpeta de pruebas. Esa opción no escribe en `arte-aprobado/`; para la producción final, sin esa opción, el proceso continúa exigiendo el predecesor aprobado declarado en el plan.
