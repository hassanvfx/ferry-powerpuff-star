---
type: Production Guide
---

# Publicar el visor web

El contenido que GitHub Pages sirve vive en `docs/` y se reconstruye sólo
cuando se quiere publicar una edición concreta. No se edita esa carpeta a mano.

## Requisitos

```bash
python3 -m pip install -r libro/produccion/requirements-publicador.txt
```

La portada, la contracubierta, el avatar de Hassan del modo guía y el avatar de
Ferry que devuelve a portada son obligatorios. Se guardan en
`libro/arte/referencias/ferry-powerpuff-star-cover.png` y
`libro/arte/referencias/ferry-powerpuff-star-back-cover.png` y
`libro/arte/referencias/ferry-guide-avatar.png` y
`libro/arte/referencias/ferry-home-avatar.png`.

## Crear una edición

Para elegir una corrida explícita:

```bash
python3 libro/produccion/scripts/publicar_comic.py \
  --run corrida-90-2k-2-3-v7-guia
```

Para elegir la corrida válida cuyos finales tengan la modificación más reciente:

```bash
python3 libro/produccion/scripts/publicar_comic.py --latest
```

El comando sólo sustituye `docs/` después de validar que hay portada,
contracubierta, ambos avatares y páginas PNG consecutivas desde 01 en número par. Para
cada página seleccionada debe existir una guía PNG del mismo número en `guias/`;
guías válidas de páginas aún no finalizadas se permiten. Para cada página, el
publicador escoge la primera capa que exista en este orden: `final-patched/`,
`finales-4k/`, `finales-2k/` y, sólo por compatibilidad con corridas anteriores,
`finales/`. Una guía
faltante, corrupta, duplicada o con nombre inválido detiene la publicación y
preserva el `docs/` anterior. El manifest deja registrada la corrida, sus assets
finales, guías y avatares optimizados como WebP.

### Edición parcial explícita

Sólo si el autor decide publicar una corrida incompleta, se puede conservar la
numeración disponible sin inventar ni renumerar páginas:

```bash
python3 libro/produccion/scripts/publicar_comic.py \
  --run corrida-90-2k-2-3-v9-referencias-guia \
  --allow-gaps
```

Este override sigue exigiendo que cada final tenga una guía del mismo nombre y
que el total publicado sea par. Las páginas ausentes quedan fuera del manifest;
por eso el lector puede mostrar rangos no consecutivos, como `27–29`. Nunca se
usa con `--latest`, que continúa seleccionando sólo corridas completas.

## Revisar antes de publicar

El directorio `docs/` contiene el sitio final y se debe versionar. Para una
vista local:

```bash
python3 -m http.server 4173 --directory docs
```

Abre `http://localhost:4173/`. En desktop se avanza por dobles páginas con los
botones, clic lateral o flechas; el avatar circular de Ferry vuelve a portada y
no aparece en ella. El avatar de Hassan alterna las páginas interiores entre
final y guía durante la sesión. A menos de 768 px el lector cambia a un feed
vertical con scroll-snap, Ferry queda arriba a la izquierda y Hassan arriba a
la derecha. La última posición se guarda por edición en el navegador; el modo
guía vuelve a final al recargar.

Las pruebas del publicador se ejecutan así:

```bash
python3 -m unittest libro/produccion/tests/test_publicar_comic.py
```

## Primer despliegue en GitHub

1. Crea o conecta el repositorio remoto y publica la rama `main`.
2. En **Settings → Pages**, elige **GitHub Actions** como fuente.
3. Revisa y haz commit de `docs/`, las cubiertas, el player, el publicador y
   `.github/workflows/deploy-pages.yml`.
4. Haz push a `main`. El workflow sólo se activa si cambió `docs/` o el propio
   workflow, y despliega el artifact construido exclusivamente desde `docs/`.

Para actualizar después, vuelve a ejecutar el publicador, revisa el cambio de
`docs/`, haz commit y push. El workflow no genera imágenes, no escoge una
corrida y no escribe commits.

> GitHub Pages hace pública la edición publicada. Antes de alojar el repositorio
> como privado con Pages público, confirma que el plan de la cuenta permite esa
> combinación y que no hay contenido sensible fuera de `docs/` que vaya a
> incluirse en el repositorio privado.
