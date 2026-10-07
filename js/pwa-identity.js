// Seleciona o manifesto antes do login, inclusive ao instalar pelo menu
// do navegador. Não usa nome em localStorage, que pode ser de outro GEM.
(function () {
  const slug = String(new URLSearchParams(window.location.search).get("gem") || "")
    .trim().toLowerCase().replace(/[^a-z0-9-]/g, "");
  const manifesto = !slug || slug === "vila-verde"
    ? "/manifest.webmanifest"
    : `/api/runtime-config?manifest=${encodeURIComponent(slug)}`;
  document.querySelector("#gem-manifest").setAttribute("href", manifesto);
  fetch(manifesto, { cache: "no-store" }).then(async (resposta) => {
    if (!resposta.ok) return;
    const dados = await resposta.json();
    if (!dados.name) return;
    document.querySelector('meta[name="apple-mobile-web-app-title"]').content = dados.name;
    document.title = `${dados.name} — gestão musical`;
  }).catch(() => { /* A identidade visual pode tentar novamente ao conectar. */ });
})();
