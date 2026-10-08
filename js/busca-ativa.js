/* Indicadores de acompanhamento; ausência de informação não é desinteresse. */
(function () {
  const normalizar = (v) => String(v || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
  function dataIso(valor) {
    const texto = String(valor || "");
    const br = texto.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    const iso = br ? `${br[3]}-${br[2]}-${br[1]}` : texto.slice(0, 10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) return "";
    const data = new Date(`${iso}T12:00:00Z`);
    return Number.isFinite(data.getTime()) && data.toISOString().slice(0, 10) === iso ? iso : "";
  }
  function diasPeriodo(inicio, fim) {
    if (!dataIso(inicio) || !dataIso(fim) || inicio > fim) throw new Error("Informe um período válido: a data inicial deve ser anterior ou igual à final.");
    const dias = [];
    for (let data = new Date(`${inicio}T12:00:00Z`); data.toISOString().slice(0, 10) <= fim; data.setUTCDate(data.getUTCDate() + 1)) dias.push(data.toISOString().slice(0, 10));
    return dias;
  }
  const disciplina = (valor) => {
    const nome = String(valor || "").replace(/^Analise_/, "").trim();
    return ({ canto: "Solfejo Melódico", "solfejo melodico": "Solfejo Melódico", pratica: "Prática", teoria: "Teoria", solfejo: "Solfejo" })[normalizar(nome)] || nome;
  };
  function disciplinasDaLinha(linha) {
    const tipos = new Set();
    Object.entries(linha?._detalhes || {}).forEach(([hora, detalhe]) => {
      if (!linha[hora]) return;
      const componentes = detalhe.componentes?.length ? detalhe.componentes : /pratica.*solfejo|solfejo.*pratica/.test(normalizar(detalhe.tipo)) ? ["Solfejo", "Prática"] : [detalhe.tipo];
      componentes.filter(Boolean).forEach((tipo) => tipos.add(disciplina(tipo)));
    });
    return tipos;
  }
  function calcular(dados, { inicio, fim, turma = "", area = "" }) {
    diasPeriodo(inicio, fim);
    const noPeriodo = (data) => data && data >= inicio && data <= fim;
    const chave = (nome, data) => JSON.stringify([nome, data]);
    const previstas = new Map(), chamadas = new Map(), disciplinas = new Set();
    (dados.calendarios || []).forEach((calendario) => {
      const data = dataIso(calendario.id);
      if (!noPeriodo(data)) return;
      (calendario.escala || []).forEach((linha) => {
        const tipos = disciplinasDaLinha(linha);
        tipos.forEach((tipo) => disciplinas.add(tipo));
        previstas.set(chave(linha.Aluna, data), tipos);
      });
    });
    const historico = (dados.historico || []).filter((item) => noPeriodo(dataIso(item.Data)));
    // A última chamada do dia prevalece sobre correções anteriores.
    [...historico].sort((a, b) => Number(a.id || 0) - Number(b.id || 0)).forEach((item) => {
      if (item.Tipo === "Chamada") chamadas.set(chave(item.Aluna, dataIso(item.Data)), item);
      if (String(item.Tipo || "").startsWith("Analise_")) disciplinas.add(disciplina(item.Tipo));
    });
    const ativas = (dados.alunas || []).filter((item) => item.ativo !== false);
    const turmas = [...new Set(ativas.map((item) => item.turma || "Sem turma"))].sort((a, b) => a.localeCompare(b, "pt-BR", { numeric: true }));
    const alunas = ativas.filter((aluna) => !turma || (aluna.turma || "Sem turma") === turma).map((aluna) => {
      const analises = historico.filter((item) => item.Aluna === aluna.nome && String(item.Tipo || "").startsWith("Analise_"));
      const vinculoArea = (data) => previstas.get(chave(aluna.nome, data))?.has(area) || analises.some((item) => dataIso(item.Data) === data && disciplina(item.Tipo) === area);
      const registros = analises.filter((item) => !area || disciplina(item.Tipo) === area);
      const faltas = [], presencas = [], dificuldades = new Map(), participacao = new Map();
      let faltasSemDisciplina = 0, diasSemChamada = 0, aulasPrevistas = 0;
      previstas.forEach((tipos, key) => {
        const [nome, data] = JSON.parse(key);
        if (nome !== aluna.nome || (area && !tipos.has(area))) return;
        aulasPrevistas++;
        const status = normalizar(chamadas.get(key)?.Status);
        if (!["presente", "ausente", "justificada", "falta justificada", "falta"].includes(status)) diasSemChamada++;
      });
      chamadas.forEach((item) => {
        if (item.Aluna !== aluna.nome) return;
        const data = dataIso(item.Data), status = normalizar(item.Status);
        const falta = ["ausente", "justificada", "falta justificada", "falta"].includes(status);
        const tipos = [...(previstas.get(chave(aluna.nome, data)) || [])];
        if (falta && !tipos.length) faltasSemDisciplina++;
        if (area && !vinculoArea(data)) return;
        if (falta) faltas.push({ data, justificada: status.includes("justificada"), disciplinas: tipos });
        if (status === "presente") presencas.push(data);
      });
      registros.forEach((registro) => {
        const data = dataIso(registro.Data), tipo = disciplina(registro.Tipo);
        const diffs = Array.isArray(registro.Dificuldades) ? registro.Dificuldades : [];
        diffs.filter((d) => d && !/nao apresentou dificuldade/.test(normalizar(d))).forEach((texto) => {
          const key = JSON.stringify([tipo, normalizar(texto)]);
          const mapa = /nao estudou|estudou de forma insatisfatoria|nao realizou|nao assistiu|nao participou/.test(normalizar(texto)) ? participacao : dificuldades;
          if (!mapa.has(key)) mapa.set(key, { disciplina: tipo, texto, datas: new Set() });
          mapa.get(key).datas.add(data);
        });
      });
      const estudosPorDia = new Map();
      (dados.estudos || []).filter((item) => item.aluna === aluna.nome && noPeriodo(dataIso(item.data))).forEach((item) => {
        const data = dataIso(item.data), estudou = Array.isArray(item.horarios) && item.horarios.length > 0;
        estudosPorDia.set(data, Boolean(estudosPorDia.get(data) || estudou));
      });
      const diasEstudo = [...estudosPorDia.values()].filter(Boolean).length;
      const diasNaoEstudou = estudosPorDia.size - diasEstudo;
      const sinais = [...participacao.values()].map((item) => ({ ...item, datas: [...item.datas].sort() }));
      const recorrencias = [...dificuldades.values()].filter((item) => item.datas.size >= 2).map((item) => ({ ...item, datas: [...item.datas].sort() }));
      const diasParticipacao = new Set(sinais.flatMap((item) => item.datas));
      const motivos = [];
      if (faltas.length) motivos.push(`${faltas.length} dia(s) de aula perdido(s)`);
      if (diasParticipacao.size) motivos.push(`${diasParticipacao.size} dia(s) com sinais de participação registrados pela professora`);
      if (recorrencias.length) motivos.push(`${recorrencias.length} dificuldade(s) recorrente(s) para reforço`);
      if (!area && diasNaoEstudou) motivos.push(`${diasNaoEstudou} dia(s) marcados como não estudou`);
      return { nome: aluna.nome, turma: aluna.turma || "Sem turma", faltas: faltas.sort((a, b) => b.data.localeCompare(a.data)), justificadas: faltas.filter((f) => f.justificada).length, ausentes: faltas.filter((f) => !f.justificada).length, presentes: presencas.length, sinais, recorrencias, diasEstudo, diasNaoEstudou, semEstudoRegistrado: !estudosPorDia.size, faltasSemDisciplina, diasSemChamada, aulasPrevistas, registros: registros.length, motivos, acompanhar: motivos.length > 0 };
    }).sort((a, b) => Number(b.acompanhar) - Number(a.acompanhar) || b.faltas.length - a.faltas.length || b.sinais.length - a.sinais.length || a.nome.localeCompare(b.nome, "pt-BR"));
    return { alunas, turmas, disciplinas: [...disciplinas].sort((a, b) => a.localeCompare(b, "pt-BR")) };
  }
  window.BuscaAtiva = { calcular, diasPeriodo, dataIso };
})();
