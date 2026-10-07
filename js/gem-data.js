/* Conexão somente de identidade visual nesta etapa.
   Dados pedagógicos só serão carregados após a migração de autenticação e
   isolamento por GEM, para não reproduzir no navegador permissões antigas. */
(function () {
  const configLocal = window.GEM_SUPABASE;
  let client = null;
  let configPrincipal = null;
  let contextoGem = { nome: "GEM Vila Verde", slug: "vila-verde", externo: false, perfilSchema: "gem-pwa-v1" };
  let r2Habilitado = null;
  const tabelasPessoasSemId = new Set();
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
    // O bucket é compartilhado pela plataforma, mas a API separa os objetos
    // por slug e só libera a pasta do GEM presente na sessão autenticada.
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
      // Com o R2 ativo não usamos o Supabase silenciosamente como reserva.
      // Isso esconderia uma regra CORS/credencial quebrada e voltaria a gerar
      // saída no Storage sem a Secretaria perceber. A pessoa recebe o erro e
      // pode corrigir a configuração antes de gravar uma foto no lugar errado.
      const detalhe = String(erro?.message || "erro desconhecido");
      throw new Error(`A foto não foi enviada ao R2 (${detalhe}). Confira as credenciais e o CORS do bucket antes de tentar novamente.`);
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

    // As Secretarias de unidades novas são administradas pela Master na base
    // central. Depois do login, elas continuam usando exclusivamente os dados
    // pedagógicos da base do GEM selecionado.
    if (contextoGem.externo) {
      const plataforma = criarCliente(await obterConfigPrincipal(), false);
      const secretariaCentral = await plataforma.rpc("validar_acesso_secretaria_gem", { p_slug: contextoGem.slug, p_login: usuario, p_senha: senha });
      const contaCentral = secretariaCentral.data?.[0];
      if (contaCentral?.perfil === "secretaria") return { role: "Secretaria", name: contaCentral.nome || "Coordenação", gem: contextoGem.nome, externo: true };
    }

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

  async function alterarStatusGem(id, ativo) {
    if (!id) throw new Error("GEM inválido.");
    const banco = await obterCliente();
    const { error } = await banco.from("gems").update({ ativo: Boolean(ativo), updated_at: new Date().toISOString() }).eq("id", id);
    if (error) throw new Error("Não foi possível alterar o status do GEM.");
  }

  async function removerGem(id, slug) {
    if (!id || String(slug) === "vila-verde") throw new Error("A unidade principal não pode ser excluída por esta tela.");
    const banco = await obterCliente();
    const { error } = await banco.from("gems").delete().eq("id", id);
    if (error) throw new Error("Não foi possível excluir o cadastro do GEM.");
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

  async function dadosSecretariasGems() {
    const banco = await obterCliente();
    const [gems, secretarias] = await Promise.all([
      banco.from("gems").select("id,nome,slug,ativo").order("nome"),
      banco.from("gem_secretarias").select("id,gem_id,nome,login,ativo,created_at").order("nome")
    ]);
    const falha = [gems, secretarias].find((resultado) => resultado.error)?.error;
    if (falha) throw new Error("Não foi possível carregar as Secretarias dos GEMs. Execute a migration 011 na base principal.");
    return { gems: gems.data || [], secretarias: secretarias.data || [] };
  }

  async function salvarSecretariaGem({ id = null, gemId, nome, login, senha = "", ativo = true }) {
    if (!gemId || !String(nome || "").trim() || !String(login || "").trim()) throw new Error("Escolha o GEM e informe nome e usuário da Secretaria.");
    if (!id && String(senha || "").length < 6) throw new Error("Informe uma senha inicial com pelo menos 6 caracteres.");
    if (id && senha && String(senha).length < 6) throw new Error("A nova senha deve ter pelo menos 6 caracteres.");
    const banco = await obterCliente();
    const { error } = await banco.rpc("salvar_secretaria_gem", { p_id: id, p_gem_id: gemId, p_nome: String(nome).trim(), p_login: String(login).trim().toLowerCase(), p_senha: String(senha || ""), p_ativo: Boolean(ativo) });
    if (error) throw new Error(error.message || "Não foi possível salvar a Secretaria.");
  }

  function normalizar(texto) {
    return String(texto || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase();
  }

  async function enviarLogoGem(arquivo) {
    if (!arquivo) throw new Error("Escolha a imagem da logo.");
    const banco = await obterCliente();
    const extensao = (arquivo.name.split(".").pop() || "png").toLowerCase();
    let caminho = await enviarFotoParaR2("logo", arquivo);
    // No Vila Verde, imagens novas sempre pertencem ao R2. Não podemos
    // voltar ao Storage do Supabase sem avisar, pois isso voltaria a gerar
    // saída e deixaria a falha de configuração invisível. Os GEMs externos
    // continuam isolados no Storage da própria unidade.
    if (!caminho && !contextoGem.externo) throw new Error("O R2 não está configurado para receber a logo.");
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
      if (!foto_path && !contextoGem.externo) throw new Error("O R2 não está configurado para receber a foto da Coordenação.");
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
      banco.from("historico_geral").select("id,Data,Aluna,Tipo,Status,Observacao,Licao_Atual,Licao_Casa,Dificuldades,Instrutora,Secretaria").eq("Data", data).order("id", { ascending: true }),
      banco.from("estudo_diario").select("aluna,data,horarios").eq("data", data)
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
    const plataforma = contextoGem.externo ? criarCliente(await obterConfigPrincipal(), false) : null;
    const consultar = async (tabela, campos, ordem) => {
      const buscar = (semId) => {
        let consulta = banco.from(tabela).select(semId ? campos : `id,${campos}`);
        ordem.forEach((campo) => { consulta = consulta.order(campo); });
        return consulta;
      };
      let resultado = await buscar(tabelasPessoasSemId.has(tabela));
      // A base original identifica pessoas pelo nome; GEMs novos têm UUID.
      // Mantém os dois formatos e não consulta senhas para montar a lista.
      if (["42703", "PGRST204"].includes(resultado.error?.code) && /\bid\b/i.test(resultado.error.message || "")) {
        tabelasPessoasSemId.add(tabela);
        resultado = await buscar(true);
      }
      return resultado;
    };
    const [alunas, professoras, secretarias, secretariasCentralizadas] = await Promise.all([
      consultar("alunas", "nome,turma,login,ativo,foto_path", ["turma", "nome"]),
      consultar("professoras", "nome,login,ativo,foto_path", ["nome"]),
      consultar("secretarias", "nome,ativo", ["nome"]),
      plataforma ? plataforma.rpc("listar_secretarias_gem_publicas", { p_slug: contextoGem.slug }) : Promise.resolve({ data: [] })
    ]);
    if (alunas.error || professoras.error) {
      const erro = alunas.error || professoras.error;
      throw new Error(`Não foi possível carregar turmas e pessoas: ${erro.message || "verifique as permissões do Supabase."}`);
    }
    const nomesLocais = new Set((secretarias.data || []).map((item) => normalizar(item.nome)));
    const centralizadas = (secretariasCentralizadas.data || []).filter((item) => !nomesLocais.has(normalizar(item.nome))).map((item) => ({ id: `central-${item.login}`, nome: item.nome, login: item.login, ativo: true, origem_master: true }));
    return { alunas: alunas.data || [], professoras: professoras.data || [], secretarias: [...(secretarias.data || []), ...centralizadas] };
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
    const caminhoR2 = await enviarFotoParaR2(tipo, arquivo);
    if (caminhoR2) return caminhoR2;
    if (!contextoGem.externo) throw new Error("O R2 não está configurado para receber fotos. Verifique as chaves do R2 na Vercel.");
    // Cada GEM externo tem sua própria base e seu próprio Storage. Essa é a
    // única situação em que mantemos o envio para o Supabase.
    const banco = await obterCliente();
    const bucket = tipo === 'aluna' ? 'fotos_alunas' : 'fotos_professoras';
    const caminho = `${crypto.randomUUID()}_${String(arquivo.name).normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').replace(/[^a-zA-Z0-9._-]+/g, '_')}`;
    const { error } = await banco.storage.from(bucket).upload(caminho, arquivo, { contentType: arquivo.type || `image/${extensao === 'jpg' ? 'jpeg' : extensao}` });
    if (error) throw new Error(error.message?.toLowerCase().includes("bucket") ? "O armazenamento de fotos ainda não está configurado. Execute a migration 007 no Supabase." : "Não foi possível enviar a foto.");
    return caminho;
  }

  async function atualizarMinhaFotoProfessora(nome, arquivo) {
    if (!String(nome || "").trim()) throw new Error("Não foi possível identificar a professora.");
    if (!arquivo) throw new Error("Escolha uma foto para enviar.");
    // O perfil da professora usa exclusivamente o R2: não voltamos a gerar
    // arquivos nem saída no Storage do Supabase.
    const foto_path = await enviarFotoParaR2("professora", arquivo);
    if (!foto_path) throw new Error("O R2 não está configurado para receber fotos.");
    await salvarPessoa("professora", { foto_path }, null, nome);
    return perfilProfessora(nome);
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

  async function dadosResumoProfessora(dataIso) {
    const banco = await obterCliente();
    const referencia = new Date(`${dataIso}T12:00:00`);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(dataIso) || !Number.isFinite(referencia.getTime())) throw new Error("Selecione uma data válida.");
    const datas = [];
    for (let dia = 0; dia < 30; dia++) {
      const data = new Date(referencia); data.setDate(data.getDate() - dia);
      const iso = `${data.getFullYear()}-${String(data.getMonth() + 1).padStart(2, "0")}-${String(data.getDate()).padStart(2, "0")}`;
      datas.push(iso, dataBr(iso));
    }
    // Busca somente os campos do resumo, sem fotos, contas ou avaliações.
    // Paginação evita truncar o ranking em GEMs com mais registros.
    const lerPaginas = async (consulta) => {
      const itens = [];
      for (let inicio = 0; ; inicio += 1000) {
        const { data, error } = await consulta().range(inicio, inicio + 999);
        if (error) throw new Error("Não foi possível carregar os destaques do GEM. Tente atualizar novamente.");
        itens.push(...(data || []));
        if (!data || data.length < 1000) return itens;
      }
    };
    const [alunas, historico, estudos] = await Promise.all([
      lerPaginas(() => banco.from("alunas").select("nome,ativo").order("nome")),
      lerPaginas(() => banco.from("historico_geral").select("Data,Aluna,Tipo,Status,Dificuldades").in("Data", datas).order("id")),
      lerPaginas(() => banco.from("estudo_diario").select("aluna,data,horarios").in("data", datas).order("aluna").order("data"))
    ]);
    return { alunas, historico, estudos };
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

  async function dadosExportacaoRelatorio() {
    const banco = await obterCliente();
    const [historico, alunas] = await Promise.all([
      banco.from("historico_geral").select("id,Data,Aluna,Tipo,Instrutora,Licao_Atual,Dificuldades,Observacao,Status").order("id", { ascending: false }),
      banco.from("alunas").select("nome,ativo").order("nome")
    ]);
    if (historico.error || alunas.error) throw new Error("Não foi possível carregar os conteúdos para a exportação.");
    return { historico: historico.data || [], alunas: alunas.data || [] };
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

  async function alterarStatusModelo(id, status) {
    const agora = new Date();
    const hoje = `${agora.getFullYear()}-${String(agora.getMonth() + 1).padStart(2, "0")}-${String(agora.getDate()).padStart(2, "0")}`;
    const banco = await obterCliente();
    const dados = { status, updated_at: agora.toISOString(), vigencia_fim: status === "encerrado" ? hoje : null };
    const { error } = await banco.from("modelos_logistica").update(dados).eq("id", id);
    if (error) throw new Error("Não foi possível alterar o status do modelo.");
    return dados;
  }

  async function removerModeloLogistica(id) {
    if (!id) throw new Error("Modelo inválido.");
    const banco = await obterCliente();
    const { error } = await banco.from("modelos_logistica").delete().eq("id", id);
    if (error) throw new Error("Não foi possível excluir o modelo.");
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
    const { data: calendario, error } = await banco.from("calendario").select("id, escala, modelo_logistica_id").eq("id", data).maybeSingle();
    if (error) throw new Error("Não foi possível carregar a agenda desta data.");
    const escala = calendario?.escala || [];
    if (!escala.length) return [];
    const { data: alunas } = await banco.from("alunas").select("nome, turma, foto_path");
    const turmaPorAluna = Object.fromEntries((alunas || []).map((aluna) => [aluna.nome, aluna.turma]));
    const fotoPorAluna = {};
    await Promise.all((alunas || []).filter((aluna) => aluna.foto_path).map(async (aluna) => {
      // Uma foto antiga, removida ou sem acesso não pode impedir a professora
      // de abrir a agenda. Nesse caso a interface mostra as iniciais da aluna.
      try {
        const url = await urlAssinadaEmCache(banco, "fotos_alunas", aluna.foto_path);
        if (url) fotoPorAluna[aluna.nome] = url;
      } catch (_) { /* foto indisponível: mantém a agenda funcional */ }
    }));
    // Escalas novas preservam os horários por componente. Nas antigas,
    // consulta o modelo vinculado (ou vigente na data), sem minutos fixos.
    let atividadesModelo = [];
    const precisaModelo = escala.some((linha) => Object.values(linha._detalhes || {}).some((detalhe) =>
      (detalhe.componentes?.length > 1 || /PRATICA.*SOLFEJO|SOLFEJO.*PRATICA/.test(normalizar(detalhe.tipo)))
      && !Object.keys(detalhe.horarios_componentes || {}).length
    ));
    if (precisaModelo) {
      try {
        const modelos = await dadosLogistica();
        const modelo = calendario.modelo_logistica_id
          ? modelos.find((item) => item.id === calendario.modelo_logistica_id)
          : modeloParaData(modelos, dataIso);
        atividadesModelo = modelo?.configuracao?.atividades || [];
      } catch (_) { /* Sem duração confirmada, mantém o horário do bloco. */ }
    }
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
        const tipoDaEscala = tipoDaAula(conteudo, detalhe);
        const detalheCombinado = /PRATICA.*SOLFEJO|SOLFEJO.*PRATICA/.test(normalizar(tipoDaEscala));
        const ehIndividual = Boolean(detalhe.individual) || detalheCombinado;
        // Escalas antigas trazem apenas "Prática + Solfejo" no detalhe. Para
        // a agenda da professora isso são duas aulas diferentes: assim a tela
        // de Solfejo nunca recebe as correções de Método/Prática.
        const componentes = ehIndividual && Array.isArray(detalhe.componentes)
          ? detalhe.componentes
          : detalheCombinado
            ? ["Solfejo", "Prática"]
            : [tipoDaEscala];
        const horariosPorTipo = Object.keys(detalhe.horarios_componentes || {}).length
          ? detalhe.horarios_componentes
          : window.RodizioEngine?.horariosComponentes?.(horario, componentes, atividadesModelo) || {};
        for (const tipo of componentes) {
          const professorasComponentes = detalhe.professoras_componentes || {};
          if (professorasComponentes[tipo] && normalizar(professorasComponentes[tipo]) !== nomeNormalizado) continue;
          const individual = ehIndividual || tipo === "Prática";
          const chave = individual ? `${horario}|${tipo}|${linha.Aluna}` : `${horario}|${tipo}|${conteudo}`;
          if (vistas.has(chave)) continue;
          vistas.add(chave);
          const alunasDaAula = individual ? [linha.Aluna] : escala.filter((outra) => String(outra[horario] || "") === conteudo).map((outra) => outra.Aluna).filter(Boolean);
          aulas.push({ horario: horariosPorTipo[tipo] || horario, tipo, local: conteudo.split("|")[0].trim(), individual, alunas: alunasDaAula, fotos: Object.fromEntries(alunasDaAula.map((aluna) => [aluna, fotoPorAluna[aluna] || null])), turma: turmaPorAluna[linha.Aluna] || "" });
        }
      }
    }
    return aulas.sort((a, b) => a.horario.localeCompare(b.horario));
  }

  async function salvarRegistroAula({ dataIso, instrutora, tipo, alunas, material, conteudo, dificuldades, observacao, registrosPorAluna, casaTipo, licaoCasa, observacaoCasa = "", limparCasas = [] }) {
    const banco = await obterCliente(); const data = dataBr(dataIso), disciplina = tipo === "Canto" ? "Solfejo Melódico" : tipo;
    if (!alunas?.length) throw new Error("Selecione ao menos uma aluna.");
    if (!material?.trim() && !conteudo?.trim()) throw new Error("Informe o material usado hoje.");
    conteudo = String(conteudo || "").trim();
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

      // Solfejo e Solfejo Melódico são conferidos no próprio registro da aula.
      // Não existe uma tela de “passou/não passou”: a aula seguinte encerra o
      // estudo anterior e registra naturalmente a nova lição para casa.
      if (["Solfejo", "Solfejo Melódico"].includes(disciplina)) {
        const tipoEstudo = disciplina === "Solfejo" ? "Casa_MSA" : "Casa_Canto";
        const { data: licoesMsa, error: erroMsa } = await banco.from("historico_geral")
          .select("id,Status").eq("Aluna", aluna).eq("Tipo", tipoEstudo);
        if (erroMsa) throw new Error(`A aula foi salva, mas não foi possível atualizar o estudo de ${aluna}.`);
        const statusFinal = ["Resolvido", "Realizada", "Realizada - sem pendência", "Realizadas - sem pendência"];
        const naoRealizou = dificuldadesDaAluna.some((dificuldade) => normalizar(dificuldade).includes("NAO REALIZOU"));
        const pendentesMsa = (licoesMsa || []).filter((licao) => !statusFinal.includes(String(licao.Status || "")));
        for (const licao of pendentesMsa) {
          const atualizacao = await banco.from("historico_geral")
            .update({ Status: naoRealizou ? "Não resolvido" : "Resolvido", Observacao: registro.Observacao })
            .eq("id", licao.id);
          if (atualizacao.error) throw new Error(`A aula foi salva, mas não foi possível atualizar o estudo de ${aluna}.`);
        }
      }
      const tipoCasa = casaTipo ? `Casa_${casaTipo}` : "";
      if (tipoCasa && licaoCasa?.trim()) {
        const pendente = await banco.from("historico_geral").select("id").eq("Aluna", aluna).eq("Data", data).eq("Tipo", tipoCasa).order("id", { ascending: false }).limit(1);
        const casa = { Aluna: aluna, Data: data, Instrutora: instrutora, Tipo: tipoCasa, Licao_Atual: "Definido", Licao_Casa: licaoCasa.trim(), Dificuldades: [], Observacao: String(observacaoCasa || "").trim(), Status: "Pendente" };
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
  async function salvarRegistrosPratica({ dataIso, instrutora, aluna, materiais, licoesCasa = [], observacao = "" }) {
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
    const licoesAtuais = new Set(lista.map((item) => `${String(item.material).trim()}: ${String(item.conteudo).trim()}`));
    for (const registro of (registrosDoDia || [])) {
      const materialAnterior = String(registro.Licao_Atual || "").split(":", 1)[0].trim();
      if (!materialAnterior || licoesAtuais.has(String(registro.Licao_Atual || "").trim())) continue;
      const apagarAnalise = await banco.from("historico_geral").delete().eq("id", registro.id);
      if (apagarAnalise.error) throw new Error(`Não foi possível remover o material ${materialAnterior}.`);
      if (materiaisAtuais.has(materialAnterior)) continue;
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
      const existente = (anteriores || []).find((registro) => String(registro.Licao_Atual || "").trim() === `${material}: ${conteudo}`);
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

      // A correção do método é feita dentro do registro de Prática (como no
      // app.py). O conteúdo e as dificuldades ficam na análise de hoje; o
      // item de casa anterior recebe somente o resultado e a observação.
      if (item.licaoPendenteId && item.resultadoLicao) {
        const statusCorrecao = {
          "Passou": "Resolvido",
          "Não passou": "Não resolvido",
          "Estudar mais": "Resolvido com pendências",
          "Resolvido": "Resolvido",
          "Resolvido com pendências": "Resolvido com pendências",
          "Não resolvido": "Não resolvido",
          "Não trouxe a apostila/atividade": "Não trouxe a apostila/atividade"
        }[item.resultadoLicao];
        if (statusCorrecao) {
          const atualizarCorrecao = await banco.from("historico_geral").update({
            Status: statusCorrecao,
            Observacao: String(item.observacaoCorrecao || "").trim()
          }).eq("id", item.licaoPendenteId);
          if (atualizarCorrecao.error) throw new Error(`O registro de ${material} foi salvo, mas não foi possível atualizar a lição anterior.`);
        }
      }
      // Registros antigos podem ter conteúdo de Apostila sem a lição de casa
      // correspondente. Ao a professora informar o resultado, criamos o item
      // de acompanhamento: só "Resolvido" fica fora da fila da Secretaria.
      if (!item.licaoPendenteId && item.correcaoApostilaAutomatica && item.resultadoLicao && item.licaoPendenteTexto) {
        const statusCorrecao = {
          "Resolvido": "Resolvido",
          "Resolvido com pendências": "Resolvido com pendências",
          "Não resolvido": "Não resolvido"
        }[item.resultadoLicao];
        if (statusCorrecao) {
          // Casa_Apostila_Prof é também lida pela Secretaria, mas não entra
          // na limpeza das novas lições de casa da aula atual. Assim a
          // correção automática não se perde ao salvar o registro.
          const { data: existenteAutomatico, error: erroBuscaAutomatica } = await banco.from("historico_geral").select("id")
            .eq("Aluna", aluna).eq("Data", data).eq("Tipo", "Casa_Apostila_Prof").eq("Licao_Casa", String(item.licaoPendenteTexto).trim()).limit(1);
          if (erroBuscaAutomatica) throw new Error("Não foi possível preparar a correção da Apostila.");
          const correcaoAutomatica = {
            Aluna: aluna, Data: data, Instrutora: instrutora, Tipo: "Casa_Apostila_Prof",
            Licao_Atual: "Definido", Licao_Casa: String(item.licaoPendenteTexto).trim(), Dificuldades: [],
            Observacao: String(item.observacaoCorrecao || "").trim(), Status: statusCorrecao
          };
          const salvarAutomatica = existenteAutomatico?.[0]
            ? await banco.from("historico_geral").update(correcaoAutomatica).eq("id", existenteAutomatico[0].id)
            : await banco.from("historico_geral").insert(correcaoAutomatica);
          if (salvarAutomatica.error) throw new Error("O registro foi salvo, mas não foi possível registrar a correção da Apostila.");
        }
      }

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

    }

    // Cada linha é uma lição independente. Assim a professora pode passar
    // várias páginas de Apostila, vários métodos ou repetir um mesmo método
    // sem que a última entrada apague as anteriores.
    const { data: casasAnteriores, error: erroCasasAnteriores } = await banco.from("historico_geral").select("id,Tipo")
      .eq("Aluna", aluna).eq("Data", data).eq("Instrutora", instrutora);
    if (erroCasasAnteriores) throw new Error("O registro foi salvo, mas não foi possível preparar as lições de casa.");
    const casasDaPratica = (casasAnteriores || []).filter((item) => item.Tipo === "Casa_Apostila" || String(item.Tipo || "").startsWith("Casa_Metodo_"));
    for (const casaAnterior of casasDaPratica) {
      const apagarCasa = await banco.from("historico_geral").delete().eq("id", casaAnterior.id);
      if (apagarCasa.error) throw new Error("O registro foi salvo, mas não foi possível atualizar as lições de casa.");
    }
    const novasCasas = (licoesCasa || []).map((item) => ({ material: String(item?.material || "").trim(), licaoCasa: String(item?.licaoCasa || "").trim(), observacao: String(item?.observacao || "").trim() }))
      .filter((item) => item.material && item.licaoCasa);
    if (novasCasas.length) {
      const salvarCasas = await banco.from("historico_geral").insert(novasCasas.map((item) => ({
        Aluna: aluna, Data: data, Instrutora: instrutora,
        Tipo: item.material === "Apostila" ? "Casa_Apostila" : `Casa_Metodo_${item.material}`,
        Licao_Atual: "Definido", Licao_Casa: item.licaoCasa, Dificuldades: [], Observacao: item.observacao, Status: "Pendente"
      })));
      if (salvarCasas.error) throw new Error("O registro foi salvo, mas não foi possível registrar as lições de casa.");
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

  async function contextoPratica({ aluna, dataIso }) {
    const banco = await obterCliente();
    const dataAtual = dataBr(dataIso);
    const { data, error } = await banco.from("historico_geral").select("id,Data,Tipo,Licao_Atual,Licao_Casa,Dificuldades,Observacao,Status")
      .eq("Aluna", aluna).order("id", { ascending: false });
    if (error) throw new Error("Não foi possível carregar o histórico de Prática da aluna.");
    const paraTempo = (valor) => {
      const texto = String(valor || "").trim();
      if (/^\d{4}-\d{2}-\d{2}/.test(texto)) return new Date(`${texto.slice(0, 10)}T12:00:00`).getTime();
      const [dia, mes, ano] = texto.split("/");
      return ano ? new Date(`${ano}-${mes}-${dia}T12:00:00`).getTime() : 0;
    };
    return (data || []).filter((registro) => registro.Data !== dataAtual).sort((a, b) => paraTempo(b.Data) - paraTempo(a.Data));
  }

  async function licoesPendentesProfessora({ alunas, tipoAula }) {
    // Solfejo e Solfejo Melódico não têm etapa de correção separada: a lição
    // apresentada entra no próprio registro pedagógico da próxima aula.
    if (normalizar(tipoAula).includes("SOLFEJO")) return [];
    const banco = await obterCliente();
    const { data, error } = await banco.from("historico_geral").select("*").in("Aluna", alunas || []).order("id", { ascending: false });
    if (error) throw new Error("Não foi possível carregar as lições pendentes.");
    const tiposPermitidos = tipoAula === "Teoria" ? ["Casa_Teoria_Prof", "Casa_Apostila_Teoria_Prof", "Casa_Apostila_Teoria"]
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
    const folgaBruta = folgas.data || null;
    let professorasDeFolga = folgaBruta?.professoras || [];
    // Alguns bancos antigos devolvem o jsonb como texto. Normalizamos aqui
    // para que o motor receba sempre uma lista real de nomes.
    if (typeof professorasDeFolga === "string") {
      try { professorasDeFolga = JSON.parse(professorasDeFolga); }
      catch (_) { professorasDeFolga = professorasDeFolga.split(","); }
    }
    if (!Array.isArray(professorasDeFolga)) professorasDeFolga = [];
    const folga = folgaBruta ? { ...folgaBruta, professoras: professorasDeFolga.map((nome) => String(nome || "").trim()).filter(Boolean) } : null;
    return { data, modelos: modelos.data || [], turmas, professoras: (professoras.data || []).filter((professora) => professora.ativo !== false).map((professora) => professora.nome), escala: calendario.data?.escala || [], modeloEscala: calendario.data?.modelo_logistica_id || null, folga, escalasAnteriores: anteriores.data || [], professorasFixas };
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
      return modelo.vigencia_inicio <= dataIso && (modelo.status !== "encerrado" || (modelo.vigencia_fim && modelo.vigencia_fim >= dataIso));
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
      try {
        const url = await urlAssinadaEmCache(banco, "fotos_alunas", perfil.foto_path);
        if (url) fotos[perfil.nome] = url;
      } catch (_) { /* foto indisponível não bloqueia a chamada */ }
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

  window.GemData = { carregarIdentidade, enviarLogoGem, perfilSecretaria, salvarPerfilSecretaria, perfilProfessora, atualizarMinhaFotoProfessora, dadosMetodos, criarMetodo, removerMetodo, dadosVisaoGeral, dadosPessoas, fotosPessoas, dadosCoordenacoesProfessoras, definirCoordenadoraProfessora, professoraEhCoordenadora, salvarPessoa, enviarFotoPessoa, dadosDocumentos, enviarDocumento, removerDocumento, urlDocumento, dadosProvas, criarProva, removerProva, salvarResponsaveisAvaliacao, salvarNotaAvaliacao, dadosMensagens, enviarMensagem, dadosAnalitico, dadosExportacaoRelatorio, salvarObjetivoPedagogico, dadosCorrecoesLicoes, dadosAjustes, contarRegistrosOrfaos, limparRegistrosOrfaos, removerRegistroHistorico, dadosAuditoriaRodizio, atualizarCorrecaoLicao, criarCorrecaoLicao, dadosLogistica, salvarModeloLogistica, alterarStatusModelo, removerModeloLogistica, autenticar, encerrarSessao, iniciarSessaoR2, restaurarSessao, listarGems, criarGem, alterarStatusGem, removerGem, gemAtivo, dadosPlataformaMaster, dadosSecretariasGems, salvarSecretariaGem, agendaProfessora, salvarRegistroAula, salvarRegistrosPratica, exerciciosDaAula, registrosDaAula, contextoPratica, licoesPendentesProfessora, corrigirLicaoProfessora, dadosAluna, dadosEstudoAluna, salvarEstudoDiario, marcarLicaoFeita, boletimAluna, dadosRodizio, dadosFolgas, salvarFolgas, modeloParaData, horarioDoBloco, dadosChamada, salvarChamada, salvarProfessorasFixas, salvarEscala, dataBr };
  window.GemData.dadosResumoProfessora = dadosResumoProfessora;
})();
