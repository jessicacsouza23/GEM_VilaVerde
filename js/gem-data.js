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
    const [modelos, alunas, professoras, calendario, folgas] = await Promise.all([
      banco.from("modelos_logistica").select("*").order("vigencia_inicio", { ascending: false }),
      banco.from("alunas").select("nome,turma,ativo").order("nome"),
      banco.from("professoras").select("nome,ativo").order("nome"),
      banco.from("calendario").select("id,escala,modelo_logistica_id").eq("id", data).maybeSingle(),
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
    return { data, modelos: modelos.data || [], turmas, professoras: (professoras.data || []).filter((professora) => professora.ativo !== false).map((professora) => professora.nome), escala: calendario.data?.escala || [], modeloEscala: calendario.data?.modelo_logistica_id || null, folga: folgas.data || null };
  }

  function modeloParaData(modelos, dataIso) {
    return (modelos || []).filter((modelo) => {
      if (!modelo.vigencia_inicio || !["programado", "vigente", "encerrado", "ativo"].includes(modelo.status)) return false;
      return modelo.vigencia_inicio <= dataIso && (!modelo.vigencia_fim || modelo.vigencia_fim >= dataIso);
    }).sort((a, b) => String(b.vigencia_inicio).localeCompare(String(a.vigencia_inicio)))[0] || null;
  }

  window.GemData = { carregarIdentidade, autenticar, listarGems, criarGem, agendaProfessora, dadosAluna, marcarLicaoFeita, boletimAluna, dadosRodizio, modeloParaData, horarioDoBloco, dataBr };
})();
