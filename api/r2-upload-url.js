const crypto = require("crypto");
const { PutObjectCommand } = require("@aws-sdk/client-s3");
const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");
const { configurado, sessaoComR2 } = require("./r2-auth");
const { clienteR2, bucket } = require("./r2-client");

const TIPOS = { aluna: "fotos_alunas", professora: "fotos_professoras", secretaria: "fotos_secretaria_gem", logo: "logo_gem" };
const MIMES = new Set(["image/jpeg", "image/png", "image/webp"]);

module.exports = async function r2UploadUrl(request, response) {
  if (request.method !== "POST") return response.status(405).json({ error: "Método não permitido." });
  if (!configurado()) return response.status(503).json({ error: "R2 ainda não está configurado." });
  const acesso = sessaoComR2(request);
  const podeEnviar = acesso?.perfil === "Secretaria" || (acesso?.perfil === "Professora" && request.body?.tipo === "professora");
  if (!podeEnviar) return response.status(401).json({ error: "Entre como Secretaria para enviar fotos ou como Professora para alterar sua própria foto." });
  try {
    const { tipo, nome, contentType, tamanho } = request.body || {};
    if (!TIPOS[tipo] || !MIMES.has(contentType) || Number(tamanho) <= 0 || Number(tamanho) > 5 * 1024 * 1024) return response.status(400).json({ error: "Arquivo de foto inválido." });
    const extensao = contentType === "image/jpeg" ? "jpg" : contentType.split("/")[1];
    const base = String(nome || "foto").replace(/[^a-zA-Z0-9._-]+/g, "_").slice(0, 80);
    const gem = String(acesso.gem || "vila-verde");
    const chave = `gems/${gem}/${TIPOS[tipo]}/${crypto.randomUUID()}_${base || `foto.${extensao}`}`;
    const url = await getSignedUrl(clienteR2(), new PutObjectCommand({ Bucket: bucket(), Key: chave, ContentType: contentType }), { expiresIn: 300 });
    return response.status(200).json({ url, key: `r2:${chave}` });
  } catch (_) { return response.status(500).json({ error: "Não foi possível preparar o envio da foto." }); }
};
