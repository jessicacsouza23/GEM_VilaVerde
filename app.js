const navByRole = {
  Master: ["GEMs", "Usuários mestres", "Visão da plataforma"],
  Secretaria: ["Visão geral", "Planejamento e rodízio", "Turmas e pessoas", "Chamada", "Relatórios", "Documentos", "Provas", "Logística"],
  Professora: ["Minhas aulas", "Envio de documentos", "Provas", "Analítico IA", "Mensagens"],
  Aluna: ["Minhas lições", "Boletim", "Documentos", "Mensagens"]
};

const exampleSchedule = [
  ["08:50 — 09:35", ["Sala 8 · Teoria", "Prof. Elaine", "Turma 1"], ["Sala 9 · Solfejo Melódico", "Prof. Roberta", "Turma 2"], ["Salas 1–7 · Prática + Solfejo", "Professoras em rodízio", "Turma 3"]],
  ["09:40 — 10:25", ["Sala 8 · Teoria", "Prof. Ester", "Turma 2"], ["Sala 9 · Solfejo Melódico", "Prof. Juliana", "Turma 3"], ["Salas 1–7 · Prática + Solfejo", "Professoras em rodízio", "Turma 1"]],
  ["10:30 — 11:15", ["Sala 8 · Teoria", "Prof. Cássia", "Turma 3"], ["Sala 9 · Solfejo Melódico", "Prof. Kamyla", "Turma 1"], ["Salas 1–7 · Prática + Solfejo", "Professoras em rodízio", "Turma 2"]]
];

const state = { role: "Secretaria", name: "Coordenação", page: "Visão geral" };
const $ = (selector) => document.querySelector(selector);
let installPrompt;

function renderNavigation() {
  const nav = $("#navigation");
  nav.innerHTML = navByRole[state.role].map((item, index) => `<button class="nav-link ${index === 0 ? "active" : ""}" data-page="${item}">${iconFor(item)} ${item}</button>`).join("");
  nav.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => {
    state.page = button.dataset.page;
    nav.querySelectorAll("button").forEach((link) => link.classList.toggle("active", link === button));
    renderPage();
    $(".sidebar").classList.remove("open");
  }));
}

function iconFor(page) {
  return ({ "GEMs":"🏫", "Usuários mestres":"🔐", "Visão da plataforma":"🌐", "Visão geral":"🏠", "Planejamento e rodízio":"🗓️", "Turmas e pessoas":"👥", "Chamada":"✅", "Relatórios":"📊", "Documentos":"📁", "Provas":"📝", "Logística":"⚙️", "Minhas aulas":"👩‍🏫", "Envio de documentos":"📤", "Analítico IA":"📈", "Mensagens":"💬", "Minhas lições":"🎼", "Boletim":"🎓" }[page] || "•");
}

function scheduleMarkup() {
  const cells = exampleSchedule.map(([time, ...classes]) => `<div class="time">${time}</div>${classes.map(([title, teacher, group]) => `<article class="room"><strong>${title}</strong><span>${teacher}</span><small>${group}</small></article>`).join("")}`).join("");
  return `<div class="schedule"><div class="schedule-grid"><div class="schedule-head">Horário</div><div class="schedule-head">Bloco 1</div><div class="schedule-head">Bloco 2</div><div class="schedule-head">Bloco 3</div>${cells}</div></div>`;
}

async function renderMasterGems(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ADMINISTRAÇÃO DA PLATAFORMA</p><h2>GEMs cadastrados</h2><p>Crie e administre as unidades sem acessar os dados pedagógicos de cada uma.</p></section><div class="section-title"><h2>Novo GEM</h2><p>O identificador será usado internamente e não pode ser repetido.</p></div><section class="panel"><div class="form-grid"><div><label for="gem-nome">Nome do GEM</label><input id="gem-nome" placeholder="Ex.: GEM Musical Central"></div><div><label for="gem-slug">Identificador</label><input id="gem-slug" placeholder="Ex.: gem-central"></div><button id="criar-gem" class="primary-action" type="button">Cadastrar GEM</button></div><p id="gem-feedback" class="hidden" role="status"></p></section><div class="section-title"><h2>Unidades</h2><p>Somente a Master visualiza esta lista.</p></div><section class="panel"><div id="gem-lista" class="gem-list"><div class="empty">Carregando GEMs...</div></div></section>`;
  const lista = $("#gem-lista");
  const carregar = async () => {
    try {
      const gems = await window.GemData.listarGems();
      lista.innerHTML = gems.length ? gems.map((gem) => `<article class="gem-row"><div><strong>${escapeHtml(gem.nome)}</strong><span>${escapeHtml(gem.slug)}</span></div><span class="badge">${gem.ativo ? "Ativo" : "Inativo"}</span></article>`).join("") : `<div class="empty">Nenhum GEM cadastrado.</div>`;
    } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#criar-gem").addEventListener("click", async () => {
    const feedback = $("#gem-feedback");
    feedback.className = "hidden";
    try {
      await window.GemData.criarGem($("#gem-nome").value, $("#gem-slug").value);
      feedback.textContent = "GEM cadastrado com sucesso.";
      feedback.className = "action-ok";
      $("#gem-nome").value = ""; $("#gem-slug").value = "";
      await carregar();
    } catch (error) { feedback.textContent = error.message; feedback.className = "action-error"; }
  });
  await carregar();
}

function escapeHtml(value) {
  const node = document.createElement("span"); node.textContent = String(value ?? ""); return node.innerHTML;
}

async function renderPage() {
  $("#page-title").textContent = state.page;
  const content = $("#page-content");
  if (state.role === "Master" && state.page === "GEMs") {
    await renderMasterGems(content);
    return;
  }
  if (state.page === "Visão geral" || state.page === "Minhas aulas" || state.page === "Minhas lições") {
    const greeting = state.role === "Secretaria" ? "O painel administrativo será migrado módulo por módulo, sem alterar os dados atuais." : "A agenda e os registros desta tela serão ligados ao mesmo histórico já usado no GEM.";
    content.innerHTML = `<section class="intro-card"><p class="eyebrow">MIGRAÇÃO PARA APLICATIVO</p><h2>Olá, ${state.name}.</h2><p>${greeting} Esta é uma base visual: ainda não grava nem altera nenhuma informação.</p></section><div class="grid"><div class="metric"><strong>Preservado</strong><span>Banco e histórico</span></div><div class="metric"><strong>Em paralelo</strong><span>Streamlit continua ativo</span></div><div class="metric"><strong>Próximo passo</strong><span>Login seguro</span></div></div><div class="section-title"><h2>Rodízio — referência visual</h2><p>Exemplo; dados reais serão carregados do Supabase.</p></div>${scheduleMarkup()}`;
  } else if (state.page === "Planejamento e rodízio") {
    content.innerHTML = `<section class="intro-card"><p class="eyebrow">RODÍZIO</p><h2>Mesmo formato, nova tecnologia.</h2><p>Antes de permitir geração oficial, esta tela vai reproduzir as regras atuais e comparar o resultado com o Streamlit para a mesma data.</p></section><div class="section-title"><h2>Mural de referência</h2><p>Sem gravação nesta etapa.</p></div>${scheduleMarkup()}`;
  } else {
    content.innerHTML = `<section class="panel empty"><h2>${iconFor(state.page)} ${state.page}</h2><p>Este módulo será trazido depois de o login seguro estar conectado ao mesmo banco do GEM.</p></section>`;
  }
}

$("#entrar").addEventListener("click", async () => {
  const botao = $("#entrar");
  const erro = $("#login-error");
  erro.classList.add("hidden");
  botao.disabled = true;
  botao.textContent = "Entrando...";
  try {
    const conta = await window.GemData?.autenticar($("#nome").value, $("#senha").value);
    if (!conta) throw new Error("A autenticação do GEM ainda não está disponível.");
    state.role = conta.role;
    state.name = conta.name;
  } catch (error) {
    erro.textContent = error?.message || "Não foi possível entrar agora.";
    erro.classList.remove("hidden");
    botao.disabled = false;
    botao.textContent = "Entrar";
    return;
  }
  state.page = navByRole[state.role][0];
  $("#profile-name").textContent = state.name;
  $("#profile-role").textContent = state.role;
  $("#avatar").textContent = state.name.slice(0, 1).toUpperCase();
  $("#login-screen").classList.add("hidden"); $("#app-screen").classList.remove("hidden");
  renderNavigation(); await renderPage();
  botao.disabled = false;
  botao.textContent = "Entrar";
});
$("#sair").addEventListener("click", () => { $("#app-screen").classList.add("hidden"); $("#login-screen").classList.remove("hidden"); });
$("#menu-button").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
  $("#install-app").classList.remove("hidden");
});
$("#install-app").addEventListener("click", async () => {
  if (!installPrompt) return;
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt = undefined;
  $("#install-app").classList.add("hidden");
});
window.addEventListener("appinstalled", () => $("#install-app").classList.add("hidden"));
if ("serviceWorker" in navigator) navigator.serviceWorker.register("service-worker.js");

// A marca é a primeira informação real carregada do Supabase. Os módulos
// pessoais entram em seguida, somente depois do login seguro multi-GEM.
window.GemData?.carregarIdentidade().then((identidade) => {
  const status = document.querySelector(".status");
  if (identidade?.connected) {
    status.innerHTML = "<span></span> Conectado ao GEM";
    if (identidade.logoUrl) {
      const marcas = document.querySelectorAll(".brand-mark, .sidebar-brand span");
      marcas.forEach((marca) => {
        marca.textContent = "";
        marca.style.backgroundImage = `url('${identidade.logoUrl}')`;
        marca.style.backgroundSize = "cover";
        marca.style.backgroundPosition = "center";
      });
    }
  }
});
