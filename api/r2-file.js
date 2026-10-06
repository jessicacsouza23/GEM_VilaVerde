const { GetObjectCommand } = require("@aws-sdk/client-s3");
const { configurado, sessaoComR2 } = require("./r2-auth");
const { clienteR2, bucket } = require("./r2-client");

async function bytesDoObjetoR2(corpo) {
  if (!corpo) throw new Error("O R2 devolveu o arquivo sem conteúdo.");
  // O SDK acrescenta este método nas execuções Node mais recentes.
  if (typeof corpo.transformToByteArray === "function") return corpo.transformToByteArray();
  // Em algumas funções serverless o corpo chega como Web ReadableStream.
  if (typeof corpo.arrayBuffer === "function") return new Uint8Array(await corpo.arrayBuffer());
  // E em outras como stream Node. Não dependemos de um único formato da
  // Vercel para que a foto que já está no R2 possa ser exibida.
  if (typeof corpo[Symbol.asyncIterator] === "function") {
    const partes = [];
    for await (const parte of corpo) partes.push(Buffer.isBuffer(parte) ? parte : Buffer.from(parte));
    return Buffer.concat(partes);
  }
  throw new Error("Formato de arquivo do R2 não suportado pela função.");
}

// As imagens seguem privadas no R2. Em vez de entregar uma URL R2 ao
// navegador, esta rota as fornece no mesmo domínio do aplicativo. Assim a
// exibição não depende de CORS nem de uma URL assinada exposta no HTML.
module.exports = async function r2File(request, response) {
  if (request.method !== "GET") return response.status(405).json({ error: "Método não permitido." });
  if (!configurado()) return response.status(503).json({ error: "R2 ainda não está configurado." });
  const acesso = sessaoComR2(request);
  if (!acesso) return response.status(401).json({ error: "Sua sessão de fotos expirou. Entre novamente no GEM." });
  const chave = String(request.query?.key || "").replace(/^r2:/, "");
  const gem = String(acesso.gem || "vila-verde");
  const chaveDaUnidade = new RegExp(`^gems/${gem}/(fotos_alunas|fotos_professoras|fotos_secretaria_gem|logo_gem)/[A-Za-z0-9._-]+$`);
  // Compatibilidade: as fotos do Vila Verde gravadas antes do modo
  // multi-GEM não tinham o prefixo gems/vila-verde/.
  const fotoLegadaVilaVerde = gem === "vila-verde" && /^(fotos_alunas|fotos_professoras|fotos_secretaria_gem|logo_gem)\/[A-Za-z0-9._-]+$/.test(chave);
  if (!chaveDaUnidade.test(chave) && !fotoLegadaVilaVerde) {
    return response.status(400).json({ error: "Arquivo inválido." });
  }
  try {
    const objeto = await clienteR2().send(new GetObjectCommand({ Bucket: bucket(), Key: chave }));
    const bytes = await bytesDoObjetoR2(objeto.Body);
    response.setHeader("Content-Type", objeto.ContentType || "application/octet-stream");
    response.setHeader("Cache-Control", "private, max-age=300");
    return response.status(200).send(Buffer.from(bytes));
  } catch (erro) {
    // Não retornamos detalhes sensíveis ao navegador, mas registramos o
    // código técnico nos Logs da Vercel para a administração conseguir
    // conferir credencial, bucket ou objeto sem adivinhar.
    console.error("Falha ao ler foto no R2", {
      name: erro?.name, code: erro?.Code || erro?.code,
      status: erro?.$metadata?.httpStatusCode, message: erro?.message
    });
    const codigo = String(erro?.name || erro?.Code || erro?.code || "");
    const ausente = codigo === "NoSuchKey" || erro?.$metadata?.httpStatusCode === 404;
    const bucketInvalido = codigo === "NoSuchBucket";
    const semPermissao = ["AccessDenied", "InvalidAccessKeyId", "SignatureDoesNotMatch", "Unauthorized"].includes(codigo)
      || erro?.$metadata?.httpStatusCode === 403;
    const mensagem = ausente ? "A foto não foi encontrada no R2."
      : bucketInvalido ? "O nome do bucket R2 configurado na Vercel não foi encontrado."
        : semPermissao ? "A chave R2 configurada na Vercel não tem permissão para ler este bucket."
          : "Não foi possível abrir a foto no R2. Consulte os Logs da Vercel para o código técnico.";
    return response.status(ausente ? 404 : 500).json({ error: mensagem });
  }
};
