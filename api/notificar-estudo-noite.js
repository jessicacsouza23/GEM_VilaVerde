const { enviarLembretesEstudo } = require("./notificar-pendencias");

module.exports = async function notificarEstudoNoite(request, response) {
  return enviarLembretesEstudo(request, response, "noite");
};
