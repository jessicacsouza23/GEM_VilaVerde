// Autorização interna compartilhada entre o proxy e as URLs assinadas.
// Nunca confiar em perfil/nome enviados pelo navegador: usar apenas a sessão assinada.
async function consultar(base, tabela, filtros) {
  const url = new URL(`/rest/v1/${tabela}`, base.url);
  url.search = new URLSearchParams(filtros).toString();
  const resposta = await fetch(url, {
    headers: { apikey: base.key, Authorization: `Bearer ${base.key}` },
    redirect: "error", signal: AbortSignal.timeout(8000)
  });
  if (!resposta.ok) throw new Error("Não foi possível verificar a permissão da foto.");
  const dados = await resposta.json();
  if (!Array.isArray(dados)) throw new Error("Resposta de permissão inválida.");
  return dados;
}

async function baseDaUnidade(slug) {
  const principal = { url: process.env.SUPABASE_URL, key: process.env.SUPABASE_SERVICE_ROLE_KEY };
  if (!principal.url || !principal.key) throw new Error("Configuração de autorização ausente.");
  if (slug === "vila-verde") return principal;
  const [gem] = await consultar(principal, "gems", { slug: `eq.${slug}`, ativo: "eq.true", select: "supabase_url,supabase_anon_key", limit: "1" });
  if (!gem?.supabase_url || !gem.supabase_anon_key) return null;
  const url = new URL(gem.supabase_url);
  if (url.protocol !== "https:" || !/^[a-z0-9-]+\.supabase\.co$/.test(url.hostname) || url.port || url.username || url.password) return null;
  return { url: url.origin, key: gem.supabase_anon_key };
}

async function podeLerFoto(acesso, chave) {
  if (!acesso || typeof chave !== "string") return false;
  const slug = acesso.gem || "vila-verde";
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) return false;
  const prefixo = `gems/${slug}/`;
  const relativa = chave.startsWith(prefixo) ? chave.slice(prefixo.length) : slug === "vila-verde" ? chave : "";
  const match = /^(fotos_alunas|fotos_professoras|fotos_secretaria_gem|logo_gem)\/([A-Za-z0-9._-]+)$/.exec(relativa);
  if (!match) return false;
  const tipo = match[1];
  if (acesso.perfil === "Secretaria") return true;
  if (tipo === "logo_gem") return ["Aluna", "Professora", "Master"].includes(acesso.perfil);
  if (!["Aluna", "Professora"].includes(acesso.perfil)) return false;
  const propria = (acesso.perfil === "Aluna" && tipo === "fotos_alunas") || (acesso.perfil === "Professora" && tipo === "fotos_professoras");
  const pedagogica = acesso.perfil === "Professora" && tipo === "fotos_alunas";
  if (!propria && !pedagogica) return false;
  const base = await baseDaUnidade(slug);
  if (!base) return false;
  const filtros = { select: "foto_path", foto_path: `eq.r2:${chave}`, limit: "1" };
  if (propria) filtros.nome = `eq.${acesso.nome}`;
  const tabela = tipo === "fotos_alunas" ? "alunas" : "professoras";
  const registros = await consultar(base, tabela, filtros);
  return registros.some((registro) => registro.foto_path === `r2:${chave}`);
}

module.exports = { podeLerFoto };
