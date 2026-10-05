/* Motor do rodízio. É a versão web das regras usadas no app.py.
   Ele trabalha apenas com cópias dos dados recebidos e nunca modifica uma
   escala anterior. A gravação é responsabilidade da tela da Secretaria. */
(function () {
  const limpar = (valor) => String(valor || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
  const nomeArea = (valor) => {
    const normalizado = limpar(valor);
    return normalizado === "CANTO" || normalizado === "SOLFEJO MELODICO" ? "Solfejo Melódico" : String(valor || "").trim();
  };
  const horario = (bloco, indice) => {
    const inicio = String(bloco["Início"] || bloco.inicio || "").trim();
    const fim = String(bloco.Fim || bloco.fim || "").trim();
    const nome = String(bloco.Bloco || bloco.nome || `Bloco ${indice + 1}`).trim();
    return inicio && fim ? `${inicio} - ${fim} (${nome})` : nome;
  };
  const dataBrParaData = (valor) => {
    const [dia, mes, ano] = String(valor || "").split("/").map(Number);
    return ano && mes && dia ? new Date(ano, mes - 1, dia) : null;
  };

  function prepararModelo(modelo, turmasReais) {
    const config = modelo?.configuracao || {};
    const blocos = (config.blocos || []).filter((item) => String(item["Início"] || item.inicio || "").trim());
    const salas = (config.salas || []).filter((item) => item.Ativa !== false);
    const individuais = salas.filter((item) => limpar(item.Uso) === "INDIVIDUAL").map((item) => String(item.Sala || "").trim()).filter(Boolean);
    const coletivas = {};
    (config.atividades || []).filter((item) => limpar(item.Formato) === "TURMA").forEach((item) => {
      const atividade = nomeArea(item.Atividade);
      if (atividade) coletivas[atividade] = String(item["Sala sugerida"] || "").trim();
    });
    const componentes = (config.atividades || []).filter((item) => limpar(item.Formato) === "INDIVIDUAL").map((item) => nomeArea(item.Atividade)).filter(Boolean);
    const turmas = (config.turmas || []).filter((item) => item["Ativa no modelo"] !== false).map((item) => String(item.Turma || "").trim()).filter((turma) => turma && turmasReais[turma]);
    return { config, blocos, individuais, coletivas, componentes, turmas };
  }

  function professoraDaPratica(valor, detalhe = {}) {
    const componentes = detalhe.professoras_componentes || {};
    const texto = String(componentes.Prática || String(valor || "").split("|").slice(1).join("|").trim());
    const encontrada = texto.match(/Prática:\s*([^·]+)\s*$/i);
    return (encontrada ? encontrada[1] : texto).replace(/^Prática:\s*/i, "").trim();
  }

  function cicloConcluido(alunasAtendidas, alunasDaRoda) {
    return alunasDaRoda.length > 0 && alunasDaRoda.every((aluna) => alunasAtendidas.has(aluna));
  }

  function registrarNoCiclo(mapa, professora, aluna, alunasDaRoda) {
    // Alunas fixas não entram na roda geral: a mesma professora foi escolhida
    // deliberadamente para elas e não deve bloquear o ciclo das demais.
    if (!alunasDaRoda.includes(aluna)) return;
    const atendidas = (mapa[professora] ||= new Set());
    if (cicloConcluido(atendidas, alunasDaRoda)) atendidas.clear();
    atendidas.add(aluna);
  }

  function memoriaDasEscalas(escalaAnteriores, dataSelecionada, alunas, alunasDaRoda, salasIndividuais) {
    const memoria = Object.fromEntries(alunas.map((aluna) => [aluna, { professoras: [], salas: [], ultima: null }]));
    const alunasPorProfessora = {};
    const limite = dataBrParaData(dataSelecionada);
    [...(escalaAnteriores || [])].sort((a, b) => (dataBrParaData(a.id)?.getTime() || 0) - (dataBrParaData(b.id)?.getTime() || 0)).forEach((anterior) => {
      const data = dataBrParaData(anterior.id);
      if (limite && data && data >= limite) return;
      (anterior.escala || []).forEach((linha) => {
        const item = memoria[linha.Aluna];
        if (!item) return;
        const detalhes = linha._detalhes || {};
        Object.entries(linha).forEach(([hora, valor]) => {
          if (hora === "Aluna" || hora === "_detalhes" || !String(valor).includes("|")) return;
          const detalhe = detalhes[hora] || {};
          const sala = String(valor).split("|", 1)[0].trim();
          if (!detalhe.individual && !salasIndividuais.includes(sala)) return;
          if (!salasIndividuais.includes(sala)) return;
          const professora = professoraDaPratica(valor, detalhe);
          if (!professora) return;
          item.professoras.push(professora);
          item.salas.push(sala);
          item.ultima = professora;
          registrarNoCiclo(alunasPorProfessora, professora, linha.Aluna, alunasDaRoda);
        });
      });
    });
    return { porAluna: memoria, alunasPorProfessora };
  }

  function gerar({ modelo, data, turmasReais, professoras, folgas = [], saidas = {}, fixas = {}, coletivas = {}, turmaInicioTeoria = null, usarFixas = false, escalasAnteriores = [] }) {
    const preparado = prepararModelo(modelo, turmasReais);
    const { config, blocos, individuais, coletivas: salasColetivas, componentes, turmas } = preparado;
    const erros = [];
    if (!blocos.length || !turmas.length || !individuais.length || !componentes.length) return { escala: null, erros: ["Complete no modelo os blocos, as turmas ativas, as salas individuais e as atividades individuais."] };
    const atividadesColetivas = Object.keys(salasColetivas);
    if (atividadesColetivas.length + 1 > blocos.length) return { escala: null, erros: ["O modelo possui mais atividades simultâneas do que blocos disponíveis."] };
    if (turmas.length > atividadesColetivas.length + 1) return { escala: null, erros: ["Há mais turmas ativas do que posições de atividade por bloco. Cadastre mais atividades coletivas ou ajuste as turmas."] };
    turmas.forEach((turma) => {
      if ((turmasReais[turma] || []).length > individuais.length) erros.push(`${turma} tem ${(turmasReais[turma] || []).length} alunas, mas há apenas ${individuais.length} salas individuais ativas.`);
    });
    if (erros.length) return { escala: null, erros };

    const habilitadas = config.professoras_habilitadas || {};
    const disponiveis = professoras.filter((professora) => !folgas.includes(professora));
    const todasAlunas = turmas.flatMap((turma) => turmasReais[turma] || []);
    const alunasDaRoda = todasAlunas.filter((aluna) => !(usarFixas && fixas[String(aluna).trim().toLowerCase()]));
    const memoriaHistorica = memoriaDasEscalas(escalasAnteriores, data, todasAlunas, alunasDaRoda, individuais);
    const memoria = memoriaHistorica.porAluna;
    const escala = Object.fromEntries(todasAlunas.map((aluna) => [aluna, { Aluna: aluna, _detalhes: {} }]));
    const mesmaProf = config.mesma_professora_nos_componentes !== false;
    const regras = config.regras_rodizio || {};
    const posicoes = [...atividadesColetivas, "__individual__"];
    const indiceTeoria = posicoes.findIndex((item) => limpar(item) === "TEORIA");
    const inicioManual = {};
    if (turmaInicioTeoria && turmas.includes(turmaInicioTeoria) && indiceTeoria >= 0) {
      const ordem = [posicoes[indiceTeoria], ...posicoes.filter((item) => item !== posicoes[indiceTeoria] && item !== "__individual__"), "__individual__"];
      const indiceDaTurma = turmas.indexOf(turmaInicioTeoria);
      turmas.forEach((turma, indice) => { inicioManual[turma] = ordem[(indice - indiceDaTurma + ordem.length) % ordem.length]; });
    }
    const horarios = blocos.map(horario);
    blocos.forEach((bloco, indiceBloco) => {
      const hora = horarios[indiceBloco];
      const alocacoes = turmas.map((turma, indiceTurma) => {
        const inicial = inicioManual[turma];
        const posicao = inicial ? posicoes[(posicoes.indexOf(inicial) + indiceBloco) % posicoes.length] : posicoes[(indiceTurma + indiceBloco) % posicoes.length];
        return { turma, posicao };
      }).sort((a, b) => Number(a.posicao === "__individual__") - Number(b.posicao === "__individual__"));
      // A professora fixa é reservada para a aluna antes da escolha das
      // coletivas. Sem esta reserva, a seleção automática podia colocá-la em
      // Teoria/Solfejo no mesmo horário e só então acusar um conflito que o
      // rodízio poderia ter evitado escolhendo outra professora habilitada.
      const turmasNoIndividual = alocacoes.filter((item) => item.posicao === "__individual__").map((item) => item.turma);
      const professorasReservadas = new Set(usarFixas ? turmasNoIndividual.flatMap((turma) => (turmasReais[turma] || [])
        .map((aluna) => fixas[String(aluna).trim().toLowerCase()]).filter(Boolean)) : []);
      alocacoes.forEach(({ turma, posicao }) => {
        const alunas = turmasReais[turma] || [];
        const indisponiveis = Object.entries(saidas).filter(([, ultimo]) => ultimo && horarios.indexOf(ultimo) < indiceBloco).map(([professora]) => professora);
        if (posicao !== "__individual__") {
          const ocupadas = new Set(todasAlunas.map((aluna) => String(escala[aluna][hora] || "")).filter((item) => item.includes("|")).map((item) => item.split("|").slice(1).join("|").trim()));
          const habilitadasDaArea = habilitadas[posicao] || (posicao === "Solfejo Melódico" ? habilitadas.Canto : null) || disponiveis;
          let candidatas = habilitadasDaArea.filter((professora) => disponiveis.includes(professora) && !indisponiveis.includes(professora) && !ocupadas.has(professora) && !professorasReservadas.has(professora));
          const escolhida = coletivas?.[posicao]?.[turma];
          if (escolhida) {
            if (!candidatas.includes(escolhida)) { erros.push(`${escolhida} não está disponível para ${posicao} de ${turma} no ${hora}. Ajuste a escolha, as folgas ou as habilitações.`); return; }
            candidatas = [escolhida];
          }
          if (!candidatas.length) { erros.push(`Não há professora disponível/habilitada para ${posicao} no ${hora}.`); return; }
          const professora = candidatas[indiceBloco % candidatas.length];
          alunas.forEach((aluna) => { escala[aluna][hora] = `${salasColetivas[posicao]} | ${professora}`; escala[aluna]._detalhes[hora] = { tipo: posicao, individual: false, turma }; });
          return;
        }
        const ocupadas = new Set(todasAlunas.map((aluna) => String(escala[aluna][hora] || "")).filter((item) => item.includes("|")).map((item) => item.split("|").slice(1).join("|").trim()));
        let habilitadasIndividuais = [...professoras];
        if (mesmaProf) componentes.forEach((componente) => { const lista = habilitadas[componente] || professoras; habilitadasIndividuais = habilitadasIndividuais.filter((professora) => lista.includes(professora)); });
        const profsLivres = disponiveis.filter((professora) => habilitadasIndividuais.includes(professora) && !ocupadas.has(professora) && !indisponiveis.includes(professora));
        if (profsLivres.length < alunas.length) { erros.push(`Faltam professoras livres para o atendimento individual de ${turma} no ${hora}.`); return; }
        const salasLivres = [...individuais];
        const alocadas = [];
        alunas.forEach((aluna) => {
          const fixa = usarFixas ? fixas[String(aluna).trim().toLowerCase()] : null;
          const candidatas = (fixa ? [fixa] : [...profsLivres]).filter((professora) => profsLivres.includes(professora));
          if (!candidatas.length || !salasLivres.length) { erros.push(fixa ? `Não foi possível alocar ${aluna} — ${turma} em ${hora}: a professora fixa ${fixa} já está ocupada, de folga ou saiu mais cedo.` : `Não foi possível alocar ${aluna} — ${turma} em ${hora}; verifique professoras, folgas e salas.`); return; }
          const mem = memoria[aluna];
          const pares = candidatas.flatMap((professora) => salasLivres.map((sala) => ({ professora, sala })));
          pares.sort((a, b) => {
            const pontuar = (item) => {
              // A roda é da professora: ela só volta a atender a mesma aluna
              // depois de ter passado por todas as alunas deste modelo.
              const alunasAtendidas = memoriaHistorica.alunasPorProfessora[item.professora] || new Set();
              const completouARoda = cicloConcluido(alunasAtendidas, alunasDaRoda);
              const repetiuAntesDaRoda = regras.nao_repetir_aluna !== false && !completouARoda && alunasAtendidas.has(aluna);
              return [Number(regras.nao_repetir_imediata !== false && candidatas.length > 1 && item.professora === mem.ultima), Number(repetiuAntesDaRoda), Number(regras.nao_repetir_sala !== false && new Set(mem.salas).size < individuais.length && mem.salas.includes(item.sala)), item.professora, item.sala];
            };
            return pontuar(a).join("|").localeCompare(pontuar(b).join("|"), "pt-BR", { numeric: true });
          });
          const { professora, sala } = pares[0];
          escala[aluna][hora] = `${sala} | ${professora}`;
          escala[aluna]._detalhes[hora] = { tipo: componentes.length > 1 ? "Prática + Solfejo" : componentes[0], componentes: [...componentes], individual: true, turma, mesma_professora_componentes: mesmaProf };
          alocadas.push({ aluna, sala, professora }); profsLivres.splice(profsLivres.indexOf(professora), 1); salasLivres.splice(salasLivres.indexOf(sala), 1);
          mem.professoras.push(professora); mem.salas.push(sala); mem.ultima = professora;
          registrarNoCiclo(memoriaHistorica.alunasPorProfessora, professora, aluna, alunasDaRoda);
        });
        if (!mesmaProf && alocadas.length > 1) {
          const pratica = alocadas.map((item) => item.professora), solfejo = [...pratica.slice(1), pratica[0]];
          alocadas.forEach((item, i) => { escala[item.aluna][hora] = `${item.sala} | Solfejo: ${solfejo[i]} · Prática: ${item.professora}`; escala[item.aluna]._detalhes[hora].professoras_componentes = { Solfejo: solfejo[i], "Prática": item.professora }; });
        }
      });
    });
    if (erros.length) return { escala: null, erros: [...new Set(erros)] };
    estabilizarSalas(escala, horarios, individuais, data, escalasAnteriores);
    return { escala: Object.values(escala), erros: [] };
  }

  function estabilizarSalas(mapa, horarios, salas, data, escalasAnteriores = []) {
    const porProf = {};
    Object.values(mapa).forEach((linha) => Object.entries(linha._detalhes || {}).forEach(([hora, detalhe]) => {
      if (!detalhe.individual) return;
      const valor = String(linha[hora] || ""); const componentes = detalhe.professoras_componentes || {};
      const professora = String(componentes.Prática || valor.split("|").slice(1).join("|").trim());
      if (professora) (porProf[professora] ||= new Set()).add(hora);
    }));
    const profs = Object.keys(porProf); const vizinhas = Object.fromEntries(profs.map((prof) => [prof, new Set()]));
    horarios.forEach((hora) => { const noBloco = profs.filter((prof) => porProf[prof].has(hora)); noBloco.forEach((prof) => noBloco.forEach((outra) => { if (prof !== outra) vizinhas[prof].add(outra); })); });
    // A professora mantém a mesma sala entre todos os blocos do sábado. No
    // próximo rodízio, a ordem começa em outra sala para a roda continuar.
    // A troca de sala acompanha a quantidade de rodízios efetivamente
    // realizados, e não os dias do calendário. Usar a data quebrava a roda
    // quando havia sete salas: um sábado para o outro são sete dias e a
    // conta voltava à mesma sala. Escalas canceladas/sem geração também não
    // avançam a sequência.
    const dataAtual = dataBrParaData(data)?.getTime() || Number.POSITIVE_INFINITY;
    const rodiziosAnteriores = (escalasAnteriores || []).filter((escala) => {
      const dataEscala = dataBrParaData(escala?.id)?.getTime();
      return Array.isArray(escala?.escala) && escala.escala.length && dataEscala && dataEscala < dataAtual;
    }).length;
    const deslocamento = salas.length ? rodiziosAnteriores % salas.length : 0;
    const ordem = [...salas.slice(deslocamento), ...salas.slice(0, deslocamento)];
    const porSala = {};
    const ordenar = [...profs].sort((a, b) => vizinhas[b].size - vizinhas[a].size || a.localeCompare(b));
    const tentar = (indice) => { if (indice >= ordenar.length) return true; const prof = ordenar[indice]; const usadas = new Set([...vizinhas[prof]].map((vizinha) => porSala[vizinha]).filter(Boolean)); for (const sala of ordem) { if (usadas.has(sala)) continue; porSala[prof] = sala; if (tentar(indice + 1)) return true; delete porSala[prof]; } return false; };
    if (!tentar(0)) return;
    Object.values(mapa).forEach((linha) => Object.entries(linha._detalhes || {}).forEach(([hora, detalhe]) => { if (!detalhe.individual) return; const valor = String(linha[hora] || ""); const componentes = detalhe.professoras_componentes || {}; const professora = String(componentes.Prática || valor.split("|").slice(1).join("|").trim()); const sala = porSala[professora]; if (!sala) return; detalhe.sala_fixa_professora = sala; linha[hora] = `${sala} | ${valor.split("|").slice(1).join("|").trim()}`; }));
  }

  window.RodizioEngine = { gerar, prepararModelo, horario, nomeArea };
})();
