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

function normalizar(valor) {
  return String(valor || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
}

function disciplinaDaCelula(valor, detalhe = {}) {
  if (detalhe.tipo) return detalhe.tipo === "Canto" ? "Solfejo Melódico" : detalhe.tipo;
  const texto = String(valor || "").toUpperCase();
  if (texto.includes("SALA 8")) return "Teoria";
  if (texto.includes("SALA 9")) return "Solfejo Melódico";
  return "Prática";
}

function configurarPush() {
  const publicKey = process.env.PUSH_VAPID_PUBLIC_KEY, privateKey = process.env.PUSH_VAPID_PRIVATE_KEY;
  if (!publicKey || !privateKey || !process.env.PUSH_CONTACT_EMAIL) {
    throw new Error("Chaves de notificação não configuradas.");
  }
  webpush.setVapidDetails(`mailto:${process.env.PUSH_CONTACT_EMAIL}`, publicKey, privateKey);
}

function cronAutorizado(request) {
  return !process.env.CRON_SECRET || request.headers.authorization === `Bearer ${process.env.CRON_SECRET}`;
}

async function enviarFila(fila) {
  let enviadas = 0;
  for (const item of fila) {
    const jaEnviada = await banco(`notificacoes_enviadas?chave=eq.${encodeURIComponent(item.chave)}&select=id`);
    if (jaEnviada?.length) continue;
    try {
      await webpush.sendNotification(item.sub.subscription, JSON.stringify(item.payload));
      await banco("notificacoes_enviadas", { method: "POST", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ chave: item.chave, usuario: item.sub.usuario, tipo: item.tipo }) });
      enviadas += 1;
    } catch (error) {
      if ([404, 410].includes(error.statusCode)) {
        await banco(`push_subscriptions?endpoint=eq.${encodeURIComponent(item.sub.endpoint)}`, { method: "PATCH", headers: { Prefer: "return=minimal" }, body: JSON.stringify({ ativo: false }) });
      }
    }
  }
  return enviadas;
}

// Cada aluna/disciplina realmente escalada é conferida separadamente. Isso
// impede que um único registro da professora esconda outras aulas pendentes.
function professorasComPendencias(calendarios, historico, inicioHoje) {
  const pendentes = new Set();
  (calendarios || []).forEach((calendario) => {
    const data = dataValida(calendario.id);
    // O cron roda às 08h. A escala do próprio sábado só entra no dia seguinte,
    // depois de a professora ter tido oportunidade de lançar as aulas. A
    // cobrança não expira após uma semana: permanece diária até o registro
    // pedagógico daquela aula ser realmente enviado.
    if (!data || data >= inicioHoje) return;
    const registrosDoDia = (historico || []).filter((registro) => registro.Data === calendario.id);
    const ausentes = new Set(registrosDoDia.filter((registro) => registro.Tipo === "Chamada" && ["Ausente", "Justificada"].includes(registro.Status)).map((registro) => normalizar(registro.Aluna)));
    (calendario.escala || []).forEach((linha) => {
      const aluna = String(linha?.Aluna || "").trim();
      if (!aluna || ausentes.has(normalizar(aluna))) return;
      Object.entries(linha || {}).forEach(([horario, valor]) => {
        if (["Aluna", "_detalhes"].includes(horario) || !String(valor || "").trim()) return;
        const detalhe = linha?._detalhes?.[horario] || {};
        const componentes = Array.isArray(detalhe.componentes) && detalhe.componentes.length
          ? detalhe.componentes : [disciplinaDaCelula(valor, detalhe)];
        const professoras = detalhe.professoras_componentes || {};
        const padrao = String(valor || "").split("|").slice(1).join("|").replace(/\s*\([^)]*\)\s*$/g, "").trim();
        componentes.forEach((componente) => {
          const disciplina = componente === "Canto" ? "Solfejo Melódico" : componente;
          const professora = String(professoras[componente] || professoras[disciplina] || padrao).trim();
          if (!professora || /todas as alunas/i.test(professora)) return;
          const possuiRegistro = registrosDoDia.some((registro) => {
            const tipo = String(registro.Tipo || "").replace(/^Analise_/, "").replace(/^Canto$/, "Solfejo Melódico");
            return normalizar(registro.Aluna) === normalizar(aluna)
              && normalizar(registro.Instrutora) === normalizar(professora)
              && normalizar(tipo) === normalizar(disciplina);
          });
          if (!possuiRegistro) pendentes.add(professora);
        });
      });
    });
  });
  return pendentes;
}

module.exports = async function notificarPendencias(request, response) {
  if (!cronAutorizado(request)) return response.status(401).json({ error: "Não autorizado." });
  try {
    configurarPush();
    const [subscriptions, calendarios, historico] = await Promise.all([
      banco("push_subscriptions?ativo=eq.true&select=*"),
      banco("calendario?select=id,escala"),
      banco("historico_geral?select=Data,Aluna,Instrutora,Tipo,Status")
    ]);
    const hoje = new Date(), chaveHoje = dataBrasil(hoje), inicioHoje = dataValida(chaveHoje);
    const horaBrasil = Number(new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", hourCycle: "h23" }).format(hoje));
    const periodoEstudo = horaBrasil < 12 ? "manha" : horaBrasil < 18 ? "tarde" : "noite";
    const mensagensEstudo = {
      manha: { title: "🌤️ Bom dia! Hora de estudar", body: "Reserve alguns minutos nesta manhã para praticar sua lição do GEM." },
      tarde: { title: "🎼 Lembrete de estudo", body: "Que tal separar um momento desta tarde para estudar sua lição do GEM?" },
      noite: { title: "🌙 Antes de encerrar o dia", body: "Faça uma breve prática da sua lição do GEM para continuar evoluindo." }
    };
    const pendenciasProfessoras = professorasComPendencias(calendarios, historico, inicioHoje);
    const fila = [];
    (subscriptions || []).forEach((sub) => {
      if (sub.perfil === "Aluna") {
        fila.push({ sub, chave: `estudo:${periodoEstudo}:${chaveHoje}:${sub.endpoint}`, tipo: `estudo_${periodoEstudo}`, payload: { ...mensagensEstudo[periodoEstudo], url: "/" } });
      }
      // A cobrança pedagógica é enviada apenas pela execução da manhã.
      if (periodoEstudo === "manha" && sub.perfil === "Professora" && [...pendenciasProfessoras].some((professora) => normalizar(professora) === normalizar(sub.usuario))) {
        fila.push({ sub, chave: `registro:${chaveHoje}:${sub.endpoint}`, tipo: "registro_pendente", payload: { title: "📝 Registro de aula pendente", body: "Há aula(s) escalada(s) sem registro. Abra o GEM e conclua o lançamento.", url: "/" } });
      }
    });
    const enviadas = await enviarFila(fila);
    return response.status(200).json({ ok: true, periodoEstudo, enviadas, pendenciasProfessoras: pendenciasProfessoras.size });
  } catch (error) {
    return response.status(500).json({ error: "Falha no envio automático de notificações." });
  }
};
