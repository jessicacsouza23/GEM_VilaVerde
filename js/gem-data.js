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

  async function carregarIdentidade() {
    if (!client) return { connected: false, message: "Configuração do banco ainda não encontrada." };
    try {
      const { data: visual, error } = await client.from("config_visual_gem")
        .select("logo_path, updated_at").eq("id", 1).maybeSingle();
      if (error) throw error;

      let logoUrl = null;
      if (visual?.logo_path) {
        const { data: arquivo } = await client.storage.from("logo_gem")
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
    if (!client) throw new Error("A conexão com o GEM não está configurada.");
    const usuario = String(login || "").trim().toLowerCase();
    if (!usuario || !senha) throw new Error("Informe usuário e senha.");

    // Contas novas (incluindo Master) usam Supabase Auth. A senha não passa
    // pelas tabelas pedagógicas e a sessão retornada é a sessão oficial.
    if (usuario.includes("@")) {
      const sessao = await client.auth.signInWithPassword({ email: usuario, password: senha });
      if (!sessao.error && sessao.data?.user) {
        const { data: plataforma } = await client.from("plataforma_usuarios")
          .select("nome, papel, ativo, status_convite")
          .eq("auth_user_id", sessao.data.user.id).maybeSingle();
        if (plataforma?.papel === "master" && plataforma.ativo && plataforma.status_convite === "ativo") {
          return { role: "Master", name: plataforma.nome, gem: null, sessao: true };
        }
      }
    }

    // A Secretaria já usa esta RPC no Streamlit. Ela devolve somente o perfil
    // correto após conferir a senha no banco.
    const secretaria = await client.rpc("validar_acesso", { p_login: usuario, p_senha: senha });
    const contaSecretaria = secretaria.data?.[0];
    if (contaSecretaria?.perfil === "secretaria") {
      return { role: "Secretaria", name: contaSecretaria.nome || "Coordenação", gem: "Vila Verde" };
    }

    // Professoras e alunas usam a ponte criada na migration desta interface.
    const pessoas = await client.rpc("validar_acesso_gem_pessoas", { p_login: usuario, p_senha: senha });
    const conta = pessoas.data?.[0];
    if (!conta) throw new Error("Usuário ou senha inválidos.");
    return {
      role: conta.perfil === "professora" ? "Professora" : "Aluna",
      name: conta.nome,
      gem: "Vila Verde"
    };
  }

  async function listarGems() {
    if (!client) throw new Error("A conexão com o GEM não está configurada.");
    const { data, error } = await client.from("gems")
      .select("id, nome, slug, ativo, created_at")
      .order("nome", { ascending: true });
    if (error) throw new Error("Não foi possível carregar os GEMs.");
    return data || [];
  }

  async function criarGem(nome, slug) {
    if (!client) throw new Error("A conexão com o GEM não está configurada.");
    const slugLimpo = String(slug || "").trim().toLowerCase()
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    if (!String(nome || "").trim() || !slugLimpo) throw new Error("Informe o nome e um identificador para o GEM.");
    const { error } = await client.from("gems").insert({ nome: String(nome).trim(), slug: slugLimpo });
    if (error) throw new Error(error.code === "23505" ? "Já existe um GEM com esse identificador." : "Não foi possível criar o GEM.");
  }

  window.GemData = { client, carregarIdentidade, autenticar, listarGems, criarGem };
})();
