const { GetObjectCommand } = require("@aws-sdk/client-s3");
const { configurado, sessaoDoVilaVerde } = require("./r2-auth");
const { clienteR2, bucket } = require("./r2-client");

// As imagens seguem privadas no R2. Em vez de entregar uma URL R2 ao
// navegador, esta rota as fornece no mesmo domínio do aplicativo. Assim a
// exibição não depende de CORS nem de uma URL assinada exposta no HTML.
module.exports = async function r2File(request, response) {
  if (request.method !== "GET") return response.status(405).json({ error: "Método não permitido." });
  if (!configurado()) return response.status(503).json({ error: "R2 ainda não está configurado." });
  if (!sessaoDoVilaVerde(request)) return response.status(401).json({ error: "Sua sessão de fotos expirou. Entre novamente no GEM Vila Verde." });
  const chave = String(request.query?.key || "").replace(/^r2:/, "");
  if (!/^(fotos_alunas|fotos_professoras|fotos_secretaria_gem|logo_gem)\/[A-Za-z0-9._-]+$/.test(chave)) {
    return response.status(400).json({ error: "Arquivo inválido." });
  }
  try {
    const objeto = await clienteR2().send(new GetObjectCommand({ Bucket: bucket(), Key: chave }));
    const bytes = await objeto.Body.transformToByteArray();
    response.setHeader("Content-Type", objeto.ContentType || "application/octet-stream");
    response.setHeader("Cache-Control", "private, max-age=300");
    return response.status(200).send(Buffer.from(bytes));
  } catch (erro) {
    const ausente = erro?.name === "NoSuchKey" || erro?.$metadata?.httpStatusCode === 404;
    return response.status(ausente ? 404 : 500).json({ error: ausente ? "A foto não foi encontrada no R2." : "Não foi possível abrir a foto no R2." });
  }
};
