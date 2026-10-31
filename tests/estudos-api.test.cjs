const {test}=require('node:test'),assert=require('node:assert/strict');
process.env.SESSION_SECRET='segredo-ficticio-para-testes';
process.env.SUPABASE_URL='https://principal.example';process.env.SUPABASE_SERVICE_ROLE_KEY='chave-servidor-teste';
const {criarSessao}=require('../server/r2-auth');const handler=require('../api/estudos');
async function executar(body,{perfil='Aluna',gem='vila-verde',externo=false,cookie=true,cross=false,falha=false}={}){
 const calls=[];const original=global.fetch;
 global.fetch=async(url,opts)=>{
   calls.push({url,opts});let data=[];
   if(url.includes('/alunas?'))data=[{nome:'Ana'}];
   else if(url.includes('/gems?'))data=[{supabase_url:'https://outro.example'}];
   else if(opts.method==='POST')data=[JSON.parse(opts.body)];
   else if(url.includes('offset=0'))data=[{aluna:'Ana',data:'31/10/2026',horarios:['14:00 às 15:00']}];
   return {ok:!falha,status:falha?403:200,json:async()=>data};
 };
 const req={method:'POST',headers:{host:'gem.example',origin:cross?'https://estranho.example':'https://gem.example',cookie:cookie?'gem_r2_session='+criarSessao({nome:'Ana',perfil,gem,externo}):''},body};
 const res={headers:{},setHeader(k,v){this.headers[k]=v;},status(s){this.code=s;return this;},json(v){this.body=v;return this;}};
 try{await handler(req,res);return {res,calls};}finally{global.fetch=original;}
}
test('aluna só lê, grava e exclui seu próprio estudo',async()=>{
 const ler=await executar({acao:'listar'});assert.equal(ler.res.code,200);assert.match(ler.calls[1].url,/aluna=eq.Ana/);
 const salvar=await executar({acao:'salvar',data:'31/10/2026',horarios:['14:00 às 15:00','14:00 às 15:00']});assert.equal(salvar.res.body.registro.aluna,'Ana');assert.equal(salvar.res.body.registro.horarios.length,1);
 const excluir=await executar({acao:'excluir',data:'31/10/2026'});assert.equal(excluir.calls[1].opts.method,'DELETE');assert.match(excluir.calls[1].url,/aluna=eq.Ana/);assert.match(excluir.calls[1].url,/data=eq.31%2F10%2F2026/);
 const outra=await executar({acao:'salvar',aluna:'Bia',data:'31/10/2026',horarios:[]});assert.equal(outra.res.code,403);assert.equal(outra.calls.length,0);
});
test('sessão ausente, origem externa e data inválida não chegam ao banco',async()=>{
 for(const [body,opts,status] of [[{acao:'listar'},{cookie:false},401],[{acao:'listar'},{cross:true},403],[{acao:'salvar',data:'31/02/2026',horarios:[]},{},400]]){const r=await executar(body,opts);assert.equal(r.res.code,status);assert.equal(r.calls.length,0);}
});
test('tela de outro GEM é recusada antes de consultar dados',async()=>{
 const r=await executar({acao:'listar',gem:'outra-unidade'});assert.equal(r.res.code,403);assert.equal(r.calls.length,0);
});
test('professoras consultam o GEM, mas não alteram estudo da aluna',async()=>{
 const ler=await executar({acao:'listar'},{perfil:'Professora'});assert.equal(ler.res.code,200);assert.ok(!ler.calls[0].url.includes('aluna=eq.'));
 assert.equal((await executar({acao:'excluir',data:'31/10/2026'},{perfil:'Professora'})).res.code,403);
});
test('GEM externo nunca usa a base principal como fallback',async()=>{
 delete process.env.GEM_ESTUDOS_BASES;
 const bloqueado=await executar({acao:'listar'},{gem:'outro',externo:true});assert.equal(bloqueado.res.code,503);assert.equal(bloqueado.calls.length,1);
 process.env.GEM_ESTUDOS_BASES=JSON.stringify({outro:{url:'https://outro.example',serviceRoleKey:'chave-outra'}});
 const liberado=await executar({acao:'listar'},{gem:'outro',externo:true});assert.equal(liberado.res.code,200);assert.ok(liberado.calls.slice(1).every(c=>c.url.startsWith('https://outro.example/')));delete process.env.GEM_ESTUDOS_BASES;
});
test('falha de banco não vira estudo vazio ou confirmação de sucesso',async()=>{
 const r=await executar({acao:'listar'},{falha:true});assert.equal(r.res.code,503);assert.ok(!r.res.body.registros);assert.equal(r.res.headers['Cache-Control'],'no-store');
});
