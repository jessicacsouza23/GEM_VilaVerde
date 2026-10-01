const { configurado, sessaoConfigurada, criarSessao, definirCookie, limparCookie } = require("./r2-auth");

async function supabaseRpc(nome, parametros) {
  const url = process.env.SUPABASE_URL, chave = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !chave) throw new Error("SUPABASE_SERVICE_ROLE_KEY ausente.");
  const resposta = await fetch(`${url}/rest/v1/rpc/${nome}`, {
    method: "POST", headers: { apikey: chave, Authorization: `Bearer ${chave}`, "Content-Type": "application/json" }, body: JSON.stringify(parametros)
  });
  if (!resposta.ok) throw new Error("Credenciais inválidas.");
  return resposta.json();
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
  if (request.method !== "POST") return response.status(405).json({ error: "Método não permitido." });
  // A mesma sessão curta protege o R2 e o Analítico IA. O R2 continua
  // opcional: a sessão pode existir mesmo antes de suas chaves serem salvas.
  if (!sessaoConfigurada() || !process.env.SUPABASE_SERVICE_ROLE_KEY) return response.status(200).json({ enabled: false, session: false });
  try {
    const login = String(request.body?.login || "").trim().toLowerCase(), senha = String(request.body?.senha || "");
    if (!login || !senha) return response.status(400).json({ error: "Dados de acesso ausentes." });
    if (login.includes("@")) {
      const master = await validarMaster(login, senha);
      if (master) {
        definirCookie(response, criarSessao({ nome: master.nome || "Master", perfil: "Master" }));
        return response.status(200).json({ enabled: configurado(), session: true });
      }
    }
    const secretaria = await supabaseRpc("validar_acesso", { p_login: login, p_senha: senha });
    const contaSecretaria = secretaria?.[0];
    if (contaSecretaria?.perfil === "secretaria") {
      definirCookie(response, criarSessao({ nome: contaSecretaria.nome || "Coordenação", perfil: "Secretaria" }));
      return response.status(200).json({ enabled: configurado(), session: true });
    }
    const pessoas = await supabaseRpc("validar_acesso_gem_pessoas", { p_login: login, p_senha: senha });
    const conta = pessoas?.[0];
    if (!conta) return response.status(401).json({ error: "Credenciais inválidas." });
    definirCookie(response, criarSessao({ nome: conta.nome, perfil: conta.perfil === "professora" ? "Professora" : "Aluna" }));
    return response.status(200).json({ enabled: configurado(), session: true });
  } catch (_) { return response.status(401).json({ error: "Não foi possível validar a sessão." }); }
};
