const { sessao } = require("./r2-auth");

async function escolherModelo(chave) {
  if (process.env.GEMINI_MODEL) return process.env.GEMINI_MODEL;
  const resposta = await fetch("https://generativelanguage.googleapis.com/v1beta/models", { headers: { "x-goog-api-key": chave } });
  if (!resposta.ok) throw new Error("Não foi possível consultar os modelos de IA disponíveis.");
  const modelos = (await resposta.json()).models || [];
  const preferidos = ["gemini-3.5-flash-lite", "gemini-2.5-flash-lite", "gemini-2.0-flash"];
  for (const nome of preferidos) {
    const modelo = modelos.find((item) => String(item.name || "").endsWith(`/${nome}`));
    if (modelo?.supportedGenerationMethods?.includes("generateContent")) return nome;
  }
  const alternativo = modelos.find((item) => item.supportedGenerationMethods?.includes("generateContent"));
  if (!alternativo?.name) throw new Error("Nenhum modelo de texto está disponível para esta chave de IA.");
  return String(alternativo.name).replace(/^models\//, "");
}

module.exports = async function analiticoIa(request, response) {
  if (request.method !== "POST") return response.status(405).json({ error: "Método não permitido." });
  if (!process.env.GEMINI_API_KEY) return response.status(503).json({ error: "A IA ainda não está configurada. Cadastre GEMINI_API_KEY na Vercel." });
  const acesso = sessao(request);
  if (!acesso || !["Secretaria", "Professora", "Master"].includes(acesso.perfil)) return response.status(401).json({ error: "Entre novamente no GEM para usar a análise com IA." });
  const resumo = String(request.body?.resumo || "").trim().slice(0, 12000);
  const pergunta = String(request.body?.pergunta || "").trim().slice(0, 1200);
  if (!resumo) return response.status(400).json({ error: "Não há dados suficientes para analisar." });

  const instrucao = "Você é uma coordenadora pedagógica de educação musical. Responda em português do Brasil, com tom acolhedor e objetivo. Use SOMENTE os dados fornecidos. Não invente fatos, não faça diagnósticos clínicos, não exponha dados sensíveis e não julgue a aluna. Estruture em: visão geral; pontos fortes; pontos que precisam de reforço; plano prático para as próximas aulas. Quando não houver dado suficiente, diga isso claramente.";
  const texto = `${instrucao}\n\nDADOS REGISTRADOS NO GEM:\n${resumo}${pergunta ? `\n\nPERGUNTA DA PROFESSORA/SECRETARIA:\n${pergunta}` : ""}`;
  try {
    const modelo = await escolherModelo(process.env.GEMINI_API_KEY);
    const resultado = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(modelo)}:generateContent`, {
      method: "POST",
      headers: { "x-goog-api-key": process.env.GEMINI_API_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ contents: [{ parts: [{ text: texto }] }], generationConfig: { temperature: 0.3, maxOutputTokens: 1000 } })
    });
    const corpo = await resultado.json().catch(() => ({}));
    const respostaIa = corpo?.candidates?.[0]?.content?.parts?.map((parte) => parte.text || "").join("\n").trim();
    if (!resultado.ok || !respostaIa) throw new Error(corpo?.error?.message || "A IA não retornou uma resposta.");
    return response.status(200).json({ texto: respostaIa, modelo });
  } catch (erro) { return response.status(502).json({ error: erro.message || "Não foi possível gerar a análise." }); }
};
