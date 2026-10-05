const { enviarLembretesEstudo } = require("./notificar-pendencias");

module.exports = async function notificarEstudoTarde(request, response) {
  return enviarLembretesEstudo(request, response, "tarde");
};
