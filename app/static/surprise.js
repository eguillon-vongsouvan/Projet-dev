(() => {
  const btn = document.getElementById("surpriseBtn");
  if (!btn) return;

  function showImageOverlay(src) {
    const layer = document.createElement("div");
    layer.className = "surprise-layer";
    layer.innerHTML = `
      <div class="surprise-backdrop"></div>
      <img class="surprise-image" alt="Surprise" src="${src}" />
      <div class="surprise-caption">BOUH (safe mode)</div>
    `;
    const img = layer.querySelector(".surprise-image");
    if (img) {
      img.addEventListener("error", () => {
        img.style.display = "none";
        const fallback = document.createElement("div");
        fallback.className = "surprise-fail";
        fallback.textContent = "Image introuvable. Ajoute /static/images/surprise-face.png";
        layer.appendChild(fallback);
      });
    }
    document.body.appendChild(layer);
    setTimeout(() => layer.classList.add("show"), 10);
    setTimeout(() => {
      layer.classList.remove("show");
      setTimeout(() => layer.remove(), 450);
    }, 1200);
  }

  function showGoofyFail() {
    const layer = document.createElement("div");
    layer.className = "surprise-layer";
    layer.innerHTML = `
      <div class="surprise-backdrop"></div>
      <div class="surprise-fail">Pas cette fois 😅</div>
    `;
    document.body.appendChild(layer);
    setTimeout(() => layer.classList.add("show"), 10);
    setTimeout(() => {
      layer.classList.remove("show");
      setTimeout(() => layer.remove(), 450);
    }, 800);
  }

  btn.addEventListener("click", () => {
    const ok = Math.random() < 0.5;
    if (!ok) {
      showGoofyFail();
      return;
    }
    const src = btn.dataset.surpriseImage || "";
    showImageOverlay(src);
  });
})();

