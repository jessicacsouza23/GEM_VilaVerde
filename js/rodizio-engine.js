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
  function horariosComponentes(hora, componentes, atividades = []) {
    if (!Array.isArray(componentes) || componentes.length < 2) return {};
    const partes = String(hora || "").match(/^(\d{1,2}):(\d{2})\s*[-–—]\s*(\d{1,2}):(\d{2})(.*)$/);
    if (!partes) return {};
    const [, hi, mi, hf, mf, sufixo] = partes;
    if (+hi > 23 || +hf > 23 || +mi > 59 || +mf > 59) return {};
    let minuto = +hi * 60 + +mi;
    const fim = +hf * 60 + +mf;
    // Mantém a ordem dos componentes do rodízio e usa os minutos do modelo.
    const duracoes = componentes.map((tipo) => Number(atividades.find((item) =>
      limpar(item.Formato) === "INDIVIDUAL" && limpar(nomeArea(item.Atividade)) === limpar(nomeArea(tipo))
    )?.["Duração (min)"]));
    if (duracoes.some((valor) => !Number.isInteger(valor) || valor <= 0) || duracoes.reduce((a, b) => a + b, 0) > fim - minuto) return {};
    const formatar = (valor) => `${String(Math.floor(valor / 60)).padStart(2, "0")}:${String(valor % 60).padStart(2, "0")}`;
    return Object.fromEntries(componentes.map((tipo, indice) => {
      const inicio = minuto;
      minuto += duracoes[indice];
      return [tipo, `${formatar(inicio)} - ${formatar(minuto)}${sufixo}`];
    }));
  }

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

  // Atribuição de custo mínimo (algoritmo húngaro): compara o grupo inteiro,
  // em vez de deixar a última aluna com o que sobrou das escolhas anteriores.
  function atribuirCustos(custos) {
    const n = custos.length, m = custos[0]?.length || 0;
    if (!n) return [];
    if (n > m) return null;
    const u = Array(n + 1).fill(0), v = Array(m + 1).fill(0);
    const p = Array(m + 1).fill(0), caminho = Array(m + 1).fill(0);
    for (let i = 1; i <= n; i++) {
      p[0] = i;
      let j0 = 0;
      const min = Array(m + 1).fill(Infinity), usadas = Array(m + 1).fill(false);
      do {
        usadas[j0] = true;
        const i0 = p[j0];
        let delta = Infinity, j1 = 0;
        for (let j = 1; j <= m; j++) {
          if (usadas[j]) continue;
          const custo = custos[i0 - 1][j - 1] - u[i0] - v[j];
          if (custo < min[j]) { min[j] = custo; caminho[j] = j0; }
          if (min[j] < delta) { delta = min[j]; j1 = j; }
        }
        if (!Number.isFinite(delta)) return null;
        for (let j = 0; j <= m; j++) {
          if (usadas[j]) { u[p[j]] += delta; v[j] -= delta; }
          else min[j] -= delta;
        }
        j0 = j1;
      } while (p[j0]);
      do { const j1 = caminho[j0]; p[j0] = p[j1]; j0 = j1; } while (j0);
    }
    const resultado = Array(n);
    for (let j = 1; j <= m; j++) if (p[j]) resultado[p[j] - 1] = j - 1;
    return resultado;
  }

  function cicloSalas(historico, salas) {
    const ciclo = new Set();
    for (const sala of historico) {
      if (!salas.includes(sala)) continue;
      if (salas.every(item => ciclo.has(item))) ciclo.clear();
      ciclo.add(sala);
    }
    if (salas.every(item => ciclo.has(item))) ciclo.clear();
    return ciclo;
  }

  function memoriaDasEscalas(escalaAnteriores, dataSelecionada, alunas, alunasDaRoda, salasIndividuais) {
    const memoria = Object.fromEntries(alunas.map((aluna) => [aluna, { professoras: [], salas: [], ultima: null }]));
    const alunasPorProfessora = {};
    // Além da roda de cada aluna, guardamos as salas já usadas por cada
    // professora. Isto é usado na primeira alocação do sábado seguinte para
    // que ela não volte automaticamente à mesma sala antes de completar a
    // roda das salas. Entre blocos, quem continua na Prática mantém sua sala;
    // nas trocas com coletivas, a substituta herda a sala liberada.
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
          if (detalhe.atividade_secretaria) return;
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
    const encaminharSecretaria = (aluna, hora, turma) => {
      escala[aluna][hora] = 'Local a definir | Secretarias';
      escala[aluna]._detalhes[hora] = { tipo: 'Atividade com as secretarias', individual: false, turma,
        atividade_secretaria: true, responsavel_papel: 'Secretaria', responsavel: '', sala: 'Local a definir' };
    };
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
        const coletivasNoBloco = [];
        for (const turma of turmas) {
          const posicao = posicoes[posicaoDaTurma(turma)];
          if (posicao === "__individual__") continue;
          const professora = coletivas?.[posicao]?.[turma];
          if (professora) {
            if (indisponivelNoBloco(professora, indiceBloco)) continue;
            if (reservadas.has(professora)) return false;
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
          if (!candidatas.length) { alunas.forEach(aluna => encaminharSecretaria(aluna, hora, turma)); return; }
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
          if (!candidatas.length) { alunas.forEach(aluna => encaminharSecretaria(aluna, hora, turma)); return; }
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
        const peso = alunas.length + 1;
        const custosProfessoras = alunasParaAlocar.map(aluna => profsLivres.map(professora => {
          const fixa = usarFixas ? fixas[String(aluna).trim().toLowerCase()] : null;
          if (fixa && professora !== fixa) return Infinity;
          const atendidas = memoriaHistorica.alunasPorProfessora[professora] || new Set();
          const imediata = !fixa && regras.nao_repetir_imediata !== false && memoria[aluna].ultima === professora;
          const ciclo = !fixa && regras.nao_repetir_aluna !== false && !cicloConcluido(atendidas, alunasDaRoda) && atendidas.has(aluna);
          const foraDaEquipe = indiceBloco > 0 && !fixa && !professorasPrioritariasNoIndividual.has(professora);
          return Number(imediata) * peso * peso + Number(ciclo) * peso + Number(foraDaEquipe);
        }));
        // Vagas virtuais custam mais que qualquer professora disponível.
        // Assim só o excedente fica com a Secretaria, nunca o grupo inteiro.
        const custoSecretaria = (peso ** 4) + 1;
        const atribuicao = atribuirCustos(custosProfessoras.map((custos, i) => [
          ...custos, ...alunasParaAlocar.map(() => {
            const fixa = usarFixas && fixas[String(alunasParaAlocar[i]).trim().toLowerCase()];
            return fixa && profsLivres.includes(fixa) ? Infinity : custoSecretaria;
          })
        ]));
        const planoProfessoras = atribuicao && new Map(alunasParaAlocar.map((aluna, i) => [aluna, profsLivres[atribuicao[i]] || null]));
        alunasParaAlocar.forEach((aluna) => {
          if (planoProfessoras?.has(aluna) && planoProfessoras.get(aluna) === null) {
            encaminharSecretaria(aluna, hora, turma);
            return;
          }
          const fixa = usarFixas ? fixas[String(aluna).trim().toLowerCase()] : null;
          const candidatas = (fixa ? [fixa] : profsLivres.filter((professora) => !professorasFixasDaTurma.has(professora)))
            .filter((professora) => profsLivres.includes(professora) && (!planoProfessoras || planoProfessoras.get(aluna) === professora));
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
          escala[aluna]._detalhes[hora] = { tipo: componentes.length > 1 ? "Prática + Solfejo" : componentes[0], componentes: [...componentes], horarios_componentes: horariosComponentes(hora, componentes, config.atividades), individual: true, turma, mesma_professora_componentes: mesmaProf };
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
    // Só redistribuímos as salas liberadas. Quem continua na Prática não muda;
    // quem volta da coletiva ocupa a sala de quem foi substituí-la.
    if (!estabilizarSalas(escala, horarios, individuais)) {
      return { escala: null, erros: ["Não foi possível distribuir as salas individuais sem conflito no mesmo horário. Confira as salas ativas e as professoras da escala."] };
    }
    if (regras.nao_repetir_sala !== false) otimizarSalasDoSabado(escala, individuais, escalasAnteriores, data);
    return { escala: Object.values(escala), erros: [] };
  }

  function otimizarSalasDoSabado(escala, salas, anteriores, data) {
    const porAluna = new Map(), porProfessora = new Map();
    const limite = dataBrParaData(data)?.getTime();
    const historico = [...anteriores].filter(item => {
      const dia = dataBrParaData(item.id)?.getTime();
      return dia && dia < limite;
    }).sort((a, b) => dataBrParaData(a.id) - dataBrParaData(b.id));
    for (const dia of historico) {
      const salasDoDia = new Map();
      for (const linha of dia.escala || []) for (const [hora, valor] of Object.entries(linha)) {
        if (hora === 'Aluna' || hora === '_detalhes' || typeof valor !== 'string' || !valor.includes('|')) continue;
        const sala = valor.split('|')[0].trim();
        if (!salas.includes(sala)) continue;
        const detalhe = linha._detalhes?.[hora] || {};
        if (detalhe.individual === false) continue;
        if (!porAluna.has(linha.Aluna)) porAluna.set(linha.Aluna, []);
        porAluna.get(linha.Aluna).push(sala);
        const professora = limpar(professoraDaPratica(valor, detalhe));
        if (!salasDoDia.has(professora)) salasDoDia.set(professora, new Set());
        salasDoDia.get(professora).add(sala);
      }
      for (const [professora, usadas] of salasDoDia) {
        if (!porProfessora.has(professora)) porProfessora.set(professora, []);
        porProfessora.get(professora).push(...usadas);
      }
    }
    // A permutação vale para o sábado INTEIRO. Não troca professoras/alunas,
    // nem salas coletivas; mantém também as substituições entre as aulas.
    const usos = salas.map(sala => Object.values(escala).flatMap(linha => Object.entries(linha._detalhes || {})
      .filter(([hora, detalhe]) => detalhe.individual && String(linha[hora]).split('|')[0].trim() === sala)
      .map(([hora, detalhe]) => ({ aluna: linha.Aluna, professora: limpar(professoraDaPratica(linha[hora], detalhe)) }))));
    const peso = usos.reduce((n, lista) => n + lista.length * 2, 0) + 1;
    const custos = usos.map(lista => salas.map(sala => {
      let custo = 0;
      for (const uso of lista) {
        const anterioresAluna = porAluna.get(uso.aluna) || [];
        const anterioresProf = porProfessora.get(uso.professora) || [];
        custo += Number(anterioresAluna.at(-1) === sala) * peso * peso;
        custo += Number(cicloSalas(anterioresAluna, salas).has(sala)) * peso;
        custo += Number(cicloSalas(anterioresProf, salas).has(sala));
      }
      return custo;
    }));
    const atribuicao = atribuirCustos(custos);
    if (!atribuicao) return;
    const novas = new Map(salas.map((sala, i) => [sala, salas[atribuicao[i]]]));
    for (const linha of Object.values(escala)) for (const [hora, detalhe] of Object.entries(linha._detalhes || {})) {
      if (!detalhe.individual) continue;
      const valor = String(linha[hora]), sala = novas.get(valor.split('|')[0].trim());
      if (!sala) continue;
      linha[hora] = `${sala} | ${valor.split('|').slice(1).join('|').trim()}`;
      detalhe.sala_fixa_professora = sala;
    }
  }

  function estabilizarSalas(mapa, horarios, salas) {
    let praticaAnterior = new Map(), coletivaAnterior = new Map();
    const ultimaSala = new Map(), alteracoes = [];
    for (const hora of horarios) {
      const individuais = [], coletivaAtual = new Map(), professoraPorColetiva = new Map();
      for (const linha of Object.values(mapa)) {
        const detalhe = linha._detalhes?.[hora];
        if (!detalhe) continue;
        const valor = String(linha[hora] || "");
        const sala = valor.split("|", 1)[0].trim();
        const professora = limpar(professoraDaPratica(valor, detalhe));
        if (detalhe.individual) individuais.push({ linha, detalhe, valor, sala, professora });
        else if (!detalhe.atividade_secretaria) {
          coletivaAtual.set(professora, sala);
          professoraPorColetiva.set(sala, professora);
        }
      }
      if (new Set(individuais.map((item) => item.professora)).size !== individuais.length) return false;
      const livres = new Set(salas), praticaAtual = new Map();
      const reservar = (item, sala) => {
        if (!livres.has(sala)) return false;
        praticaAtual.set(item.professora, sala);
        livres.delete(sala);
        return true;
      };
      // Primeiro protegemos TODAS as professoras que continuam na Prática.
      // A ordem das alunas no bloco não pode deslocar essas professoras.
      for (const item of individuais) {
        if (praticaAnterior.has(item.professora)
          && !reservar(item, praticaAnterior.get(item.professora))) return false;
      }
      // Troca direta: quem saiu da Teoria ocupa a sala de quem foi à Teoria.
      // Também seguimos cadeias (Teoria -> Solfejo -> Prática), sem mover
      // nenhuma sala coletiva e sem mudar as professoras/alunas escolhidas.
      for (const item of individuais) {
        if (praticaAtual.has(item.professora)) continue;
        let substituta = item.professora;
        const visitadas = new Set();
        while (coletivaAnterior.has(substituta) && !visitadas.has(substituta)) {
          visitadas.add(substituta);
          substituta = professoraPorColetiva.get(coletivaAnterior.get(substituta));
          if (praticaAnterior.has(substituta)) {
            reservar(item, praticaAnterior.get(substituta));
            break;
          }
        }
      }
      // Entradas, saídas antecipadas e salas vagas: somente as salas ainda
      // livres podem ser usadas. O primeiro bloco mantém a escolha histórica
      // feita por gerar(), permitindo rodar as salas no sábado seguinte.
      for (const item of individuais) {
        if (praticaAtual.has(item.professora)) continue;
        const preferencias = [ultimaSala.get(item.professora), item.sala, ...livres];
        if (!preferencias.some((sala) => reservar(item, sala))) return false;
      }
      for (const item of individuais) {
        const sala = praticaAtual.get(item.professora);
        ultimaSala.set(item.professora, sala);
        alteracoes.push({ ...item, hora, sala });
      }
      praticaAnterior = praticaAtual;
      coletivaAnterior = coletivaAtual;
    }
    // Só aplica depois de validar todos os blocos: falhas não deixam a escala
    // parcialmente alterada. Os componentes e horários originais são mantidos.
    for (const { linha, detalhe, hora, sala, valor } of alteracoes) {
      detalhe.sala_fixa_professora = sala;
      linha[hora] = `${sala} | ${valor.split("|").slice(1).join("|").trim()}`;
    }
    return true;
  }

  function editarAtividadeComplementar(escala, indice, hora, { atividade, sala, papel, responsavel }) {
    const linha = escala[indice], anterior = linha?._detalhes?.[hora];
    if (!anterior?.atividade_secretaria) throw new Error('Este atendimento não é uma atividade complementar.');
    if (!String(atividade || '').trim() || !String(sala || '').trim()) throw new Error('Informe o nome da atividade e a sala.');
    if (!['Professora', 'Secretaria'].includes(papel) || (papel === 'Professora' && !String(responsavel || '').trim())) throw new Error('Escolha uma responsável válida.');
    linha._detalhes[hora] = { ...anterior, tipo: atividade.trim(), sala: sala.trim(), responsavel_papel: papel,
      responsavel: String(responsavel || '').trim(), editada_manualmente: true };
    linha[hora] = `${sala.trim()} | ${String(responsavel || '').trim() || 'Secretarias'}`;
  }

  function preservarAtividadesComplementares(nova, anterior) {
    for (const linha of nova) {
      const salva = (anterior || []).find(item => item.Aluna === linha.Aluna);
      for (const [hora, detalhe] of Object.entries(salva?._detalhes || {})) {
        if (!detalhe.atividade_secretaria || !detalhe.editada_manualmente || !linha._detalhes?.[hora]) continue;
        linha[hora] = salva[hora];
        linha._detalhes[hora] = JSON.parse(JSON.stringify(detalhe));
      }
    }
    return nova;
  }

  window.RodizioEngine = { gerar, prepararModelo, horario, nomeArea, horariosComponentes, editarAtividadeComplementar, preservarAtividadesComplementares };
})();
