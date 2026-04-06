// Interactions légères (sans framework)

function enhanceButtons() {
  document.addEventListener("submit", (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    const btn = form.querySelector("button[type='submit']");
    if (!(btn instanceof HTMLButtonElement)) return;
    btn.dataset.originalText = btn.textContent || "";
    btn.disabled = true;
    btn.classList.add("is-loading");
    btn.textContent = "Traitement…";
  });
}

function autoDismissToasts() {
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach((el) => {
    setTimeout(() => el.classList.add("hide"), 3000);
    setTimeout(() => el.remove(), 3600);
  });
}

function goofyLoginConfetti() {
  const success = document.querySelector(".flash.flash-success");
  if (!success) return;
  const msg = (success.textContent || "").toLowerCase();
  if (!msg.includes("connexion")) return;

  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const layer = document.createElement("div");
  layer.className = "goofy-layer";
  document.body.appendChild(layer);

  const pieces = reduced ? 80 : 320;
  const colors = ["#2563eb", "#0ea5e9", "#22c55e", "#f97316", "#a855f7", "#ef4444", "#eab308"];

  for (let i = 0; i < pieces; i++) {
    const p = document.createElement("i");
    p.className = "confetti";
    const left = Math.random() * 100;
    const size = 6 + Math.random() * 10;
    const delay = Math.random() * 0.8;
    const dur = (reduced ? 3.4 : 4.4) + Math.random() * 2.2;
    const rot = Math.random() * 360;
    const drift = (Math.random() * 2 - 1) * 120;
    p.style.left = `${left}vw`;
    p.style.width = `${size}px`;
    p.style.height = `${Math.max(6, size * 0.55)}px`;
    p.style.background = colors[i % colors.length];
    p.style.animationDelay = `${delay}s`;
    p.style.animationDuration = `${dur}s`;
    p.style.setProperty("--rot", `${rot}deg`);
    p.style.setProperty("--drift", `${drift}px`);
    layer.appendChild(p);
  }

  const rocket = document.createElement("div");
  rocket.className = "rocket";
  rocket.innerHTML = `
    <div class="rocket-body">
      <div class="rocket-window"></div>
      <div class="rocket-fin left"></div>
      <div class="rocket-fin right"></div>
    </div>
    <div class="rocket-flame"></div>
    <div class="rocket-smoke"></div>
  `;
  layer.appendChild(rocket);

  // Cleanup
  const cleanupMs = reduced ? 6500 : 12000;
  setTimeout(() => layer.remove(), cleanupMs);
}

function init() {
  enhanceButtons();
  autoDismissToasts();
  goofyLoginConfetti();

  // Calendrier emploi du temps (style Pronote/Google Calendar)
  const calendar = document.getElementById("calendar");
  if (calendar) {
    const timesEl = document.getElementById("calTimes");
    const gridEl = document.getElementById("calGrid");
    const eventsEl = document.getElementById("calEvents");

    const startHour = 8;
    const endHour = 20;
    const hourHeight = 56; // px

    const toMinutes = (hhmmss) => {
      const parts = String(hhmmss).split(":");
      const h = Number(parts[0] || 0);
      const m = Number(parts[1] || 0);
      return h * 60 + m;
    };

    // Build time gutter
    if (timesEl) {
      timesEl.innerHTML = "";
      for (let h = startHour; h <= endHour; h++) {
        const div = document.createElement("div");
        div.className = "cal-time";
        div.style.height = `${hourHeight}px`;
        div.textContent = `${String(h).padStart(2, "0")}:00`;
        timesEl.appendChild(div);
      }
    }

    // Set grid height
    if (gridEl) {
      const totalHours = endHour - startHour;
      gridEl.style.setProperty("--cal-height", `${totalHours * hourHeight}px`);
      gridEl.style.height = `${totalHours * hourHeight}px`;
    }

    // Place events
    const children = Array.from(eventsEl?.children || []);
    children.forEach((n) => {
      const day = n.dataset.day;
      const start = toMinutes(n.dataset.start);
      const end = toMinutes(n.dataset.end);
      const cls = n.dataset.class || "";
      const loc = n.dataset.location || "";

      const col = document.querySelector(`.cal-col[data-day-col="${day}"]`);
      if (!col) return;

      const top = ((start - startHour * 60) / 60) * hourHeight;
      const height = Math.max(18, ((end - start) / 60) * hourHeight);

      const ev = document.createElement("div");
      ev.className = "cal-event";
      ev.dataset.day = day;
      ev.style.top = `${top}px`;
      ev.style.height = `${height}px`;
      ev.innerHTML = `
        <div class="cal-event-title">${cls}</div>
        ${loc ? `<div class="cal-event-sub">${loc}</div>` : ``}
        <div class="cal-event-sub">${String(n.dataset.start).slice(0,5)}–${String(n.dataset.end).slice(0,5)}</div>
      `;
      col.appendChild(ev);
    });

    // Filtres par jour -> masquer colonnes
    const chips = document.querySelectorAll("[data-chip-day]");
    if (chips.length) {
      const setDay = (day) => {
        chips.forEach((c) => c.classList.toggle("active", c.dataset.chipDay === day));
        document.querySelectorAll("[data-day-col]").forEach((el) => {
          const d = el.dataset.dayCol;
          el.style.display = day === "ALL" || d === day ? "" : "none";
        });
      };
      chips.forEach((c) => c.addEventListener("click", () => setDay(c.dataset.chipDay)));
      setDay("ALL");
    }
  }
}

document.addEventListener("DOMContentLoaded", init);

