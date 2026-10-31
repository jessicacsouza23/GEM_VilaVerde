const { sessao, origemPermitida } = require('./r2-auth');

function dataValida(valor) {
  const m = String(valor || '').match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return false;
  const d = new Date(Date.UTC(+m[3], +m[2]-1, +m[1]));
  return d.getUTCFullYear() === +m[3] && d.getUTCMonth() === +m[2]-1 && d.getUTCDate() === +m[1];
}
async function consultar(config, path, options = {}) {
  const r = await fetch(`${config.url.replace(/\/$/, '')}/rest/v1/${path}`, {
    ...options, headers: { apikey: config.key, Authorization: `Bearer ${config.key}`, 'Content-Type':'application/json', ...(options.headers || {}) }
  });
  if (!r.ok) throw new Error('Não foi possível acessar os estudos no banco. Peça à Secretaria para conferir a configuração do servidor.');
  return r.status === 204 ? [] : r.json();
}
async function baseDaSessao(acesso) {
  const principal = {url:process.env.SUPABASE_URL, key:process.env.SUPABASE_SERVICE_ROLE_KEY};
  if (!principal.url || !principal.key) throw new Error('Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY na Vercel.');
  const slug = acesso.gem || 'vila-verde';
  if (slug === 'vila-verde' && !acesso.externo) return principal;
  const unidades = await consultar(principal, `gems?slug=eq.${encodeURIComponent(slug)}&ativo=eq.true&select=supabase_url`);
  let bases;
  try { bases = JSON.parse(process.env.GEM_ESTUDOS_BASES || '{}'); } catch (_) { throw new Error('Configuração das bases de estudos inválida.'); }
  const base = bases[slug];
  if (!unidades[0] || !base?.url || !base?.serviceRoleKey || base.url.replace(/\/$/,'') !== String(unidades[0].supabase_url).replace(/\/$/,'')) throw new Error('O acesso seguro aos estudos deste GEM ainda não está configurado na Vercel.');
  if (!/^https:\/\//.test(base.url)) throw new Error('URL da base inválida.');
  return {url:base.url, key:base.serviceRoleKey};
}
module.exports = async function estudos(request, response) {
  response.setHeader('Cache-Control','no-store');
  if (request.method !== 'POST') return response.status(405).json({error:'Método não permitido.'});
  if (!origemPermitida(request)) return response.status(403).json({error:'Origem não permitida.'});
  const acesso = sessao(request);
  if (!acesso) return response.status(401).json({error:'Sua sessão expirou. Saia e entre novamente para acessar os estudos.'});
  const {acao, aluna, data, horarios, datas} = request.body || {};
  if (request.body?.gem && request.body.gem !== (acesso.gem || 'vila-verde')) return response.status(403).json({error:'A sessão pertence a outro GEM. Saia e entre novamente nesta unidade.'});
  if (!['listar','salvar','excluir'].includes(acao)) return response.status(400).json({error:'Operação inválida.'});
  if (acao !== 'listar' && acesso.perfil !== 'Aluna') return response.status(403).json({error:'Somente a aluna pode alterar seu estudo nesta tela.'});
  if (acesso.perfil === 'Aluna' && aluna && aluna !== acesso.nome) return response.status(403).json({error:'Você só pode acessar seus próprios estudos.'});
  if (aluna != null && (typeof aluna !== 'string' || aluna.length > 300)) return response.status(400).json({error:'Aluna inválida.'});
  if (datas != null && (!Array.isArray(datas) || datas.length > 100 || datas.some(d=>!dataValida(d)))) return response.status(400).json({error:'Datas inválidas.'});
  if (acao !== 'listar' && !dataValida(data)) return response.status(400).json({error:'Data inválida.'});
  if (acao === 'salvar' && (!Array.isArray(horarios) || horarios.length > 48 || horarios.some(h=>typeof h !== 'string' || !h.trim() || h.length > 100))) return response.status(400).json({error:'Confira os horários informados.'});
  try {
    const config = await baseDaSessao(acesso);
    const nome = acesso.perfil === 'Aluna' ? acesso.nome : aluna;
    if (acesso.perfil === 'Aluna') {
      const contas = await consultar(config, `alunas?nome=eq.${encodeURIComponent(nome)}&ativo=eq.true&select=nome`);
      if (!contas.length) return response.status(403).json({error:'Cadastro inativo ou não encontrado. Procure a Secretaria.'});
    }
    if (acao === 'listar') {
      const query = new URLSearchParams({select:'aluna,data,horarios',order:'aluna.asc,data.asc'});
      if (nome) query.set('aluna',`eq.${nome}`);
      if (datas?.length) query.set('data',`in.(${datas.flatMap(d=>[d,d.split('/').reverse().join('-')]).join(',')})`);
      const registros=[];
      for(let offset=0;;offset+=500){
        const pagina=await consultar(config,`estudo_diario?${query}&offset=${offset}&limit=500`);
        registros.push(...pagina);if(pagina.length<500)break;
      }
      return response.status(200).json({registros});
    }
    if (acao === 'salvar') {
      const registro={aluna:acesso.nome,data,horarios:[...new Set(horarios.map(h=>h.trim()))]};
      const salvo=await consultar(config,'estudo_diario?on_conflict=aluna,data&select=aluna,data,horarios',{method:'POST',headers:{Prefer:'resolution=merge-duplicates,return=representation'},body:JSON.stringify(registro)});
      if(salvo.length!==1 || salvo[0].aluna!==acesso.nome || salvo[0].data!==data)throw new Error('O banco não confirmou o estudo. Recarregue para conferir.');
      return response.status(200).json({registro:salvo[0]});
    }
    const query=new URLSearchParams({aluna:`eq.${acesso.nome}`,data:`eq.${data}`});
    await consultar(config,`estudo_diario?${query}`,{method:'DELETE',headers:{Prefer:'return=representation'}});
    return response.status(200).json({excluido:true});
  } catch(erro) { return response.status(503).json({error:erro.message}); }
};
