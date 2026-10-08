const CACHE = "gem-vila-verde-v17";
const RUNTIME_IMAGES = "gem-vila-verde-images-v1";
const FILES = ["./", "./index.html", "./styles.css", "./app.js?v=20261008-busca-ativa-5", "./manifest.webmanifest", "./icon.svg", "./js/gem-data.js?v=20261008-busca-ativa", "./js/rodizio-engine.js?v=20261007-horarios-2", "./js/pwa-identity.js", "./js/busca-ativa.js?v=20261008-4"];
self.addEventListener("install", (event) => event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(FILES)).then(() => self.skipWaiting())));
self.addEventListener("activate", (event) => event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE && key !== RUNTIME_IMAGES).map((key) => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  // Fotos e logos do Storage do Supabase são servidas por URLs assinadas. Com
  // a URL reaproveitada pelo app, esta cópia local evita nova transferência ao
  // abrir telas diferentes ou ao usar o aplicativo instalado.
  const fotoSupabase = url.hostname.endsWith(".supabase.co") && url.pathname.includes("/storage/v1/object/");
  const fotoR2 = url.hostname.endsWith(".r2.cloudflarestorage.com");
  // A rota /api/r2-file é privada e depende da sessão. Ela não pode ser
  // guardada neste cache, pois um segundo usuário do mesmo aparelho poderia
  // receber uma imagem deixada pela conta anterior.
  if (fotoSupabase || fotoR2) {
    event.respondWith(caches.open(RUNTIME_IMAGES).then(async (cache) => {
      const salvo = await cache.match(event.request);
      if (salvo) return salvo;
      try {
        const resposta = await fetch(event.request);
        if (resposta?.ok || resposta?.type === "opaque") cache.put(event.request, resposta.clone());
        return resposta;
      } catch (_) { return salvo || Response.error(); }
    }));
    return;
  }
  // Para os arquivos do próprio aplicativo, a rede é priorizada. Assim, uma
  // publicação nova na Vercel aparece também no PWA instalado; sem internet,
  // a última versão em cache continua disponível.
  if (url.origin === self.location.origin && !url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request).then(async (resposta) => {
      if (resposta?.ok) {
        const cache = await caches.open(CACHE);
        cache.put(event.request, resposta.clone());
      }
      return resposta;
    }).catch(async () => (await caches.match(event.request)) || Response.error()));
    return;
  }
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
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
