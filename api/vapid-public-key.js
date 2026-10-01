module.exports = function vapidPublicKey(request, response) {
  const key = process.env.PUSH_VAPID_PUBLIC_KEY;
  if (!key) return response.status(503).json({ error: "Notificações ainda não foram configuradas." });
  response.setHeader("Cache-Control", "no-store");
  return response.status(200).json({ publicKey: key });
};
