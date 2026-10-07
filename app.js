const navByRole = {
  Master: ["GEMs", "Secretarias dos GEMs", "Usuários mestres", "Visão da plataforma"],
  Secretaria: ["Visão geral", "Planejamento e rodízio", "Folgas", "Turmas e pessoas", "Chamada", "Correção de lições", "Relatórios", "Analítico", "Documentos", "Provas", "Mensagens", "Logística", "Ajustes"],
  Professora: ["Minhas aulas", "Configurar Métodos", "Envio de documentos", "Provas", "Analítico IA", "Mensagens"],
  Aluna: ["Minhas lições", "Boletim", "Documentos", "Mensagens"]
};

const exampleSchedule = [
  ["08:50 — 09:35", ["Sala 8 · Teoria", "Prof. Elaine", "Turma 1"], ["Sala 9 · Solfejo Melódico", "Prof. Roberta", "Turma 2"], ["Salas 1–7 · Prática + Solfejo", "Professoras em rodízio", "Turma 3"]],
  ["09:40 — 10:25", ["Sala 8 · Teoria", "Prof. Ester", "Turma 2"], ["Sala 9 · Solfejo Melódico", "Prof. Juliana", "Turma 3"], ["Salas 1–7 · Prática + Solfejo", "Professoras em rodízio", "Turma 1"]],
  ["10:30 — 11:15", ["Sala 8 · Teoria", "Prof. Cássia", "Turma 3"], ["Sala 9 · Solfejo Melódico", "Prof. Kamyla", "Turma 1"], ["Salas 1–7 · Prática + Solfejo", "Professoras em rodízio", "Turma 2"]]
];

// Mesmas opções pedagógicas usadas no registro de aula do app.py.
const dificuldadesPorAula = {
  "Prática": ["Não estudou nada", "Estudou de forma insatisfatória", "Não assistiu os vídeos dos métodos", "Dificuldade rítmica", "Dificuldade em distinguir os nomes das figuras rítmicas", "Está adentrando às teclas", "Dificuldade com a postura (costas, ombros e braços)", "Está deixando o punho alto ou baixo", "Não senta no centro da banqueta", "Está quebrando as falanges", "Unhas muito compridas", "Dificuldade em deixar os dedos arredondados", "Dificuldade em fazer nota de apoio", "Esquece de colocar o pé direito no pedal de expressão", "Faz movimentos desnecessários com o pé esquerdo na pedaleira", "Dificuldade com o uso do metrônomo", "Estuda sem o metrônomo", "Dificuldades em ler as notas na clave de sol", "Dificuldades no movimento da mão", "Demonstra insegurança ao lidar com o conteúdo", "Dificuldade em leitura rítmica", "Dificuldades em leitura métrica", "Dificuldades na ordem das notas, ascendente e descendente", "Dificuldade na pedaleira", "Dificuldades em ler as notas na clave de fá", "Não realizou as atividades da apostila", "Dificuldade em fazer a articulação ligada e semiligada", "Dificuldade com as respirações", "Dificuldade com as respirações sobre passagem", "Dificuldades em recurso de dedilhado (passagem, alargamento, contração, mudança ou substituição)", "Não apresentou dificuldades"],
  "Teoria": ["Não assistiu os vídeos complementares", "Não apresentou dificuldades", "Não participou da aula", "Dificuldade em utilizar o metrônomo", "Não compreende o que é música na igreja", "Não compreende o que é música", "Não compreende o que é som", "Dificuldade em compreender os elementos da música", "Dificuldade em compreender as propriedades do som", "Dificuldade de leitura de clave de sol", "Dificuldade de leitura de clave de fá", "Não realizou as atividades da apostila", "Não estudou", "Não realizou as atividades para casa", "Ficou dispersa durante a aula", "Não realizou as atividades durante a aula", "Não trouxe o material necessário", "Demonstra insegurança ao lidar com o conteúdo"],
  "Solfejo": ["Não assistiu os vídeos complementares", "Dificuldades em ler as notas na clave de sol", "Dificuldades em ler as notas na clave de fá", "Está com dificuldades no uso do metrônomo", "Estuda em metrônomo", "Não realizou as atividades", "Dificuldade em leitura rítmica", "Dificuldades em leitura métrica", "Dificuldade em solfejo (afinação)", "Dificuldades no movimento da mão", "Demonstra insegurança ao lidar com o conteúdo", "Dificuldade rítmica", "Dificuldades na ordem das notas, ascendente e descendente", "Não realizou as atividades da apostila", "Não estudou nada", "Estudou de forma insatisfatória", "Não apresentou dificuldades"]
};

const state = { role: "Secretaria", name: "Coordenação", page: "Visão geral", coordenadora: false, gem: "GEM Musical", externo: false };
const $ = (selector) => document.querySelector(selector);
let installPrompt;

function paginasDoPerfil() {
  const paginas = [...navByRole[state.role]];
  if (state.role === "Professora" && state.coordenadora) paginas.push("Folgas");
  return paginas;
}

function renderNavigation() {
  const nav = $("#navigation");
  nav.innerHTML = paginasDoPerfil().map((item) => `<button class="nav-link ${item === state.page ? "active" : ""}" data-page="${item}">${iconFor(item)} ${item}</button>`).join("");
  nav.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => {
    state.page = button.dataset.page;
    nav.querySelectorAll("button").forEach((link) => link.classList.toggle("active", link === button));
    renderPage();
    $(".sidebar").classList.remove("open");
  }));
}

function iconFor(page) {
  return ({ "GEMs":"🏫", "Usuários mestres":"🔐", "Visão da plataforma":"🌐", "Visão geral":"🏠", "Planejamento e rodízio":"🗓️", "Folgas":"👑", "Turmas e pessoas":"👥", "Chamada":"✅", "Correção de lições":"📋", "Relatórios":"📊", "Analítico":"📈", "Documentos":"📁", "Provas":"📝", "Mensagens":"💬", "Logística":"⚙️", "Ajustes":"🛠️", "Minhas aulas":"👩‍🏫", "Configurar Métodos":"⚙️", "Envio de documentos":"📤", "Analítico IA":"📈", "Minhas lições":"🎼", "Boletim":"🎓" }[page] || "•");
}

function scheduleMarkup() {
  const cells = exampleSchedule.map(([time, ...classes]) => `<div class="time">${time}</div>${classes.map(([title, teacher, group]) => `<article class="room"><strong>${title}</strong><span>${teacher}</span><small>${group}</small></article>`).join("")}`).join("");
  return `<div class="schedule"><div class="schedule-grid"><div class="schedule-head">Horário</div><div class="schedule-head">Bloco 1</div><div class="schedule-head">Bloco 2</div><div class="schedule-head">Bloco 3</div>${cells}</div></div>`;
}

function casaCategoria(tipo) {
  if (tipo === "Casa_MSA") return "Solfejo";
  if (tipo === "Casa_Canto") return "Solfejo Melódico";
  if (["Casa_Teoria", "Casa_Teoria_Prof", "Casa_Apostila_Teoria", "Casa_Apostila_Teoria_Prof"].includes(tipo)) return "Teoria";
  if (["Casa_Apostila", "Casa_Apostila_Prof"].includes(tipo) || String(tipo || "").startsWith("Casa_Metodo_")) return "Prática";
  return "Atividade";
}

function eResolvida(status) { return ["Resolvido", "Realizada", "Realizadas - sem pendência", "Realizada - sem pendência"].includes(status); }

async function renderMinhasAulas(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">REGISTRO DE AULA</p><h2>Olá, ${escapeHtml(state.name)}.</h2><p>Sua agenda vem do rodízio salvo. Abra uma aula para registrar o conteúdo, as dificuldades e a lição de casa, como no sistema original.</p></section><div class="section-title"><h2>Minhas aulas</h2><p>As fotos das alunas e as turmas também seguem a escala real daquela data.</p></div><section class="panel"><div class="agenda-date"><div><label for="agenda-data">Data da aula</label><input id="agenda-data" type="date" value="${hoje}"></div></div><div id="agenda-lista" class="lesson-list"></div><div id="registro-aula"></div></section>`;
  const lista = $("#agenda-lista");
  const areaRegistro = $("#registro-aula");
  let aulasAtuais = [];
  let bibliotecaMetodos = [];

  const fotosDasAlunas = (aula, opcoes = {}) => `<div class="lesson-students ${opcoes.selecionavel ? "students-selectable" : ""}">${aula.alunas.map((aluna, indice) => {
    const foto = aula.fotos?.[aluna];
    const iniciais = String(aluna || "?").split(/\s+/).slice(0, 2).map((parte) => parte[0]).join("");
    const retrato = foto ? `<button class="photo-zoom lesson-photo" type="button" data-foto-zoom="${escapeHtml(foto)}" data-foto-titulo="${escapeHtml(aluna)}" title="Ampliar foto de ${escapeHtml(aluna)}"><img src="${escapeHtml(foto)}" alt="Foto de ${escapeHtml(aluna)}"></button>` : `<span title="${escapeHtml(aluna)}">${escapeHtml(iniciais)}</span>`;
    const status = opcoes.statusChamada?.[aluna] || "Presente";
    const indisponivel = Boolean(opcoes.statusChamada) && /ausente|justificada|falta/i.test(String(status));
    const seletor = opcoes.selecionavel ? `<label class="student-select-check" title="${indisponivel ? `${escapeHtml(aluna)}: ${escapeHtml(status)}` : `Incluir ${escapeHtml(aluna)} no registro`}"><input type="checkbox" data-aluna-turma="${indice}" ${indisponivel ? "disabled" : "checked"}><span aria-hidden="true"></span></label>` : "";
    return `<div class="lesson-student ${opcoes.selecionavel ? "is-selectable" : ""} ${indisponivel ? "is-absent" : ""}">${seletor}${retrato}<small>${escapeHtml(aluna)}${indisponivel ? `<em>Falta${/justificada/i.test(String(status)) ? " justificada" : ""}</em>` : ""}</small></div>`;
  }).join("")}</div>`;

  const abrirRegistro = async (indice) => {
    const aula = aulasAtuais[indice];
    if (!aula) return;
    let registrosSalvos = [];
    let licoesPendentes = [];
    let historicoPratica = [];
    try { registrosSalvos = await window.GemData.registrosDaAula({ dataIso: $("#agenda-data").value, instrutora: state.name, alunas: aula.alunas }); }
    catch (erro) { console.warn("Registros anteriores não puderam ser carregados", erro); }
    const ehAulaDeSolfejo = String(aula.tipo || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase().includes("SOLFEJO");
    // Solfejo é conferido no próprio registro da aula seguinte. Nunca abre a
    // fila visual de correções (nem MSA, nem método) nessa tela.
    try { licoesPendentes = ehAulaDeSolfejo ? [] : await window.GemData.licoesPendentesProfessora({ alunas: aula.alunas, tipoAula: aula.tipo }); }
    catch (erro) { console.warn("Lições pendentes não puderam ser carregadas", erro); }
    if (aula.tipo === "Prática") {
      try { historicoPratica = await window.GemData.contextoPratica({ aluna: aula.alunas[0], dataIso: $("#agenda-data").value }); }
      catch (erro) { console.warn("Histórico anterior de Prática não pôde ser carregado", erro); }
    }
    const tipoAnalise = `Analise_${aula.tipo}`;
    const analisesSalvas = registrosSalvos.filter((registro) => registro.Tipo === tipoAnalise);
    const porAluna = Object.fromEntries(analisesSalvas.map((registro) => [registro.Aluna, registro]));
    const primeiroRegistro = porAluna[aula.alunas[0]] || {};
    const partesRegistro = String(primeiroRegistro.Licao_Atual || "").split(":");
    const materialSalvo = partesRegistro.length > 1 ? partesRegistro.shift().trim() : "";
    const conteudoSalvo = partesRegistro.length > 1 ? partesRegistro.join(":").trim() : (partesRegistro[0] || "");
    const opcoesDificuldades = dificuldadesPorAula[aula.tipo] || dificuldadesPorAula.Solfejo;
    const aulaPorTurma = !aula.individual;
    // A chamada é a fonte de presença, como no app.py. Ausentes e justificadas
    // continuam visíveis para a professora, mas não podem receber análise.
    let statusChamada = {};
    try {
      const chamada = await window.GemData.dadosChamada($("#agenda-data").value);
      statusChamada = Object.fromEntries((chamada.chamadas || []).map((item) => [item.Aluna, item.Status]));
    } catch (erro) { console.warn("Não foi possível consultar a chamada antes do registro", erro); }
    const presente = (aluna) => !/ausente|justificada|falta/i.test(String(statusChamada[aluna] || ""));
    const faltaIndividual = aula.individual && !presente(aula.alunas[0]);
    const turmaTodaAusente = aulaPorTurma && aula.alunas.length > 0 && aula.alunas.every((aluna) => !presente(aluna));
    const registroBloqueadoPorFalta = faltaIndividual || turmaTodaAusente;
    const dificuldadesSalvas = new Set(Array.isArray(primeiroRegistro.Dificuldades) ? primeiroRegistro.Dificuldades : []);
    const dificuldades = `<div class="difficulty-checks">${opcoesDificuldades.map((dificuldade) => `<label><input type="checkbox" data-dificuldade${aulaPorTurma ? "-compartilhada" : "-aluna"} ${aulaPorTurma ? "" : `data-dificuldade-aluna="${escapeHtml(aula.alunas[0])}"`} value="${escapeHtml(dificuldade)}" ${dificuldadesSalvas.has(dificuldade) ? "checked" : ""}> ${escapeHtml(dificuldade)}</label>`).join("")}</div>`;
    const camposIndividuais = (aluna, indice) => {
      const salvo = porAluna[aluna] || {};
      const marcadas = new Set(Array.isArray(salvo.Dificuldades) ? salvo.Dificuldades : []);
      const referenciaLicao = ehAulaDeSolfejo;
      return `<section class="student-record"><h4>${escapeHtml(aluna)}</h4><p class="field-caption">${referenciaLicao ? "Dificuldades observadas na lição de casa apresentada:" : "Dificuldades observadas:"}</p><div class="difficulty-checks">${opcoesDificuldades.map((dificuldade) => `<label><input type="checkbox" data-dificuldade-individual="${indice}" value="${escapeHtml(dificuldade)}" ${marcadas.has(dificuldade) ? "checked" : ""}> ${escapeHtml(dificuldade)}</label>`).join("")}</div><label>${referenciaLicao ? "Observações sobre a lição apresentada e a aula:" : "Observações pedagógicas:"}<textarea data-observacao-individual="${indice}" placeholder="Observações sobre ${escapeHtml(aluna)}">${escapeHtml(salvo.Observacao || "")}</textarea></label></section>`;
    };
    const tituloDificuldadesTurma = ehAulaDeSolfejo
      ? "Dificuldades observadas na lição de casa apresentada pela turma:"
      : "Dificuldades compartilhadas para a turma:";
    const tituloObservacaoTurma = ehAulaDeSolfejo
      ? "Observações sobre a lição apresentada e a aula:"
      : "Observações pedagógicas:";
    const secaoDificuldades = aulaPorTurma
      ? `<div id="registro-compartilhado" class="student-records shared-record"><p class="field-caption">${tituloDificuldadesTurma}</p>${dificuldades}<label>${tituloObservacaoTurma}<textarea id="registro-observacao-compartilhada" placeholder="Observação sobre a aula da turma">${escapeHtml(primeiroRegistro.Observacao || "")}</textarea></label></div><div id="registro-por-aluna" class="student-records hidden"></div>`
      : `<div class="student-records"><section class="student-record"><h4>${escapeHtml(aula.alunas[0])}</h4><p class="field-caption">Dificuldades observadas:</p>${dificuldades}<label>Observações pedagógicas:<textarea data-observacao-aluna="${escapeHtml(aula.alunas[0])}" placeholder="Observações sobre a aula">${escapeHtml(primeiroRegistro.Observacao || "")}</textarea></label></section></div>`;
    const opcoesLicaoGenerica = `<option value="">Não deixar lição</option>`;
    const opcoesPratica = ["Apostila", ...bibliotecaMetodos.filter((metodo) => metodo.categoria === "Prática").map((metodo) => metodo.nome)];
    const campoMaterial = aula.tipo === "Prática" ? `<select id="registro-material"><option value="">Selecione o método/apostila</option>${opcoesPratica.map((material) => `<option ${material === materialSalvo ? "selected" : ""}>${escapeHtml(material)}</option>`).join("")}</select><small class="field-help">Cadastre novos métodos em Configurar Métodos.</small>` : `<input id="registro-material" value="${escapeHtml(materialSalvo)}" placeholder="Ex.: MSA, Apostila, Folha Extra">`;
    const registrosVisiveis = analisesSalvas.length ? `<section class="saved-records"><h4>Registro já salvo nesta aula</h4>${analisesSalvas.map((registro) => { const diffs = Array.isArray(registro.Dificuldades) ? registro.Dificuldades : []; return `<article><strong>${escapeHtml(registro.Aluna)}</strong><span>${escapeHtml(registro.Licao_Atual || "—")}</span>${diffs.length ? `<small>⚠ ${escapeHtml(diffs.join(" · "))}</small>` : ""}${registro.Observacao ? `<small>📝 ${escapeHtml(registro.Observacao)}</small>` : ""}</article>`; }).join("")}</section>` : "";
    const casaSalva = (tipos) => registrosSalvos.find((registro) => aula.alunas.includes(registro.Aluna) && tipos.includes(String(registro.Tipo || ""))) || {};
    const casaTeoriaSalva = casaSalva(["Casa_Teoria", "Casa_Teoria_Prof", "Casa_Apostila_Teoria_Prof", "Casa_Apostila_Teoria"]);
    const casaGenericaTipo = aula.tipo === "Solfejo" ? "Casa_MSA" : aula.tipo === "Solfejo Melódico" ? "Casa_Canto" : "";
    const casaGenericaSalva = casaGenericaTipo ? casaSalva([casaGenericaTipo]) : {};
    const teoriaApostila = ["Casa_Apostila_Teoria_Prof", "Casa_Apostila_Teoria"].includes(casaTeoriaSalva.Tipo);
    const teoriaSecretaria = casaTeoriaSalva.Tipo !== "Casa_Teoria_Prof";
    const tituloCasa = (tipo) => tipo === "Casa_MSA" ? "MSA de Solfejo" : tipo === "Casa_Canto" ? "Estudo de Solfejo Melódico" : ["Casa_Apostila_Teoria_Prof", "Casa_Apostila_Teoria"].includes(tipo) ? "Apostila de Teoria" : tipo === "Casa_Teoria_Prof" ? "Folha avulsa de Teoria" : ["Casa_Apostila_Prof", "Casa_Apostila"].includes(tipo) ? "Apostila de Prática" : "Método de Prática";
    // Resultado é uma decisão única: radio evita que uma mesma lição seja
    // salva, por engano, como resolvida e não resolvida ao mesmo tempo.
    const opcoesResultadoPendente = (indice, metodo) => (metodo ? ["Passou", "Não passou", "Estudar mais"] : ["Resolvido", "Resolvido com pendências", "Não resolvido", "Não trouxe a apostila/atividade"]).map((resultado, posicao) => `<label class="result-check ${posicao === 0 ? "selected" : ""}"><input type="radio" name="status-pendente-${indice}" data-status-pendente="${indice}" data-resultado-metodo="${metodo ? "1" : "0"}" value="${resultado}" ${posicao === 0 ? "checked" : ""}><span>${escapeHtml(resultado)}</span></label>`).join("");
    const correcoesPendentes = aula.tipo !== "Prática" && licoesPendentes.length ? `<section class="teacher-corrections correction-queue"><div class="correction-queue-head"><div><h4>📋 Correções para esta aula</h4><p>Escolha o resultado, registre a observação e salve. A informação entra no histórico da aluna.</p></div><span>${licoesPendentes.length} pendente${licoesPendentes.length > 1 ? "s" : ""}</span></div>${licoesPendentes.map((licao, indicePendente) => {
      const metodo = String(licao.Tipo || "").startsWith("Casa_Metodo_");
      const tipo = tituloCasa(licao.Tipo);
      const subtitulo = metodo ? "Se não passou, a lição de reforço será levada para a próxima aula." : "Esta lição é corrigida pela professora; não aparece na fila da Secretaria.";
      return `<article class="pending-card correction-card"><div class="correction-card-info"><span class="correction-kind">${escapeHtml(tipo)}</span><h3>${escapeHtml(licao.Aluna)}</h3><p>Deixada em ${escapeHtml(licao.Data || "—")}</p><p class="correction-homework">📚 ${escapeHtml(licao.Licao_Casa || "Lição não informada")}</p><small>${escapeHtml(subtitulo)}</small></div><div class="pending-action"><div class="result-area"><strong>Resultado</strong><div class="result-checks">${opcoesResultadoPendente(indicePendente, metodo)}</div></div>${metodo ? `<label class="correction-note hidden" data-reforco-wrap="${indicePendente}">Lição de reforço para a próxima aula<textarea data-reforco-pendente="${indicePendente}" placeholder="Edite a lição que a aluna deve retomar.">${escapeHtml(licao.Licao_Casa || "")}</textarea><small>Obrigatória para “Não passou” ou “Estudar mais”.</small></label>` : ""}<label class="correction-note">Observação da professora<textarea data-obs-pendente="${indicePendente}" placeholder="Ex.: realizou parcialmente; retomar os exercícios 3 e 4."></textarea></label><button class="primary-action" type="button" data-corrigir-licao="${indicePendente}">Salvar correção</button></div></article>`;
    }).join("")}</section>` : "";
    const licaoTeoria = `<section class="homework-panel"><h4>🏠 Lição de casa</h4><p>Folha avulsa pode ser encaminhada para a Secretaria ou corrigida por você na próxima aula. Apostila de Teoria é sempre corrigida pela professora.</p><div class="homework-options"><label class="result-check ${!teoriaApostila ? "selected" : ""}"><input type="radio" name="tipo-casa-teoria" value="folha" ${!teoriaApostila ? "checked" : ""}> Folha avulsa</label><label class="result-check ${teoriaApostila ? "selected" : ""}"><input type="radio" name="tipo-casa-teoria" value="apostila" ${teoriaApostila ? "checked" : ""}> Apostila de Teoria</label></div><div id="corretora-folha" class="homework-options"><strong>Quem corrige a folha avulsa?</strong><label class="result-check ${teoriaSecretaria ? "selected" : ""}"><input type="radio" name="corretora-folha" value="Secretaria" ${teoriaSecretaria ? "checked" : ""}> Secretaria</label><label class="result-check ${!teoriaSecretaria ? "selected" : ""}"><input type="radio" name="corretora-folha" value="Professora" ${!teoriaSecretaria ? "checked" : ""}> Eu mesma, na próxima aula</label></div><label>Lição deixada para casa<input id="registro-casa" value="${escapeHtml(casaTeoriaSalva.Licao_Casa || "")}" placeholder="Ex.: folha 3, exercícios 1 a 4"></label><label>Observação da lição (opcional)<textarea id="registro-obs-casa" placeholder="Ex.: fazer com metrônomo e trazer as dúvidas.">${escapeHtml(casaTeoriaSalva.Observacao || "")}</textarea></label></section>`;
    const licaoGenerica = `<div class="record-form"><div><label for="registro-casa-tipo">Lição de casa</label><select id="registro-casa-tipo">${opcoesLicaoGenerica}</select></div><div><label for="registro-casa">Lição deixada para casa</label><input id="registro-casa" value="${escapeHtml(casaGenericaSalva.Licao_Casa || "")}" placeholder="Ex.: página 18, exercícios 1 e 2" disabled></div></div>`;
    const licaoSolfejo = `<section class="homework-panel"><h4>🎼 Estudo para a próxima aula</h4><p>${aula.tipo === "Solfejo Melódico" ? "Registre o estudo que será trabalhado até o próximo encontro." : "Registre a lição de MSA que será trabalhada até o próximo encontro."} Não há etapa separada de “passou/não passou”.</p><label>${aula.tipo === "Solfejo Melódico" ? "Estudo de Solfejo Melódico" : "Lição de Solfejo (MSA)"}<input id="registro-casa" value="${escapeHtml(casaGenericaSalva.Licao_Casa || "")}" placeholder="${aula.tipo === "Solfejo Melódico" ? "Ex.: vocalize, música ou trecho para praticar" : "Ex.: MSA, exercício ou página para estudar"}"></label><label>Observação da lição (opcional)<textarea id="registro-obs-casa" placeholder="Ex.: estudar lentamente e marcar a pulsação.">${escapeHtml(casaGenericaSalva.Observacao || "")}</textarea></label></section>`;
    const praticaMarkup = aula.tipo === "Prática" ? `<section class="practice-register"><div class="practice-register-head"><div><h4>🎹 Métodos e apostila conferidos hoje</h4><p>Escolha o método na lista e faça um registro para cada lição trabalhada.</p></div></div><div id="materiais-pratica"></div><button id="adicionar-material-pratica" class="secondary-action" type="button">＋ Adicionar outra lição</button><label class="practice-observation">Observações pedagógicas gerais<textarea id="registro-observacao-pratica" placeholder="Observações sobre a aula e a evolução da aluna"></textarea></label><section id="licoes-casa-pratica" class="practice-homework-panel"></section></section>` : `<div class="record-form"><div><label for="registro-material">Material usado hoje:</label>${campoMaterial}</div><div><label for="registro-conteudo">Página/Lição trabalhada:</label><input id="registro-conteudo" value="${escapeHtml(conteudoSalvo)}" placeholder="Ex.: MSA: exercício 9, páginas 12 a 15"></div></div>${secaoDificuldades}${aula.tipo === "Teoria" ? licaoTeoria : ["Solfejo", "Solfejo Melódico"].includes(aula.tipo) ? licaoSolfejo : licaoGenerica}`;
    const avisoFalta = registroBloqueadoPorFalta ? `<section class="absence-register"><h4>🚫 Falta registrada</h4><p>${faltaIndividual ? (/justificada/i.test(String(statusChamada[aula.alunas[0]])) ? "Falta justificada" : "Ausente") : "Todas as alunas desta turma estão ausentes ou justificadas"}. Não é possível lançar registro pedagógico para esta aula.</p></section>` : "";
    const corpoRegistro = registroBloqueadoPorFalta ? avisoFalta : `${registrosVisiveis}${correcoesPendentes}${praticaMarkup}<div class="register-actions"><button id="salvar-registro-aula" class="primary-action" type="button">Salvar registro da aula</button><div id="registro-retorno"></div></div>`;
    areaRegistro.innerHTML = `<section class="lesson-register"><div class="register-heading"><div><p class="eyebrow">LANÇAR REGISTRO</p><h3>📝 Registro: ${escapeHtml(aula.tipo)}</h3><p>${escapeHtml(aula.individual ? "Aula individual" : `Aula por turma${aula.turma ? ` · ${aula.turma}` : ""}`)}</p></div><button id="fechar-registro" class="secondary-action" type="button">Fechar</button></div>${fotosDasAlunas(aula, { selecionavel: aulaPorTurma, statusChamada })}${corpoRegistro}</section>`;
    $("#fechar-registro").addEventListener("click", () => { areaRegistro.innerHTML = ""; });
    if (registroBloqueadoPorFalta) { areaRegistro.scrollIntoView({ behavior: "smooth", block: "start" }); return; }
    areaRegistro.querySelectorAll("[data-corrigir-licao]").forEach((botao) => botao.addEventListener("click", async () => {
      const indicePendente = Number(botao.dataset.corrigirLicao), licao = licoesPendentes[indicePendente];
      const status = areaRegistro.querySelector(`[data-status-pendente="${indicePendente}"]:checked`)?.value;
      if (!status) { botao.closest(".pending-action").insertAdjacentHTML("beforeend", `<div class="action-error">Escolha o resultado da correção.</div>`); return; }
      botao.disabled = true;
      try {
        const reforco = areaRegistro.querySelector(`[data-reforco-pendente="${indicePendente}"]`);
        if (["Não passou", "Estudar mais"].includes(status) && !reforco?.value.trim()) { botao.closest(".pending-action").insertAdjacentHTML("beforeend", `<div class="action-error">Informe a lição de reforço para a próxima aula.</div>`); botao.disabled = false; return; }
        await window.GemData.corrigirLicaoProfessora(licao.id, { status, observacao: areaRegistro.querySelector(`[data-obs-pendente="${indicePendente}"]`).value, repetirLicao: reforco?.value, dataIso: $("#agenda-data").value, instrutora: state.name, licao });
        botao.textContent = "Correção salva ✓";
        botao.closest("article").classList.add("is-corrected");
      } catch (erro) { alert(erro.message); botao.disabled = false; }
    }));
    if (aulaPorTurma) {
      const atualizarSelecionadas = () => {
        const selecionadas = [...areaRegistro.querySelectorAll("[data-aluna-turma]:checked")].map((campo) => Number(campo.dataset.alunaTurma));
        const individual = selecionadas.length === 1;
        $("#registro-compartilhado").classList.toggle("hidden", individual || !selecionadas.length);
        $("#registro-por-aluna").classList.toggle("hidden", !individual && selecionadas.length > 0);
        if (individual) $("#registro-por-aluna").innerHTML = camposIndividuais(aula.alunas[selecionadas[0]], selecionadas[0]);
        if (!selecionadas.length) $("#registro-por-aluna").innerHTML = `<div class="action-error">Marque ao menos uma aluna presente para registrar.</div>`;
      };
      areaRegistro.querySelectorAll("[data-aluna-turma]").forEach((campo) => campo.addEventListener("change", atualizarSelecionadas));
      atualizarSelecionadas();
    }
    if (aula.tipo === "Prática") {
      const areaMateriais = $("#materiais-pratica");
      const materiaisRegistrados = analisesSalvas.map((registro) => {
        const partes = String(registro.Licao_Atual || "").split(":");
        const material = partes.length > 1 ? partes.shift().trim() : "Apostila";
        const tipoCasa = material === "Apostila" ? "Casa_Apostila" : `Casa_Metodo_${material}`;
        const casaSalva = registrosSalvos.find((item) => item.Tipo === tipoCasa);
        return { material, conteudo: partes.join(":").trim(), dificuldades: Array.isArray(registro.Dificuldades) ? registro.Dificuldades : [], licaoCasa: casaSalva?.Licao_Casa || "" };
      }).filter((item) => opcoesPratica.includes(item.material));
      let proximoMaterial = 0;
      const licoesCasaSalvas = registrosSalvos
        .filter((item) => aula.alunas.includes(item.Aluna) && (item.Tipo === "Casa_Apostila" || String(item.Tipo || "").startsWith("Casa_Metodo_")))
        .map((item) => ({ material: item.Tipo === "Casa_Apostila" ? "Apostila" : String(item.Tipo).replace(/^Casa_Metodo_/, ""), licaoCasa: item.Licao_Casa || "", observacao: item.Observacao || "" }))
        .filter((item) => opcoesPratica.includes(item.material));
      const linhaLicaoCasa = (registro = {}) => `<div class="practice-homework-row" data-casa-item><label>Material da lição<select data-casa-material>${opcoesPratica.map((material) => `<option value="${escapeHtml(material)}" ${material === (registro.material || "Apostila") ? "selected" : ""}>${escapeHtml(material)}</option>`).join("")}</select></label><label>Lição para a próxima aula<input data-casa-conteudo value="${escapeHtml(registro.licaoCasa || "")}" placeholder="Ex.: página 20, exercícios 1 e 2"></label><button class="icon-action" data-remover-casa type="button" title="Remover esta lição">×</button><label class="practice-homework-note">Observação da lição (opcional)<textarea data-casa-observacao placeholder="Ex.: fazer devagar com metrônomo.">${escapeHtml(registro.observacao || "")}</textarea></label></div>`;
      const conectarLicoesCasa = (areaCasa) => {
        areaCasa.querySelectorAll("[data-remover-casa]").forEach((botao) => { if (!botao.dataset.conectado) { botao.dataset.conectado = "1"; botao.addEventListener("click", () => { const linhas = areaCasa.querySelectorAll("[data-casa-item]"); if (linhas.length > 1) botao.closest("[data-casa-item]").remove(); else botao.closest("[data-casa-item]").querySelector("[data-casa-conteudo]").value = ""; }); } });
      };
      const montarLicoesCasa = () => {
        const areaCasa = $("#licoes-casa-pratica");
        if (!areaCasa) return;
          const iniciais = licoesCasaSalvas.length ? licoesCasaSalvas : [{ material: "Apostila", licaoCasa: "", observacao: "" }];
        areaCasa.innerHTML = `<h3>🏠 Lição de casa para a próxima aula</h3><p>Escolha Apostila ou o método em cada linha. Apostila segue para a Secretaria; métodos ficam para a professora conferir.</p><div data-lista-casas>${iniciais.map((item) => linhaLicaoCasa(item)).join("")}</div><button data-adicionar-casa class="secondary-action" type="button">＋ Adicionar lição de casa</button>`;
        areaCasa.querySelector("[data-adicionar-casa]").addEventListener("click", () => { areaCasa.querySelector("[data-lista-casas]").insertAdjacentHTML("beforeend", linhaLicaoCasa()); conectarLicoesCasa(areaCasa); });
        conectarLicoesCasa(areaCasa);
      };
      const linhasDificuldadesPratica = (marcadas = []) => dificuldadesPorAula.Prática.map((dificuldade) => `<label><input type="checkbox" data-dificuldade-pratica value="${escapeHtml(dificuldade)}" ${marcadas.includes(dificuldade) ? "checked" : ""}> ${escapeHtml(dificuldade)}</label>`).join("");
      // A correção com os quatro resultados é exclusiva da Apostila. Os
      // métodos mantêm as dificuldades e o resultado pedagógico próprios.
      const dificuldadesDoMaterial = (nomeMaterial, marcadas = []) => !nomeMaterial || nomeMaterial === "Apostila" ? "" : `<p class="field-caption">Dificuldades observadas na lição de casa e no material trabalhado:</p><div class="difficulty-checks">${linhasDificuldadesPratica(marcadas)}</div>`;
      const novaLinhaExercicio = (exercicio = {}) => `<div class="exercise-row"><label>Lição/exercício trabalhado<input data-exercicio-nome value="${escapeHtml(exercicio.exercicio || "")}" placeholder="Ex.: Estudo 21, exercício 3"></label><div class="difficulty-checks compact">${dificuldadesPorAula.Prática.map((dificuldade) => `<label><input type="checkbox" data-exercicio-dificuldade value="${escapeHtml(dificuldade)}" ${(exercicio.dificuldades || []).includes(dificuldade) ? "checked" : ""}> ${escapeHtml(dificuldade)}</label>`).join("")}</div><button class="icon-action remover-exercicio" type="button" title="Remover lição/exercício">×</button></div>`;
      const conectarExercicios = (cartao) => {
        cartao.querySelector("[data-adicionar-exercicio]").addEventListener("click", () => {
          cartao.querySelector("[data-exercicios]").insertAdjacentHTML("beforeend", novaLinhaExercicio());
          conectarExercicios(cartao);
        });
        cartao.querySelectorAll(".remover-exercicio").forEach((botao) => { if (!botao.dataset.conectado) { botao.dataset.conectado = "1"; botao.addEventListener("click", () => botao.closest(".exercise-row").remove()); } });
      };
      const conectarCorrecaoPratica = (cartao) => {
        const correcao = cartao.querySelector("[data-pratica-correcao]");
        const resultado = cartao.querySelector("[data-pratica-resultado]");
        if (!correcao || !resultado) return;
        resultado.querySelectorAll('input[type="radio"]').forEach((campo) => campo.addEventListener("change", () => {
          resultado.querySelectorAll(".result-check").forEach((opcao) => opcao.classList.toggle("selected", opcao.querySelector("input").checked));
          if (correcao.dataset.correcaoTipo === "apostila") return;
          const metodo = cartao.querySelector("[data-pratica-material]").value;
          const casa = [...$("#licoes-casa-pratica").querySelectorAll("[data-casa-item]")].find((linha) => linha.querySelector("[data-casa-material]")?.value === metodo)?.querySelector("[data-casa-conteudo]");
          if (campo.checked && ["Não passou", "Estudar mais"].includes(campo.value) && casa && !casa.value.trim()) casa.value = correcao.dataset.licaoPendente || "";
        }));
      };
      const adicionarMaterial = async (registro = {}) => {
        const indice = proximoMaterial++;
        const material = registro.material || "";
        const cartao = document.createElement("article");
        cartao.className = "practice-material-card";
        cartao.dataset.materialIndex = indice;
        // A Apostila é acompanhada também pela Secretaria. “Resolvido” é o
        // único resultado que a retira da fila; os demais continuam visíveis.
        const pendenciaApostila = () => historicoPratica.find((licao) => ["Casa_Apostila", "Casa_Apostila_Prof"].includes(licao.Tipo) && !["Resolvido", "Realizada", "Realizada - sem pendência", "Realizadas - sem pendência"].includes(licao.Status));
        const referenciaApostila = () => {
          const pendente = pendenciaApostila();
          if (pendente) return { ...pendente, automatica: false };
          const ultimaApostila = historicoPratica.find((item) => item.Tipo === "Analise_Prática" && String(item.Licao_Atual || "").startsWith("Apostila:"));
          if (!ultimaApostila) return null;
          return { id: "", Licao_Casa: String(ultimaApostila.Licao_Atual || "").split(":").slice(1).join(":").trim(), Observacao: "", Status: "", automatica: true };
        };
        const correcaoDaLicao = (nomeMaterial) => {
          const apostila = nomeMaterial === "Apostila";
          const pendente = apostila ? referenciaApostila() : licoesPendentes.find((licao) => String(licao.Tipo || "") === `Casa_Metodo_${nomeMaterial}`);
          if (!pendente) return "";
          return `<section class="practice-correction ${apostila ? "secretary-style-correction" : ""}" data-pratica-correcao data-correcao-tipo="${apostila ? "apostila" : "metodo"}" data-correcao-automatica="${pendente.automatica ? "true" : "false"}" data-licao-pendente-id="${escapeHtml(pendente.id)}" data-licao-pendente="${escapeHtml(pendente.Licao_Casa || "")}"><h4>📋 ${apostila ? "Correção da Apostila" : "Lição de casa a conferir"}</h4><p>📚 ${escapeHtml(pendente.Licao_Casa || "Lição não informada")}</p>${apostila ? "<small>Escolha o resultado e registre a observação, como na correção da Secretaria. Somente “Resolvido” não aparece para a Secretaria.</small>" : ""}</section>`;
        };
        const resultadoDaCorrecao = (nomeMaterial) => {
          const apostila = nomeMaterial === "Apostila";
          const pendente = apostila ? referenciaApostila() : licoesPendentes.find((licao) => String(licao.Tipo || "") === `Casa_Metodo_${nomeMaterial}`);
          if (!pendente) return "";
          const opcoes = apostila ? ["Resolvido", "Resolvido com pendências", "Não resolvido"] : ["Passou", "Não passou", "Estudar mais"];
          return `<div class="practice-result" data-pratica-resultado><strong>Resultado da correção</strong><div class="result-checks">${opcoes.map((resultado, posicao) => `<label class="result-check ${apostila ? (pendente.Status === resultado ? "selected" : "") : (posicao === 0 ? "selected" : "")}"><input type="radio" name="resultado-pratica-${indice}" value="${escapeHtml(resultado)}" ${apostila ? (pendente.Status === resultado ? "checked" : "") : (posicao === 0 ? "checked" : "")}> <span>${escapeHtml(resultado)}</span></label>`).join("")}</div>${apostila ? `<label class="correction-note">Observação da correção<textarea data-pratica-obs-correcao placeholder="Ex.: exercícios incompletos; retomar as páginas 36 e 37.">${escapeHtml(String(pendente.Observacao || "").replace(/^Sec:\s*/i, ""))}</textarea></label>` : ""}</div>`;
        };
        const resumoUltimaAula = (nomeMaterial) => {
          const anterior = historicoPratica.find((item) => item.Tipo === "Analise_Prática" && String(item.Licao_Atual || "").startsWith(`${nomeMaterial}:`));
          if (!nomeMaterial) return `<p class="practice-last-class">Selecione primeiro um método ou Apostila para registrar a aula.</p>`;
          if (!anterior) return `<p class="practice-last-class">📋 Nenhuma aula anterior encontrada com este método.</p>`;
          const conteudoAnterior = String(anterior.Licao_Atual || "").split(":").slice(1).join(":").trim();
          const dificuldadesAnteriores = Array.isArray(anterior.Dificuldades) ? anterior.Dificuldades.filter((item) => item && item !== "Não apresentou dificuldades") : [];
          return `<p class="practice-last-class">📋 <strong>Última aula (${escapeHtml(anterior.Data || "—")}):</strong> ${escapeHtml(conteudoAnterior || "conteúdo não informado")}${dificuldadesAnteriores.length ? ` — ⚠ dificuldades: ${escapeHtml(dificuldadesAnteriores.join(" · "))}` : " — ✓ sem dificuldades"}</p>`;
        };
        cartao.innerHTML = `<div class="practice-material-title"><label>Método/Apostila da lição registrada<select data-pratica-material><option value="" ${!material ? "selected" : ""}>Selecione o método ou Apostila</option>${opcoesPratica.map((opcao) => `<option value="${escapeHtml(opcao)}" ${opcao === material ? "selected" : ""}>${escapeHtml(opcao)}</option>`).join("")}</select></label><button class="icon-action remover-material" type="button" title="Remover esta lição">×</button></div><div data-pratica-resumo-area>${resumoUltimaAula(material)}</div><div data-pratica-correcao-area>${correcaoDaLicao(material)}</div><div data-pratica-resultado-area>${resultadoDaCorrecao(material)}</div><label>Conteúdo trabalhado hoje — página/lição<input data-pratica-conteudo value="${escapeHtml(registro.conteudo || "")}" placeholder="Ex.: página 18, exercício 4"></label><div data-pratica-dificuldades-area>${dificuldadesDoMaterial(material, registro.dificuldades || [])}</div>`;
        areaMateriais.appendChild(cartao);
        conectarCorrecaoPratica(cartao);
        cartao.querySelector(".remover-material").addEventListener("click", () => { if (areaMateriais.children.length > 1) cartao.remove(); });
        const atualizarMaterialPratica = () => {
          const dificuldadesMarcadas = [...cartao.querySelectorAll("[data-dificuldade-pratica]:checked")].map((campo) => campo.value);
          cartao.querySelector("[data-pratica-correcao-area]").innerHTML = correcaoDaLicao(cartao.querySelector("[data-pratica-material]").value);
          cartao.querySelector("[data-pratica-resultado-area]").innerHTML = resultadoDaCorrecao(cartao.querySelector("[data-pratica-material]").value);
          cartao.querySelector("[data-pratica-resumo-area]").innerHTML = resumoUltimaAula(cartao.querySelector("[data-pratica-material]").value);
          cartao.querySelector("[data-pratica-dificuldades-area]").innerHTML = dificuldadesDoMaterial(cartao.querySelector("[data-pratica-material]").value, dificuldadesMarcadas);
          conectarCorrecaoPratica(cartao);
        };
        cartao.querySelector("[data-pratica-material]").addEventListener("change", atualizarMaterialPratica);
      };
      for (const registro of (materiaisRegistrados.length ? materiaisRegistrados : [{ material: materialSalvo || "", conteudo: conteudoSalvo, dificuldades: dificuldadesSalvas }])) await adicionarMaterial(registro);
      montarLicoesCasa();
      $("#adicionar-material-pratica").addEventListener("click", () => adicionarMaterial());
    } else if (aula.tipo === "Teoria") {
      const atualizarLicaoTeoria = () => {
        const folha = areaRegistro.querySelector('input[name="tipo-casa-teoria"]:checked').value === "folha";
        $("#corretora-folha").classList.toggle("hidden", !folha);
        areaRegistro.querySelectorAll('input[name="tipo-casa-teoria"], input[name="corretora-folha"]').forEach((campo) => campo.closest(".result-check").classList.toggle("selected", campo.checked));
      };
      areaRegistro.querySelectorAll('input[name="tipo-casa-teoria"], input[name="corretora-folha"]').forEach((campo) => campo.addEventListener("change", atualizarLicaoTeoria));
      atualizarLicaoTeoria();
    } else if (!["Solfejo", "Solfejo Melódico"].includes(aula.tipo)) {
      const tipoCasa = $("#registro-casa-tipo"), licaoCasa = $("#registro-casa");
      tipoCasa.addEventListener("change", () => { licaoCasa.disabled = !tipoCasa.value; if (!tipoCasa.value) licaoCasa.value = ""; });
    }
    areaRegistro.querySelectorAll("[data-status-pendente]").forEach((campo) => campo.addEventListener("change", () => {
      if (campo.checked) areaRegistro.querySelectorAll(`[data-status-pendente="${campo.dataset.statusPendente}"]`).forEach((outro) => { if (outro !== campo) outro.checked = false; });
      areaRegistro.querySelectorAll(`[data-status-pendente="${campo.dataset.statusPendente}"]`).forEach((outro) => outro.closest(".result-check").classList.toggle("selected", outro.checked));
      const reforco = areaRegistro.querySelector(`[data-reforco-wrap="${campo.dataset.statusPendente}"]`);
      if (reforco) reforco.classList.toggle("hidden", !["Não passou", "Estudar mais"].includes(campo.value) || !campo.checked);
    }));
    $("#salvar-registro-aula").addEventListener("click", async () => {
      const botao = $("#salvar-registro-aula");
      const conteudo = $("#registro-conteudo")?.value.trim();
      const material = $("#registro-material")?.value.trim();
      // Igual ao app.py: o registro pedagógico identifica tanto o material
      // quanto a página/lição. Isso evita históricos sem referência.
      if (aula.tipo !== "Prática" && (!material || !conteudo)) { $("#registro-retorno").innerHTML = `<div class="action-error">Informe o material e o conteúdo trabalhado antes de salvar.</div>`; return; }
      const alunasParaSalvar = aulaPorTurma
        ? [...areaRegistro.querySelectorAll("[data-aluna-turma]:checked")].map((campo) => aula.alunas[Number(campo.dataset.alunaTurma)])
        : [...aula.alunas];
      if (!alunasParaSalvar.length) { $("#registro-retorno").innerHTML = `<div class="action-error">Marque ao menos uma aluna presente para receber o registro.</div>`; return; }
      const modoIndividualTurma = aulaPorTurma && alunasParaSalvar.length === 1;
      const marcadas = [...areaRegistro.querySelectorAll("input[data-dificuldade-aluna]:checked")];
      const observacoes = [...areaRegistro.querySelectorAll("[data-observacao-aluna]")];
      const dificuldadesCompartilhadas = [...areaRegistro.querySelectorAll("input[data-dificuldade-compartilhada]:checked")].map((campo) => campo.value);
      const observacaoCompartilhada = $("#registro-observacao-compartilhada")?.value.trim() || "";
      const registrosPorAluna = Object.fromEntries(alunasParaSalvar.map((aluna) => {
        const indice = aula.alunas.indexOf(aluna);
        return [aluna, {
        dificuldades: modoIndividualTurma
          ? [...areaRegistro.querySelectorAll(`[data-dificuldade-individual="${indice}"]:checked`)].map((campo) => campo.value)
          : aulaPorTurma ? dificuldadesCompartilhadas : marcadas.filter((campo) => campo.dataset.dificuldadeAluna === aluna).map((campo) => campo.value),
        observacao: modoIndividualTurma
          ? areaRegistro.querySelector(`[data-observacao-individual="${indice}"]`)?.value.trim() || ""
          : aulaPorTurma ? observacaoCompartilhada : observacoes.find((campo) => campo.dataset.observacaoAluna === aluna)?.value.trim() || ""
        }];
      }));
      botao.disabled = true;
      try {
        if (aula.tipo === "Prática") {
          const licoesCasa = [...areaRegistro.querySelectorAll("[data-casa-item]")].map((linha) => ({ material: linha.querySelector("[data-casa-material]")?.value || "", licaoCasa: linha.querySelector("[data-casa-conteudo]")?.value.trim() || "", observacao: linha.querySelector("[data-casa-observacao]")?.value.trim() || "" }));
          const materiais = [...areaRegistro.querySelectorAll(".practice-material-card")].map((cartao) => {
            const correcao = cartao.querySelector("[data-pratica-correcao]");
            const resultado = cartao.querySelector("[data-pratica-resultado]");
            return {
              material: cartao.querySelector("[data-pratica-material]").value,
              conteudo: cartao.querySelector("[data-pratica-conteudo]").value.trim(),
              dificuldades: [...cartao.querySelectorAll("[data-dificuldade-pratica]:checked")].map((campo) => campo.value),
              exercicios: [...cartao.querySelectorAll(".exercise-row")].map((linha) => ({ exercicio: linha.querySelector("[data-exercicio-nome]").value.trim(), dificuldades: [...linha.querySelectorAll("[data-exercicio-dificuldade]:checked")].map((campo) => campo.value) })),
              licaoPendenteId: correcao?.dataset.licaoPendenteId || "",
              correcaoApostilaAutomatica: correcao?.dataset.correcaoAutomatica === "true",
              licaoPendenteTexto: correcao?.dataset.licaoPendente || "",
              resultadoLicao: resultado?.querySelector('input[type="radio"]:checked')?.value || "",
              observacaoCorrecao: cartao.querySelector("[data-pratica-obs-correcao]")?.value.trim() || ""
            };
          });
          const licoesRepetidas = materiais.map((item) => `${item.material}|${item.conteudo}`).filter((chave, indice, lista) => lista.indexOf(chave) !== indice);
          if (licoesRepetidas.length) throw new Error("Cada registro deve ter uma lição diferente. Use outro conteúdo ou remova o duplicado.");
          await window.GemData.salvarRegistrosPratica({ dataIso: $("#agenda-data").value, instrutora: state.name, aluna: aula.alunas[0], materiais, licoesCasa, observacao: $("#registro-observacao-pratica").value.trim() });
        } else {
          let casaTipo = $("#registro-casa-tipo")?.value || "", licaoCasa = $("#registro-casa")?.value || "";
          if (aula.tipo === "Solfejo") casaTipo = "MSA";
          if (aula.tipo === "Solfejo Melódico") casaTipo = "Canto";
          let limparCasas = aula.tipo === "Solfejo" ? ["Casa_MSA"] : aula.tipo === "Solfejo Melódico" ? ["Casa_Canto"] : [];
          if (aula.tipo === "Teoria") {
            const tipoTeoria = areaRegistro.querySelector('input[name="tipo-casa-teoria"]:checked')?.value;
            limparCasas = ["Casa_Teoria", "Casa_Teoria_Prof", "Casa_Apostila_Teoria", "Casa_Apostila_Teoria_Prof"];
            if (tipoTeoria === "apostila") casaTipo = "Apostila_Teoria_Prof";
            else casaTipo = areaRegistro.querySelector('input[name="corretora-folha"]:checked')?.value === "Secretaria" ? "Teoria" : "Teoria_Prof";
          }
          await window.GemData.salvarRegistroAula({ dataIso: $("#agenda-data").value, instrutora: state.name, tipo: aula.tipo, alunas: alunasParaSalvar, material, conteudo, registrosPorAluna, casaTipo, licaoCasa, observacaoCasa: $("#registro-obs-casa")?.value.trim() || "", limparCasas });
        }
        $("#registro-retorno").innerHTML = `<div class="action-ok">Registro salvo para ${alunasParaSalvar.length === 1 ? "a aluna" : "as alunas"} desta aula.</div>`;
      } catch (erro) { $("#registro-retorno").innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; botao.disabled = false; }
    });
    areaRegistro.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const diaDeDescanso = (dataIso) => {
    const [ano, mes, dia] = String(dataIso || "").split("-");
    const data = ano ? `${dia}/${mes}/${ano}` : "a data escolhida";
    return `<section class="rest-day"><div class="rest-balloons" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div><div class="rest-day-icon" aria-hidden="true">🎈</div><h3>Dia de Descanso!</h3><p>Olá, ${escapeHtml(state.name)}!</p><small>Nenhuma aula encontrada para você nesta data.</small><span>🗓️ ${escapeHtml(data)}</span><em>“O descanso é o tempero que torna o trabalho mais saboroso.”</em></section>`;
  };
  const carregar = async () => {
    lista.innerHTML = `<div class="empty">Carregando agenda...</div>`;
    areaRegistro.innerHTML = "";
    try {
      const [agenda, metodos] = await Promise.all([window.GemData.agendaProfessora(state.name, $("#agenda-data").value), window.GemData.dadosMetodos().catch(() => [])]);
      aulasAtuais = agenda;
      bibliotecaMetodos = metodos;
      if (!aulasAtuais.length) { lista.innerHTML = diaDeDescanso($("#agenda-data").value); return; }
      lista.innerHTML = aulasAtuais.map((aula, indice) => `<article class="agenda-card"><h3>${escapeHtml(aula.horario)} · ${escapeHtml(aula.tipo)}</h3><p><strong>${escapeHtml(aula.local)}</strong></p>${fotosDasAlunas(aula)}<span class="agenda-tag">${aula.individual ? "Aula individual" : `Turma ${escapeHtml(aula.turma || "")}`}</span><button class="secondary-action register-open" type="button" data-registro="${indice}">📝 Registrar aula</button></article>`).join("");
      lista.querySelectorAll("[data-registro]").forEach((botao) => botao.addEventListener("click", () => abrirRegistro(Number(botao.dataset.registro))));
    } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#agenda-data").addEventListener("change", carregar);
  await carregar();
}

async function renderConfigurarMetodos(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">BIBLIOTECA DA PROFESSORA</p><h2>Configurar métodos</h2><p>Cadastre os livros e métodos que aparecem no Registro de Aula. As áreas seguem as disciplinas do modelo de Logística ativo.</p></section><section class="panel"><h3>Adicionar método</h3><div class="form-grid"><div><label for="metodo-nome">Nome do método</label><input id="metodo-nome" placeholder="Ex.: Kohler, Burgmüller, MSA"></div><div><label for="metodo-categoria">Área</label><select id="metodo-categoria" disabled><option>Carregando disciplinas...</option></select><small id="metodo-area-ajuda" class="hint"></small></div><button id="adicionar-metodo" class="primary-action" type="button">Adicionar</button></div><div id="metodo-feedback"></div></section><section class="panel"><h3>Biblioteca cadastrada</h3><div id="lista-metodos" class="lesson-list"><div class="empty">Carregando métodos...</div></div></section>`;
  const lista = $("#lista-metodos");
  const carregarAreas = async () => {
    const seletor = $("#metodo-categoria"), ajuda = $("#metodo-area-ajuda");
    try {
      const modelos = await window.GemData.dadosLogistica();
      const hoje = new Date().toISOString().slice(0, 10);
      const modelo = window.GemData.modeloParaData(modelos, hoje) || modelos.find((item) => item.status !== "encerrado") || null;
      const areas = [...new Set((modelo?.configuracao?.atividades || []).map((atividade) => String(atividade.Atividade || "").trim()).filter(Boolean))];
      if (!areas.length) {
        seletor.innerHTML = `<option value="">Cadastre disciplinas na Logística</option>`; seletor.disabled = true;
        ajuda.textContent = "Crie ou edite um modelo de Logística e inclua as atividades antes de cadastrar métodos.";
        return;
      }
      seletor.innerHTML = areas.map((area) => `<option value="${escapeHtml(area)}">${escapeHtml(area)}</option>`).join("");
      seletor.disabled = false;
      ajuda.textContent = `Áreas disponíveis no modelo “${modelo.nome}”.`;
    } catch (_) {
      seletor.innerHTML = `<option value="">Não foi possível carregar a Logística</option>`; seletor.disabled = true;
      ajuda.textContent = "Confira se há um modelo salvo na Logística.";
    }
  };
  const carregar = async () => {
    try {
      const metodos = await window.GemData.dadosMetodos();
      lista.innerHTML = metodos.length ? metodos.map((metodo, indice) => `<article class="method-row"><div><strong>${escapeHtml(metodo.nome)}</strong><span>${escapeHtml(metodo.categoria)}</span></div><button type="button" class="secondary-action" data-remover-metodo="${indice}">Remover</button></article>`).join("") : `<div class="empty">Nenhum método cadastrado ainda.</div>`;
      lista.querySelectorAll("[data-remover-metodo]").forEach((botao) => botao.addEventListener("click", async () => {
        if (!confirm(`Remover ${metodos[Number(botao.dataset.removerMetodo)].nome} da biblioteca?`)) return;
        try { await window.GemData.removerMetodo(metodos[Number(botao.dataset.removerMetodo)]); await carregar(); }
        catch (erro) { $("#metodo-feedback").innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
      }));
    } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  };
  $("#adicionar-metodo").addEventListener("click", async () => {
    const feedback = $("#metodo-feedback"), nome = $("#metodo-nome").value.trim();
    if (!nome) { feedback.innerHTML = `<div class="action-error">Informe o nome do método.</div>`; return; }
    if ($("#metodo-categoria").disabled || !$("#metodo-categoria").value) { feedback.innerHTML = `<div class="action-error">Cadastre as disciplinas na Logística antes de adicionar um método.</div>`; return; }
    try { await window.GemData.criarMetodo(nome, $("#metodo-categoria").value); $("#metodo-nome").value = ""; feedback.innerHTML = `<div class="action-ok">Método salvo na biblioteca.</div>`; await carregar(); }
    catch (erro) { feedback.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  });
  await Promise.all([carregarAreas(), carregar()]);
}

function formularioDocumento(prefixo, pessoas) {
  const turmas = [...new Set((pessoas.alunas || []).filter((aluna) => aluna.ativo !== false).map((aluna) => aluna.turma).filter(Boolean))].sort((a, b) => a.localeCompare(b, "pt-BR"));
  const alunas = (pessoas.alunas || []).filter((aluna) => aluna.ativo !== false).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
  const destino = () => {
    const modo = $(`#${prefixo}-destino`).value;
    const campo = $(`#${prefixo}-destino-campo`);
    if (modo === "interno") { campo.innerHTML = `<p class="field-help">🔒 Uso interno: nenhuma aluna poderá ver este documento.</p>`; return; }
    if (modo === "turma") { campo.innerHTML = `<label>Turma que receberá<select id="${prefixo}-turma"><option value="">Escolha a turma</option>${turmas.map((turma) => `<option value="${escapeHtml(turma)}">${escapeHtml(turma)}</option>`).join("")}</select></label>`; return; }
    campo.innerHTML = `<label>Aluna que receberá<select id="${prefixo}-aluna"><option value="">Escolha a aluna</option>${alunas.map((aluna) => `<option value="${escapeHtml(aluna.nome)}">${escapeHtml(aluna.nome)}${aluna.turma ? ` · ${escapeHtml(aluna.turma)}` : ""}</option>`).join("")}</select></label>`;
  };
  const markup = `<div class="document-form"><label>Título do documento<input id="${prefixo}-titulo" placeholder="Ex.: Apostila MSA — páginas 7 e 8"></label><label>Disciplina<select id="${prefixo}-disciplina"><option>Prática</option><option>Teoria</option><option>Solfejo</option><option>Solfejo Melódico</option></select></label><label>Destino<select id="${prefixo}-destino"><option value="interno">Uso interno</option><option value="turma">Enviar para uma turma</option><option value="aluna">Enviar para uma aluna</option></select></label><label>Data do documento<input id="${prefixo}-data" type="date" value="${new Date().toISOString().slice(0, 10)}"></label><label class="document-file">Arquivo (PDF ou imagem)<input id="${prefixo}-arquivo" type="file" accept="application/pdf,image/*"></label><label class="document-observation">Observação opcional<textarea id="${prefixo}-observacao" placeholder="Ex.: ler antes da próxima aula"></textarea></label><div id="${prefixo}-destino-campo"></div><button id="${prefixo}-enviar" class="primary-action" type="button">Enviar documento</button></div>`;
  return { markup, destino, vincular: () => { $(`#${prefixo}-destino`).addEventListener("change", destino); destino(); }, dados: () => { const modo = $(`#${prefixo}-destino`).value; return { arquivo: $(`#${prefixo}-arquivo`).files[0], titulo: $(`#${prefixo}-titulo`).value.trim(), disciplina: $(`#${prefixo}-disciplina`).value, data: $(`#${prefixo}-data`).value, turma: modo === "turma" ? $(`#${prefixo}-turma`)?.value || "" : "", aluna: modo === "aluna" ? $(`#${prefixo}-aluna`)?.value || "" : "", observacao: $(`#${prefixo}-observacao`).value.trim(), visivel: modo !== "interno" }; } };
}

async function renderEnvioDocumentosProfessora(content) {
  const pessoas = await window.GemData.dadosPessoas();
  const form = formularioDocumento("doc-prof", pessoas);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ARQUIVOS DA PROFESSORA</p><h2>Envio de documentos</h2><p>Envie materiais, exercícios ou avisos para uso interno, uma turma ou uma aluna. O destino define automaticamente a visibilidade no acesso das alunas.</p></section><section class="panel">${form.markup}<div id="doc-prof-feedback"></div></section><section class="panel"><h3>Documentos enviados por você</h3><div id="lista-docs-prof" class="lesson-list"><div class="empty">Carregando documentos...</div></div></section>`;
  form.vincular();
  const lista = $("#lista-docs-prof");
  const carregar = async () => {
    try {
      const documentos = await window.GemData.dadosDocumentos();
      const meus = documentos.filter((documento) => documento.professora === state.name);
      lista.innerHTML = meus.length ? meus.map((documento) => `<article class="method-row"><div><strong>${escapeHtml(documento.titulo)}</strong><span>${escapeHtml(documento.disciplina || "—")} · ${documento.aluna ? `Aluna: ${escapeHtml(documento.aluna)}` : documento.turma ? `Turma: ${escapeHtml(documento.turma)}` : "Sem destino específico"}</span></div><div class="person-actions"><button class="secondary-action" type="button" data-doc-prof="${escapeHtml(documento.arquivo_path)}">Abrir</button><button class="secondary-action danger-action" type="button" data-excluir-doc-prof="${escapeHtml(documento.id)}">Excluir</button></div></article>`).join("") : `<div class="empty">Você ainda não enviou documentos.</div>`;
      lista.querySelectorAll("[data-doc-prof]").forEach((botao) => botao.addEventListener("click", async () => { try { window.open(await window.GemData.urlDocumento(botao.dataset.docProf), "_blank", "noopener"); } catch (erro) { alert(erro.message); } }));
      lista.querySelectorAll("[data-excluir-doc-prof]").forEach((botao) => botao.addEventListener("click", async () => { const documento = meus.find((item) => String(item.id) === String(botao.dataset.excluirDocProf)); if (!documento || !confirm(`Excluir o documento “${documento.titulo}”?`)) return; botao.disabled = true; try { await window.GemData.removerDocumento(documento); await carregar(); } catch (erro) { alert(erro.message); botao.disabled = false; } }));
    } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  };
  $("#doc-prof-enviar").addEventListener("click", async () => {
    const feedback = $("#doc-prof-feedback");
    const dados = form.dados();
    if (dados.visivel && !dados.turma && !dados.aluna) { feedback.innerHTML = `<div class="action-error">Escolha a turma ou a aluna que receberá o documento.</div>`; return; }
    try { await window.GemData.enviarDocumento({ ...dados, professora: state.name }); feedback.innerHTML = `<div class="action-ok">Documento enviado.</div>`; await carregar(); }
    catch (erro) { feedback.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  });
  await carregar();
}

async function renderDocumentosAluna(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">MEUS ARQUIVOS</p><h2>Documentos</h2><p>Materiais enviados pela Secretaria e pelas professoras para você ou para a sua turma.</p></section><section class="panel"><div id="docs-aluna-lista" class="lesson-list"><div class="empty">Carregando documentos...</div></div></section>`;
  const lista = $("#docs-aluna-lista");
  try {
    const [documentos, pessoas] = await Promise.all([window.GemData.dadosDocumentos(), window.GemData.dadosPessoas()]);
    const turma = pessoas.alunas.find((aluna) => aluna.nome === state.name)?.turma;
    const disponiveis = documentos.filter((documento) => documento.visivel_alunas && (!documento.aluna || documento.aluna === state.name) && (!documento.turma || documento.turma === turma));
    lista.innerHTML = disponiveis.length ? disponiveis.map((documento) => `<article class="method-row"><div><strong>${escapeHtml(documento.titulo)}</strong><span>${escapeHtml(documento.disciplina || "Material")} · Enviado por ${escapeHtml(documento.professora || "Secretaria")}</span>${documento.observacao ? `<span>${escapeHtml(documento.observacao)}</span>` : ""}</div><button class="secondary-action" type="button" data-doc-aluna="${escapeHtml(documento.arquivo_path)}">Abrir</button></article>`).join("") : `<div class="empty">Nenhum documento disponível para você ainda.</div>`;
    lista.querySelectorAll("[data-doc-aluna]").forEach((botao) => botao.addEventListener("click", async () => { try { window.open(await window.GemData.urlDocumento(botao.dataset.docAluna), "_blank", "noopener"); } catch (erro) { alert(erro.message); } }));
  } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
}

async function renderProvasProfessora(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">AVALIAÇÕES</p><h2>Provas</h2><p>Somente as avaliações que a Secretaria atribuiu a você aparecem aqui. Cada nota continua vinculada à aluna e à disciplina.</p></section><section class="panel"><div id="notas-prof-lista" class="lesson-list"><div class="empty">Carregando avaliações atribuídas...</div></div></section>`;
  const lista = $("#notas-prof-lista");
  const carregar = async () => {
    const { avaliacoes, notas, responsaveis } = await window.GemData.dadosProvas();
    const minhas = responsaveis.filter((item) => item.professora === state.name);
    if (!minhas.length) { lista.innerHTML = `<div class="empty">Nenhuma avaliação foi atribuída a você ainda.</div>`; return; }
    lista.innerHTML = minhas.map((responsavel, indice) => {
      const prova = avaliacoes.find((item) => String(item.id) === String(responsavel.avaliacao_id));
      const nota = notas.find((item) => String(item.avaliacao_id) === String(responsavel.avaliacao_id) && item.aluna === responsavel.aluna && item.disciplina === responsavel.disciplina);
      return `<article class="evaluation-card"><div><strong>${escapeHtml(prova?.titulo || "Avaliação")}</strong><span>${escapeHtml(prova?.data_avaliacao || "Sem data")} · ${escapeHtml(responsavel.disciplina)}</span><p>Aluna: <strong>${escapeHtml(responsavel.aluna)}</strong></p></div><div class="evaluation-grade"><label>Nota (0 a 10)<input data-nota-avaliacao="${indice}" type="number" min="0" max="10" step="0.1" value="${nota?.nota ?? ""}" placeholder="0,0"></label><button data-salvar-nota="${indice}" class="primary-action" type="button">Salvar nota</button></div></article>`;
    }).join("");
    lista.querySelectorAll("[data-salvar-nota]").forEach((botao) => botao.addEventListener("click", async () => {
      const responsavel = minhas[Number(botao.dataset.salvarNota)], campo = lista.querySelector(`[data-nota-avaliacao="${botao.dataset.salvarNota}"]`);
      botao.disabled = true;
      try { await window.GemData.salvarNotaAvaliacao({ avaliacaoId: responsavel.avaliacao_id, aluna: responsavel.aluna, disciplina: responsavel.disciplina, nota: campo.value, professora: state.name }); botao.textContent = "Nota salva ✓"; }
      catch (erro) { alert(erro.message); botao.disabled = false; }
    }));
  };
  try { await carregar(); } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
}

// Mantido temporariamente como referência do painel antigo, que restringia a
// visão à própria professora. O painel ativo abaixo usa o mesmo prontuário
// completo da Secretaria.
async function renderAnaliticoProfessoraLegado(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ACOMPANHAMENTO PEDAGÓGICO</p><h2>Analítico IA da professora</h2><p>Consulte os seus próprios registros por aluna e peça uma sugestão pedagógica baseada somente no que foi lançado no GEM.</p></section><section class="panel"><div class="analytics-filters"><label>Aluna<select id="analitico-prof-aluna"></select></label><button id="atualizar-analitico-prof" class="primary-action" type="button">Atualizar</button></div><div id="analitico-prof-lista"><div class="empty">Carregando seus registros...</div></div></section>`;
  const destino = $("#analitico-prof-lista");
  try {
    const dados = await window.GemData.dadosAnalitico();
    const normalizar = (texto) => String(texto || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
    const meus = dados.historico.filter((item) => normalizar(item.Instrutora) === normalizar(state.name) && String(item.Tipo || "").startsWith("Analise_"));
    const alunas = [...new Set(meus.map((item) => item.Aluna).filter(Boolean))].sort((a, b) => a.localeCompare(b, "pt-BR"));
    const seletor = $("#analitico-prof-aluna");
    if (!alunas.length) { seletor.innerHTML = `<option>Sem registros</option>`; destino.innerHTML = `<div class="empty">Você ainda não tem registros de aula salvos.</div>`; return; }
    seletor.innerHTML = alunas.map((aluna) => `<option value="${escapeHtml(aluna)}">${escapeHtml(aluna)}</option>`).join("");
    const lerDificuldades = (valor) => Array.isArray(valor) ? valor : typeof valor === "string" ? valor.replace(/^\[|\]$/g, "").split(/[,;]/).map((item) => item.trim()) : [];
    const renderizar = () => {
      const aluna = seletor.value;
      const registros = meus.filter((item) => item.Aluna === aluna).sort((a, b) => String(b.Data || "").localeCompare(String(a.Data || "")) || String(b.id || "").localeCompare(String(a.id || "")));
      const dificuldades = registros.flatMap((item) => lerDificuldades(item.Dificuldades)).filter((item) => item && !/não apresentou dificuldade/i.test(item));
      const porDisciplina = [...new Set(registros.map((item) => String(item.Tipo || "").replace(/^Analise_/, "").replace(/^Canto$/, "Solfejo Melódico")))];
      const pendentes = dados.historico.filter((item) => item.Aluna === aluna && String(item.Tipo || "").startsWith("Casa_") && !/resolvido|realizada|sem pendência/i.test(String(item.Status || "")));
      const objetivoAtual = (dados.objetivos || []).find((item) => item.aluna === aluna) || {};
      const painelObjetivo = `<section class="feedback-panel objective-panel"><h4>🎯 Próximos objetivos pedagógicos</h4><p>${objetivoAtual.texto ? escapeHtml(objetivoAtual.texto) : "Nenhum objetivo combinado ainda para esta aluna."}</p>${objetivoAtual.professora ? `<small>Última atualização por: ${escapeHtml(objetivoAtual.professora)}</small>` : ""}</section>`;
      const painelIa = state.externo
        ? `<section class="feedback-panel"><h4>🤖 IA não configurada para este GEM</h4><p>Este GEM usa uma base independente. Para usar sugestões com IA nele, conecte uma integração própria da IA no ambiente deste GEM.</p></section>`
        : `<section class="feedback-panel ai-feedback"><h4>🤖 Sugestão pedagógica com IA</h4><p>A IA recebe apenas o resumo dos registros, dificuldades e lições desta aluna. Ela não recebe fotos, documentos ou senhas.</p><label>Pergunta opcional<textarea id="pergunta-ia-prof" placeholder="Ex.: Qual deve ser o foco da próxima aula?"></textarea></label><button id="gerar-ia-prof" class="primary-action" type="button">Gerar sugestão</button><div id="resposta-ia-prof"></div></section>`;
      destino.innerHTML = `<section class="analytics-summary"><h3>👧 ${escapeHtml(aluna)}</h3><div class="grid"><div class="metric"><strong>${registros.length}</strong><span>Registros seus</span></div><div class="metric"><strong>${porDisciplina.length}</strong><span>Disciplina(s) registrada(s)</span></div><div class="metric"><strong>${[...new Set(dificuldades)].length}</strong><span>Dificuldades observadas</span></div><div class="metric"><strong>${pendentes.length}</strong><span>Lições pendentes</span></div></div><div class="analytics-columns"><section><h4>⚠ Dificuldades recorrentes</h4>${dificuldades.length ? `<ul>${[...new Set(dificuldades)].map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : `<p>Sem dificuldades registradas por você.</p>`}</section><section><h4>📚 Lições de casa</h4>${pendentes.length ? pendentes.map((item) => `<p class="homework-line"><strong>${escapeHtml(casaCategoria(item.Tipo))}:</strong> ${escapeHtml(item.Licao_Casa || "—")}<small>${escapeHtml(item.Status || "Pendente")}</small></p>`).join("") : `<p>Nenhuma lição pendente.</p>`}</section></div><section class="feedback-panel"><h4>📝 Histórico das suas aulas</h4>${registros.map((item) => `<article><strong>${escapeHtml(String(item.Tipo || "").replace(/^Analise_/, ""))} — ${escapeHtml(item.Data || "")}</strong><p>${escapeHtml(item.Licao_Atual || "Sem conteúdo informado")}</p>${item.Observacao ? `<p class="report-note">📝 ${escapeHtml(item.Observacao)}</p>` : ""}</article>`).join("")}</section>${painelObjetivo}${painelIa}</section>`;
      const resumo = `Professora: ${state.name}\nAluna: ${aluna}\nRegistros: ${registros.length}\nDisciplinas: ${porDisciplina.join(", ") || "sem disciplina"}\nDificuldades: ${[...new Set(dificuldades)].join("; ") || "nenhuma registrada"}\nLições pendentes: ${pendentes.map((item) => `${casaCategoria(item.Tipo)} — ${item.Licao_Casa || "sem conteúdo"}`).join("; ") || "nenhuma"}\nÚltimos registros:\n${registros.slice(0, 12).map((item) => `${item.Data || ""} | ${String(item.Tipo || "").replace(/^Analise_/, "")} | ${item.Licao_Atual || ""} | ${item.Observacao || ""}`).join("\n")}`;
      $("#gerar-ia-prof")?.addEventListener("click", async () => {
        const botao = $("#gerar-ia-prof"), resposta = $("#resposta-ia-prof"); botao.disabled = true; botao.textContent = "Analisando...";
        try {
          const retorno = await fetch("/api/analitico-ia", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resumo, pergunta: $("#pergunta-ia-prof").value.trim() }) });
          const corpo = await retorno.json().catch(() => ({}));
          if (!retorno.ok) throw new Error(corpo.error || "Não foi possível gerar a sugestão.");
          resposta.innerHTML = `<article class="ai-answer">${escapeHtml(corpo.texto || "").replace(/\n/g, "<br>")}</article>`;
        } catch (erro) { resposta.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
        finally { botao.disabled = false; botao.textContent = "Gerar sugestão"; }
      });
    };
    seletor.addEventListener("change", renderizar);
    $("#atualizar-analitico-prof").addEventListener("click", renderizar);
    renderizar();
  } catch (erro) { destino.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
}

async function renderAnaliticoProfessora(content) {
  return renderAnalitico(content, {
    somenteLeitura: true,
    titulo: "Analítico pedagógico",
    descricao: "Acompanhe o prontuário completo de cada aluna: aulas de todas as professoras, frequência, lições, estudo em casa, provas e observações da Secretaria."
  });
}

async function renderMensagens(content) {
  const eProfessora = state.role === "Professora", eAluna = state.role === "Aluna", meuId = state.role === "Secretaria" ? "Secretaria" : state.name;
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">COMUNICAÇÃO</p><h2>Mensagens</h2><p>Envie avisos gerais, recados para professoras ou uma mensagem direta.</p></section><section class="panel"><div class="person-tabs"><button class="tab-action active" data-msg-tab="mural">Mural geral</button>${eProfessora ? `<button class="tab-action" data-msg-tab="professoras">Só professoras</button>` : ""}<button class="tab-action" data-msg-tab="direta">Conversa direta</button></div><div id="mensagens-conteudo"><div class="empty">Carregando mensagens...</div></div></section>`;
  const pessoas = await window.GemData.dadosPessoas();
  let mensagens = [];
  const destino = $("#mensagens-conteudo");
  const dataMensagem = (item) => item.created_at ? new Date(item.created_at).toLocaleString("pt-BR") : "";
  const atualizar = async () => { mensagens = await window.GemData.dadosMensagens(); };
  const publicar = async (para, campo, retorno) => { try { await window.GemData.enviarMensagem(meuId, para, $(campo).value); $(campo).value = ""; await atualizar(); retorno(); } catch (erro) { destino.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(erro.message)}</div>`); } };
  const mostrarMural = () => { const itens = mensagens.filter((item) => eAluna ? item.para === "TODOS_ALUNAS" : ["TODOS", "TODOS_ALUNAS"].includes(item.para)); const formulario = eAluna ? `<p class="hint">Avisos gerais enviados pela Secretaria e pelas professoras.</p>` : `<p class="hint">Avisos entre Secretaria e professoras. Marque se as alunas também devem visualizar.</p><label>Novo aviso<textarea id="mensagem-mural" placeholder="Escreva o aviso"></textarea></label><label class="checkbox-line"><input id="mural-alunas" type="checkbox"> Enviar também para as alunas</label><button id="publicar-mural" class="primary-action" type="button">Publicar no mural</button>`; destino.innerHTML = `${formulario}<div class="message-list">${itens.length ? itens.slice().reverse().map((item) => `<article><strong>${escapeHtml(item.de)}</strong><small>${escapeHtml(dataMensagem(item))}${item.para === "TODOS_ALUNAS" && !eAluna ? " · 📚 também para alunas" : ""}</small><p>${escapeHtml(item.texto)}</p></article>`).join("") : `<div class="empty">Nenhum aviso publicado ainda.</div>`}</div>`; $("#publicar-mural")?.addEventListener("click", () => publicar($("#mural-alunas").checked ? "TODOS_ALUNAS" : "TODOS", "#mensagem-mural", mostrarMural)); };
  const mostrarProfessoras = () => { const itens = mensagens.filter((item) => item.para === "PROFESSORAS"); destino.innerHTML = `<p class="hint">Este mural é visível somente para professoras.</p><label>Novo recado<textarea id="mensagem-professoras" placeholder="Escreva o recado"></textarea></label><button id="publicar-professoras" class="primary-action" type="button">Publicar para professoras</button><div class="message-list">${itens.length ? itens.slice().reverse().map((item) => `<article><strong>${escapeHtml(item.de)}</strong><small>${escapeHtml(dataMensagem(item))}</small><p>${escapeHtml(item.texto)}</p></article>`).join("") : `<div class="empty">Nenhum recado publicado ainda.</div>`}</div>`; $("#publicar-professoras").onclick = () => publicar("PROFESSORAS", "#mensagem-professoras", mostrarProfessoras); };
  const mostrarDireta = () => { const opcoes = eAluna ? [{ grupo: "Secretaria", nomes: ["Secretaria"] }, { grupo: "Professoras", nomes: pessoas.professoras.filter((item) => item.ativo !== false).map((item) => item.nome) }] : eProfessora ? [{ grupo: "Secretaria", nomes: ["Secretaria"] }, { grupo: "Professoras", nomes: pessoas.professoras.filter((item) => item.ativo !== false && item.nome !== state.name).map((item) => item.nome) }, { grupo: "Alunas", nomes: pessoas.alunas.filter((item) => item.ativo !== false).map((item) => item.nome) }] : [{ grupo: "Professoras", nomes: pessoas.professoras.filter((item) => item.ativo !== false).map((item) => item.nome) }, { grupo: "Alunas", nomes: pessoas.alunas.filter((item) => item.ativo !== false).map((item) => item.nome) }]; destino.innerHTML = `<label>Contato<select id="mensagem-contato">${opcoes.map((grupo) => `<optgroup label="${escapeHtml(grupo.grupo)}">${grupo.nomes.map((nome) => `<option>${escapeHtml(nome)}</option>`).join("")}</optgroup>`).join("")}</select></label><div id="conversa-direta"></div><label>Mensagem<textarea id="mensagem-direta" placeholder="Escreva sua mensagem"></textarea></label><button id="enviar-direta" class="primary-action" type="button">Enviar mensagem</button>`; const desenhar = () => { const contato = $("#mensagem-contato").value, itens = mensagens.filter((item) => (item.de === meuId && item.para === contato) || (item.de === contato && item.para === meuId)); $("#conversa-direta").innerHTML = `<div class="message-list">${itens.length ? itens.map((item) => `<article class="${item.de === meuId ? "my-message" : ""}"><strong>${item.de === meuId ? "Você" : escapeHtml(item.de)}</strong><small>${escapeHtml(dataMensagem(item))}</small><p>${escapeHtml(item.texto)}</p></article>`).join("") : `<div class="empty">Nenhuma mensagem nesta conversa.</div>`}</div>`; }; $("#mensagem-contato").onchange = desenhar; $("#enviar-direta").onclick = () => publicar($("#mensagem-contato").value, "#mensagem-direta", desenhar); desenhar(); };
  try { await atualizar(); mostrarMural(); } catch (erro) { destino.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  document.querySelectorAll("[data-msg-tab]").forEach((botao) => botao.onclick = () => { document.querySelectorAll("[data-msg-tab]").forEach((item) => item.classList.toggle("active", item === botao)); if (botao.dataset.msgTab === "mural") mostrarMural(); else if (botao.dataset.msgTab === "professoras") mostrarProfessoras(); else mostrarDireta(); });
}

async function renderMinhasLicoes(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">MINHAS LIÇÕES</p><h2>Olá, ${escapeHtml(state.name)}.</h2><p>Seu controle de lições e estudo em casa fica salvo no mesmo histórico usado pela professora e pela Coordenação.</p></section><section id="aluna-indicadores" class="grid"><div class="metric"><strong>—</strong><span>Carregando indicadores</span></div></section><section class="panel"><div class="person-tabs"><button class="tab-action active" data-aluna-aba="licoes">📚 Minhas lições de casa</button><button class="tab-action" data-aluna-aba="historico">🗂️ Histórico</button><button class="tab-action" data-aluna-aba="estudo">✅ Controle de estudo diário</button></div><div id="aluna-conteudo"><div class="empty">Carregando...</div></div></section>`;
  const destino = $("#aluna-conteudo"), indicadores = $("#aluna-indicadores");
  let dadosAluna = { historico: [], feitas: [] }, estudos = [], erroEstudo = "", aba = "licoes", horariosEditando = [];
  const dataIso = (valor) => { const texto = String(valor || ""); if (/^\d{4}-\d{2}-\d{2}/.test(texto)) return texto.slice(0, 10); const [dia, mes, ano] = texto.split("/"); return ano ? `${ano}-${mes}-${dia}` : ""; };
  const hoje = new Date().toISOString().slice(0, 10);
  const eDificuldade = (valor) => { const itens = Array.isArray(valor) ? valor : typeof valor === "string" ? valor.replace(/^\[|\]$/g, "").split(/[,;]+/) : []; return itens.some((item) => String(item || "").trim() && !/não apresentou dificuldade/i.test(String(item))); };
  const disciplinaAnalitica = (tipo) => {
    const texto = String(tipo || "").replace(/^Analise_/, "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
    if (texto === "CANTO" || texto === "SOLFEJO MELODICO") return "Solfejo Melódico";
    if (texto === "PRATICA") return "Prática";
    if (texto === "TEORIA") return "Teoria";
    if (texto === "SOLFEJO") return "Solfejo";
    return "";
  };
  const classificacao = (disciplina) => { const inicio = new Date(); inicio.setDate(inicio.getDate() - 30); const limite = inicio.toISOString().slice(0, 10); const registros = dadosAluna.historico.filter((item) => dataIso(item.Data) >= limite && disciplinaAnalitica(item.Tipo) === disciplina); if (!registros.length) return "🥉 Sem registros"; const percentual = Math.round(registros.filter((item) => !eDificuldade(item.Dificuldades)).length / registros.length * 100); return percentual >= 80 ? "🥇 Ouro" : percentual >= 50 ? "🥈 Prata" : "🥉 Bronze"; };
  const desenharIndicadores = () => {
    const chamadas = dadosAluna.historico.filter((item) => item.Tipo === "Chamada"), presentes = chamadas.filter((item) => !["Ausente", "Justificada"].includes(item.Status)).length, faltas = chamadas.filter((item) => item.Status === "Ausente").length, justificadas = chamadas.filter((item) => item.Status === "Justificada").length;
    const frequencia = chamadas.length ? Math.round((presentes + justificadas * .5) / chamadas.length * 100) : 0;
    indicadores.innerHTML = `<div class="metric"><strong>${frequencia}%</strong><span>Frequência ponderada</span></div><div class="metric"><strong>${faltas}</strong><span>Ausência(s)</span></div><div class="metric"><strong>${justificadas}</strong><span>Justificada(s)</span></div><div class="metric"><strong>${classificacao("Prática")}</strong><span>Prática — últimos 30 dias</span></div><div class="metric"><strong>${classificacao("Teoria")}</strong><span>Teoria — últimos 30 dias</span></div><div class="metric"><strong>${classificacao("Solfejo")}</strong><span>Solfejo — últimos 30 dias</span></div>`;
  };
  const mostrarLicoes = () => {
    const idsFeitos = new Set(dadosAluna.feitas.map((item) => String(item.historico_id)));
    const casas = dadosAluna.historico.filter((item) => String(item.Tipo || "").startsWith("Casa_"));
    const maisRecente = (itens) => itens.reduce((atual, item) => !atual || dataIso(item.Data) > dataIso(atual.Data) || (dataIso(item.Data) === dataIso(atual.Data) && Number(item.id || 0) > Number(atual.id || 0)) ? item : atual, null);
    // Método é sempre a lição do último sábado: se a professora lançar uma
    // nova, a anterior sai da lista mesmo que tenha ficado pendente. MSA e
    // Solfejo Melódico seguem a mesma regra. Apostila mantém pendências
    // separadas porque a Secretaria ainda precisa acompanhá-las.
    const ultimaDataPratica = maisRecente(casas.filter((item) => String(item.Tipo || "").startsWith("Casa_Metodo_")))?.Data;
    const ultimaMsa = maisRecente(casas.filter((item) => item.Tipo === "Casa_MSA"));
    const ultimoCanto = maisRecente(casas.filter((item) => item.Tipo === "Casa_Canto"));
    const materialDaLicao = (tipo) => {
      if (["Casa_Apostila", "Casa_Apostila_Prof"].includes(tipo)) return "Apostila";
      if (String(tipo || "").startsWith("Casa_Metodo_")) return String(tipo).replace(/^Casa_Metodo_/, "");
      if (tipo === "Casa_MSA") return "MSA";
      if (tipo === "Casa_Canto") return "Solfejo Melódico";
      if (String(tipo || "").includes("Apostila")) return "Apostila de Teoria";
      return "Folha avulsa de Teoria";
    };
    const licoes = casas.filter((item) => {
      if (eResolvida(item.Status)) return false;
      const tipo = String(item.Tipo || "");
      if (tipo.startsWith("Casa_Metodo_")) return item.Data === ultimaDataPratica;
      if (tipo === "Casa_MSA") return String(item.id) === String(ultimaMsa?.id);
      if (tipo === "Casa_Canto") return String(item.id) === String(ultimoCanto?.id);
      return true;
    });
    destino.innerHTML = `<div class="section-title"><div><h2>Lições de casa</h2><p>Em Método, MSA e Solfejo Melódico aparece sempre a orientação mais recente. A Apostila permanece até ser resolvida.</p></div></div>${licoes.length ? `<div class="lesson-list">${licoes.map((licao) => { const feito = idsFeitos.has(String(licao.id)); return `<article class="lesson-card"><h3>${escapeHtml(casaCategoria(licao.Tipo))}</h3><p><strong>Material:</strong> ${escapeHtml(materialDaLicao(licao.Tipo))}</p><p><strong>Lição:</strong> ${escapeHtml(licao.Licao_Casa || "—")}</p>${licao.Observacao ? `<p class="report-note">📝 ${escapeHtml(String(licao.Observacao).replace(/^Sec:\s*/i, ""))}</p>` : ""}<span class="lesson-meta">Lançada em ${escapeHtml(licao.Data || "—")}</span><br><button class="lesson-action ${feito ? "done" : ""}" data-licao="${escapeHtml(licao.id)}" data-feito="${feito}">${feito ? "✓ Feito — desfazer" : "✓ Marcar como feito"}</button></article>`; }).join("")}</div>` : `<div class="empty">✅ Nenhuma lição pendente agora. As lições resolvidas continuam no seu histórico.</div>`}`;
    destino.querySelectorAll("button[data-licao]").forEach((botao) => botao.addEventListener("click", async () => { botao.disabled = true; try { await window.GemData.marcarLicaoFeita(state.name, botao.dataset.licao, botao.dataset.feito !== "true"); dadosAluna = await window.GemData.dadosAluna(state.name); mostrarLicoes(); } catch (erro) { botao.disabled = false; alert(erro.message); } }));
  };
  const mostrarHistorico = () => {
    const licoes = dadosAluna.historico.filter((item) => String(item.Tipo || "").startsWith("Casa_"))
      .sort((a, b) => dataIso(b.Data).localeCompare(dataIso(a.Data)) || Number(b.id || 0) - Number(a.id || 0));
    destino.innerHTML = `<div class="section-title"><div><h2>Histórico de lições</h2><p>As lições resolvidas ficam registradas aqui com as orientações da professora ou da Secretaria.</p></div></div>${licoes.length ? `<div class="lesson-list">${licoes.map((licao) => `<article class="lesson-card ${eResolvida(licao.Status) ? "resolved-lesson" : ""}"><h3>${escapeHtml(casaCategoria(licao.Tipo))}</h3><p><strong>Lição:</strong> ${escapeHtml(licao.Licao_Casa || "—")}</p><span class="lesson-meta">Lançada em ${escapeHtml(licao.Data || "—")} · ${escapeHtml(licao.Status || "Pendente")}</span>${licao.Observacao ? `<p class="report-note">📝 ${escapeHtml(String(licao.Observacao).replace(/^Sec:\s*/i, ""))}</p>` : ""}</article>`).join("")}</div>` : `<div class="empty">Nenhuma lição registrada ainda.</div>`}`;
  };
  const mostrarEstudo = () => {
    if (erroEstudo) { destino.innerHTML = `<div class="action-error">${escapeHtml(erroEstudo)}</div>`; return; }
    const dataAtual = $("#estudo-dia")?.value || hoje, dataAtualBr = `${dataAtual.slice(8, 10)}/${dataAtual.slice(5, 7)}/${dataAtual.slice(0, 4)}`;
    const historico = estudos.slice().sort((a, b) => dataIso(b.data).localeCompare(dataIso(a.data))).slice(0, 30);
    destino.innerHTML = `<section class="study-panel"><h2>✅ Registrar meu estudo do dia</h2><p>Informe os horários que você estudou. Você pode salvar mais de um horário no mesmo dia.</p><label>Dia<input id="estudo-dia" type="date" value="${dataAtual}"></label><div class="study-add"><label>Início<input id="estudo-inicio" placeholder="Ex.: 14:00"></label><label>Término<input id="estudo-fim" placeholder="Ex.: 15:30"></label><button id="adicionar-horario-estudo" class="secondary-action" type="button">＋ Adicionar</button></div><div id="horarios-estudo" class="study-times"></div><button id="salvar-estudo" class="primary-action" type="button">Salvar estudo do dia</button><div id="estudo-feedback"></div></section><section class="study-history"><h3>📅 Meu histórico de estudo — últimos 30 registros</h3>${historico.length ? historico.map((item) => `<article><strong>${escapeHtml(item.data || "—")}</strong><span>${(item.horarios || []).length ? `😊 ${escapeHtml((item.horarios || []).join(" · "))}` : "😢 Não registrou horário"}</span></article>`).join("") : `<p class="hint">Nenhum estudo registrado ainda.</p>`}</section>`;
    const desenharHorarios = () => { $("#horarios-estudo").innerHTML = horariosEditando.length ? horariosEditando.map((horario, indice) => `<span>🕐 ${escapeHtml(horario)} <button type="button" data-remover-horario="${indice}" aria-label="Remover horário">×</button></span>`).join("") : `<p class="hint">Nenhum horário adicionado neste dia.</p>`; destino.querySelectorAll("[data-remover-horario]").forEach((botao) => botao.onclick = () => { horariosEditando.splice(Number(botao.dataset.removerHorario), 1); desenharHorarios(); }); };
    const carregarDia = () => { const dia = $("#estudo-dia").value, chave = `${dia.slice(8, 10)}/${dia.slice(5, 7)}/${dia.slice(0, 4)}`; horariosEditando = [...(estudos.find((item) => item.data === chave)?.horarios || [])]; desenharHorarios(); };
    $("#estudo-dia").onchange = carregarDia;
    $("#adicionar-horario-estudo").onclick = () => { const inicio = $("#estudo-inicio").value.trim(), fim = $("#estudo-fim").value.trim(); if (!inicio || !fim) { $("#estudo-feedback").innerHTML = `<div class="action-error">Informe início e término.</div>`; return; } horariosEditando.push(`${inicio} às ${fim}`); $("#estudo-inicio").value = ""; $("#estudo-fim").value = ""; $("#estudo-feedback").innerHTML = ""; desenharHorarios(); };
    $("#salvar-estudo").onclick = async () => { const botao = $("#salvar-estudo"); botao.disabled = true; try { await window.GemData.salvarEstudoDiario({ aluna: state.name, dataIso: $("#estudo-dia").value, horarios: horariosEditando }); estudos = await window.GemData.dadosEstudoAluna(state.name); $("#estudo-feedback").innerHTML = `<div class="action-ok">Estudo registrado.</div>`; } catch (erro) { $("#estudo-feedback").innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; botao.disabled = false; } };
    const existente = estudos.find((item) => item.data === dataAtualBr); horariosEditando = [...(existente?.horarios || [])]; desenharHorarios();
  };
  try { dadosAluna = await window.GemData.dadosAluna(state.name); try { estudos = await window.GemData.dadosEstudoAluna(state.name); } catch (erro) { erroEstudo = erro.message; } desenharIndicadores(); mostrarLicoes(); }
  catch (erro) { destino.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  document.querySelectorAll("[data-aluna-aba]").forEach((botao) => botao.addEventListener("click", () => { aba = botao.dataset.alunaAba; document.querySelectorAll("[data-aluna-aba]").forEach((item) => item.classList.toggle("active", item === botao)); if (aba === "estudo") mostrarEstudo(); else if (aba === "historico") mostrarHistorico(); else mostrarLicoes(); }));
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
      lista.innerHTML = `<div class="attendance-list">${alunas.map((aluna) => { const chamada = porAluna[aluna] || { Status: "Presente", Observacao: "" }; const foto = fotos[aluna] ? `<button class="photo-zoom attendance-photo" type="button" data-foto-zoom="${escapeHtml(fotos[aluna])}" data-foto-titulo="${escapeHtml(aluna)}" title="Ampliar foto de ${escapeHtml(aluna)}"><img src="${escapeHtml(fotos[aluna])}" alt="Foto de ${escapeHtml(aluna)}"></button>` : `<span>${escapeHtml(aluna.slice(0, 1))}</span>`; return `<article class="attendance-row"><div class="attendance-student">${foto}<strong>${escapeHtml(aluna)}</strong></div><div class="attendance-checks"><label><input type="checkbox" data-presente="${escapeHtml(aluna)}" ${chamada.Status === "Presente" ? "checked" : ""}> Presente</label><label><input type="checkbox" data-ausente="${escapeHtml(aluna)}" ${chamada.Status === "Ausente" ? "checked" : ""}> Ausente</label><label><input type="checkbox" data-justificada="${escapeHtml(aluna)}" ${chamada.Status === "Justificada" ? "checked" : ""}> Falta justificada</label></div><input class="${chamada.Status === "Justificada" ? "" : "hidden"}" data-motivo="${escapeHtml(aluna)}" value="${escapeHtml(chamada.Observacao || "")}" placeholder="Motivo da falta justificada"></article>`; }).join("")}</div><button id="salvar-chamada" class="primary-action full-action" type="button">Salvar chamada</button><div id="chamada-retorno"></div>`;
      lista.querySelectorAll("input[data-presente],input[data-ausente],input[data-justificada]").forEach((campo) => campo.addEventListener("change", (evento) => {
        const linha = evento.target.closest(".attendance-row");
        const opcoes = [...linha.querySelectorAll("input[data-presente],input[data-ausente],input[data-justificada]")];
        // São checkboxes para a tela ficar mais direta, mas os três estados
        // continuam mutuamente exclusivos para preservar a regra da chamada.
        if (evento.target.checked) opcoes.forEach((opcao) => { if (opcao !== evento.target) opcao.checked = false; });
        else if (!opcoes.some((opcao) => opcao.checked)) linha.querySelector("[data-presente]").checked = true;
        const aluna = evento.target.dataset.presente || evento.target.dataset.ausente || evento.target.dataset.justificada;
        linha.querySelector(`[data-motivo="${CSS.escape(aluna)}"]`).classList.toggle("hidden", !linha.querySelector("[data-justificada]").checked);
      }));
      $("#salvar-chamada").addEventListener("click", async () => { const botao = $("#salvar-chamada"); botao.disabled = true; try { await window.GemData.salvarChamada($("#chamada-data").value, alunas.map((aluna) => ({ aluna, status: lista.querySelector(`[data-justificada="${CSS.escape(aluna)}"]`).checked ? "Justificada" : lista.querySelector(`[data-ausente="${CSS.escape(aluna)}"]`).checked ? "Ausente" : "Presente", observacao: lista.querySelector(`[data-justificada="${CSS.escape(aluna)}"]`).checked ? lista.querySelector(`[data-motivo="${CSS.escape(aluna)}"]`).value : "" }))); $("#chamada-retorno").innerHTML = `<div class="action-ok">Chamada salva.</div>`; } catch (erro) { $("#chamada-retorno").innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; botao.disabled = false; } });
    } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  };
  $("#carregar-chamada").addEventListener("click", carregar);
  await carregar();
}

async function conferirRegistrosPendentesCoordenacao(dataIso, destino) {
  destino.innerHTML = `<div class="empty">Conferindo escala e registros...</div>`;
  try {
    const dados = await window.GemData.dadosVisaoGeral(dataIso);
    if (!dados.escala.length) { destino.innerHTML = `<div class="empty">Não há rodízio salvo para esta data.</div>`; return; }
    const normalizarDisciplina = (tipo) => String(tipo || "").replace(/^Analise_/, "").replace(/^Canto$/, "Solfejo Melódico").trim();
    const disciplinasDaCelula = (valor, detalhe = {}) => {
      const componentes = Array.isArray(detalhe.componentes) ? detalhe.componentes.filter(Boolean) : detalhe.tipo ? [detalhe.tipo] : [];
      if (componentes.length) return componentes.map((item) => item === "Canto" ? "Solfejo Melódico" : item);
      const texto = String(valor || "").toUpperCase();
      if (texto.includes("SALA 8")) return ["Teoria"];
      if (texto.includes("SALA 9")) return ["Solfejo Melódico"];
      return texto.includes("SALA") ? ["Prática", "Solfejo"] : [];
    };
    const chamadaPorAluna = Object.fromEntries(dados.registros.filter((item) => item.Tipo === "Chamada").map((item) => [item.Aluna, item]));
    const faltantes = [], vistos = new Set();
    for (const linha of dados.escala) {
      const aluna = linha.Aluna;
      if (!aluna || ["Ausente", "Justificada"].includes(chamadaPorAluna[aluna]?.Status)) continue;
      const registrosAluna = dados.registros.filter((item) => item.Aluna === aluna);
      const disciplinasRegistradas = new Set(registrosAluna.map((item) => normalizarDisciplina(item.Tipo)));
      const detalhes = linha._detalhes || {};
      for (const [horario, valor] of Object.entries(linha)) {
        if (["Aluna", "_detalhes"].includes(horario) || !String(valor || "").includes("|")) continue;
        const detalhe = detalhes[horario] || {};
        const professoras = detalhe.professoras_componentes || {};
        const professoraPadrao = String(valor).split("|").slice(1).join("|").trim();
        for (const disciplina of disciplinasDaCelula(valor, detalhe)) {
          const professora = String(professoras[disciplina] || professoraPadrao).trim();
          const chave = `${aluna}|${disciplina}|${professora}`;
          if (vistos.has(chave) || disciplinasRegistradas.has(disciplina)) continue;
          vistos.add(chave);
          faltantes.push({ professora: professora || "Professora não identificada", aluna, disciplina });
        }
      }
    }
    if (!faltantes.length) { destino.innerHTML = `<div class="action-ok">✅ Todos os registros das alunas presentes foram preenchidos neste sábado.</div>`; return; }
    const porProfessora = new Map();
    faltantes.sort((a, b) => a.professora.localeCompare(b.professora, "pt-BR") || a.aluna.localeCompare(b.aluna, "pt-BR")).forEach((item) => (porProfessora.get(item.professora) || porProfessora.set(item.professora, []).get(item.professora)).push(item));
    destino.innerHTML = `<div class="grid"><div class="metric"><strong>${faltantes.length}</strong><span>Registros pendentes</span></div><div class="metric"><strong>${porProfessora.size}</strong><span>Professoras com pendência</span></div></div><div class="lesson-list">${[...porProfessora.entries()].map(([professora, itens]) => `<article class="student-report"><h3>👩‍🏫 ${escapeHtml(professora)}</h3>${itens.map((item) => `<div class="report-record"><strong>${escapeHtml(item.aluna)}</strong><p>🎼 ${escapeHtml(item.disciplina)}</p></div>`).join("")}</article>`).join("")}</div>`;
  } catch (erro) { destino.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
}

async function renderFolgas(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  const eCoordenadora = state.role === "Professora" && state.coordenadora;
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">LOGÍSTICA DO SÁBADO</p><h2>${eCoordenadora ? "Rodízio de folgas" : "Folgas das professoras"}</h2><p>${eCoordenadora ? "Organize as folgas e confira os registros das aulas deste sábado." : "As folgas salvas aqui entram automaticamente na geração do rodízio daquela data. Você pode reabrir e corrigir uma informação antes de gerar."}</p></section>${eCoordenadora ? `<section class="panel"><div class="person-tabs"><button class="tab-action active" data-coord-aba="folgas">📅 Folgas</button><button class="tab-action" data-coord-aba="pendencias">🔎 Registros pendentes</button></div></section>` : ""}<div id="coord-aba-folgas"><section class="panel"><div class="agenda-date"><div><label for="folga-data">Sábado</label><input id="folga-data" type="date" value="${hoje}"></div><button id="carregar-folga" class="primary-action" type="button">Abrir folgas</button></div><div id="folga-formulario"><div class="empty">Carregando professoras...</div></div></section><section class="panel"><h3>Folgas já cadastradas</h3><div id="folgas-lista" class="lesson-list"><div class="empty">Carregando...</div></div></section></div>${eCoordenadora ? `<section id="coord-aba-pendencias" class="panel hidden"><div class="agenda-date"><div><label for="pendencias-data">Sábado para conferir</label><input id="pendencias-data" type="date" value="${hoje}"></div><button id="verificar-pendencias" class="primary-action" type="button">Verificar registros</button></div><div id="pendencias-coordenacao"><p class="hint">Escolha o sábado e confira quem ainda não lançou o registro pedagógico.</p></div></section>` : ""}`;
  const formulario = $("#folga-formulario"), lista = $("#folgas-lista");
  let professoras = [];
  const carregarLista = async () => {
    const folgas = await window.GemData.dadosFolgas();
    lista.innerHTML = folgas.length ? folgas.map((folga) => `<article class="method-row"><div><strong>${escapeHtml(folga.data)}</strong><span>${escapeHtml((folga.professoras || []).join(", ") || "Nenhuma professora de folga")}</span>${folga.observacao ? `<span>${escapeHtml(folga.observacao)}</span>` : ""}</div><button class="secondary-action" type="button" data-abrir-folga="${escapeHtml(folga.data)}">Editar</button></article>`).join("") : `<div class="empty">Nenhuma folga cadastrada ainda.</div>`;
    lista.querySelectorAll("[data-abrir-folga]").forEach((botao) => botao.addEventListener("click", () => { $("#folga-data").value = botao.dataset.abrirFolga; abrir(); window.scrollTo({ top: 0, behavior: "smooth" }); }));
    return folgas;
  };
  const abrir = async () => {
    formulario.innerHTML = `<div class="empty">Carregando folga deste sábado...</div>`;
    try {
      const [folgas, pessoas] = await Promise.all([window.GemData.dadosFolgas(), window.GemData.dadosPessoas()]);
      professoras = pessoas.professoras.filter((item) => item.ativo !== false).map((item) => item.nome);
      const salvo = folgas.find((item) => item.data === $("#folga-data").value) || {};
      const selecionadas = new Set(salvo.professoras || []);
      formulario.innerHTML = `<div class="folga-checks">${professoras.map((professora) => `<label class="checkbox-line"><input type="checkbox" data-professora-folga value="${escapeHtml(professora)}" ${selecionadas.has(professora) ? "checked" : ""}> ${escapeHtml(professora)}</label>`).join("")}</div><label>Observação opcional<textarea id="folga-observacao" placeholder="Ex.: Missão Fraternal, troca combinada">${escapeHtml(salvo.observacao || "")}</textarea></label><button id="salvar-folga" class="primary-action" type="button">Salvar folgas deste sábado</button><div id="folga-feedback"></div>`;
      $("#salvar-folga").addEventListener("click", async () => { const feedback = $("#folga-feedback"); try { const selecionadasAgora = [...formulario.querySelectorAll("[data-professora-folga]:checked")].map((campo) => campo.value); await window.GemData.salvarFolgas({ data: $("#folga-data").value, coordenadora: state.name, professoras: selecionadasAgora, observacao: $("#folga-observacao").value }); feedback.innerHTML = `<div class="action-ok">Folgas salvas. O gerador do rodízio considerará esta lista.</div>`; await carregarLista(); } catch (erro) { feedback.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; } });
    } catch (erro) { formulario.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  };
  $("#carregar-folga").addEventListener("click", abrir);
  try { await Promise.all([abrir(), carregarLista()]); } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  if (eCoordenadora) {
    const pendencias = $("#pendencias-coordenacao");
    const verificar = () => conferirRegistrosPendentesCoordenacao($("#pendencias-data").value, pendencias);
    $("#verificar-pendencias").addEventListener("click", verificar);
    document.querySelectorAll("[data-coord-aba]").forEach((botao) => botao.addEventListener("click", () => {
      const pendenciasAtivas = botao.dataset.coordAba === "pendencias";
      document.querySelectorAll("[data-coord-aba]").forEach((item) => item.classList.toggle("active", item === botao));
      $("#coord-aba-folgas").classList.toggle("hidden", pendenciasAtivas);
      $("#coord-aba-pendencias").classList.toggle("hidden", !pendenciasAtivas);
      if (pendenciasAtivas && !pendencias.dataset.carregadas) { pendencias.dataset.carregadas = "1"; verificar(); }
    }));
  }
}

async function renderBoletim(content) {
  content.innerHTML = `<section class="boletim-cover"><p>BOLETIM MUSICAL</p><h2>🎼 Meu Boletim</h2><span>${escapeHtml(state.name)} · suas notas, frequência e avaliações</span></section><section id="boletim-resumo" class="boletim-summary"><div class="metric"><strong>—</strong><span>Carregando indicadores</span></div></section><section class="panel"><div id="boletim-lista" class="lesson-list"><div class="empty">Carregando boletim...</div></div></section>`;
  const lista = $("#boletim-lista");
  try {
    const { avaliacoes, notas, historico } = await window.GemData.boletimAluna(state.name);
    const chamadasPorData = new Map();
    historico.filter((item) => item.Tipo === "Chamada").forEach((item) => chamadasPorData.set(item.Data, item));
    const chamadas = [...chamadasPorData.values()];
    const presentes = chamadas.filter((item) => item.Status === "Presente").length;
    const faltas = chamadas.filter((item) => item.Status === "Ausente").length;
    const justificadas = chamadas.filter((item) => item.Status === "Justificada").length;
    const frequencia = chamadas.length ? Math.round((presentes + justificadas * .5) / chamadas.length * 100) : 0;
    const valores = notas.map((nota) => Number(nota.nota)).filter(Number.isFinite);
    const media = valores.length ? (valores.reduce((total, nota) => total + nota, 0) / valores.length).toFixed(1).replace(".", ",") : "Aguardando";
    $("#boletim-resumo").innerHTML = `<div class="metric"><strong>${frequencia}%</strong><span>📅 Frequência ponderada</span></div><div class="metric"><strong>${media}</strong><span>🎵 Média das notas</span></div><div class="metric"><strong>${faltas}</strong><span>❌ Ausência(s)</span></div><div class="metric"><strong>${justificadas}</strong><span>🟡 Falta(s) justificada(s)</span></div>`;
    if (!avaliacoes.length) { lista.innerHTML = `<div class="empty">Nenhuma avaliação cadastrada ainda.</div>`; return; }
    lista.innerHTML = avaliacoes.map((avaliacao) => {
      const notasDaProva = notas.filter((nota) => String(nota.avaliacao_id) === String(avaliacao.id));
      const disciplinas = [["🎹", "Prática"], ["📚", "Teoria"], ["🔊", "Solfejo"]];
      return `<article class="boletim-card"><h3>🎶 ${escapeHtml(avaliacao.titulo || "Avaliação")}</h3><p>📅 ${escapeHtml(avaliacao.data_avaliacao || "Data ainda não informada")}</p><div class="boletim-grades">${disciplinas.map(([icone, disciplina]) => { const valor = notasDaProva.find((item) => item.disciplina === disciplina)?.nota; return `<div><span>${icone} ${disciplina}</span><strong>${valor === undefined || valor === null || valor === "" ? "Aguardando" : escapeHtml(Number(valor).toFixed(1).replace(".", ","))}</strong></div>`; }).join("")}</div></article>`;
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
  return `<div class="mural-scroll"><section class="mural-print" id="mural-rodizio"><header><h2>Rodízio Geral das aulas - ${escapeHtml(state.gem || "GEM Vila Verde")}</h2><p>Data: ${escapeHtml(data)}</p></header><div class="mural-columns">${colunas}</div></section></div>`;
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
      if (!modelo && !base.escala.length) {
        area.innerHTML = `<div class="action-error">Não há modelo logístico programado para esta data. Cadastre ou programe o modelo em Logística, sem alterar os rodízios anteriores.</div>`;
        return;
      }
      const modeloExibido = modelo || { nome: "Modelo legado — escala histórica", configuracao: {} };
      const config = modeloExibido.configuracao || {};
      const preparacao = modelo ? window.RodizioEngine.prepararModelo(modelo, base.turmas) : { coletivas: {}, turmas: [], blocos: [] };
      // A ordem cadastrada no modelo pode variar conforme quem criou cada
      // turma. Na tela, sempre exibimos a sequência humana: Turma 1, 2, 3…
      // Isso vale para Teoria, Solfejo Melódico e a prévia de rotação, sem
      // alterar a configuração nem a regra usada pelo motor.
      preparacao.turmas = [...preparacao.turmas].sort((a, b) => String(a).localeCompare(String(b), "pt-BR", { numeric: true, sensitivity: "base" }));
      const atividades = Object.keys(preparacao.coletivas);
      const todasAlunas = Object.values(base.turmas).flat();
      const normalizarProf = (nome) => String(nome || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
      const folgasAtivas = Array.isArray(base.folga?.professoras) ? base.folga.professoras : [];
      const nomesEmFolga = new Set(folgasAtivas.map(normalizarProf));
      const professorasDisponiveis = base.professoras.filter((prof) => !nomesEmFolga.has(normalizarProf(prof)));
      const opcoesProf = professorasDisponiveis.map((prof) => `<option value="${escapeHtml(prof)}">${escapeHtml(prof)}</option>`).join("");
      const fixasSalvas = Object.entries(base.professorasFixas).map(([alunaNormalizada, professora]) => ({ aluna: todasAlunas.find((nome) => nome.trim().toLowerCase() === alunaNormalizada) || "", professora })).filter((item) => item.aluna);
      const coletivas = atividades.map((atividade) => `<section class="collective-box"><h3>${escapeHtml(atividade)} <small>(${escapeHtml(preparacao.coletivas[atividade] || "Sala a definir")})</small></h3>${preparacao.turmas.map((turma) => { const habilitadas = (config.professoras_habilitadas?.[atividade] || (atividade === "Solfejo Melódico" ? config.professoras_habilitadas?.Canto : null) || base.professoras).filter((prof) => !nomesEmFolga.has(normalizarProf(prof))); return `<label>Prof. ${escapeHtml(atividade)} — ${escapeHtml(turma)}<select data-coletiva="${escapeHtml(atividade)}" data-turma="${escapeHtml(turma)}" ${habilitadas.length ? "" : "disabled"}>${habilitadas.length ? habilitadas.map((prof) => `<option value="${escapeHtml(prof)}">${escapeHtml(prof)}</option>`).join("") : "<option>Nenhuma professora disponível</option>"}</select></label>`; }).join("")}</section>`).join("");
      const escalaSalva = base.escala.length;
      const rodiziosSalvos = (base.escalasAnteriores || []).filter((item) => Array.isArray(item.escala) && item.escala.length).sort((a, b) => { const [da, ma, aa] = String(a.id).split("/"); const [db, mb, ab] = String(b.id).split("/"); return `${ab}${mb}${db}`.localeCompare(`${aa}${ma}${da}`); });
      const historico = rodiziosSalvos.length ? `<div class="rodizio-history"><label>Ver rodízio de outra data<select id="rodizios-anteriores"><option value="">Escolha uma data</option>${rodiziosSalvos.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.id)}</option>`).join("")}</select></label></div>` : "";
      const avisoFolga = folgasAtivas.length ? `<div class="action-ok">👑 Folga(s) deste sábado: <strong>${escapeHtml(folgasAtivas.join(" · "))}</strong>. Elas foram removidas das opções do rodízio.</div>` : "";
      area.innerHTML = `${historico}${escalaSalva ? rodizioSalvoMarkup(base) : `<section class="generator-panel"><h2>Gerar novo rodízio</h2><p>As alunas ativas entram no novo rodízio. Alunas desativadas continuam nas escalas e registros dos sábados já realizados.</p>${avisoFolga}<div class="generator-grid"><div><h3>Professoras das aulas por turma</h3>${coletivas}</div><div><h3>Rotação das turmas</h3><label class="checkbox-line"><input id="rotacao-manual" type="checkbox"> Definir manualmente a rotação das turmas?</label><div id="rotacao-opcoes" class="hidden"><label><input type="radio" name="criterio-rotacao" value="teoria" checked> Turma que começa em Teoria</label><label><input type="radio" name="criterio-rotacao" value="individual"> Turma no último bloco de Prática + Solfejo</label><select id="turma-rotacao">${preparacao.turmas.map((turma) => `<option value="${escapeHtml(turma)}">${escapeHtml(turma)}</option>`).join("")}</select><div id="previa-rotacao"></div></div><h3>Saída antecipada</h3><p class="hint">Selecione somente quem sairá antes. Depois escolha o último bloco em que cada uma ainda pode atender.</p><select id="professoras-saida" multiple size="5">${opcoesProf}</select><div id="saidas-detalhes"></div></div></div>${config.usar_professoras_fixas ? `<section class="fixas-box"><h3>Professoras fixas neste modelo</h3><p>Escolha somente as alunas que terão professora fixa. Você pode acrescentar quantas precisar.</p><div class="fixed-list" id="fixed-list"></div><button id="adicionar-fixa" class="secondary-action" type="button">＋ Adicionar aluna fixa</button><button id="salvar-fixas" class="secondary-action" type="button">Salvar professoras fixas</button><label class="checkbox-line"><input id="usar-fixas" type="checkbox" checked> Usar professoras fixas neste rodízio?</label></section>` : ""}<button id="gerar-rodizio" class="primary-action wide-action" type="button">Gerar rodízio do modelo</button><div id="gerar-feedback"></div></section>`}`;
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
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">COORDENAÇÃO</p><h2>Resumo do GEM</h2><p>Indicadores gerais da escola, frequência, estrutura e alunas em destaque.</p></section><section class="panel"><div class="agenda-date"><div><label for="visao-data">Referência para o resumo</label><input id="visao-data" type="date" value="${hoje}"></div><button id="carregar-visao" class="primary-action" type="button">Atualizar resumo</button></div><div id="visao-conteudo"><div class="empty">Carregando dados...</div></div></section><section class="panel branding-panel"><h2>Marca e perfil da Coordenação</h2><p>A logo aparece no login e na barra lateral. A foto substitui a letra do perfil da Coordenação neste aplicativo.</p><div class="branding-grid"><label>Nova logo do GEM<input id="logo-gem" type="file" accept="image/png,image/jpeg,image/webp"></label><button id="salvar-logo" class="secondary-action" type="button">Salvar logo</button><label>Nome exibido<input id="nome-coordenacao" value="${escapeHtml(state.name)}"></label><label>Foto da Coordenação<input id="foto-coordenacao" type="file" accept="image/png,image/jpeg,image/webp"></label><button id="salvar-perfil" class="secondary-action" type="button">Salvar perfil</button></div><div id="marca-feedback"></div></section>`;
  const carregar = async () => {
    const destino = $("#visao-conteudo"); destino.innerHTML = `<div class="empty">Carregando resumo...</div>`;
    try {
      const dataReferencia = $("#visao-data").value;
      const [dados, pessoas, baseRodizio, analitico] = await Promise.all([
        window.GemData.dadosVisaoGeral(dataReferencia),
        window.GemData.dadosPessoas(),
        window.GemData.dadosRodizio(dataReferencia).catch(() => ({ modelos: [] })),
        window.GemData.dadosAnalitico().catch(() => ({ historico: [], estudos: [] }))
      ]);
      const chamadas = Object.fromEntries(dados.registros.filter((item) => item.Tipo === "Chamada").map((item) => [item.Aluna, item]));
      const estudos = Object.fromEntries((dados.estudos || []).map((item) => [item.aluna, item.horarios || []]));
      const disciplinasDaEscala = (linha) => {
        const detalhes = Object.values(linha?._detalhes || {}), disciplinas = new Set();
        detalhes.forEach((detalhe) => (detalhe.componentes || [detalhe.tipo]).filter(Boolean).forEach((tipo) => disciplinas.add(tipo === "Canto" ? "Solfejo Melódico" : tipo)));
        if (disciplinas.size) return [...disciplinas];
        Object.values(linha || {}).forEach((valor) => { const texto = String(valor || "").toUpperCase(); if (texto.includes("SALA 8")) disciplinas.add("Teoria"); else if (texto.includes("SALA 9")) disciplinas.add("Solfejo Melódico"); else if (texto.includes("SALA")) { disciplinas.add("Prática"); disciplinas.add("Solfejo"); } });
        return [...disciplinas];
      };
      const normalizarDisciplina = (tipo) => String(tipo || "").replace(/^Analise_/, "").replace("Canto", "Solfejo Melódico");
      const normalizarNome = (nome) => String(nome || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
      // A escala salva é a fonte de verdade de quem estava designada para a
      // aula. Isso mantém a conferência do relatório diário do app.py e evita
      // considerar como regular um registro lançado pela professora errada.
      const professorasPrevistas = (linha) => {
        const previstas = {};
        Object.entries(linha?._detalhes || {}).forEach(([hora, detalhe]) => {
          const componentes = (detalhe.componentes || [detalhe.tipo]).filter(Boolean);
          const valor = String(linha?.[hora] || "");
          const textoProfessoras = valor.includes("|") ? valor.split("|").slice(1).join("|").trim() : "";
          componentes.forEach((componente) => {
            const disciplina = normalizarDisciplina(componente);
            let professora = detalhe.professoras_componentes?.[componente] || "";
            if (!professora && componentes.length > 1) {
              const encontrada = textoProfessoras.match(new RegExp(`${String(componente).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*:\\s*([^·]+)`, "i"));
              professora = encontrada?.[1]?.trim() || textoProfessoras;
            }
            if (!professora) professora = textoProfessoras;
            if (professora) (previstas[disciplina] ||= new Set()).add(professora);
          });
        });
        return previstas;
      };
      const cards = dados.alunas.map((aluna) => {
        const linhaEscala = dados.escala.find((linha) => linha.Aluna === aluna) || {}, chamada = chamadas[aluna], status = chamada?.Status || "Sem chamada", registros = dados.registros.filter((item) => item.Aluna === aluna && String(item.Tipo || "").startsWith("Analise_")), licoes = dados.registros.filter((item) => item.Aluna === aluna && String(item.Tipo || "").startsWith("Casa_"));
        const previstas = disciplinasDaEscala(linhaEscala), registradas = new Set(registros.map((item) => normalizarDisciplina(item.Tipo))), faltantes = previstas.filter((disciplina) => !registradas.has(disciplina));
        const escalaProfessoras = professorasPrevistas(linhaEscala);
        const estudo = estudos[aluna];
        const registrosMarkup = registros.length ? registros.map((registro) => { const dificuldades = Array.isArray(registro.Dificuldades) ? registro.Dificuldades.filter((item) => item && !/não apresentou dificuldade/i.test(item)) : []; const disciplina = normalizarDisciplina(registro.Tipo), esperadas = escalaProfessoras[disciplina] || new Set(), divergente = registro.Instrutora && esperadas.size && ![...esperadas].some((professora) => normalizarNome(professora) === normalizarNome(registro.Instrutora)); return `<article class="daily-record"><strong>${escapeHtml(disciplina)}${registro.Instrutora ? ` · ${escapeHtml(registro.Instrutora)}` : ""}</strong><span>${escapeHtml(registro.Licao_Atual || "Conteúdo não informado")}</span>${divergente ? `<small class="record-divergence">⚠️ Rodízio: prevista ${escapeHtml([...esperadas].join(" / "))}</small>` : ""}${dificuldades.length ? `<small>⚠️ ${escapeHtml(dificuldades.join(" · "))}</small>` : `<small>✓ Sem dificuldades registradas</small>`}${registro.Observacao ? `<small>📝 ${escapeHtml(registro.Observacao)}</small>` : ""}</article>`; }).join("") : `<p class="hint">Nenhum registro pedagógico lançado ainda.</p>`;
        const licoesMarkup = licoes.filter((licao) => !eResolvida(licao.Status) || licao.Observacao).map((licao) => `<span>📚 ${escapeHtml(casaCategoria(licao.Tipo))}: ${escapeHtml(licao.Licao_Casa || "—")} <small>${escapeHtml(licao.Status || "Pendente")}</small></span>`).join("");
        return `<article class="daily-student"><header><div><h3>${escapeHtml(aluna)}</h3><p>${chamada ? `${escapeHtml(status)}${chamada.Observacao ? ` · ${escapeHtml(chamada.Observacao)}` : ""}` : "Chamada ainda não lançada"}</p></div><span class="daily-badge ${status === "Presente" ? "ok" : status === "Sem chamada" ? "wait" : "alert"}">${status === "Presente" ? "✓ Presente" : escapeHtml(status)}</span></header><div class="daily-study">${estudo === undefined ? "📚 Sem registro de estudo em casa" : estudo.length ? `📚 😊 Estudou: ${escapeHtml(estudo.join(" · "))}` : "📚 😢 Não estudou"}</div><div class="daily-planned"><strong>Aulas previstas:</strong> ${previstas.length ? escapeHtml(previstas.join(" · ")) : "escala sem detalhes"}</div><div class="daily-records">${registrosMarkup}</div>${faltantes.length && !["Ausente", "Justificada"].includes(status) ? `<div class="daily-warning">⚠️ Falta registro: ${escapeHtml(faltantes.join(" · "))}</div>` : ""}${licoesMarkup ? `<div class="daily-homework"><strong>Para a próxima aula</strong>${licoesMarkup}</div>` : ""}</article>`;
      }).join("");
      const presentes = dados.alunas.filter((aluna) => chamadas[aluna]?.Status === "Presente").length, ausentes = dados.alunas.filter((aluna) => ["Ausente", "Justificada"].includes(chamadas[aluna]?.Status)).length, semRegistro = dados.alunas.filter((aluna) => { if (["Ausente", "Justificada"].includes(chamadas[aluna]?.Status)) return false; const linha = dados.escala.find((item) => item.Aluna === aluna) || {}, esperadas = disciplinasDaEscala(linha), feitas = new Set(dados.registros.filter((item) => item.Aluna === aluna && String(item.Tipo || "").startsWith("Analise_")).map((item) => normalizarDisciplina(item.Tipo))); return esperadas.some((disciplina) => !feitas.has(disciplina)); }).length;
      // A conferência é por professora, disciplina e aluna. Não basta existir
      // qualquer análise: ela precisa ter sido lançada pela professora prevista
      // naquela aula. Ausências não geram pendência pedagógica.
      const pendenciasPorProfessora = new Map();
      dados.alunas.forEach((aluna) => {
        if (["Ausente", "Justificada"].includes(chamadas[aluna]?.Status)) return;
        const linha = dados.escala.find((item) => item.Aluna === aluna) || {};
        const previstas = professorasPrevistas(linha);
        const registrosDaAluna = dados.registros.filter((item) => item.Aluna === aluna && String(item.Tipo || "").startsWith("Analise_"));
        Object.entries(previstas).forEach(([disciplina, professoras]) => {
          professoras.forEach((professora) => {
            const temRegistro = registrosDaAluna.some((item) => normalizarDisciplina(item.Tipo) === disciplina && normalizarNome(item.Instrutora) === normalizarNome(professora));
            if (temRegistro) return;
            if (!pendenciasPorProfessora.has(professora)) pendenciasPorProfessora.set(professora, new Set());
            pendenciasPorProfessora.get(professora).add(`${aluna} · ${disciplina}`);
          });
        });
      });
      const professorasPendentesRegistro = [...pendenciasPorProfessora.entries()].sort(([nomeA], [nomeB]) => nomeA.localeCompare(nomeB, "pt-BR"));
      const conferenciaRegistros = !(dados.escala || []).length
        ? `<section class="record-check"><div><h3>🔎 Conferência de Registros</h3><p>Não há rodízio salvo nesta data para conferir os registros pedagógicos.</p></div></section>`
        : `<section class="record-check"><div><h3>🔎 Conferência de Registros</h3><p>Verifique rapidamente quem ainda não lançou o registro pedagógico deste dia.</p></div>${professorasPendentesRegistro.length ? `<div class="record-check-alert"><strong>${professorasPendentesRegistro.length} professora${professorasPendentesRegistro.length === 1 ? "" : "s"} com registro${professorasPendentesRegistro.length === 1 ? "" : "s"} pendente${professorasPendentesRegistro.length === 1 ? "" : "s"}</strong><div class="record-check-list">${professorasPendentesRegistro.map(([professora, pendencias]) => { const itens = [...pendencias]; const resumo = itens.slice(0, 4).join(" · "); const resto = itens.length - 4; return `<article><strong>${escapeHtml(professora)}</strong><small>${itens.length} registro${itens.length === 1 ? "" : "s"} pendente${itens.length === 1 ? "" : "s"}: ${escapeHtml(resumo)}${resto > 0 ? ` · +${resto}` : ""}</small></article>`; }).join("")}</div></div>` : `<div class="action-ok">✓ Todas as professoras previstas já lançaram seus registros pedagógicos.</div>`}</section>`;
      const ativas = (pessoas.alunas || []).filter((aluna) => aluna.ativo !== false);
      const professorasAtivas = (pessoas.professoras || []).filter((professora) => professora.ativo !== false);
      const modelo = window.GemData.modeloParaData(baseRodizio.modelos || [], dataReferencia);
      const configuracao = modelo?.configuracao || {};
      const salasModelo = (configuracao.salas || []).filter((sala) => sala.Ativa !== false && sala.ativa !== false);
      const salasEscala = new Set((dados.escala || []).flatMap((linha) => Object.values(linha || {}).filter((valor) => /SALA\s*\d+/i.test(String(valor))).map((valor) => (String(valor).match(/SALA\s*\d+/i) || [""])[0].toUpperCase()).filter(Boolean)));
      const quantidadeSalas = salasModelo.length || salasEscala.size;
      const disciplinasModelo = (configuracao.atividades || []).map((atividade) => atividade.Atividade || atividade.atividade || atividade.tipo).filter(Boolean);
      const disciplinas = [...new Set((disciplinasModelo.length ? disciplinasModelo : dados.escala.flatMap(disciplinasDaEscala)).map((disciplina) => disciplina === "Canto" ? "Solfejo Melódico" : disciplina))];
      const historicoGeral = analitico.historico || [];
      const chamadasGerais = historicoGeral.filter((item) => item.Tipo === "Chamada" && ["Presente", "Ausente", "Justificada"].includes(item.Status));
      const frequencia = chamadasGerais.length ? Math.round((chamadasGerais.filter((item) => item.Status === "Presente").length / chamadasGerais.length) * 100) : null;
      const dataEmMs = (valor) => { const texto = String(valor || ""); if (/^\d{4}-\d{2}-\d{2}/.test(texto)) return new Date(`${texto.slice(0, 10)}T12:00:00`).getTime(); const [dia, mes, ano] = texto.split("/"); return ano ? new Date(`${ano}-${mes}-${dia}T12:00:00`).getTime() : 0; };
      const referenciaMs = new Date(`${dataReferencia}T12:00:00`).getTime();
      const destaque = (dias) => {
        const inicio = referenciaMs - ((dias - 1) * 86400000), pontos = new Map(ativas.map((aluna) => [aluna.nome, 0]));
        historicoGeral.forEach((item) => {
          if (dataEmMs(item.Data) < inicio || dataEmMs(item.Data) > referenciaMs || !pontos.has(item.Aluna)) return;
          if (item.Tipo === "Chamada") pontos.set(item.Aluna, pontos.get(item.Aluna) + (item.Status === "Presente" ? 3 : -2));
          if (String(item.Tipo || "").startsWith("Analise_")) { const dificuldades = Array.isArray(item.Dificuldades) ? item.Dificuldades.filter((dificuldade) => dificuldade && !/não apresentou dificuldade/i.test(dificuldade)) : []; pontos.set(item.Aluna, pontos.get(item.Aluna) + (dificuldades.length ? 1 : 2)); }
        });
        (analitico.estudos || []).forEach((estudo) => { const dataEstudo = dataEmMs(estudo.data); if (dataEstudo >= inicio && dataEstudo <= referenciaMs && pontos.has(estudo.aluna) && (estudo.horarios || []).length) pontos.set(estudo.aluna, pontos.get(estudo.aluna) + 2); });
        const ordenado = [...pontos.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "pt-BR"));
        return ordenado[0]?.[1] > 0 ? ordenado[0] : null;
      };
      const destaqueSemana = destaque(7), destaqueMes = destaque(30);
      const cardDestaque = (titulo, item) => `<article class="gem-highlight"><span>${titulo}</span><strong>${item ? escapeHtml(item[0]) : "Ainda sem dados"}</strong><small>${item ? `${item[1]} pontos por presença, estudo e registros` : "Aparecerá quando houver registros no período."}</small></article>`;
      // O ranking de estudo conta dias distintos com pelo menos um horário
      // marcado. Assim uma aluna não sobe artificialmente no quadro por
      // selecionar manhã, tarde e noite no mesmo dia.
      const inicioEstudo = referenciaMs - (29 * 86400000);
      const estudoPorAluna = new Map(ativas.map((aluna) => [aluna.nome, 0]));
      (analitico.estudos || []).forEach((estudo) => {
        const quando = dataEmMs(estudo.data);
        if (quando >= inicioEstudo && quando <= referenciaMs && estudoPorAluna.has(estudo.aluna) && (estudo.horarios || []).length) {
          estudoPorAluna.set(estudo.aluna, estudoPorAluna.get(estudo.aluna) + 1);
        }
      });
      const rankingEstudo = [...estudoPorAluna.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0], "pt-BR"));
      const maiorEstudo = rankingEstudo[0] || null;
      const menorEstudo = rankingEstudo.length ? rankingEstudo[rankingEstudo.length - 1] : null;
      const cardEstudo = (titulo, item, vazio) => `<article class="gem-highlight"><span>${titulo}</span><strong>${item ? escapeHtml(item[0]) : "Ainda sem dados"}</strong><small>${item ? `${item[1]} dia(s) de estudo nos últimos 30 dias` : vazio}</small></article>`;
      destino.innerHTML = `<div class="grid gem-summary"><div class="metric"><strong>${ativas.length}</strong><span>Alunas ativas</span></div><div class="metric"><strong>${frequencia === null ? "—" : `${frequencia}%`}</strong><span>Frequência geral</span></div><div class="metric"><strong>${quantidadeSalas || "—"}</strong><span>Salas ativas</span></div><div class="metric"><strong>${professorasAtivas.length}</strong><span>Professoras ativas</span></div><div class="metric"><strong>${disciplinas.length}</strong><span>Disciplinas oferecidas</span></div></div><section class="gem-summary-details"><div><h3>🎼 Disciplinas do GEM</h3><p>${disciplinas.length ? escapeHtml(disciplinas.join(" · ")) : "Defina as disciplinas no modelo de rodízio."}</p></div><div><h3>📅 Referência</h3><p>${dados.alunas.length ? `${dados.alunas.length} aluna(s) no rodízio de hoje · ${presentes} presente(s)` : "Sem rodízio salvo nesta data."}</p></div></section>${conferenciaRegistros}<section class="gem-highlights"><div><h3>🌟 Destaques de desempenho</h3><p>Calculados pelo quadro de desempenho: presença, estudo diário e registros pedagógicos.</p></div><div class="gem-highlight-grid">${cardDestaque("Destaque da semana", destaqueSemana)}${cardDestaque("Destaque do mês", destaqueMes)}</div></section><section class="gem-highlights"><div><h3>📚 Estudo em casa</h3><p>Ranking de dias estudados nos 30 dias anteriores à data de referência.</p></div><div class="gem-highlight-grid">${cardEstudo("Quem mais estudou", maiorEstudo, "Aparecerá quando houver estudo registrado.")}${cardEstudo("Quem menos estudou", menorEstudo, "Aparecerá quando houver alunas ativas.")}</div></section>`;
    } catch (error) { destino.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#carregar-visao").addEventListener("click", carregar); await carregar();
  $("#salvar-logo").addEventListener("click", async () => { const feedback = $("#marca-feedback"); try { const identidade = await window.GemData.enviarLogoGem($("#logo-gem").files[0]); aplicarLogo(identidade.logoUrl); feedback.innerHTML = `<p class="action-ok">Logo atualizada. Ela aparecerá também no próximo acesso.</p>`; } catch (error) { feedback.innerHTML = `<p class="action-error">${escapeHtml(error.message)}</p>`; } });
  $("#salvar-perfil").addEventListener("click", async () => { const feedback = $("#marca-feedback"); try { const perfil = await window.GemData.salvarPerfilSecretaria({ nome: $("#nome-coordenacao").value, arquivo: $("#foto-coordenacao").files[0] }); state.name = perfil.nome_exibicao || state.name; $("#profile-name").textContent = state.name; aplicarAvatar(perfil.fotoUrl, state.name); feedback.innerHTML = `<p class="action-ok">Perfil da Coordenação atualizado.</p>`; } catch (error) { feedback.innerHTML = `<p class="action-error">${escapeHtml(error.message)}</p>`; } });
}

async function renderPessoas(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">CADASTROS</p><h2>Turmas e pessoas</h2><p>Alunas desativadas deixam de entrar apenas em rodízios novos; os rodízios, chamadas e registros anteriores continuam visíveis.</p></section><section class="panel"><div class="person-tabs"><button class="tab-action active" data-pessoas="aluna">Alunas e turmas</button><button class="tab-action" data-pessoas="professora">Professoras</button><button class="tab-action" data-pessoas="secretaria">Secretarias</button></div><div id="pessoas-conteudo"><div class="empty">Carregando pessoas...</div></div></section>`;
  const [dados, fotos] = await Promise.all([window.GemData.dadosPessoas(), window.GemData.fotosPessoas().catch(() => ({ aluna: {}, professora: {} }))]); const destino = $("#pessoas-conteudo");
  let coordenacoes = [], erroCoordenacoes = "";
  try { coordenacoes = await window.GemData.dadosCoordenacoesProfessoras(); }
  catch (erro) { erroCoordenacoes = erro.message || "Não foi possível carregar as coordenações."; }
  const hoje = new Date().toISOString().slice(0, 10);
  const terminoPadrao = new Date(`${hoje}T12:00:00`); terminoPadrao.setDate(terminoPadrao.getDate() + 90);
  const dataCoordenacao = (data) => data ? new Date(`${data}T12:00:00`).toLocaleDateString("pt-BR") : "—";
  const mostrar = (tipo) => {
    const lista = tipo === "aluna" ? dados.alunas : tipo === "professora" ? dados.professoras : dados.secretarias;
    const titulo = tipo === "aluna" ? "Adicionar aluna" : tipo === "professora" ? "Adicionar professora" : "Adicionar secretaria";
    destino.innerHTML = `<div class="person-add"><h3>${titulo}</h3><div class="form-grid"><input id="pessoa-nome" placeholder="Nome completo">${tipo === "aluna" ? '<input id="pessoa-turma" placeholder="Turma">' : ""}${tipo !== "secretaria" ? '<input id="pessoa-login" placeholder="Login"><input id="pessoa-senha" type="password" autocomplete="new-password" placeholder="Senha inicial (mínimo 6 caracteres)"><label>Foto de perfil (opcional)<input id="pessoa-foto" type="file" accept="image/jpeg,image/png,image/webp"></label>' : ""}<button id="adicionar-pessoa" class="primary-action" type="button">Adicionar</button></div><div id="pessoa-feedback" aria-live="polite"></div></div><div class="person-list">${lista.length ? lista.map((pessoa, indice) => { const foto = fotos[tipo]?.[pessoa.nome]; const retrato = tipo !== "secretaria" ? (foto ? `<button class="person-photo photo-zoom" type="button" data-foto-zoom="${escapeHtml(foto)}" data-foto-titulo="${escapeHtml(pessoa.nome)}" title="Ampliar foto de ${escapeHtml(pessoa.nome)}"><img src="${escapeHtml(foto)}" alt="Foto de ${escapeHtml(pessoa.nome)}"></button>` : `<span class="person-photo initials">${escapeHtml(pessoa.nome.slice(0, 1))}</span>`) : ""; return `<article class="person-row person-card"><div class="person-identity">${retrato}<div><strong>${escapeHtml(pessoa.nome)}</strong><span>${tipo === "aluna" ? escapeHtml(pessoa.turma || "Sem turma") : pessoa.login ? `Login: ${escapeHtml(pessoa.login)}` : ""}</span></div></div><span class="badge ${pessoa.ativo === false ? "inactive" : ""}">${pessoa.ativo === false ? "Desativada" : "Ativa"}</span><div class="person-actions"><button data-editar="${indice}" class="secondary-action" type="button">Editar</button><button data-toggle="${indice}" class="secondary-action" type="button">${pessoa.ativo === false ? "Reativar" : "Desativar"}</button></div><div class="person-editor hidden" data-editor="${indice}"><label>Nome<input data-campo="nome" value="${escapeHtml(pessoa.nome)}"></label>${tipo === "aluna" ? `<label>Turma<input data-campo="turma" value="${escapeHtml(pessoa.turma || "")}"></label>` : ""}${tipo !== "secretaria" ? `<label>Login<input data-campo="login" value="${escapeHtml(pessoa.login || "")}"></label><label>Nova senha <small>(deixe vazia para manter a atual)</small><input data-campo="senha" type="password" autocomplete="new-password" placeholder="Nova senha"></label><label>Trocar foto <small>(JPG, PNG ou WEBP, até 5 MB)</small><input data-campo="foto" type="file" accept="image/jpeg,image/png,image/webp"></label>` : ""}<button data-salvar="${indice}" class="primary-action" type="button">Salvar alterações</button></div></article>`; }).join("") : "<div class=\"empty\">Nenhum cadastro ainda.</div>"}</div>`;
    if (tipo === "professora") {
      const professorasAtivas = lista.filter((pessoa) => pessoa.ativo !== false);
      const coordenacaoAtual = coordenacoes.filter((item) => item.inicio <= hoje && item.fim >= hoje);
      const historico = coordenacoes.length ? coordenacoes.map((item) => `<article><strong>${escapeHtml(item.professora)}</strong><span>${escapeHtml(item.periodo || "Coordenação")} · ${escapeHtml(dataCoordenacao(item.inicio))} a ${escapeHtml(dataCoordenacao(item.fim))}</span></article>`).join("") : `<p class="hint">Nenhuma professora coordenadora definida ainda.</p>`;
      destino.querySelector(".person-add").insertAdjacentHTML("afterend", `<section class="coordinator-panel"><div><h3>👑 Professora coordenadora</h3><p>Somente a professora definida para o período verá a página <strong>Folgas</strong> no login dela. Ao substituir a responsável, o período anterior é encerrado, sem apagar o histórico.</p></div>${erroCoordenacoes ? `<div class="action-error">${escapeHtml(erroCoordenacoes)}</div>` : `<div class="coordinator-form"><label>Professora<select id="coordenadora-professora"><option value="">Escolha a professora</option>${professorasAtivas.map((pessoa) => `<option value="${escapeHtml(pessoa.nome)}" ${coordenacaoAtual[0]?.professora === pessoa.nome ? "selected" : ""}>${escapeHtml(pessoa.nome)}</option>`).join("")}</select></label><label>Tipo do período<select id="coordenadora-periodo"><option>Bimestre</option><option>Semestre</option><option>Plantão / da vez</option></select></label><label>Começa em<input id="coordenadora-inicio" type="date" value="${hoje}"></label><label>Termina em<input id="coordenadora-fim" type="date" value="${terminoPadrao.toISOString().slice(0, 10)}"></label><button id="salvar-coordenadora" class="primary-action" type="button">Definir coordenadora</button></div><div id="coordenadora-feedback"></div><div class="coordinator-history">${historico}</div>`}</section>`);
      $("#salvar-coordenadora")?.addEventListener("click", async () => { const botao = $("#salvar-coordenadora"), feedback = $("#coordenadora-feedback"); botao.disabled = true; try { await window.GemData.definirCoordenadoraProfessora({ professora: $("#coordenadora-professora").value, inicio: $("#coordenadora-inicio").value, fim: $("#coordenadora-fim").value, periodo: $("#coordenadora-periodo").value }); feedback.innerHTML = `<div class="action-ok">Professora coordenadora definida. No próximo login dela, a página Folgas será exibida.</div>`; coordenacoes = await window.GemData.dadosCoordenacoesProfessoras(); } catch (erro) { feedback.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; botao.disabled = false; } });
    }
    $("#adicionar-pessoa").addEventListener("click", async () => { const nome = $("#pessoa-nome").value.trim(), loginInicial = tipo === "secretaria" ? "" : $("#pessoa-login").value.trim().toLowerCase(), senhaInicial = tipo === "secretaria" ? "" : $("#pessoa-senha").value, feedback = $("#pessoa-feedback"); if (!nome) { feedback.innerHTML = `<div class="action-error">Informe o nome completo.</div>`; return; } if (tipo !== "secretaria" && (!loginInicial || String(senhaInicial).length < 6)) { feedback.innerHTML = `<div class="action-error">Informe login e uma senha inicial com pelo menos 6 caracteres.</div>`; return; } const novo = tipo === "aluna" ? { nome, turma: $("#pessoa-turma").value.trim() || "Sem turma", ativo: true, login: loginInicial, senha: senhaInicial } : tipo === "professora" ? { nome, login: loginInicial, senha: senhaInicial, ativo: true } : { nome, ativo: true }; const botao = $("#adicionar-pessoa"); botao.disabled = true; feedback.innerHTML = ""; try { if (tipo !== "secretaria") { const foto = await window.GemData.enviarFotoPessoa(tipo, $("#pessoa-foto").files[0]); if (foto) novo.foto_path = foto; } await window.GemData.salvarPessoa(tipo, novo); await renderPessoas(content); } catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message || "Não foi possível cadastrar.")}</div>`; botao.disabled = false; } });
    destino.querySelectorAll("[data-editar]").forEach((botao) => botao.addEventListener("click", () => destino.querySelector(`[data-editor="${botao.dataset.editar}"]`).classList.toggle("hidden")));
    destino.querySelectorAll("[data-toggle]").forEach((botao) => botao.addEventListener("click", async () => { const pessoa = lista[Number(botao.dataset.toggle)]; try { await window.GemData.salvarPessoa(tipo, { ativo: pessoa.ativo === false }, pessoa.id, pessoa.nome); pessoa.ativo = pessoa.ativo === false; mostrar(tipo); } catch (error) { alert(error.message); } }));
    destino.querySelectorAll("[data-salvar]").forEach((botao) => botao.addEventListener("click", async () => { const pessoa = lista[Number(botao.dataset.salvar)], editor = destino.querySelector(`[data-editor="${botao.dataset.salvar}"]`); const atualizado = { nome: editor.querySelector('[data-campo="nome"]').value.trim() }; if (tipo === "aluna") atualizado.turma = editor.querySelector('[data-campo="turma"]').value.trim() || "Sem turma"; if (tipo !== "secretaria") { atualizado.login = editor.querySelector('[data-campo="login"]').value.trim().toLowerCase(); const senha = editor.querySelector('[data-campo="senha"]').value; if (senha) atualizado.senha = senha; } if (!atualizado.nome) { alert("Informe o nome."); return; } botao.disabled = true; try { if (tipo !== "secretaria") { const foto = await window.GemData.enviarFotoPessoa(tipo, editor.querySelector('[data-campo="foto"]').files[0]); if (foto) atualizado.foto_path = foto; } await window.GemData.salvarPessoa(tipo, atualizado, pessoa.id, pessoa.nome); await renderPessoas(content); } catch (error) { editor.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); botao.disabled = false; } }));
  };
  document.querySelectorAll("[data-pessoas]").forEach((botao) => botao.addEventListener("click", () => { document.querySelectorAll("[data-pessoas]").forEach((item) => item.classList.toggle("active", item === botao)); mostrar(botao.dataset.pessoas); }));
  mostrar("aluna");
}

async function renderDocumentos(content) {
  const pessoas = await window.GemData.dadosPessoas();
  const form = formularioDocumento("doc", pessoas);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ARQUIVOS</p><h2>Documentos</h2><p>Envie materiais para uso interno, uma turma ou uma aluna. A visibilidade é definida pelo destino, como no sistema Streamlit.</p></section><section class="panel">${form.markup}<div id="doc-feedback"></div></section><section class="panel"><h2>Documentos enviados</h2><div id="lista-docs"><div class="empty">Carregando documentos...</div></div></section>`;
  form.vincular();
  const carregar = async () => { const lista = $("#lista-docs"); try { const docs = await window.GemData.dadosDocumentos(); lista.innerHTML = docs.length ? docs.map((doc) => `<article class="person-row"><div><strong>${escapeHtml(doc.titulo)}</strong><span>${escapeHtml(doc.disciplina || "—")} · ${doc.aluna ? `Aluna: ${escapeHtml(doc.aluna)}` : doc.turma ? `Turma: ${escapeHtml(doc.turma)}` : "Uso interno"}</span></div><span class="badge">${doc.visivel_alunas ? "Disponível" : "Interno"}</span><div class="person-actions"><button data-documento="${escapeHtml(doc.arquivo_path)}" class="secondary-action" type="button">Abrir</button><button data-excluir-documento="${escapeHtml(doc.id)}" class="secondary-action danger-action" type="button">Excluir</button></div></article>`).join("") : `<div class="empty">Nenhum documento enviado ainda.</div>`; lista.querySelectorAll("[data-documento]").forEach((botao) => botao.addEventListener("click", async () => { try { window.open(await window.GemData.urlDocumento(botao.dataset.documento), "_blank", "noopener"); } catch (error) { alert(error.message); } })); lista.querySelectorAll("[data-excluir-documento]").forEach((botao) => botao.addEventListener("click", async () => { const documento = docs.find((item) => String(item.id) === String(botao.dataset.excluirDocumento)); if (!documento || !confirm(`Excluir o documento “${documento.titulo}”?`)) return; botao.disabled = true; try { await window.GemData.removerDocumento(documento); await carregar(); } catch (erro) { alert(erro.message); botao.disabled = false; } })); } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } };
  $("#doc-enviar").addEventListener("click", async () => { const feedback = $("#doc-feedback"), dados = form.dados(); if (dados.visivel && !dados.turma && !dados.aluna) { feedback.innerHTML = `<div class="action-error">Escolha a turma ou a aluna que receberá o documento.</div>`; return; } try { await window.GemData.enviarDocumento(dados); feedback.innerHTML = `<div class="action-ok">Documento enviado.</div>`; await carregar(); } catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } }); await carregar();
}

async function renderProvas(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">AVALIAÇÕES</p><h2>Provas</h2><p>Crie a avaliação e indique quem corrige cada aluna em cada disciplina, exatamente como no controle do GEM.</p></section><section class="panel"><div class="form-grid"><input id="prova-titulo" placeholder="Nome da prova ou avaliação"><input id="prova-data" type="date" value="${new Date().toISOString().slice(0, 10)}"><button id="criar-prova" class="primary-action" type="button">Criar avaliação</button></div><div id="prova-feedback"></div></section><section class="panel"><div id="lista-provas"><div class="empty">Carregando avaliações...</div></div></section><section id="responsaveis-avaliacao"></section>`;
  const lista = $("#lista-provas"), areaResponsaveis = $("#responsaveis-avaliacao");
  let base = null;
  const abrirResponsaveis = (avaliacaoId) => {
    const avaliacao = base.avaliacoes.find((item) => String(item.id) === String(avaliacaoId));
    const alunas = base.pessoas.alunas.filter((item) => item.ativo !== false), professoras = base.pessoas.professoras.filter((item) => item.ativo !== false).map((item) => item.nome), disciplinas = ["Prática", "Teoria", "Solfejo", "Solfejo Melódico"];
    if (!professoras.length) { areaResponsaveis.innerHTML = `<div class="action-error">Cadastre professoras antes de definir responsáveis.</div>`; return; }
    const responsavelAtual = (aluna, disciplina) => base.responsaveis.find((item) => String(item.avaliacao_id) === String(avaliacaoId) && item.aluna === aluna && item.disciplina === disciplina)?.professora || professoras[0];
    areaResponsaveis.innerHTML = `<section class="panel"><div class="section-title"><div><h2>👩‍🏫 Professoras responsáveis</h2><p>${escapeHtml(avaliacao?.titulo || "Avaliação")} · defina uma responsável por disciplina e aluna.</p></div><button id="fechar-responsaveis" class="secondary-action" type="button">Fechar</button></div><div class="responsibility-list">${alunas.map((aluna, indice) => `<article><h3>${escapeHtml(aluna.nome)}</h3><div class="responsibility-grid">${disciplinas.map((disciplina) => `<label>${disciplina}<select data-responsavel-aluna="${indice}" data-responsavel-disciplina="${escapeHtml(disciplina)}">${professoras.map((professora) => `<option ${responsavelAtual(aluna.nome, disciplina) === professora ? "selected" : ""}>${escapeHtml(professora)}</option>`).join("")}</select></label>`).join("")}</div></article>`).join("")}</div><button id="salvar-responsaveis" class="primary-action" type="button">Salvar professoras responsáveis</button><div id="responsaveis-feedback"></div></section>`;
    $("#fechar-responsaveis").onclick = () => { areaResponsaveis.innerHTML = ""; };
    $("#salvar-responsaveis").onclick = async () => { const botao = $("#salvar-responsaveis"), linhas = [...areaResponsaveis.querySelectorAll("[data-responsavel-aluna]")].map((campo) => ({ aluna: alunas[Number(campo.dataset.responsavelAluna)].nome, disciplina: campo.dataset.responsavelDisciplina, professora: campo.value })); botao.disabled = true; try { await window.GemData.salvarResponsaveisAvaliacao(avaliacaoId, linhas); $("#responsaveis-feedback").innerHTML = `<div class="action-ok">Professoras responsáveis salvas.</div>`; await carregar(); } catch (error) { $("#responsaveis-feedback").innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; botao.disabled = false; } };
  };
  const carregar = async () => {
    try {
      const [provas, pessoas] = await Promise.all([window.GemData.dadosProvas(), window.GemData.dadosPessoas()]); base = { ...provas, pessoas };
      lista.innerHTML = base.avaliacoes.length ? base.avaliacoes.map((avaliacao) => `<article class="person-row"><div><strong>${escapeHtml(avaliacao.titulo)}</strong><span>${escapeHtml(avaliacao.data_avaliacao || "Sem data")} · ${base.notas.filter((nota) => String(nota.avaliacao_id) === String(avaliacao.id)).length} nota(s) lançada(s) · ${base.responsaveis.filter((item) => String(item.avaliacao_id) === String(avaliacao.id)).length} atribuição(ões)</span></div><div class="person-actions"><button data-configurar-prova="${escapeHtml(avaliacao.id)}" class="secondary-action" type="button">Responsáveis</button><button data-excluir-prova="${escapeHtml(avaliacao.id)}" class="secondary-action danger-action" type="button">Excluir</button></div></article>`).join("") : `<div class="empty">Nenhuma avaliação cadastrada ainda.</div>`;
      lista.querySelectorAll("[data-configurar-prova]").forEach((botao) => botao.onclick = () => abrirResponsaveis(botao.dataset.configurarProva));
      lista.querySelectorAll("[data-excluir-prova]").forEach((botao) => botao.onclick = async () => { if (!confirm("Excluir esta avaliação e as notas vinculadas?")) return; try { await window.GemData.removerProva(botao.dataset.excluirProva); areaResponsaveis.innerHTML = ""; await carregar(); } catch (error) { alert(error.message); } });
    } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#criar-prova").addEventListener("click", async () => { const feedback = $("#prova-feedback"), titulo = $("#prova-titulo").value.trim(); if (!titulo) { feedback.innerHTML = `<div class="action-error">Informe o nome da avaliação.</div>`; return; } try { const criada = await window.GemData.criarProva(titulo, $("#prova-data").value); feedback.innerHTML = `<div class="action-ok">Avaliação criada. Agora defina as professoras responsáveis.</div>`; $("#prova-titulo").value = ""; await carregar(); abrirResponsaveis(criada.id); } catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } }); await carregar();
}

async function renderLogistica(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">LOGÍSTICA</p><h2>Modelos de aulas</h2><p>Edite o modelo para as próximas escalas. Rodízios já salvos continuam preservados como retrato do sábado em que foram gerados.</p></section><section class="panel"><div class="section-title"><h2>Modelos cadastrados</h2><button id="novo-modelo" class="primary-action" type="button">Novo modelo</button></div><div id="lista-modelos"><div class="empty">Carregando modelos...</div></div></section><div id="editor-modelo"></div>`;
  const lista = $("#lista-modelos");
  let modelos, pessoas;
  try {
    [modelos, pessoas] = await Promise.all([window.GemData.dadosLogistica(), window.GemData.dadosPessoas()]);
  } catch (error) {
    lista.innerHTML = `<div class="action-error">${escapeHtml(error.message || "Não foi possível carregar a Logística.")}</div>`;
    return;
  }
  const statusVisualModelo = (modelo) => {
    const hoje = new Date().toISOString().slice(0, 10);
    if (modelo.status === "encerrado" || (modelo.vigencia_fim && modelo.vigencia_fim < hoje)) return "encerrado";
    if (modelo.status === "programado" && modelo.vigencia_inicio <= hoje) return "vigente";
    return modelo.status || "rascunho";
  };
  const renderLista = () => { lista.innerHTML = modelos.length ? modelos.map((modelo, indice) => {
    const config = modelo.configuracao || {}, statusVisual = statusVisualModelo(modelo);
    const periodo = `${modelo.vigencia_inicio || "—"} até ${modelo.vigencia_fim || "sem data final"}`;
    const acoes = statusVisual === "vigente"
      ? `<label class="model-end-date">Encerrar em <input data-fim-modelo="${indice}" type="date" min="${new Date().toISOString().slice(0, 10)}" value="${new Date().toISOString().slice(0, 10)}"></label><button data-encerrar-modelo="${indice}" class="secondary-action danger-action" type="button">Encerrar modelo</button>`
      : modelo.status === "programado"
        ? `<button data-rascunho-modelo="${indice}" class="secondary-action" type="button">Voltar a rascunho</button>`
        : modelo.status !== "encerrado"
          ? `<button data-programar-modelo="${indice}" class="primary-action" type="button">Programar início</button>` : "";
    return `<article class="agenda-card"><h3>${escapeHtml(modelo.nome)}</h3><p><strong>${escapeHtml(statusVisual)}</strong> · vigência: ${escapeHtml(periodo)}</p><p>${(config.blocos || []).length} bloco(s), ${(config.turmas || []).filter((t) => t["Ativa no modelo"] !== false).length} turma(s), ${(config.salas || []).filter((s) => String(s.Uso || "").toLowerCase() === "individual").length} sala(s) individual(is).</p><div class="scale-actions"><button data-editar-modelo="${indice}" class="secondary-action" type="button">Editar modelo</button><button data-excluir-modelo="${indice}" class="secondary-action danger-action" type="button">Excluir</button>${acoes}</div></article>`;
  }).join("") : `<div class="empty">Nenhum modelo cadastrado. Crie o primeiro para gerar novos rodízios.</div>`; ligarLista(); };
  const editor = $("#editor-modelo");
  const linhas = (itens, tipo, habilitadas = {}) => (itens || []).map((item) => {
    if (tipo === "bloco") return `<div class="model-row"><input data-bloco-nome value="${escapeHtml(item.Bloco || "")}" placeholder="Bloco"><input data-bloco-inicio value="${escapeHtml(item["Início"] || "")}" placeholder="08:50"><input data-bloco-fim value="${escapeHtml(item.Fim || "")}" placeholder="09:35"><button class="remove-row" type="button">×</button></div>`;
    if (tipo === "sala") return `<div class="model-row room-model-row"><input data-sala-nome value="${escapeHtml(item.Sala || "")}" placeholder="Ex.: SALA 1"><select data-sala-uso><option ${item.Uso === "Individual" ? "selected" : ""}>Individual</option><option ${item.Uso === "Turma" ? "selected" : ""}>Turma</option></select><input data-sala-area value="${escapeHtml(item["Área"] || "")}" placeholder="Área"><label class="checkbox-line"><input data-sala-ativa type="checkbox" ${item.Ativa !== false ? "checked" : ""}> Ativa</label><button class="remove-row" type="button">×</button></div>`;
    const professorasAtivas = pessoas.professoras.filter((professora) => professora.ativo !== false).map((professora) => professora.nome);
    const escolhidas = habilitadas[item.Atividade] || professorasAtivas;
    return `<div class="model-row activity-model-row"><div class="activity-fields"><label>Atividade<input data-atividade-nome value="${escapeHtml(item.Atividade || "")}" placeholder="Ex.: Teoria"></label><label>Formato<select data-atividade-formato><option ${item.Formato === "Turma" ? "selected" : ""}>Turma</option><option ${item.Formato === "Individual" ? "selected" : ""}>Individual</option></select></label><label>Duração<input data-atividade-duracao type="number" min="1" value="${escapeHtml(item["Duração (min)"] || "")}" placeholder="Minutos"></label><label>Sala sugerida<input data-atividade-sala value="${escapeHtml(item["Sala sugerida"] || "")}" placeholder="Ex.: SALA 8"></label></div><fieldset class="activity-enabled"><legend>Professoras habilitadas</legend><div class="activity-enabled-actions"><button type="button" class="text-action" data-marcar-todas>Marcar todas</button><button type="button" class="text-action" data-desmarcar-todas>Limpar</button></div><div class="activity-teacher-checks">${professorasAtivas.length ? professorasAtivas.map((professora) => `<label><input data-atividade-habilitada type="checkbox" value="${escapeHtml(professora)}" ${escolhidas.includes(professora) ? "checked" : ""}><span>${escapeHtml(professora)}</span></label>`).join("") : `<p class="hint">Cadastre professoras em Turmas e pessoas para habilitá-las aqui.</p>`}</div></fieldset><button class="remove-row" type="button" aria-label="Remover atividade">×</button></div>`;
  }).join("");
  const abrirEditor = (modelo = null) => {
    const config = modelo?.configuracao || {};
    const blocos = config.blocos || [{ Bloco: "Bloco 1", "Início": "08:50", Fim: "09:35" }, { Bloco: "Bloco 2", "Início": "09:40", Fim: "10:25" }, { Bloco: "Bloco 3", "Início": "10:30", Fim: "11:15" }];
    const atividades = config.atividades || [{ Atividade: "Teoria", Formato: "Turma", "Duração (min)": 45, "Sala sugerida": "SALA 8" }, { Atividade: "Solfejo Melódico", Formato: "Turma", "Duração (min)": 45, "Sala sugerida": "SALA 9" }, { Atividade: "Solfejo", Formato: "Individual", "Duração (min)": 15, "Sala sugerida": "Salas individuais" }, { Atividade: "Prática", Formato: "Individual", "Duração (min)": 30, "Sala sugerida": "Salas individuais" }];
    const salas = config.salas || [...Array.from({ length: 7 }, (_, indice) => ({ Sala: `SALA ${indice + 1}`, Uso: "Individual", Área: "Prática + Solfejo", Ativa: true })), { Sala: "SALA 8", Uso: "Turma", Área: "Teoria", Ativa: true }, { Sala: "SALA 9", Uso: "Turma", Área: "Solfejo Melódico", Ativa: true }];
    const ativas = new Set((config.turmas || []).filter((turma) => turma["Ativa no modelo"] !== false).map((turma) => turma.Turma));
    const turmasDoModelo = [...new Set([...pessoas.alunas.map((aluna) => aluna.turma).filter(Boolean), ...(config.turmas || []).map((turma) => turma.Turma).filter(Boolean)])];
    const capacidadePorTurma = Object.fromEntries((config.turmas || []).map((turma) => [turma.Turma, turma["Capacidade planejada"] || ""]));
    const linhaTurma = (turma, marcada = true, capacidade = "") => `<label class="model-turma-row"><span><input data-turma-modelo value="${escapeHtml(turma)}" type="checkbox" ${marcada ? "checked" : ""}> ${escapeHtml(turma)}</span><input data-capacidade-turma type="number" min="1" value="${escapeHtml(capacidade)}" placeholder="Capacidade"></label>`;
    editor.innerHTML = `<section class="panel model-editor"><h2>${modelo ? "Editar modelo" : "Novo modelo"}</h2><p>${modelo ? "As alterações substituem este modelo somente para as próximas escalas. Rodízios já salvos não são alterados." : "Defina os elementos que a Secretaria poderá usar na geração."}</p><div class="form-grid"><label>Nome do modelo<input id="modelo-nome" value="${escapeHtml(modelo?.nome || "Próximo bimestre")}"></label><label>Começa a valer em<input id="modelo-inicio" type="date" value="${escapeHtml(String(modelo?.vigencia_inicio || new Date().toISOString().slice(0, 10)).slice(0, 10))}"></label></div><h3>1. Blocos de horário</h3><div id="blocos-modelo">${linhas(blocos, "bloco")}</div><button id="adicionar-bloco" class="secondary-action" type="button">＋ Adicionar bloco</button><h3>2. Turmas participantes</h3><div class="turmas-checks" id="turmas-modelo">${turmasDoModelo.map((turma) => linhaTurma(turma, ativas.size === 0 || ativas.has(turma), capacidadePorTurma[turma] || pessoas.alunas.filter((aluna) => aluna.turma === turma && aluna.ativo !== false).length || "")).join("")}</div><div class="add-turma-modelo"><input id="nova-turma-modelo" placeholder="Ex.: Turma 4"><button id="adicionar-turma-modelo" class="secondary-action" type="button">＋ Adicionar turma</button></div><p class="hint">Uma turma planejada sem alunas ainda será salva no modelo; ela passa a entrar no rodízio quando houver alunas vinculadas a ela.</p><h3>3. Salas e capacidade</h3><div id="salas-modelo">${linhas(salas, "sala")}</div><button id="adicionar-sala" class="secondary-action" type="button">＋ Adicionar sala</button><h3>4. Atividades, duração e professoras habilitadas</h3><p class="hint">A geração do rodízio mostra apenas as professoras marcadas em cada atividade.</p><div id="atividades-modelo">${linhas(atividades, "atividade", config.professoras_habilitadas || {})}</div><button id="adicionar-atividade" class="secondary-action" type="button">＋ Adicionar atividade</button><h3>5. Regras</h3><div class="turmas-checks"><label class="checkbox-line"><input id="modelo-fixas" type="checkbox" ${config.usar_professoras_fixas ? "checked" : ""}> Este modelo usa professoras fixas</label><label class="checkbox-line"><input id="modelo-mesma-prof" type="checkbox" ${config.mesma_professora_nos_componentes !== false ? "checked" : ""}> Mesma professora em Solfejo e Prática</label><label class="checkbox-line"><input id="regra-prof" type="checkbox" ${(config.regras_rodizio?.nao_repetir_aluna !== false) ? "checked" : ""}> Não repetir professora antes de completar a roda</label><label class="checkbox-line"><input id="regra-sala" type="checkbox" ${(config.regras_rodizio?.nao_repetir_sala !== false) ? "checked" : ""}> Não repetir sala antes de completar a roda</label><label class="checkbox-line"><input id="regra-imediata" type="checkbox" ${(config.regras_rodizio?.nao_repetir_imediata !== false) ? "checked" : ""}> Evitar professora da semana anterior</label></div><div class="scale-actions"><button id="salvar-modelo" class="primary-action" type="button">${modelo ? "Salvar alterações" : "Salvar como rascunho"}</button><button id="cancelar-modelo" class="secondary-action" type="button">Cancelar</button></div><div id="modelo-feedback"></div></section>`;
    const remover = () => editor.querySelectorAll(".remove-row").forEach((botao) => botao.onclick = () => botao.closest(".model-row").remove());
    const ligarHabilitadas = () => {
      editor.querySelectorAll(".activity-model-row").forEach((linha) => {
        linha.querySelector("[data-marcar-todas]")?.addEventListener("click", () => linha.querySelectorAll("[data-atividade-habilitada]").forEach((campo) => { campo.checked = true; }));
        linha.querySelector("[data-desmarcar-todas]")?.addEventListener("click", () => linha.querySelectorAll("[data-atividade-habilitada]").forEach((campo) => { campo.checked = false; }));
      });
    };
    remover(); ligarHabilitadas();
    $("#adicionar-bloco").onclick = () => { $("#blocos-modelo").insertAdjacentHTML("beforeend", linhas([{ Bloco: `Bloco ${editor.querySelectorAll("[data-bloco-nome]").length + 1}`, "Início": "", Fim: "" }], "bloco")); remover(); };
    $("#adicionar-sala").onclick = () => { $("#salas-modelo").insertAdjacentHTML("beforeend", linhas([{ Sala: "", Uso: "Individual", Área: "Prática + Solfejo", Ativa: true }], "sala")); remover(); };
    $("#adicionar-atividade").onclick = () => { $("#atividades-modelo").insertAdjacentHTML("beforeend", linhas([{ Atividade: "", Formato: "Turma", "Duração (min)": 45, "Sala sugerida": "" }], "atividade")); remover(); ligarHabilitadas(); };
    $("#adicionar-turma-modelo").onclick = () => { const campo = $("#nova-turma-modelo"), nome = campo.value.trim(); if (!nome) return; const jaExiste = [...editor.querySelectorAll("[data-turma-modelo]")].some((item) => item.value.trim().toLocaleLowerCase("pt-BR") === nome.toLocaleLowerCase("pt-BR")); if (jaExiste) { campo.focus(); return; } $("#turmas-modelo").insertAdjacentHTML("beforeend", linhaTurma(nome, true)); campo.value = ""; };
    $("#cancelar-modelo").onclick = () => editor.innerHTML = "";
    $("#salvar-modelo").onclick = async () => {
      const nome = $("#modelo-nome").value.trim(), inicio = $("#modelo-inicio").value, feedback = $("#modelo-feedback");
      const novosBlocos = [...editor.querySelectorAll("#blocos-modelo .model-row")].map((linha) => ({ Bloco: linha.querySelector("[data-bloco-nome]").value.trim(), "Início": linha.querySelector("[data-bloco-inicio]").value.trim(), Fim: linha.querySelector("[data-bloco-fim]").value.trim() })).filter((bloco) => bloco["Início"] && bloco.Fim);
      const atividadesComHabilitadas = [...editor.querySelectorAll("#atividades-modelo .model-row")].map((linha) => ({
        Atividade: linha.querySelector("[data-atividade-nome]").value.trim(), Formato: linha.querySelector("[data-atividade-formato]").value,
        "Duração (min)": Number(linha.querySelector("[data-atividade-duracao]").value || 0), "Sala sugerida": linha.querySelector("[data-atividade-sala]").value.trim(),
        habilitadas: [...linha.querySelectorAll("[data-atividade-habilitada]:checked")].map((opcao) => opcao.value)
      })).filter((atividade) => atividade.Atividade);
      const novasAtividades = atividadesComHabilitadas.map(({ habilitadas, ...atividade }) => atividade);
      const habilitadas = Object.fromEntries(atividadesComHabilitadas.map((atividade) => [atividade.Atividade, atividade.habilitadas]));
      const novasSalas = [...editor.querySelectorAll("#salas-modelo .model-row")].map((linha) => ({ Sala: linha.querySelector("[data-sala-nome]").value.trim(), Uso: linha.querySelector("[data-sala-uso]").value, "Área": linha.querySelector("[data-sala-area]").value.trim(), Ativa: linha.querySelector("[data-sala-ativa]").checked })).filter((sala) => sala.Sala);
      const turmas = [...editor.querySelectorAll("[data-turma-modelo]")].map((item) => ({ Turma: item.value, "Ativa no modelo": item.checked, "Capacidade planejada": Number(item.closest(".model-turma-row")?.querySelector("[data-capacidade-turma]")?.value || 0) || null }));
      const salasIndividuais = novasSalas.filter((sala) => sala.Ativa && sala.Uso === "Individual");
      const atividadesSemProfessoras = atividadesComHabilitadas.filter((atividade) => !atividade.habilitadas.length).map((atividade) => atividade.Atividade);
      if (!nome || !inicio || !novosBlocos.length || !novasAtividades.length || !turmas.some((turma) => turma["Ativa no modelo"]) || !salasIndividuais.length || atividadesSemProfessoras.length) {
        feedback.innerHTML = `<div class="action-error">Informe nome, início, blocos completos, ao menos uma turma, uma sala individual ativa e professoras habilitadas para cada atividade${atividadesSemProfessoras.length ? ` (${escapeHtml(atividadesSemProfessoras.join(", "))})` : ""}.</div>`; return;
      }
      const configuracao = { modo: "configuravel", blocos: novosBlocos, turmas, salas: novasSalas, atividades: novasAtividades, professoras_habilitadas: habilitadas, usar_professoras_fixas: $("#modelo-fixas").checked, mesma_professora_nos_componentes: $("#modelo-mesma-prof").checked, regras_rodizio: { nao_repetir_aluna: $("#regra-prof").checked, nao_repetir_sala: $("#regra-sala").checked, nao_repetir_imediata: $("#regra-imediata").checked } };
      try { const salvo = await window.GemData.salvarModeloLogistica({ id: modelo?.id, nome, vigenciaInicio: inicio, configuracao, status: modelo?.status || "rascunho" }); if (salvo) { const indiceExistente = modelos.findIndex((item) => item.id === salvo.id); if (indiceExistente >= 0) modelos[indiceExistente] = salvo; else modelos.unshift(salvo); } feedback.innerHTML = `<div class="action-ok">${modelo ? "Modelo atualizado." : "Modelo salvo como rascunho. Programe-o quando quiser usá-lo para novas escalas."}</div>`; renderLista(); }
      catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
    };
  };
  const ligarLista = () => {
    lista.querySelectorAll("[data-editar-modelo]").forEach((botao) => botao.onclick = () => abrirEditor(modelos[Number(botao.dataset.editarModelo)]));
    lista.querySelectorAll("[data-excluir-modelo]").forEach((botao) => botao.onclick = async () => {
      const indice = Number(botao.dataset.excluirModelo), modelo = modelos[indice];
      if (!modelo || !confirm(`Excluir o modelo “${modelo.nome}”? Rodízios já salvos serão preservados, mas este modelo não poderá mais ser usado.`)) return;
      try { await window.GemData.removerModeloLogistica(modelo.id); modelos.splice(indice, 1); editor.innerHTML = ""; renderLista(); }
      catch (error) { alert(error.message); }
    });
    lista.querySelectorAll("[data-programar-modelo]").forEach((botao) => botao.onclick = async () => {
      try { await window.GemData.alterarStatusModelo(modelos[Number(botao.dataset.programarModelo)].id, "programado"); modelos[Number(botao.dataset.programarModelo)].status = "programado"; renderLista(); }
      catch (error) { alert(error.message); }
    });
    lista.querySelectorAll("[data-rascunho-modelo]").forEach((botao) => botao.onclick = async () => {
      try { await window.GemData.alterarStatusModelo(modelos[Number(botao.dataset.rascunhoModelo)].id, "rascunho"); modelos[Number(botao.dataset.rascunhoModelo)].status = "rascunho"; renderLista(); }
      catch (error) { alert(error.message); }
    });
    lista.querySelectorAll("[data-encerrar-modelo]").forEach((botao) => botao.onclick = async () => {
      const indice = Number(botao.dataset.encerrarModelo), modelo = modelos[indice];
      const dataFim = lista.querySelector(`[data-fim-modelo="${indice}"]`)?.value;
      if (!dataFim) { alert("Informe a data de encerramento."); return; }
      if (!confirm(`Encerrar “${modelo.nome}” para novas escalas a partir de ${dataFim}? As escalas já salvas serão preservadas.`)) return;
      try {
        await window.GemData.alterarStatusModelo(modelo.id, "encerrado", dataFim);
        modelo.status = "encerrado"; modelo.vigencia_fim = dataFim; renderLista();
      } catch (error) { alert(error.message); }
    });
  };
  $("#novo-modelo").onclick = () => abrirEditor(); renderLista();
}

async function renderRelatorios(content) {
  const hoje = new Date().toISOString().slice(0, 10);
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">RELATÓRIOS</p><h2>Relatório diário</h2><p>Consulte a escala, a chamada e os registros pedagógicos de qualquer sábado já salvo.</p></section><section class="panel"><div class="agenda-date"><div><label for="relatorio-data">Data</label><input id="relatorio-data" type="date" value="${hoje}"></div><button id="gerar-relatorio" class="primary-action" type="button">Gerar relatório</button></div><div id="relatorio-conteudo"></div></section><section class="panel report-export-panel"><div class="section-title"><div><h2>Exportar conteúdos para Excel</h2><p>Baixe somente os conteúdos de aula já lançados, sem fotos, senhas ou dados de chamada.</p></div></div><div class="analytics-filters"><label>Relatório<select id="excel-escopo"><option value="geral">Geral do GEM</option><option value="aluna">Por aluna</option></select></label><label id="excel-aluna-wrap" class="hidden">Aluna<select id="excel-aluna"></select></label><label>De <small>(opcional)</small><input id="excel-inicio" type="date"></label><label>Até <small>(opcional)</small><input id="excel-fim" type="date"></label><button id="baixar-relatorio-excel" class="primary-action" type="button">Baixar Excel</button></div><p id="excel-resumo" class="hint">Carregando conteúdos disponíveis…</p></section>`;
  const carregar = async () => {
    const destino = $("#relatorio-conteudo"); destino.innerHTML = `<div class="empty">Gerando relatório...</div>`;
    try {
      const dados = await window.GemData.dadosVisaoGeral($("#relatorio-data").value);
      const porAluna = new Map(dados.alunas.map((aluna) => [aluna, []]));
      dados.registros.forEach((registro) => { if (registro.Aluna) (porAluna.get(registro.Aluna) || porAluna.set(registro.Aluna, []).get(registro.Aluna)).push(registro); });
      const rotulo = (tipo) => ({ Chamada: "📍 Presença", Casa_MSA: "📚 Lição de casa — MSA", Casa_Apostila: "📚 Lição de casa — Apostila", Casa_Apostila_Prof: "📚 Lição de casa — Apostila de Prática", Casa_Teoria: "📚 Lição de casa — Folha Avulsa de Teoria", Casa_Teoria_Prof: "📚 Lição de casa — Folha Avulsa de Teoria", Casa_Apostila_Teoria_Prof: "📚 Lição de casa — Apostila de Teoria", Casa_Canto: "🎤 Lição de casa — Solfejo Melódico" }[tipo] || String(tipo || "Registro").replace(/^Analise_/, "📖 "));
      const mostrarDificuldades = (valor) => Array.isArray(valor) ? valor.filter(Boolean).join(" · ") : String(valor || "").replace(/^\[|\]$/g, "");
      const card = (item) => {
        const tipo = String(item.Tipo || ""), casa = tipo.startsWith("Casa_"), presenca = tipo === "Chamada", conteudo = casa ? (item.Licao_Casa || item.Licao_Atual) : item.Licao_Atual, dificuldade = mostrarDificuldades(item.Dificuldades);
        return `<article class="report-record ${casa ? "homework-record" : ""}"><h4>${escapeHtml(rotulo(tipo))}${item.Instrutora ? ` <small>— Professora: ${escapeHtml(item.Instrutora)}</small>` : ""}</h4>${presenca ? `<p><strong>Status:</strong> ${escapeHtml(item.Status || "Presente")}${item.Observacao ? ` · ${escapeHtml(item.Observacao)}` : ""}</p>` : ""}${conteudo ? `<p><strong>${casa ? "Lição deixada para casa" : "Conteúdo/atividade de hoje"}:</strong> ${escapeHtml(conteudo)}</p>` : ""}${dificuldade && dificuldade !== "Não apresentou dificuldades" ? `<p class="report-warning"><strong>⚠ Dificuldades:</strong> ${escapeHtml(dificuldade)}</p>` : dificuldade === "Não apresentou dificuldades" ? `<p class="report-ok">✓ Sem dificuldades registradas nesta aula.</p>` : ""}${item.Observacao && !presenca ? `<p class="report-note"><strong>📝 Observação da professora/Secretaria:</strong> ${escapeHtml(item.Observacao)}</p>` : ""}${item.Status && !presenca ? `<p class="report-status"><strong>Situação:</strong> ${escapeHtml(item.Status)}</p>` : ""}</article>`;
      };
      const linhasWhatsApp = [...porAluna.entries()].sort(([a], [b]) => a.localeCompare(b, "pt-BR")).map(([aluna, registros]) => {
        const chamada = registros.filter((item) => item.Tipo === "Chamada").at(-1);
        const linhas = [`👤 *${String(aluna).toUpperCase()}*`, `📍 Presença: ${chamada?.Status || "Ainda não registrada"}`];
        registros.filter((item) => item.Tipo !== "Chamada" && item.Tipo).forEach((item) => {
          const tipo = String(item.Tipo), casa = tipo.startsWith("Casa_");
          const conteudo = casa ? item.Licao_Casa : item.Licao_Atual;
          if (conteudo) linhas.push(`${casa ? "📚" : "📖"} *${rotulo(tipo).replace(/^📚 |^📖 |^🎤 /, "")}*: ${conteudo}`);
          const dificuldades = mostrarDificuldades(item.Dificuldades);
          if (dificuldades && !/não apresentou dificuldade/i.test(dificuldades)) linhas.push(`⚠ Dificuldades: ${dificuldades}`);
          if (item.Observacao && item.Tipo !== "Chamada") linhas.push(`📝 ${item.Observacao}`);
        });
        return linhas.join("\n");
      }).join("\n\n");
      const textoWhatsApp = `🎼 *${state.gem || "GEM Vila Verde"} — Relatório ${dados.data}*\n\n${linhasWhatsApp || "Não há alunas na escala deste sábado."}`;
      const corpo = porAluna.size ? [...porAluna.entries()].sort(([a], [b]) => a.localeCompare(b, "pt-BR")).map(([aluna, registros]) => `<section class="student-report"><h3>👧 ${escapeHtml(aluna)}</h3>${registros.length ? registros.map(card).join("") : `<div class="report-empty">Nenhum registro lançado ainda para esta aluna.</div>`}</section>`).join("") : `<div class="empty">Não há escala salva para esta data.</div>`;
      destino.innerHTML = `<div class="report-actions"><button id="copiar-relatorio-whatsapp" class="secondary-action" type="button">📋 Copiar para WhatsApp</button><button id="abrir-relatorio-whatsapp" class="secondary-action" type="button">💬 Enviar PDF pelo WhatsApp</button><button id="baixar-relatorio-pdf" class="primary-action" type="button">Baixar relatório em PDF</button></div><div id="report-print"><section class="compact-panel report-header"><h3>Relatório completo — ${escapeHtml(dados.data)}</h3><p><strong>${dados.alunas.length}</strong> aluna(s) na escala · <strong>${dados.ausentes.length}</strong> ausência(s) · <strong>${dados.analises.length}</strong> registro(s) pedagógico(s).</p></section>${corpo}</div>`;
      $("#copiar-relatorio-whatsapp").addEventListener("click", async () => {
        const botao = $("#copiar-relatorio-whatsapp");
        try {
          if (!navigator.clipboard?.writeText) throw new Error("A cópia automática não é suportada neste navegador.");
          await navigator.clipboard.writeText(textoWhatsApp);
          botao.textContent = "✓ Texto copiado";
          setTimeout(() => { botao.textContent = "📋 Copiar para WhatsApp"; }, 2500);
        } catch (erro) { alert(`${erro.message}\n\nCopie o texto abaixo:\n\n${textoWhatsApp}`); }
      });
      const nomePdf = `Relatorio_GEM_${dados.data.replaceAll("/", "-")}.pdf`;
      const gerarPdf = async () => {
        if (!window.html2canvas || !window.jspdf?.jsPDF) { alert("A ferramenta de PDF ainda está carregando. Tente novamente em alguns segundos."); return; }
        const alvo = $("#report-print"), blocos = [...alvo.querySelectorAll(".report-header, .student-report")];
        const pdf = new window.jspdf.jsPDF("p", "mm", "a4"), larguraPagina = 190, alturaPagina = 277;
        let primeiraPagina = true;
        for (const bloco of blocos) {
          const canvas = await window.html2canvas(bloco, { scale: 2, backgroundColor: "#ffffff", useCORS: true, windowWidth: bloco.scrollWidth });
          // Cada bloco mantém a mesma largura no PDF. Se o histórico da
          // aluna for longo, recortamos o canvas em páginas em vez de
          // diminuí-lo até ficar ilegível ou perder o fim do conteúdo.
          const pixelsPorMm = canvas.width / larguraPagina;
          const alturaMaximaEmPixels = Math.max(1, Math.floor(alturaPagina * pixelsPorMm));
          for (let inicioY = 0; inicioY < canvas.height; inicioY += alturaMaximaEmPixels) {
            const alturaTrecho = Math.min(alturaMaximaEmPixels, canvas.height - inicioY);
            const paginaCanvas = document.createElement("canvas");
            paginaCanvas.width = canvas.width;
            paginaCanvas.height = alturaTrecho;
            paginaCanvas.getContext("2d").drawImage(canvas, 0, inicioY, canvas.width, alturaTrecho, 0, 0, canvas.width, alturaTrecho);
            if (!primeiraPagina) pdf.addPage();
            primeiraPagina = false;
            const alturaNoPdf = alturaTrecho / pixelsPorMm;
            pdf.addImage(paginaCanvas.toDataURL("image/png"), "PNG", 10, 10, larguraPagina, alturaNoPdf);
          }
        }
        return pdf;
      };
      $("#abrir-relatorio-whatsapp").addEventListener("click", async () => {
        const botao = $("#abrir-relatorio-whatsapp"); botao.disabled = true; botao.textContent = "Gerando PDF...";
        try {
          const pdf = await gerarPdf(); if (!pdf) return;
          const arquivo = new File([pdf.output("blob")], nomePdf, { type: "application/pdf" });
          if (navigator.share && (!navigator.canShare || navigator.canShare({ files: [arquivo] }))) {
            await navigator.share({ title: "Relatório GEM", text: `Relatório ${dados.data}`, files: [arquivo] });
          } else {
            pdf.save(nomePdf);
            window.open("https://web.whatsapp.com/", "_blank", "noopener,noreferrer");
            alert("O PDF foi baixado. No WhatsApp, clique em Anexar e selecione esse arquivo para enviar.");
          }
        } catch (erro) { if (erro?.name !== "AbortError") alert("Não foi possível preparar o PDF: " + erro.message); }
        finally { botao.disabled = false; botao.textContent = "💬 Enviar PDF pelo WhatsApp"; }
      });
      $("#baixar-relatorio-pdf").addEventListener("click", async () => {
        const botao = $("#baixar-relatorio-pdf"); botao.disabled = true; botao.textContent = "Gerando PDF...";
        try { const pdf = await gerarPdf(); if (pdf) pdf.save(nomePdf); }
        catch (error) { alert("Não foi possível gerar o PDF: " + error.message); }
        finally { botao.disabled = false; botao.textContent = "Baixar relatório em PDF"; }
      });
    } catch (error) { destino.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  const prepararExportacaoExcel = async () => {
    const resumo = $("#excel-resumo"), seletorAluna = $("#excel-aluna");
    try {
      const base = await window.GemData.dadosExportacaoRelatorio();
      const normalizarData = (valor) => {
        const texto = String(valor || "").trim();
        if (/^\d{4}-\d{2}-\d{2}/.test(texto)) return texto.slice(0, 10);
        const [dia, mes, ano] = texto.split("/");
        return ano ? `${ano}-${mes}-${dia}` : "";
      };
      const disciplina = (tipo) => {
        const texto = String(tipo || "").replace(/^Analise_/, "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
        return texto === "CANTO" || texto === "SOLFEJO MELODICO" ? "Solfejo Melódico" : texto === "PRATICA" ? "Prática" : texto === "TEORIA" ? "Teoria" : texto === "SOLFEJO" ? "Solfejo" : "";
      };
      const textoDificuldades = (valor) => {
        if (Array.isArray(valor)) return valor.filter(Boolean).join("; ");
        const texto = String(valor || "").trim();
        if (!texto || /^\[\]$|^null$/i.test(texto)) return "";
        try { const lista = JSON.parse(texto); if (Array.isArray(lista)) return lista.filter(Boolean).join("; "); } catch (_) { /* histórico antigo em texto */ }
        return texto.replace(/^\[|\]$/g, "").replace(/[\"']/g, "");
      };
      const conteudos = base.historico.filter((registro) => disciplina(registro.Tipo) && String(registro.Licao_Atual || "").trim());
      seletorAluna.innerHTML = base.alunas.filter((aluna) => aluna.ativo !== false).map((aluna) => `<option value="${escapeHtml(aluna.nome)}">${escapeHtml(aluna.nome)}</option>`).join("");
      const atualizarResumo = () => {
        const escopo = $("#excel-escopo").value, aluna = seletorAluna.value, inicio = $("#excel-inicio").value, fim = $("#excel-fim").value;
        $("#excel-aluna-wrap").classList.toggle("hidden", escopo !== "aluna");
        const selecionados = conteudos.filter((registro) => {
          const data = normalizarData(registro.Data);
          return (!inicio || data >= inicio) && (!fim || data <= fim) && (escopo !== "aluna" || registro.Aluna === aluna);
        });
        resumo.textContent = `${selecionados.length} conteúdo(s) de aula selecionado(s)${escopo === "aluna" && aluna ? ` para ${aluna}` : ""}.`;
        return selecionados;
      };
      const nomeSeguro = (valor) => String(valor || "GEM").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "") || "GEM";
      const baixarExcel = () => {
        if (!window.XLSX) { alert("A ferramenta de Excel ainda está carregando. Verifique sua conexão e tente novamente."); return; }
        const selecionados = atualizarResumo();
        if (!selecionados.length) { alert("Não há conteúdos de aula no filtro escolhido."); return; }
        const botao = $("#baixar-relatorio-excel"); botao.disabled = true; botao.textContent = "Gerando Excel…";
        try {
          const linhas = selecionados.sort((a, b) => normalizarData(a.Data).localeCompare(normalizarData(b.Data)) || String(a.Aluna).localeCompare(String(b.Aluna), "pt-BR")).map((registro) => {
            const licao = String(registro.Licao_Atual || "").trim(), separador = licao.indexOf(":");
            const material = separador > 0 ? licao.slice(0, separador).trim() : "";
            const conteudo = separador > 0 ? licao.slice(separador + 1).trim() : licao;
            const data = normalizarData(registro.Data), [ano, mes, dia] = data.split("-").map(Number);
            return [data ? new Date(ano, mes - 1, dia) : "", registro.Aluna || "", disciplina(registro.Tipo), material, conteudo, registro.Instrutora || "", textoDificuldades(registro.Dificuldades), registro.Observacao || "", registro.Status || ""];
          });
          const cabecalhos = ["Data", "Aluna", "Disciplina", "Material", "Conteúdo trabalhado", "Professora", "Dificuldades observadas", "Observações", "Situação"];
          const planilha = XLSX.utils.aoa_to_sheet([cabecalhos, ...linhas], { cellDates: true });
          planilha["!cols"] = [{ wch: 13 }, { wch: 28 }, { wch: 20 }, { wch: 24 }, { wch: 48 }, { wch: 28 }, { wch: 45 }, { wch: 45 }, { wch: 24 }];
          planilha["!autofilter"] = { ref: `A1:I${Math.max(1, linhas.length + 1)}` };
          for (let linha = 2; linha <= linhas.length + 1; linha += 1) if (planilha[`A${linha}`]) planilha[`A${linha}`].z = "dd/mm/yyyy";
          const arquivo = XLSX.utils.book_new();
          const escopo = $("#excel-escopo").value, aluna = seletorAluna.value, inicio = $("#excel-inicio").value || "Início", fim = $("#excel-fim").value || "Hoje";
          const resumoPlanilha = XLSX.utils.aoa_to_sheet([["Relatório de conteúdos"], ["GEM", state.gem || "GEM Musical"], ["Escopo", escopo === "aluna" ? `Aluna: ${aluna}` : "Geral do GEM"], ["Período", `${inicio} até ${fim}`], ["Conteúdos exportados", linhas.length], ["Gerado em", new Date()]], { cellDates: true });
          resumoPlanilha["!cols"] = [{ wch: 24 }, { wch: 50 }];
          XLSX.utils.book_append_sheet(arquivo, resumoPlanilha, "Resumo");
          XLSX.utils.book_append_sheet(arquivo, planilha, "Conteúdos");
          XLSX.writeFile(arquivo, `Conteudos_${nomeSeguro(state.gem)}_${escopo === "aluna" ? nomeSeguro(aluna) : "Geral"}.xlsx`, { compression: true, cellDates: true });
        } catch (erro) { alert(`Não foi possível gerar o Excel: ${erro.message}`); }
        finally { botao.disabled = false; botao.textContent = "Baixar Excel"; }
      };
      $("#excel-escopo").addEventListener("change", atualizarResumo);
      [seletorAluna, $("#excel-inicio"), $("#excel-fim")].forEach((campo) => campo.addEventListener("change", atualizarResumo));
      $("#baixar-relatorio-excel").addEventListener("click", baixarExcel);
      atualizarResumo();
    } catch (erro) { resumo.textContent = erro.message || "Não foi possível preparar a exportação."; resumo.className = "action-error"; }
  };
  $("#gerar-relatorio").addEventListener("click", carregar); await carregar(); await prepararExportacaoExcel();
}

async function renderCorrecoesLicoes(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">SECRETARIA</p><h2>Correção de lições</h2><p>Este painel recebe Folha Avulsa de Teoria encaminhada pela professora e Apostila de Prática. Métodos, MSA e Apostila de Teoria são avaliados pela própria professora na aula seguinte.</p></section><section class="panel"><div class="analytics-filters"><label>Aluna<select id="correcao-aluna"></select></label><label>Responsável da Secretaria<select id="correcao-secretaria"></select></label><label>Data da conferência<input id="correcao-data" type="date" value="${new Date().toISOString().slice(0, 10)}"></label><button id="atualizar-correcoes" class="primary-action" type="button">Consultar pendências</button></div><div id="pendencias-licoes"><div class="empty">Carregando lições...</div></div></section><section class="panel"><h2>➕ Registrar atividade para correção</h2><p class="hint">Use se a folha de Teoria ou a Apostila de Prática foi entregue à Secretaria sem lançamento anterior.</p><div class="form-grid"><input id="nova-licao-conteudo" placeholder="Folha ou Apostila / exercícios"><select id="nova-licao-tipo"><option value="Casa_Teoria">Folha Avulsa de Teoria</option><option value="Casa_Apostila">Apostila de Prática</option></select><select id="nova-licao-status"><option>Pendente</option><option>Resolvido</option><option>Resolvido com pendências</option><option>Não resolvido</option><option>Não trouxe a apostila/atividade</option></select><input id="nova-licao-obs" placeholder="Observações técnicas / dicas"><button id="criar-licao-secretaria" class="primary-action" type="button">Salvar atividade</button></div><div id="correcao-feedback"></div></section>`;
  const base = await window.GemData.dadosCorrecoesLicoes(); const alunas = base.alunas.filter((aluna) => aluna.ativo !== false).map((aluna) => aluna.nome), secretarias = base.secretarias.filter((item) => item.ativo !== false).map((item) => item.nome);
  $("#correcao-aluna").innerHTML = alunas.map((aluna) => `<option value="${escapeHtml(aluna)}">${escapeHtml(aluna)}</option>`).join(""); $("#correcao-secretaria").innerHTML = (secretarias.length ? secretarias : [state.name]).map((nome) => `<option value="${escapeHtml(nome)}">${escapeHtml(nome)}</option>`).join("");
  const dataBr = (iso) => { const [ano, mes, dia] = String(iso).split("-"); return ano ? `${dia}/${mes}/${ano}` : iso; };
  const dataOrdenavel = (valor) => { const [dia, mes, ano] = String(valor || "").split("/"); return ano ? `${ano}${mes}${dia}` : "00000000"; };
  const atualizar = () => {
    const aluna = $("#correcao-aluna").value, porLicao = new Map();
    base.historico.filter((item) => item.Aluna === aluna).sort((a, b) => dataOrdenavel(a.Data).localeCompare(dataOrdenavel(b.Data)) || Number(a.id || 0) - Number(b.id || 0)).forEach((item) => porLicao.set(`${item.Tipo}|${item.Licao_Casa}`, item));
    const pendentes = [...porLicao.values()].filter((item) => !["Resolvido", "Realizada", "Realizadas - sem pendência", "Realizada - sem pendência"].includes(item.Status)); const destino = $("#pendencias-licoes");
    const opcoesResultado = (item, indice) => ["Resolvido", "Resolvido com pendências", "Não resolvido", "Não trouxe a apostila/atividade"].map((resultado) => `<label class="result-check ${item.Status === resultado ? "selected" : ""}"><input type="radio" name="status-correcao-${indice}" data-status-correcao="${indice}" value="${resultado}" ${item.Status === resultado ? "checked" : ""}><span>${escapeHtml(resultado)}</span></label>`).join("");
    const dataConferencia = dataBr($("#correcao-data").value);
    destino.innerHTML = pendentes.length ? `<div class="pending-title">🚨 Lições pendentes para ${escapeHtml(aluna)}</div>${pendentes.map((item, indice) => {
      const tipo = ["Casa_Apostila", "Casa_Apostila_Prof"].includes(item.Tipo) ? "📕 Apostila (Prática)" : "📘 Folha Avulsa (Teoria)";
      // “Resolvido com pendências” continua na fila. A observação é
      // reaproveitada somente se a Secretaria reabrir a própria correção no
      // mesmo dia; em outro dia começa limpa para registrar a nova devolutiva.
      const manterObservacao = item.Status === "Resolvido com pendências" && String(item.Data || "") === dataConferencia;
      const observacaoInicial = manterObservacao ? String(item.Observacao || "").replace(/^Sec:\s*/i, "") : "";
      return `<article class="pending-card"><div><h3>${tipo}</h3><p><strong>${escapeHtml(item.Licao_Casa || "Lição não informada")}</strong></p><p class="hint">Lançada em ${escapeHtml(item.Data || "—")} · Status atual: ${escapeHtml(item.Status || "Pendente")}</p></div><div class="pending-action"><div class="result-area"><strong>Resultado da correção</strong><div class="result-checks">${opcoesResultado(item, indice)}</div></div><label class="correction-note">Observação da Secretaria<textarea data-obs-correcao="${indice}" placeholder="Ex.: quais exercícios ficaram incompletos e o que deve ser retomado">${escapeHtml(observacaoInicial)}</textarea></label><button data-salvar-correcao="${indice}" class="primary-action" type="button">Salvar correção</button></div></article>`;
    }).join("")}` : `<div class="action-ok">✅ Nenhuma folha de Teoria ou Apostila de Prática pendente para esta aluna.</div>`;
    destino.querySelectorAll("[data-status-correcao]").forEach((campo) => campo.addEventListener("change", () => {
      destino.querySelectorAll(`[data-status-correcao="${campo.dataset.statusCorrecao}"]`).forEach((outro) => outro.closest(".result-check").classList.toggle("selected", outro.checked));
    }));
    destino.querySelectorAll("[data-salvar-correcao]").forEach((botao) => botao.addEventListener("click", async () => {
      const indice = Number(botao.dataset.salvarCorrecao), item = pendentes[indice], status = destino.querySelector(`[data-status-correcao="${indice}"]:checked`)?.value;
      if (!status) { botao.closest(".pending-action").insertAdjacentHTML("beforeend", `<div class="action-error">Escolha o resultado da correção.</div>`); return; }
      botao.disabled = true;
      try {
        await window.GemData.atualizarCorrecaoLicao(item.id, { status, observacao: destino.querySelector(`[data-obs-correcao="${indice}"]`).value.trim(), secretaria: $("#correcao-secretaria").value, data: dataBr($("#correcao-data").value) });
        const posicao = base.historico.findIndex((registro) => String(registro.id) === String(item.id));
        if (posicao >= 0) base.historico[posicao] = { ...base.historico[posicao], Status: status, Observacao: `Sec: ${destino.querySelector(`[data-obs-correcao="${indice}"]`).value.trim()}`, Data: dataBr($("#correcao-data").value) };
        atualizar();
      } catch (error) { botao.disabled = false; botao.closest(".pending-action").insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); }
    }));
  };
  $("#atualizar-correcoes").addEventListener("click", atualizar); atualizar();
  $("#criar-licao-secretaria").addEventListener("click", async () => { const feedback = $("#correcao-feedback"), licao = $("#nova-licao-conteudo").value.trim(); if (!licao) { feedback.innerHTML = `<div class="action-error">Informe a lição ou página.</div>`; return; } try { await window.GemData.criarCorrecaoLicao({ aluna: $("#correcao-aluna").value, tipo: $("#nova-licao-tipo").value, licao, status: $("#nova-licao-status").value, observacao: $("#nova-licao-obs").value.trim(), secretaria: $("#correcao-secretaria").value, data: dataBr($("#correcao-data").value) }); feedback.innerHTML = `<div class="action-ok">Atividade registrada para correção.</div>`; } catch (error) { feedback.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; } });
}

async function renderAnalitico(content, opcoes = {}) {
  const titulo = opcoes.titulo || "Analítico e desempenho", descricao = opcoes.descricao || "Indicadores calculados somente a partir dos registros, chamadas, lições e notas já existentes no GEM.";
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ACOMPANHAMENTO PEDAGÓGICO</p><h2>${escapeHtml(titulo)}</h2><p>${escapeHtml(descricao)}</p></section><section class="panel"><div class="person-tabs"><button class="tab-action active" data-analise="prontuario">Prontuário individual</button><button class="tab-action" data-analise="quadro">Quadro de desempenho</button><button class="tab-action" data-analise="boletim">Boletim</button></div><div class="analytics-filters"><label>Período<select id="analise-periodo"><option value="30">Mensal</option><option value="60" selected>Bimestral</option><option value="180">Semestral</option><option value="tudo">Tudo</option><option value="personalizado">Personalizado</option></select></label><label>De<input id="analise-inicio" type="date"></label><label>Até<input id="analise-fim" type="date"></label><label id="analise-aluna-wrap">Aluna<select id="analise-aluna"></select></label><button id="atualizar-analise" class="primary-action" type="button">Atualizar</button></div><div id="analise-conteudo"><div class="empty">Carregando indicadores...</div></div></section>`;
  const dados = await window.GemData.dadosAnalitico();
  const hoje = new Date(), inicio = new Date(); inicio.setDate(hoje.getDate() - 60);
  $("#analise-inicio").value = inicio.toISOString().slice(0, 10); $("#analise-fim").value = hoje.toISOString().slice(0, 10);
  $("#analise-aluna").innerHTML = dados.alunas.map((aluna) => `<option value="${escapeHtml(aluna.nome)}">${escapeHtml(aluna.nome)}</option>`).join("");
  let aba = "prontuario";
  const dataRegistro = (valor) => { const texto = String(valor || "").trim(); if (/^\d{4}-\d{2}-\d{2}/.test(texto)) return texto.slice(0, 10); const [dia, mes, ano] = texto.split("/"); return ano ? `${ano}-${mes}-${dia}` : ""; };
  const disciplinaAnalise = (tipo) => { const texto = String(tipo || "").replace(/^Analise_/, "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase(); return texto === "CANTO" || texto === "SOLFEJO MELODICO" ? "Solfejo Melódico" : texto === "PRATICA" ? "Prática" : texto === "TEORIA" ? "Teoria" : texto === "SOLFEJO" ? "Solfejo" : ""; };
  const dificuldades = (valor) => { if (Array.isArray(valor)) return valor.filter((item) => item && !/^\[\]$|^null$|^nan$/i.test(String(item).trim())); if (typeof valor !== "string") return []; const texto = valor.trim(); if (!texto || /^\[\]$|^null$|^nan$/i.test(texto)) return []; try { const json = JSON.parse(texto); if (Array.isArray(json)) return json.filter(Boolean); } catch (_) {} return texto.replace(/^\[|\]$/g, "").split(/[,;]+/).map((item) => item.trim().replace(/^['"]|['"]$/g, "")).filter(Boolean); };
  const dentroPeriodo = (registro) => { const data = dataRegistro(registro.Data); return data && data >= $("#analise-inicio").value && data <= $("#analise-fim").value; };
  // Há histórico antigo no GEM em que o Tipo veio somente como "Prática",
  // "Teoria" ou "Solfejo". Ele é uma aula verdadeira e não pode aparecer
  // como "sem registros" só porque não recebeu o prefixo Analise_.
  const ehRegistroPedagogico = (registro) => Boolean(disciplinaAnalise(registro.Tipo)) && !String(registro.Tipo || "").startsWith("Casa_");
  const classificacao = (registros) => { if (!registros.length) return { icone: "🥉", nome: "Sem registros", nota: null }; const limpos = registros.filter((registro) => !dificuldades(registro.Dificuldades).some((item) => !/não apresentou dificuldade/i.test(item))); const nota = Math.round(limpos.length / registros.length * 100); return nota >= 80 ? { icone: "🥇", nome: "Ouro", nota } : nota >= 50 ? { icone: "🥈", nome: "Prata", nota } : { icone: "🥉", nome: "Bronze", nota }; };
  const graficoBarras = (titulo, itens, maximoFixo) => {
    const maximo = maximoFixo || Math.max(1, ...itens.map((item) => Number(item.valor) || 0));
    if (!itens.some((item) => Number(item.valor))) return `<article class="analytics-chart empty-chart"><h4>${escapeHtml(titulo)}</h4><p>Ainda não há dados no período escolhido.</p></article>`;
    return `<article class="analytics-chart"><h4>${escapeHtml(titulo)}</h4><div class="bar-chart">${itens.map((item) => `<div class="bar-item"><div class="bar-track"><i style="height:${Math.max(3, Math.round((Number(item.valor) || 0) / maximo * 100))}%;background:${escapeHtml(item.cor || "#577db8")}"></i></div><strong>${escapeHtml(item.valor)}</strong><small>${escapeHtml(item.rotulo)}</small></div>`).join("")}</div></article>`;
  };
  const graficoAssiduidade = (chamadas) => {
    const porDia = new Map();
    chamadas.forEach((item) => { const data = dataRegistro(item.Data); if (data) porDia.set(data, item.Status === "Presente" ? 1 : item.Status === "Justificada" ? .5 : 0); });
    const pontos = [...porDia.entries()].sort(([a], [b]) => a.localeCompare(b));
    if (!pontos.length) return `<article class="analytics-chart empty-chart"><h4>Linha do tempo de assiduidade</h4><p>Ainda não há chamada no período escolhido.</p></article>`;
    const largura = 520, altura = 170, margem = 20;
    const coordenadas = pontos.map(([_, nivel], indice) => {
      const x = pontos.length === 1 ? largura / 2 : margem + indice * ((largura - margem * 2) / (pontos.length - 1));
      const y = margem + (1 - nivel) * (altura - margem * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
    return `<article class="analytics-chart attendance-chart"><h4>Linha do tempo de assiduidade</h4><svg viewBox="0 0 ${largura} ${altura}" role="img" aria-label="Assiduidade no período"><line x1="${margem}" y1="${margem}" x2="${largura - margem}" y2="${margem}"/><line x1="${margem}" y1="${altura / 2}" x2="${largura - margem}" y2="${altura / 2}"/><line x1="${margem}" y1="${altura - margem}" x2="${largura - margem}" y2="${altura - margem}"/><polyline points="${coordenadas}"/></svg><div class="chart-legend"><span>● Presente</span><span>● Justificada</span><span>● Ausente</span></div><small>${pontos.map(([data]) => escapeHtml(data.split("-").reverse().join("/"))).join(" · ")}</small></article>`;
  };
  const graficoProvas = (itens) => {
    if (!itens.length) return `<div class="empty-chart"><p>Ainda não há aulas ou notas de provas para comparar.</p></div>`;
    return `<div class="comparison-chart">${itens.map((item) => `<div class="comparison-chart-row"><strong>${escapeHtml(item.disciplina)}</strong><div><span class="comparison-pedagogico" style="width:${item.rendimento === null ? 0 : item.rendimento}%"></span><span class="comparison-provas" style="width:${item.media === null ? 0 : item.media * 10}%"></span></div><small>Aulas ${item.rendimento === null ? "—" : `${item.rendimento}%`} · Provas ${item.media === null ? "—" : `${item.media.toFixed(1)}/10`}</small></div>`).join("")}<p class="chart-legend"><span class="legend-pedagogico">■ Rendimento pedagógico</span><span class="legend-provas">■ Média das provas</span></p></div>`;
  };
  const render = () => {
    const destino = $("#analise-conteudo"), periodo = dados.historico.filter(dentroPeriodo);
    $("#analise-aluna-wrap").classList.toggle("hidden", aba !== "prontuario" && aba !== "boletim");
    if (aba === "quadro") {
      const disciplinas = ["Prática", "Teoria", "Solfejo", "Solfejo Melódico"];
      const estudoDoPeriodo = (nome) => dados.estudos.filter((estudo) => {
        const data = dataRegistro(estudo.data || estudo.Data);
        return estudo.aluna === nome && data && data >= $("#analise-inicio").value && data <= $("#analise-fim").value;
      });
      const celulaEstudo = (nome) => {
        const estudos = estudoDoPeriodo(nome);
        if (!estudos.length) return "— sem registro";
        const dias = estudos.filter((item) => Array.isArray(item.horarios) && item.horarios.length).length;
        const percentual = Math.round(dias / estudos.length * 100);
        const rosto = percentual >= 70 ? "😊" : percentual >= 40 ? "😐" : "😢";
        return `${rosto} ${percentual}%<br><small>${dias}/${estudos.length} dias</small>`;
      };
      destino.innerHTML = `<h3>🏆 Quadro de desempenho</h3><p class="hint">A medalha usa a porcentagem de aulas sem dificuldades registradas no período escolhido. A última coluna mostra o estudo em casa informado pela própria aluna.</p><div class="table-wrap"><table class="scale-table performance-table"><thead><tr><th>Aluna</th>${disciplinas.map((disciplina) => `<th>${escapeHtml(disciplina)}</th>`).join("")}<th>Estudo em casa</th></tr></thead><tbody>${dados.alunas.filter((aluna) => aluna.ativo !== false).map((aluna) => `<tr><th>${escapeHtml(aluna.nome)}</th>${disciplinas.map((disciplina) => { const resultado = classificacao(periodo.filter((registro) => registro.Aluna === aluna.nome && disciplinaAnalise(registro.Tipo) === disciplina)); return `<td>${resultado.icone} ${resultado.nome}${resultado.nota !== null ? `<br><small>${resultado.nota}%</small>` : ""}</td>`; }).join("")}<td>${celulaEstudo(aluna.nome)}</td></tr>`).join("")}</tbody></table></div>`;
      return;
    }
    const aluna = $("#analise-aluna").value, registros = periodo.filter((registro) => registro.Aluna === aluna), chamadas = registros.filter((registro) => registro.Tipo === "Chamada"), aulas = registros.filter(ehRegistroPedagogico), casas = registros.filter((registro) => String(registro.Tipo || "").startsWith("Casa_"));
    const estudos = dados.estudos.filter((estudo) => { const data = dataRegistro(estudo.data || estudo.Data); return estudo.aluna === aluna && data && data >= $("#analise-inicio").value && data <= $("#analise-fim").value; });
    const diasEstudados = estudos.filter((estudo) => Array.isArray(estudo.horarios) && estudo.horarios.length).length;
    const inicioPeriodo = new Date(`${$("#analise-inicio").value}T12:00:00`), fimPeriodo = new Date(`${$("#analise-fim").value}T12:00:00`);
    const diasDoPeriodo = Math.max(1, Math.round((fimPeriodo - inicioPeriodo) / 86400000) + 1);
    const constanciaEstudo = Math.round(diasEstudados / diasDoPeriodo * 100);
    if (aba === "boletim") { const notas = dados.notas.filter((nota) => nota.aluna === aluna); destino.innerHTML = `<h3>🎼 Boletim — ${escapeHtml(aluna)}</h3>${notas.length ? `<div class="table-wrap"><table class="scale-table"><thead><tr><th>Avaliação</th><th>Disciplina</th><th>Nota</th></tr></thead><tbody>${notas.map((nota) => { const avaliacao = dados.avaliacoes.find((item) => String(item.id) === String(nota.avaliacao_id)); return `<tr><td>${escapeHtml(avaliacao?.titulo || "Avaliação")}</td><td>${escapeHtml(nota.disciplina || "—")}</td><td>${escapeHtml(nota.nota ?? "—")}</td></tr>`; }).join("")}</tbody></table></div>` : `<div class="empty">Ainda não há notas lançadas para esta aluna.</div>`}`; return; }
    const presentes = chamadas.filter((item) => !["Ausente", "Justificada"].includes(item.Status)).length, faltas = chamadas.filter((item) => item.Status === "Ausente").length, justificadas = chamadas.filter((item) => item.Status === "Justificada").length, aproveitamento = classificacao(aulas).nota || 0;
    const listaDificuldades = [...new Set(aulas.flatMap((registro) => dificuldades(registro.Dificuldades)).filter((item) => !/não apresentou dificuldade/i.test(item)))]; const pendentes = casas.filter((registro) => !/resolvido|realizada|sem pendência/i.test(String(registro.Status || "")));
    const dificuldadesGrafico = [...new Set(listaDificuldades)].map((dificuldade) => ({ rotulo: dificuldade, valor: aulas.reduce((total, aula) => total + dificuldades(aula.Dificuldades).filter((item) => item === dificuldade).length, 0), cor: "#a76486" })).sort((a, b) => b.valor - a.valor).slice(0, 8);
    destino.innerHTML = `<section class="analytics-summary"><h3>👤 Prontuário — ${escapeHtml(aluna)}</h3><div class="grid"><div class="metric"><strong>${chamadas.length ? Math.round((presentes + justificadas * .5) / chamadas.length * 100) : 0}%</strong><span>Frequência ponderada</span></div><div class="metric"><strong>${faltas} / ${justificadas}</strong><span>Faltas / justificadas</span></div><div class="metric"><strong>${aproveitamento}%</strong><span>Aproveitamento nas aulas</span></div><div class="metric"><strong>${pendentes.length}</strong><span>Lições pendentes</span></div><div class="metric"><strong>${constanciaEstudo}%</strong><span>Constância de estudo</span></div></div><div class="analytics-columns"><section><h4>⚠ Dificuldades registradas</h4>${listaDificuldades.length ? `<ul>${listaDificuldades.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>` : "<p>Sem dificuldades registradas no período.</p>"}</section><section><h4>📚 Lições de casa</h4>${casas.length ? casas.map((item) => `<p class="homework-line"><strong>${escapeHtml(item.Tipo.replace("Casa_", ""))}:</strong> ${escapeHtml(item.Licao_Casa || "—")} <small>${escapeHtml(item.Status || "Pendente")}</small></p>`).join("") : "<p>Nenhuma lição registrada no período.</p>"}</section><section><h4>✅ Estudo em casa</h4>${estudos.length ? `<p><strong>${diasEstudados}</strong> dia(s) com estudo registrado em ${estudos.length} lançamento(s).</p>${estudos.slice(0, 10).map((item) => `<p class="homework-line"><strong>${escapeHtml(item.data || item.Data || "—")}:</strong> ${escapeHtml((item.horarios || []).join(" · ") || "sem horário informado")}</p>`).join("")}` : "<p>Não há estudo informado no período.</p>"}</section></div><section class="feedback-panel"><h4>👩‍🏫 Feedback das professoras e Secretaria</h4>${aulas.length ? aulas.map((item) => `<article><strong>${escapeHtml(disciplinaAnalise(item.Tipo) || String(item.Tipo).replace("Analise_", ""))} — ${escapeHtml(item.Data || "")}</strong>${item.Instrutora ? ` · ${escapeHtml(item.Instrutora)}` : ""}<p>${escapeHtml(item.Licao_Atual || "Sem conteúdo informado")}</p>${item.Observacao ? `<p class="report-note">📝 ${escapeHtml(item.Observacao)}</p>` : ""}</article>`).join("") : "<p>Nenhuma aula registrada no período.</p>"}</section></section>`;
    const caixaDificuldades = destino.querySelector(".analytics-columns > section:first-child");
    if (caixaDificuldades) caixaDificuldades.innerHTML = `<h4>⚠ Dificuldades registradas</h4>${graficoBarras("Ocorrências no período", dificuldadesGrafico)}`;
    destino.querySelector(".analytics-summary > .grid")?.insertAdjacentHTML("afterend", `<section class="analytics-charts">${graficoAssiduidade(chamadas)}${graficoBarras("Status de frequência", [{ rotulo: "Presenças", valor: presentes, cor: "#3a9d6d" }, { rotulo: "Faltas", valor: faltas, cor: "#d65b70" }, { rotulo: "Justificadas", valor: justificadas, cor: "#d6a33a" }])}</section>`);
    const objetivoAtual = (dados.objetivos || []).find((item) => item.aluna === aluna) || {};
    const objetivoMarkup = opcoes.somenteLeitura
      ? `<section class="feedback-panel objective-panel"><h4>🎯 Próximos objetivos pedagógicos</h4><p>${objetivoAtual.texto ? escapeHtml(objetivoAtual.texto) : "Nenhum objetivo combinado ainda para esta aluna."}</p>${objetivoAtual.professora ? `<small>Última atualização por: ${escapeHtml(objetivoAtual.professora)}</small>` : ""}</section>`
      : `<section class="feedback-panel objective-panel"><h4>🎯 Próximos objetivos pedagógicos</h4><p class="hint">Visível para a Secretaria e para as professoras que derem aula a esta aluna.</p><label>Foco para as próximas aulas<textarea id="objetivo-pedagogico" placeholder="Ex.: consolidar leitura de clave de sol e manter o estudo diário.">${escapeHtml(objetivoAtual.texto || "")}</textarea></label>${objetivoAtual.professora ? `<small>Última atualização por: ${escapeHtml(objetivoAtual.professora)}</small>` : ""}<div class="inline-actions"><button id="salvar-objetivo-pedagogico" class="secondary-action" type="button">Salvar objetivo</button><span id="objetivo-feedback" aria-live="polite"></span></div></section>`;
    destino.querySelector(".analytics-summary")?.insertAdjacentHTML("beforeend", objetivoMarkup);
    $("#salvar-objetivo-pedagogico")?.addEventListener("click", async () => {
      const botao = $("#salvar-objetivo-pedagogico"), retorno = $("#objetivo-feedback");
      botao.disabled = true;
      try {
        await window.GemData.salvarObjetivoPedagogico({ aluna, texto: $("#objetivo-pedagogico").value, professora: state.name });
        const salvo = (dados.objetivos || []).find((item) => item.aluna === aluna);
        if (salvo) { salvo.texto = $("#objetivo-pedagogico").value.trim(); salvo.professora = state.name; }
        else (dados.objetivos ||= []).push({ aluna, texto: $("#objetivo-pedagogico").value.trim(), professora: state.name });
        retorno.innerHTML = `<span class="action-ok">Objetivo salvo.</span>`;
      } catch (erro) { retorno.innerHTML = `<span class="action-error">${escapeHtml(erro.message)}</span>`; }
      finally { botao.disabled = false; }
    });
    const avaliacoesDoPeriodo = new Set(dados.avaliacoes.filter((avaliacao) => {
      const data = dataRegistro(avaliacao.data_avaliacao);
      return data && data >= $("#analise-inicio").value && data <= $("#analise-fim").value;
    }).map((avaliacao) => String(avaliacao.id)));
    const notasPeriodo = dados.notas.filter((nota) => nota.aluna === aluna && avaliacoesDoPeriodo.has(String(nota.avaliacao_id)) && Number.isFinite(Number(nota.nota)));
    const resumoDisciplinas = ["Prática", "Teoria", "Solfejo", "Solfejo Melódico"].map((disciplina) => {
      const registrosDisciplina = aulas.filter((registro) => disciplinaAnalise(registro.Tipo) === disciplina);
      if (!registrosDisciplina.length) return `${disciplina}: sem aula registrada no período.`;
      const resultado = classificacao(registrosDisciplina), ocorrencias = registrosDisciplina.flatMap((registro) => dificuldades(registro.Dificuldades)).filter((item) => !/não apresentou dificuldade/i.test(item));
      const recorrente = ocorrencias.length ? [...new Set(ocorrencias)].sort((a, b) => ocorrencias.filter((item) => item === b).length - ocorrencias.filter((item) => item === a).length)[0] : "nenhuma dificuldade registrada";
      return `${disciplina}: ${resultado.nota}% de aulas sem dificuldade; dificuldade mais recorrente: ${recorrente}.`;
    }).join("\n");
    const mediaProvas = notasPeriodo.length ? (notasPeriodo.reduce((total, nota) => total + Number(nota.nota), 0) / notasPeriodo.length).toFixed(1) : "sem notas de prova";
    const comparacaoProvas = ["Prática", "Teoria", "Solfejo", "Solfejo Melódico"].map((disciplina) => {
      const aulasDisciplina = aulas.filter((registro) => disciplinaAnalise(registro.Tipo) === disciplina);
      const notasDisciplina = notasPeriodo.filter((nota) => nota.disciplina === disciplina).map((nota) => Number(nota.nota)).filter(Number.isFinite);
      if (!aulasDisciplina.length && !notasDisciplina.length) return null;
      const rendimento = aulasDisciplina.length ? classificacao(aulasDisciplina).nota : null;
      const media = notasDisciplina.length ? notasDisciplina.reduce((total, nota) => total + nota, 0) / notasDisciplina.length : null;
      return { disciplina, rendimento, media };
    }).filter(Boolean);
    const notasSecretaria = casas.filter((item) => ["Casa_Teoria", "Casa_Apostila", "Casa_Apostila_Prof"].includes(String(item.Tipo || "")) && /^Sec:\s*/i.test(String(item.Observacao || "")));
    const dificuldadesPorMes = new Map();
    aulas.forEach((item) => {
      const mes = dataRegistro(item.Data).slice(0, 7);
      if (!mes) return;
      dificuldades(item.Dificuldades).filter((dificuldade) => !/não apresentou dificuldade|não participou/i.test(dificuldade)).forEach((dificuldade) => {
        const chave = `${mes}|${dificuldade}`;
        dificuldadesPorMes.set(chave, (dificuldadesPorMes.get(chave) || 0) + 1);
      });
    });
    const evolucao = [...dificuldadesPorMes.entries()].map(([chave, quantidade]) => { const [mes, dificuldade] = chave.split("|"); return { mes, dificuldade, quantidade }; }).sort((a, b) => a.mes.localeCompare(b.mes) || b.quantidade - a.quantidade);
    destino.querySelector(".analytics-summary")?.insertAdjacentHTML("beforeend", `<section class="analytics-columns analytics-expanded"><section><h4>🎼 Provas e rendimento pedagógico</h4>${comparacaoProvas.length ? `<div class="comparison-list">${comparacaoProvas.map((item) => `<article><strong>${escapeHtml(item.disciplina)}</strong><span>Aulas: ${item.rendimento === null ? "sem registro" : `${item.rendimento}% sem dificuldade`}</span><span>Provas: ${item.media === null ? "sem nota" : `${item.media.toFixed(1)} / 10`}</span></article>`).join("")}</div><p class="hint">O rendimento das aulas considera os registros pedagógicos; a nota de prova não é convertida nem altera esse indicador.</p>` : `<p>Não há aulas ou notas no período escolhido.</p>`}</section><section><h4>🏢 Observações da Secretaria</h4>${notasSecretaria.length ? notasSecretaria.map((item) => `<article class="secretary-note"><strong>${escapeHtml(casaCategoria(item.Tipo))} — ${escapeHtml(item.Data || "")}</strong><p>${escapeHtml(item.Licao_Casa || "Lição não informada")}</p><p>${escapeHtml(String(item.Observacao || "").replace(/^Sec:\s*/i, ""))}</p></article>`).join("") : `<p>Não há observações de correção da Secretaria no período.</p>`}</section></section><section class="feedback-panel evolution-panel"><h4>📉 Evolução das dificuldades</h4>${evolucao.length ? `<div class="evolution-list">${evolucao.map((item) => `<article><span>${escapeHtml(item.mes)}</span><strong>${escapeHtml(item.dificuldade)}</strong><b>${item.quantidade}×</b></article>`).join("")}</div><p class="hint">Cada linha é uma dificuldade registrada nas aulas daquele mês. Use como sinal pedagógico, não como diagnóstico.</p>` : `<p>Não há dificuldades registradas no período.</p>`}</section>`);
    destino.querySelector(".analytics-expanded section")?.insertAdjacentHTML("beforeend", graficoProvas(comparacaoProvas));
    const maisFrequentes = [...new Set(evolucao.map((item) => item.dificuldade))].map((dificuldade) => ({ rotulo: dificuldade, valor: evolucao.filter((item) => item.dificuldade === dificuldade).reduce((total, item) => total + item.quantidade, 0), cor: "#a76486" })).sort((a, b) => b.valor - a.valor).slice(0, 6);
    destino.querySelector(".evolution-panel")?.insertAdjacentHTML("afterbegin", graficoBarras("Dificuldades mais recorrentes", maisFrequentes));
    const resumoIa = `Aluna: ${aluna}\nPeríodo: ${$("#analise-inicio").value} a ${$("#analise-fim").value}\nFrequência ponderada: ${chamadas.length ? Math.round((presentes + justificadas * .5) / chamadas.length * 100) : 0}% (${faltas} faltas e ${justificadas} justificadas)\nEstudo em casa: ${diasEstudados} dia(s) com estudo em ${diasDoPeriodo} dias do período (${constanciaEstudo}% de constância); ${estudos.length} lançamento(s) feitos pela aluna.\nLições pendentes: ${pendentes.length}\nMédia das provas: ${mediaProvas}\nNotas por disciplina: ${notasPeriodo.map((nota) => `${nota.disciplina} ${nota.nota}`).join(", ") || "sem notas no período"}\nDesempenho por disciplina:\n${resumoDisciplinas}`;
    destino.insertAdjacentHTML("beforeend", state.externo
      ? `<section class="feedback-panel"><h4>🤖 IA não configurada para este GEM</h4><p>Este GEM usa uma base independente. Para usar a análise pedagógica com IA, conecte uma integração própria da IA no ambiente deste GEM.</p></section>`
      : `<section class="feedback-panel ai-feedback"><h4>🤖 Resumo pedagógico com IA</h4><p>A IA recebe apenas este resumo de registros, frequência, lições e provas. Ela não recebe fotos, documentos nem senha; é uma sugestão pedagógica, não um diagnóstico.</p><label>Pergunta opcional para a IA<textarea id="pergunta-analitico-ia" placeholder="Ex.: Em qual conteúdo vale focar na próxima aula?"></textarea></label><button id="gerar-analitico-ia" class="primary-action" type="button">Gerar análise pedagógica</button><div id="resposta-analitico-ia"></div></section>`);
    $("#gerar-analitico-ia")?.addEventListener("click", async () => {
      const botao = $("#gerar-analitico-ia"), resposta = $("#resposta-analitico-ia");
      botao.disabled = true; botao.textContent = "Analisando..."; resposta.innerHTML = "";
      try {
        const retorno = await fetch("/api/analitico-ia", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resumo: resumoIa, pergunta: $("#pergunta-analitico-ia").value.trim() }) });
        const corpo = await retorno.json().catch(() => ({}));
        if (!retorno.ok) throw new Error(corpo.error || "Não foi possível gerar a análise.");
        resposta.innerHTML = `<article class="ai-answer">${escapeHtml(corpo.texto || "").replace(/\n/g, "<br>")}</article>`;
      } catch (erro) { resposta.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
      finally { botao.disabled = false; botao.textContent = "Gerar análise pedagógica"; }
    });
  };
  const aplicarPeriodo = () => {
    const escolha = $("#analise-periodo").value;
    if (escolha === "personalizado") return;
    const fim = new Date(), comeco = new Date();
    if (escolha === "tudo") comeco.setFullYear(2024, 0, 1); else comeco.setDate(fim.getDate() - Number(escolha));
    $("#analise-inicio").value = comeco.toISOString().slice(0, 10);
    $("#analise-fim").value = fim.toISOString().slice(0, 10);
    render();
  };
  document.querySelectorAll("[data-analise]").forEach((botao) => botao.addEventListener("click", () => { aba = botao.dataset.analise; document.querySelectorAll("[data-analise]").forEach((item) => item.classList.toggle("active", item === botao)); render(); })); $("#analise-periodo").addEventListener("change", aplicarPeriodo); $("#atualizar-analise").addEventListener("click", render); render();
}

function rodizioSalvoMarkup(base) {
  return `<section class="section-title"><div><h2>Rodízio salvo</h2><p>Este é o retrato da data. Use “Corrigir” somente se houve erro de lançamento; a versão anterior ficará registrada.</p></div><div class="scale-actions"><button id="ampliar-rodizio" class="secondary-action" type="button">Ampliar</button><button id="baixar-rodizio" class="primary-action" type="button">Baixar imagem</button><button id="editar-rodizio" class="secondary-action" type="button">Corrigir rodízio</button></div></section>${muralRodizio(base.escala, base.data)}<div id="edicao-rodizio"></div>`;
}

async function baixarImagemRodizio(mural, data) {
  if (!window.html2canvas) throw new Error("A ferramenta de imagem ainda está carregando. Tente novamente em alguns segundos.");
  // A cópia fica fora da tela, sempre com largura de computador. Assim a
  // imagem não depende da rolagem, do zoom ou da largura do celular.
  const areaExportacao = document.createElement("div");
  areaExportacao.style.cssText = "position:fixed;left:-10000px;top:0;width:1320px;padding:0;background:#fff;z-index:-1;";
  const copia = mural.cloneNode(true);
  copia.removeAttribute("id");
  copia.style.width = "1320px";
  copia.style.minWidth = "1320px";
  copia.style.marginTop = "0";
  areaExportacao.appendChild(copia);
  document.body.appendChild(areaExportacao);
  try {
    const canvas = await window.html2canvas(copia, { scale: 2, backgroundColor: "#ffffff", width: 1320, windowWidth: 1320, windowHeight: copia.scrollHeight });
    const link = document.createElement("a");
    link.download = `Rodizio_${data.replaceAll("/", "-")}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  } finally {
    areaExportacao.remove();
  }
}

function ligarGerador(base, modelo, preparacao, fixasSalvas = []) {
  const manual = $("#rotacao-manual"), opcoes = $("#rotacao-opcoes"), turma = $("#turma-rotacao"), previa = $("#previa-rotacao"), saidas = $("#professoras-saida"), detalhesSaidas = $("#saidas-detalhes");
  const atualizarPrevia = () => {
    if (!manual.checked) { previa.innerHTML = ""; return; }
    const valor = turma.value;
    // Compatível com a regra do app.py: nesta opção, a turma anterior à
    // escolhida é a referência que começa em Teoria. A prévia precisa usar
    // exatamente a mesma transformação aplicada ao gerar a escala.
    const individual = document.querySelector('input[name="criterio-rotacao"]:checked')?.value === "individual";
    const comecaTeoria = individual
      ? preparacao.turmas[(preparacao.turmas.indexOf(valor) - 1 + preparacao.turmas.length) % preparacao.turmas.length]
      : valor;
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
    let turmaTeoria = null;
    if (manual.checked) {
      turmaTeoria = turma.value;
      if (document.querySelector('input[name="criterio-rotacao"]:checked')?.value === "individual") {
        turmaTeoria = preparacao.turmas[(preparacao.turmas.indexOf(turmaTeoria) - 1 + preparacao.turmas.length) % preparacao.turmas.length];
      }
    }
    const resultado = window.RodizioEngine.gerar({ modelo, data: base.data, turmasReais: base.turmas, professoras: base.professoras, folgas: base.folga?.professoras || [], saidas: saidasMap, fixas, coletivas, turmaInicioTeoria: turmaTeoria, usarFixas: Boolean($("#usar-fixas")?.checked), escalasAnteriores: base.escalasAnteriores });
    if (resultado.erros.length) { feedback.innerHTML = `<div class="action-error"><strong>O rodízio não foi salvo.</strong><br>${resultado.erros.map(escapeHtml).join("<br>")}</div>`; return; }
    feedback.innerHTML = `${muralRodizio(resultado.escala, base.data)}<button id="confirmar-geracao" class="primary-action wide-action" type="button">Confirmar e salvar rodízio</button>`;
    $("#confirmar-geracao").addEventListener("click", async () => { try { await window.GemData.salvarEscala($("#rodizio-data").value, resultado.escala, modelo.id); await renderRodizio($("#page-content")); } catch (error) { feedback.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); } });
  });
}

function ligarAcoesEscala(base, modelo) {
  $("#baixar-rodizio")?.addEventListener("click", async () => { try { await baixarImagemRodizio($("#mural-rodizio"), base.data); } catch (erro) { alert(erro.message || "Não foi possível gerar a imagem do rodízio."); } });
  $("#ampliar-rodizio")?.addEventListener("click", () => { document.body.insertAdjacentHTML("beforeend", `<div class="mural-modal" id="mural-modal"><button aria-label="Fechar" class="modal-close">×</button>${muralRodizio(base.escala, base.data)}</div>`); $("#mural-modal").addEventListener("click", (event) => { if (event.target.id === "mural-modal" || event.target.classList.contains("modal-close")) $("#mural-modal").remove(); }); });
  $("#editar-rodizio")?.addEventListener("click", () => { const horarios = [...new Set(base.escala.flatMap((linha) => Object.keys(linha).filter((chave) => !["Aluna", "_detalhes"].includes(chave))))]; $("#edicao-rodizio").innerHTML = `<section class="panel edit-scale"><h3>Corrigir rodízio</h3><p>Edite somente a sala/professora incorreta. Os detalhes pedagógicos e a turma são preservados; informe o motivo da correção antes de salvar.</p><div class="table-wrap"><table class="scale-table"><thead><tr><th>Aluna</th>${horarios.map((hora) => `<th>${escapeHtml(hora)}</th>`).join("")}</tr></thead><tbody>${base.escala.map((linha, i) => `<tr><th>${escapeHtml(linha.Aluna)}</th>${horarios.map((hora) => `<td><input data-escala="${i}" data-hora="${escapeHtml(hora)}" value="${escapeHtml(linha[hora] || "")}"></td>`).join("")}</tr>`).join("")}</tbody></table></div><label>Motivo da correção<input id="motivo-edicao" placeholder="Ex.: troca de professora confirmada pela Secretaria"></label><button id="salvar-edicao" class="primary-action" type="button">Salvar correção</button></section>`; $("#salvar-edicao").addEventListener("click", async () => { const corrigida = structuredClone(base.escala); document.querySelectorAll("[data-escala]").forEach((item) => { corrigida[Number(item.dataset.escala)][item.dataset.hora] = item.value.trim(); }); try { await window.GemData.salvarEscala($("#rodizio-data").value, corrigida, modelo.id, $("#motivo-edicao").value); await renderRodizio($("#page-content")); } catch (error) { $("#edicao-rodizio").insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(error.message)}</div>`); } }); });
}

async function renderMasterGems(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ADMINISTRAÇÃO DA PLATAFORMA</p><h2>GEMs cadastrados</h2><p>Cada GEM novo usa uma base Supabase própria. O Vila Verde e o Streamlit permanecem isolados na base atual.</p></section><section class="panel compact-panel"><h2>Passo a passo para criar uma unidade</h2><ol class="report-list"><li><strong>Uma única vez na base principal:</strong> execute <code>011_secretarias_dos_gems.sql</code> e <code>013_notificacoes_multi_gem.sql</code>. Não repita esses arquivos a cada novo GEM.</li><li><strong>Para cada novo Supabase:</strong> execute primeiro <code>012_base_pedagogica_novo_gem.sql</code> e depois <code>001_validar_login_professoras_alunas.sql</code>.</li><li>Cadastre abaixo o nome, identificador, URL e chave anon do GEM.</li><li>Em <strong>Secretarias dos GEMs</strong>, crie o login da Secretaria. Ela já terá todas as telas administrativas da unidade.</li><li>A Secretaria cadastra professoras e alunas em <strong>Turmas e pessoas</strong>; cada uma já sai com login e senha inicial.</li></ol><p class="hint">Nunca execute 011 ou 013 nas bases novas dos GEMs.</p></section><div class="section-title"><h2>Novo GEM</h2><p>Informe a conexão do projeto Supabase exclusivo já criado para esta unidade.</p></div><section class="panel"><div class="master-gem-form"><label>Nome do GEM<input id="gem-nome" placeholder="Ex.: GEM Musical Central"></label><label>Identificador do link<input id="gem-slug" placeholder="Ex.: gem-central"></label><label>URL do Supabase<input id="gem-supabase-url" type="url" placeholder="https://projeto.supabase.co"></label><label>Chave anon do Supabase<input id="gem-supabase-anon" autocomplete="off" placeholder="Chave pública anon"></label><button id="criar-gem" class="primary-action" type="button">Cadastrar GEM e conexão</button></div><p class="hint">A chave anon é pública; senhas e service role nunca são salvas aqui. Antes do primeiro acesso, execute as migrations do GEM nessa nova base.</p><p id="gem-feedback" class="hidden" role="status"></p></section><div class="section-title"><h2>Unidades</h2><p>Somente a Master visualiza esta lista.</p></div><section class="panel"><div id="gem-lista" class="gem-list"><div class="empty">Carregando GEMs...</div></div></section>`;
  const lista = $("#gem-lista");
  const carregar = async () => {
    try {
      const gems = await window.GemData.listarGems();
      lista.innerHTML = gems.length ? gems.map((gem) => { const origemPublica = String(window.GEM_SUPABASE?.publicUrl || window.location.origin).replace(/\/$/, ""); const link = `${origemPublica}/?gem=${encodeURIComponent(gem.slug)}`; const conectado = Boolean(gem.supabase_url && gem.supabase_anon_key) || gem.slug === "vila-verde"; const principal = gem.slug === "vila-verde"; return `<article class="gem-row"><div><strong>${escapeHtml(gem.nome)}</strong><span>${escapeHtml(gem.slug)} · ${conectado ? "Base Supabase vinculada" : "Base ainda não vinculada"}</span><small class="gem-login-link">${escapeHtml(link)}</small>${principal ? "<small>Unidade principal: não pode ser desativada ou excluída nesta tela.</small>" : ""}</div><div class="person-actions"><button class="secondary-action" type="button" data-copiar-link-gem="${escapeHtml(link)}">Copiar link</button><span class="badge ${gem.ativo ? "" : "inactive"}">${gem.ativo ? "Ativo" : "Inativo"}</span>${principal ? "" : `<button class="secondary-action" type="button" data-status-gem="${escapeHtml(gem.id)}">${gem.ativo ? "Desativar" : "Reativar"}</button><button class="secondary-action danger-action" type="button" data-excluir-gem="${escapeHtml(gem.id)}">Excluir</button>`}</div></article>`; }).join("") : `<div class="empty">Nenhum GEM cadastrado.</div>`;
      lista.querySelectorAll("[data-copiar-link-gem]").forEach((botao) => botao.addEventListener("click", async () => { try { await navigator.clipboard.writeText(botao.dataset.copiarLinkGem); botao.textContent = "Link copiado ✓"; } catch (_) { prompt("Copie o link do GEM:", botao.dataset.copiarLinkGem); } }));
      lista.querySelectorAll("[data-status-gem]").forEach((botao) => botao.addEventListener("click", async () => {
        const gem = gems.find((item) => String(item.id) === String(botao.dataset.statusGem));
        if (!gem || !confirm(`${gem.ativo ? "Desativar" : "Reativar"} o GEM “${gem.nome}”? ${gem.ativo ? "Os dados serão preservados e novos logins ficarão bloqueados." : "Os logins voltarão a ser permitidos."}`)) return;
        botao.disabled = true;
        try { await window.GemData.alterarStatusGem(gem.id, !gem.ativo); await carregar(); }
        catch (erro) { alert(erro.message); botao.disabled = false; }
      }));
      lista.querySelectorAll("[data-excluir-gem]").forEach((botao) => botao.addEventListener("click", async () => {
        const gem = gems.find((item) => String(item.id) === String(botao.dataset.excluirGem));
        if (!gem) return;
        const confirmacao = prompt(`Esta ação remove o cadastro da plataforma e as Secretarias vinculadas. A base Supabase e as fotos no R2 não serão apagadas.\n\nPara confirmar, digite EXCLUIR ${gem.slug}`);
        if (confirmacao !== `EXCLUIR ${gem.slug}`) return;
        botao.disabled = true;
        try { await window.GemData.removerGem(gem.id, gem.slug); await carregar(); }
        catch (erro) { alert(erro.message); botao.disabled = false; }
      }));
    } catch (error) { lista.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
  };
  $("#criar-gem").addEventListener("click", async () => {
    const feedback = $("#gem-feedback");
    feedback.className = "hidden";
    try {
      await window.GemData.criarGem($("#gem-nome").value, $("#gem-slug").value, { url: $("#gem-supabase-url").value, anonKey: $("#gem-supabase-anon").value });
      feedback.textContent = "GEM cadastrado com sucesso.";
      feedback.className = "action-ok";
      $("#gem-nome").value = ""; $("#gem-slug").value = ""; $("#gem-supabase-url").value = ""; $("#gem-supabase-anon").value = "";
      await carregar();
    } catch (error) { feedback.textContent = error.message; feedback.className = "action-error"; }
  });
  await carregar();
}

async function renderMasterUsuarios(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ADMINISTRAÇÃO DA PLATAFORMA</p><h2>Usuários mestres</h2><p>Contas Master administram GEMs, mas não entram nos dados pedagógicos de nenhuma unidade sem receber acesso específico.</p></section><section class="panel"><div id="master-usuarios-lista"><div class="empty">Carregando usuários...</div></div></section>`;
  const lista = $("#master-usuarios-lista");
  try {
    const { usuarios } = await window.GemData.dadosPlataformaMaster();
    lista.innerHTML = usuarios.length ? usuarios.map((usuario) => `<article class="method-row"><div><strong>${escapeHtml(usuario.nome)}</strong><span>${escapeHtml(usuario.email)} · ${escapeHtml(usuario.papel)}</span><span>${usuario.ativo ? "Ativa" : "Bloqueada"} · ${usuario.status_convite === "ativo" ? "Login configurado" : "Aguardando criação da senha"}</span></div><span class="badge ${usuario.ativo ? "" : "inactive"}">${usuario.status_convite === "ativo" ? "Ativo" : "Pendente"}</span></article>`).join("") : `<div class="empty">Nenhuma conta Master cadastrada.</div>`;
  } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
}

async function renderMasterSecretarias(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ADMINISTRAÇÃO DA PLATAFORMA</p><h2>Secretarias dos GEMs</h2><p>Cadastre e edite os acessos das Secretarias. Cada conta entra somente pelo link do GEM escolhido e recebe todas as telas administrativas daquela unidade.</p></section><section class="panel"><h3>Cadastrar usuária Secretaria</h3><div class="master-gem-form"><label>GEM<select id="secretaria-gem"></select></label><label>Nome completo<input id="secretaria-nome" placeholder="Ex.: Maria da Silva"></label><label>Usuário ou e-mail<input id="secretaria-login" autocomplete="username" placeholder="Ex.: maria ou maria@email.com"></label><label>Senha inicial<input id="secretaria-senha" type="password" autocomplete="new-password" placeholder="Mínimo de 6 caracteres"></label><button id="cadastrar-secretaria-gem" class="primary-action" type="button">Cadastrar Secretaria</button></div><p id="secretaria-gem-feedback" class="hidden" role="status"></p></section><section class="panel"><div class="section-title"><div><h3>Usuárias cadastradas</h3><p>Use Editar para alterar nome, usuário, senha ou bloquear o acesso sem apagar o histórico.</p></div><label>Filtrar por GEM<select id="filtro-secretaria-gem"><option value="">Todos os GEMs</option></select></label></div><div id="lista-secretarias-gems"><div class="empty">Carregando Secretarias...</div></div></section>`;
  const destino = $("#lista-secretarias-gems");
  let base = { gems: [], secretarias: [] };
  const nomeGem = (gemId) => base.gems.find((gem) => gem.id === gemId)?.nome || "GEM removido";
  const preencherSeletores = () => {
    // GEMs criados antes da coluna `ativo` podem chegar sem esse campo.
    // Eles continuam disponíveis, salvo quando foram desativados explicitamente.
    const gemsDisponiveis = base.gems.filter((gem) => gem.ativo !== false);
    const opcoes = gemsDisponiveis.map((gem) => `<option value="${escapeHtml(gem.id)}">${escapeHtml(gem.nome)}</option>`).join("");
    $("#secretaria-gem").innerHTML = `<option value="">Escolha o GEM</option>${opcoes}`;
    $("#filtro-secretaria-gem").innerHTML = `<option value="">Todos os GEMs</option>${opcoes}`;
  };
  const mostrar = () => {
    const filtro = $("#filtro-secretaria-gem").value;
    const lista = base.secretarias.filter((item) => !filtro || item.gem_id === filtro).sort((a, b) => nomeGem(a.gem_id).localeCompare(nomeGem(b.gem_id), "pt-BR") || a.nome.localeCompare(b.nome, "pt-BR"));
    destino.innerHTML = lista.length ? lista.map((item) => `<article class="person-row person-card"><div class="person-identity"><span class="person-photo initials">${escapeHtml(item.nome.slice(0, 1))}</span><div><strong>${escapeHtml(item.nome)}</strong><span>${escapeHtml(nomeGem(item.gem_id))} · Login: ${escapeHtml(item.login)}</span></div></div><span class="badge ${item.ativo ? "" : "inactive"}">${item.ativo ? "Ativa" : "Bloqueada"}</span><div class="person-actions"><button class="secondary-action" type="button" data-editar-secretaria="${escapeHtml(item.id)}">Editar</button></div><div class="person-editor hidden" data-editor-secretaria="${escapeHtml(item.id)}"><label>GEM<select data-secretaria-campo="gem_id">${base.gems.filter((gem) => gem.ativo !== false || gem.id === item.gem_id).map((gem) => `<option value="${escapeHtml(gem.id)}" ${gem.id === item.gem_id ? "selected" : ""}>${escapeHtml(gem.nome)}</option>`).join("")}</select></label><label>Nome<input data-secretaria-campo="nome" value="${escapeHtml(item.nome)}"></label><label>Usuário ou e-mail<input data-secretaria-campo="login" value="${escapeHtml(item.login)}"></label><label>Nova senha <small>(deixe vazia para manter a atual)</small><input data-secretaria-campo="senha" type="password" autocomplete="new-password" placeholder="Nova senha"></label><label class="checkbox-row"><input data-secretaria-campo="ativo" type="checkbox" ${item.ativo ? "checked" : ""}> Acesso ativo</label><button class="primary-action" type="button" data-salvar-secretaria="${escapeHtml(item.id)}">Salvar alterações</button></div></article>`).join("") : `<div class="empty">Nenhuma Secretaria cadastrada para este filtro.</div>`;
    destino.querySelectorAll("[data-editar-secretaria]").forEach((botao) => botao.addEventListener("click", () => destino.querySelector(`[data-editor-secretaria="${botao.dataset.editarSecretaria}"]`)?.classList.toggle("hidden")));
    destino.querySelectorAll("[data-salvar-secretaria]").forEach((botao) => botao.addEventListener("click", async () => {
      const item = base.secretarias.find((secretaria) => secretaria.id === botao.dataset.salvarSecretaria);
      const editor = destino.querySelector(`[data-editor-secretaria="${botao.dataset.salvarSecretaria}"]`);
      const dados = { id: item?.id, gemId: editor.querySelector('[data-secretaria-campo="gem_id"]').value, nome: editor.querySelector('[data-secretaria-campo="nome"]').value.trim(), login: editor.querySelector('[data-secretaria-campo="login"]').value.trim(), senha: editor.querySelector('[data-secretaria-campo="senha"]').value, ativo: editor.querySelector('[data-secretaria-campo="ativo"]').checked };
      botao.disabled = true;
      try { await window.GemData.salvarSecretariaGem(dados); base = await window.GemData.dadosSecretariasGems(); mostrar(); }
      catch (erro) { editor.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(erro.message)}</div>`); botao.disabled = false; }
    }));
  };
  try {
    base = await window.GemData.dadosSecretariasGems();
    preencherSeletores(); mostrar();
    $("#filtro-secretaria-gem").addEventListener("change", mostrar);
    $("#cadastrar-secretaria-gem").addEventListener("click", async () => {
      const botao = $("#cadastrar-secretaria-gem"), feedback = $("#secretaria-gem-feedback");
      botao.disabled = true; feedback.className = "hidden";
      try {
        await window.GemData.salvarSecretariaGem({ gemId: $("#secretaria-gem").value, nome: $("#secretaria-nome").value.trim(), login: $("#secretaria-login").value.trim(), senha: $("#secretaria-senha").value, ativo: true });
        feedback.textContent = "Secretaria cadastrada. Ela já pode entrar pelo link do GEM selecionado."; feedback.className = "action-ok";
        $("#secretaria-nome").value = ""; $("#secretaria-login").value = ""; $("#secretaria-senha").value = "";
        base = await window.GemData.dadosSecretariasGems(); preencherSeletores(); mostrar();
      } catch (erro) { feedback.textContent = erro.message; feedback.className = "action-error"; }
      botao.disabled = false;
    });
  } catch (erro) { destino.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
}

async function renderMasterVisao(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">PLATAFORMA GEM</p><h2>Visão da plataforma</h2><p>Resumo das unidades e dos acessos já configurados. Os dados pedagógicos de cada GEM permanecem separados.</p></section><div id="master-visao"><div class="empty">Carregando plataforma...</div></div>`;
  const destino = $("#master-visao");
  try {
    const { gems, usuarios, acessos } = await window.GemData.dadosPlataformaMaster();
    const porGem = Object.fromEntries(gems.map((gem) => [gem.id, acessos.filter((acesso) => acesso.gem_id === gem.id && acesso.ativo !== false)]));
    destino.innerHTML = `<div class="grid"><div class="metric"><strong>${gems.length}</strong><span>GEM(s) cadastrado(s)</span></div><div class="metric"><strong>${gems.filter((gem) => gem.ativo).length}</strong><span>GEM(s) ativo(s)</span></div><div class="metric"><strong>${usuarios.filter((usuario) => usuario.status_convite === "ativo" && usuario.ativo).length}</strong><span>Master(s) ativo(s)</span></div></div><section class="panel compact-panel"><h3>Unidades</h3><div class="lesson-list">${gems.length ? gems.map((gem) => `<article class="method-row"><div><strong>${escapeHtml(gem.nome)}</strong><span>${escapeHtml(gem.slug)} · ${porGem[gem.id]?.length || 0} acesso(s) vinculado(s)</span></div><span class="badge ${gem.ativo ? "" : "inactive"}">${gem.ativo ? "Ativo" : "Inativo"}</span></article>`).join("") : `<div class="empty">Nenhum GEM cadastrado.</div>`}</div></section>`;
  } catch (erro) { destino.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
}

async function renderAjustes(content) {
  content.innerHTML = `<section class="intro-card"><p class="eyebrow">ADMINISTRAÇÃO DO HISTÓRICO</p><h2>Ajustes</h2><p>Use esta área somente para corrigir registros antigos. O rodízio e o histórico das outras alunas não são alterados automaticamente.</p></section><section class="panel"><h3>🧹 Registros órfãos do rodízio</h3><p class="hint">São linhas antigas sem Tipo, criadas por uma versão anterior do rodízio. Primeiro confira a quantidade; a exclusão pede confirmação.</p><button id="contar-orfaos" class="secondary-action" type="button">Verificar registros órfãos</button><div id="orfaos-retorno"></div></section><section class="panel"><h3>📝 Ajustar registro por aluna</h3><p class="hint">Escolha uma aluna, confira os dados e exclua somente o registro selecionado.</p><label>Aluna<select id="ajuste-aluna"></select></label><div id="ajuste-registros" class="lesson-list"><div class="empty">Carregando registros...</div></div></section><section class="panel"><h3>🔎 Auditar rodízios salvos</h3><p class="hint">Confere as escalas reais já salvas: professora ou sala duplicada no mesmo horário, professora fixa e repetição imediata de professora para a aluna.</p><button id="auditar-rodizio" class="secondary-action" type="button">Rodar auditoria</button><div id="auditoria-rodizio"></div></section>`;
  const seletor = $("#ajuste-aluna"), lista = $("#ajuste-registros"), retornoOrfaos = $("#orfaos-retorno");
  const dataParaOrdenar = (valor) => { const texto = String(valor || ""); if (/^\d{4}-\d{2}-\d{2}/.test(texto)) return texto.slice(0, 10); const [dia, mes, ano] = texto.split("/"); return ano ? `${ano}-${mes}-${dia}` : ""; };
  const iconeTipo = (tipo) => { const texto = String(tipo || "").toUpperCase(); return texto.includes("PRATICA") ? "🎹" : texto.includes("TEORIA") ? "📚" : texto.includes("SOLFEJO") || texto.includes("CANTO") ? "🔊" : texto.includes("CASA") ? "🏠" : texto === "CHAMADA" ? "✅" : "📌"; };
  let dados;
  const mostrarRegistros = () => {
    const aluna = seletor.value;
    const registros = dados.historico.filter((registro) => registro.Aluna === aluna).sort((a, b) => dataParaOrdenar(b.Data).localeCompare(dataParaOrdenar(a.Data)) || Number(b.id) - Number(a.id));
    lista.innerHTML = registros.length ? registros.map((registro, indice) => `<article class="student-report"><div class="report-header"><h3>${iconeTipo(registro.Tipo)} ${escapeHtml(registro.Tipo || "Sem tipo")}</h3><span>${escapeHtml(registro.Data || "Sem data")}</span></div><div class="report-record"><p><strong>Instrutora:</strong> ${escapeHtml(registro.Instrutora || registro.Secretaria || "—")}</p><p><strong>Status:</strong> ${escapeHtml(registro.Status || "—")}</p><p><strong>Conteúdo:</strong> ${escapeHtml(registro.Licao_Casa || registro.Licao_Atual || registro.Observacao || "—")}</p></div><button class="secondary-action danger-action" type="button" data-remover-registro="${indice}">Excluir este registro</button></article>`).join("") : `<div class="empty">Nenhum registro encontrado para esta aluna.</div>`;
    lista.querySelectorAll("[data-remover-registro]").forEach((botao) => botao.addEventListener("click", async () => {
      const registro = registros[Number(botao.dataset.removerRegistro)];
      if (!registro || !confirm(`Excluir este registro de ${registro.Data || "data não informada"}? Esta ação não pode ser desfeita.`)) return;
      botao.disabled = true;
      try { await window.GemData.removerRegistroHistorico(registro.id); dados = await window.GemData.dadosAjustes(); mostrarRegistros(); }
      catch (erro) { alert(erro.message); botao.disabled = false; }
    }));
  };
  try {
    dados = await window.GemData.dadosAjustes();
    seletor.innerHTML = dados.alunas.map((aluna) => `<option value="${escapeHtml(aluna.nome)}">${escapeHtml(aluna.nome)}${aluna.ativo === false ? " · inativa" : ""}</option>`).join("");
    seletor.addEventListener("change", mostrarRegistros);
    mostrarRegistros();
  } catch (erro) { lista.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
  $("#contar-orfaos").addEventListener("click", async () => {
    const botao = $("#contar-orfaos"); botao.disabled = true; retornoOrfaos.innerHTML = "";
    try {
      const quantidade = await window.GemData.contarRegistrosOrfaos();
      if (!quantidade) { retornoOrfaos.innerHTML = `<div class="action-ok">✅ Nenhum registro órfão encontrado.</div>`; return; }
      retornoOrfaos.innerHTML = `<div class="action-error">⚠️ ${quantidade} registro(s) sem Tipo encontrado(s).</div><button id="apagar-orfaos" class="secondary-action danger-action" type="button">Apagar somente estes ${quantidade} registro(s)</button>`;
      $("#apagar-orfaos").addEventListener("click", async () => {
        if (!confirm(`Apagar ${quantidade} registro(s) sem Tipo? Esta ação não pode ser desfeita.`)) return;
        const apagar = $("#apagar-orfaos"); apagar.disabled = true;
        try { await window.GemData.limparRegistrosOrfaos(); retornoOrfaos.innerHTML = `<div class="action-ok">✅ Registros órfãos apagados.</div>`; }
        catch (erro) { retornoOrfaos.insertAdjacentHTML("beforeend", `<div class="action-error">${escapeHtml(erro.message)}</div>`); apagar.disabled = false; }
      });
    } catch (erro) { retornoOrfaos.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
    finally { botao.disabled = false; }
  });
  $("#auditar-rodizio").addEventListener("click", async () => {
    const botao = $("#auditar-rodizio"), destino = $("#auditoria-rodizio"); botao.disabled = true; destino.innerHTML = `<div class="empty">Auditando escalas salvas...</div>`;
    try {
      const { escalas, fixas } = await window.GemData.dadosAuditoriaRodizio();
      const dataEscala = (id) => { const [dia, mes, ano] = String(id || "").split("/"); return ano ? `${ano}-${mes}-${dia}` : ""; };
      const normalizarNome = (nome) => String(nome || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
      const ordenadas = escalas.filter((item) => Array.isArray(item.escala) && item.escala.length).sort((a, b) => dataEscala(a.id).localeCompare(dataEscala(b.id)));
      if (!ordenadas.length) { destino.innerHTML = `<div class="empty">Nenhum rodízio salvo para auditar.</div>`; return; }
      const fixasPorAluna = Object.fromEntries(fixas.map((item) => [normalizarNome(item.aluna), item.professora]));
      const problemas = [], ultimaProfessora = new Map();
      const extrair = (linha, horario) => {
        const valor = String(linha[horario] || ""), detalhe = linha._detalhes?.[horario] || {};
        if (!valor.includes("|")) return null;
        const sala = valor.split("|")[0].trim(), salaMaiuscula = sala.toUpperCase();
        if (!detalhe.individual && (salaMaiuscula.includes("SALA 8") || salaMaiuscula.includes("SALA 9") || !salaMaiuscula.startsWith("SALA"))) return null;
        if (!salaMaiuscula.startsWith("SALA") || salaMaiuscula.includes("SALA 8") || salaMaiuscula.includes("SALA 9") || /SECRETARIA|TODAS/i.test(valor)) return null;
        const professora = String(detalhe.professoras_componentes?.Prática || valor.split("|").slice(1).join("|")).trim();
        return professora ? { sala, professora } : null;
      };
      for (const escala of ordenadas) {
        const ocupacao = new Map();
        for (const linha of escala.escala) {
          const aluna = linha.Aluna;
          if (!aluna) continue;
          for (const horario of Object.keys(linha).filter((chave) => !["Aluna", "_detalhes"].includes(chave))) {
            const alocacao = extrair(linha, horario);
            if (!alocacao) continue;
            const chave = horario, usado = ocupacao.get(chave) || { professoras: new Set(), salas: new Set() };
            if (usado.professoras.has(normalizarNome(alocacao.professora))) problemas.push({ data: escala.id, aluna, regra: "Professora em duplicidade", detalhe: `${alocacao.professora} aparece em duas práticas no mesmo horário.` });
            if (usado.salas.has(alocacao.sala.toUpperCase())) problemas.push({ data: escala.id, aluna, regra: "Sala em duplicidade", detalhe: `${alocacao.sala} aparece com mais de uma aluna no mesmo horário.` });
            usado.professoras.add(normalizarNome(alocacao.professora)); usado.salas.add(alocacao.sala.toUpperCase()); ocupacao.set(chave, usado);
            const fixa = fixasPorAluna[normalizarNome(aluna)];
            if (fixa && normalizarNome(fixa) !== normalizarNome(alocacao.professora)) problemas.push({ data: escala.id, aluna, regra: "Professora fixa", detalhe: `Deveria estar com ${fixa}, mas está com ${alocacao.professora}.` });
            const anterior = ultimaProfessora.get(aluna);
            if (anterior && anterior.data !== escala.id && normalizarNome(anterior.professora) === normalizarNome(alocacao.professora)) problemas.push({ data: escala.id, aluna, regra: "Professora repetida", detalhe: `${alocacao.professora} também atendeu a aluna no rodízio anterior.` });
            ultimaProfessora.set(aluna, { data: escala.id, professora: alocacao.professora });
          }
        }
      }
      const ultimaData = ordenadas.at(-1).id, doUltimo = problemas.filter((item) => item.data === ultimaData);
      destino.innerHTML = doUltimo.length ? `<div class="action-error">⚠️ ${doUltimo.length} possível(is) inconsistência(s) no último rodízio (${escapeHtml(ultimaData)}).</div><div class="lesson-list">${doUltimo.map((item) => `<article class="report-record"><strong>${escapeHtml(item.regra)} · ${escapeHtml(item.aluna)}</strong><p>${escapeHtml(item.detalhe)}</p></article>`).join("")}</div>` : `<div class="action-ok">✅ Rodízio consistente: nenhuma duplicidade, quebra de professora fixa ou repetição imediata foi encontrada em ${escapeHtml(ultimaData)}.</div>`;
    } catch (erro) { destino.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; }
    finally { botao.disabled = false; }
  });
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
  avatar.dataset.fotoZoom = url || "";
  avatar.dataset.fotoTitulo = nome || "Foto de perfil";
  avatar.title = url ? "Ampliar foto" : "";
}

function abrirZoomFoto(url, titulo = "Foto") {
  if (!url) return;
  document.querySelector(".photo-modal")?.remove();
  const modal = document.createElement("div");
  modal.className = "photo-modal";
  modal.innerHTML = `<div class="photo-modal-card" role="dialog" aria-modal="true" aria-label="Foto ampliada"><button class="modal-close" type="button" aria-label="Fechar">×</button><img src="${escapeHtml(url)}" alt="Foto ampliada de ${escapeHtml(titulo)}"><strong>${escapeHtml(titulo)}</strong></div>`;
  const fechar = () => modal.remove();
  modal.addEventListener("click", (evento) => { if (evento.target === modal) fechar(); });
  modal.querySelector(".modal-close").addEventListener("click", fechar);
  document.body.appendChild(modal);
}

function abrirTrocaFotoProfessora() {
  document.querySelector(".profile-photo-modal")?.remove();
  const modal = document.createElement("div");
  modal.className = "photo-modal profile-photo-modal";
  modal.innerHTML = `<section class="profile-photo-card" role="dialog" aria-modal="true" aria-label="Alterar foto de perfil"><button class="modal-close" type="button" aria-label="Fechar">×</button><h3>Alterar minha foto</h3><p>A imagem será salva no R2 e aparecerá no seu perfil.</p><label>Nova foto<input data-minha-foto type="file" accept="image/jpeg,image/png,image/webp"></label><button data-salvar-minha-foto class="primary-action" type="button">Salvar foto</button><div data-retorno-foto></div></section>`;
  const fechar = () => modal.remove();
  modal.addEventListener("click", (evento) => { if (evento.target === modal) fechar(); });
  modal.querySelector(".modal-close").addEventListener("click", fechar);
  modal.querySelector("[data-salvar-minha-foto]").addEventListener("click", async (evento) => {
    const botao = evento.currentTarget, retorno = modal.querySelector("[data-retorno-foto]"), arquivo = modal.querySelector("[data-minha-foto]").files[0];
    botao.disabled = true;
    try {
      const perfil = await window.GemData.atualizarMinhaFotoProfessora(state.name, arquivo);
      aplicarAvatar(perfil.fotoUrl, state.name);
      retorno.innerHTML = `<div class="action-ok">Foto atualizada.</div>`;
      setTimeout(fechar, 700);
    } catch (erro) { retorno.innerHTML = `<div class="action-error">${escapeHtml(erro.message)}</div>`; botao.disabled = false; }
  });
  document.body.appendChild(modal);
}

document.addEventListener("click", (evento) => {
  const foto = evento.target.closest("[data-foto-zoom]");
  if (!foto) return;
  abrirZoomFoto(foto.dataset.fotoZoom, foto.dataset.fotoTitulo || "Foto");
});

function aplicarNomeGem(nome) {
  const gem = String(nome || "GEM Musical").trim();
  const palavras = gem.replace(/^GEM\s+/i, "").split(/\s+/).filter(Boolean);
  const exibicaoLateral = palavras.length > 1 ? `${palavras.slice(0, -1).join(" ")}<br>${palavras.at(-1)}` : palavras[0] || "GEM";
  $("#titulo-login").textContent = palavras.join(" ") || "GEM";
  document.querySelector(".sidebar-brand strong").innerHTML = escapeHtml(exibicaoLateral).replace("&lt;br&gt;", "<br>");
  document.querySelector(".topbar .eyebrow").textContent = gem.toUpperCase();
  document.title = `${gem} — gestão musical`;
}

function chavePushParaBytes(chave) {
  const ajustada = `${chave}`.replace(/-/g, "+").replace(/_/g, "/");
  const preenchida = ajustada.padEnd(ajustada.length + (4 - ajustada.length % 4) % 4, "=");
  const binaria = atob(preenchida);
  return Uint8Array.from(binaria, (caractere) => caractere.charCodeAt(0));
}

async function ativarNotificacoes() {
  const botao = $("#ativar-notificacoes");
  if (!["Aluna", "Professora"].includes(state.role)) return;
  if (!("Notification" in window) || !("serviceWorker" in navigator)) { alert("Este navegador não oferece notificações para o aplicativo."); return; }
  botao.disabled = true;
  try {
    const permissao = await Notification.requestPermission();
    if (permissao !== "granted") throw new Error("Você precisa permitir notificações para receber os lembretes.");
    const respostaChave = await fetch("/api/vapid-public-key", { cache: "no-store" });
    if (!respostaChave.ok) throw new Error("As notificações ainda não foram configuradas pela Administração.");
    const { publicKey } = await respostaChave.json();
    const registro = await navigator.serviceWorker.ready;
    const subscription = await registro.pushManager.getSubscription() || await registro.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: chavePushParaBytes(publicKey) });
    const contextoGem = await window.GemData.gemAtivo();
    const resposta = await fetch("/api/push-subscribe", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ usuario: state.role === "Secretaria" ? "Secretaria" : state.name, perfil: state.role, gem: contextoGem.slug, subscription }) });
    if (!resposta.ok) throw new Error("Não foi possível registrar este aparelho para os lembretes.");
    botao.textContent = "🔔 Lembretes ativos";
  } catch (erro) {
    alert(erro.message || "Não foi possível ativar os lembretes.");
    botao.disabled = false;
  }
}

async function atualizarBotaoNotificacoes() {
  const botao = $("#ativar-notificacoes");
  if (!botao || !["Aluna", "Professora"].includes(state.role) || !("Notification" in window) || !("serviceWorker" in navigator)) return;
  botao.textContent = "🔔 Ativar lembretes";
  if (Notification.permission !== "granted") return;
  try {
    const registro = await navigator.serviceWorker.ready;
    if (await registro.pushManager.getSubscription()) botao.textContent = "🔔 Lembretes ativos";
  } catch (_) { /* o botão continua permitindo uma nova ativação manual */ }
}

async function renderPage() {
  $("#page-title").textContent = state.page;
  const content = $("#page-content");
  if (state.role === "Master" && state.page === "GEMs") {
    await renderMasterGems(content);
    return;
  }
  if (state.role === "Master" && state.page === "Usuários mestres") {
    await renderMasterUsuarios(content);
    return;
  }
  if (state.role === "Master" && state.page === "Secretarias dos GEMs") {
    await renderMasterSecretarias(content);
    return;
  }
  if (state.role === "Master" && state.page === "Visão da plataforma") {
    await renderMasterVisao(content);
    return;
  }
  if (state.role === "Professora" && state.page === "Minhas aulas") {
    await renderMinhasAulas(content);
    return;
  }
  if (state.role === "Professora" && state.page === "Configurar Métodos") {
    await renderConfigurarMetodos(content);
    return;
  }
  if (state.role === "Professora" && state.page === "Envio de documentos") {
    await renderEnvioDocumentosProfessora(content);
    return;
  }
  if (state.role === "Professora" && state.page === "Provas") {
    await renderProvasProfessora(content);
    return;
  }
  if (state.role === "Professora" && state.page === "Analítico IA") {
    await renderAnaliticoProfessora(content);
    return;
  }
  if (state.role === "Professora" && state.coordenadora && state.page === "Folgas") {
    await renderFolgas(content);
    return;
  }
  if ((state.role === "Professora" || state.role === "Secretaria" || state.role === "Aluna") && state.page === "Mensagens") {
    try { await renderMensagens(content); } catch (error) { content.innerHTML = `<div class="action-error">${escapeHtml(error.message)}</div>`; }
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
  if (state.role === "Aluna" && state.page === "Documentos") {
    await renderDocumentosAluna(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Planejamento e rodízio") {
    await renderRodizio(content);
    return;
  }
  if (state.role === "Secretaria" && state.page === "Folgas") {
    await renderFolgas(content);
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
  if (state.role === "Secretaria" && state.page === "Ajustes") {
    await renderAjustes(content);
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
    content.innerHTML = `<section class="panel empty"><h2>${iconFor(state.page)} ${state.page}</h2><p>Esta página não está disponível para o perfil atual.</p></section>`;
  }
}

async function abrirConta(conta) {
  state.role = conta.role;
  state.name = conta.name;
  state.gem = conta.gem || "GEM Musical";
  state.externo = Boolean(conta.externo);
  state.coordenadora = false;
  if (state.role === "Professora") {
    try { state.coordenadora = await window.GemData.professoraEhCoordenadora(state.name); }
    catch (error) { console.warn("Não foi possível confirmar a coordenação da professora", error); }
  }
  state.page = paginasDoPerfil()[0];
  $("#profile-name").textContent = state.name;
  $("#profile-role").textContent = state.role;
  aplicarNomeGem(state.gem);
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
    document.querySelector(".profile-photo-action")?.remove();
    const trocarFoto = document.createElement("button");
    trocarFoto.className = "profile-photo-action";
    trocarFoto.type = "button";
    trocarFoto.textContent = "Alterar minha foto";
    trocarFoto.addEventListener("click", abrirTrocaFotoProfessora);
    document.querySelector(".profile").appendChild(trocarFoto);
  }
  if (["Aluna", "Professora"].includes(state.role) && "Notification" in window && "serviceWorker" in navigator) { $("#ativar-notificacoes").classList.remove("hidden"); atualizarBotaoNotificacoes(); }
  renderNavigation(); await renderPage();
}

$("#entrar").addEventListener("click", async () => {
  const botao = $("#entrar");
  const erro = $("#login-error");
  erro.classList.add("hidden");
  botao.disabled = true;
  botao.textContent = "Entrando...";
  try {
    const login = $("#nome").value, senha = $("#senha").value;
    const conta = await window.GemData?.autenticar(login, senha);
    if (!conta) throw new Error("A autenticação do GEM ainda não está disponível.");
    // A sessão adicional é usada apenas para URLs privadas das fotos no R2.
    // Se o R2 ainda não estiver configurado, o login normal continua igual.
    const r2Ativo = await window.GemData?.iniciarSessaoR2?.(login, senha);
    if (r2Ativo) {
      const identidade = await window.GemData?.carregarIdentidade?.();
      if (identidade?.logoUrl) aplicarLogo(identidade.logoUrl);
    }
    await abrirConta(conta);
  } catch (error) {
    erro.textContent = error?.message || "Não foi possível entrar agora.";
    erro.classList.remove("hidden");
    botao.disabled = false;
    botao.textContent = "Entrar";
    return;
  }
  botao.disabled = false;
  botao.textContent = "Entrar";
});
$("#sair").addEventListener("click", async () => { try { await window.GemData?.encerrarSessao?.(); } finally { state.coordenadora = false; state.externo = false; $("#ativar-notificacoes").classList.add("hidden"); $("#senha").value = ""; $("#app-screen").classList.add("hidden"); $("#login-screen").classList.remove("hidden"); } });
$("#menu-button").addEventListener("click", () => $(".sidebar").classList.toggle("open"));
$("#ativar-notificacoes").addEventListener("click", ativarNotificacoes);
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
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js", { updateViaCache: "none" })
    .then((registro) => registro.update())
    .catch((erro) => console.warn("Não foi possível atualizar o aplicativo offline.", erro));
}

// A marca é carregada da configuração já usada pelo GEM.
window.GemData?.carregarIdentidade().then((identidade) => {
  const status = document.querySelector(".status");
  if (identidade?.connected) {
    if (identidade.gem?.nome) aplicarNomeGem(identidade.gem.nome);
    status.innerHTML = "<span></span> Conectado ao GEM";
    if (identidade.logoUrl) {
      aplicarLogo(identidade.logoUrl);
    }
  }
});

// Atualizar a página não encerra a sessão: a identidade é restaurada a partir
// do cookie seguro (HttpOnly), que expira em até oito horas ou ao clicar em Sair.
(async () => {
  const conta = await window.GemData?.restaurarSessao?.();
  if (!conta) return;
  try { await abrirConta(conta); }
  catch (erro) { console.warn("Não foi possível restaurar a sessão do GEM.", erro); }
})();
