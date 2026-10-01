/* Conexão somente de identidade visual nesta etapa.
   Dados pedagógicos só serão carregados após a migração de autenticação e
   isolamento por GEM, para não reproduzir no navegador permissões antigas. */
(function () {
  const config = window.GEM_SUPABASE;
  let client = null;

  if (config?.url && config?.anonKey && window.supabase?.createClient) {
    client = window.supabase.createClient(config.url, config.anonKey, {
      auth: { persistSession: true, autoRefreshToken: true }
    });
  }

  async function obterCliente() {
    if (client) return client;
    if (!window.supabase?.createClient) throw new Error("A biblioteca de conexão não foi carregada.");
    const resposta = await fetch("/api/runtime-config", { cache: "no-store" });
    if (!resposta.ok) throw new Error("A configuração do aplicativo não está disponível.");
    const remoto = await resposta.json();
    if (!remoto?.url || !remoto?.anonKey) throw new Error("A configuração do aplicativo está incompleta.");
    client = window.supabase.createClient(remoto.url, remoto.anonKey, {
      auth: { persistSession: true, autoRefreshToken: true }
    });
    return client;
  }

  async function carregarIdentidade() {
    try {
      const banco = await obterCliente();
      const { data: visual, error } = await banco.from("config_visual_gem")
        .select("logo_path, updated_at").eq("id", 1).maybeSingle();
      if (error) throw error;

      let logoUrl = null;
      if (visual?.logo_path) {
        const { data: arquivo } = await banco.storage.from("logo_gem")
          .createSignedUrl(visual.logo_path, 3600);
        logoUrl = arquivo?.signedUrl || null;
      }
      return { connected: true, logoUrl };
    } catch (error) {
      console.warn("A identidade visual do GEM ainda não pôde ser carregada.", error);
      return { connected: false, message: "Não foi possível confirmar a conexão agora." };
    }
  }

  async function autenticar(login, senha) {
    const banco = await obterCliente();
    const usuario = String(login || "").trim().toLowerCase();
    if (!usuario || !senha) throw new Error("Informe usuário e senha.");

    // Contas novas (incluindo Master) usam Supabase Auth. A senha não passa
    // pelas tabelas pedagógicas e a sessão retornada é a sessão oficial.
    if (usuario.includes("@")) {
      const sessao = await banco.auth.signInWithPassword({ email: usuario, password: senha });
      if (!sessao.error && sessao.data?.user) {
        const { data: plataforma } = await banco.from("plataforma_usuarios")
          .select("nome, papel, ativo, status_convite")
          .eq("auth_user_id", sessao.data.user.id).maybeSingle();
        if (plataforma?.papel === "master" && plataforma.ativo && plataforma.status_convite === "ativo") {
          return { role: "Master", name: plataforma.nome, gem: null, sessao: true };
        }
      }
    }

    // A Secretaria já usa esta RPC no Streamlit. Ela devolve somente o perfil
    // correto após conferir a senha no banco.
    const secretaria = await banco.rpc("validar_acesso", { p_login: usuario, p_senha: senha });
    const contaSecretaria = secretaria.data?.[0];
    if (contaSecretaria?.perfil === "secretaria") {
      return { role: "Secretaria", name: contaSecretaria.nome || "Coordenação", gem: "Vila Verde" };
    }

    // Professoras e alunas usam a ponte criada na migration desta interface.
    const pessoas = await banco.rpc("validar_acesso_gem_pessoas", { p_login: usuario, p_senha: senha });
    const conta = pessoas.data?.[0];
    if (!conta) throw new Error("Usuário ou senha inválidos.");
    return {
      role: conta.perfil === "professora" ? "Professora" : "Aluna",
      name: conta.nome,
      gem: "Vila Verde"
    };
  }

  async function listarGems() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("gems")
      .select("id, nome, slug, ativo, created_at")
      .order("nome", { ascending: true });
    if (error) throw new Error("Não foi possível carregar os GEMs.");
    return data || [];
  }

  async function criarGem(nome, slug) {
    const banco = await obterCliente();
    const slugLimpo = String(slug || "").trim().toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    if (!String(nome || "").trim() || !slugLimpo) throw new Error("Informe o nome e um identificador para o GEM.");
    const { error } = await banco.from("gems").insert({ nome: String(nome).trim(), slug: slugLimpo });
    if (error) throw new Error(error.code === "23505" ? "Já existe um GEM com esse identificador." : "Não foi possível criar o GEM.");
  }

  function normalizar(texto) {
    return String(texto || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
  }

  function dataBr(iso) {
    if (!iso) return "";
    const [ano, mes, dia] = String(iso).split("-");
    return ano && mes && dia ? `${dia}/${mes}/${ano}` : String(iso);
  }

  function tipoDaAula(valor, detalhe) {
    if (detalhe?.tipo) return detalhe.tipo;
    const texto = normalizar(valor);
    if (texto.includes("SALA 8")) return "Teoria";
    if (texto.includes("SALA 9")) return "Solfejo Melódico";
    return "Prática";
  }

  async function agendaProfessora(professora, dataIso) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const { data: calendario, error } = await banco.from("calendario").select("id, escala").eq("id", data).maybeSingle();
    if (error) throw new Error("Não foi possível carregar a agenda desta data.");
    const escala = calendario?.escala || [];
    if (!escala.length) return [];
    const { data: alunas } = await banco.from("alunas").select("nome, turma");
    const turmaPorAluna = Object.fromEntries((alunas || []).map((aluna) => [aluna.nome, aluna.turma]));
    const nomeNormalizado = normalizar(professora);
    const aulas = [];
    const vistas = new Set();
    for (const linha of escala) {
      const detalhes = linha._detalhes || {};
      for (const horario of Object.keys(linha)) {
        if (["Aluna", "_detalhes"].includes(horario)) continue;
        const conteudo = String(linha[horario] || "");
        if (!conteudo || !normalizar(conteudo).includes(nomeNormalizado)) continue;
        const detalhe = detalhes[horario] || {};
        const componentes = detalhe.individual && Array.isArray(detalhe.componentes) ? detalhe.componentes : [tipoDaAula(conteudo, detalhe)];
        for (const tipo of componentes) {
          const professorasComponentes = detalhe.professoras_componentes || {};
          if (professorasComponentes[tipo] && normalizar(professorasComponentes[tipo]) !== nomeNormalizado) continue;
          const individual = Boolean(detalhe.individual) || tipo === "Prática";
          const chave = individual ? `${horario}|${tipo}|${linha.Aluna}` : `${horario}|${tipo}|${conteudo}`;
          if (vistas.has(chave)) continue;
          vistas.add(chave);
          const alunasDaAula = individual ? [linha.Aluna] : escala.filter((outra) => String(outra[horario] || "") === conteudo).map((outra) => outra.Aluna).filter(Boolean);
          aulas.push({ horario, tipo, local: conteudo.split("|")[0].trim(), individual, alunas: alunasDaAula, turma: turmaPorAluna[linha.Aluna] || "" });
        }
      }
    }
    return aulas.sort((a, b) => a.horario.localeCompare(b.horario));
  }

  async function dadosAluna(aluna) {
    const banco = await obterCliente();
    const [{ data: historico, error: erroHist }, { data: feitas }] = await Promise.all([
      banco.from("historico_geral").select("*").eq("Aluna", aluna).order("id", { ascending: false }),
      banco.from("licoes_feitas_alunas").select("*").eq("aluna", aluna)
    ]);
    if (erroHist) throw new Error("Não foi possível carregar o histórico da aluna.");
    return { historico: historico || [], feitas: feitas || [] };
  }

  async function marcarLicaoFeita(aluna, historicoId, feito) {
    const banco = await obterCliente();
    if (feito) {
      const { error } = await banco.from("licoes_feitas_alunas").upsert({ aluna, historico_id: String(historicoId) }, { onConflict: "aluna,historico_id" });
      if (error) throw new Error("Não foi possível marcar a lição como feita.");
    } else {
      const { error } = await banco.from("licoes_feitas_alunas").delete().eq("aluna", aluna).eq("historico_id", String(historicoId));
      if (error) throw new Error("Não foi possível desfazer a marcação.");
    }
  }

  async function boletimAluna(aluna) {
    const banco = await obterCliente();
    const [{ data: avaliacoes }, { data: notas }] = await Promise.all([
      banco.from("avaliacoes").select("*").order("data_avaliacao", { ascending: false }),
      banco.from("avaliacao_notas").select("*").eq("aluna", aluna)
    ]);
    return { avaliacoes: avaliacoes || [], notas: notas || [] };
  }

  function horarioDoBloco(bloco, indice) {
    const inicio = String(bloco["Início"] || bloco.inicio || "").trim();
    const fim = String(bloco.Fim || bloco.fim || "").trim();
    const nome = String(bloco.Bloco || bloco.nome || `Bloco ${indice + 1}`).trim();
    return inicio && fim ? `${inicio} - ${fim} (${nome})` : nome;
  }

  async function dadosRodizio(dataIso) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const [modelos, alunas, professoras, calendario, historicoEscalas, fixas, folgas] = await Promise.all([
      banco.from("modelos_logistica").select("*").order("vigencia_inicio", { ascending: false }),
      banco.from("alunas").select("nome,turma,ativo").order("nome"),
      banco.from("professoras").select("nome,ativo").order("nome"),
      banco.from("calendario").select("id,escala,modelo_logistica_id").eq("id", data).maybeSingle(),
      banco.from("calendario").select("id,escala").order("id", { ascending: true }),
      banco.from("professoras_fixas").select("aluna,professora"),
      banco.from("folgas_professoras").select("*").eq("data", dataIso).maybeSingle()
    ]);
    const falha = [modelos, alunas, professoras, calendario].find((resultado) => resultado.error)?.error;
    if (falha) throw new Error(`Não foi possível carregar a base do rodízio: ${falha.message || "verifique as migrations e permissões."}`);
    const turmas = {};
    (alunas.data || []).filter((aluna) => aluna.ativo !== false).forEach((aluna) => {
      const turma = aluna.turma || "Sem turma";
      (turmas[turma] ||= []).push(aluna.nome);
    });
    Object.values(turmas).forEach((lista) => lista.sort());
    const mapaFixas = Object.fromEntries((fixas.data || []).map((item) => [normalizar(item.aluna), item.professora]));
    return { data, modelos: modelos.data || [], turmas, professoras: (professoras.data || []).filter((professora) => professora.ativo !== false).map((professora) => professora.nome), escala: calendario.data?.escala || [], escalasAnteriores: historicoEscalas.data || [], modeloEscala: calendario.data?.modelo_logistica_id || null, fixas: mapaFixas, folga: folgas.data || null };
  }

  function modeloParaData(modelos, dataIso) {
    return (modelos || []).filter((modelo) => {
      if (!modelo.vigencia_inicio || !["programado", "vigente", "encerrado", "ativo"].includes(modelo.status)) return false;
      return modelo.vigencia_inicio <= dataIso && (!modelo.vigencia_fim || modelo.vigencia_fim >= dataIso);
    }).sort((a, b) => String(b.vigencia_inicio).localeCompare(String(a.vigencia_inicio)))[0] || null;
  }

  async function salvarRodizio(dataIso, modeloId, escala) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const { data: existente, error: consultaErro } = await banco.from("calendario").select("id").eq("id", data).maybeSingle();
    if (consultaErro) throw new Error("Não foi possível conferir a escala existente.");
    if (existente) throw new Error("Já existe um rodízio salvo nesta data. Ele não foi substituído.");
    const { error } = await banco.from("calendario").insert({ id: data, escala, modelo_logistica_id: modeloId });
    if (error) throw new Error(`Não foi possível salvar o rodízio: ${error.message}`);
  }

  async function dadosChamada(dataIso) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const [{ data: calendario, error: erroEscala }, { data: historico, error: erroHistorico }] = await Promise.all([
      banco.from("calendario").select("escala").eq("id", data).maybeSingle(),
      banco.from("historico_geral").select("id,Aluna,Status,Observacao").eq("Data", data).eq("Tipo", "Chamada")
    ]);
    if (erroEscala || erroHistorico) throw new Error("Não foi possível carregar a chamada desta data.");
    const alunas = [...new Set((calendario?.escala || []).map((linha) => linha.Aluna).filter(Boolean))].sort();
    const { data: perfis } = alunas.length ? await banco.from("alunas").select("nome,foto_path").in("nome", alunas) : { data: [] };
    const fotos = {};
    await Promise.all((perfis || []).filter((aluna) => aluna.foto_path).map(async (aluna) => {
      const { data: arquivo } = await banco.storage.from("fotos_alunas").createSignedUrl(aluna.foto_path, 3600);
      if (arquivo?.signedUrl) fotos[aluna.nome] = arquivo.signedUrl;
    }));
    return { alunas, chamadas: historico || [], fotos };
  }

  async function salvarChamada(dataIso, registros) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const { error: apagarErro } = await banco.from("historico_geral").delete().eq("Data", data).eq("Tipo", "Chamada");
    if (apagarErro) throw new Error("Não foi possível atualizar a chamada.");
    if (!registros.length) return;
    const linhas = registros.map((registro) => ({ Data: data, Aluna: registro.aluna, Tipo: "Chamada", Status: registro.status, Observacao: registro.observacao || "", Licao_Atual: "Presença em Aula" }));
    const { error } = await banco.from("historico_geral").insert(linhas);
    if (error) throw new Error("Não foi possível salvar a chamada.");
  }

  async function dadosVisaoGeral(dataIso) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const [{ data: escala, error: erroEscala }, { data: historico, error: erroHistorico }] = await Promise.all([
      banco.from("calendario").select("escala").eq("id", data).maybeSingle(),
      banco.from("historico_geral").select("*").eq("Data", data)
    ]);
    if (erroEscala || erroHistorico) throw new Error("Não foi possível carregar a visão diária.");
    return { escala: escala?.escala || [], historico: historico || [], data };
  }

  async function dadosPessoas() {
    const banco = await obterCliente();
    const [alunas, professoras, secretarias] = await Promise.all([
      banco.from("alunas").select("*").order("turma").order("nome"),
      banco.from("professoras").select("*").order("nome"),
      banco.from("secretarias").select("*").order("nome")
    ]);
    const falha = [alunas, professoras, secretarias].find((resultado) => resultado.error)?.error;
    if (falha) throw new Error(`Não foi possível carregar pessoas: ${falha.message}`);
    return { alunas: alunas.data || [], professoras: professoras.data || [], secretarias: secretarias.data || [] };
  }

  async function atualizarAtivoPessoa(tabela, id, ativo) {
    const banco = await obterCliente();
    const { error } = await banco.from(tabela).update({ ativo }).eq("id", id);
    if (error) throw new Error("Não foi possível atualizar o cadastro.");
  }

  async function dadosLicoesSecretaria(dataIso) {
    const banco = await obterCliente();
    let consulta = banco.from("historico_geral").select("*").order("id", { ascending: false });
    if (dataIso) consulta = consulta.eq("Data", dataBr(dataIso));
    const { data, error } = await consulta;
    if (error) throw new Error("Não foi possível carregar os registros pedagógicos.");
    return (data || []).filter((registro) => String(registro.Tipo || "").startsWith("Casa_") || String(registro.Tipo || "").startsWith("Analise_"));
  }

  async function dadosFolgas(dataIso) {
    const banco = await obterCliente();
    const { data, error } = await banco.from("folgas_professoras").select("*").eq("data", dataIso).maybeSingle();
    if (error) throw new Error("Não foi possível carregar as folgas.");
    return data || null;
  }

  async function salvarRegistroAula(registro) {
    const banco = await obterCliente();
    const data = dataBr(registro.data);
    const tipo = `Analise_${registro.tipo}`;
    const { error: apagarErro } = await banco.from("historico_geral").delete()
      .eq("Data", data).eq("Aluna", registro.aluna).eq("Tipo", tipo);
    if (apagarErro) throw new Error("Não foi possível atualizar o registro anterior desta aula.");
    const linha = {
      Data: data,
      Aluna: registro.aluna,
      Tipo: tipo,
      Instrutora: registro.instrutora,
      Licao_Atual: registro.licaoAtual || "",
      Licao_Casa: registro.licaoCasa || "",
      Dificuldades: registro.dificuldades || [],
      Observacao: registro.observacao || "",
      Status: registro.status || "Realizada"
    };
    const { error } = await banco.from("historico_geral").insert(linha);
    if (error) throw new Error("Não foi possível salvar o registro da aula.");
  }

  async function salvarFolgas(dataIso, professoras, observacao, responsavel) {
    const banco = await obterCliente();
    const linha = { data: dataIso, professoras: professoras || [], observacao: observacao || "" };
    if (responsavel) linha.coordenadora = responsavel;
    const { error } = await banco.from("folgas_professoras").upsert(linha, { onConflict: "data" });
    if (error) throw new Error("Não foi possível salvar as folgas.");
  }

  async function dadosLogistica() {
    const banco = await obterCliente();
    const [modelos, alunas, professoras] = await Promise.all([
      banco.from("modelos_logistica").select("*").order("vigencia_inicio", { ascending: false }),
      banco.from("alunas").select("nome,turma,ativo").order("turma").order("nome"),
      banco.from("professoras").select("nome,ativo").order("nome")
    ]);
    const falha = [modelos, alunas, professoras].find((resultado) => resultado.error)?.error;
    if (falha) throw new Error(`Não foi possível carregar a logística: ${falha.message}`);
    return { modelos: modelos.data || [], alunas: alunas.data || [], professoras: professoras.data || [] };
  }

  async function salvarModeloLogistica(modelo) {
    const banco = await obterCliente();
    const linha = { nome: modelo.nome, vigencia_inicio: modelo.vigencia_inicio, configuracao: modelo.configuracao, status: modelo.status || "rascunho" };
    if (modelo.id) {
      const { data: escalas, error: erroEscalas } = await banco.from("calendario").select("id").eq("modelo_logistica_id", modelo.id).limit(1);
      if (erroEscalas) throw new Error("Não foi possível verificar se este modelo já gerou rodízios.");
      if (!escalas?.length) {
        const { error } = await banco.from("modelos_logistica").update(linha).eq("id", modelo.id);
        if (error) throw new Error("Não foi possível atualizar o modelo.");
        return { revisao: false };
      }
      linha.status = "rascunho";
    }
    const { error } = await banco.from("modelos_logistica").insert(linha);
    if (error) throw new Error("Não foi possível salvar a revisão do modelo.");
    return { revisao: Boolean(modelo.id) };
  }

  async function alterarStatusModelo(id, status, vigenciaFim = null) {
    const banco = await obterCliente();
    const dados = { status };
    if (vigenciaFim) dados.vigencia_fim = vigenciaFim;
    const { error } = await banco.from("modelos_logistica").update(dados).eq("id", id);
    if (error) throw new Error("Não foi possível alterar o status do modelo.");
  }

  window.GemData = { carregarIdentidade, autenticar, listarGems, criarGem, agendaProfessora, dadosAluna, marcarLicaoFeita, boletimAluna, dadosRodizio, modeloParaData, horarioDoBloco, salvarRodizio, dadosChamada, salvarChamada, dadosVisaoGeral, dadosPessoas, atualizarAtivoPessoa, dadosLicoesSecretaria, dadosFolgas, salvarFolgas, dadosLogistica, salvarModeloLogistica, alterarStatusModelo, salvarRegistroAula, dataBr, normalizar };
})();
