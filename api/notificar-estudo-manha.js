const { enviarLembretesEstudo } = require("./notificar-pendencias");

module.exports = async function notificarEstudoManha(request, response) {
  return enviarLembretesEstudo(request, response, "manha");
};
