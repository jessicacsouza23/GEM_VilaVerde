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
  if (!valor || !valor.includes(".")) return null;
  const [payload, assinatura] = valor.split(".");
  const esperada = assinar(payload);
  if (assinatura.length !== esperada.length || !crypto.timingSafeEqual(Buffer.from(assinatura), Buffer.from(esperada))) return null;
  try {
    const dados = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    return Number(dados.exp) > Math.floor(Date.now() / 1000) ? dados : null;
  } catch (_) { return null; }
}

// Cookies emitidos antes da implantação multi-GEM não possuem `gem`; eles
// continuam válidos exclusivamente para o Vila Verde até expirarem.
function sessaoDoVilaVerde(request) {
  const acesso = sessao(request);
  return acesso && !acesso.externo && (!acesso.gem || acesso.gem === "vila-verde") ? acesso : null;
}

function definirCookie(response, token) {
  response.setHeader("Set-Cookie", `${COOKIE}=${token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${MAX_AGE}`);
}

function limparCookie(response) {
  response.setHeader("Set-Cookie", `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`);
}

module.exports = { configurado, sessaoConfigurada, criarSessao, sessao, sessaoDoVilaVerde, definirCookie, limparCookie };
