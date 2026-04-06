(() => {
  const root = document.getElementById("flashcards");
  if (!root) return;

  const frontEl = document.getElementById("fcFront");
  const backEl = document.getElementById("fcBack");
  const counterEl = document.getElementById("fcCounter");
  const btnFlip = document.getElementById("fcFlip");
  const btnNext = document.getElementById("fcNext");
  const btnShuffle = document.getElementById("fcShuffle");

  const CARDS = [
    { front: "Quand ton RBAC est nickel…", back: "…et que même l’IDOR dit “GG”." },
    { front: "Le prof : “on fait un pentest”", back: "Moi : ouvre ZAP → “baseline” → panique contrôlée." },
    { front: "Moi : “c’est sécurisé”", back: "Bandit : “B110” — moi : “bon… presque”." },
    { front: "Quand tu vois 'unsafe-inline'", back: "CSP : “on en reparle après le rendu”." },
    { front: "Le devoir : “pas d’IA générative”", back: "Moi : “OK, je fais du secure coding… manuellement”." },
    { front: "Session fixation ? ", back: "session.clear() au login — bye bye l’ancien cookie." },
    { front: "SQL injection mood", back: "Requêtes paramétrées only. CONCAT = carton rouge." },
    { front: "CSRF token", back: "invisible mais présent — comme un ninja." },
    { front: "Quand tu pushes sur main", back: "CI/CD : flake8 → pip-audit → bandit → ZAP. Respire." },
    { front: "Le bug à 2h du mat", back: "“Unknown column” — migration idempotente → paix intérieure." },
  ];

  let deck = CARDS.slice();
  let idx = 0;
  let flipped = false;

  function shuffle(a) {
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function render() {
    const card = deck[idx];
    if (frontEl) frontEl.textContent = card.front;
    if (backEl) backEl.textContent = card.back;
    if (counterEl) counterEl.textContent = `${idx + 1}/${deck.length}`;
    root.classList.toggle("is-flipped", flipped);
  }

  function flip() {
    flipped = !flipped;
    render();
  }

  function next() {
    idx = (idx + 1) % deck.length;
    flipped = false;
    render();
  }

  function reshuffle() {
    deck = shuffle(deck.slice());
    idx = 0;
    flipped = false;
    render();
  }

  btnFlip?.addEventListener("click", flip);
  btnNext?.addEventListener("click", next);
  btnShuffle?.addEventListener("click", reshuffle);

  // Raccourcis clavier quand la section est visible
  document.addEventListener("keydown", (e) => {
    const rect = root.getBoundingClientRect();
    const onScreen = rect.bottom > 0 && rect.top < window.innerHeight;
    if (!onScreen) return;

    if (e.code === "Space") {
      e.preventDefault();
      flip();
    } else if (e.key.toLowerCase() === "n") {
      next();
    } else if (e.key.toLowerCase() === "r") {
      reshuffle();
    }
  });

  reshuffle();
})();

