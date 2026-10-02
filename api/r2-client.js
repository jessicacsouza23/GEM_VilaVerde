const { S3Client } = require("@aws-sdk/client-s3");
const { configurado } = require("./r2-auth");

function clienteR2() {
  if (!configurado()) throw new Error("R2 não configurado.");
  return new S3Client({
    region: "auto",
    // O R2 não aceita os parâmetros de checksum que as versões novas do SDK
    // da AWS incluem por padrão nas URLs assinadas; sem isto o envio falha.
    requestChecksumCalculation: "WHEN_REQUIRED",
    responseChecksumValidation: "WHEN_REQUIRED",
    endpoint: `https://${process.env.R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
    credentials: { accessKeyId: process.env.R2_ACCESS_KEY_ID, secretAccessKey: process.env.R2_SECRET_ACCESS_KEY }
  });
}

function bucket() { return process.env.R2_BUCKET_NAME; }

module.exports = { clienteR2, bucket };
