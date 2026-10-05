/* Conexão somente de identidade visual nesta etapa.
   Dados pedagógicos só serão carregados após a migração de autenticação e
   isolamento por GEM, para não reproduzir no navegador permissões antigas. */
(function () {
  const configLocal = window.GEM_SUPABASE;
  let client = null;
  let configPrincipal = null;
  let contextoGem = { nome: "GEM Vila Verde", slug: "vila-verde", externo: false, perfilSchema: "gem-pwa-v1" };
  let r2Habilitado = null;
  // v2 invalida somente URLs antigas do R2 que eram assinadas diretamente.
  const CACHE_URL_ASSINADA = "gem-url-assinada-v2:";

  function slugSolicitado() {
    const valor = new URLSearchParams(window.location.search).get("gem");
    return String(valor || "").trim().toLowerCase().replace(/[^a-z0-9-]/g, "");
  }

  function criarCliente(configuracao, persistir = true) {
    return window.supabase.createClient(configuracao.url, configuracao.anonKey, {
      auth: { persistSession: persistir, autoRefreshToken: persistir }
    });
  }

  async function obterConfigPrincipal() {
    if (configPrincipal?.url && configPrincipal?.anonKey) return configPrincipal;
    if (configLocal?.url && configLocal?.anonKey) {
      configPrincipal = configLocal;
      return configPrincipal;
    }
    const resposta = await fetch("/api/runtime-config", { cache: "no-store" });
    if (!resposta.ok) throw new Error("A configuração principal do aplicativo não está disponível.");
    const remoto = await resposta.json();
    if (!remoto?.url || !remoto?.anonKey) throw new Error("A configuração principal do aplicativo está incompleta.");
    configPrincipal = remoto;
    return configPrincipal;
  }

  async function r2EstaHabilitado() {
    // A sessão R2 da Vercel pertence à base padrão. GEMs externos usam o
    // Storage privado da própria unidade, sem misturar arquivos.
    if (contextoGem.externo) return false;
    if (r2Habilitado !== null) return r2Habilitado;
    try {
      const resposta = await fetch("/api/r2-status", { cache: "no-store", credentials: "same-origin" });
      r2Habilitado = Boolean(resposta.ok && (await resposta.json()).enabled);
    } catch (_) { r2Habilitado = false; }
    return r2Habilitado;
  }

  async function enviarFotoParaR2(tipo, arquivo) {
    if (!await r2EstaHabilitado()) return null;
    try {
      const resposta = await fetch("/api/r2-upload-url", {
        method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tipo, nome: arquivo.name, contentType: arquivo.type, tamanho: arquivo.size })
      });
      const dados = await resposta.json().catch(() => ({}));
      if (!resposta.ok || !dados.url || !dados.key) throw new Error(dados.error || "Não foi possível preparar o envio da foto.");
      const envio = await fetch(dados.url, { method: "PUT", headers: { "Content-Type": arquivo.type }, body: arquivo });
      if (!envio.ok) throw new Error("O R2 recusou o envio da foto.");
      return dados.key;
    } catch (erro) {
      // O R2 recebe o arquivo diretamente do navegador. Se uma regra CORS do
      // bucket estiver temporariamente incorreta, não bloqueamos o cadastro:
      // o fluxo continua pelo Storage privado já usado como reserva.
      console.warn("R2 indisponível para esta foto; usando o Storage de reserva.", erro);
      return null;
    }
  }

  // As fotos ficam em buckets privados. Sem esta memória, cada tela criava
  // uma URL assinada nova e o navegador baixava a mesma imagem novamente.
  // A URL continua privada e expira normalmente; apenas é reutilizada por 50
  // minutos no mesmo aparelho para reduzir a saída do Supabase.
  async function urlAssinadaEmCache(banco, bucket, caminho, segundos = 3600) {
    if (!caminho) return null;
    const chave = `${CACHE_URL_ASSINADA}${bucket}:${caminho}`;
    try {
      const salvo = JSON.parse(localStorage.getItem(chave) || "null");
      if (salvo?.url && Number(salvo.expiraEm) > Date.now()) return salvo.url;
    } catch (_) { /* cache local é apenas uma otimização */ }
    let url = null;
    if (String(caminho).startsWith("r2:")) {
      // A própria Vercel lê o objeto privado do R2 e o entrega no mesmo
      // domínio do GEM. Isso evita falhas de CORS e URLs assinadas expiradas
      // no elemento <img> do navegador.
      url = `/api/r2-file?key=${encodeURIComponent(caminho)}`;
    } else {
      const resposta = await banco.storage.from(bucket).createSignedUrl(caminho, segundos);
      url = resposta.data?.signedUrl || null;
    }
    if (url) {
      try { localStorage.setItem(chave, JSON.stringify({ url, expiraEm: Date.now() + Math.max(60, segundos - 600) * 1000 })); } catch (_) { /* sem espaço local: usa a URL normalmente */ }
    }
    return url;
  }

  async function obterCliente() {
    if (client) return client;
    if (!window.supabase?.createClient) throw new Error("A biblioteca de conexão não foi carregada.");
    const principal = await obterConfigPrincipal();
    const slug = slugSolicitado();
    if (slug && slug !== "vila-verde") {
      const plataforma = criarCliente(principal, false);
      const { data: gem, error } = await plataforma.from("gems")
        .select("nome,slug,ativo,supabase_url,supabase_anon_key,perfil_schema")
        .eq("slug", slug).eq("ativo", true).maybeSingle();
      if (error || !gem) throw new Error("Este GEM não foi encontrado ou está inativo.");
      if (!gem.supabase_url || !gem.supabase_anon_key) throw new Error("A base deste GEM ainda não foi vinculada pela conta Master.");
      contextoGem = { nome: gem.nome, slug: gem.slug, externo: true, perfilSchema: gem.perfil_schema || "gem-pwa-v1" };
      client = criarCliente({ url: gem.supabase_url, anonKey: gem.supabase_anon_key });
    } else {
      contextoGem = { nome: "GEM Vila Verde", slug: "vila-verde", externo: false, perfilSchema: "gem-pwa-v1" };
      client = criarCliente(principal);
    }
    return client;
  }

  async function carregarIdentidade() {
    try {
      const banco = await obterCliente();
      const { data: visual, error } = await banco.from("config_visual_gem")
        .select("logo_path, updated_at").eq("id", 1).maybeSingle();
      if (error) throw error;

      const caminhoLogo = visual?.logo_path || "logo_atual";
      const logoUrl = await urlAssinadaEmCache(banco, "logo_gem", caminhoLogo);
      return { connected: true, logoUrl, gem: { ...contextoGem } };
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
    // pelas tabelas pedagógicas e a sessão retornada é a sessão oficial. A
    // primeira administradora pode entrar por "master" ou pelo e-mail que
    // foi definido para ela na migration da plataforma.
    const emailAuth = usuario.includes("@") ? usuario
      : (!contextoGem.externo && usuario === "master" ? "jessicavitorioit@gmail.com" : "");
    if (emailAuth) {
      const sessao = await banco.auth.signInWithPassword({ email: emailAuth, password: senha });
      if (!sessao.error && sessao.data?.user) {
        if (!contextoGem.externo) {
          const { data: plataforma } = await banco.from("plataforma_usuarios")
            .select("nome, papel, ativo, status_convite")
            .eq("auth_user_id", sessao.data.user.id).maybeSingle();
          if (plataforma?.papel === "master" && plataforma.ativo && plataforma.status_convite === "ativo") {
            return { role: "Master", name: plataforma.nome, gem: null, sessao: true, externo: false };
          }
        }
      }
    }

    // A Secretaria já usa esta RPC no Streamlit. Ela devolve somente o perfil
    // correto após conferir a senha no banco.
    const secretaria = await banco.rpc("validar_acesso", { p_login: usuario, p_senha: senha });
    if (secretaria.error && [401, 403].includes(Number(secretaria.error.status))) {
      throw new Error("O GEM não conseguiu validar o acesso no Supabase. Confira a chave pública anon publicada e atualize a página.");
    }
    const contaSecretaria = secretaria.data?.[0];
    if (contaSecretaria?.perfil === "secretaria") {
      return { role: "Secretaria", name: contaSecretaria.nome || "Coordenação", gem: contextoGem.nome, externo: contextoGem.externo };
    }

    // Professoras e alunas usam a ponte criada na migration desta interface.
    const pessoas = await banco.rpc("validar_acesso_gem_pessoas", { p_login: usuario, p_senha: senha });
    if (pessoas.error) {
      throw new Error(`Não foi possível validar o acesso no Supabase: ${pessoas.error.message || "confira a chave anon e as migrations do GEM."}`);
    }
    const conta = pessoas.data?.[0];
    if (!conta) throw new Error("Usuário ou senha inválidos.");
    return {
      role: conta.perfil === "professora" ? "Professora" : "Aluna",
      name: conta.nome,
      gem: contextoGem.nome,
      externo: contextoGem.externo
    };
  }

  async function encerrarSessao() {
    const banco = await obterCliente();
    const { error } = await banco.auth.signOut();
    if (error) console.warn("Não foi possível encerrar a sessão do Supabase.", error);
    try { await fetch("/api/r2-session", { method: "DELETE", credentials: "same-origin" }); } catch (_) { /* sessão de fotos expira em no máximo oito horas */ }
  }

  async function iniciarSessaoR2(login, senha) {
    try {
      const resposta = await fetch("/api/r2-session", {
        method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login: String(login || "").trim().toLowerCase(), senha: String(senha || ""), gem: contextoGem.slug })
      });
      const dados = await resposta.json().catch(() => ({}));
      r2Habilitado = Boolean(dados.enabled);
      // Apesar do nome histórico da função, a rota também persiste a sessão
      // dos GEMs externos. O R2 continua restrito ao Vila Verde.
      return Boolean(resposta.ok && dados.session);
    } catch (_) { return false; }
  }

  async function restaurarSessao() {
    try {
      const resposta = await fetch("/api/r2-session", { method: "GET", credentials: "same-origin", cache: "no-store" });
      const dados = await resposta.json().catch(() => ({}));
      const perfis = ["Master", "Secretaria", "Professora", "Aluna"];
      if (!resposta.ok || !dados.session || !perfis.includes(dados.perfil)) return null;
      // Um cookie de outro GEM jamais restaura uma tela na base errada.
      if (String(dados.gem || "vila-verde") !== contextoGem.slug) return null;
      r2Habilitado = Boolean(dados.enabled);
      return { role: dados.perfil, name: dados.nome, gem: contextoGem.nome, externo: Boolean(dados.externo) };
    } catch (_) { return null; }
  }

  async function listarGems() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("gems")
      .select("id, nome, slug, ativo, perfil_schema, supabase_url, supabase_anon_key, created_at")
      .order("nome", { ascending: true });
    if (error) throw new Error("Não foi possível carregar os GEMs.");
    return data || [];
  }

  async function criarGem(nome, slug, conexao = {}) {
    const banco = await obterCliente();
    const slugLimpo = String(slug || "").trim().toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    if (!String(nome || "").trim() || !slugLimpo) throw new Error("Informe o nome e um identificador para o GEM.");
    const url = String(conexao.url || "").trim().replace(/\/$/, "");
    const anonKey = String(conexao.anonKey || "").trim();
    if (!/^https:\/\/[^\s]+\.supabase\.co$/i.test(url) || !anonKey) throw new Error("Informe a URL e a chave anon da base Supabase exclusiva deste GEM.");
    const { error } = await banco.from("gems").insert({ nome: String(nome).trim(), slug: slugLimpo, supabase_url: url, supabase_anon_key: anonKey, perfil_schema: "gem-pwa-v1" });
    if (error) throw new Error(error.code === "23505" ? "Já existe um GEM com esse identificador." : "Não foi possível criar o GEM.");
  }

  async function gemAtivo() {
    await obterCliente();
    return { ...contextoGem };
  }

  async function dadosPlataformaMaster() {
    const banco = await obterCliente();
    const [gems, usuarios, acessos] = await Promise.all([
      banco.from("gems").select("*").order("nome"),
      banco.from("plataforma_usuarios").select("*").order("created_at"),
      banco.from("gem_acessos").select("gem_id,papel,ativo")
    ]);
    const falha = [gems, usuarios, acessos].find((resultado) => resultado.error)?.error;
    if (falha) throw new Error("Não foi possível carregar a administração da plataforma.");
    return { gems: gems.data || [], usuarios: usuarios.data || [], acessos: acessos.data || [] };
  }

  function normalizar(texto) {
    return String(texto || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
  }

  async function enviarLogoGem(arquivo) {
    if (!arquivo) throw new Error("Escolha a imagem da logo.");
    const banco = await obterCliente();
    const extensao = (arquivo.name.split(".").pop() || "png").toLowerCase();
    let caminho = await enviarFotoParaR2("logo", arquivo);
    if (!caminho) {
      caminho = `logo_atual.${extensao}`;
      const envio = await banco.storage.from("logo_gem").upload(caminho, arquivo, { upsert: true, contentType: arquivo.type || "image/png" });
      if (envio.error) throw new Error("Não foi possível enviar a logo.");
    }
    try { localStorage.removeItem(`${CACHE_URL_ASSINADA}logo_gem:${caminho}`); } catch (_) { /* sem cache local */ }
    const salvar = await banco.from("config_visual_gem").upsert({ id: 1, logo_path: caminho, updated_at: new Date().toISOString() });
    if (salvar.error) throw new Error("A logo foi enviada, mas não foi possível registrar a configuração.");
    return carregarIdentidade();
  }

  async function perfilSecretaria() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("secretaria_perfil").select("nome_exibicao,foto_path").eq("id", 1).maybeSingle();
    if (error && error.code !== "42P01") throw new Error("Não foi possível carregar o perfil da Coordenação.");
    if (!data?.foto_path) return data || {};
    return { ...data, fotoUrl: await urlAssinadaEmCache(banco, "fotos_secretaria_gem", data.foto_path) };
  }

  async function perfilProfessora(nome) {
    const banco = await obterCliente();
    const { data, error } = await banco.from("professoras").select("*").eq("nome", nome).maybeSingle();
    if (error) throw new Error("Não foi possível carregar o perfil da professora.");
    if (!data?.foto_path) return data || {};
    return { ...data, fotoUrl: await urlAssinadaEmCache(banco, "fotos_professoras", data.foto_path) };
  }

  async function dadosMetodos() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("config_metodos").select("*").order("categoria").order("nome");
    if (error) throw new Error(error.code === "42P01" ? "A biblioteca de métodos ainda não foi criada no banco." : "Não foi possível carregar a biblioteca de métodos.");
    return data || [];
  }

  async function criarMetodo(nome, categoria) {
    const banco = await obterCliente();
    const registro = { nome: String(nome || "").trim(), categoria: String(categoria || "").trim() };
    if (!registro.nome || !registro.categoria) throw new Error("Informe o nome e a área do método.");
    const { error } = await banco.from("config_metodos").insert(registro);
    if (error) throw new Error("Não foi possível salvar o método.");
  }

  async function removerMetodo(metodo) {
    const banco = await obterCliente();
    let consulta = banco.from("config_metodos").delete();
    consulta = metodo.id != null ? consulta.eq("id", metodo.id) : consulta.eq("nome", metodo.nome).eq("categoria", metodo.categoria);
    const { error } = await consulta;
    if (error) throw new Error("Não foi possível remover o método.");
  }

  async function salvarPerfilSecretaria({ nome, arquivo }) {
    const banco = await obterCliente();
    let foto_path;
    if (arquivo) {
      const extensao = (arquivo.name.split(".").pop() || "png").toLowerCase();
      foto_path = await enviarFotoParaR2("secretaria", arquivo);
      if (!foto_path) {
        foto_path = `coordenacao.${extensao}`;
        const envio = await banco.storage.from("fotos_secretaria_gem").upload(foto_path, arquivo, { upsert: true, contentType: arquivo.type || "image/png" });
        if (envio.error) throw new Error("Não foi possível enviar a foto da Coordenação.");
      }
      try { localStorage.removeItem(`${CACHE_URL_ASSINADA}fotos_secretaria_gem:${foto_path}`); } catch (_) { /* sem cache local */ }
    }
    const dados = { id: 1, nome_exibicao: String(nome || "Coordenação").trim(), updated_at: new Date().toISOString() };
    if (foto_path) dados.foto_path = foto_path;
    const { error } = await banco.from("secretaria_perfil").upsert(dados);
    if (error) throw new Error("Execute a migration 004_perfil_secretaria_e_marca.sql no Supabase antes de salvar este perfil.");
    return perfilSecretaria();
  }

  async function dadosVisaoGeral(dataIso) {
    const banco = await obterCliente(); const data = dataBr(dataIso);
    const [calendario, historico, estudos] = await Promise.all([
      banco.from("calendario").select("escala").eq("id", data).maybeSingle(),
      banco.from("historico_geral").select("*").eq("Data", data).order("id", { ascending: true }),
      banco.from("estudo_diario").select("*").eq("data", data)
    ]);
    if (calendario.error || historico.error) throw new Error("Não foi possível carregar a visão geral desta data.");
    const alunas = [...new Set((calendario.data?.escala || []).map((linha) => linha.Aluna).filter(Boolean))];
    const chamadas = historico.data?.filter((item) => item.Tipo === "Chamada") || [];
    const ausentes = chamadas.filter((item) => ["Ausente", "Justificada"].includes(item.Status));
    const analises = historico.data?.filter((item) => String(item.Tipo || "").startsWith("Analise_")) || [];
    return { data, escala: calendario.data?.escala || [], alunas, ausentes, analises, registros: historico.data || [], estudos: estudos.error ? [] : estudos.data || [] };
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

  async function fotosPessoas() {
    const banco = await obterCliente();
    const [alunas, professoras] = await Promise.all([
      banco.from("alunas").select("nome, foto_path").not("foto_path", "is", null),
      banco.from("professoras").select("nome, foto_path").not("foto_path", "is", null)
    ]);
    const carregar = async (registros, bucket) => {
      const resultado = {};
      await Promise.all((registros || []).map(async (pessoa) => {
        try {
          const url = await urlAssinadaEmCache(banco, bucket, pessoa.foto_path);
          if (url) resultado[pessoa.nome] = url;
        } catch (_) { /* Uma foto indisponível não impede o cadastro de abrir. */ }
      }));
      return resultado;
    };
    return {
      aluna: alunas.error ? {} : await carregar(alunas.data, "fotos_alunas"),
      professora: professoras.error ? {} : await carregar(professoras.data, "fotos_professoras")
    };
  }

  async function dadosCoordenacoesProfessoras() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("coordenacoes_professoras").select("*").order("inicio", { ascending: false });
    if (error) {
      if (["42P01", "PGRST205"].includes(error.code)) throw new Error("A tabela da professora coordenadora ainda não existe no Supabase. Execute a migration 009 e atualize a página.");
      throw new Error(`Não foi possível carregar as coordenações (${error.code || "erro"}): ${error.message || "verifique as permissões da tabela."}`);
    }
    return data || [];
  }

  async function definirCoordenadoraProfessora({ professora, inicio, fim, periodo }) {
    if (!String(professora || "").trim() || !inicio || !fim) throw new Error("Escolha a professora e informe o início e o fim da coordenação.");
    if (fim < inicio) throw new Error("A data final não pode ser anterior à data inicial.");
    const banco = await obterCliente();
    const existentes = await dadosCoordenacoesProfessoras();
    // Uma professora coordenadora por vez. Ao trocar a responsável, o período
    // anterior termina no dia anterior ao início do novo período, sem apagar
    // o histórico de quem já coordenou.
    const diaAnterior = new Date(`${inicio}T12:00:00`);
    diaAnterior.setDate(diaAnterior.getDate() - 1);
    const fimAnterior = diaAnterior.toISOString().slice(0, 10);
    const sobrepostas = existentes.filter((item) => item.inicio <= fim && item.fim >= inicio);
    for (const item of sobrepostas) {
      const { error } = await banco.from("coordenacoes_professoras").update({ fim: fimAnterior }).eq("id", item.id);
      if (error) throw new Error("Não foi possível encerrar a coordenação anterior.");
    }
    const { error } = await banco.from("coordenacoes_professoras").insert({ professora: String(professora).trim(), inicio, fim, periodo: String(periodo || "Coordenação").trim() || "Coordenação" });
    if (error) throw new Error("Não foi possível definir a professora coordenadora.");
  }

  async function professoraEhCoordenadora(nome, dataIso = new Date().toISOString().slice(0, 10)) {
    try {
      const coordenacoes = await dadosCoordenacoesProfessoras();
      const nomeNormalizado = normalizar(nome);
      return coordenacoes.some((item) => normalizar(item.professora) === nomeNormalizado && item.inicio <= dataIso && item.fim >= dataIso);
    } catch (error) {
      // A migration não impede o login de professoras que já usam o GEM.
      if (/migration 009/i.test(error.message || "")) return false;
      throw error;
    }
  }

  async function salvarPessoa(tipo, dados, id, nomeAtual = "") {
    const banco = await obterCliente(); const tabela = ({ aluna: "alunas", professora: "professoras", secretaria: "secretarias" })[tipo];
    if (!tabela) throw new Error("Tipo de pessoa inválido.");
    const consulta = id ? banco.from(tabela).update(dados).eq("id", id) : nomeAtual ? banco.from(tabela).update(dados).eq("nome", nomeAtual) : banco.from(tabela).insert(dados);
    const { error } = await consulta; if (error) throw new Error(error.message || "Não foi possível salvar.");
  }

  async function enviarFotoPessoa(tipo, arquivo) {
    if (!arquivo) return null;
    if (!['aluna', 'professora'].includes(tipo)) throw new Error("Foto disponível somente para aluna ou professora.");
    const extensao = String(arquivo.name || "").split(".").pop().toLowerCase();
    if (!['jpg', 'jpeg', 'png', 'webp'].includes(extensao)) throw new Error("Envie uma foto JPG, PNG ou WEBP.");
    // Fotos de celular muito grandes multiplicam a saída do Storage. O limite
    // evita cadastrar uma foto desproporcional para o avatar do sistema.
    if (arquivo.size > 5 * 1024 * 1024) throw new Error("A foto deve ter no máximo 5 MB.");
    const banco = await obterCliente();
    const caminhoR2 = await enviarFotoParaR2(tipo, arquivo);
    if (caminhoR2) return caminhoR2;
    const bucket = tipo === 'aluna' ? 'fotos_alunas' : 'fotos_professoras';
    const caminho = `${crypto.randomUUID()}_${String(arquivo.name).normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').replace(/[^a-zA-Z0-9._-]+/g, '_')}`;
    const { error } = await banco.storage.from(bucket).upload(caminho, arquivo, { contentType: arquivo.type || `image/${extensao === 'jpg' ? 'jpeg' : extensao}` });
    if (error) throw new Error(error.message?.toLowerCase().includes("bucket") ? "O armazenamento de fotos ainda não está configurado. Execute a migration 007 no Supabase." : "Não foi possível enviar a foto.");
    return caminho;
  }

  async function dadosDocumentos() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("gabaritos").select("*").order("id", { ascending: false });
    if (error) throw new Error(`Não foi possível carregar documentos: ${error.message || "verifique as permissões."}`);
    return data || [];
  }

  async function enviarDocumento({ arquivo, titulo, disciplina, data, turma, aluna, observacao, visivel, professora = "Secretaria" }) {
    if (!arquivo || !titulo) throw new Error("Informe o título e selecione o arquivo.");
    const banco = await obterCliente(); const caminho = `${crypto.randomUUID()}_${arquivo.name.replace(/[^a-zA-Z0-9._-]+/g, "_")}`;
    const envio = await banco.storage.from("gabaritos").upload(caminho, arquivo, { contentType: arquivo.type || "application/octet-stream" });
    if (envio.error) throw new Error("Não foi possível enviar o arquivo.");
    const { error } = await banco.from("gabaritos").insert({ titulo, disciplina, turma: turma || null, aluna: aluna || null, observacao: observacao || "", professora, arquivo_path: caminho, arquivo_nome: arquivo.name, data_correcao: data || new Date().toISOString().slice(0, 10), visivel_alunas: Boolean(visivel) });
    if (error) throw new Error("O arquivo foi enviado, mas o documento não foi registrado.");
  }

  async function removerDocumento(documento) {
    if (!documento?.id || !documento?.arquivo_path) throw new Error("Documento inválido para exclusão.");
    const banco = await obterCliente();
    const { error: apagarCadastro } = await banco.from("gabaritos").delete().eq("id", documento.id);
    if (apagarCadastro) throw new Error("Não foi possível excluir o cadastro do documento.");
    // O cadastro é apagado primeiro para que o arquivo não siga aparecendo no
    // aplicativo mesmo se o Storage estiver temporariamente indisponível.
    const { error: apagarArquivo } = await banco.storage.from("gabaritos").remove([documento.arquivo_path]);
    if (apagarArquivo) console.warn("Cadastro excluído, mas o arquivo não pôde ser removido do Storage.", apagarArquivo);
  }

  async function urlDocumento(caminho) {
    const banco = await obterCliente(); const { data, error } = await banco.storage.from("gabaritos").createSignedUrl(caminho, 3600);
    if (error) throw new Error("Não foi possível abrir este documento."); return data?.signedUrl;
  }

  async function dadosProvas() {
    const banco = await obterCliente(); const [avaliacoes, notas, responsaveis] = await Promise.all([banco.from("avaliacoes").select("*").order("data_avaliacao", { ascending: false }), banco.from("avaliacao_notas").select("*"), banco.from("avaliacao_responsaveis").select("*")]);
    if (avaliacoes.error || notas.error || responsaveis.error) throw new Error(`Não foi possível carregar provas: ${(avaliacoes.error || notas.error || responsaveis.error).message || "verifique as permissões e a tabela de responsáveis."}`);
    return { avaliacoes: avaliacoes.data || [], notas: notas.data || [], responsaveis: responsaveis.data || [] };
  }

  async function criarProva(titulo, data) {
    const banco = await obterCliente(); const { data: criada, error } = await banco.from("avaliacoes").insert({ titulo, data_avaliacao: data }).select().single(); if (error) throw new Error("Não foi possível criar a avaliação."); return criada;
  }

  async function salvarResponsaveisAvaliacao(avaliacaoId, responsaveis) {
    const linhas = (responsaveis || []).filter((item) => item.aluna && item.disciplina && item.professora).map((item) => ({ avaliacao_id: avaliacaoId, aluna: item.aluna, disciplina: item.disciplina, professora: item.professora }));
    if (!linhas.length) throw new Error("Escolha ao menos uma professora responsável.");
    const banco = await obterCliente(); const { error } = await banco.from("avaliacao_responsaveis").upsert(linhas, { onConflict: "avaliacao_id,aluna,disciplina" });
    if (error) throw new Error("Não foi possível salvar as professoras responsáveis.");
  }

  async function removerProva(avaliacaoId) {
    const banco = await obterCliente(); const { error } = await banco.from("avaliacoes").delete().eq("id", avaliacaoId);
    if (error) throw new Error("Não foi possível excluir a avaliação.");
  }

  async function salvarNotaAvaliacao({ avaliacaoId, aluna, disciplina, nota, professora = null }) {
    const banco = await obterCliente();
    const registro = { avaliacao_id: avaliacaoId, aluna, disciplina, nota: Number(nota) };
    if (professora) registro.professora = professora;
    if (!registro.aluna || !registro.disciplina || !Number.isFinite(registro.nota)) throw new Error("Informe aluna, disciplina e nota.");
    const existente = await banco.from("avaliacao_notas").select("id").eq("avaliacao_id", avaliacaoId).eq("aluna", aluna).eq("disciplina", disciplina).maybeSingle();
    const { error } = existente.data?.id ? await banco.from("avaliacao_notas").update(registro).eq("id", existente.data.id) : await banco.from("avaliacao_notas").insert(registro);
    if (error) throw new Error("Não foi possível salvar a nota.");
  }

  async function dadosMensagens() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("mensagens").select("*").order("id", { ascending: true });
    if (error) throw new Error(error.code === "42P01" ? "A tabela de mensagens ainda não está criada ou liberada no Supabase." : "Não foi possível carregar as mensagens.");
    return data || [];
  }

  async function enviarMensagem(de, para, texto) {
    const banco = await obterCliente();
    const mensagem = String(texto || "").trim();
    if (!mensagem) throw new Error("Escreva uma mensagem antes de enviar.");
    const { error } = await banco.from("mensagens").insert({ de, para, texto: mensagem });
    if (error) throw new Error("Não foi possível enviar a mensagem.");
  }

  async function dadosAnalitico() {
    const banco = await obterCliente();
    const [historico, alunas, avaliacoes, notas, estudos, objetivos] = await Promise.all([
      banco.from("historico_geral").select("*").order("id", { ascending: false }),
      banco.from("alunas").select("*").order("nome"),
      banco.from("avaliacoes").select("*").order("data_avaliacao", { ascending: false }),
      banco.from("avaliacao_notas").select("*"),
      banco.from("estudo_diario").select("*"),
      banco.from("objetivos_pedagogicos").select("*")
    ]);
    if (historico.error || alunas.error) throw new Error(`Não foi possível carregar o analítico: ${(historico.error || alunas.error).message || "verifique as permissões."}`);
    return { historico: historico.data || [], alunas: alunas.data || [], avaliacoes: avaliacoes.data || [], notas: notas.data || [], estudos: estudos.error ? [] : estudos.data || [], objetivos: objetivos.error ? [] : objetivos.data || [] };
  }

  async function salvarObjetivoPedagogico({ aluna, texto, professora }) {
    const banco = await obterCliente();
    if (!String(aluna || "").trim()) throw new Error("Escolha a aluna antes de salvar o objetivo.");
    const registro = { aluna: String(aluna).trim(), texto: String(texto || "").trim(), professora: String(professora || "Secretaria").trim() };
    const { error } = await banco.from("objetivos_pedagogicos").upsert(registro, { onConflict: "aluna" });
    if (error) throw new Error(error.code === "42P01" ? "A tabela de objetivos pedagógicos ainda não existe nesta base do GEM." : "Não foi possível salvar o objetivo pedagógico.");
  }

  async function dadosCorrecoesLicoes() {
    const banco = await obterCliente();
    const [historico, alunas, secretarias] = await Promise.all([
      // A Secretaria corrige folhas avulsas de Teoria encaminhadas para ela
      // e as apostilas de Prática. Somente os métodos voltam à professora.
      // Casa_Apostila_Prof é lida também para trazer para a Secretaria as
      // apostilas cadastradas antes desta regra ser corrigida no PWA.
      banco.from("historico_geral").select("*").in("Tipo", ["Casa_Teoria", "Casa_Apostila", "Casa_Apostila_Prof"]).order("id", { ascending: false }),
      banco.from("alunas").select("*").order("nome"),
      banco.from("secretarias").select("*").order("nome")
    ]);
    if (historico.error || alunas.error) throw new Error(`Não foi possível carregar as correções: ${(historico.error || alunas.error).message || "verifique as permissões."}`);
    return { historico: historico.data || [], alunas: alunas.data || [], secretarias: secretarias.error ? [] : secretarias.data || [] };
  }

  async function dadosAjustes() {
    const banco = await obterCliente();
    const [historico, alunas] = await Promise.all([
      banco.from("historico_geral").select("*").order("id", { ascending: false }),
      banco.from("alunas").select("id,nome,ativo").order("nome")
    ]);
    if (historico.error || alunas.error) throw new Error(`Não foi possível carregar os ajustes: ${(historico.error || alunas.error).message || "verifique as permissões."}`);
    return { historico: historico.data || [], alunas: alunas.data || [] };
  }

  async function contarRegistrosOrfaos() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("historico_geral").select("id").is("Tipo", null);
    if (error) throw new Error("Não foi possível consultar os registros órfãos.");
    return (data || []).length;
  }

  async function limparRegistrosOrfaos() {
    const banco = await obterCliente();
    const { error } = await banco.from("historico_geral").delete().is("Tipo", null);
    if (error) throw new Error("Não foi possível apagar os registros órfãos.");
  }

  async function removerRegistroHistorico(id) {
    if (!id) throw new Error("Registro inválido.");
    const banco = await obterCliente();
    const { error } = await banco.from("historico_geral").delete().eq("id", id);
    if (error) throw new Error("Não foi possível apagar este registro.");
  }

  async function dadosAuditoriaRodizio() {
    const banco = await obterCliente();
    const [calendario, fixas] = await Promise.all([
      banco.from("calendario").select("id,escala").order("id", { ascending: true }),
      banco.from("professoras_fixas").select("aluna,professora")
    ]);
    if (calendario.error) throw new Error("Não foi possível carregar as escalas salvas para a auditoria.");
    if (fixas.error && !["42P01", "PGRST205"].includes(fixas.error.code)) throw new Error("Não foi possível carregar as professoras fixas para a auditoria.");
    return { escalas: calendario.data || [], fixas: fixas.data || [] };
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
    const { data, error } = await banco.from("modelos_logistica").upsert(dados, { onConflict: "id" }).select().maybeSingle();
    if (error) throw new Error(`Não foi possível salvar o modelo: ${error.message || "execute a migration de logística."}`);
    return data;
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
      const url = await urlAssinadaEmCache(banco, "fotos_alunas", aluna.foto_path);
      if (url) fotoPorAluna[aluna.nome] = url;
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

  async function salvarRegistroAula({ dataIso, instrutora, tipo, alunas, material, conteudo, dificuldades, observacao, registrosPorAluna, casaTipo, licaoCasa, limparCasas = [] }) {
    const banco = await obterCliente(); const data = dataBr(dataIso), disciplina = tipo === "Canto" ? "Solfejo Melódico" : tipo;
    if (!alunas?.length || !conteudo?.trim()) throw new Error("Informe o conteúdo trabalhado.");
    for (const aluna of alunas) {
      const registroIndividual = registrosPorAluna?.[aluna] || {};
      const tipoAnalise = `Analise_${disciplina}`;
      const existente = await banco.from("historico_geral").select("id,Licao_Atual").eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoAnalise).eq("Instrutora", instrutora).order("id", { ascending: false });
      const dificuldadesDaAluna = registroIndividual.dificuldades ?? dificuldades ?? [];
      const temDificuldade = dificuldadesDaAluna.some((dificuldade) => String(dificuldade).trim() && String(dificuldade).trim() !== "Não apresentou dificuldades");
      const registro = {
        Aluna: aluna, Data: data, Instrutora: instrutora, Tipo: tipoAnalise,
        Licao_Atual: material ? `${material}: ${conteudo}` : conteudo,
        Dificuldades: dificuldadesDaAluna,
        Observacao: registroIndividual.observacao ?? observacao ?? "",
        Status: temDificuldade ? "Realizada - com dificuldades" : "Realizada - sem pendência"
      };
      // Em uma mesma aula a professora pode registrar mais de um material.
      // Só atualizamos o cartão que corresponde ao mesmo material, como no app.py.
      const existenteMesmoMaterial = (existente.data || []).find((item) => !material || String(item.Licao_Atual || "").trim().startsWith(`${material}:`));
      const salvar = existenteMesmoMaterial ? await banco.from("historico_geral").update(registro).eq("id", existenteMesmoMaterial.id) : await banco.from("historico_geral").insert(registro);
      if (salvar.error) throw new Error(`Não foi possível salvar o registro de ${aluna}.`);
      const tipoCasa = casaTipo ? `Casa_${casaTipo}` : "";
      if (tipoCasa && licaoCasa?.trim()) {
        const pendente = await banco.from("historico_geral").select("id").eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoCasa).order("id", { ascending: false }).limit(1);
        const casa = { Aluna: aluna, Data: data, Instrutora: instrutora, Tipo: tipoCasa, Licao_Atual: "Definido", Licao_Casa: licaoCasa.trim(), Dificuldades: [], Observacao: "", Status: "Pendente" };
        const salvarCasa = pendente.data?.[0] ? await banco.from("historico_geral").update(casa).eq("id", pendente.data[0].id) : await banco.from("historico_geral").insert(casa);
        if (salvarCasa.error) throw new Error(`A aula foi salva, mas não foi possível registrar a lição de ${aluna}.`);
      }
      // Reabrir uma aula e remover/trocar a lição precisa refletir no mesmo
      // histórico. No Streamlit, uma lição apagada não fica pendente para
      // sempre; fazemos a mesma limpeza limitada à disciplina da tela atual.
      const tiposRemover = [...new Set([...(limparCasas || []), ...(tipoCasa && !String(licaoCasa || "").trim() ? [tipoCasa] : [])])]
        .filter((tipo) => tipo && tipo !== (String(licaoCasa || "").trim() ? tipoCasa : ""));
      for (const tipoRemover of tiposRemover) {
        const apagarCasa = await banco.from("historico_geral").delete().eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoRemover);
        if (apagarCasa.error) throw new Error(`A aula foi salva, mas não foi possível atualizar a lição de ${aluna}.`);
      }
    }
  }

  // Prática é diferente das demais disciplinas: uma mesma aula pode trabalhar
  // Apostila e mais de um método. Cada material vira seu próprio registro
  // Analise_Prática, exatamente como ocorre no app.py, para não misturar
  // páginas, dificuldades e exercícios de livros diferentes.
  async function salvarRegistrosPratica({ dataIso, instrutora, aluna, materiais, observacao = "" }) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const lista = (materiais || []).filter((item) => String(item?.material || "").trim() && String(item?.conteudo || "").trim());
    if (!aluna || !lista.length) throw new Error("Informe ao menos um método/apostila e a página ou lição trabalhada.");

    // O cartão de um material pode ser removido ao corrigir um registro já
    // salvo. Espelhamos o editor do Streamlit: o método removido deixa de
    // existir no histórico daquela aula, inclusive sua lição pendente.
    const { data: registrosDoDia, error: erroRegistrosDoDia } = await banco.from("historico_geral").select("id,Licao_Atual")
      .eq("Aluna", aluna).eq("Data", data).eq("Tipo", "Analise_Prática").eq("Instrutora", instrutora);
    if (erroRegistrosDoDia) throw new Error("Não foi possível preparar a atualização dos materiais de Prática.");
    const materiaisAtuais = new Set(lista.map((item) => String(item.material).trim()));
    for (const registro of (registrosDoDia || [])) {
      const materialAnterior = String(registro.Licao_Atual || "").split(":", 1)[0].trim();
      if (!materialAnterior || materiaisAtuais.has(materialAnterior)) continue;
      const apagarAnalise = await banco.from("historico_geral").delete().eq("id", registro.id);
      if (apagarAnalise.error) throw new Error(`Não foi possível remover o material ${materialAnterior}.`);
      const tipoCasaAnterior = materialAnterior === "Apostila" ? "Casa_Apostila" : `Casa_Metodo_${materialAnterior}`;
      const apagarCasa = await banco.from("historico_geral").delete().eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoCasaAnterior);
      if (apagarCasa.error) throw new Error(`O material foi removido, mas não foi possível remover sua lição de casa.`);
      const apagarExercicios = await banco.from("exercicios_registro").delete().eq("aluna", aluna).eq("data", data).eq("disciplina", "Prática").eq("material", materialAnterior);
      if (apagarExercicios.error && apagarExercicios.error.code !== "42P01") throw new Error(`O material foi removido, mas não foi possível remover seus exercícios.`);
    }

    for (const item of lista) {
      const material = String(item.material).trim();
      const conteudo = String(item.conteudo).trim();
      const tipoAnalise = "Analise_Prática";
      // O Analítico usa o registro principal de Prática. Por isso as
      // dificuldades informadas nos exercícios precisam acompanhar também o
      // material, exatamente como no fluxo do app.py.
      const dificuldadesDosExercicios = (item.exercicios || [])
        .flatMap((exercicio) => Array.isArray(exercicio?.dificuldades) ? exercicio.dificuldades : []);
      const dificuldadesDoMaterial = Array.from(new Set([
        ...(Array.isArray(item.dificuldades) ? item.dificuldades : []),
        ...dificuldadesDosExercicios
      ].map((dificuldade) => String(dificuldade || "").trim()).filter(Boolean)));
      const temDificuldade = dificuldadesDoMaterial
        .some((dificuldade) => dificuldade !== "Não apresentou dificuldades");
      const { data: anteriores, error: erroAnteriores } = await banco.from("historico_geral").select("id,Licao_Atual")
        .eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoAnalise).eq("Instrutora", instrutora).order("id", { ascending: false });
      if (erroAnteriores) throw new Error("Não foi possível conferir o registro de Prática já salvo.");
      const prefixo = `${material}:`;
      const existente = (anteriores || []).find((registro) => String(registro.Licao_Atual || "").trim().startsWith(prefixo));
      const registro = {
        Aluna: aluna, Data: data, Instrutora: instrutora, Tipo: tipoAnalise,
        Licao_Atual: `${material}: ${conteudo}`,
        Dificuldades: dificuldadesDoMaterial,
        Observacao: String(observacao || "").trim(),
        Status: temDificuldade ? "Realizada - com dificuldades" : "Realizada - sem pendência"
      };
      const salvar = existente
        ? await banco.from("historico_geral").update(registro).eq("id", existente.id)
        : await banco.from("historico_geral").insert(registro);
      if (salvar.error) throw new Error(`Não foi possível salvar o registro de ${material}.`);

      // Mantém os exercícios separados para consulta futura, mas as suas
      // dificuldades também estão agregadas acima — o Analítico lê o registro
      // principal, como no Streamlit.
      const apagar = await banco.from("exercicios_registro").delete()
        .eq("aluna", aluna).eq("data", data).eq("disciplina", "Prática").eq("material", material);
      if (apagar.error && apagar.error.code !== "42P01") throw new Error(`Não foi possível atualizar os exercícios de ${material}.`);
      const exercicios = (item.exercicios || []).filter((exercicio) => String(exercicio?.exercicio || "").trim())
        .map((exercicio, ordem) => ({
          aluna, data, instrutora, disciplina: "Prática", material,
          exercicio: String(exercicio.exercicio).trim(), dificuldades: Array.from(new Set(exercicio.dificuldades || [])), ordem
        }));
      if (exercicios.length) {
        const inserir = await banco.from("exercicios_registro").insert(exercicios);
        if (inserir.error) throw new Error(inserir.error.code === "42P01"
          ? "A tabela de exercícios ainda não existe no banco. Ela já é usada pelo app.py; confirme que está no mesmo projeto Supabase."
          : `Não foi possível salvar os exercícios de ${material}.`);
      }

      if (item.casaTipo) {
        // Apostila de Prática é corrigida pela Secretaria; Métodos são
        // corrigidos pela professora na próxima aula.
        const tipoCasa = item.casaTipo === "Apostila" ? "Casa_Apostila" : `Casa_Metodo_${material}`;
        const { data: casas, error: erroCasas } = await banco.from("historico_geral").select("id")
          .eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoCasa).order("id", { ascending: false }).limit(1);
        if (erroCasas) throw new Error(`O registro foi salvo, mas não foi possível consultar a lição de ${material}.`);
        if (!String(item.licaoCasa || "").trim()) {
          if (casas?.[0]) {
            const apagarCasa = await banco.from("historico_geral").delete().eq("id", casas[0].id);
            if (apagarCasa.error) throw new Error(`O registro foi salvo, mas não foi possível remover a lição de ${material}.`);
          }
          continue;
        }
        const casa = { Aluna: aluna, Data: data, Instrutora: instrutora, Tipo: tipoCasa, Licao_Atual: "Definido", Licao_Casa: String(item.licaoCasa).trim(), Dificuldades: [], Observacao: "", Status: "Pendente" };
        const salvarCasa = casas?.[0]
          ? await banco.from("historico_geral").update(casa).eq("id", casas[0].id)
          : await banco.from("historico_geral").insert(casa);
        if (salvarCasa.error) throw new Error(`O registro foi salvo, mas não foi possível registrar a lição de ${material}.`);
      }
    }
  }

  async function exerciciosDaAula({ dataIso, aluna, material }) {
    const banco = await obterCliente();
    const { data, error } = await banco.from("exercicios_registro").select("*")
      .eq("aluna", aluna).eq("data", dataBr(dataIso)).eq("disciplina", "Prática").eq("material", material).order("ordem");
    // Instalações antigas podem não ter a tabela. Não falhamos a abertura do
    // registro; apenas começamos a lista vazia e explicamos ao salvar.
    if (error && error.code !== "42P01") throw new Error("Não foi possível carregar os exercícios deste material.");
    return data || [];
  }

  async function registrosDaAula({ dataIso, instrutora, alunas }) {
    const banco = await obterCliente();
    const data = dataBr(dataIso);
    const { data: registros, error } = await banco.from("historico_geral").select("*")
      .eq("Data", data).eq("Instrutora", instrutora).in("Aluna", alunas || []).order("id", { ascending: true });
    if (error) throw new Error("Não foi possível carregar os registros já salvos desta aula.");
    return (registros || []).filter((registro) => String(registro.Tipo || "").startsWith("Analise_") || String(registro.Tipo || "").startsWith("Casa_"));
  }

  async function licoesPendentesProfessora({ alunas, tipoAula }) {
    const banco = await obterCliente();
    const { data, error } = await banco.from("historico_geral").select("*").in("Aluna", alunas || []).order("id", { ascending: false });
    if (error) throw new Error("Não foi possível carregar as lições pendentes.");
    const tiposPermitidos = tipoAula === "Solfejo" ? ["Casa_MSA"]
      : tipoAula === "Solfejo Melódico" ? ["Casa_Canto"]
        : tipoAula === "Teoria" ? ["Casa_Teoria_Prof", "Casa_Apostila_Teoria_Prof", "Casa_Apostila_Teoria"]
          : tipoAula === "Prática" ? []
            : null;
    // Mantém na fila tudo o que ainda requer acompanhamento. Em métodos,
    // "Não passou" e "Estudar mais" já criam uma nova lição pendente para a
    // próxima aula; portanto, a versão anterior não deve duplicar a fila.
    const finalizados = ["Resolvido", "Realizada", "Realizada - sem pendência", "Realizadas - sem pendência"];
    return (data || []).filter((registro) => {
      const tipo = String(registro.Tipo || "");
      const pertence = tiposPermitidos ? (tiposPermitidos.includes(tipo) || (tipoAula === "Prática" && tipo.startsWith("Casa_Metodo_"))) : tipo.startsWith("Casa_Metodo_");
      const ehMetodo = tipo.startsWith("Casa_Metodo_");
      const baixada = finalizados.includes(registro.Status)
        || (ehMetodo && ["Resolvido com pendências", "Não resolvido"].includes(registro.Status));
      return pertence && !baixada;
    });
  }

  async function corrigirLicaoProfessora(id, { status, observacao, repetirLicao, dataIso, instrutora, licao }) {
    const banco = await obterCliente();
    // O app.py trata o resultado pedagógico dos métodos separadamente do
    // status técnico do histórico. Mantemos os dois significados: a lição
    // corrigida é baixada e, quando necessário, uma nova pendência editável é
    // criada para a próxima aula.
    const statusHistorico = ({ "Passou": "Resolvido", "Não passou": "Não resolvido", "Estudar mais": "Resolvido com pendências" })[status] || status;
    const { error } = await banco.from("historico_geral").update({ Status: statusHistorico, Observacao: String(observacao || "").trim() }).eq("id", id);
    if (error) throw new Error("Não foi possível salvar a correção da lição.");

    const tipo = String(licao?.Tipo || "");
    const deveRepetir = tipo.startsWith("Casa_Metodo_") && ["Não passou", "Estudar mais"].includes(status) && String(repetirLicao || "").trim();
    if (!deveRepetir) return;
    const data = dataBr(dataIso);
    const proxima = {
      Aluna: licao.Aluna,
      Data: data,
      Instrutora: instrutora || licao.Instrutora || "",
      Tipo: tipo,
      Licao_Atual: "Definido",
      Licao_Casa: String(repetirLicao).trim(),
      Dificuldades: [],
      Observacao: "",
      Status: "Pendente"
    };
    const { data: existentes, error: erroBusca } = await banco.from("historico_geral").select("id")
      .eq("Aluna", proxima.Aluna).eq("Data", data).eq("Tipo", tipo).order("id", { ascending: false }).limit(1);
    if (erroBusca) throw new Error("A correção foi salva, mas não foi possível preparar a lição de reforço.");
    const operacao = existentes?.[0]?.id
      ? banco.from("historico_geral").update(proxima).eq("id", existentes[0].id)
      : banco.from("historico_geral").insert(proxima);
    const { error: erroRepeticao } = await operacao;
    if (erroRepeticao) throw new Error("A correção foi salva, mas não foi possível preparar a lição de reforço.");
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

  async function dadosEstudoAluna(aluna) {
    const banco = await obterCliente();
    const { data, error } = await banco.from("estudo_diario").select("*").eq("aluna", aluna).order("data", { ascending: false });
    if (error) throw new Error(error.code === "42P01" || error.code === "PGRST205" ? "O Controle de Estudo Diário ainda não foi criado no Supabase." : "Não foi possível carregar seu histórico de estudo.");
    return data || [];
  }

  async function salvarEstudoDiario({ aluna, dataIso, horarios }) {
    if (!aluna || !dataIso) throw new Error("Informe o dia do estudo.");
    const banco = await obterCliente();
    const { error } = await banco.from("estudo_diario").upsert({
      aluna,
      data: dataBr(dataIso),
      horarios: Array.from(new Set((horarios || []).map((horario) => String(horario).trim()).filter(Boolean)))
    }, { onConflict: "aluna,data" });
    if (error) throw new Error("Não foi possível salvar seu estudo do dia.");
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
    const [{ data: avaliacoes, error: erroAvaliacoes }, { data: notas, error: erroNotas }, { data: historico, error: erroHistorico }] = await Promise.all([
      banco.from("avaliacoes").select("*").order("data_avaliacao", { ascending: false }),
      banco.from("avaliacao_notas").select("*").eq("aluna", aluna),
      banco.from("historico_geral").select("Data,Tipo,Status").eq("Aluna", aluna)
    ]);
    if (erroAvaliacoes || erroNotas || erroHistorico) throw new Error("Não foi possível carregar o boletim.");
    return { avaliacoes: avaliacoes || [], notas: notas || [], historico: historico || [] };
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

  async function dadosFolgas() {
    const banco = await obterCliente();
    const { data, error } = await banco.from("folgas_professoras").select("*").order("data", { ascending: false });
    if (error) throw new Error(error.code === "42P01" ? "A tabela de folgas ainda não foi criada no Supabase." : "Não foi possível carregar as folgas.");
    return data || [];
  }

  async function salvarFolgas({ data, coordenadora, professoras, observacao }) {
    const banco = await obterCliente();
    const { error } = await banco.from("folgas_professoras").upsert({ data, coordenadora, professoras: professoras || [], observacao: String(observacao || "").trim() }, { onConflict: "data" });
    if (error) throw new Error("Não foi possível salvar as folgas deste sábado.");
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
      const url = await urlAssinadaEmCache(banco, "fotos_alunas", perfil.foto_path);
      if (url) fotos[perfil.nome] = url;
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

  window.GemData = { carregarIdentidade, enviarLogoGem, perfilSecretaria, salvarPerfilSecretaria, perfilProfessora, dadosMetodos, criarMetodo, removerMetodo, dadosVisaoGeral, dadosPessoas, fotosPessoas, dadosCoordenacoesProfessoras, definirCoordenadoraProfessora, professoraEhCoordenadora, salvarPessoa, enviarFotoPessoa, dadosDocumentos, enviarDocumento, removerDocumento, urlDocumento, dadosProvas, criarProva, removerProva, salvarResponsaveisAvaliacao, salvarNotaAvaliacao, dadosMensagens, enviarMensagem, dadosAnalitico, salvarObjetivoPedagogico, dadosCorrecoesLicoes, dadosAjustes, contarRegistrosOrfaos, limparRegistrosOrfaos, removerRegistroHistorico, dadosAuditoriaRodizio, atualizarCorrecaoLicao, criarCorrecaoLicao, dadosLogistica, salvarModeloLogistica, alterarStatusModelo, autenticar, encerrarSessao, iniciarSessaoR2, restaurarSessao, listarGems, criarGem, gemAtivo, dadosPlataformaMaster, agendaProfessora, salvarRegistroAula, salvarRegistrosPratica, exerciciosDaAula, registrosDaAula, licoesPendentesProfessora, corrigirLicaoProfessora, dadosAluna, dadosEstudoAluna, salvarEstudoDiario, marcarLicaoFeita, boletimAluna, dadosRodizio, dadosFolgas, salvarFolgas, modeloParaData, horarioDoBloco, dadosChamada, salvarChamada, salvarProfessorasFixas, salvarEscala, dataBr };
})();
