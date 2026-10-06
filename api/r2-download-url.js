const { GetObjectCommand } = require("@aws-sdk/client-s3");
const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");
const { configurado, sessaoComR2 } = require("./r2-auth");
const { clienteR2, bucket } = require("./r2-client");

module.exports = async function r2DownloadUrl(request, response) {
  if (request.method !== "GET") return response.status(405).json({ error: "Método não permitido." });
  if (!configurado()) return response.status(503).json({ error: "R2 ainda não está configurado." });
  const acesso = sessaoComR2(request);
  if (!acesso) return response.status(401).json({ error: "Sua sessão de fotos expirou. Entre novamente no GEM." });
  const chave = String(request.query?.key || "").replace(/^r2:/, "");
  const gem = String(acesso.gem || "vila-verde");
  const chaveDaUnidade = new RegExp(`^gems/${gem}/(fotos_alunas|fotos_professoras|fotos_secretaria_gem|logo_gem)/[A-Za-z0-9._-]+$`);
  const fotoLegadaVilaVerde = gem === "vila-verde" && /^(fotos_alunas|fotos_professoras|fotos_secretaria_gem|logo_gem)\/[A-Za-z0-9._-]+$/.test(chave);
  if (!chaveDaUnidade.test(chave) && !fotoLegadaVilaVerde) return response.status(400).json({ error: "Arquivo inválido." });
  try {
    const url = await getSignedUrl(clienteR2(), new GetObjectCommand({ Bucket: bucket(), Key: chave }), { expiresIn: 3600 });
    return response.status(200).json({ url });
  } catch (_) { return response.status(500).json({ error: "Não foi possível abrir a foto." }); }
};
