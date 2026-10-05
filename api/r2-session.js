const { configurado, sessaoConfigurada, criarSessao, sessao, definirCookie, limparCookie } = require("./r2-auth");

async function supabaseRpc(nome, parametros) {
  const url = process.env.SUPABASE_URL, chave = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !chave) throw new Error("SUPABASE_SERVICE_ROLE_KEY ausente.");
  const resposta = await fetch(`${url}/rest/v1/rpc/${nome}`, {
    method: "POST", headers: { apikey: chave, Authorization: `Bearer ${chave}`, "Content-Type": "application/json" }, body: JSON.stringify(parametros)
  });
  if (!resposta.ok) throw new Error("Credenciais inválidas.");
  return resposta.json();
}

function slugValido(valor) {
  const slug = String(valor || "").trim().toLowerCase();
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) ? slug : null;
}

async function buscarGemExterno(slug) {
  const url = process.env.SUPABASE_URL, chave = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !chave) return null;
  const resposta = await fetch(`${url}/rest/v1/gems?slug=eq.${encodeURIComponent(slug)}&ativo=eq.true&select=nome,slug,supabase_url,supabase_anon_key`, {
    headers: { apikey: chave, Authorization: `Bearer ${chave}` }
  });
  if (!resposta.ok) return null;
  const gem = (await resposta.json())?.[0];
  if (!gem?.supabase_url || !gem?.supabase_anon_key || !/^https:\/\//i.test(gem.supabase_url)) return null;
  return gem;
}

async function rpcNoGem(gem, nome, parametros) {
  const resposta = await fetch(`${String(gem.supabase_url).replace(/\/$/, "")}/rest/v1/rpc/${nome}`, {
    method: "POST",
    headers: { apikey: gem.supabase_anon_key, Authorization: `Bearer ${gem.supabase_anon_key}`, "Content-Type": "application/json" },
    body: JSON.stringify(parametros)
  });
  if (!resposta.ok) return null;
  return resposta.json();
}

async function validarNoGemExterno(slug, login, senha) {
  const gem = await buscarGemExterno(slug);
  if (!gem) return null;
  const parametros = { p_login: login, p_senha: senha };
  const secretaria = await rpcNoGem(gem, "validar_acesso", parametros);
  const contaSecretaria = secretaria?.[0];
  if (contaSecretaria?.perfil === "secretaria") {
    return { nome: contaSecretaria.nome || "Coordenação", perfil: "Secretaria", gem };
  }
  const pessoas = await rpcNoGem(gem, "validar_acesso_gem_pessoas", parametros);
  const conta = pessoas?.[0];
  if (!conta) return null;
  return { nome: conta.nome, perfil: conta.perfil === "professora" ? "Professora" : "Aluna", gem };
}

async function validarMaster(email, senha) {
  const url = process.env.SUPABASE_URL, anon = process.env.SUPABASE_ANON_KEY, chave = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !anon || !chave) return null;
  const login = await fetch(`${url}/auth/v1/token?grant_type=password`, {
    method: "POST", headers: { apikey: anon, "Content-Type": "application/json" }, body: JSON.stringify({ email, password: senha })
  });
  if (!login.ok) return null;
  const usuario = (await login.json()).user;
  if (!usuario?.id) return null;
  const perfil = await fetch(`${url}/rest/v1/plataforma_usuarios?auth_user_id=eq.${encodeURIComponent(usuario.id)}&select=nome,papel,ativo,status_convite`, {
    headers: { apikey: chave, Authorization: `Bearer ${chave}` }
  });
  if (!perfil.ok) return null;
  const conta = (await perfil.json())?.[0];
  return conta?.papel === "master" && conta.ativo && conta.status_convite === "ativo" ? conta : null;
}

module.exports = async function r2Session(request, response) {
  if (request.method === "DELETE") { limparCookie(response); return response.status(204).end(); }
  // O cookie é HttpOnly: o navegador o envia, mas nenhum script consegue lê-lo.
  // Esta rota só devolve a identidade mínima necessária para reconstruir a tela
  // depois de atualizar a página.
  if (request.method === "GET") {
    const acesso = sessao(request);
    if (!acesso) return response.status(401).json({ session: false });
    return response.status(200).json({ enabled: configurado() && !acesso.externo, session: true, nome: acesso.nome, perfil: acesso.perfil, gem: acesso.gem || "vila-verde", externo: Boolean(acesso.externo) });
  }
  if (request.method !== "POST") return response.status(405).json({ error: "Método não permitido." });
  // A mesma sessão curta protege o R2 e o Analítico IA. O R2 continua
  // opcional: a sessão pode existir mesmo antes de suas chaves serem salvas.
  if (!sessaoConfigurada() || !process.env.SUPABASE_SERVICE_ROLE_KEY) return response.status(200).json({ enabled: false, session: false });
  try {
    const login = String(request.body?.login || "").trim().toLowerCase(), senha = String(request.body?.senha || "");
    if (!login || !senha) return response.status(400).json({ error: "Dados de acesso ausentes." });
    const slug = slugValido(request.body?.gem) || "vila-verde";
    if (slug !== "vila-verde") {
      const contaExterna = await validarNoGemExterno(slug, login, senha);
      if (!contaExterna) return response.status(401).json({ error: "Credenciais inválidas." });
      definirCookie(response, criarSessao({ nome: contaExterna.nome, perfil: contaExterna.perfil, gem: slug, externo: true }));
      return response.status(200).json({ enabled: false, session: true, gem: slug, externo: true });
    }
    const emailMaster = login === "master" ? "jessicavitorioit@gmail.com" : login;
    if (emailMaster.includes("@")) {
      const master = await validarMaster(emailMaster, senha);
      if (master) {
        definirCookie(response, criarSessao({ nome: master.nome || "Master", perfil: "Master", gem: "vila-verde" }));
        return response.status(200).json({ enabled: configurado(), session: true, gem: "vila-verde", externo: false });
      }
    }
    const secretaria = await supabaseRpc("validar_acesso", { p_login: login, p_senha: senha });
    const contaSecretaria = secretaria?.[0];
    if (contaSecretaria?.perfil === "secretaria") {
      definirCookie(response, criarSessao({ nome: contaSecretaria.nome || "Coordenação", perfil: "Secretaria", gem: "vila-verde" }));
      return response.status(200).json({ enabled: configurado(), session: true, gem: "vila-verde", externo: false });
    }
    const pessoas = await supabaseRpc("validar_acesso_gem_pessoas", { p_login: login, p_senha: senha });
    const conta = pessoas?.[0];
    if (!conta) return response.status(401).json({ error: "Credenciais inválidas." });
    definirCookie(response, criarSessao({ nome: conta.nome, perfil: conta.perfil === "professora" ? "Professora" : "Aluna", gem: "vila-verde" }));
    return response.status(200).json({ enabled: configurado(), session: true, gem: "vila-verde", externo: false });
  } catch (_) { return response.status(401).json({ error: "Não foi possível validar a sessão." }); }
};
