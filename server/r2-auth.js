const crypto = require("crypto");

const COOKIE = "gem_r2_session";
const MAX_AGE = 60 * 60 * 8;

function sessaoConfigurada() {
  return Boolean(process.env.SESSION_SECRET);
}

function configurado() {
  return Boolean(process.env.R2_ACCOUNT_ID && process.env.R2_ACCESS_KEY_ID && process.env.R2_SECRET_ACCESS_KEY && process.env.R2_BUCKET_NAME && sessaoConfigurada());
}

function assinar(texto) {
  return crypto.createHmac("sha256", process.env.SESSION_SECRET).update(texto).digest("base64url");
}

function criarSessao({ nome, perfil, gem = "vila-verde", externo = false }) {
  const payload = Buffer.from(JSON.stringify({
    nome: String(nome || ""), perfil: String(perfil || ""),
    gem: String(gem || "vila-verde"), externo: Boolean(externo),
    exp: Math.floor(Date.now() / 1000) + MAX_AGE
  })).toString("base64url");
  return `${payload}.${assinar(payload)}`;
}

function lerCookies(request) {
  return String(request.headers.cookie || "").split(";").reduce((resultado, item) => {
    const texto = item.trim(), indice = texto.indexOf("=");
    if (indice > 0) resultado[texto.slice(0, indice)] = texto.slice(indice + 1);
    return resultado;
  }, {});
}

function sessao(request) {
  if (!sessaoConfigurada()) return null;
  const valor = lerCookies(request)[COOKIE];
  if (!valor || valor.length > 4096 || !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}$/.test(valor)) return null;
  const [payload, assinatura] = valor.split(".");
  const esperada = assinar(payload);
  if (assinatura.length !== esperada.length || !crypto.timingSafeEqual(Buffer.from(assinatura), Buffer.from(esperada))) return null;
  try {
    const dados = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    const agora = Math.floor(Date.now() / 1000);
    if (!Number.isInteger(dados.exp) || dados.exp <= agora || dados.exp > agora + MAX_AGE) return null;
    if (typeof dados.nome !== "string" || !dados.nome.trim() || dados.nome.length > 300) return null;
    if (!["Aluna", "Professora", "Secretaria", "Master"].includes(dados.perfil)) return null;
    if (dados.gem !== undefined && (typeof dados.gem !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(dados.gem))) return null;
    return dados;
  } catch (_) { return null; }
}

// Cookies emitidos antes da implantação multi-GEM não possuem `gem`; eles
// continuam válidos exclusivamente para o Vila Verde até expirarem.
function sessaoDoVilaVerde(request) {
  const acesso = sessao(request);
  return acesso && !acesso.externo && (!acesso.gem || acesso.gem === "vila-verde") ? acesso : null;
}

// Todas as unidades usam o mesmo bucket, mas cada sessão só enxerga o seu
// próprio prefixo. Mantemos sessaoDoVilaVerde para compatibilidade com os
// arquivos antigos, sem restringir os novos GEMs ao Storage do Supabase.
function sessaoComR2(request) {
  const acesso = sessao(request);
  return acesso && String(acesso.gem || "vila-verde").match(/^[a-z0-9]+(?:-[a-z0-9]+)*$/) ? acesso : null;
}

function definirCookie(response, token) {
  response.setHeader("Set-Cookie", `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${MAX_AGE}`);
}

function limparCookie(response) {
  response.setHeader("Set-Cookie", `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`);
}

function origemPermitida(request) {
  if (request.headers["sec-fetch-site"] === "cross-site") return false;
  const origem = request.headers.origin;
  if (!origem) return true; // Clientes não navegador continuam precisando de autenticação.
  try {
    const url = new URL(origem);
    return url.protocol === "https:" && url.host === request.headers.host;
  } catch (_) { return false; }
}

module.exports = { configurado, sessaoConfigurada, criarSessao, sessao, sessaoDoVilaVerde, sessaoComR2, definirCookie, limparCookie, origemPermitida };
