const CACHE = "gem-vila-verde-v23";
const FILES = ["./", "./index.html", "./styles.css", "./app.js?v=20261012-coordenadora", "./manifest.webmanifest", "./icon.svg", "./js/gem-data.js?v=20261013-seguranca", "./js/rodizio-engine.js?v=20261014-trocas-coletivas", "./js/pwa-identity.js", "./js/busca-ativa.js?v=20261008-4"];
self.addEventListener("install", (event) => event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener("activate", (event) => event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key.startsWith("gem-vila-verde-") && key !== CACHE).map((key) => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  // Só arquivos públicos da interface podem ser armazenados no aparelho.
  // APIs, fotos privadas e respostas do Supabase nunca têm fallback em cache.
  const estatico = url.origin === self.location.origin && FILES.some((file) => new URL(file, self.location.href).pathname === url.pathname);
  if (!estatico) {
    event.respondWith(fetch(event.request, { cache: "no-store" }));
    return;
  }
  event.respondWith(fetch(event.request).then(async (resposta) => {
    if (resposta?.ok && !/no-store|private/i.test(resposta.headers.get("Cache-Control") || "")) {
      const cache = await caches.open(CACHE);
      await cache.put(event.request, resposta.clone());
    }
    return resposta;
  }).catch(async () => (await caches.match(event.request)) || Response.error()));
});
self.addEventListener("push", (event) => {
  let mensagem = {};
  try { mensagem = event.data?.json() || {}; } catch (_) { mensagem = { body: event.data?.text() || "Você tem uma nova atualização no GEM." }; }
  event.waitUntil(self.registration.showNotification(mensagem.title || "GEM Musical", {
    body: mensagem.body || "Você tem uma nova atualização.",
    icon: "./icon.svg",
    badge: "./icon.svg",
    data: { url: mensagem.url || "./" }
  }));
});
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data?.url || "./"));
});
