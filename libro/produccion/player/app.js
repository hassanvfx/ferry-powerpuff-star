import PhotoSwipeLightbox from "./vendor/photoswipe/photoswipe-lightbox.esm.js";
import PhotoSwipe from "./vendor/photoswipe/photoswipe.esm.js";

const root = document.querySelector("#comic-player");
const desktopQuery = window.matchMedia("(min-width: 768px)");
const POSITION_STORAGE_PREFIX = "ferry-powerpuff-star:position:";

let comic;
let desktopIndex = 0;
let guideMode = false;
let currentPosition = { kind: "cover" };
let mobileObserver;
let photoSwipeLightbox;

function materialIcon(name) {
  return `<span class="material-symbols-rounded" aria-hidden="true">${name}</span>`;
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

function activeAsset(page) {
  return guideMode && page.kind === "page" ? page.guide : page;
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

function homeButtonMarkup(hidden = false) {
  return `<button class="reader-button" type="button" data-action="home" aria-label="Volver a la portada" ${hidden ? "hidden" : ""}>
    ${materialIcon("home")}<span class="reader-button__label">Inicio</span>
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
      </nav>
    </section>`;

  const reader = root.querySelector(".desktop-reader");
  initializeLightbox(reader);
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
    ${guideToggleMarkup(!onInterior)}
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
    savePosition(sheet.dataset.kind === "page"
      ? { kind: "page", number: Number(sheet.dataset.number) }
      : { kind: sheet.dataset.kind });
    updateMobileControls(currentPosition);
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
  window.requestAnimationFrame(() => {
    const target = reader.querySelector(`[data-position="${positionId(currentPosition)}"]`) || reader.querySelector(".mobile-sheet");
    reader.scrollTop = target.offsetTop;
    startMobilePositionTracking(reader);
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
    if (!manifest.cover || !manifest.backCover || !manifest.guideAvatar?.src || !hasGuideAssets) {
      throw new Error("El manifiesto de la edición no incluye los assets requeridos.");
    }
    comic = manifest;
    document.title = manifest.title;
    currentPosition = loadPosition();
    render();
  })
  .catch((error) => {
    root.innerHTML = `<p class="error-message">${error.message}</p>`;
  });
