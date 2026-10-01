const navByRole = {
  Master: ["GEMs", "Usuários mestres", "Visão da plataforma"],
  Secretaria: ["Visão geral", "Planejamento e rodízio", "Turmas e pessoas", "Chamada", "Correção de lições", "Relatórios", "Analítico", "Documentos", "Provas", "Logística"],
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
  return ({ "GEMs":"🏫", "Usuários mestres":"🔐", "Visão da plataforma":"🌐", "Visão geral":"🏠", "Planejamento e rodízio":"🗓️", "Turmas e pessoas":"👥", "Chamada":"✅", "Correção de lições":"📋", "Relatórios":"📊", "Analítico":"📈", "Documentos":"📁", "Provas":"📝", "Logística":"⚙️", "Minhas aulas":"👩‍🏫", "Envio de documentos":"📤", "Analítico IA":"📈", "Mensagens":"💬", "Minhas lições":"🎼", "Boletim":"🎓" }[page] || "•");
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
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">REGISTRO DE AULA</p><h2>Olá, ${escapeHtml(state.name)}.</h2><p>Sua agenda vem do rodízio salvo. Abra uma aula para registrar o conteúdo, as dificuldades e a lição de casa, como no sistema original.</p></section><div class="section-title"><h2>Minhas aulas</h2><p>As fotos das alunas e as turmas também seguem a escala real daquela data.</p></div><section class="panel"><div class="agenda-date"><div><label for="agenda-data">Data da aula</label><input id="agenda-data" type="date" value="${hoje}"></div><button id="carregar-agenda" class="primary-action" type="button">Carregar agenda</button></div><div id="agenda-lista" class="lesson-list"></div><div id="registro-aula"></div></section>`;
  const lista = $("#agenda-lista");
  const areaRegistro = $("#registro-aula");
  let aulasAtuais = [];

  const fotosDasAlunas = (aula) => `<div class="lesson-students">${aula.alunas.map((aluna) => {
    const foto = aula.fotos?.[aluna];
    const iniciais = String(aluna || "?").split(/\s+/).slice(0, 2).map((parte) => parte[0]).join("");
    const retrato = foto ? `<a href="${escapeHtml(foto)}" target="_blank" rel="noopener" title="Ampliar foto de ${escapeHtml(aluna)}"><img src="${escapeHtml(foto)}" alt="Foto de ${escapeHtml(aluna)}"></a>` : `<span title="${escapeHtml(aluna)}">${escapeHtml(iniciais)}</span>`;
    return `<div class="lesson-student">${retrato}<small>${escapeHtml(aluna)}</small></div>`;
  }).join("")}</div>`;

  const abrirRegistro = (indice) => {
    const aula = aulasAtuais[indice];
    if (!aula) return;
    areaRegistro.innerHTML = `<section class="lesson-register"><div class="register-heading"><div><p class="eyebrow">LANÇAR REGISTRO</p><h3>${escapeHtml(aula.horario)} · ${escapeHtml(aula.tipo)}</h3><p>${escapeHtml(aula.individual ? "Aula individual" : `Aula por turma${aula.turma ? ` · ${aula.turma}` : ""}`)}</p></div><button id="fechar-registro" class="secondary-action" type="button">Fechar</button></div>${fotosDasAlunas(aula)}<div class="record-form"><div><label for="registro-material">Material usado hoje</label><input id="registro-material" placeholder="Ex.: MSA, Apostila, Folha Extra"></div><div><label for="registro-conteudo">Conteúdo / página / lição trabalhada</label><input id="registro-conteudo" placeholder="Ex.: MSA: exercício 9, páginas 12 a 15"></div><div><label for="registro-dificuldades">Dificuldades observadas</label><textarea id="registro-dificuldades" placeholder="Uma por linha ou separadas por vírgula. Deixe vazio se não houve dificuldades."></textarea></div><div><label for="registro-observacao">Observações pedagógicas</label><textarea id="registro-observacao" placeholder="Observações sobre a aula"></textarea></div><div><label for="registro-casa-tipo">Lição de casa</label><select id="registro-casa-tipo"><option value="">Não deixar lição</option><option value="MSA">MSA — corrigida pela professora de Solfejo</option><option value="Canto">Solfejo Melódico — corrigida pela professora</option><option value="Apostila">Apostila — correção pela Secretaria</option><option value="Teoria">Teoria / folha avulsa — correção pela Secretaria</option></select></div><div><label for="registro-casa">Lição deixada para casa</label><input id="registro-casa" placeholder="Ex.: página 18, exercícios 1 e 2" disabled></div></div><div class="register-actions"><button id="salvar-registro-aula" class="primary-action" type="button">Salvar registro da aula</button><div id="registro-retorno"></div></div></section>`;
    $("#fechar-registro").addEventListener("click", () => { areaRegistro.innerHTML = ""; });
    const tipoCasa = $("#registro-casa-tipo"), licaoCasa = $("#registro-casa");
    tipoCasa.addEventListener("change", () => { licaoCasa.disabled = !tipoCasa.value; if (!tipoCasa.value) licaoCasa.value = ""; });
    $("#salvar-registro-aula").addEventListener("click", async () => {
      const botao = $("#salvar-registro-aula");
      const conteudo = $("#registro-conteudo").value.trim();
      if (!conteudo) { $("#registro-retorno").innerHTML = `<div class="action-error">Informe o conteúdo trabalhado antes de salvar.</div>`; return; }
      const dificuldades = $("#registro-dificuldades").value.split(/[\n,;]/).map((item) => item.trim()).filter(Boolean);
      botao.disabled = true;
      try {
        await window.GemData.salvarRegistroAula({ dataIso: $("#agenda-data").value, instrutora: state.name, tipo: aula.tipo, alunas: aula.alunas, material: $("#registro-material").value.trim(), conteudo, dificuldades, observacao: $("#registro-observacao").value.trim(), casaTipo: tipoCasa.value, licaoCasa: licaoCasa.value });
        $("#registro-retorno").innerHTML = `<div class="action-ok">Registro salvo para ${aula.alunas.length === 1 ? "a aluna" : "as alunas"} desta aula.</div>`;
      } catch (erro) { $("#registro-retorno").innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; botao.disabled = false; }
    });
    areaRegistro.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const carregar = async () => {
    lista.innerHTML = `<div class="empty">Carregando agenda...</div>`;
    areaRegistro.innerHTML = "";
    try {
      aulasAtuais = await window.GemData.agendaProfessora(state.name, $("#agenda-data").value);
      if (!aulasAtuais.length) { lista.innerHTML = `<div class="empty">Nenhuma aula encontrada para você nesta data.</div>`; return; }
      lista.innerHTML = aulasAtuais.map((aula, indice) => `<article class="agenda-card"><h3>${escapeHtml(aula.horario)} · ${escapeHtml(aula.tipo)}</h3><p><strong>${escapeHtml(aula.local)}</strong></p>${fotosDasAlunas(aula)}<span class="agenda-tag">${aula.individual ? "Aula individual" : `Turma ${escapeHtml(aula.turma || "")}`}</span><button class="secondary-action register-open" type="button" data-registro="${indice}">📝 Registrar aula</button></article>`).join("");
      lista.querySelectorAll("[data-registro]").forEach((botao) => botao.addEventListener("click", () => abrirRegistro(Number(botao.dataset.registro))));
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
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">SECRETARIA</p><h2>📍 Chamada Geral</h2><p>A lista é formada somente pelas alunas do rodízio já salvo para a data.</p></section><section class="panel"><div class="agenda-date"><div><label for="chamada-data">Data da chamada</label><input id="chamada-data" type="date" value="${hoje}"></div><button id="carregar-chamada" class="primary-action" type="button">Carregar</button></div><div id="chamada-lista" class="empty">Carregando...</div></section>`;
  const lista = $("#chamada-lista");
  const carregar = async () => {
    try {
      const { alunas, chamadas, fotos } = await window.GemData.dadosChamada($("#chamada-data").value);
      if (!alunas.length) { lista.innerHTML = `<div class="empty">Não há rodízio salvo nesta data.</div>`; return; }
      const porAluna = Object.fromEntries(chamadas.map((item) => [item.Aluna, item]));
      lista.innerHTML = `<div class="attendance-list">${alunas.map((aluna, indice) => { const chamada = porAluna[aluna] || { Status: "Presente", Observacao: "" }; const foto = fotos[aluna] ? `<a href="${escapeHtml(fotos[aluna])}" target="_blank" rel="noopener" title="Abrir foto ampliada"><img src="${escapeHtml(fotos[aluna])}" alt="Foto de ${escapeHtml(aluna)}"></a>` : `<span>${escapeHtml(aluna.slice(0, 1))}</span>`; return `<article class="attendance-row"><div class="attendance-student">${foto}<strong>${escapeHtml(aluna)}</strong></div><div class="attendance-checks"><label><input type="radio" name="presenca-${indice}" data-presente="${escapeHtml(aluna)}" ${chamada.Status === "Presente" ? "checked" : ""}> Presente</label><label><input type="radio" name="presenca-${indice}" data-ausente="${escapeHtml(aluna)}" ${chamada.Status === "Ausente" ? "checked" : ""}> Ausente</label><label><input type="radio" name="presenca-${indice}" data-justificada="${escapeHtml(aluna)}" ${chamada.Status === "Justificada" ? "checked" : ""}> Falta justificada</label></div><input class="${chamada.Status === "Justificada" ? "" : "hidden"}" data-motivo="${escapeHtml(aluna)}" value="${escapeHtml(chamada.Observacao || "")}" placeholder="Motivo da falta justificada"></article>`; }).join("")}</div><button id="salvar-chamada" class="primary-action full-action" type="button">Salvar chamada</button><div id="chamada-retorno"></div>`;
      lista.querySelectorAll("input[data-presente],input[data-ausente],input[data-justificada]").forEach((campo) => campo.addEventListener("change", (evento) => { const aluna = evento.target.dataset.presente || evento.target.dataset.ausente || evento.target.dataset.justificada; lista.querySelector(`[data-motivo="${CSS.escape(aluna)}"]`).classList.toggle("hidden", !evento.target.dataset.justificada); }));
      $("#salvar-chamada").addEventListener("click", async () => { const botao = $("#salvar-chamada"); botao.disabled = true; try { await window.GemData.salvarChamada($("#chamada-data").value, alunas.map((aluna) => ({ aluna, status: lista.querySelector(`[data-justificada="${CSS.escape(aluna)}"]`).checked ? "Justificada" : lista.querySelector(`[data-ausente="${CSS.escape(aluna)}"]`).checked ? "Ausente" : "Presente", observacao: lista.querySelector(`[data-justificada="${CSS.escape(aluna)}"]`).checked ? lista.querySelector(`[data-motivo="${CSS.escape(aluna)}"]`).value : "" }))); $("#chamada-retorno").innerHTML = `<div class="action-ok">Chamada salva.</div>`; } catch (erro) { $("#chamada-retorno").innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; botao.disabled = false; } });
    } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
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

function muralRodizio(escala, data) {
  if (!escala?.length) return `<div class="empty">Ainda não existe rodízio salvo para esta data.</div>`;
  const horarios = [...new Set(escala.flatMap((linha) => Object.keys(linha).filter((chave) => !["Aluna", "_detalhes"].includes(chave))))];
  const cores = ["#dbeafe", "#dcfce7", "#fef9c3", "#fee2e2", "#f3e8ff", "#ccfbf1", "#e0f2fe", "#ffedd5", "#e0e7ff"];
  const colunas = horarios.map((horario) => {
    const grupos = new Map();
    escala.forEach((linha) => { const valor = String(linha[horario] || ""); if (valor) (grupos.get(valor) || grupos.set(valor, []).get(valor)).push(linha); });
    const cards = [...grupos.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([valor, linhas], indice) => {
      const detalhe = linhas[0]._detalhes?.[horario] || {};
      const sala = valor.split("|")[0].trim();
      const professora = valor.split("|").slice(1).join("|").trim();
      const turma = detalhe.turma || "";
      const coletiva = !detalhe.individual && (/SALA 8|SALA 9/i.test(sala) || linhas.length > 1);
      const titulo = coletiva && /SALA 9/i.test(sala) ? `${sala} | ${professora} (Solfejo Melódico)` : coletiva && /SALA 8/i.test(sala) ? `${sala} | ${professora} (Teoria)` : `${sala} | ${professora}`;
      const texto = coletiva ? turma : linhas.map((linha) => linha.Aluna).join(" + ");
      return `<article class="mural-card" style="background:${cores[Math.min(indice, cores.length - 1)]}"><strong>${escapeHtml(titulo)}</strong><span>${escapeHtml(texto)}</span></article>`;
    }).join("");
    return `<section class="mural-column"><h3>${escapeHtml(horario)}</h3>${cards}</section>`;
  }).join("");
  return `<div class="mural-scroll"><section class="mural-print" id="mural-rodizio"><header><h2>Rodízio Geral das aulas - GEM Vila Verde</h2><p>Data: ${escapeHtml(data)}</p></header><div class="mural-columns">${colunas}</div></section></div>`;
}

function resumoModelo(modelo, turmas) {
  const configuracao = modelo?.configuracao || {};
  const blocos = configuracao.blocos || [];
  const atividades = configuracao.atividades || [];
  const salas = configuracao.salas || [];
  return `<section class="panel model-summary"><h3>${escapeHtml(modelo?.nome || "Modelo legado")}</h3><p><strong>${blocos.length}</strong> blocos · <strong>${Object.keys(turmas).length}</strong> turmas ativas · <strong>${salas.filter((sala) => String(sala.Uso || "").toLowerCase() === "individual").length}</strong> salas individuais</p><div class="model-chips">${atividades.map((atividade) => `<span>${escapeHtml(atividade.Atividade || "Atividade")} · ${escapeHtml(atividade.Formato || "")}</span>`).join("") || "<span>Configuração do modelo será exibida aqui.</span>"}</div></section>`;
}

async function renderRodizio(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">PLANEJAMENTO</p><h2>Rodízio</h2><p>Gere uma nova escala com as mesmas regras do GEM. Uma escala já salva só muda quando a Secretaria confirma uma correção; as versões anteriores não são apagadas.</p></section><section class="panel"><div class="agenda-date"><div><label for="rodizio-data">Sábado</label><input id="rodizio-data" type="date" value="${hoje}"></div><button id="carregar-rodizio" class="primary-action" type="button">Carregar planejamento</button></div><div id="rodizio-base"><div class="empty">Carregando base do rodízio...</div></div></section>`;
  const area = $("#rodizio-base");
  const carregar = async () => {
    area.innerHTML = `<div class="empty">Carregando turmas, professoras, modelo e escala...</div>`;
    try {
      const base = await window.GemData.dadosRodizio($("#rodizio-data").value);
      const modelo = base.modeloEscala ? base.modelos.find((item) => item.id === base.modeloEscala) : window.GemData.modeloParaData(base.modelos, $("#rodizio-data").value);
      const turmas = Object.entries(base.turmas).map(([turma, alunas]) => `<li><strong>${escapeHtml(turma)}</strong>: ${alunas.length} aluna(s)</li>`).join("");
      const folgas = base.folga?.professoras?.length ? base.folga.professoras.join(", ") : "Nenhuma folga informada";
      if (!modelo && !base.escala.length) {
        area.innerHTML = `<div class="action-error">Não há modelo logístico programado para esta data. Cadastre ou programe o modelo em Logística, sem alterar os rodízios anteriores.</div>`;
        return;
      }
      const modeloExibido = modelo || { nome: "Modelo legado — escala histórica", configuracao: {} };
      const config = modeloExibido.configuracao || {};
      const preparacao = modelo ? window.RodizioEngine.prepararModelo(modelo, base.turmas) : { coletivas: {}, turmas: [], blocos: [] };
      const atividades = Object.keys(preparacao.coletivas);
      const todasAlunas = Object.values(base.turmas).flat();
      const opcoesProf = base.professoras.map((prof) => `<option value="${escapeHtml(prof)}">${escapeHtml(prof)}</option>`).join("");
      const fixasSalvas = Object.entries(base.professorasFixas).map(([alunaNormalizada, professora]) => ({ aluna: todasAlunas.find((nome) => nome.trim().toLowerCase() === alunaNormalizada) || "", professora })).filter((item) => item.aluna);
      const coletivas = atividades.map((atividade) => `<section class="collective-box"><h3>${escapeHtml(atividade)} <small>(${escapeHtml(preparacao.coletivas[atividade] || "Sala a definir")})</small></h3>${preparacao.turmas.map((turma) => `<label>Prof. ${escapeHtml(atividade)} — ${escapeHtml(turma)}<select data-coletiva="${escapeHtml(atividade)}" data-turma="${escapeHtml(turma)}">${(config.professoras_habilitadas?.[atividade] || (atividade === "Solfejo Melódico" ? config.professoras_habilitadas?.Canto : null) || base.professoras).map((prof) => `<option value="${escapeHtml(prof)}">${escapeHtml(prof)}</option>`).join("")}</select></label>`).join("")}</section>`).join("");
      const escalaSalva = base.escala.length;
      const rodiziosSalvos = (base.escalasAnteriores || []).filter((item) => Array.isArray(item.escala) && item.escala.length).sort((a, b) => { const [da, ma, aa] = String(a.id).split("/"); const [db, mb, ab] = String(b.id).split("/"); return `${ab}${mb}${db}`.localeCompare(`${aa}${ma}${da}`); });
      area.innerHTML = `${resumoModelo(modeloExibido, base.turmas)}<div class="planning-grid"><section><h3>Turmas ativas</h3><ul>${turmas || "<li>Nenhuma turma cadastrada.</li>"}</ul></section><section><h3>Professoras disponíveis</h3><p>${escapeHtml(base.professoras.join(", ") || "Nenhuma professora cadastrada.")}</p><h3>Folgas deste sábado</h3><p>${escapeHtml(folgas)}</p>${rodiziosSalvos.length ? `<label>Rodízios já salvos<select id="rodizios-anteriores"><option value="">Escolha uma data para abrir</option>${rodiziosSalvos.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.id)}</option>`).join("")}</select></label>` : ""}</section></div>${escalaSalva ? rodizioSalvoMarkup(base) : `<section class="generator-panel"><h2>Gerar novo rodízio</h2><p>As alunas ativas entram no novo rodízio. Alunas desativadas continuam nas escalas e registros dos sábados já realizados.</p><div class="generator-grid"><div><h3>Professoras das aulas por turma</h3>${coletivas}</div><div><h3>Rotação das turmas</h3><label class="checkbox-line"><input id="rotacao-manual" type="checkbox"> Definir manualmente a rotação das turmas?</label><div id="rotacao-opcoes" class="hidden"><label><input type="radio" name="criterio-rotacao" value="teoria" checked> Turma que começa em Teoria</label><label><input type="radio" name="criterio-rotacao" value="individual"> Turma no último bloco de Prática + Solfejo</label><select id="turma-rotacao">${preparacao.turmas.map((turma) => `<option value="${escapeHtml(turma)}">${escapeHtml(turma)}</option>`).join("")}</select><div id="previa-rotacao"></div></div><h3>Saída antecipada</h3><p class="hint">Selecione somente quem sairá antes. Depois escolha o último bloco em que cada uma ainda pode atender.</p><select id="professoras-saida" multiple size="5">${opcoesProf}</select><div id="saidas-detalhes"></div></div></div>${config.usar_professoras_fixas ? `<section class="fixas-box"><h3>Professoras fixas neste modelo</h3><p>Escolha somente as alunas que terão professora fixa. Você pode acrescentar quantas precisar.</p><div class="fixed-list" id="fixed-list"></div><button id="adicionar-fixa" class="secondary-action" type="button">＋ Adicionar aluna fixa</button><button id="salvar-fixas" class="secondary-action" type="button">Salvar professoras fixas</button><label class="checkbox-line"><input id="usar-fixas" type="checkbox" checked> Usar professoras fixas neste rodízio?</label></section>` : ""}<button id="gerar-rodizio" class="primary-action wide-action" type="button">Gerar rodízio do modelo</button><div id="gerar-feedback"></div></section>`}`;
      $("#rodizios-anteriores")?.addEventListener("change", (event) => { if (!event.target.value) return; const [dia, mes, ano] = event.target.value.split("/"); $("#rodizio-data").value = `${ano}-${mes}-${dia}`; carregar(); });
      if (escalaSalva) ligarAcoesEscala(base, modeloExibido);
      else ligarGerador(base, modelo, preparacao, fixasSalvas);
    } catch (error) { area.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#carregar-rodizio").addEventListener("click", carregar);
  await carregar();
}

async function renderVisaoGeral(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">COORDENAÇÃO</p><h2>Visão geral diária</h2><p>Resumo real do rodízio, presença e registros lançados pelas professoras.</p></section><section class="panel"><div class="agenda-date"><div><label for="visao-data">Data da análise</label><input id="visao-data" type="date" value="${hoje}"></div><button id="carregar-visao" class="primary-action" type="button">Atualizar visão</button></div><div id="visao-conteudo"><div class="empty">Carregando dados...</div></div></section><section class="panel branding-panel"><h2>Marca e perfil da Coordenação</h2><p>A logo aparece no login e na barra lateral. A foto substitui a letra do perfil da Coordenação neste aplicativo.</p><div class="branding-grid"><label>Nova logo do GEM<input id="logo-gem" type="file" accept="image/png,image/jpeg,image/webp"></label><button id="salvar-logo" class="secondary-action" type="button">Salvar logo</button><label>Nome exibido<input id="nome-coordenacao" value="${escapeHtml(state.name)}"></label><label>Foto da Coordenação<input id="foto-coordenacao" type="file" accept="image/png,image/jpeg,image/webp"></label><button id="salvar-perfil" class="secondary-action" type="button">Salvar perfil</button></div><div id="marca-feedback"></div></section>`;
  const carregar = async () => { const destino = $("#visao-conteudo"); destino.innerHTML = `<div class="empty">Carregando resumo...</div>`; try { const dados = await window.GemData.dadosVisaoGeral($("#visao-data").value); const presentes = Math.max(0, dados.alunas.length - dados.ausentes.length); destino.innerHTML = `<div class="grid"><div class="metric"><strong>${dados.alunas.length}</strong><span>Alunas no rodízio</span></div><div class="metric"><strong>${presentes}</strong><span>Presentes</span></div><div class="metric"><strong>${dados.ausentes.length}</strong><span>Ausências/justificadas</span></div><div class="metric"><strong>${dados.analises.length}</strong><span>Registros pedagógicos</span></div></div><section class="panel compact-panel"><h3>Ausências</h3>${dados.ausentes.length ? `<ul>${dados.ausentes.map((item) => `<li><strong>${escapeHtml(item.Aluna)}</strong> — ${escapeHtml(item.Status)}${item.Observacao ? `: ${escapeHtml(item.Observacao)}` : ""}</li>`).join("")}</ul>` : "<p>Nenhuma ausência registrada nesta data.</p>"}</section>`; } catch (error) { destino.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } };
  $("#carregar-visao").addEventListener("click", carregar); await carregar();
  $("#salvar-logo").addEventListener("click", async () => { const feedback = $("#marca-feedback"); try { const identidade = await window.GemData.enviarLogoGem($("#logo-gem").files[0]); aplicarLogo(identidade.logoUrl); feedback.innerHTML = `<p class="action-ok">Logo atualizada. Ela aparecerá também no próximo acesso.</p>`; } catch (error) { feedback.innerHTML = `<p class="action-error">${escapeHtml(error.message)}</p>`; } });
  $("#salvar-perfil").addEventListener("click", async () => { const feedback = $("#marca-feedback"); try { const perfil = await window.GemData.salvarPerfilSecretaria({ nome: $("#nome-coordenacao").value, arquivo: $("#foto-coordenacao").files[0] }); state.name = perfil.nome_exibicao || state.name; $("#profile-name").textContent = state.name; aplicarAvatar(perfil.fotoUrl, state.name); feedback.innerHTML = `<p class="action-ok">Perfil da Coordenação atualizado.</p>`; } catch (error) { feedback.innerHTML = `<p class="action-error">${escapeHtml(error.message)}</p>`; } });
}

async function renderPessoas(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">CADASTROS</p><h2>Turmas e pessoas</h2><p>Alunas desativadas deixam de entrar apenas em rodízios novos; os rodízios, chamadas e registros anteriores continuam visíveis.</p></section><section class="panel"><div class="person-tabs"><button class="tab-action active" data-pessoas="aluna">Alunas e turmas</button><button class="tab-action" data-pessoas="professora">Professoras</button><button class="tab-action" data-pessoas="secretaria">Secretarias</button></div><div id="pessoas-conteudo"><div class="empty">Carregando pessoas...</div></div></section>`;
  const dados = await window.GemData.dadosPessoas(); const destino = $("#pessoas-conteudo");
  const mostrar = (tipo) => {
    const lista = tipo === "aluna" ? dados.alunas : tipo === "professora" ? dados.professoras : dados.secretarias;
    const titulo = tipo === "aluna" ? "Adicionar aluna" : tipo === "professora" ? "Adicionar professora" : "Adicionar secretaria";
    destino.innerHTML = `<div class="person-add"><h3>${titulo}</h3><div class="form-grid"><input id="pessoa-nome" placeholder="Nome completo">${tipo === "aluna" ? '<input id="pessoa-turma" placeholder="Turma">' : ""}${tipo !== "secretaria" ? '<input id="pessoa-login" placeholder="Login">' : ""}<button id="adicionar-pessoa" class="primary-action" type="button">Adicionar</button></div></div><div class="person-list">${lista.length ? lista.map((pessoa, indice) => `<article class="person-row person-card"><div><strong>${escapeHtml(pessoa.nome)}</strong><span>${tipo === "aluna" ? escapeHtml(pessoa.turma || "Sem turma") : pessoa.login ? `Login: ${escapeHtml(pessoa.login)}` : ""}</span></div><span class="badge ${pessoa.ativo === false ? "inactive" : ""}">${pessoa.ativo === false ? "Desativada" : "Ativa"}</span><div class="person-actions"><button data-editar="${indice}" class="secondary-action" type="button">Editar</button><button data-toggle="${indice}" class="secondary-action" type="button">${pessoa.ativo === false ? "Reativar" : "Desativar"}</button></div><div class="person-editor hidden" data-editor="${indice}"><label>Nome<input data-campo="nome" value="${escapeHtml(pessoa.nome)}"></label>${tipo === "aluna" ? `<label>Turma<input data-campo="turma" value="${escapeHtml(pessoa.turma || "")}"></label>` : ""}${tipo !== "secretaria" ? `<label>Login<input data-campo="login" value="${escapeHtml(pessoa.login || "")}"></label><label>Nova senha <small>(deixe vazia para manter a atual)</small><input data-campo="senha" type="password" autocomplete="new-password" placeholder="Nova senha"></label>` : ""}<button data-salvar="${indice}" class="primary-action" type="button">Salvar alterações</button></div></article>`).join("") : "<div class=\"empty\">Nenhum cadastro ainda.</div>"}</div>`;
    $("#adicionar-pessoa").addEventListener("click", async () => { const nome = $("#pessoa-nome").value.trim(); if (!nome) return; const novo = tipo === "aluna" ? { nome, turma: $("#pessoa-turma").value.trim() || "Sem turma", ativo: true, login: $("#pessoa-login").value.trim().toLowerCase() || null } : tipo === "professora" ? { nome, login: $("#pessoa-login").value.trim().toLowerCase(), ativo: true } : { nome, ativo: true }; try { await window.GemData.salvarPessoa(tipo, novo); await renderPessoas(content); } catch (error) { destino.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); } });
    destino.querySelectorAll("[data-editar]").forEach((botao) => botao.addEventListener("click", () => destino.querySelector(`[data-editor="${botao.dataset.editar}"]`).classList.toggle("hidden")));
    destino.querySelectorAll("[data-toggle]").forEach((botao) => botao.addEventListener("click", async () => { const pessoa = lista[Number(botao.dataset.toggle)]; try { await window.GemData.salvarPessoa(tipo, { ativo: pessoa.ativo === false }, pessoa.id, pessoa.nome); pessoa.ativo = pessoa.ativo === false; mostrar(tipo); } catch (error) { alert(error.message); } }));
    destino.querySelectorAll("[data-salvar]").forEach((botao) => botao.addEventListener("click", async () => { const pessoa = lista[Number(botao.dataset.salvar)], editor = destino.querySelector(`[data-editor="${botao.dataset.salvar}"]`); const atualizado = { nome: editor.querySelector('[data-campo="nome"]').value.trim() }; if (tipo === "aluna") atualizado.turma = editor.querySelector('[data-campo="turma"]').value.trim() || "Sem turma"; if (tipo !== "secretaria") { atualizado.login = editor.querySelector('[data-campo="login"]').value.trim().toLowerCase(); const senha = editor.querySelector('[data-campo="senha"]').value; if (senha) atualizado.senha = senha; } if (!atualizado.nome) { alert("Informe o nome."); return; } try { await window.GemData.salvarPessoa(tipo, atualizado, pessoa.id, pessoa.nome); await renderPessoas(content); } catch (error) { editor.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); } }));
  };
  document.querySelectorAll("[data-pessoas]").forEach((botao) => botao.addEventListener("click", () => { document.querySelectorAll("[data-pessoas]").forEach((item) => item.classList.toggle("active", item === botao)); mostrar(botao.dataset.pessoas); }));
  mostrar("aluna");
}

async function renderDocumentos(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ARQUIVOS</p><h2>Documentos</h2><p>Envie materiais internos ou libere um documento para uma turma ou aluna.</p></section><section class="panel"><div class="form-grid"><input id="doc-titulo" placeholder="Título do documento"><select id="doc-disciplina"><option>Prática</option><option>Teoria</option><option>Solfejo</option><option>Solfejo Melódico</option></select><input id="doc-arquivo" type="file" accept="application/pdf,image/*"><input id="doc-turma" placeholder="Turma (opcional)"><input id="doc-aluna" placeholder="Aluna (opcional)"><label class="checkbox-line"><input id="doc-visivel" type="checkbox"> Disponível para alunas</label><button id="enviar-doc" class="primary-action" type="button">Enviar documento</button></div><div id="doc-feedback"></div></section><section class="panel"><h2>Documentos enviados</h2><div id="lista-docs"><div class="empty">Carregando documentos...</div></div></section>`;
  const carregar = async () => { const lista = $("#lista-docs"); try { const docs = await window.GemData.dadosDocumentos(); lista.innerHTML = docs.length ? docs.map((doc) => `<article class="person-row"><div><strong>${escapeHtml(doc.titulo)}</strong><span>${escapeHtml(doc.disciplina || "—")} · ${doc.aluna ? `Aluna: ${escapeHtml(doc.aluna)}` : doc.turma ? `Turma: ${escapeHtml(doc.turma)}` : "Uso interno"}</span></div><span class="badge">${doc.visivel_alunas ? "Disponível" : "Interno"}</span><button data-documento="${escapeHtml(doc.arquivo_path)}" class="secondary-action" type="button">Abrir</button></article>`).join("") : `<div class="empty">Nenhum documento enviado ainda.</div>`; lista.querySelectorAll("[data-documento]").forEach((botao) => botao.addEventListener("click", async () => { try { window.open(await window.GemData.urlDocumento(botao.dataset.documento), "_blank", "noopener"); } catch (error) { alert(error.message); } })); } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } };
  $("#enviar-doc").addEventListener("click", async () => { const feedback = $("#doc-feedback"); try { await window.GemData.enviarDocumento({ arquivo: $("#doc-arquivo").files[0], titulo: $("#doc-titulo").value.trim(), disciplina: $("#doc-disciplina").value, turma: $("#doc-turma").value.trim(), aluna: $("#doc-aluna").value.trim(), visivel: $("#doc-visivel").checked }); feedback.innerHTML = `<div class="action-ok">Documento enviado.</div>`; await carregar(); } catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } }); await carregar();
}

async function renderProvas(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">AVALIAÇÕES</p><h2>Provas</h2><p>Crie avaliações e acompanhe as notas já lançadas no GEM.</p></section><section class="panel"><div class="form-grid"><input id="prova-titulo" placeholder="Nome da prova ou avaliação"><input id="prova-data" type="date" value="${new Date().toISOString().slice(0, 10)}"><button id="criar-prova" class="primary-action" type="button">Criar avaliação</button></div><div id="prova-feedback"></div></section><section class="panel"><div id="lista-provas"><div class="empty">Carregando avaliações...</div></div></section>`;
  const carregar = async () => { const lista = $("#lista-provas"); try { const { avaliacoes, notas } = await window.GemData.dadosProvas(); lista.innerHTML = avaliacoes.length ? avaliacoes.map((avaliacao) => `<article class="person-row"><div><strong>${escapeHtml(avaliacao.titulo)}</strong><span>${escapeHtml(avaliacao.data_avaliacao || "Sem data")} · ${notas.filter((nota) => String(nota.avaliacao_id) === String(avaliacao.id)).length} nota(s) lançada(s)</span></div><span class="badge">Ativa</span></article>`).join("") : `<div class="empty">Nenhuma avaliação cadastrada ainda.</div>`; } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } };
  $("#criar-prova").addEventListener("click", async () => { const feedback = $("#prova-feedback"), titulo = $("#prova-titulo").value.trim(); if (!titulo) { feedback.innerHTML = `<div class="action-error">Informe o nome da avaliação.</div>`; return; } try { await window.GemData.criarProva(titulo, $("#prova-data").value); feedback.innerHTML = `<div class="action-ok">Avaliação criada.</div>`; $("#prova-titulo").value = ""; await carregar(); } catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } }); await carregar();
}

async function renderLogistica(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">LOGÍSTICA</p><h2>Modelos de aulas</h2><p>Modelos são versões. Ao editar um modelo existente, o aplicativo cria uma revisão para o futuro e nunca altera rodízios ou registros de sábados anteriores.</p></section><section class="panel"><div class="section-title"><h2>Modelos cadastrados</h2><button id="novo-modelo" class="primary-action" type="button">Novo modelo</button></div><div id="lista-modelos"><div class="empty">Carregando modelos...</div></div></section><div id="editor-modelo"></div>`;
  const lista = $("#lista-modelos");
  const modelos = await window.GemData.dadosLogistica();
  const pessoas = await window.GemData.dadosPessoas();
  const renderLista = () => { lista.innerHTML = modelos.length ? modelos.map((modelo, indice) => { const config = modelo.configuracao || {}; return `<article class="agenda-card"><h3>${escapeHtml(modelo.nome)}</h3><p><strong>${escapeHtml(modelo.status || "rascunho")}</strong> · começa em ${escapeHtml(modelo.vigencia_inicio || "—")}</p><p>${(config.blocos || []).length} bloco(s), ${(config.turmas || []).filter((t) => t["Ativa no modelo"] !== false).length} turma(s), ${(config.salas || []).filter((s) => String(s.Uso || "").toLowerCase() === "individual").length} sala(s) individual(is).</p><div class="scale-actions"><button data-editar-modelo="${indice}" class="secondary-action" type="button">Criar revisão</button>${modelo.status !== "programado" ? `<button data-programar-modelo="${indice}" class="primary-action" type="button">Programar</button>` : `<button data-rascunho-modelo="${indice}" class="secondary-action" type="button">Voltar a rascunho</button>`}</div></article>`; }).join("") : `<div class="empty">Nenhum modelo cadastrado. Crie o primeiro para gerar novos rodízios.</div>`; ligarLista(); };
  const editor = $("#editor-modelo");
  const linhas = (itens, tipo) => (itens || []).map((item) => tipo === "bloco" ? `<div class="model-row"><input data-bloco-nome value="${escapeHtml(item.Bloco || "")}" placeholder="Bloco"><input data-bloco-inicio value="${escapeHtml(item["Início"] || "")}" placeholder="08:50"><input data-bloco-fim value="${escapeHtml(item.Fim || "")}" placeholder="09:35"><button class="remove-row" type="button">×</button></div>` : `<div class="model-row"><input data-atividade-nome value="${escapeHtml(item.Atividade || "")}" placeholder="Atividade"><select data-atividade-formato><option ${item.Formato === "Turma" ? "selected" : ""}>Turma</option><option ${item.Formato === "Individual" ? "selected" : ""}>Individual</option></select><input data-atividade-duracao value="${escapeHtml(item["Duração (min)"] || "")}" placeholder="Minutos"><input data-atividade-sala value="${escapeHtml(item["Sala sugerida"] || "")}" placeholder="Sala sugerida"><button class="remove-row" type="button">×</button></div>`).join("");
  const abrirEditor = (modelo = null) => {
    const config = modelo?.configuracao || {};
    const blocos = config.blocos || [{ Bloco: "Bloco 1", "Início": "08:50", Fim: "09:35" }, { Bloco: "Bloco 2", "Início": "09:40", Fim: "10:25" }, { Bloco: "Bloco 3", "Início": "10:30", Fim: "11:15" }];
    const atividades = config.atividades || [{ Atividade: "Teoria", Formato: "Turma", "Duração (min)": 45, "Sala sugerida": "SALA 8" }, { Atividade: "Solfejo Melódico", Formato: "Turma", "Duração (min)": 45, "Sala sugerida": "SALA 9" }, { Atividade: "Solfejo", Formato: "Individual", "Duração (min)": 15, "Sala sugerida": "Salas individuais" }, { Atividade: "Prática", Formato: "Individual", "Duração (min)": 30, "Sala sugerida": "Salas individuais" }];
    const ativas = new Set((config.turmas || []).filter((turma) => turma["Ativa no modelo"] !== false).map((turma) => turma.Turma));
    const turmasDoModelo = [...new Set([...pessoas.alunas.map((aluna) => aluna.turma).filter(Boolean), ...(config.turmas || []).map((turma) => turma.Turma).filter(Boolean)])];
    const quantidadeSalas = (config.salas || []).filter((sala) => String(sala.Uso || "").toLowerCase() === "individual" && sala.Ativa !== false).length || 7;
    editor.innerHTML = `<section class="panel model-editor"><h2>${modelo ? "Nova revisão do modelo" : "Novo modelo"}</h2><p>${modelo ? "A revisão será salva separadamente. As escalas existentes permanecem intactas." : "Defina os elementos que a Secretaria poderá usar na geração."}</p><div class="form-grid"><label>Nome do modelo<input id="modelo-nome" value="${escapeHtml(modelo ? `${modelo.nome} — revisão` : "Próximo bimestre")}"></label><label>Começa a valer em<input id="modelo-inicio" type="date" value="${escapeHtml(String(modelo?.vigencia_inicio || new Date().toISOString().slice(0, 10)).slice(0, 10))}"></label><label>Quantidade de salas individuais<input id="modelo-salas" type="number" min="1" value="${quantidadeSalas}"></label></div><h3>Blocos de horário</h3><div id="blocos-modelo">${linhas(blocos, "bloco")}</div><button id="adicionar-bloco" class="secondary-action" type="button">＋ Adicionar bloco</button><h3>Turmas participantes</h3><div class="turmas-checks" id="turmas-modelo">${turmasDoModelo.map((turma) => `<label class="checkbox-line"><input data-turma-modelo value="${escapeHtml(turma)}" type="checkbox" ${ativas.size === 0 || ativas.has(turma) ? "checked" : ""}> ${escapeHtml(turma)}</label>`).join("")}</div><div class="add-turma-modelo"><input id="nova-turma-modelo" placeholder="Ex.: Turma 4"><button id="adicionar-turma-modelo" class="secondary-action" type="button">＋ Adicionar turma</button></div><p class="hint">Uma turma planejada sem alunas ainda será salva no modelo; ela passa a entrar no rodízio quando houver alunas vinculadas a ela.</p><h3>Atividades, duração e salas</h3><div id="atividades-modelo">${linhas(atividades, "atividade")}</div><button id="adicionar-atividade" class="secondary-action" type="button">＋ Adicionar atividade</button><h3>Regras</h3><div class="turmas-checks"><label class="checkbox-line"><input id="modelo-fixas" type="checkbox" ${config.usar_professoras_fixas ? "checked" : ""}> Este modelo usa professoras fixas</label><label class="checkbox-line"><input id="modelo-mesma-prof" type="checkbox" ${config.mesma_professora_nos_componentes !== false ? "checked" : ""}> Mesma professora em Solfejo e Prática</label><label class="checkbox-line"><input id="regra-prof" type="checkbox" ${(config.regras_rodizio?.nao_repetir_aluna !== false) ? "checked" : ""}> Não repetir professora antes de completar a roda</label><label class="checkbox-line"><input id="regra-sala" type="checkbox" ${(config.regras_rodizio?.nao_repetir_sala !== false) ? "checked" : ""}> Não repetir sala antes de completar a roda</label><label class="checkbox-line"><input id="regra-imediata" type="checkbox" ${(config.regras_rodizio?.nao_repetir_imediata !== false) ? "checked" : ""}> Evitar professora da semana anterior</label></div><div class="scale-actions"><button id="salvar-modelo" class="primary-action" type="button">Salvar como rascunho</button><button id="cancelar-modelo" class="secondary-action" type="button">Cancelar</button></div><div id="modelo-feedback"></div></section>`;
    const remover = () => editor.querySelectorAll(".remove-row").forEach((botao) => botao.onclick = () => botao.closest(".model-row").remove()); remover();
    $("#adicionar-bloco").onclick = () => { $("#blocos-modelo").insertAdjacentHTML("beforeend", linhas([{ Bloco: `Bloco ${editor.querySelectorAll("[data-bloco-nome]").length + 1}`, "Início": "", Fim: "" }], "bloco")); remover(); };
    $("#adicionar-atividade").onclick = () => { $("#atividades-modelo").insertAdjacentHTML("beforeend", linhas([{ Atividade: "", Formato: "Turma", "Duração (min)": 45, "Sala sugerida": "" }], "atividade")); remover(); };
    $("#adicionar-turma-modelo").onclick = () => { const campo = $("#nova-turma-modelo"), nome = campo.value.trim(); if (!nome) return; const jaExiste = [...editor.querySelectorAll("[data-turma-modelo]")].some((item) => item.value.trim().toLocaleLowerCase("pt-BR") === nome.toLocaleLowerCase("pt-BR")); if (jaExiste) { campo.focus(); return; } $("#turmas-modelo").insertAdjacentHTML("beforeend", `<label class="checkbox-line"><input data-turma-modelo value="${escapeHtml(nome)}" type="checkbox" checked> ${escapeHtml(nome)}</label>`); campo.value = ""; };
    $("#cancelar-modelo").onclick = () => editor.innerHTML = "";
    $("#salvar-modelo").onclick = async () => { const nome = $("#modelo-nome").value.trim(), inicio = $("#modelo-inicio").value, feedback = $("#modelo-feedback"); const novosBlocos = [...editor.querySelectorAll("#blocos-modelo .model-row")].map((linha) => ({ Bloco: linha.querySelector("[data-bloco-nome]").value.trim(), "Início": linha.querySelector("[data-bloco-inicio]").value.trim(), Fim: linha.querySelector("[data-bloco-fim]").value.trim() })).filter((bloco) => bloco["Início"]); const novasAtividades = [...editor.querySelectorAll("#atividades-modelo .model-row")].map((linha) => ({ Atividade: linha.querySelector("[data-atividade-nome]").value.trim(), Formato: linha.querySelector("[data-atividade-formato]").value, "Duração (min)": Number(linha.querySelector("[data-atividade-duracao]").value || 0), "Sala sugerida": linha.querySelector("[data-atividade-sala]").value.trim() })).filter((atividade) => atividade.Atividade); if (!nome || !inicio || !novosBlocos.length || !novasAtividades.length) { feedback.innerHTML = `<div class="action-error">Informe nome, início, ao menos um bloco e uma atividade.</div>`; return; } const turmas = [...editor.querySelectorAll("[data-turma-modelo]:checked")].map((item) => ({ Turma: item.value, "Ativa no modelo": true })); const salas = Array.from({ length: Number($("#modelo-salas").value || 0) }, (_, i) => ({ Sala: `SALA ${i + 1}`, Uso: "Individual", Área: "Prática + Solfejo", Ativa: true })); novasAtividades.filter((atividade) => atividade.Formato === "Turma").forEach((atividade) => salas.push({ Sala: atividade["Sala sugerida"], Uso: "Turma", Área: atividade.Atividade, Ativa: true })); const professoras = pessoas.professoras.filter((prof) => prof.ativo !== false).map((prof) => prof.nome); const habilitadas = Object.fromEntries(novasAtividades.map((atividade) => [atividade.Atividade, professoras])); const configuracao = { modo: "configuravel", blocos: novosBlocos, turmas, salas, atividades: novasAtividades, professoras_habilitadas: habilitadas, usar_professoras_fixas: $("#modelo-fixas").checked, mesma_professora_nos_componentes: $("#modelo-mesma-prof").checked, regras_rodizio: { nao_repetir_aluna: $("#regra-prof").checked, nao_repetir_sala: $("#regra-sala").checked, nao_repetir_imediata: $("#regra-imediata").checked } }; try { await window.GemData.salvarModeloLogistica({ nome, vigenciaInicio: inicio, configuracao }); feedback.innerHTML = `<div class="action-ok">Modelo salvo como rascunho. Programe-o quando quiser usá-lo para novas escalas.</div>`; } catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } };
  };
  const ligarLista = () => { lista.querySelectorAll("[data-editar-modelo]").forEach((botao) => botao.onclick = () => abrirEditor(modelos[Number(botao.dataset.editarModelo)])); lista.querySelectorAll("[data-programar-modelo]").forEach((botao) => botao.onclick = async () => { try { await window.GemData.alterarStatusModelo(modelos[Number(botao.dataset.programarModelo)].id, "programado"); modelos[Number(botao.dataset.programarModelo)].status = "programado"; renderLista(); } catch (error) { alert(error.message); } }); lista.querySelectorAll("[data-rascunho-modelo]").forEach((botao) => botao.onclick = async () => { try { await window.GemData.alterarStatusModelo(modelos[Number(botao.dataset.rascunhoModelo)].id, "rascunho"); modelos[Number(botao.dataset.rascunhoModelo)].status = "rascunho"; renderLista(); } catch (error) { alert(error.message); } }); };
  $("#novo-modelo").onclick = () => abrirEditor(); renderLista();
}

async function renderRelatorios(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">RELATÓRIOS</p><h2>Relatório diário</h2><p>Consulte a escala, a chamada e os registros pedagógicos de qualquer sábado já salvo.</p></section><section class="panel"><div class="agenda-date"><div><label for="relatorio-data">Data</label><input id="relatorio-data" type="date" value="${hoje}"></div><button id="gerar-relatorio" class="primary-action" type="button">Gerar relatório</button></div><div id="relatorio-conteudo"></div></section>`;
  const carregar = async () => {
    const destino = $("#relatorio-conteudo"); destino.innerHTML = `<div class="empty">Gerando relatório...</div>`;
    try {
      const dados = await window.GemData.dadosVisaoGeral($("#relatorio-data").value);
      const porAluna = new Map(dados.alunas.map((aluna) => [aluna, []]));
      dados.registros.forEach((registro) => { if (registro.Aluna) (porAluna.get(registro.Aluna) || porAluna.set(registro.Aluna, []).get(registro.Aluna)).push(registro); });
      const rotulo = (tipo) => ({ Chamada: "📍 Presença", Casa_MSA: "📚 Lição de casa — MSA", Casa_Apostila: "📚 Lição de casa — Apostila", Casa_Canto: "🎤 Lição de casa — Solfejo Melódico" }[tipo] || String(tipo || "Registro").replace(/^Analise_/, "📖 "));
      const mostrarDificuldades = (valor) => Array.isArray(valor) ? valor.filter(Boolean).join(" · ") : String(valor || "").replace(/^\[|\]$/g, "");
      const card = (item) => {
        const tipo = String(item.Tipo || ""), casa = tipo.startsWith("Casa_"), presenca = tipo === "Chamada", conteudo = casa ? (item.Licao_Casa || item.Licao_Atual) : item.Licao_Atual, dificuldade = mostrarDificuldades(item.Dificuldades);
        return `<article class="report-record ${casa ? "homework-record" : ""}"><h4>${escapeHtml(rotulo(tipo))}${item.Instrutora ? ` <small>— Professora: ${escapeHtml(item.Instrutora)}</small>` : ""}</h4>${presenca ? `<p><strong>Status:</strong> ${escapeHtml(item.Status || "Presente")}${item.Observacao ? ` · ${escapeHtml(item.Observacao)}` : ""}</p>` : ""}${conteudo ? `<p><strong>${casa ? "Lição deixada para casa" : "Conteúdo/atividade de hoje"}:</strong> ${escapeHtml(conteudo)}</p>` : ""}${dificuldade && dificuldade !== "Não apresentou dificuldades" ? `<p class="report-warning"><strong>⚠ Dificuldades:</strong> ${escapeHtml(dificuldade)}</p>` : dificuldade === "Não apresentou dificuldades" ? `<p class="report-ok">✓ Sem dificuldades registradas nesta aula.</p>` : ""}${item.Observacao && !presenca ? `<p class="report-note"><strong>📝 Observação da professora/Secretaria:</strong> ${escapeHtml(item.Observacao)}</p>` : ""}${item.Status && !presenca ? `<p class="report-status"><strong>Situação:</strong> ${escapeHtml(item.Status)}</p>` : ""}</article>`;
      };
      const corpo = porAluna.size ? [...porAluna.entries()].sort(([a], [b]) => a.localeCompare(b, "pt-BR")).map(([aluna, registros]) => `<section class="student-report"><h3>👧 ${escapeHtml(aluna)}</h3>${registros.length ? registros.map(card).join("") : `<div class="report-empty">Nenhum registro lançado ainda para esta aluna.</div>`}</section>`).join("") : `<div class="empty">Não há escala salva para esta data.</div>`;
      destino.innerHTML = `<div class="report-actions"><button id="baixar-relatorio-pdf" class="primary-action" type="button">Baixar relatório em PDF</button></div><div id="report-print"><section class="compact-panel report-header"><h3>Relatório completo — ${escapeHtml(dados.data)}</h3><p><strong>${dados.alunas.length}</strong> aluna(s) na escala · <strong>${dados.ausentes.length}</strong> ausência(s) · <strong>${dados.analises.length}</strong> registro(s) pedagógico(s).</p></section>${corpo}</div>`;
      $("#baixar-relatorio-pdf").addEventListener("click", async () => {
        if (!window.html2canvas || !window.jspdf?.jsPDF) { alert("A ferramenta de PDF ainda está carregando. Tente novamente em alguns segundos."); return; }
        const botao = $("#baixar-relatorio-pdf"); botao.disabled = true; botao.textContent = "Gerando PDF...";
        try {
          const alvo = $("#report-print"), blocos = [...alvo.querySelectorAll(".report-header, .student-report")];
          const pdf = new window.jspdf.jsPDF("p", "mm", "a4"), larguraPagina = 190, alturaPagina = 277;
          for (let indice = 0; indice < blocos.length; indice += 1) {
            const bloco = blocos[indice];
            const canvas = await window.html2canvas(bloco, { scale: 2, backgroundColor: "#ffffff", useCORS: true, windowWidth: bloco.scrollWidth });
            const proporcao = Math.min(larguraPagina / canvas.width, alturaPagina / canvas.height);
            const largura = canvas.width * proporcao, altura = canvas.height * proporcao;
            if (indice > 0) pdf.addPage();
            pdf.addImage(canvas.toDataURL("image/png"), "PNG", (210 - largura) / 2, 10, largura, altura);
          }
          pdf.save(`Relatorio_GEM_${dados.data.replaceAll("/", "-")}.pdf`);
        } catch (error) { alert("Não foi possível gerar o PDF: " + error.message); } finally { botao.disabled = false; botao.textContent = "Baixar relatório em PDF"; }
      });
    } catch (error) { destino.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#gerar-relatorio").addEventListener("click", carregar); await carregar();
}

async function renderCorrecoesLicoes(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">SECRETARIA</p><h2>Correção de lições</h2><p>Este painel corrige somente Apostila da Prática e Folha Avulsa de Teoria. MSA, métodos e Solfejo continuam sendo corrigidos pela professora na aula seguinte.</p></section><section class="panel"><div class="analytics-filters"><label>Aluna<select id="correcao-aluna"></select></label><label>Responsável da Secretaria<select id="correcao-secretaria"></select></label><label>Data da conferência<input id="correcao-data" type="date" value="${new Date().toISOString().slice(0, 10)}"></label><button id="atualizar-correcoes" class="primary-action" type="button">Consultar pendências</button></div><div id="pendencias-licoes"><div class="empty">Carregando lições...</div></div></section><section class="panel"><h2>➕ Registrar atividade nova</h2><p class="hint">Use somente se a professora não lançou a lição no sistema.</p><div class="form-grid"><select id="nova-licao-tipo"><option value="Casa_Apostila">Apostila — Prática</option><option value="Casa_Teoria">Folha Avulsa — Teoria</option></select><input id="nova-licao-conteudo" placeholder="Lição / página, ex.: Lição 05, pág. 12"><select id="nova-licao-status"><option>Pendente</option><option>Resolvido</option><option>Resolvido com pendências</option><option>Não resolvido</option></select><input id="nova-licao-obs" placeholder="Observações técnicas / dicas"><button id="criar-licao-secretaria" class="primary-action" type="button">Salvar atividade</button></div><div id="correcao-feedback"></div></section>`;
  const base = await window.GemData.dadosCorrecoesLicoes(); const alunas = base.alunas.filter((aluna) => aluna.ativo !== false).map((aluna) => aluna.nome), secretarias = base.secretarias.filter((item) => item.ativo !== false).map((item) => item.nome);
  $("#correcao-aluna").innerHTML = alunas.map((aluna) => `<option value="${escapeHtml(aluna)}">${escapeHtml(aluna)}</option>`).join(""); $("#correcao-secretaria").innerHTML = (secretarias.length ? secretarias : [state.name]).map((nome) => `<option value="${escapeHtml(nome)}">${escapeHtml(nome)}</option>`).join("");
  const dataBr = (iso) => { const [ano, mes, dia] = String(iso).split("-"); return ano ? `${dia}/${mes}/${ano}` : iso; };
  const dataOrdenavel = (valor) => { const [dia, mes, ano] = String(valor || "").split("/"); return ano ? `${ano}${mes}${dia}` : "00000000"; };
  const atualizar = () => {
    const aluna = $("#correcao-aluna").value, porLicao = new Map();
    base.historico.filter((item) => item.Aluna === aluna).sort((a, b) => dataOrdenavel(a.Data).localeCompare(dataOrdenavel(b.Data)) || Number(a.id || 0) - Number(b.id || 0)).forEach((item) => porLicao.set(`${item.Tipo}|${item.Licao_Casa}`, item));
    const pendentes = [...porLicao.values()].filter((item) => !["Resolvido", "Realizada", "Realizadas - sem pendência", "Realizada - sem pendência"].includes(item.Status)); const destino = $("#pendencias-licoes");
    destino.innerHTML = pendentes.length ? `<div class="pending-title">🚨 Atividades pendentes para ${escapeHtml(aluna)}</div>${pendentes.map((item, indice) => `<article class="pending-card"><div><h3>${item.Tipo === "Casa_Apostila" ? "🎼 Apostila (Prática)" : "📘 Folha Avulsa (Teoria)"}</h3><p><strong>${escapeHtml(item.Licao_Casa || "Lição não informada")}</strong></p><p class="hint">Lançada em ${escapeHtml(item.Data || "—")} · Status atual: ${escapeHtml(item.Status || "Pendente")}</p></div><div class="pending-action"><label>Resultado<select data-status-correcao="${indice}"><option ${item.Status === "Resolvido" ? "selected" : ""}>Resolvido</option><option ${item.Status === "Resolvido com pendências" ? "selected" : ""}>Resolvido com pendências</option><option ${item.Status === "Não resolvido" ? "selected" : ""}>Não resolvido</option></select></label><label>Observação da Secretaria<textarea data-obs-correcao="${indice}" placeholder="Escreva a observação da correção">${escapeHtml(String(item.Observacao || "").replace(/^Sec:\s*/i, ""))}</textarea></label><button data-salvar-correcao="${indice}" class="primary-action" type="button">Atualizar status</button></div></article>`).join("")}` : `<div class="action-ok">✅ Nenhuma pendência de Apostila ou Teoria para esta aluna.</div>`;
    destino.querySelectorAll("[data-salvar-correcao]").forEach((botao) => botao.addEventListener("click", async () => { const indice = Number(botao.dataset.salvarCorrecao), item = pendentes[indice]; try { await window.GemData.atualizarCorrecaoLicao(item.id, { status: destino.querySelector(`[data-status-correcao="${indice}"]`).value, observacao: destino.querySelector(`[data-obs-correcao="${indice}"]`).value.trim(), secretaria: $("#correcao-secretaria").value, data: dataBr($("#correcao-data").value) }); const posicao = base.historico.findIndex((registro) => String(registro.id) === String(item.id)); if (posicao >= 0) base.historico[posicao] = { ...base.historico[posicao], Status: destino.querySelector(`[data-status-correcao="${indice}"]`).value }; atualizar(); } catch (error) { destino.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); } }));
  };
  $("#atualizar-correcoes").addEventListener("click", atualizar); atualizar();
  $("#criar-licao-secretaria").addEventListener("click", async () => { const feedback = $("#correcao-feedback"), licao = $("#nova-licao-conteudo").value.trim(); if (!licao) { feedback.innerHTML = `<div class="action-error">Informe a lição ou página.</div>`; return; } try { await window.GemData.criarCorrecaoLicao({ aluna: $("#correcao-aluna").value, tipo: $("#nova-licao-tipo").value, licao, status: $("#nova-licao-status").value, observacao: $("#nova-licao-obs").value.trim(), secretaria: $("#correcao-secretaria").value, data: dataBr($("#correcao-data").value) }); feedback.innerHTML = `<div class="action-ok">Atividade registrada.</div>`; } catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } });
}

async function renderAnalitico(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ACOMPANHAMENTO PEDAGÓGICO</p><h2>Analítico e desempenho</h2><p>Indicadores calculados somente a partir dos registros, chamadas, lições e notas já existentes no GEM.</p></section><section class="panel"><div class="person-tabs"><button class="tab-action active" data-analise="prontuario">Prontuário individual</button><button class="tab-action" data-analise="quadro">Quadro de desempenho</button><button class="tab-action" data-analise="boletim">Boletim</button></div><div class="analytics-filters"><label>De<input id="analise-inicio" type="date"></label><label>Até<input id="analise-fim" type="date"></label><label id="analise-aluna-wrap">Aluna<select id="analise-aluna"></select></label><button id="atualizar-analise" class="primary-action" type="button">Atualizar</button></div><div id="analise-conteudo"><div class="empty">Carregando indicadores...</div></div></section>`;
  const dados = await window.GemData.dadosAnalitico();
  const hoje = new Date(), inicio = new Date(); inicio.setDate(hoje.getDate() - 60);
  $("#analise-inicio").value = inicio.toISOString().slice(0, 10); $("#analise-fim").value = hoje.toISOString().slice(0, 10);
  $("#analise-aluna").innerHTML = dados.alunas.map((aluna) => `<option value="${escapeHtml(aluna.nome)}">${escapeHtml(aluna.nome)}</option>`).join("");
  let aba = "prontuario";
  const dataRegistro = (valor) => { const texto = String(valor || "").trim(); if (/^\d{4}-\d{2}-\d{2}/.test(texto)) return texto.slice(0, 10); const [dia, mes, ano] = texto.split("/"); return ano ? `${ano}-${mes}-${dia}` : ""; };
  const disciplinaAnalise = (tipo) => { const texto = String(tipo || "").replace(/^Analise_/, "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase(); return texto === "CANTO" || texto === "SOLFEJO MELODICO" ? "Solfejo Melódico" : texto === "PRATICA" ? "Prática" : texto === "TEORIA" ? "Teoria" : texto === "SOLFEJO" ? "Solfejo" : ""; };
  const dificuldades = (valor) => { if (Array.isArray(valor)) return valor.filter((item) => item && !/^\[\]$|^null$|^nan$/i.test(String(item).trim())); if (typeof valor !== "string") return []; const texto = valor.trim(); if (!texto || /^\[\]$|^null$|^nan$/i.test(texto)) return []; try { const json = JSON.parse(texto); if (Array.isArray(json)) return json.filter(Boolean); } catch (_) {} return texto.replace(/^\[|\]$/g, "").split(/[,;]+/).map((item) => item.trim().replace(/^['"]|['"]$/g, "")).filter(Boolean); };
  const dentroPeriodo = (registro) => { const data = dataRegistro(registro.Data); return data && data >= $("#analise-inicio").value && data <= $("#analise-fim").value; };
  const classificacao = (registros) => { if (!registros.length) return { icone: "🥉", nome: "Sem registros", nota: null }; const limpos = registros.filter((registro) => !dificuldades(registro.Dificuldades).some((item) => !/não apresentou dificuldade/i.test(item))); const nota = Math.round(limpos.length / registros.length * 100); return nota >= 80 ? { icone: "🥇", nome: "Ouro", nota } : nota >= 50 ? { icone: "🥈", nome: "Prata", nota } : { icone: "🥉", nome: "Bronze", nota }; };
  const render = () => {
    const destino = $("#analise-conteudo"), periodo = dados.historico.filter(dentroPeriodo);
    $("#analise-aluna-wrap").classList.toggle("hidden", aba !== "prontuario" && aba !== "boletim");
    if (aba === "quadro") {
      const disciplinas = ["Prática", "Teoria", "Solfejo", "Solfejo Melódico"];
      destino.innerHTML = `<h3>🏆 Quadro de desempenho</h3><p class="hint">A medalha usa a porcentagem de aulas sem dificuldades registradas no período escolhido. Registros antigos de Canto são considerados como Solfejo Melódico.</p><div class="table-wrap"><table class="scale-table performance-table"><thead><tr><th>Aluna</th>${disciplinas.map((disciplina) => `<th>${escapeHtml(disciplina)}</th>`).join("")}</tr></thead><tbody>${dados.alunas.filter((aluna) => aluna.ativo !== false).map((aluna) => `<tr><th>${escapeHtml(aluna.nome)}</th>${disciplinas.map((disciplina) => { const resultado = classificacao(periodo.filter((registro) => registro.Aluna === aluna.nome && disciplinaAnalise(registro.Tipo) === disciplina)); return `<td>${resultado.icone} ${resultado.nome}${resultado.nota !== null ? `<br><small>${resultado.nota}%</small>` : ""}</td>`; }).join("")}</tr>`).join("")}</tbody></table></div>`;
      return;
    }
    const aluna = $("#analise-aluna").value, registros = periodo.filter((registro) => registro.Aluna === aluna), chamadas = registros.filter((registro) => registro.Tipo === "Chamada"), aulas = registros.filter((registro) => String(registro.Tipo || "").startsWith("Analise_")), casas = registros.filter((registro) => String(registro.Tipo || "").startsWith("Casa_"));
    if (aba === "boletim") { const notas = dados.notas.filter((nota) => nota.aluna === aluna); destino.innerHTML = `<h3>🎼 Boletim — ${escapeHtml(aluna)}</h3>${notas.length ? `<div class="table-wrap"><table class="scale-table"><thead><tr><th>Avaliação</th><th>Disciplina</th><th>Nota</th></tr></thead><tbody>${notas.map((nota) => { const avaliacao = dados.avaliacoes.find((item) => String(item.id) === String(nota.avaliacao_id)); return `<tr><td>${escapeHtml(avaliacao?.titulo || "Avaliação")}</td><td>${escapeHtml(nota.disciplina || "—")}</td><td>${escapeHtml(nota.nota ?? "—")}</td></tr>`; }).join("")}</tbody></table></div>` : `<div class="empty">Ainda não há notas lançadas para esta aluna.</div>`}`; return; }
    const presentes = chamadas.filter((item) => !["Ausente", "Justificada"].includes(item.Status)).length, faltas = chamadas.filter((item) => item.Status === "Ausente").length, justificadas = chamadas.filter((item) => item.Status === "Justificada").length, aproveitamento = classificacao(aulas).nota || 0;
    const listaDificuldades = [...new Set(aulas.flatMap((registro) => dificuldades(registro.Dificuldades)).filter((item) => !/não apresentou dificuldade/i.test(item)))]; const pendentes = casas.filter((registro) => !/resolvido|realizada|sem pendência/i.test(String(registro.Status || "")));
    destino.innerHTML = `<section class="analytics-summary"><h3>👤 Prontuário — ${escapeHtml(aluna)}</h3><div class="grid"><div class="metric"><strong>${chamadas.length ? Math.round((presentes + justificadas * .5) / chamadas.length * 100) : 0}%</strong><span>Frequência ponderada</span></div><div class="metric"><strong>${faltas} / ${justificadas}</strong><span>Faltas / justificadas</span></div><div class="metric"><strong>${aproveitamento}%</strong><span>Aproveitamento nas aulas</span></div><div class="metric"><strong>${pendentes.length}</strong><span>Lições pendentes</span></div></div><div class="analytics-columns"><section><h4>⚠ Dificuldades registradas</h4>${listaDificuldades.length ? `<ul>${listaDificuldades.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : "<p>Sem dificuldades registradas no período.</p>"}</section><section><h4>📚 Lições de casa</h4>${casas.length ? casas.map((item) => `<p class="homework-line"><strong>${escapeHtml(item.Tipo.replace("Casa_", ""))}:</strong> ${escapeHtml(item.Licao_Casa || "—")} <small>${escapeHtml(item.Status || "Pendente")}</small></p>`).join("") : "<p>Nenhuma lição registrada no período.</p>"}</section></div><section class="feedback-panel"><h4>👩‍🏫 Feedback das professoras e Secretaria</h4>${aulas.length ? aulas.map((item) => `<article><strong>${escapeHtml(disciplinaAnalise(item.Tipo) || String(item.Tipo).replace("Analise_", ""))} — ${escapeHtml(item.Data || "")}</strong>${item.Instrutora ? ` · ${escapeHtml(item.Instrutora)}` : ""}<p>${escapeHtml(item.Licao_Atual || "Sem conteúdo informado")}</p>${item.Observacao ? `<p class="report-note">📝 ${escapeHtml(item.Observacao)}</p>` : ""}</article>`).join("") : "<p>Nenhuma aula registrada no período.</p>"}</section></section>`;
  };
  document.querySelectorAll("[data-analise]").forEach((botao) => botao.addEventListener("click", () => { aba = botao.dataset.analise; document.querySelectorAll("[data-analise]").forEach((item) => item.classList.toggle("active", item === botao)); render(); })); $("#atualizar-analise").addEventListener("click", render); render();
}

function rodizioSalvoMarkup(base) {
  return `<section class="section-title"><div><h2>Rodízio salvo</h2><p>Este é o retrato da data. Use “Corrigir” somente se houve erro de lançamento; a versão anterior ficará registrada.</p></div><div class="scale-actions"><button id="ampliar-rodizio" class="secondary-action" type="button">Ampliar</button><button id="baixar-rodizio" class="primary-action" type="button">Baixar imagem</button><button id="editar-rodizio" class="secondary-action" type="button">Corrigir rodízio</button></div></section>${muralRodizio(base.escala, base.data)}<div id="edicao-rodizio"></div>`;
}

function ligarGerador(base, modelo, preparacao, fixasSalvas = []) {
  const manual = $("#rotacao-manual"), opcoes = $("#rotacao-opcoes"), turma = $("#turma-rotacao"), previa = $("#previa-rotacao"), saidas = $("#professoras-saida"), detalhesSaidas = $("#saidas-detalhes");
  const atualizarPrevia = () => {
    if (!manual.checked) { previa.innerHTML = ""; return; }
    const valor = turma.value; const individual = document.querySelector('input[name="criterio-rotacao"]:checked')?.value === "individual";
    let comecaTeoria = valor;
    if (individual) comecaTeoria = preparacao.turmas[(preparacao.turmas.indexOf(valor) - 1 + preparacao.turmas.length) % preparacao.turmas.length];
    const posicoes = [...Object.keys(preparacao.coletivas), "Prática + Solfejo"], teoria = posicoes.findIndex((item) => window.RodizioEngine.nomeArea(item) === "Teoria");
    const ordem = [posicoes[teoria], ...posicoes.filter((item) => item !== posicoes[teoria] && item !== "Prática + Solfejo"), "Prática + Solfejo"];
    previa.innerHTML = `<p class="hint">Para isso, <strong>${escapeHtml(comecaTeoria)}</strong> começa em Teoria.</p><table class="mini-table"><thead><tr><th>Bloco</th>${preparacao.turmas.map((item) => `<th>${escapeHtml(item)}</th>`).join("")}</tr></thead><tbody>${preparacao.blocos.map((bloco, indice) => `<tr><td>${escapeHtml(window.RodizioEngine.horario(bloco, indice))}</td>${preparacao.turmas.map((turmaNome, indiceTurma) => `<td>${escapeHtml(ordem[(indiceTurma - preparacao.turmas.indexOf(comecaTeoria) + indice + ordem.length * 3) % ordem.length])}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
  };
  const atualizarSaidas = () => { const selecionadas = [...saidas.selectedOptions].map((item) => item.value); detalhesSaidas.innerHTML = selecionadas.map((prof) => `<label>Último bloco disponível — ${escapeHtml(prof)}<select data-saida="${escapeHtml(prof)}">${preparacao.blocos.slice(0, -1).map((bloco, i) => `<option ${i === preparacao.blocos.length - 2 ? "selected" : ""} value="${escapeHtml(window.RodizioEngine.horario(bloco, i))}">${escapeHtml(window.RodizioEngine.horario(bloco, i))}</option>`).join("")}</select></label>`).join(""); };
  manual.addEventListener("change", () => { opcoes.classList.toggle("hidden", !manual.checked); atualizarPrevia(); });
  turma.addEventListener("change", atualizarPrevia); document.querySelectorAll('input[name="criterio-rotacao"]').forEach((item) => item.addEventListener("change", atualizarPrevia)); saidas.addEventListener("change", atualizarSaidas);
  const listaFixas = $("#fixed-list");
  const parFixo = (atual = {}) => `<div class="fixed-row"><select data-fixa-aluna><option value="">Escolha a aluna</option>${Object.values(base.turmas).flat().map((aluna) => `<option ${atual.aluna === aluna ? "selected" : ""} value="${escapeHtml(aluna)}">${escapeHtml(aluna)}</option>`).join("")}</select><select data-fixa-prof><option value="">Escolha a professora</option>${base.professoras.map((prof) => `<option ${atual.professora === prof ? "selected" : ""} value="${escapeHtml(prof)}">${escapeHtml(prof)}</option>`).join("")}</select><button type="button" class="remove-fixa" aria-label="Remover professora fixa">×</button></div>`;
  const ativarLinhasFixas = () => listaFixas?.querySelectorAll(".remove-fixa").forEach((botao) => botao.onclick = () => { botao.closest(".fixed-row").remove(); });
  if (listaFixas) { listaFixas.innerHTML = (fixasSalvas.length ? fixasSalvas : [{}]).map(parFixo).join(""); ativarLinhasFixas(); $("#adicionar-fixa").addEventListener("click", () => { listaFixas.insertAdjacentHTML("beforeend", parFixo()); ativarLinhasFixas(); }); }
  const mapaDasFixas = () => Object.fromEntries([...document.querySelectorAll(".fixed-row")].map((linha) => [linha.querySelector("[data-fixa-aluna]")?.value.trim().toLowerCase(), linha.querySelector("[data-fixa-prof]")?.value]).filter(([aluna, professora]) => aluna && professora));
  $("#salvar-fixas")?.addEventListener("click", async () => { try { await window.GemData.salvarProfessorasFixas(mapaDasFixas()); alert("Professoras fixas salvas."); } catch (error) { alert(error.message); } });
  $("#gerar-rodizio").addEventListener("click", async () => {
    const feedback = $("#gerar-feedback"); const coletivas = {}; document.querySelectorAll("[data-coletiva]").forEach((item) => { (coletivas[item.dataset.coletiva] ||= {})[item.dataset.turma] = item.value; });
    const fixas = mapaDasFixas(); const saidasMap = Object.fromEntries([...document.querySelectorAll("[data-saida]")].map((item) => [item.dataset.saida, item.value]));
    let turmaTeoria = null; if (manual.checked) { turmaTeoria = turma.value; if (document.querySelector('input[name="criterio-rotacao"]:checked')?.value === "individual") turmaTeoria = preparacao.turmas[(preparacao.turmas.indexOf(turmaTeoria) - 1 + preparacao.turmas.length) % preparacao.turmas.length]; }
    const resultado = window.RodizioEngine.gerar({ modelo, data: base.data, turmasReais: base.turmas, professoras: base.professoras, folgas: base.folga?.professoras || [], saidas: saidasMap, fixas, coletivas, turmaInicioTeoria: turmaTeoria, usarFixas: Boolean($("#usar-fixas")?.checked), escalasAnteriores: base.escalasAnteriores });
    if (resultado.erros.length) { feedback.innerHTML = `<div class="action-error"><strong>O rodízio não foi salvo.</strong><br>${resultado.erros.map(escapeHtml).join("<br>")}</div>`; return; }
    feedback.innerHTML = `${muralRodizio(resultado.escala, base.data)}<button id="confirmar-geracao" class="primary-action wide-action" type="button">Confirmar e salvar rodízio</button>`;
    $("#confirmar-geracao").addEventListener("click", async () => { try { await window.GemData.salvarEscala($("#rodizio-data").value, resultado.escala, modelo.id); await renderRodizio($("#page-content")); } catch (error) { feedback.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); } });
  });
}

function ligarAcoesEscala(base, modelo) {
  $("#baixar-rodizio")?.addEventListener("click", async () => { const mural = $("#mural-rodizio"); if (!window.html2canvas) { alert("A ferramenta de imagem ainda não foi carregada. Tente novamente em alguns segundos."); return; } const canvas = await window.html2canvas(mural, { scale: 2, backgroundColor: "#ffffff", width: mural.scrollWidth, windowWidth: mural.scrollWidth }); const link = document.createElement("a"); link.download = `Rodizio_${base.data.replaceAll("/", "-")}.png`; link.href = canvas.toDataURL("image/png"); link.click(); });
  $("#ampliar-rodizio")?.addEventListener("click", () => { document.body.insertAdjacentHTML("beforeend", `<div class="mural-modal" id="mural-modal"><button aria-label="Fechar" class="modal-close">×</button>${muralRodizio(base.escala, base.data)}</div>`); $("#mural-modal").addEventListener("click", (event) => { if (event.target.id === "mural-modal" || event.target.classList.contains("modal-close")) $("#mural-modal").remove(); }); });
  $("#editar-rodizio")?.addEventListener("click", () => { const horarios = [...new Set(base.escala.flatMap((linha) => Object.keys(linha).filter((chave) => !["Aluna", "_detalhes"].includes(chave))))]; $("#edicao-rodizio").innerHTML = `<section class="panel edit-scale"><h3>Corrigir rodízio</h3><p>Edite somente a sala/professora incorreta. Os detalhes pedagógicos e a turma são preservados; informe o motivo da correção antes de salvar.</p><div class="table-wrap"><table class="scale-table"><thead><tr><th>Aluna</th>${horarios.map((hora) => `<th>${escapeHtml(hora)}</th>`).join("")}</tr></thead><tbody>${base.escala.map((linha, i) => `<tr><th>${escapeHtml(linha.Aluna)}</th>${horarios.map((hora) => `<td><input data-escala="${i}" data-hora="${escapeHtml(hora)}" value="${escapeHtml(linha[hora] || "")}"></td>`).join("")}</tr>`).join("")}</tbody></table></div><label>Motivo da correção<input id="motivo-edicao" placeholder="Ex.: troca de professora confirmada pela Secretaria"></label><button id="salvar-edicao" class="primary-action" type="button">Salvar correção</button></section>`; $("#salvar-edicao").addEventListener("click", async () => { const corrigida = structuredClone(base.escala); document.querySelectorAll("[data-escala]").forEach((item) => { corrigida[Number(item.dataset.escala)][item.dataset.hora] = item.value.trim(); }); try { await window.GemData.salvarEscala($("#rodizio-data").value, corrigida, modelo.id, $("#motivo-edicao").value); await renderRodizio($("#page-content")); } catch (error) { $("#edicao-rodizio").insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); } }); });
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

function aplicarLogo(url) {
  if (!url) return;
  document.querySelectorAll(".brand-mark, .sidebar-brand span").forEach((marca) => {
    marca.textContent = ""; marca.style.backgroundImage = `url('${url}')`; marca.style.backgroundSize = "cover"; marca.style.backgroundPosition = "center";
  });
}

function aplicarAvatar(url, nome) {
  const avatar = $("#avatar");
  avatar.textContent = url ? "" : String(nome || "G").slice(0, 1).toUpperCase();
  avatar.style.backgroundImage = url ? `url('${url}')` : "";
  avatar.style.backgroundSize = url ? "cover" : "";
  avatar.style.backgroundPosition = url ? "center" : "";
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
  if (state.role === "Secretaria" && state.page === "Visão geral") {
    await renderVisaoGeral(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Turmas e pessoas") {
    try { await renderPessoas(content); } catch (error) { content.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
    return;
  }
  if (state.role === "Secretaria" && state.page === "Relatórios") {
    await renderRelatorios(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Analítico") {
    try { await renderAnalitico(content); } catch (error) { content.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
    return;
  }
  if (state.role === "Secretaria" && state.page === "Documentos") {
    await renderDocumentos(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Provas") {
    await renderProvas(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Logística") {
    await renderLogistica(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Chamada") {
    await renderChamada(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Correção de lições") {
    try { await renderCorrecoesLicoes(content); } catch (error) { content.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
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
  aplicarAvatar(null, state.name);
  $("#login-screen").classList.add("hidden"); $("#app-screen").classList.remove("hidden");
  if (state.role === "Secretaria") {
    try {
      const perfil = await window.GemData.perfilSecretaria();
      if (perfil.nome_exibicao) { state.name = perfil.nome_exibicao; $("#profile-name").textContent = state.name; }
      aplicarAvatar(perfil.fotoUrl, state.name);
    } catch (error) { console.warn("Perfil visual indisponível", error); }
  }
  if (state.role === "Professora") {
    try {
      const perfil = await window.GemData.perfilProfessora(state.name);
      aplicarAvatar(perfil.fotoUrl, state.name);
    } catch (error) { console.warn("Foto de perfil da professora indisponível", error); }
  }
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
      aplicarLogo(identidade.logoUrl);
    }
  }
});
