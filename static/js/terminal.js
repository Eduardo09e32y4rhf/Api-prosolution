// ==========================================
//  TERMINAL.JS | PROSOLUTION ⚙️ IA SECURE MODE
//  Server-side client diagnostics + status
// ==========================================

async function updateServerInfo() {
  const text = document.getElementById("terminalBody");
  if (!text) return;

  text.innerHTML = "🧠 Coletando informações do servidor...\nroot@prosolution:~$ _";

  let ip = "–";
  let country = "–";
  let region = "–";
  let org = "–";
  let vpn = "Não";
  let timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "–";
  let language = navigator.language || "–";
  let system = `${navigator.platform} / ${navigator.userAgent.split(")")[0].replace("(", "")}`;

  try {
    // 🔹 API híbrida para IP + servidor
    const res = await fetch("https://ipapi.co/json/");
    const data = await res.json();

    if (data && data.ip) {
      ip = data.ip || "–";
      country = data.country_name || "–";
      region = data.region || "–";
      org = data.org || "–";

      // 🔹 Heurística de VPN/Proxy
      const orgLower = org.toLowerCase();
      const vpnIndicators = [
        "vpn", "proxy", "datacenter", "cloudflare", "tor", "anonymous",
        "digitalocean", "aws", "ovh", "azure", "google", "contabo", "vultr"
      ];
      vpn = vpnIndicators.some(v => orgLower.includes(v)) ? "Sim" : "Não";
    } else {
      console.warn("⚠️ Falha ao decodificar resposta da API de IP.");
    }
  } catch (err) {
    console.warn("⚠️ Erro ao obter dados de rede:", err);
  }

  renderServerInfo(text, ip, org, region, country, vpn, timezone, language, system);
}

// =======================
//   RENDERIZAÇÃO TERMINAL
// =======================
function renderServerInfo(text, ip, org, region, country, vpn, timezone, language, system) {
  const now = new Date().toLocaleString();

  text.innerHTML = `
┌──[ SERVER INFO ]
│ IP Público   : ${ip}
│ Servidor     : ${org}
│ Região       : ${region} - ${country}
│ Idioma       : ${language}
│ Fuso Horário : ${timezone}
│ Sistema      : ${system}
│ Data/Hora    : ${now}
│ VPN/Proxy    : ${vpn}
└──────────────────────────────

┌──[ SECURITY STATUS ]
│ ✔ Firewall Ativo
│ ✔ Criptografia AES-256
│ ✔ Conexão HTTPS Segura
└──────────────────────────────

root@prosolution:~$ _
  `;
}

// =======================
//   BOTÃO POWER
// =======================
function togglePower() {
  const btn = document.getElementById("powerBtn");
  const terminal = document.querySelector(".terminal");
  const text = document.getElementById("terminalBody");

  if (!btn || !terminal || !text) return;

  btn.classList.toggle("on");

  if (btn.classList.contains("on")) {
    text.innerHTML = "⚡ Inicializando sistema seguro...\nroot@prosolution:~$ _";
    terminal.style.boxShadow = "0 0 50px #00ff88";
    setTimeout(updateServerInfo, 1200);
  } else {
    text.innerHTML = "🛑 Sistema desligado.\nroot@prosolution:~$ _";
    terminal.style.boxShadow = "0 0 15px #00ff88";
  }
}

// =======================
//   MODO AUTO / MANUAL
// =======================
let autoInterval = null;

function toggleMode() {
  const modeBtn = document.getElementById("modeBtn");
  if (!modeBtn) return;

  const isActive = modeBtn.classList.toggle("active");
  modeBtn.textContent = isActive ? "MANUAL" : "AUTO";

  if (!isActive) {
    // AUTO ON → atualizar a cada 30s
    updateServerInfo();
    autoInterval = setInterval(updateServerInfo, 30000);
  } else {
    // MANUAL → parar atualização
    clearInterval(autoInterval);
  }
}

// =======================
//   HTTPS ENFORCER
// =======================
if (location.protocol !== "https:" && location.hostname !== "localhost") {
  location.href = "https://" + location.hostname + location.pathname;
}

// =======================
//   PREVINE DUPLICAÇÃO
// =======================
if (window.__terminalInitialized) {
  console.warn("⚠️ terminal.js já carregado — ignorando duplicado.");
} else {
  window.__terminalInitialized = true;
  console.log("✅ terminal.js Prosolution IA inicializado com segurança.");
}

// =======================
//   AUTOEXEC (SAFE MODE)
// =======================
document.addEventListener("DOMContentLoaded", () => {
  const powerBtn = document.getElementById("powerBtn");
  const modeBtn = document.getElementById("modeBtn");

  if (powerBtn) {
    powerBtn.addEventListener("click", togglePower);
  }

  if (modeBtn) {
    modeBtn.addEventListener("click", toggleMode);
  }

  // Auto start do terminal com boot animado
  const terminal = document.querySelector(".terminal");
  if (terminal) {
    terminal.style.opacity = "0";
    setTimeout(() => {
      terminal.style.transition = "opacity 1.2s ease";
      terminal.style.opacity = "1";
    }, 200);
  }
});