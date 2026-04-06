(() => {
  const root = document.getElementById("blackjack");
  if (!root) return;

  const playerCardsEl = document.getElementById("bjPlayerCards");
  const dealerCardsEl = document.getElementById("bjDealerCards");
  const playerScoreEl = document.getElementById("bjPlayerScore");
  const dealerScoreEl = document.getElementById("bjDealerScore");
  const statusEl = document.getElementById("bjStatus");
  const bestEl = document.getElementById("bjBest");

  const btnNew = document.getElementById("bjNew");
  const btnHit = document.getElementById("bjHit");
  const btnStand = document.getElementById("bjStand");

  let best = Number(localStorage.getItem("bjBest") || "0");
  if (bestEl) bestEl.textContent = String(best);

  const SUITS = ["♠", "♥", "♦", "♣"];
  const RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];

  function makeDeck() {
    const d = [];
    for (const s of SUITS) {
      for (const r of RANKS) d.push({ r, s });
    }
    // shuffle Fisher-Yates
    for (let i = d.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [d[i], d[j]] = [d[j], d[i]];
    }
    return d;
  }

  function cardColor(c) {
    return c.s === "♥" || c.s === "♦" ? "red" : "black";
  }

  function score(hand) {
    // A = 11 or 1
    let total = 0;
    let aces = 0;
    for (const c of hand) {
      if (c.r === "A") {
        aces++;
        total += 11;
      } else if (["K", "Q", "J"].includes(c.r)) total += 10;
      else total += Number(c.r);
    }
    while (total > 21 && aces > 0) {
      total -= 10;
      aces--;
    }
    return total;
  }

  function renderCards(el, hand, { hideFirst = false } = {}) {
    if (!el) return;
    el.innerHTML = "";
    hand.forEach((c, idx) => {
      const div = document.createElement("div");
      if (hideFirst && idx === 0) {
        div.className = "bj-card back";
        div.title = "Carte cachée";
      } else {
        div.className = `bj-card ${cardColor(c)}`;
        div.textContent = `${c.r}${c.s}`;
      }
      el.appendChild(div);
    });
  }

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function setButtons({ canHit, canStand }) {
    if (btnHit) btnHit.disabled = !canHit;
    if (btnStand) btnStand.disabled = !canStand;
  }

  let deck = [];
  let player = [];
  let dealer = [];
  let finished = false;
  let winReported = false;
  let winFxShown = false;

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function showBigWinFx() {
    const reduced = prefersReducedMotion();
    const layer = document.createElement("div");
    layer.className = "fx-layer fx-dim fx-bjwin-layer";

    layer.innerHTML = `
      <div class="fx-bjwin-burst" aria-hidden="true"></div>
      <div class="fx-bjwin-title">Big Win <span>20/20</span> !!!</div>
      <div class="fx-bjwin-slot" aria-hidden="true">
        <div class="fx-bjwin-slot-reels">
          <div class="fx-bjwin-reel"></div>
          <div class="fx-bjwin-reel"></div>
          <div class="fx-bjwin-reel"></div>
        </div>
        <div class="fx-bjwin-slot-bottom"></div>
      </div>
      <div class="fx-bjwin-coins" aria-hidden="true"></div>
      <div class="fx-bjwin-cards" aria-hidden="true"></div>
    `;

    const coinsWrap = layer.querySelector(".fx-bjwin-coins");
    const cardsWrap = layer.querySelector(".fx-bjwin-cards");

    // Pièces (nombre réduit si réduction de mouvement)
    const coinCount = reduced ? 45 : 110;
    for (let i = 0; i < coinCount; i++) {
      const coin = document.createElement("div");
      coin.className = "fx-bjwin-coin";

      const dx = (Math.random() * 2 - 1) * (200 + Math.random() * 520);
      const dy = (Math.random() * 2 - 1) * (90 + Math.random() * 260);
      const delay = (Math.random() * (reduced ? 0.25 : 0.55)).toFixed(2) + "s";

      coin.style.setProperty("--dx", `${dx}px`);
      coin.style.setProperty("--dy", `${dy}px`);
      coin.style.setProperty("--delay", delay);

      coinsWrap.appendChild(coin);
    }

    // Cartes qui fusent (légères, pas stroboscopiques)
    const cardsCount = reduced ? 10 : 22;
    const sampleRanks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
    const sampleSuits = ["♠", "♥", "♦", "♣"];
    for (let i = 0; i < cardsCount; i++) {
      const card = document.createElement("div");
      card.className = "fx-bjwin-card";
      const tx = (Math.random() * 2 - 1) * (280 + Math.random() * 620);
      const ty = (Math.random() * 2 - 1) * (120 + Math.random() * 330);
      const rot = (Math.random() * 2 - 1) * 220;

      card.style.setProperty("--tx", `${tx}px`);
      card.style.setProperty("--ty", `${ty}px`);
      card.style.setProperty("--rot", `${rot}deg`);

      const r = sampleRanks[Math.floor(Math.random() * sampleRanks.length)];
      const s = sampleSuits[Math.floor(Math.random() * sampleSuits.length)];
      card.textContent = `${r}${s}`;
      cardsWrap.appendChild(card);
    }

    document.body.appendChild(layer);
    window.setTimeout(() => layer.remove(), reduced ? 2400 : 3800);
  }

  function shakeLayoutSoft() {
    const root = document.querySelector(".app") || document.body;
    if (!root) return;
    root.classList.add("layout-shake");
    window.setTimeout(() => root.classList.remove("layout-shake"), 260);
  }

  function updateBest(wins) {
    if (wins > best) {
      best = wins;
      localStorage.setItem("bjBest", String(best));
      if (bestEl) bestEl.textContent = String(best);
    }
  }

  let winStreak = Number(localStorage.getItem("bjWinStreak") || "0");
  updateBest(winStreak);

  function resetRound() {
    deck = makeDeck();
    player = [deck.pop(), deck.pop()];
    dealer = [deck.pop(), deck.pop()];
    finished = false;
    winReported = false;
    winFxShown = false;

    const p = score(player);
    if (p === 21) {
      // blackjack immédiat
      stand(true);
      return;
    }
    render(false);
    setStatus("À toi : Tirer ou Rester.");
    setButtons({ canHit: true, canStand: true });
  }

  function render(revealDealer = false) {
    renderCards(playerCardsEl, player);
    renderCards(dealerCardsEl, dealer, { hideFirst: !revealDealer });

    const p = score(player);
    const d = score(dealer);
    if (playerScoreEl) playerScoreEl.textContent = String(p);
    if (dealerScoreEl) dealerScoreEl.textContent = revealDealer ? String(d) : "??";
  }

  function endRound(outcome) {
    finished = true;
    render(true);
    setButtons({ canHit: false, canStand: false });

    if (outcome === "WIN") {
      if (!winFxShown) {
        winFxShown = true;
        showBigWinFx();
      }
      shakeLayoutSoft();
      // Notifie le backend (bonus note 20/20 + historique) une seule fois par manche.
      if (!winReported) {
        winReported = true;
        const tokenEl = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = tokenEl ? tokenEl.getAttribute("content") : "";
        fetch("/games/blackjack/win", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
            "X-CSRF-Token": csrfToken,
          },
          body: JSON.stringify({}),
        })
          .then(() => {
            // rien
          })
          .catch(() => {
            // ignore : jeu côté client OK, note non critique
          });
      }
      winStreak += 1;
      localStorage.setItem("bjWinStreak", String(winStreak));
      updateBest(winStreak);
      setStatus(`Gagné ! Série: ${winStreak}. Clique “Nouvelle partie”.`);
    } else if (outcome === "LOSE") {
      winStreak = 0;
      localStorage.setItem("bjWinStreak", "0");
      setStatus("Perdu. Clique “Nouvelle partie”.");
    } else {
      // PUSH
      setStatus("Égalité. Clique “Nouvelle partie”.");
    }
  }

  function hit() {
    if (finished) return;
    player.push(deck.pop());
    const p = score(player);
    render(false);
    if (p > 21) endRound("LOSE");
    else setStatus("À toi : Tirer ou Rester.");
  }

  function stand(fromBlackjack = false) {
    if (finished) return;
    // dealer plays (reveal)
    let d = score(dealer);
    while (d < 17) {
      dealer.push(deck.pop());
      d = score(dealer);
    }
    const p = score(player);
    render(true);

    if (fromBlackjack && p === 21 && d !== 21) return endRound("WIN");
    if (d > 21) return endRound("WIN");
    if (p > d) return endRound("WIN");
    if (p < d) return endRound("LOSE");
    return endRound("PUSH");
  }

  if (btnNew) btnNew.addEventListener("click", resetRound);
  if (btnHit) btnHit.addEventListener("click", hit);
  if (btnStand) btnStand.addEventListener("click", () => stand(false));

  document.addEventListener("keydown", (e) => {
    if (!root) return;
    // raccourcis seulement si la section est visible à l'écran
    const rect = root.getBoundingClientRect();
    const onScreen = rect.bottom > 0 && rect.top < window.innerHeight;
    if (!onScreen) return;

    if (e.key.toLowerCase() === "h") hit();
    else if (e.key.toLowerCase() === "s") stand(false);
    else if (e.key.toLowerCase() === "n") resetRound();
  });

  // init
  resetRound();
})();

