(() => {
  const root = document.getElementById("voiceAssistant");
  if (!root) return;

  const mascot = document.getElementById("voiceAssistant");
  const statusEl = document.getElementById("vaStatus");
  const btn = document.getElementById("vaToggle");

  const userEl = document.getElementById("username");
  const passEl = document.getElementById("password");
  const form = document.getElementById("loginForm");

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    statusEl.textContent = "Reconnaissance vocale indisponible sur ce navigateur.";
    btn.disabled = true;
    return;
  }

  const rec = new SpeechRecognition();
  rec.lang = "fr-FR";
  rec.interimResults = false;
  rec.maxAlternatives = 1;

  let listening = false;

  function setListening(v) {
    listening = v;
    btn.textContent = listening ? "Stop" : "Parler";
    mascot?.classList.toggle("listening", listening);
    statusEl.textContent = listening
      ? "J’écoute… Dis: “focus identifiant”, “effacer”, “se connecter”, “remplir identifiant <nom>”."
      : "Assistant prêt. Clique “Parler” puis donne une commande.";
  }

  function normalize(t) {
    return (t || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "")
      .trim();
  }

  function setUsernameFrom(text) {
    // Ex: "remplir identifiant prof1"
    const m = text.match(/remplir\s+identifiant\s+(.+)$/);
    if (!m) return false;
    const v = m[1].trim().replace(/[^\w.-]/g, "");
    if (v && userEl) userEl.value = v;
    return true;
  }

  function runCommand(raw) {
    const t = normalize(raw);
    if (!t) return;

    if (setUsernameFrom(t)) return;

    if (t.includes("focus identifiant") || t.includes("focus login") || t.includes("focus username")) {
      userEl?.focus();
      return;
    }
    if (t.includes("focus mot de passe") || t.includes("focus password")) {
      passEl?.focus();
      return;
    }
    if (t === "effacer" || t.includes("effacer tout")) {
      if (userEl) userEl.value = "";
      if (passEl) passEl.value = "";
      return;
    }
    if (t.includes("se connecter") || t.includes("connecte moi") || t.includes("connexion")) {
      // On évite de dicter le mot de passe (meilleure pratique).
      // L'utilisateur peut le saisir manuellement, puis dire "se connecter".
      if (form) form.requestSubmit();
      return;
    }
    if (t.includes("stop") || t.includes("arrete")) {
      if (listening) rec.stop();
      return;
    }
  }

  rec.onstart = () => setListening(true);
  rec.onend = () => setListening(false);
  rec.onerror = () => setListening(false);
  rec.onresult = (e) => {
    const said = e.results?.[0]?.[0]?.transcript || "";
    statusEl.textContent = `Commande: “${said}”`;
    runCommand(said);
  };

  btn.addEventListener("click", () => {
    if (listening) rec.stop();
    else rec.start();
  });

  setListening(false);
})();

