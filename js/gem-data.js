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

      const caminhoLogo = visual?.logo_path || "logo_atual";
      const { data: arquivo } = await banco.storage.from("logo_gem")
        .createSignedUrl(caminhoLogo, 3600);
      const logoUrl = arquivo?.signedUrl || null;
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

  async function enviarLogoGem(arquivo) {
    if (!arquivo) throw new Error("Escolha a imagem da logo.");
    const banco = await obterCliente();
    const extensao = (arquivo.name.split(".").pop() || "png").toLowerCase();
    const caminho = `logo_atual.${extensao}`;
    const envio = await banco.storage.from("logo_gem").upload(caminho, arquivo, { upsert: true, contentType: arquivo.type || "image/png" });
    if (envio.error) throw new Error("Não foi possível enviar a logo.");
    const salvar = await banco.from("config_visual_gem").upsert({ id: 1, logo_path: caminho, updated_at: new Date().toISOString() });
    if (salvar.error) throw new Error("A logo foi enviada, mas não foi possível registrar a configuração.");
    return carregarIdentidade();
  }

  async function perfilSecretaria() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("secretaria_perfil").select("nome_exibicao,foto_path").eq("id", 1).maybeSingle();
    if (error && error.code !== "42P01") throw new Error("Não foi possível carregar o perfil da Coordenação.");
    if (!data?.foto_path) return data || {};
    const foto = await banco.storage.from("fotos_secretaria_gem").createSignedUrl(data.foto_path, 3600);
    return { ...data, fotoUrl: foto.data?.signedUrl || null };
  }

  async function perfilProfessora(nome) {
    const banco = await obterCliente();
    const { data, error } = await banco.from("professoras").select("*").eq("nome", nome).maybeSingle();
    if (error) throw new Error("Não foi possível carregar o perfil da professora.");
    if (!data?.foto_path) return data || {};
    const foto = await banco.storage.from("fotos_professoras").createSignedUrl(data.foto_path, 3600);
    return { ...data, fotoUrl: foto.data?.signedUrl || null };
  }

  async function salvarPerfilSecretaria({ nome, arquivo }) {
    const banco = await obterCliente();
    let foto_path;
    if (arquivo) {
      const extensao = (arquivo.name.split(".").pop() || "png").toLowerCase();
      foto_path = `coordenacao.${extensao}`;
      const envio = await banco.storage.from("fotos_secretaria_gem").upload(foto_path, arquivo, { upsert: true, contentType: arquivo.type || "image/png" });
      if (envio.error) throw new Error("Não foi possível enviar a foto da Coordenação.");
    }
    const dados = { id: 1, nome_exibicao: String(nome || "Coordenação").trim(), updated_at: new Date().toISOString() };
    if (foto_path) dados.foto_path = foto_path;
    const { error } = await banco.from("secretaria_perfil").upsert(dados);
    if (error) throw new Error("Execute a migration 004_perfil_secretaria_e_marca.sql no Supabase antes de salvar este perfil.");
    return perfilSecretaria();
  }

  async function dadosVisaoGeral(dataIso) {
    const banco = await obterCliente(); const data = dataBr(dataIso);
    const [calendario, historico] = await Promise.all([
      banco.from("calendario").select("escala").eq("id", data).maybeSingle(),
      banco.from("historico_geral").select("*").eq("Data", data).order("id", { ascending: true })
    ]);
    if (calendario.error || historico.error) throw new Error("Não foi possível carregar a visão geral desta data.");
    const alunas = [...new Set((calendario.data?.escala || []).map((linha) => linha.Aluna).filter(Boolean))];
    const chamadas = historico.data?.filter((item) => item.Tipo === "Chamada") || [];
    const ausentes = chamadas.filter((item) => ["Ausente", "Justificada"].includes(item.Status));
    const analises = historico.data?.filter((item) => String(item.Tipo || "").startsWith("Analise_")) || [];
    return { data, alunas, ausentes, analises, registros: historico.data || [] };
  }

  async function dadosPessoas() {
    const banco = await obterCliente();
    const [alunas, professoras, secretarias] = await Promise.all([
      banco.from("alunas").select("*").order("turma").order("nome"),
      banco.from("professoras").select("*").order("nome"),
      banco.from("secretarias").select("*").order("nome")
    ]);
    if (alunas.error || professoras.error) {
      const erro = alunas.error || professoras.error;
      throw new Error(`Não foi possível carregar turmas e pessoas: ${erro.message || "verifique as permissões do Supabase."}`);
    }
    return { alunas: alunas.data || [], professoras: professoras.data || [], secretarias: secretarias.data || [] };
  }

  async function salvarPessoa(tipo, dados, id, nomeAtual = "") {
    const banco = await obterCliente(); const tabela = ({ aluna: "alunas", professora: "professoras", secretaria: "secretarias" })[tipo];
    if (!tabela) throw new Error("Tipo de pessoa inválido.");
    const consulta = id ? banco.from(tabela).update(dados).eq("id", id) : nomeAtual ? banco.from(tabela).update(dados).eq("nome", nomeAtual) : banco.from(tabela).insert(dados);
    const { error } = await consulta; if (error) throw new Error(error.message || "Não foi possível salvar.");
  }

  async function dadosDocumentos() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("gabaritos").select("*").order("id", { ascending: false });
    if (error) throw new Error(`Não foi possível carregar documentos: ${error.message || "verifique as permissões."}`);
    return data || [];
  }

  async function enviarDocumento({ arquivo, titulo, disciplina, turma, aluna, observacao, visivel }) {
    if (!arquivo || !titulo) throw new Error("Informe o título e selecione o arquivo.");
    const banco = await obterCliente(); const caminho = `${crypto.randomUUID()}_${arquivo.name.replace(/[^a-zA-Z0-9._-]+/g, "_")}`;
    const envio = await banco.storage.from("gabaritos").upload(caminho, arquivo, { contentType: arquivo.type || "application/octet-stream" });
    if (envio.error) throw new Error("Não foi possível enviar o arquivo.");
    const { error } = await banco.from("gabaritos").insert({ titulo, disciplina, turma: turma || null, aluna: aluna || null, observacao: observacao || "", professora: "Secretaria", arquivo_path: caminho, arquivo_nome: arquivo.name, data_correcao: new Date().toISOString().slice(0, 10), visivel_alunas: Boolean(visivel) });
    if (error) throw new Error("O arquivo foi enviado, mas o documento não foi registrado.");
  }

  async function urlDocumento(caminho) {
    const banco = await obterCliente(); const { data, error } = await banco.storage.from("gabaritos").createSignedUrl(caminho, 3600);
    if (error) throw new Error("Não foi possível abrir este documento."); return data?.signedUrl;
  }

  async function dadosProvas() {
    const banco = await obterCliente(); const [avaliacoes, notas] = await Promise.all([banco.from("avaliacoes").select("*").order("data_avaliacao", { ascending: false }), banco.from("avaliacao_notas").select("*")]);
    if (avaliacoes.error || notas.error) throw new Error(`Não foi possível carregar provas: ${(avaliacoes.error || notas.error).message || "verifique as permissões."}`);
    return { avaliacoes: avaliacoes.data || [], notas: notas.data || [] };
  }

  async function criarProva(titulo, data) {
    const banco = await obterCliente(); const { error } = await banco.from("avaliacoes").insert({ titulo, data_avaliacao: data }); if (error) throw new Error("Não foi possível criar a avaliação.");
  }

  async function dadosAnalitico() {
    const banco = await obterCliente();
    const [historico, alunas, avaliacoes, notas, estudos] = await Promise.all([
      banco.from("historico_geral").select("*").order("id", { ascending: false }),
      banco.from("alunas").select("*").order("nome"),
      banco.from("avaliacoes").select("*").order("data_avaliacao", { ascending: false }),
      banco.from("avaliacao_notas").select("*"),
      banco.from("estudo_diario").select("*")
    ]);
    if (historico.error || alunas.error) throw new Error(`Não foi possível carregar o analítico: ${(historico.error || alunas.error).message || "verifique as permissões."}`);
    return { historico: historico.data || [], alunas: alunas.data || [], avaliacoes: avaliacoes.data || [], notas: notas.data || [], estudos: estudos.error ? [] : estudos.data || [] };
  }

  async function dadosCorrecoesLicoes() {
    const banco = await obterCliente();
    const [historico, alunas, secretarias] = await Promise.all([
      banco.from("historico_geral").select("*").in("Tipo", ["Casa_Apostila", "Casa_Teoria"]).order("id", { ascending: false }),
      banco.from("alunas").select("*").order("nome"),
      banco.from("secretarias").select("*").order("nome")
    ]);
    if (historico.error || alunas.error) throw new Error(`Não foi possível carregar as correções: ${(historico.error || alunas.error).message || "verifique as permissões."}`);
    return { historico: historico.data || [], alunas: alunas.data || [], secretarias: secretarias.error ? [] : secretarias.data || [] };
  }

  async function atualizarCorrecaoLicao(id, { status, observacao, secretaria, data }) {
    const banco = await obterCliente(); const { error } = await banco.from("historico_geral").update({ Status: status, Observacao: observacao ? `Sec: ${observacao}` : "", Secretaria: secretaria, Data: data }).eq("id", id);
    if (error) throw new Error("Não foi possível atualizar a correção.");
  }

  async function criarCorrecaoLicao({ aluna, tipo, licao, status, observacao, secretaria, data }) {
    const banco = await obterCliente(); const { error } = await banco.from("historico_geral").insert({ Aluna: aluna, Tipo: tipo, Data: data, Secretaria: secretaria, Licao_Casa: licao, Status: status, Observacao: observacao || "" });
    if (error) throw new Error("Não foi possível registrar a atividade.");
  }

  async function dadosLogistica() {
    const banco = await obterCliente(); const { data, error } = await banco.from("modelos_logistica").select("*").order("vigencia_inicio", { ascending: false });
    if (error) throw new Error(`Não foi possível carregar modelos: ${error.message || "execute a migration de logística."}`); return data || [];
  }

  async function salvarModeloLogistica({ id, nome, vigenciaInicio, configuracao, status = "rascunho" }) {
    const banco = await obterCliente(); const dados = { nome, vigencia_inicio: vigenciaInicio, configuracao, status, updated_at: new Date().toISOString() };
    if (id) dados.id = id;
    const { error } = await banco.from("modelos_logistica").upsert(dados, { onConflict: "id" });
    if (error) throw new Error(`Não foi possível salvar o modelo: ${error.message || "execute a migration de logística."}`);
  }

  async function alterarStatusModelo(id, status, vigenciaFim = null) {
    const banco = await obterCliente(); const dados = { status, updated_at: new Date().toISOString() }; if (vigenciaFim) dados.vigencia_fim = vigenciaFim;
    const { error } = await banco.from("modelos_logistica").update(dados).eq("id", id);
    if (error) throw new Error("Não foi possível alterar o status do modelo.");
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
    const { data: alunas } = await banco.from("alunas").select("nome, turma, foto_path");
    const turmaPorAluna = Object.fromEntries((alunas || []).map((aluna) => [aluna.nome, aluna.turma]));
    const fotoPorAluna = {};
    await Promise.all((alunas || []).filter((aluna) => aluna.foto_path).map(async (aluna) => {
      const foto = await banco.storage.from("fotos_alunas").createSignedUrl(aluna.foto_path, 3600);
      if (foto.data?.signedUrl) fotoPorAluna[aluna.nome] = foto.data.signedUrl;
    }));
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
          aulas.push({ horario, tipo, local: conteudo.split("|")[0].trim(), individual, alunas: alunasDaAula, fotos: Object.fromEntries(alunasDaAula.map((aluna) => [aluna, fotoPorAluna[aluna] || null])), turma: turmaPorAluna[linha.Aluna] || "" });
        }
      }
    }
    return aulas.sort((a, b) => a.horario.localeCompare(b.horario));
  }

  async function salvarRegistroAula({ dataIso, instrutora, tipo, alunas, material, conteudo, dificuldades, observacao, casaTipo, licaoCasa }) {
    const banco = await obterCliente(); const data = dataBr(dataIso), disciplina = tipo === "Canto" ? "Solfejo Melódico" : tipo;
    if (!alunas?.length || !conteudo?.trim()) throw new Error("Informe o conteúdo trabalhado.");
    for (const aluna of alunas) {
      const tipoAnalise = `Analise_${disciplina}`;
      const existente = await banco.from("historico_geral").select("id").eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoAnalise).eq("Instrutora", instrutora).order("id", { ascending: false }).limit(1);
      const registro = { Aluna: aluna, Data: data, Instrutora: instrutora, Tipo: tipoAnalise, Licao_Atual: material ? `${material}: ${conteudo}` : conteudo, Dificuldades: dificuldades || [], Observacao: observacao || "", Status: "Registrado" };
      const salvar = existente.data?.[0] ? await banco.from("historico_geral").update(registro).eq("id", existente.data[0].id) : await banco.from("historico_geral").insert(registro);
      if (salvar.error) throw new Error(`Não foi possível salvar o registro de ${aluna}.`);
      if (casaTipo && licaoCasa?.trim()) {
        const tipoCasa = `Casa_${casaTipo}`;
        const pendente = await banco.from("historico_geral").select("id").eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoCasa).order("id", { ascending: false }).limit(1);
        const casa = { Aluna: aluna, Data: data, Instrutora: instrutora, Tipo: tipoCasa, Licao_Atual: "Definido", Licao_Casa: licaoCasa.trim(), Dificuldades: [], Observacao: "", Status: "Pendente" };
        const salvarCasa = pendente.data?.[0] ? await banco.from("historico_geral").update(casa).eq("id", pendente.data[0].id) : await banco.from("historico_geral").insert(casa);
        if (salvarCasa.error) throw new Error(`A aula foi salva, mas não foi possível registrar a lição de ${aluna}.`);
      }
    }
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
    const [modelos, alunas, professoras, calendario, folgas, anteriores, fixas] = await Promise.all([
      banco.from("modelos_logistica").select("*").order("vigencia_inicio", { ascending: false }),
      banco.from("alunas").select("nome,turma,ativo").order("nome"),
      banco.from("professoras").select("nome,ativo").order("nome"),
      banco.from("calendario").select("id,escala,modelo_logistica_id").eq("id", data).maybeSingle(),
      banco.from("folgas_professoras").select("*").eq("data", dataIso).maybeSingle(),
      banco.from("calendario").select("id,escala").order("id", { ascending: true }),
      banco.from("professoras_fixas").select("aluna,professora")
    ]);
    const falha = [modelos, alunas, professoras, calendario].find((resultado) => resultado.error)?.error;
    if (falha) throw new Error(`Não foi possível carregar a base do rodízio: ${falha.message || "verifique as migrations e permissões."}`);
    const turmas = {};
    (alunas.data || []).filter((aluna) => aluna.ativo !== false).forEach((aluna) => {
      const turma = aluna.turma || "Sem turma";
      (turmas[turma] ||= []).push(aluna.nome);
    });
    Object.values(turmas).forEach((lista) => lista.sort());
    const professorasFixas = Object.fromEntries((fixas.data || []).filter((item) => item.aluna && item.professora).map((item) => [String(item.aluna).trim().toLowerCase(), item.professora]));
    return { data, modelos: modelos.data || [], turmas, professoras: (professoras.data || []).filter((professora) => professora.ativo !== false).map((professora) => professora.nome), escala: calendario.data?.escala || [], modeloEscala: calendario.data?.modelo_logistica_id || null, folga: folgas.data || null, escalasAnteriores: anteriores.data || [], professorasFixas };
  }

  async function salvarProfessorasFixas(mapa) {
    const banco = await obterCliente();
    const apagar = await banco.from("professoras_fixas").delete().neq("aluna", "");
    if (apagar.error) throw new Error("Não foi possível atualizar as professoras fixas.");
    const linhas = Object.entries(mapa || {}).filter(([, professora]) => professora).map(([aluna, professora]) => ({ aluna, professora }));
    if (!linhas.length) return;
    const inserir = await banco.from("professoras_fixas").insert(linhas);
    if (inserir.error) throw new Error("Não foi possível salvar as professoras fixas.");
  }

  async function salvarEscala(dataIso, escala, modeloId, motivoEdicao = "") {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const existente = await banco.from("calendario").select("id,escala,modelo_logistica_id").eq("id", data).maybeSingle();
    if (existente.error) throw new Error("Não foi possível conferir a escala já salva.");
    if (existente.data) {
      // Auditoria é adicional: se a migration ainda não tiver sido executada,
      // a edição permanece possível e o aplicativo explica isso ao usuário.
      const auditoria = await banco.from("calendario_edicoes").insert({ data_escala: data, escala_anterior: existente.data.escala || [], escala_nova: escala || [], motivo: motivoEdicao || "Correção pela Secretaria" });
      if (auditoria.error && auditoria.error.code !== "42P01") console.warn("Não foi possível registrar a auditoria da escala", auditoria.error);
      const atualizar = await banco.from("calendario").update({ escala, modelo_logistica_id: modeloId || existente.data.modelo_logistica_id }).eq("id", data);
      if (atualizar.error) throw new Error("Não foi possível salvar a correção da escala.");
      return "editada";
    }
    const inserir = await banco.from("calendario").insert({ id: data, escala, modelo_logistica_id: modeloId || null });
    if (inserir.error) throw new Error("Não foi possível salvar o rodízio.");
    return "criada";
  }

  function modeloParaData(modelos, dataIso) {
    return (modelos || []).filter((modelo) => {
      if (!modelo.vigencia_inicio || !["programado", "vigente", "encerrado", "ativo"].includes(modelo.status)) return false;
      return modelo.vigencia_inicio <= dataIso && (!modelo.vigencia_fim || modelo.vigencia_fim >= dataIso);
    }).sort((a, b) => String(b.vigencia_inicio).localeCompare(String(a.vigencia_inicio)))[0] || null;
  }

  async function dadosChamada(dataIso) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const [calendario, historico] = await Promise.all([
      banco.from("calendario").select("escala").eq("id", data).maybeSingle(),
      banco.from("historico_geral").select("Aluna,Status,Observacao").eq("Data", data).eq("Tipo", "Chamada")
    ]);
    if (calendario.error || historico.error) throw new Error("Não foi possível carregar a chamada desta data.");
    const alunas = [...new Set((calendario.data?.escala || []).map((linha) => linha.Aluna).filter(Boolean))].sort();
    const perfis = alunas.length ? await banco.from("alunas").select("nome,foto_path").in("nome", alunas) : { data: [] };
    const fotos = {};
    await Promise.all((perfis.data || []).filter((perfil) => perfil.foto_path).map(async (perfil) => {
      const arquivo = await banco.storage.from("fotos_alunas").createSignedUrl(perfil.foto_path, 3600);
      if (arquivo.data?.signedUrl) fotos[perfil.nome] = arquivo.data.signedUrl;
    }));
    return { alunas, chamadas: historico.data || [], fotos };
  }

  async function salvarChamada(dataIso, registros) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const apagar = await banco.from("historico_geral").delete().eq("Data", data).eq("Tipo", "Chamada");
    if (apagar.error) throw new Error("Não foi possível atualizar a chamada.");
    if (!registros.length) return;
    const inserir = await banco.from("historico_geral").insert(registros.map((registro) => ({ Data: data, Aluna: registro.aluna, Tipo: "Chamada", Status: registro.status, Observacao: registro.observacao || "", Licao_Atual: "Presença em Aula" })));
    if (inserir.error) throw new Error("Não foi possível salvar a chamada.");
  }

  window.GemData = { carregarIdentidade, enviarLogoGem, perfilSecretaria, salvarPerfilSecretaria, perfilProfessora, dadosVisaoGeral, dadosPessoas, salvarPessoa, dadosDocumentos, enviarDocumento, urlDocumento, dadosProvas, criarProva, dadosAnalitico, dadosCorrecoesLicoes, atualizarCorrecaoLicao, criarCorrecaoLicao, dadosLogistica, salvarModeloLogistica, alterarStatusModelo, autenticar, listarGems, criarGem, agendaProfessora, salvarRegistroAula, dadosAluna, marcarLicaoFeita, boletimAluna, dadosRodizio, modeloParaData, horarioDoBloco, dadosChamada, salvarChamada, salvarProfessorasFixas, salvarEscala, dataBr };
})();
