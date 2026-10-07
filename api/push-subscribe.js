const { sessao } = require("./r2-auth");

async function supabaseRequest(path, options = {}) {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error("A configuração segura de notificações está incompleta.");
  const result = await fetch(`${url}/rest/v1/${path}`, {
    ...options,
    headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json", ...(options.headers || {}) }
  });
  if (!result.ok) throw new Error(await result.text());
  return result;
}

module.exports = async function pushSubscribe(request, response) {
  if (request.method !== "POST") return response.status(405).json({ error: "Método não permitido." });
  try {
    const { usuario, perfil, subscription, gem } = request.body || {};
    const acesso = sessao(request);
    if (!acesso) return response.status(401).json({ error: "Entre novamente no GEM antes de ativar lembretes." });
    if (!usuario || !["Aluna", "Professora", "Secretaria", "Master"].includes(perfil) || !subscription?.endpoint) {
      return response.status(400).json({ error: "Inscrição de notificação inválida." });
    }
    const mesmoPerfil = acesso.perfil === perfil;
    const mesmoUsuario = perfil === "Secretaria"
      ? ["Secretaria", String(acesso.nome || "")].includes(String(usuario))
      : String(acesso.nome || "") === String(usuario);
    if (!mesmoPerfil || !mesmoUsuario) return response.status(403).json({ error: "A inscrição precisa pertencer à conta que está logada." });
    const gemDaSessao = String(acesso.gem || "vila-verde").trim().toLowerCase();
    if (gem && String(gem).trim().toLowerCase() !== gemDaSessao) return response.status(403).json({ error: "A inscrição precisa pertencer ao GEM que está aberto." });
    await supabaseRequest("push_subscriptions?on_conflict=gem_slug,endpoint", {
      method: "POST",
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
      body: JSON.stringify({ gem_slug: gemDaSessao, usuario: String(usuario).trim(), perfil, endpoint: subscription.endpoint, subscription, ativo: true, updated_at: new Date().toISOString() })
    });
    return response.status(200).json({ ok: true });
  } catch (error) {
    return response.status(500).json({ error: "Não foi possível ativar as notificações." });
  }
};
