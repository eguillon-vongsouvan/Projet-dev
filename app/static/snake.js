(() => {
  const canvas = document.getElementById("snakeCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // HiDPI
  const size = 420;
  const dpr = Math.max(1, Math.floor(window.devicePixelRatio || 1));
  canvas.width = size * dpr;
  canvas.height = size * dpr;
  canvas.style.width = `${size}px`;
  canvas.style.height = `${size}px`;
  ctx.scale(dpr, dpr);

  const grid = 21;
  const cell = Math.floor(size / grid);

  const scoreEl = document.getElementById("snakeScore");
  const bestEl = document.getElementById("snakeBest");
  const btn = document.getElementById("snakeToggle");

  let best = Number(localStorage.getItem("snakeBest") || "0");
  if (bestEl) bestEl.textContent = String(best);

  let loseFxShown = false;

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function showSnakeLoseFx() {
    const reduced = prefersReducedMotion();
    const layer = document.createElement("div");
    layer.className = "fx-layer fx-dim fx-snake-lose-layer";
    layer.innerHTML = `
      <div class="fx-snake-lose-text">You lose</div>
      <div class="fx-snake-lose-snake" aria-hidden="true"></div>
    `;
    document.body.appendChild(layer);
    window.setTimeout(() => layer.remove(), reduced ? 1300 : 2200);
  }

  function shakeLayout() {
    const root = document.querySelector(".app") || document.body;
    if (!root) return;
    root.classList.add("layout-shake");
    window.setTimeout(() => root.classList.remove("layout-shake"), 260);
  }

  const initialState = () => ({
    dir: { x: 1, y: 0 },
    nextDir: { x: 1, y: 0 },
    snake: [{ x: 8, y: 10 }, { x: 7, y: 10 }, { x: 6, y: 10 }],
    food: { x: 14, y: 10 },
    running: false,
    score: 0,
    tickMs: 120,
    lastTick: 0,
  });

  let state = initialState();

  function randCell() {
    return Math.floor(Math.random() * grid);
  }

  function placeFood() {
    let tries = 0;
    while (tries < 200) {
      const fx = randCell();
      const fy = randCell();
      const hit = state.snake.some((s) => s.x === fx && s.y === fy);
      if (!hit) {
        state.food = { x: fx, y: fy };
        return;
      }
      tries++;
    }
  }

  function drawBackground() {
    ctx.clearRect(0, 0, size, size);
    // background glow + grid
    const bg = ctx.createLinearGradient(0, 0, 0, size);
    bg.addColorStop(0, "rgba(37,99,235,0.06)");
    bg.addColorStop(1, "rgba(14,165,233,0.03)");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, size, size);

    ctx.strokeStyle = "rgba(226, 232, 240, 0.85)";
    ctx.lineWidth = 1;
    for (let i = 0; i <= grid; i++) {
      const p = i * cell + 0.5;
      ctx.beginPath();
      ctx.moveTo(p, 0);
      ctx.lineTo(p, size);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, p);
      ctx.lineTo(size, p);
      ctx.stroke();
    }
  }

  function drawCell(x, y, fill, radius = 8, strokeColor = null, strokeWidth = 1) {
    const px = x * cell + 2;
    const py = y * cell + 2;
    const w = cell - 4;
    const h = cell - 4;
    const r = Math.min(radius, w / 2, h / 2);
    ctx.fillStyle = fill;
    ctx.beginPath();
    ctx.moveTo(px + r, py);
    ctx.arcTo(px + w, py, px + w, py + h, r);
    ctx.arcTo(px + w, py + h, px, py + h, r);
    ctx.arcTo(px, py + h, px, py, r);
    ctx.arcTo(px, py, px + w, py, r);
    ctx.closePath();
    ctx.fill();

    if (strokeColor) {
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = strokeWidth;
      ctx.stroke();
    }
  }

  function render(t = 0) {
    drawBackground();

    // food (pulse when running)
    const pulse = state.running ? 0.5 + 0.5 * Math.sin(t / 120) : 0;
    const foodAlpha = 0.7 + pulse * 0.3;
    drawCell(
      state.food.x,
      state.food.y,
      `rgba(14,165,233,${foodAlpha})`,
      10 + pulse * 2,
      "rgba(37,99,235,0.35)",
      1
    );

    // snake
    state.snake.forEach((p, i) => {
      const isHead = i === 0;
      const headGlow = isHead && state.running ? 10 : 0;
      if (headGlow) {
        ctx.save();
        ctx.shadowColor = "rgba(37,99,235,0.55)";
        ctx.shadowBlur = headGlow;
      }
      drawCell(
        p.x,
        p.y,
        isHead ? "rgba(37,99,235,1)" : "rgba(37,99,235,0.74)",
        isHead ? 12 : 10,
        "rgba(37,99,235,0.25)",
        1
      );
      if (headGlow) ctx.restore();

      // Eyes on head
      if (isHead) {
        const px = p.x * cell;
        const py = p.y * cell;
        const centerX = px + cell / 2;
        const centerY = py + cell / 2;
        const dx = state.dir.x;
        const dy = state.dir.y;
        const eyeOff = 5;
        const ex1 = centerX + (-dy * eyeOff) + dx * 1;
        const ey1 = centerY + (dx * eyeOff) + dy * 1;
        const ex2 = centerX + (dy * eyeOff) + dx * 1;
        const ey2 = centerY + (-dx * eyeOff) + dy * 1;

        ctx.fillStyle = "rgba(255,255,255,0.92)";
        ctx.beginPath();
        ctx.arc(ex1, ey1, 2.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(ex2, ey2, 2.2, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = "rgba(15,23,42,0.9)";
        ctx.beginPath();
        ctx.arc(ex1 + dx * 0.9, ey1 + dy * 0.9, 1.2, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(ex2 + dx * 0.9, ey2 + dy * 0.9, 1.2, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // overlay if paused
    if (!state.running) {
      ctx.fillStyle = "rgba(15, 23, 42, 0.05)";
      ctx.fillRect(0, 0, size, size);
      ctx.fillStyle = "rgba(15, 23, 42, 0.75)";
      ctx.font = "700 18px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.textAlign = "center";
      ctx.fillText("Snake", size / 2, size / 2 - 10);
      ctx.font = "500 13px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.fillText("Clique sur Démarrer ou appuie sur Espace", size / 2, size / 2 + 14);
    }
  }

  function setScore(v) {
    state.score = v;
    if (scoreEl) scoreEl.textContent = String(v);
    if (v > best) {
      best = v;
      localStorage.setItem("snakeBest", String(best));
      if (bestEl) bestEl.textContent = String(best);
    }
  }

  function reset() {
    state = initialState();
    placeFood();
    setScore(0);
    loseFxShown = false;
    if (btn) btn.textContent = "Démarrer";
    render(0);
  }

  function toggle() {
    state.running = !state.running;
    if (btn) btn.textContent = state.running ? "Pause" : "Démarrer";
    render(0);
  }

  function crash() {
    state.running = false;
    if (btn) btn.textContent = "Rejouer";
    if (!loseFxShown) {
      loseFxShown = true;
      showSnakeLoseFx();
    }
     shakeLayout();
    render(0);
  }

  function step() {
    state.dir = state.nextDir;
    const head = state.snake[0];
    const nh = { x: head.x + state.dir.x, y: head.y + state.dir.y };

    // walls
    if (nh.x < 0 || nh.y < 0 || nh.x >= grid || nh.y >= grid) return crash();

    // self-collision
    if (state.snake.some((s) => s.x === nh.x && s.y === nh.y)) return crash();

    state.snake.unshift(nh);

    // food
    if (nh.x === state.food.x && nh.y === state.food.y) {
      setScore(state.score + 1);
      placeFood();
      // speed up slightly
      state.tickMs = Math.max(70, state.tickMs - 2);
      shakeLayout();
    } else {
      state.snake.pop();
    }
  }

  function loop(ts) {
    if (!state.lastTick) state.lastTick = ts;
    const dt = ts - state.lastTick;
    if (state.running && dt >= state.tickMs) {
      state.lastTick = ts;
      step();
      render(ts);
    }
    requestAnimationFrame(loop);
  }

  function setDir(x, y) {
    // prevent reverse
    if (state.dir.x === -x && state.dir.y === -y) return;
    state.nextDir = { x, y };
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowUp") setDir(0, -1);
    else if (e.key === "ArrowDown") setDir(0, 1);
    else if (e.key === "ArrowLeft") setDir(-1, 0);
    else if (e.key === "ArrowRight") setDir(1, 0);
    else if (e.code === "Space") {
      e.preventDefault();
      // if game over (button says rejouer) -> reset then start
      if (btn && btn.textContent === "Rejouer") {
        reset();
        toggle();
      } else {
        toggle();
      }
    }
  });

  if (btn) {
    btn.addEventListener("click", () => {
      if (btn.textContent === "Rejouer") {
        reset();
        state.running = true;
        btn.textContent = "Pause";
        render();
      } else {
        toggle();
      }
    });
  }

  reset();
  requestAnimationFrame(loop);
})();

