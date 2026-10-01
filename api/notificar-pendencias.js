const webpush = require("web-push");

function dataBrasil(date) {
  return new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", year: "numeric" }).format(date);
}

function dataValida(data) {
  const [dia, mes, ano] = String(data || "").split("/").map(Number);
  return ano ? new Date(Date.UTC(ano, mes - 1, dia)) : null;
}

async function banco(path, options = {}) {
  const url = process.env.SUPABASE_URL, key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error("Supabase não configurado para o envio automático.");
  const resultado = await fetch(`${url}/rest/v1/${path}`, { ...options, headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json", ...(options.headers || {}) } });
  if (!resultado.ok) throw new Error(await resultado.text());
  return resultado.status === 204 ? null : resultado.json();
}

function professorasDaEscala(escala) {
  const nomes = new Set();
  (escala || []).forEach((linha) => {
    Object.entries(linha || {}).forEach(([horario, valor]) => {
      if (["Aluna", "_detalhes"].includes(horario)) return;
      const texto = String(valor || "");
      const depoisDaBarra = texto.split("|").slice(1).join("|").trim();
      if (depoisDaBarra && !/TODAS AS ALUNAS/i.test(depoisDaBarra)) nomes.add(depoisDaBarra.replace(/\s*\([^)]*\)\s*$/g, "").trim());
    });
    Object.values(linha?._detalhes || {}).forEach((detalhe) => Object.values(detalhe?.professoras_componentes || {}).forEach((nome) => { if (nome) nomes.add(String(nome).trim()); }));
  });
  return [...nomes].filter(Boolean);
}

module.exports = async function notificarPendencias(request, response) {
  if (process.env.CRON_SECRET && request.headers.authorization !== `Bearer ${process.env.CRON_SECRET}`) return response.status(401).json({ error: "Não autorizado." });
  try {
    const publicKey = process.env.PUSH_VAPID_PUBLIC_KEY, privateKey = process.env.PUSH_VAPID_PRIVATE_KEY;
    if (!publicKey || !privateKey || !process.env.PUSH_CONTACT_EMAIL) return response.status(503).json({ error: "Chaves de notificação não configuradas." });
    webpush.setVapidDetails(`mailto:${process.env.PUSH_CONTACT_EMAIL}`, publicKey, privateKey);
    const [subscriptions, calendarios, historico] = await Promise.all([
      banco("push_subscriptions?ativo=eq.true&select=*"),
      banco("calendario?select=id,escala"),
      banco("historico_geral?select=Data,Instrutora,Tipo")
    ]);
    const hoje = new Date(), chaveHoje = dataBrasil(hoje), limite = new Date(hoje.getTime() - 7 * 86400000);
    const pendenciasProfessoras = new Set();
    (calendarios || []).forEach((calendario) => {
      const data = dataValida(calendario.id);
      if (!data || data > hoje || data < limite) return;
      professorasDaEscala(calendario.escala).forEach((professora) => {
        const temRegistro = (historico || []).some((registro) => registro.Data === calendario.id && registro.Instrutora === professora && String(registro.Tipo || "").startsWith("Analise_"));
        if (!temRegistro) pendenciasProfessoras.add(`${calendario.id}|${professora}`);
      });
    });
    const fila = [];
    (subscriptions || []).forEach((sub) => {
      if (sub.perfil === "Aluna") fila.push({ sub, chave: `estudo:${chaveHoje}:${sub.endpoint}`, tipo: "estudo", payload: { title: "🎼 Hora de estudar", body: "Separe alguns minutos para praticar sua lição do GEM hoje.", url: "/" } });
      if (sub.perfil === "Professora" && [...pendenciasProfessoras].some((item) => item.endsWith(`|${sub.usuario}`))) fila.push({ sub, chave: `registro:${chaveHoje}:${sub.endpoint}`, tipo: "registro_pendente", payload: { title: "📝 Registro de aula pendente", body: "Há uma aula escalada sem registro. Abra o GEM e conclua o lançamento.", url: "/" } });
    });
    let enviadas = 0;
    for (const item of fila) {
      const jaEnviada = await banco(`notificacoes_enviadas?chave=eq.${encodeURIComponent(item.chave)}&select=id`);
      if (jaEnviada?.length) continue;
      try {
        await webpush.sendNotification(item.sub.subscription, JSON.stringify(item.payload));
        await banco("notificacoes_enviadas", { method: "POST", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ chave: item.chave, usuario: item.sub.usuario, tipo: item.tipo }) });
        enviadas += 1;
      } catch (error) {
        if ([404, 410].includes(error.statusCode)) await banco(`push_subscriptions?endpoint=eq.${encodeURIComponent(item.sub.endpoint)}`, { method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ ativo: false }) });
      }
    }
    return response.status(200).json({ ok: true, enviadas, pendenciasProfessoras: pendenciasProfessoras.size });
  } catch (error) {
    return response.status(500).json({ error: "Falha no envio automático de notificações." });
  }
};
