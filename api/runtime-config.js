// Esta função entrega somente a URL e a chave pública (anon) do Supabase.
// A service_role key jamais deve ser configurada ou retornada aqui.
module.exports = function runtimeConfig(request, response) {
  const url = process.env.SUPABASE_URL;
  const anonKey = process.env.SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    return response.status(503).json({ error: "Configuração do aplicativo indisponível." });
  }
  response.setHeader("Cache-Control", "no-store");
  return response.status(200).json({ url, anonKey });
};
