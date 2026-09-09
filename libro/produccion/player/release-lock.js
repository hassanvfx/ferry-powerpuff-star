const RELEASE_AT = "2026-09-10T00:00:00-06:00";
const RELEASE_AT_MS = Date.parse(RELEASE_AT);
const TEST_OFFSET_MS = 60 * 60 * 1000;
const query = new URLSearchParams(window.location.search);
const bypassWait = query.get("bypass-wait") === "true";
const browserStartedAt = Date.now();
const player = document.querySelector("#comic-player");

function effectiveNow() {
  if (!bypassWait) return Date.now();
  return RELEASE_AT_MS - TEST_OFFSET_MS + (Date.now() - browserStartedAt);
}

function remainingMilliseconds() {
  return RELEASE_AT_MS - effectiveNow();
}

function plural(value, singular, pluralWord) {
  return `${value} ${value === 1 ? singular : pluralWord}`;
}

function countdownLabel(remaining) {
  const totalSeconds = Math.max(0, Math.floor(remaining / 1000));
  const days = Math.floor(totalSeconds / 86400);
  const hours = Math.floor((totalSeconds % 86400) / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `Faltan ${plural(days, "día", "días")}, ${plural(hours, "hora", "horas")}, ${plural(minutes, "minuto", "minutos")}, ${plural(seconds, "segundo", "segundos")}`;
}

function restoreReader(overlay) {
  window.clearInterval(overlay.timer);
  overlay.remove();
  document.body.classList.remove("is-release-locked");
  player.removeAttribute("inert");
  player.removeAttribute("aria-hidden");
}

function mountOverlay(manifest) {
  if (remainingMilliseconds() <= 0 || !manifest.cover?.large || !manifest.backCover?.large) return;
  player.setAttribute("inert", "");
  player.setAttribute("aria-hidden", "true");
  document.body.classList.add("is-release-locked");

  const overlay = document.createElement("section");
  overlay.className = "release-lock";
  overlay.setAttribute("aria-label", "Cuenta regresiva para el lanzamiento");
  overlay.innerHTML = `
    <div class="release-lock__spread" aria-hidden="true">
      <img src="${manifest.backCover.large}" alt="">
      <img src="${manifest.cover.large}" alt="">
    </div>
    <p class="release-lock__countdown" aria-live="polite"></p>`;
  document.body.append(overlay);

  const countdown = overlay.querySelector(".release-lock__countdown");
  const update = () => {
    const remaining = remainingMilliseconds();
    if (remaining <= 0) {
      restoreReader(overlay);
      return;
    }
    countdown.textContent = countdownLabel(remaining);
  };
  update();
  overlay.timer = window.setInterval(update, 1000);
}

if (remainingMilliseconds() > 0) {
  fetch("./manifest.json")
    .then((response) => response.ok ? response.json() : null)
    .then((manifest) => manifest && mountOverlay(manifest))
    .catch(() => {
      // The player retains its own fetch error handling; the lock fails open only when assets cannot load.
    });
}
