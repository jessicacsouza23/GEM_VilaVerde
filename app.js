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

function casaCategoria(tipo) {
  if (tipo === "Casa_MSA") return "Solfejo";
  if (tipo === "Casa_Canto") return "Solfejo Melódico";
  if (["Casa_Teoria", "Casa_Teoria_Prof", "Casa_Apostila_Teoria", "Casa_Apostila_Teoria_Prof", "Casa_Apostila_Prof"].includes(tipo)) return "Teoria";
  if (tipo === "Casa_Apostila" || String(tipo || "").startsWith("Casa_Metodo_")) return "Prática";
  return "Atividade";
}

function eResolvida(status) { return ["Resolvido", "Realizada", "Realizadas - sem pendência", "Realizada - sem pendência"].includes(status); }

async function renderMinhasAulas(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">AGENDA DA PROFESSORA</p><h2>Olá, ${escapeHtml(state.name)}.</h2><p>Escolha a data para visualizar a escala real que foi salva no rodízio.</p></section><div class="section-title"><h2>Minhas aulas</h2><p>As turmas seguem a escala daquela data, inclusive registros históricos.</p></div><section class="panel"><div class="agenda-date"><div><label for="agenda-data">Data da aula</label><input id="agenda-data" type="date" value="${hoje}"></div><button id="carregar-agenda" class="primary-action" type="button">Carregar agenda</button></div><div id="agenda-lista" class="lesson-list"></div></section>`;
  const lista = $("#agenda-lista");
  const carregar = async () => {
    lista.innerHTML = `<div class="empty">Carregando agenda...</div>`;
    try {
      const aulas = await window.GemData.agendaProfessora(state.name, $("#agenda-data").value);
      if (!aulas.length) { lista.innerHTML = `<div class="empty">Nenhuma aula encontrada para você nesta data.</div>`; return; }
      lista.innerHTML = aulas.map((aula) => `<article class="agenda-card"><h3>${escapeHtml(aula.horario)} · ${escapeHtml(aula.tipo)}</h3><p><strong>${escapeHtml(aula.local)}</strong></p><p>${aula.individual ? `Aluna: ${escapeHtml(aula.alunas[0] || "—")}` : `Alunas: ${escapeHtml(aula.alunas.join(", "))}`}</p><span class="agenda-tag">${aula.individual ? "Aula individual" : `Turma ${escapeHtml(aula.turma || "")}`}</span></article>`).join("");
    } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#carregar-agenda").addEventListener("click", carregar);
  await carregar();
}

async function renderMinhasLicoes(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">MINHAS LIÇÕES</p><h2>Olá, ${escapeHtml(state.name)}.</h2><p>Marcar como feito é apenas o seu controle. A professora continua fazendo o acompanhamento pedagógico na aula.</p></section><div class="section-title"><h2>Lições de casa</h2><p>As lições anteriores continuam disponíveis para consulta.</p></div><section class="panel"><div id="licoes-lista" class="lesson-list"><div class="empty">Carregando lições...</div></div></section>`;
  const lista = $("#licoes-lista");
  const carregar = async () => {
    try {
      const { historico, feitas } = await window.GemData.dadosAluna(state.name);
      const idsFeitos = new Set(feitas.map((item) => String(item.historico_id)));
      const licoes = historico.filter((item) => String(item.Tipo || "").startsWith("Casa_"));
      if (!licoes.length) { lista.innerHTML = `<div class="empty">Nenhuma lição de casa registrada ainda.</div>`; return; }
      lista.innerHTML = licoes.map((licao) => {
        const feito = idsFeitos.has(String(licao.id));
        return `<article class="lesson-card"><h3>${escapeHtml(casaCategoria(licao.Tipo))}</h3><p><strong>Lição:</strong> ${escapeHtml(licao.Licao_Casa || "—")}</p><span class="lesson-meta">Lançada em ${escapeHtml(licao.Data || "—")}${eResolvida(licao.Status) ? " · Corrigida" : ""}</span><br><button class="lesson-action ${feito ? "done" : ""}" data-licao="${escapeHtml(licao.id)}" data-feito="${feito}">${feito ? "✓ Feito — desfazer" : "✓ Marcar como feito"}</button></article>`;
      }).join("");
      lista.querySelectorAll("button[data-licao]").forEach((botao) => botao.addEventListener("click", async () => {
        botao.disabled = true;
        try { await window.GemData.marcarLicaoFeita(state.name, botao.dataset.licao, botao.dataset.feito !== "true"); await carregar(); }
        catch (error) { botao.disabled = false; alert(error.message); }
      }));
    } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  await carregar();
}

async function renderChamada(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">SECRETARIA</p><h2>📍 Chamada Geral</h2><p>A chamada usa apenas as alunas que constam no rodízio salvo para a data.</p></section><section class="panel"><div class="agenda-date"><div><label for="chamada-data">Data da chamada</label><input id="chamada-data" type="date" value="${hoje}"></div><button id="carregar-chamada" class="primary-action" type="button">Carregar chamada</button></div><div id="chamada-lista"><div class="empty">Carregando...</div></div></section>`;
  const lista = $("#chamada-lista");
  const carregar = async () => {
    lista.innerHTML = `<div class="empty">Carregando chamada...</div>`;
    try {
      const { alunas, chamadas, fotos } = await window.GemData.dadosChamada($("#chamada-data").value);
      if (!alunas.length) { lista.innerHTML = `<div class="empty">Não há rodízio salvo nesta data. Gere ou escolha uma escala antes da chamada.</div>`; return; }
      const porAluna = Object.fromEntries(chamadas.map((chamada) => [chamada.Aluna, chamada]));
      lista.innerHTML = `<div class="attendance-list">${alunas.map((aluna) => { const chamada = porAluna[aluna] || { Status: "Presente", Observacao: "" }; const foto = fotos[aluna] ? `<img src="${escapeHtml(fotos[aluna])}" alt="">` : `<span>${escapeHtml(aluna.slice(0, 1))}</span>`; return `<article class="attendance-row"><div class="attendance-student">${foto}<strong>${escapeHtml(aluna)}</strong></div><div class="attendance-checks"><label><input type="checkbox" data-ausente="${escapeHtml(aluna)}" ${chamada.Status === "Ausente" ? "checked" : ""}> Ausente</label><label><input type="checkbox" data-justificada="${escapeHtml(aluna)}" ${chamada.Status === "Justificada" ? "checked" : ""}> Falta justificada</label></div><input class="${chamada.Status === "Justificada" ? "" : "hidden"}" data-observacao="${escapeHtml(aluna)}" value="${escapeHtml(chamada.Observacao || "")}" placeholder="Motivo da falta justificada"></article>`; }).join("")}</div><button id="salvar-chamada" class="primary-action full-action" type="button">Salvar chamada</button><div id="chamada-retorno"></div>`;
      lista.querySelectorAll("input[data-ausente], input[data-justificada]").forEach((campo) => campo.addEventListener("change", (evento) => {
        const aluna = evento.target.dataset.ausente || evento.target.dataset.justificada;
        const ausente = lista.querySelector(`[data-ausente="${CSS.escape(aluna)}"]`);
        const justificada = lista.querySelector(`[data-justificada="${CSS.escape(aluna)}"]`);
        if (evento.target === ausente && ausente.checked) justificada.checked = false;
        if (evento.target === justificada && justificada.checked) ausente.checked = false;
        lista.querySelector(`[data-observacao="${CSS.escape(aluna)}"]`).classList.toggle("hidden", !justificada.checked);
      }));
      $("#salvar-chamada").addEventListener("click", async () => {
        const botao = $("#salvar-chamada"); botao.disabled = true;
        const registros = alunas.map((aluna) => { const justificada = document.querySelector(`[data-justificada="${CSS.escape(aluna)}"]`).checked; const ausente = document.querySelector(`[data-ausente="${CSS.escape(aluna)}"]`).checked; return { aluna, status: justificada ? "Justificada" : ausente ? "Ausente" : "Presente", observacao: justificada ? document.querySelector(`[data-observacao="${CSS.escape(aluna)}"]`).value : "" }; });
        try { await window.GemData.salvarChamada($("#chamada-data").value, registros); $("#chamada-retorno").innerHTML = `<div class="action-ok">Chamada salva para ${escapeHtml(window.GemData.dataBr($("#chamada-data").value))}.</div>`; }
        catch (error) { $("#chamada-retorno").innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; botao.disabled = false; }
      });
    } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#carregar-chamada").addEventListener("click", carregar);
  await carregar();
}

async function renderBoletim(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">BOLETIM MUSICAL</p><h2>Notas de ${escapeHtml(state.name)}</h2><p>Suas avaliações individuais, organizadas por prova e disciplina.</p></section><section class="panel"><div id="boletim-lista" class="lesson-list"><div class="empty">Carregando boletim...</div></div></section>`;
  const lista = $("#boletim-lista");
  try {
    const { avaliacoes, notas } = await window.GemData.boletimAluna(state.name);
    if (!avaliacoes.length) { lista.innerHTML = `<div class="empty">Nenhuma avaliação cadastrada ainda.</div>`; return; }
    lista.innerHTML = avaliacoes.map((avaliacao) => {
      const notasDaProva = notas.filter((nota) => String(nota.avaliacao_id) === String(avaliacao.id));
      const texto = ["Prática", "Teoria", "Solfejo"].map((disciplina) => `${disciplina}: ${notasDaProva.find((item) => item.disciplina === disciplina)?.nota ?? "Aguardando"}`).join(" · ");
      return `<article class="lesson-card"><h3>${escapeHtml(avaliacao.titulo || "Avaliação")}</h3><p>${escapeHtml(texto)}</p><span class="lesson-meta">${escapeHtml(avaliacao.data_avaliacao || "Data ainda não informada")}</span></article>`;
    }).join("");
  } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
}

function tabelaDaEscala(escala) {
  if (!escala?.length) return `<div class="empty">Ainda não existe rodízio salvo para esta data.</div>`;
  const horarios = [...new Set(escala.flatMap((linha) => Object.keys(linha).filter((chave) => !["Aluna", "_detalhes"].includes(chave))))];
  return `<div class="table-wrap"><table class="scale-table"><thead><tr><th>Aluna</th>${horarios.map((horario) => `<th>${escapeHtml(horario)}</th>`).join("")}</tr></thead><tbody>${escala.map((linha) => `<tr><th>${escapeHtml(linha.Aluna)}</th>${horarios.map((horario) => `<td>${escapeHtml(linha[horario] || "—")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function muralRodizio(escala, data, turmaPorAluna = {}) {
  if (!escala?.length) return `<div class="empty">Ainda não existe rodízio salvo para esta data.</div>`;
  const horarios = [...new Set(escala.flatMap((linha) => Object.keys(linha).filter((chave) => !["Aluna", "_detalhes"].includes(chave))))];
  const cores = { "SALA 1": "#dbeafe", "SALA 2": "#dcfce7", "SALA 3": "#fef9c3", "SALA 4": "#fee2e2", "SALA 5": "#f3e8ff", "SALA 6": "#ccfbf1", "SALA 7": "#e0f2fe", "SALA 8": "#ffedd5", "SALA 9": "#e0e7ff", "SECRETARIA": "#fef3c7" };
  const colunas = horarios.map((horario) => {
    const grupos = new Map();
    escala.forEach((linha) => { const valor = String(linha[horario] || ""); if (valor) (grupos.get(valor) || grupos.set(valor, []).get(valor)).push(linha); });
    const ordenados = [...grupos.entries()].sort(([a], [b]) => {
      const ordem = (valor) => /SALA [1-7](?:\D|$)/i.test(valor) ? 0 : /SALA 8/i.test(valor) ? 1 : /SALA 9/i.test(valor) ? 2 : 3;
      return ordem(a) - ordem(b) || a.localeCompare(b);
    });
    const cards = ordenados.map(([localProf, linhas]) => {
      const detalhe = linhas[0]._detalhes?.[horario] || {};
      const localMaiusculo = localProf.toUpperCase();
      if (/FALTA|FALTOU|AUSENTE|VAZIO|NINGUÉM/.test(localMaiusculo) && !localMaiusculo.includes("SECRETARIA")) return "";
      let titulo = localProf;
      if (/SALA 8/i.test(localMaiusculo) && !detalhe.individual) titulo += " (Teoria)";
      if (/SALA 9/i.test(localMaiusculo) && !detalhe.individual) titulo += ` (${detalhe.tipo === "Solfejo" ? "Solfejo" : "Solfejo Melódico"})`;
      if (localMaiusculo.startsWith("SECRETARIA")) titulo = "ATIVIDADE COM AS SECRETARIAS";
      const turmas = [...new Set(linhas.map((linha) => linha._detalhes?.[horario]?.turma || turmaPorAluna[linha.Aluna]).filter(Boolean))];
      const coletiva = (/SALA 8|SALA 9/i.test(localMaiusculo) && !detalhe.individual);
      const pessoas = localMaiusculo.includes("TODAS") ? "Todas as alunas" : coletiva ? (turmas.join(" + ") || "Turma") : linhas.map((linha) => linha.Aluna).join(" + ");
      const cor = Object.entries(cores).find(([sala]) => localMaiusculo.includes(sala))?.[1] || "#fff";
      return `<article class="mural-card" style="--mural-bg:${cor}"><strong>${escapeHtml(titulo)}</strong><span>${escapeHtml(pessoas)}</span></article>`;
    }).join("");
    return `<section class="mural-column"><h3>${escapeHtml(horario)}</h3>${cards}</section>`;
  }).join("");
  return `<section class="mural-print"><header><h2>Rodízio Geral das aulas - GEM Vila Verde</h2><p>Data: ${escapeHtml(data)}</p><div>Horário do café: 08:00h até 08:30h, Oração: 08:35h até 08:45h</div></header><div class="mural-columns">${colunas}</div></section>`;
}

function resumoModelo(modelo, turmas) {
  const configuracao = modelo?.configuracao || {};
  const blocos = configuracao.blocos || [];
  const atividades = configuracao.atividades || [];
  const salas = configuracao.salas || [];
  return `<section class="panel model-summary"><h3>${escapeHtml(modelo?.nome || "Modelo legado")}</h3><p><strong>${blocos.length}</strong> blocos · <strong>${Object.keys(turmas).length}</strong> turmas ativas · <strong>${salas.filter((sala) => String(sala.Uso || "").toLowerCase() === "individual").length}</strong> salas individuais</p><div class="model-chips">${atividades.map((atividade) => `<span>${escapeHtml(atividade.Atividade || "Atividade")} · ${escapeHtml(atividade.Formato || "")}</span>`).join("") || "<span>Configuração do modelo será exibida aqui.</span>"}</div></section>`;
}

function textoSeguroId(texto) { return String(texto).normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/gi, "-").replace(/(^-|-$)/g, "").toLowerCase(); }
function nomeAtividade(atividade) { return atividade === "Canto" ? "Solfejo Melódico" : atividade; }

function dadosDoModelo(modelo, turmas) {
  const config = modelo?.configuracao || {};
  const blocos = (config.blocos || []).filter((bloco) => String(bloco["Início"] || bloco.inicio || "").trim());
  const salas = (config.salas || []).filter((sala) => sala.Ativa !== false);
  const individuais = salas.filter((sala) => String(sala.Uso || "").toLowerCase() === "individual").map((sala) => String(sala.Sala || "").trim()).filter(Boolean);
  const atividades = config.atividades || [];
  const coletivas = atividades.filter((atividade) => String(atividade.Formato || "").toLowerCase() === "turma").map((atividade) => ({ nome: nomeAtividade(atividade.Atividade), sala: String(atividade["Sala sugerida"] || "").trim() }));
  const componentes = atividades.filter((atividade) => String(atividade.Formato || "").toLowerCase() === "individual").map((atividade) => nomeAtividade(atividade.Atividade));
  const turmasAtivas = (config.turmas || []).filter((turma) => turma["Ativa no modelo"] !== false).map((turma) => String(turma.Turma || "").trim()).filter((turma) => turmas[turma]);
  return { config, blocos, individuais, coletivas, componentes, turmas: turmasAtivas };
}

function memoriaDoRodizio(escalas, dataBr, alunas, salasIndividuais) {
  const memoria = Object.fromEntries(alunas.map((aluna) => [aluna, { professoras: [], salas: [], ultima: null }]));
  (escalas || []).filter((item) => String(item.id || "") < dataBr).forEach((item) => (item.escala || []).forEach((linha) => {
    const dados = linha._detalhes || {};
    Object.entries(linha).forEach(([horario, valor]) => {
      if (["Aluna", "_detalhes"].includes(horario) || !memoria[linha.Aluna] || !String(valor).includes("|")) return;
      const detalhe = dados[horario] || {};
      const sala = String(valor).split("|")[0].trim();
      if (!detalhe.individual && !salasIndividuais.includes(sala)) return;
      const textoProf = String(valor).split("|").slice(1).join("|").trim();
      const pratica = detalhe.professoras_componentes?.Prática || textoProf.replace(/^.*Prática:\s*/i, "").split("·")[0].trim();
      if (!pratica) return;
      memoria[linha.Aluna].professoras.push(pratica);
      memoria[linha.Aluna].salas.push(sala);
      memoria[linha.Aluna].ultima = pratica;
    });
  }));
  return memoria;
}

function gerarEscalaModelo(base, modelo, opcoes) {
  const { config, blocos, individuais, coletivas, componentes, turmas } = dadosDoModelo(modelo, base.turmas);
  const erros = [];
  if (!blocos.length || !turmas.length || !individuais.length || !componentes.length) return { erros: ["Complete o modelo com blocos, turmas, salas individuais e atividades individuais."], escala: [] };
  if (coletivas.length + 1 > blocos.length || turmas.length > coletivas.length + 1) return { erros: ["O modelo não possui posições suficientes para as turmas ativas."], escala: [] };
  turmas.forEach((turma) => { if (base.turmas[turma].length > individuais.length) erros.push(`${turma} tem mais alunas do que salas individuais disponíveis.`); });
  if (erros.length) return { erros, escala: [] };
  const alunas = turmas.flatMap((turma) => base.turmas[turma]);
  const memoria = memoriaDoRodizio(base.escalasAnteriores, window.GemData.dataBr(opcoes.data), alunas, individuais);
  const escala = Object.fromEntries(alunas.map((aluna) => [aluna, { Aluna: aluna, _detalhes: {} }]));
  const posicoes = [...coletivas.map((item) => item.nome), "__individual__"];
  const indiceTeoria = posicoes.findIndex((item) => window.GemData.normalizar(item) === "TEORIA");
  const inicio = {};
  if (opcoes.turmaInicioTeoria && indiceTeoria >= 0) {
    const ordem = [posicoes[indiceTeoria], ...posicoes.filter((item) => item !== posicoes[indiceTeoria] && item !== "__individual__"), "__individual__"];
    const indiceEscolhido = turmas.indexOf(opcoes.turmaInicioTeoria);
    turmas.forEach((turma, indice) => { inicio[turma] = ordem[(indice - indiceEscolhido + ordem.length) % ordem.length]; });
  }
  const indisponiveis = new Set(base.folga?.professoras || []);
  const habilitadas = config.professoras_habilitadas || {};
  const horarios = blocos.map((bloco, indice) => window.GemData.horarioDoBloco(bloco, indice));
  const salaDaProfessora = {};
  blocos.forEach((bloco, indiceBloco) => {
    const horario = horarios[indiceBloco];
    const usadas = new Set();
    const turmasNoBloco = turmas.map((turma, indiceTurma) => {
      const primeira = inicio[turma] || posicoes[indiceTurma % posicoes.length];
      return { turma, posicao: posicoes[(posicoes.indexOf(primeira) + indiceBloco) % posicoes.length] };
    }).sort((a, b) => Number(a.posicao === "__individual__") - Number(b.posicao === "__individual__"));
    for (const { turma, posicao } of turmasNoBloco) {
      const alunasDaTurma = base.turmas[turma];
      const bloqueadas = new Set([...indisponiveis, ...Object.entries(opcoes.saidas || {}).filter(([, ultimo]) => horarios.indexOf(ultimo) < indiceBloco).map(([professora]) => professora)]);
      if (posicao !== "__individual__") {
        const atividade = coletivas.find((item) => item.nome === posicao);
        const opcoesArea = habilitadas[posicao] || habilitadas[posicao === "Solfejo Melódico" ? "Canto" : posicao] || base.professoras;
        const escolhida = opcoes.coletivas?.[posicao]?.[turma];
        const candidatas = opcoesArea.filter((professora) => base.professoras.includes(professora) && !bloqueadas.has(professora) && !usadas.has(professora));
        const professora = escolhida || candidatas[indiceBloco % Math.max(candidatas.length, 1)];
        if (!professora || !candidatas.includes(professora)) { erros.push(`${escolhida || "Nenhuma professora"} não está disponível para ${posicao} — ${turma} em ${horario}.`); continue; }
        usadas.add(professora);
        alunasDaTurma.forEach((aluna) => { escala[aluna][horario] = `${atividade?.sala || "Sala coletiva"} | ${professora}`; escala[aluna]._detalhes[horario] = { tipo: posicao, individual: false, turma }; });
        continue;
      }
      const livres = base.professoras.filter((professora) => !bloqueadas.has(professora) && !usadas.has(professora));
      if (livres.length < alunasDaTurma.length) { erros.push(`Faltam professoras livres para o atendimento individual de ${turma} em ${horario}.`); continue; }
      const salasEmUso = new Set();
      alunasDaTurma.forEach((aluna) => {
        const mem = memoria[aluna];
        const fixa = opcoes.usarFixas ? base.fixas[window.GemData.normalizar(aluna)] : null;
        const candidatas = (fixa ? [fixa] : livres).filter((professora) => livres.includes(professora));
        const professora = candidatas.sort((a, b) => Number(a === mem.ultima) - Number(b === mem.ultima) || Number(mem.professoras.includes(a)) - Number(mem.professoras.includes(b)) || a.localeCompare(b))[0];
        let sala = salaDaProfessora[professora];
        if (!sala || salasEmUso.has(sala)) sala = individuais.filter((item) => !salasEmUso.has(item)).sort((a, b) => Number(mem.salas.includes(a)) - Number(mem.salas.includes(b)) || a.localeCompare(b))[0];
        if (!professora || !sala) { erros.push(`Não foi possível alocar ${aluna} — ${turma} em ${horario}.`); return; }
        salaDaProfessora[professora] ||= sala;
        salasEmUso.add(sala); usadas.add(professora); livres.splice(livres.indexOf(professora), 1);
        escala[aluna][horario] = `${sala} | ${professora}`;
        escala[aluna]._detalhes[horario] = { tipo: componentes.length > 1 ? "Prática + Solfejo" : componentes[0], componentes, individual: true, turma, mesma_professora_componentes: true, sala_fixa_professora: sala };
        mem.professoras.push(professora); mem.salas.push(sala); mem.ultima = professora;
      });
    }
  });
  return { erros: [...new Set(erros)], escala: Object.values(escala), horarios };
}

async function renderRodizio(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">PLANEJAMENTO E MURAL</p><h2>🗓️ Planejamento e Rodízio</h2><p>Escolha o sábado. As escalas já geradas são mantidas como histórico; uma nova escala só pode ser salva para uma data ainda vazia.</p></section><section class="panel"><div class="agenda-date"><div><label for="rodizio-data">Selecione o sábado</label><input id="rodizio-data" type="date" value="${hoje}"></div><button id="carregar-rodizio" class="primary-action" type="button">Carregar</button></div><div id="rodizio-base"><div class="empty">Carregando planejamento...</div></div></section>`;
  const area = $("#rodizio-base");
  const carregar = async () => {
    area.innerHTML = `<div class="empty">Carregando turmas, professoras, modelo e escala...</div>`;
    try {
      const base = await window.GemData.dadosRodizio($("#rodizio-data").value);
      const modelo = base.modeloEscala ? base.modelos.find((item) => item.id === base.modeloEscala) : window.GemData.modeloParaData(base.modelos, $("#rodizio-data").value);
      const turmaPorAluna = Object.fromEntries(Object.entries(base.turmas).flatMap(([turma, alunas]) => alunas.map((aluna) => [aluna, turma])));
      if (base.escala.length) { area.innerHTML = `${resumoModelo(modelo, base.turmas)}<div class="section-title"><h2>📸 Mural para print</h2><p>Este sábado está protegido: nenhuma geração substituirá esta escala.</p></div>${muralRodizio(base.escala, window.GemData.dataBr($("#rodizio-data").value), turmaPorAluna)}`; return; }
      if (!modelo) { area.innerHTML = `<div class="action-error">Não há modelo logístico vigente para esta data. Programe um modelo na Logística antes de gerar.</div>`; return; }
      const dados = dadosDoModelo(modelo, base.turmas);
      const folgas = base.folga?.professoras?.length ? base.folga.professoras.join(", ") : "Nenhuma folga informada";
      const horarios = dados.blocos.map((bloco, indice) => window.GemData.horarioDoBloco(bloco, indice));
      const camposColetivos = dados.coletivas.map((atividade) => `<section class="collective-area"><h3>${escapeHtml(atividade.nome)} <small>(${escapeHtml(atividade.sala)})</small></h3>${dados.turmas.map((turma, indice) => `<label>Prof. ${escapeHtml(atividade.nome)} — ${escapeHtml(turma)}<select data-coletiva="${escapeHtml(atividade.nome)}" data-turma="${escapeHtml(turma)}">${base.professoras.map((professora) => `<option value="${escapeHtml(professora)}" ${indice % base.professoras.length === base.professoras.indexOf(professora) ? "selected" : ""}>${escapeHtml(professora)}</option>`).join("")}</select></label>`).join("")}</section>`).join("");
      area.innerHTML = `${resumoModelo(modelo, base.turmas)}<div class="planning-grid"><section><h3>👩‍🏫 Professoras das aulas por turma</h3><p>A professora acompanha a turma quando ela chegar à atividade.</p>${camposColetivos}</section><section><h3>🔁 Rotação das turmas</h3><label class="check-line"><input id="rotacao-manual" type="checkbox"> Definir manualmente a rotação das turmas?</label><div id="opcoes-rotacao" class="hidden"><label><input type="radio" name="criterio-rotacao" value="teoria" checked> Turma que começa em Teoria</label><label><input type="radio" name="criterio-rotacao" value="individual"> Turma no último bloco de Prática + Solfejo</label><select id="turma-rotacao">${dados.turmas.map((turma) => `<option>${escapeHtml(turma)}</option>`).join("")}</select></div><h3>👑 Folgas informadas</h3><p>${escapeHtml(folgas)}</p><h3>Saída antecipada</h3><label>Professoras que saem antes<select id="professoras-saida" multiple size="5">${base.professoras.filter((professora) => !(base.folga?.professoras || []).includes(professora)).map((professora) => `<option>${escapeHtml(professora)}</option>`).join("")}</select></label><div id="ultimos-blocos"></div>${dados.config.usar_professoras_fixas ? `<label class="check-line"><input id="usar-fixas" type="checkbox" checked> Usar professoras fixas neste rodízio?</label>` : ""}</section></div><div class="section-title"><h2>Gerar rodízio do modelo</h2><p>Primeiro confira a prévia. Salvar cria a escala somente se não existir outra nesta data.</p></div><button id="gerar-rodizio" class="primary-action full-action" type="button">🚀 Gerar prévia do rodízio</button><div id="resultado-rodizio"></div>`;
      const saida = $("#professoras-saida"), ultimos = $("#ultimos-blocos");
      const mostrarSaidas = () => { ultimos.innerHTML = [...saida.selectedOptions].map((opcao) => `<label>Último bloco disponível — ${escapeHtml(opcao.value)}<select data-saida="${escapeHtml(opcao.value)}">${horarios.slice(0, -1).map((horario) => `<option value="${escapeHtml(horario)}">${escapeHtml(horario)}</option>`).join("")}</select></label>`).join(""); };
      saida.addEventListener("change", mostrarSaidas); mostrarSaidas();
      $("#rotacao-manual").addEventListener("change", (evento) => $("#opcoes-rotacao").classList.toggle("hidden", !evento.target.checked));
      $("#gerar-rodizio").addEventListener("click", () => {
        const coletivas = {};
        area.querySelectorAll("select[data-coletiva]").forEach((campo) => { (coletivas[campo.dataset.coletiva] ||= {})[campo.dataset.turma] = campo.value; });
        const saidas = Object.fromEntries([...area.querySelectorAll("select[data-saida]")].map((campo) => [campo.dataset.saida, campo.value]));
        let turmaInicioTeoria = null;
        if ($("#rotacao-manual").checked) { const turma = $("#turma-rotacao").value; turmaInicioTeoria = document.querySelector('input[name="criterio-rotacao"]:checked').value === "teoria" ? turma : dados.turmas[(dados.turmas.indexOf(turma) - 1 + dados.turmas.length) % dados.turmas.length]; }
        const resultado = gerarEscalaModelo(base, modelo, { data: $("#rodizio-data").value, coletivas, saidas, turmaInicioTeoria, usarFixas: Boolean($("#usar-fixas")?.checked) });
        const destino = $("#resultado-rodizio");
        if (resultado.erros.length) { destino.innerHTML = `<div class="action-error"><strong>O rodízio não foi salvo.</strong><br>${resultado.erros.map((erro) => `• ${escapeHtml(erro)}`).join("<br>")}</div>`; return; }
        destino.innerHTML = `<div class="action-ok">Prévia gerada. Confira antes de salvar.</div>${muralRodizio(resultado.escala, window.GemData.dataBr($("#rodizio-data").value), turmaPorAluna)}<button id="salvar-rodizio" class="primary-action full-action" type="button">Salvar rodízio deste sábado</button>`;
        $("#salvar-rodizio").addEventListener("click", async () => { const botao = $("#salvar-rodizio"); botao.disabled = true; try { await window.GemData.salvarRodizio($("#rodizio-data").value, modelo.id, resultado.escala); destino.innerHTML = `<div class="action-ok">Rodízio salvo com sucesso. A escala está protegida como histórico.</div>${muralRodizio(resultado.escala, window.GemData.dataBr($("#rodizio-data").value), turmaPorAluna)}`; } catch (erro) { botao.disabled = false; destino.insertAdjacentHTML("afterbegin", `<div class="action-error">${escapeHtml(erro.message)}</div>`); } });
      });
    } catch (error) { area.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#carregar-rodizio").addEventListener("click", carregar);
  await carregar();
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
  if (state.role === "Professora" && state.page === "Minhas aulas") {
    await renderMinhasAulas(content);
    return;
  }
  if (state.role === "Aluna" && state.page === "Minhas lições") {
    await renderMinhasLicoes(content);
    return;
  }
  if (state.role === "Aluna" && state.page === "Boletim") {
    await renderBoletim(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Planejamento e rodízio") {
    await renderRodizio(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Chamada") {
    await renderChamada(content);
    return;
  }
  if (state.page === "Visão geral" || state.page === "Minhas aulas" || state.page === "Minhas lições") {
    const greeting = state.role === "Secretaria" ? "Os módulos administrativos serão trazidos usando os mesmos dados já existentes." : "Seus dados e agenda são carregados do histórico do GEM.";
    content.innerHTML = `<section class="intro-card"><p class="eyebrow">GEM MUSICAL</p><h2>Olá, ${state.name}.</h2><p>${greeting}</p></section><div class="grid"><div class="metric"><strong>Dados reais</strong><span>Mesmo banco do GEM</span></div><div class="metric"><strong>Histórico</strong><span>Escalas anteriores preservadas</span></div><div class="metric"><strong>Aplicativo</strong><span>Disponível também no celular</span></div></div>`;
  } else {
    content.innerHTML = `<section class="panel empty"><h2>${iconFor(state.page)} ${state.page}</h2><p>Este módulo está sendo integrado ao mesmo banco do GEM.</p></section>`;
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

// A marca é carregada da configuração já usada pelo GEM.
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
