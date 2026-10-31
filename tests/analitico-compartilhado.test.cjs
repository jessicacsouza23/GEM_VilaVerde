const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../js/gem-data.js'),'utf8');
const trecho=source.slice(source.indexOf('  async function dadosAnalitico()'),source.indexOf('  async function dadosExportacaoRelatorio()'));
function preparar(falhar=false){
 const registros=Array.from({length:1203},(_,i)=>({id:i,Aluna:`Aluna ${i%3}`,Instrutora:i%2?'Outra professora':'Professora atual',Observacao:'Observação preservada'}));
 const chamadas=[];
 const banco={from(tabela){const q={select(){return q;},order(){return q;},range:async(a,b)=>{chamadas.push([tabela,a,b]);return falhar&&tabela==='historico_geral'&&a===500?{error:{message:'Falha de leitura'}}:{data:(tabela==='historico_geral'?registros:[{nome:'Aluna nunca atendida'}]).slice(a,b+1)};},then(ok){return Promise.resolve({data:[]}).then(ok);}};return q;}};
 const ctx={obterCliente:async()=>banco};vm.createContext(ctx);vm.runInContext(trecho,ctx);return {ctx,chamadas};
}
test('analítico inclui todas as professoras e alunas da base atual em todas as páginas',async()=>{
 const {ctx,chamadas}=preparar();const r=await ctx.dadosAnalitico();
 assert.equal(r.historico.length,1203);assert.equal(r.alunas[0].nome,'Aluna nunca atendida');
 assert.ok(r.historico.some(r=>r.Instrutora==='Outra professora'));
 assert.ok(r.historico.every(r=>r.Observacao==='Observação preservada'));
 assert.equal(chamadas.filter(c=>c[0]==='historico_geral').length,3);
});
test('falha em página posterior não apresenta prontuário incompleto como completo',async()=>{
 await assert.rejects(preparar(true).ctx.dadosAnalitico(),/Falha de leitura/);
});
