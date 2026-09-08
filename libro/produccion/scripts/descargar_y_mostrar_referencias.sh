#!/usr/bin/env bash
# Descarga las referencias de personajes a un directorio temporal y abre una galería.
set -euo pipefail

destino="$(mktemp -d "${TMPDIR:-/tmp}/referencias-personajes.XXXXXX")"

descargar() {
  local nombre="$1"
  local url="$2"
  local archivo="$destino/$nombre.png"

  printf 'Descargando %s...\n' "$nombre"
  curl --fail --location --silent --show-error "$url" --output "$archivo"
}

descargar \
  'ferry' \
  'https://tempfile.aiquickdraw.com/h/906205fd9cae44fd41f9c755538e6513_1788852998.png'
descargar \
  'hassan' \
  'https://tempfile.aiquickdraw.com/h/e37d2e9a8e0c81bc1ba4e6b658c568fe_1788853048.png'

galeria="$destino/index.html"
cat >"$galeria" <<HTML
<!doctype html>
<html lang="es"><meta charset="utf-8"><title>Referencias de personajes</title>
<style>body{font:16px system-ui;margin:32px;background:#171717;color:#fff}main{display:flex;gap:24px;flex-wrap:wrap}figure{margin:0;width:min(440px,100%)}img{display:block;width:100%;border-radius:12px}figcaption{padding:10px 2px;font-size:20px}</style>
<main><figure><img src="ferry.png" alt="Ferry"><figcaption>Ferry</figcaption></figure><figure><img src="hassan.png" alt="Hassan"><figcaption>Hassan</figcaption></figure></main>
</html>
HTML

printf '\nImágenes guardadas en: %s\n' "$destino"
open "$galeria"
