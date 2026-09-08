const root = document.querySelector("#comic-player");
const desktopQuery = window.matchMedia("(min-width: 768px)");
const POSITION_STORAGE_PREFIX = "ferry-powerpuff-star:position:";

let comic;
let desktopIndex = 0;
let guideMode = false;
let currentPosition = { kind: "cover" };
let mobileObserver;
let activeLightbox;

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
  const pageData = page.kind === "page" ? `data-page-number="${page.number}"` : "";
  return `<button class="comic-page-button" type="button" data-action="open-lightbox" data-page-kind="${page.kind}" ${pageData} aria-label="Abrir ${alt.toLowerCase()} en pantalla completa">
    <img class="comic-image ${guideClass} ${className}" src="${asset.large}" srcset="${srcset}" sizes="${sizes}" alt="${alt}" decoding="async" ${page.kind === "cover" ? "fetchpriority=\"high\"" : "loading=\"lazy\""}>
  </button>`;
}

function pageFromButton(button) {
  const position = button.dataset.pageKind === "page"
    ? { kind: "page", number: Number(button.dataset.pageNumber) }
    : { kind: button.dataset.pageKind };
  return pageForPosition(position);
}

function bindLightboxButtons(container) {
  container.querySelectorAll("[data-action='open-lightbox']").forEach((button) => {
    button.addEventListener("click", () => openLightbox(pageFromButton(button)));
  });
}

function closeLightbox() {
  if (!activeLightbox) return;
  const { element, previousFocus } = activeLightbox;
  activeLightbox = undefined;
  document.body.classList.remove("lightbox-open");
  element.remove();
  if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus();
}

function openLightbox(page) {
  if (!page) return;
  closeLightbox();

  const asset = activeAsset(page);
  const isGuide = asset === page.guide;
  const alt = imageAlt(page, isGuide);
  const srcset = asset.small
    ? `${asset.small} ${asset.smallWidth}w, ${asset.large} ${asset.largeWidth}w`
    : asset.large;
  const dialog = document.createElement("section");
  dialog.className = "comic-lightbox";
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "true");
  dialog.setAttribute("aria-label", `${alt}. Vista ampliada`);
  dialog.innerHTML = `
    <button class="lightbox-close" type="button" aria-label="Cerrar vista ampliada">${materialIcon("close")}</button>
    <div class="lightbox-stage">
      <img class="lightbox-image" src="${asset.large}" srcset="${srcset}" sizes="100vw" alt="${alt}" draggable="false">
      <p class="lightbox-hint">Pellizca o usa la rueda para ampliar</p>
    </div>`;

  const previousFocus = document.activeElement;
  const stage = dialog.querySelector(".lightbox-stage");
  const image = dialog.querySelector(".lightbox-image");
  const closeButton = dialog.querySelector(".lightbox-close");
  const pointers = new Map();
  let scale = 1;
  let x = 0;
  let y = 0;
  let pinchDistance = 0;
  let pinchScale = 1;

  const constrainPosition = () => {
    const maxX = Math.max(0, (image.offsetWidth * (scale - 1)) / 2);
    const maxY = Math.max(0, (image.offsetHeight * (scale - 1)) / 2);
    x = Math.max(-maxX, Math.min(maxX, x));
    y = Math.max(-maxY, Math.min(maxY, y));
  };
  const paint = () => {
    constrainPosition();
    image.style.transform = `translate3d(${x}px, ${y}px, 0) scale(${scale})`;
    stage.classList.toggle("is-zoomed", scale > 1);
  };
  const setScale = (nextScale) => {
    scale = Math.max(1, Math.min(4, nextScale));
    paint();
  };
  const pointerDistance = () => {
    const [first, second] = [...pointers.values()];
    return Math.hypot(second.x - first.x, second.y - first.y);
  };

  stage.addEventListener("pointerdown", (event) => {
    stage.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (pointers.size === 2) {
      pinchDistance = pointerDistance();
      pinchScale = scale;
    }
  });
  stage.addEventListener("pointermove", (event) => {
    const previous = pointers.get(event.pointerId);
    if (!previous) return;
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (pointers.size === 2 && pinchDistance) {
      setScale(pinchScale * (pointerDistance() / pinchDistance));
    } else if (scale > 1) {
      x += event.clientX - previous.x;
      y += event.clientY - previous.y;
      paint();
    }
  });
  ["pointerup", "pointercancel"].forEach((eventName) => stage.addEventListener(eventName, (event) => {
    pointers.delete(event.pointerId);
    if (pointers.size < 2) pinchDistance = 0;
  }));
  stage.addEventListener("wheel", (event) => {
    event.preventDefault();
    setScale(scale + (event.deltaY < 0 ? .25 : -.25));
  }, { passive: false });
  stage.addEventListener("dblclick", () => {
    scale = scale > 1 ? 1 : 2;
    x = 0;
    y = 0;
    paint();
  });
  closeButton.addEventListener("click", closeLightbox);
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) closeLightbox();
  });

  document.body.append(dialog);
  document.body.classList.add("lightbox-open");
  activeLightbox = { element: dialog, previousFocus, closeButton };
  closeButton.focus();
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
  bindLightboxButtons(reader);
  reader.addEventListener("click", (event) => {
    if (event.target.closest("button")) return;
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

function renderMobile() {
  if (mobileObserver) mobileObserver.disconnect();
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
  bindLightboxButtons(reader);
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
  if (activeLightbox) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeLightbox();
    }
    if (event.key === "Tab") {
      event.preventDefault();
      activeLightbox.closeButton.focus();
    }
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
