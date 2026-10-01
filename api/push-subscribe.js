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
    const { usuario, perfil, subscription } = request.body || {};
    if (!usuario || !["Aluna", "Professora", "Secretaria", "Master"].includes(perfil) || !subscription?.endpoint) {
      return response.status(400).json({ error: "Inscrição de notificação inválida." });
    }
    await supabaseRequest("push_subscriptions?on_conflict=endpoint", {
      method: "POST",
      headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
      body: JSON.stringify({ usuario: String(usuario).trim(), perfil, endpoint: subscription.endpoint, subscription, ativo: true, updated_at: new Date().toISOString() })
    });
    return response.status(200).json({ ok: true });
  } catch (error) {
    return response.status(500).json({ error: "Não foi possível ativar as notificações." });
  }
};
