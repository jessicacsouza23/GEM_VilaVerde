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
    // Além da roda de cada aluna, guardamos as salas já usadas por cada
    // professora. Isto é usado na primeira alocação do sábado seguinte para
    // que ela não volte automaticamente à mesma sala antes de completar a
    // roda das salas. A sala escolhida nesse primeiro bloco continua fixa
    // até o fim daquele sábado (ver estabilizarSalas).
    const salasPorProfessora = {};
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
          (salasPorProfessora[professora] ||= new Set()).add(sala);
          registrarNoCiclo(alunasPorProfessora, professora, linha.Aluna, alunasDaRoda);
        });
      });
    });
    return { porAluna: memoria, alunasPorProfessora, salasPorProfessora };
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
    // Folgas vêm de um cadastro e professoras de outro. Comparamos a forma
    // normalizada para que espaços, acentos ou diferença de maiúsculas nunca
    // façam uma professora de folga voltar para a escala.
    const folgasNormalizadas = new Set((Array.isArray(folgas) ? folgas : []).map(limpar));
    const estaDeFolga = (professora) => folgasNormalizadas.has(limpar(professora));
    const disponiveis = professoras.filter((professora) => !estaDeFolga(professora));
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
    // Depois do primeiro bloco, quem já estava no individual continua sendo
    // a equipe prioritária dele. Isso evita trocar, por exemplo, Patrícia da
    // Sala 1 por uma professora que estava em Teoria no bloco anterior sem
    // que haja uma saída/indisponibilidade real.
    let professorasPrioritariasNoIndividual = new Set();
    // No modo automático, a ordem visual das turmas é uma preferência, não
    // pode derrubar uma professora fixa. O app.py procura uma combinação de
    // Teoria / Solfejo / Individual que deixe a fixa livre no bloco certo.
    // Mantemos a sequência padrão como primeira opção e só remanejamos se ela
    // criar conflito; a rotação manual continua sendo respeitada literalmente.
    let planoAutomatico = null;
    if (!turmaInicioTeoria && usarFixas && turmas.length === posicoes.length && turmas.length <= 6) {
      const permutar = (itens) => itens.length < 2 ? [itens] : itens.flatMap((item, indice) => permutar([...itens.slice(0, indice), ...itens.slice(indice + 1)]).map((restante) => [item, ...restante]));
      const indisponivelNoBloco = (professora, indiceBloco) => estaDeFolga(professora)
        || (saidas[professora] && horarios.indexOf(saidas[professora]) < indiceBloco);
      const respeitaFixas = (ordemTurmas, direcao) => blocos.every((_, indiceBloco) => {
        const posicaoDaTurma = (turma) => (ordemTurmas.indexOf(turma) + direcao * indiceBloco + posicoes.length * 10) % posicoes.length;
        const turmaIndividual = turmas.find((turma) => posicoes[posicaoDaTurma(turma)] === "__individual__");
        const reservadas = new Set((turmasReais[turmaIndividual] || []).map((aluna) => fixas[String(aluna).trim().toLowerCase()]).filter(Boolean));
        if ([...reservadas].some((professora) => indisponivelNoBloco(professora, indiceBloco))) return false;
        const coletivasNoBloco = [];
        for (const turma of turmas) {
          const posicao = posicoes[posicaoDaTurma(turma)];
          if (posicao === "__individual__") continue;
          const professora = coletivas?.[posicao]?.[turma];
          if (professora) {
            if (reservadas.has(professora) || indisponivelNoBloco(professora, indiceBloco)) return false;
            coletivasNoBloco.push(professora);
          }
        }
        return new Set(coletivasNoBloco).size === coletivasNoBloco.length;
      });
      // A primeira candidata é precisamente a ordem antiga (turmas + rotação
      // para frente), então não há mudança quando ela já é válida.
      for (const direcao of [1, -1]) {
        for (const ordemTurmas of permutar(turmas)) {
          if (respeitaFixas(ordemTurmas, direcao)) { planoAutomatico = { ordemTurmas, direcao }; break; }
        }
        if (planoAutomatico) break;
      }
      if (!planoAutomatico) return { escala: null, erros: ["Não existe combinação de horários que respeite simultaneamente as professoras fixas, as aulas coletivas, as folgas e as saídas antecipadas. Ajuste uma dessas informações."] };
    }
    blocos.forEach((bloco, indiceBloco) => {
      const hora = horarios[indiceBloco];
      const alocacoes = turmas.map((turma, indiceTurma) => {
        const inicial = inicioManual[turma];
        const indiceInicial = planoAutomatico ? planoAutomatico.ordemTurmas.indexOf(turma) : indiceTurma;
        const passo = planoAutomatico ? planoAutomatico.direcao : 1;
        const posicao = inicial ? posicoes[(posicoes.indexOf(inicial) + indiceBloco) % posicoes.length] : posicoes[(indiceInicial + passo * indiceBloco + posicoes.length * 10) % posicoes.length];
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
            // A professora escolhida pela Secretaria para Teoria/Solfejo
            // nunca é trocada automaticamente. A prioridade do individual
            // vale para a distribuição das professoras livres, não para
            // desfazer uma escolha explícita da aula coletiva.
            if (!candidatas.includes(escolhida)) { erros.push(`${escolhida} não está disponível para ${posicao} de ${turma} no ${hora}. Ajuste a escolha, as folgas ou as habilitações.`); return; }
            candidatas = [escolhida];
          } else {
            // Sem escolha explícita, preservamos a equipe que já começou o
            // atendimento individual e usamos outra professora na coletiva.
            const alternativasSemPrioritarias = indiceBloco > 0
              ? candidatas.filter((professora) => !professorasPrioritariasNoIndividual.has(professora))
              : candidatas;
            if (alternativasSemPrioritarias.length) candidatas = alternativasSemPrioritarias;
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
        // Havendo professora fixa, continuamos até a verificação por aluna:
        // assim a Secretaria recebe a causa verdadeira (folga, habilitação,
        // coletiva ou duplicidade), em vez de uma mensagem genérica sobre
        // quantidade de professoras.
        const haFixaNestaTurma = usarFixas && alunas.some((aluna) => fixas[String(aluna).trim().toLowerCase()]);
        if (profsLivres.length < alunas.length && !haFixaNestaTurma) { erros.push(`Faltam professoras livres para o atendimento individual de ${turma} no ${hora}.`); return; }
        const salasLivres = [...individuais];
        const alocadas = [];
        // A regra do app.py é obrigatória: primeiro reservamos as professoras
        // fixas para as respectivas alunas; só depois distribuímos as demais.
        // Sem isso, uma aluna sem fixa que aparecesse antes na lista podia
        // receber a professora de uma aluna fixa e criar um falso conflito.
        const professorasFixasDaTurma = new Set(usarFixas
          ? alunas.map((aluna) => fixas[String(aluna).trim().toLowerCase()]).filter(Boolean)
          : []);
        const alunasParaAlocar = [...alunas].sort((a, b) => {
          const aFixa = Boolean(usarFixas && fixas[String(a).trim().toLowerCase()]);
          const bFixa = Boolean(usarFixas && fixas[String(b).trim().toLowerCase()]);
          return Number(bFixa) - Number(aFixa);
        });
        alunasParaAlocar.forEach((aluna) => {
          const fixa = usarFixas ? fixas[String(aluna).trim().toLowerCase()] : null;
          const candidatas = (fixa ? [fixa] : profsLivres.filter((professora) => !professorasFixasDaTurma.has(professora)))
            .filter((professora) => profsLivres.includes(professora));
          if (!candidatas.length || !salasLivres.length) {
            if (fixa) {
              let motivo = "não está disponível para este atendimento.";
              if (!professoras.includes(fixa)) motivo = "não está cadastrada como professora ativa no rodízio.";
              else if (estaDeFolga(fixa)) motivo = "está de folga.";
              else if (indisponiveis.includes(fixa)) motivo = "tem saída antecipada antes deste bloco.";
              else if (!habilitadasIndividuais.includes(fixa)) motivo = `não está habilitada para ${componentes.join(" + ") || "a aula individual"}.`;
              else if (alocadas.some((item) => item.professora === fixa)) motivo = "já está atendendo outra aluna no mesmo horário; uma professora não pode atender duas alunas simultaneamente.";
              else if (ocupadas.has(fixa)) motivo = "já está em uma aula coletiva neste mesmo horário.";
              erros.push(`Não foi possível alocar ${aluna} — ${turma} em ${hora}: a professora fixa ${fixa} ${motivo}`);
            } else {
              erros.push(`Não foi possível alocar ${aluna} — ${turma} em ${hora}; verifique professoras, folgas e salas.`);
            }
            return;
          }
          const mem = memoria[aluna];
          const pares = candidatas.flatMap((professora) => salasLivres.map((sala) => ({ professora, sala })));
          pares.sort((a, b) => {
            const pontuar = (item) => {
              // A roda é da professora: ela só volta a atender a mesma aluna
              // depois de ter passado por todas as alunas deste modelo.
              const alunasAtendidas = memoriaHistorica.alunasPorProfessora[item.professora] || new Set();
              const completouARoda = cicloConcluido(alunasAtendidas, alunasDaRoda);
              const repetiuAntesDaRoda = regras.nao_repetir_aluna !== false && !completouARoda && alunasAtendidas.has(aluna);
              const salasDaProfessora = memoriaHistorica.salasPorProfessora[item.professora] || new Set();
              const repetiuSalaDaProfessora = regras.nao_repetir_sala !== false
                && salasDaProfessora.size < individuais.length
                && salasDaProfessora.has(item.sala);
              const foraDaEquipeInicial = indiceBloco > 0 && !fixa && !professorasPrioritariasNoIndividual.has(item.professora);
              return [Number(foraDaEquipeInicial), Number(regras.nao_repetir_imediata !== false && candidatas.length > 1 && item.professora === mem.ultima), Number(repetiuAntesDaRoda), Number(repetiuSalaDaProfessora), Number(regras.nao_repetir_sala !== false && new Set(mem.salas).size < individuais.length && mem.salas.includes(item.sala)), item.professora, item.sala];
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
        if (indiceBloco === 0) {
          professorasPrioritariasNoIndividual = new Set(alocadas.map((item) => item.professora));
        }
      });
    });
    if (erros.length) return { escala: null, erros: [...new Set(erros)] };
    estabilizarSalas(escala, horarios, individuais, data, escalasAnteriores);
    return { escala: Object.values(escala), erros: [] };
  }

  function estabilizarSalas(mapa, horarios, salas, data, escalasAnteriores = []) {
    const porProf = {};
    const primeiraSalaPorProfessora = {};
    Object.values(mapa).forEach((linha) => Object.entries(linha._detalhes || {}).forEach(([hora, detalhe]) => {
      if (!detalhe.individual) return;
      const valor = String(linha[hora] || ""); const componentes = detalhe.professoras_componentes || {};
      const professora = String(componentes.Prática || valor.split("|").slice(1).join("|").trim());
      if (professora) (porProf[professora] ||= new Set()).add(hora);
      // A sala sorteada/selecionada no primeiro bloco é a referência do
      // sábado. Ela não pode ser recalculada nos blocos seguintes.
      if (hora === horarios[0] && professora) {
        const salaInicial = valor.split("|", 1)[0].trim();
        if (salas.includes(salaInicial)) primeiraSalaPorProfessora[professora] = salaInicial;
      }
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
    // Professoras que começaram no individual têm suas salas travadas. As
    // demais — por exemplo, quem veio de Teoria/Solfejo para cobrir uma
    // saída — receberão uma das salas ainda livres e compatíveis.
    const porSala = { ...primeiraSalaPorProfessora };
    const ordenar = [...profs].sort((a, b) => vizinhas[b].size - vizinhas[a].size || a.localeCompare(b));
    const tentar = (indice) => {
      if (indice >= ordenar.length) return true;
      const prof = ordenar[indice];
      const usadas = new Set([...vizinhas[prof]].map((vizinha) => porSala[vizinha]).filter(Boolean));
      if (porSala[prof]) return !usadas.has(porSala[prof]) && tentar(indice + 1);
      for (const sala of ordem) {
        if (usadas.has(sala)) continue;
        porSala[prof] = sala;
        if (tentar(indice + 1)) return true;
        delete porSala[prof];
      }
      return false;
    };
    if (!tentar(0)) return;
    Object.values(mapa).forEach((linha) => Object.entries(linha._detalhes || {}).forEach(([hora, detalhe]) => { if (!detalhe.individual) return; const valor = String(linha[hora] || ""); const componentes = detalhe.professoras_componentes || {}; const professora = String(componentes.Prática || valor.split("|").slice(1).join("|").trim()); const sala = porSala[professora]; if (!sala) return; detalhe.sala_fixa_professora = sala; linha[hora] = `${sala} | ${valor.split("|").slice(1).join("|").trim()}`; }));
  }

  window.RodizioEngine = { gerar, prepararModelo, horario, nomeArea };
})();
