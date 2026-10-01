const { configurado } = require("./r2-auth");

module.exports = function r2Status(_request, response) {
  response.setHeader("Cache-Control", "no-store");
  return response.status(200).json({ enabled: configurado() });
};
