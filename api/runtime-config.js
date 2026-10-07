// Esta função entrega somente a URL e a chave pública (anon) do Supabase.
// A service_role key jamais deve ser configurada ou retornada aqui.
module.exports = async function runtimeConfig(request, response) {
  response.setHeader("Cache-Control", "no-store");
  // O navegador consulta esta URL também depois da instalação. O nome
  // vem do cadastro central; a identidade e o início ficam ligados ao slug.
  if (request.query?.manifest !== undefined) {
    const slug = request.query.manifest;
    if (typeof slug !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
      return response.status(400).json({ error: "GEM inválido." });
    }
    let nome = "GEM Vila Verde";
    if (slug !== "vila-verde") {
      const url = process.env.SUPABASE_URL;
      const anonKey = process.env.SUPABASE_ANON_KEY;
      if (!url || !anonKey) return response.status(503).json({ error: "Configuração do aplicativo indisponível." });
      try {
        const consulta = new URL("/rest/v1/gems", url);
        consulta.search = new URLSearchParams({ select: "nome", slug: `eq.${slug}`, ativo: "eq.true", limit: "1" }).toString();
        const resultado = await fetch(consulta, {
          headers: { apikey: anonKey, Authorization: `Bearer ${anonKey}` },
          signal: AbortSignal.timeout(8000)
        });
        if (!resultado.ok) throw new Error("Consulta indisponível");
        const gems = await resultado.json();
        nome = gems[0]?.nome?.trim();
        if (!nome) return response.status(404).json({ error: "GEM não encontrado ou inativo." });
      } catch (_) {
        return response.status(503).json({ error: "Não foi possível carregar o nome do GEM." });
      }
    }
    const inicio = slug === "vila-verde" ? "/index.html" : `/?gem=${encodeURIComponent(slug)}`;
    response.setHeader("Content-Type", "application/manifest+json; charset=utf-8");
    return response.status(200).send(JSON.stringify({
      id: inicio, name: nome, short_name: nome, lang: "pt-BR",
      start_url: inicio, scope: "/", display: "standalone",
      background_color: "#f7f8fc", theme_color: "#e94b6a",
      description: `Gestão musical — ${nome}.`,
      icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any maskable" }]
    }));
  }
  const url = process.env.SUPABASE_URL;
  const anonKey = process.env.SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    return response.status(503).json({ error: "Configuração do aplicativo indisponível." });
  }
  response.setHeader("Cache-Control", "no-store");
  return response.status(200).json({ url, anonKey });
};
