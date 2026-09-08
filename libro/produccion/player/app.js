import PhotoSwipeLightbox from "./vendor/photoswipe/photoswipe-lightbox.esm.js";
import PhotoSwipe from "./vendor/photoswipe/photoswipe.esm.js";

const root = document.querySelector("#comic-player");
const desktopQuery = window.matchMedia("(min-width: 768px)");
const POSITION_STORAGE_PREFIX = "ferry-powerpuff-star:position:";
const REVIEW_STORAGE_PREFIX = "ferry-powerpuff-star:review-notes:";
const reviewEnabled = new URLSearchParams(window.location.search).get("review") === "true";

let comic;
let desktopIndex = 0;
let guideMode = false;
let currentPosition = { kind: "cover" };
let mobileObserver;
let photoSwipeLightbox;
const preloadedAssets = new Set();
const pendingPreloads = new Set();
const preloadingImages = new Set();
let reviewNotes = [];
let reviewModalOpen = false;
let reviewEditingId = null;
let reviewStatus = "";

function materialIcon(name) {
  return `<span class="material-symbols-rounded" aria-hidden="true">${name}</span>`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
}

function readerPages() {
  return [
    { ...comic.cover, kind: "cover" },
    ...comic.pages.map((page) => ({ ...page, kind: "page" })),
    { ...comic.backCover, kind: "back-cover" },
  ];
}

function positionFor(page) {
  return page.kind === "page" ? { kind: "page", number: page.number } : { kind: page.kind };
}

function positionId(position) {
  return position.kind === "page" ? `page-${position.number}` : position.kind;
}

function pageForPosition(position) {
  return readerPages().find((page) => (
    page.kind === position.kind && (page.kind !== "page" || page.number === position.number)
  ));
}

function storageKey() {
  return `${POSITION_STORAGE_PREFIX}${comic.edition}`;
}

function loadPosition() {
  try {
    const stored = JSON.parse(window.localStorage.getItem(storageKey()));
    if (stored && typeof stored === "object" && pageForPosition(stored)) return stored;
  } catch {
    // A private browsing policy or malformed historic value must not block reading.
  }
  return { kind: "cover" };
}

function savePosition(page) {
  currentPosition = positionFor(page);
  try {
    window.localStorage.setItem(storageKey(), JSON.stringify(currentPosition));
  } catch {
    // Reading remains usable when localStorage is unavailable.
  }
}

function reviewStorageKey() {
  return `${REVIEW_STORAGE_PREFIX}${comic.edition}`;
}

function reviewPageValue(position) {
  return position.kind === "page" ? position.number : position.kind;
}

function reviewPageLabel(page) {
  if (page === "cover") return "Portada";
  if (page === "back-cover") return "Contraportada";
  return `Página ${page}`;
}

function parseReviewPage(value) {
  return /^\d+$/.test(value) ? Number(value) : value;
}

function isReviewPage(page) {
  return page === "cover" || page === "back-cover" || comic.pages.some((item) => item.number === page);
}

function loadReviewNotes() {
  if (!reviewEnabled) return [];
  try {
    const stored = JSON.parse(window.localStorage.getItem(reviewStorageKey()));
    if (!Array.isArray(stored)) return [];
    return stored.filter((note) => (
      note && typeof note.id === "string" && typeof note.note === "string" && isReviewPage(note.page)
    ));
  } catch {
    return [];
  }
}

function saveReviewNotes() {
  try {
    window.localStorage.setItem(reviewStorageKey(), JSON.stringify(reviewNotes));
  } catch {
    reviewStatus = "No se pudo guardar localmente en este navegador.";
  }
}

function reviewPageOptions(selectedPage) {
  return readerPages().map((page) => {
    const value = reviewPageValue(positionFor(page));
    return `<option value="${value}" ${value === selectedPage ? "selected" : ""}>${reviewPageLabel(value)}</option>`;
  }).join("");
}

function reviewNoteId() {
  return window.crypto?.randomUUID?.() || `note-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function reviewModalMarkup() {
  const editingNote = reviewNotes.find((note) => note.id === reviewEditingId);
  const selectedPage = editingNote?.page ?? reviewPageValue(currentPosition);
  const noteList = reviewNotes.length
    ? `<ul class="review-note-list">${reviewNotes.map((note) => `<li>
      <button class="review-note" type="button" data-review-edit="${note.id}">
        <span class="review-note__page">${reviewPageLabel(note.page)}</span>
        <span class="review-note__text">${escapeHtml(note.note)}</span>
      </button>
      <button class="review-note-delete" type="button" data-review-delete="${note.id}" aria-label="Borrar nota de ${reviewPageLabel(note.page)}">${materialIcon("delete")}</button>
    </li>`).join("")}</ul>`
    : '<p class="review-empty">Aún no hay anotaciones para esta edición.</p>';
  const content = reviewEditingId !== null
    ? `<form class="review-editor" data-review-form>
        <h3 id="review-editor-title">${editingNote ? "Editar anotación" : "Nueva anotación"}</h3>
        <label>Imagen
          <select name="page">${reviewPageOptions(selectedPage)}</select>
        </label>
        <label>Nota
          <textarea name="note" rows="7" required placeholder="Escribe la observación para esta imagen…">${escapeHtml(editingNote?.note || "")}</textarea>
        </label>
        <div class="review-editor__actions">
          <button class="reader-button" type="button" data-action="review-cancel">Cancelar</button>
          <button class="reader-button review-primary" type="submit">${materialIcon("save")} Guardar</button>
        </div>
      </form>`
    : `<div class="review-list-view">
        <div class="review-modal__actions">
          <button class="reader-button review-primary" type="button" data-action="review-add">${materialIcon("add")} Agregar</button>
          <button class="reader-button" type="button" data-action="review-export" ${reviewNotes.length ? "" : "disabled"}>${materialIcon("content_copy")} Exportar</button>
          <button class="reader-button review-danger" type="button" data-action="review-clear" ${reviewNotes.length ? "" : "disabled"}>${materialIcon("delete_sweep")} Borrar todo</button>
        </div>
        ${noteList}
      </div>`;
  return `<section class="review-modal" role="dialog" aria-modal="true" aria-labelledby="review-modal-title">
    <div class="review-modal__backdrop"></div>
    <div class="review-modal__panel">
      <header class="review-modal__header">
        <div><p class="review-eyebrow">Modo de revisión</p><h2 id="review-modal-title">Anotaciones</h2></div>
        <button class="review-close" type="button" data-action="review-close" aria-label="Cerrar anotaciones">${materialIcon("close")}</button>
      </header>
      ${reviewStatus ? `<p class="review-status" role="status">${escapeHtml(reviewStatus)}</p>` : ""}
      ${content}
    </div>
  </section>`;
}

function renderReviewModal() {
  root.querySelector(".review-modal")?.remove();
  if (!reviewEnabled || !reviewModalOpen) return;
  root.insertAdjacentHTML("beforeend", reviewModalMarkup());
  const modal = root.querySelector(".review-modal");
  modal.querySelector("[data-action='review-close']").addEventListener("click", closeReviewModal);
  modal.querySelector("[data-action='review-add']")?.addEventListener("click", () => openReviewEditor());
  modal.querySelector("[data-action='review-cancel']")?.addEventListener("click", () => {
    reviewEditingId = null;
    reviewStatus = "";
    renderReviewModal();
  });
  modal.querySelector("[data-action='review-export']")?.addEventListener("click", exportReviewNotes);
  modal.querySelector("[data-action='review-clear']")?.addEventListener("click", clearReviewNotes);
  modal.querySelectorAll("[data-review-edit]").forEach((button) => {
    button.addEventListener("click", () => openReviewEditor(button.dataset.reviewEdit));
  });
  modal.querySelectorAll("[data-review-delete]").forEach((button) => {
    button.addEventListener("click", () => deleteReviewNote(button.dataset.reviewDelete));
  });
  modal.querySelector("[data-review-form]")?.addEventListener("submit", saveReviewNote);
  window.requestAnimationFrame(() => modal.querySelector("textarea, [data-action='review-add']")?.focus());
}

function openReviewModal() {
  reviewModalOpen = true;
  reviewEditingId = null;
  reviewStatus = "";
  renderReviewModal();
}

function closeReviewModal() {
  reviewModalOpen = false;
  reviewEditingId = null;
  reviewStatus = "";
  renderReviewModal();
  root.querySelector("[data-action='review']")?.focus();
}

function openReviewEditor(noteId = "") {
  reviewEditingId = noteId;
  reviewStatus = "";
  renderReviewModal();
}

function saveReviewNote(event) {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const note = String(formData.get("note") || "").trim();
  if (!note) return;
  const page = parseReviewPage(String(formData.get("page")));
  const existingIndex = reviewNotes.findIndex((item) => item.id === reviewEditingId);
  const record = { id: existingIndex >= 0 ? reviewEditingId : reviewNoteId(), page, note };
  reviewNotes = existingIndex >= 0
    ? reviewNotes.map((item, index) => index === existingIndex ? record : item)
    : [record, ...reviewNotes];
  saveReviewNotes();
  reviewEditingId = null;
  reviewStatus = "Nota guardada.";
  renderReviewModal();
}

function deleteReviewNote(noteId) {
  reviewNotes = reviewNotes.filter((note) => note.id !== noteId);
  saveReviewNotes();
  reviewStatus = "Nota eliminada.";
  renderReviewModal();
}

function clearReviewNotes() {
  if (!window.confirm("¿Borrar todas las anotaciones locales de esta edición?")) return;
  reviewNotes = [];
  saveReviewNotes();
  reviewStatus = "Todas las notas fueron eliminadas.";
  renderReviewModal();
}

async function exportReviewNotes() {
  const payload = JSON.stringify({
    edition: comic.edition,
    notes: reviewNotes.map(({ page, note }) => ({ page, note })),
  }, null, 2);
  try {
    if (!navigator.clipboard?.writeText) throw new Error("Clipboard API unavailable");
    await navigator.clipboard.writeText(payload);
    reviewStatus = `${reviewNotes.length} nota${reviewNotes.length === 1 ? "" : "s"} copiada${reviewNotes.length === 1 ? "" : "s"} al portapapeles.`;
  } catch {
    reviewStatus = "No se pudo copiar al portapapeles. Revisa los permisos del navegador.";
  }
  renderReviewModal();
}

function activeAsset(page) {
  return guideMode && page.kind === "page" ? page.guide : page;
}

function shouldPreload() {
  const connection = navigator.connection;
  return !connection?.saveData && !["slow-2g", "2g"].includes(connection?.effectiveType);
}

function preloadAsset(page) {
  const asset = activeAsset(page);
  return desktopQuery.matches ? asset.large : asset.small || asset.large;
}

function schedulePreload(pages) {
  if (!shouldPreload()) return;
  const urls = pages
    .filter(Boolean)
    .map(preloadAsset)
    .filter((url) => url && !preloadedAssets.has(url) && !pendingPreloads.has(url));
  if (!urls.length) return;
  urls.forEach((url) => pendingPreloads.add(url));

  const preload = () => {
    urls.forEach((url) => {
      pendingPreloads.delete(url);
      preloadedAssets.add(url);
      const image = new Image();
      image.decoding = "async";
      image.fetchPriority = "low";
      image.addEventListener("load", () => preloadingImages.delete(image), { once: true });
      image.addEventListener("error", () => preloadingImages.delete(image), { once: true });
      preloadingImages.add(image);
      image.src = url;
    });
  };
  if ("requestIdleCallback" in window) window.requestIdleCallback(preload, { timeout: 1200 });
  else window.setTimeout(preload, 0);
}

function imageAlt(page, isGuide = activeAsset(page) === page.guide) {
  if (page.kind === "cover") return "Portada de Ferry PowerPuff Star";
  if (page.kind === "back-cover") return "Contracubierta de Ferry PowerPuff Star";
  return isGuide
    ? `Guía visual de la página ${page.number} del cómic`
    : `Página ${page.number} del cómic`;
}

function imageMarkup(page, className = "") {
  const asset = activeAsset(page);
  const isGuide = asset === page.guide;
  const alt = imageAlt(page, isGuide);
  const srcset = asset.small
    ? `${asset.small} ${asset.smallWidth}w, ${asset.large} ${asset.largeWidth}w`
    : asset.large;
  const sizes = asset.small ? "(max-width: 767px) 100vw, 50vw" : "(max-width: 767px) 100vw, 46vw";
  const guideClass = isGuide ? "comic-image--guide" : "";
  return `<a class="comic-page-button" href="${asset.large}" data-pswp-width="${asset.largeWidth}" data-pswp-height="${asset.largeHeight}" data-pswp-srcset="${srcset}" aria-label="Abrir ${alt.toLowerCase()} en pantalla completa">
    <img class="comic-image ${guideClass} ${className}" src="${asset.large}" srcset="${srcset}" sizes="${sizes}" alt="${alt}" decoding="async" ${page.kind === "cover" ? "fetchpriority=\"high\"" : "loading=\"lazy\""}>
  </a>`;
}

function resetLightbox() {
  photoSwipeLightbox?.destroy();
  photoSwipeLightbox = undefined;
}

function initializeLightbox(gallery) {
  resetLightbox();
  photoSwipeLightbox = new PhotoSwipeLightbox({
    gallery,
    children: ".comic-page-button",
    pswpModule: PhotoSwipe,
    bgOpacity: .94,
    wheelToZoom: true,
    pinchToClose: false,
    closeOnVerticalDrag: false,
    allowPanToNext: false,
    maxZoomLevel: 4,
  });
  photoSwipeLightbox.init();
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

function nextReaderPage(position) {
  const pages = readerPages();
  const currentIndex = pages.findIndex((page) => (
    page.kind === position.kind && (page.kind !== "page" || page.number === position.number)
  ));
  return pages[currentIndex + 1];
}

function desktopIndexFor(position) {
  const index = desktopViews().findIndex((view) => view.some((page) => (
    page.kind === position.kind && (page.kind !== "page" || page.number === position.number)
  )));
  return index < 0 ? 0 : index;
}

function guideToggleMarkup(hidden = false) {
  const label = guideMode ? "Mostrar arte final" : "Mostrar guía visual";
  return `<button class="guide-toggle" type="button" data-action="toggle-guide" aria-label="${label}" aria-pressed="${guideMode}" ${hidden ? "hidden" : ""}>
    <img src="${comic.guideAvatar.src}" width="${comic.guideAvatar.width}" height="${comic.guideAvatar.height}" alt="">
    <span class="sr-only">${label}</span>
  </button>`;
}

function reviewButtonMarkup(hidden = false) {
  if (!reviewEnabled) return "";
  return `<button class="review-button" type="button" data-action="review" aria-label="Abrir anotaciones de revisión" ${hidden ? "hidden" : ""}>
    ${materialIcon("settings")}<span class="sr-only">Abrir anotaciones de revisión</span>
  </button>`;
}

function homeButtonMarkup(hidden = false) {
  return `<button class="home-avatar" type="button" data-action="home" aria-label="Volver a la portada" ${hidden ? "hidden" : ""}>
    <img src="${comic.homeAvatar.src}" width="${comic.homeAvatar.width}" height="${comic.homeAvatar.height}" alt="">
    <span class="sr-only">Volver a la portada</span>
  </button>`;
}

function renderDesktop() {
  if (mobileObserver) mobileObserver.disconnect();
  resetLightbox();
  const views = desktopViews();
  desktopIndex = Math.max(0, Math.min(desktopIndex, views.length - 1));
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
        ${view.map((page) => {
          const image = imageMarkup(page, page.kind === "cover" ? "cover-image" : "");
          return single ? image : `<div class="spread-page">${image}</div>`;
        }).join("")}
      </div>
      ${desktopIndex === 0 ? '<p class="cover-hint">Clic o → para comenzar</p>' : ""}
      <nav class="reader-nav" aria-label="Navegación del cómic">
        ${desktopIndex === 0 ? "" : homeButtonMarkup()}
        <button class="reader-button" type="button" data-action="previous" aria-label="Página anterior" ${desktopIndex === 0 ? "disabled" : ""}>
          ${materialIcon("arrow_back")}<span class="reader-button__label">Anterior</span>
        </button>
        <span class="page-status" aria-live="polite">${progress}</span>
        <button class="reader-button" type="button" data-action="next" aria-label="Página siguiente" ${desktopIndex === views.length - 1 ? "disabled" : ""}>
          <span class="reader-button__label">Siguiente</span>${materialIcon("arrow_forward")}
        </button>
        ${guideToggleMarkup(desktopIndex === 0 || desktopIndex === views.length - 1)}
        ${reviewButtonMarkup()}
      </nav>
    </section>`;

  const reader = root.querySelector(".desktop-reader");
  initializeLightbox(reader);
  schedulePreload(views[desktopIndex + 1] || []);
  reader.addEventListener("click", (event) => {
    if (event.target.closest("button, a")) return;
    const rect = event.currentTarget.getBoundingClientRect();
    changeDesktopIndex(desktopIndex + (event.clientX - rect.left < rect.width / 2 ? -1 : 1));
  });
  root.querySelector("[data-action='previous']").addEventListener("click", () => changeDesktopIndex(desktopIndex - 1));
  root.querySelector("[data-action='next']").addEventListener("click", () => changeDesktopIndex(desktopIndex + 1));
  const homeButton = root.querySelector("[data-action='home']");
  if (homeButton) homeButton.addEventListener("click", goHome);
  root.querySelector("[data-action='toggle-guide']").addEventListener("click", toggleGuide);
  root.querySelector("[data-action='review']")?.addEventListener("click", openReviewModal);
  renderReviewModal();
}

function changeDesktopIndex(nextIndex) {
  const views = desktopViews();
  desktopIndex = Math.max(0, Math.min(nextIndex, views.length - 1));
  savePosition(views[desktopIndex][0]);
  renderDesktop();
}

function mobileControlsMarkup() {
  const onCover = currentPosition.kind === "cover";
  const onInterior = currentPosition.kind === "page";
  return `<nav class="mobile-controls" aria-label="Controles del cómic">
    ${homeButtonMarkup(onCover)}
    <div class="mobile-controls__right">
      ${guideToggleMarkup(!onInterior)}
      ${reviewButtonMarkup()}
    </div>
  </nav>`;
}

function updateMobileControls(position) {
  const homeButton = root.querySelector("[data-action='home']");
  const guideButton = root.querySelector("[data-action='toggle-guide']");
  if (homeButton) homeButton.hidden = position.kind === "cover";
  if (guideButton) guideButton.hidden = position.kind !== "page";
}

function startMobilePositionTracking(reader) {
  const sheets = [...reader.querySelectorAll(".mobile-sheet")];
  mobileObserver = new IntersectionObserver((entries) => {
    entries
      .filter((entry) => entry.isIntersecting && entry.intersectionRatio >= 0.3)
      .forEach((entry) => entry.target.classList.add("is-visible"));
    const visible = entries
      .filter((entry) => entry.isIntersecting && entry.intersectionRatio >= 0.6)
      .sort((first, second) => second.intersectionRatio - first.intersectionRatio)[0];
    if (!visible) return;
    const sheet = visible.target;
    const position = sheet.dataset.kind === "page"
      ? { kind: "page", number: Number(sheet.dataset.number) }
      : { kind: sheet.dataset.kind };
    savePosition(position);
    updateMobileControls(currentPosition);
    schedulePreload([nextReaderPage(position)]);
  }, { root: reader, threshold: [0.6, 0.8] });
  sheets.forEach((sheet) => mobileObserver.observe(sheet));
}

function enableMouseDragScroll(reader) {
  let pointerId;
  let startY;
  let startScrollTop;
  let didDrag = false;
  let suppressClickUntil = 0;

  reader.addEventListener("pointerdown", (event) => {
    if (event.pointerType !== "mouse" || event.button !== 0 || event.target.closest("button")) return;
    pointerId = event.pointerId;
    startY = event.clientY;
    startScrollTop = reader.scrollTop;
    didDrag = false;
    reader.setPointerCapture(pointerId);
  });
  reader.addEventListener("pointermove", (event) => {
    if (event.pointerId !== pointerId) return;
    const distance = event.clientY - startY;
    if (Math.abs(distance) > 5) didDrag = true;
    if (!didDrag) return;
    event.preventDefault();
    reader.classList.add("is-mouse-dragging");
    reader.scrollTop = startScrollTop - distance;
  });
  const finishDrag = (event) => {
    if (event.pointerId !== pointerId) return;
    if (reader.hasPointerCapture(pointerId)) reader.releasePointerCapture(pointerId);
    if (didDrag) suppressClickUntil = Date.now() + 80;
    reader.classList.remove("is-mouse-dragging");
    pointerId = undefined;
  };
  reader.addEventListener("pointerup", finishDrag);
  reader.addEventListener("pointercancel", finishDrag);
  reader.addEventListener("click", (event) => {
    if (Date.now() > suppressClickUntil) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  }, true);
}

function renderMobile() {
  if (mobileObserver) mobileObserver.disconnect();
  resetLightbox();
  const pages = readerPages();
  root.innerHTML = `<section class="mobile-reader" aria-label="Lector de cómic vertical">
    ${mobileControlsMarkup()}
    ${pages.map((page, index) => `
      <article class="mobile-sheet" data-position="${positionId(positionFor(page))}" data-kind="${page.kind}" ${page.kind === "page" ? `data-number="${page.number}"` : ""}>
        ${imageMarkup(page, page.kind === "cover" ? "cover-image" : "")}
        ${index === 0 ? '<p class="cover-hint">Desliza para comenzar</p>' : ""}
      </article>`).join("")}
    </section>`;
  const reader = root.querySelector(".mobile-reader");
  initializeLightbox(reader);
  enableMouseDragScroll(reader);
  root.querySelector("[data-action='home']").addEventListener("click", goHome);
  root.querySelector("[data-action='toggle-guide']").addEventListener("click", toggleGuide);
  root.querySelector("[data-action='review']")?.addEventListener("click", openReviewModal);
  renderReviewModal();
  window.requestAnimationFrame(() => {
    const target = reader.querySelector(`[data-position="${positionId(currentPosition)}"]`) || reader.querySelector(".mobile-sheet");
    reader.scrollTop = target.offsetTop;
    startMobilePositionTracking(reader);
    schedulePreload([nextReaderPage(currentPosition)]);
  });
}

function goHome() {
  const cover = readerPages()[0];
  savePosition(cover);
  if (desktopQuery.matches) {
    desktopIndex = 0;
    renderDesktop();
  } else {
    renderMobile();
  }
}

function toggleGuide() {
  guideMode = !guideMode;
  if (desktopQuery.matches) renderDesktop();
  else renderMobile();
}

function render() {
  if (desktopQuery.matches) {
    desktopIndex = desktopIndexFor(currentPosition);
    renderDesktop();
  } else {
    renderMobile();
  }
}

window.addEventListener("keydown", (event) => {
  if (reviewModalOpen && event.key === "Escape") {
    event.preventDefault();
    closeReviewModal();
    return;
  }
  if (!comic || !desktopQuery.matches) return;
  if (event.key === "Home") {
    event.preventDefault();
    goHome();
    return;
  }
  if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
  event.preventDefault();
  changeDesktopIndex(desktopIndex + (event.key === "ArrowLeft" ? -1 : 1));
});

desktopQuery.addEventListener("change", render);

fetch("./manifest.json")
  .then((response) => {
    if (!response.ok) throw new Error("No se pudo cargar la edición publicada.");
    return response.json();
  })
  .then((manifest) => {
    const hasGuideAssets = Array.isArray(manifest.pages) && manifest.pages.every((page) => page.guide?.small && page.guide?.large);
    if (!manifest.cover || !manifest.backCover || !manifest.guideAvatar?.src || !manifest.homeAvatar?.src || !hasGuideAssets) {
      throw new Error("El manifiesto de la edición no incluye los assets requeridos.");
    }
    comic = manifest;
    document.title = manifest.title;
    currentPosition = loadPosition();
    reviewNotes = loadReviewNotes();
    render();
  })
  .catch((error) => {
    root.innerHTML = `<p class="error-message">${error.message}</p>`;
  });
