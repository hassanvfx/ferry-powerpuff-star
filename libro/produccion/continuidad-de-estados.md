# Continuidad de estados — auditoría retrospectiva

Este documento no describe estilo: fija qué existe, qué no existe y cuándo cambia. Se leyó el arco desde la llegada a la playa hacia el laboratorio inicial para rastrear el primer origen permitido de cada motivo. El [compilador](scripts/compilar_prompts_desde_corpus.py) convierte estos estados en bloqueos visibles dentro de cada prompt y del plan.

## Regla de producción

Una referencia de la página anterior conserva apariencia; **no prueba cronología**. Cada prompt debe declarar el estado requerido y las ausencias relevantes. Un prop que todavía no existe no se añade como decoración, presagio, accesorio ni SFX visual.

## Estados canónicos de los objetos recurrentes

| Elemento | Origen permitido | Transiciones obligatorias | Prohibición clave |
| --- | --- | --- | --- |
| Monitor | 01 / 2 encendido con gráficos azules | 02 / 1 aún encendido → 02 / 2 Hassan pulsa y se vuelve negro → 02 / 3 permanece apagado | Jamás aparece apagado antes de 02 / 2. |
| Matraz | 01 / 3 vacío y transparente | Se mantiene vacío; 64 / 3 recibe sólo una chispa de fondo; 66 / 2 nace el primer líquido celeste | No tiene líquido, vapor ni magia activa antes de 66 / 2. |
| Punto rosa-dorado | 01 / 3, apenas un reflejo puntual | 07 / 3 es partícula; 09 / 2 toma forma de estrella en sueño; 84 / 2 nace como estrella física de laboratorio | Antes de 09 no es estrella dibujada; antes de 84 no hay estrella física en el laboratorio. |
| Hilo rojo | 14 / 3, motivo casi invisible dentro del sueño | 31–35 acompaña la nota onírica; 40 / 3 aparece físicamente en la esquina de la nota; 56 / 2 aparece el carrete físico | No existe en realidad durante 01–39; no hay carrete antes de 56 / 2. |
| Nota | 32, en el sueño y con escritura ilegible | 40 / 1 aparece físicamente pegada al monitor; 41 se despega; 45–46 se vuelve receta visual | No existe como objeto físico antes de 40. |
| Lupa | 44 / 1, Hassan la toma para investigar | Permanece como herramienta de búsqueda y receta cuando el beat la llama | No aparece antes de 44. |
| Concha | 57 / 1, Hassan la encuentra en la casa | 57 / 3 emite gota turquesa; 71 / 3 entra como ingrediente; 90 / 2 reaparece en playa | No se anticipa como souvenir en el laboratorio inicial. |

## Bloque crítico: páginas 01–02

| Página / celda | Estado que debe verse | Ausencias obligatorias |
| --- | --- | --- |
| 01 / 1 | Fachada nocturna; sólo una ventana blanca encendida. | Sin hilo rojo, carrete, nota, lupa, concha, estrella ni destello mágico. |
| 01 / 2 | Monitor encendido con gráficos azules abstractos; Hassan termina su medición. | Sin objetos del sueño ni ingredientes futuros. |
| 01 / 3 | Matraz vacío y transparente; sólo un punto rosa-dorado microscópico de reflexión. | Sin hilo/curva roja, carrete, estrella con puntas, llave, nota o emisión mágica. |
| 02 / 1 | El mismo monitor continúa encendido y muestra gráficos azules. | Sin hilo, carrete, estrella, nota, lupa, llave ni props mágicos. |
| 02 / 2 | Hassan pulsa el botón del mismo monitor: inicia encendido y termina apagado/negro en esta única celda. | Sin adelantar objetos de la receta. |
| 02 / 3 | El monitor ya está negro/apagado; Hassan mira el reloj. | Sin hilo, carrete, estrella, nota, lupa, llave ni props mágicos. |

## Auditoría inversa antes de producir una página

1. Partir del prop visible y buscar su primera fila de origen en esta tabla.
2. Confirmar que su estado previo coincide con la última transición del prompt anterior.
3. Si no hay beat que lo introduzca, prohibirlo explícitamente: no se usa como decoración para “hacerla más mágica”.
4. Revisar la página resultante contra sus celdas, no sólo contra la página anterior completa. Una celda puede cambiar un estado que las demás no cambian.

La auditoría automatizada prueba que los bloqueos se compilaron; la revisión humana prueba que la imagen los obedeció.
