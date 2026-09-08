const root = document.querySelector("#comic-player");
const desktopQuery = window.matchMedia("(min-width: 768px)");
let comic;
let desktopIndex = 0;

function imageMarkup(page, className = "") {
  const alt = page.kind === "cover"
    ? "Portada de Ferry PowerPuff Star"
    : page.kind === "back-cover"
      ? "Contracubierta de Ferry PowerPuff Star"
      : `Página ${page.number} del cómic`;
  const srcset = page.small
    ? `${page.small} ${page.smallWidth}w, ${page.large} ${page.largeWidth}w`
    : page.large;
  const sizes = page.small ? "(max-width: 767px) 100vw, 50vw" : "(max-width: 767px) 100vw, 46vw";
  return `<img class="comic-image ${className}" src="${page.large}" srcset="${srcset}" sizes="${sizes}" alt="${alt}" decoding="async" ${page.kind === "cover" ? "fetchpriority=\"high\"" : "loading=\"lazy\""}>`;
}

function desktopViews() {
  const pages = comic.pages.map((page) => ({ ...page, kind: "page" }));
  const pairs = [];
  for (let index = 0; index < pages.length; index += 2) pairs.push(pages.slice(index, index + 2));
  return [
    [{ ...comic.cover, kind: "cover" }],
    ...pairs,
    [{ ...comic.backCover, kind: "back-cover" }],
  ];
}

function renderDesktop() {
  const views = desktopViews();
  desktopIndex = Math.min(desktopIndex, views.length - 1);
  const view = views[desktopIndex];
  const single = view.length === 1;
  const progress = desktopIndex === 0
    ? "Portada"
    : desktopIndex === views.length - 1
      ? "Final"
      : `Págs. ${view[0].number}–${view[1].number}`;
  root.innerHTML = `
    <section class="desktop-reader" aria-label="Lector de cómic">
      <div class="spread ${single ? "spread--single" : ""}">
        ${view.map((page) => imageMarkup(page, page.kind === "cover" ? "cover-image" : "")).join("")}
      </div>
      ${desktopIndex === 0 ? '<p class="cover-hint">Clic o → para comenzar</p>' : ""}
      <nav class="reader-nav" aria-label="Navegación del cómic">
        <button type="button" data-action="previous" ${desktopIndex === 0 ? "disabled" : ""}>← Anterior</button>
        <span class="page-status" aria-live="polite">${progress}</span>
        <button type="button" data-action="next" ${desktopIndex === views.length - 1 ? "disabled" : ""}>Siguiente →</button>
      </nav>
    </section>`;

  root.querySelector(".desktop-reader").addEventListener("click", (event) => {
    if (event.target.closest("button")) return;
    const rect = event.currentTarget.getBoundingClientRect();
    desktopIndex += event.clientX - rect.left < rect.width / 2 ? -1 : 1;
    desktopIndex = Math.max(0, Math.min(desktopIndex, views.length - 1));
    renderDesktop();
  });
  root.querySelector("[data-action='previous']").addEventListener("click", () => {
    desktopIndex = Math.max(0, desktopIndex - 1);
    renderDesktop();
  });
  root.querySelector("[data-action='next']").addEventListener("click", () => {
    desktopIndex = Math.min(views.length - 1, desktopIndex + 1);
    renderDesktop();
  });
}

function renderMobile() {
  const pages = [
    { ...comic.cover, kind: "cover" },
    ...comic.pages.map((page) => ({ ...page, kind: "page" })),
    { ...comic.backCover, kind: "back-cover" },
  ];
  root.innerHTML = `<section class="mobile-reader" aria-label="Lector de cómic vertical">${pages.map((page, index) => `
    <article class="mobile-sheet">
      ${imageMarkup(page, page.kind === "cover" ? "cover-image" : "")}
      ${index === 0 ? '<p class="cover-hint">Desliza para comenzar</p>' : ""}
    </article>`).join("")}</section>`;
}

function render() {
  if (desktopQuery.matches) renderDesktop();
  else renderMobile();
}

window.addEventListener("keydown", (event) => {
  if (!comic || !desktopQuery.matches || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
  event.preventDefault();
  const change = event.key === "ArrowLeft" ? -1 : 1;
  desktopIndex = Math.max(0, Math.min(desktopViews().length - 1, desktopIndex + change));
  renderDesktop();
});

desktopQuery.addEventListener("change", render);

fetch("./manifest.json")
  .then((response) => {
    if (!response.ok) throw new Error("No se pudo cargar la edición publicada.");
    return response.json();
  })
  .then((manifest) => {
    if (!manifest.cover || !manifest.backCover || !Array.isArray(manifest.pages)) throw new Error("El manifiesto de la edición no es válido.");
    comic = manifest;
    document.title = manifest.title;
    render();
  })
  .catch((error) => {
    root.innerHTML = `<p class="error-message">${error.message}</p>`;
  });
