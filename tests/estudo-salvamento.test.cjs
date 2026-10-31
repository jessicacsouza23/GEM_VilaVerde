const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync(require.resolve('../js/gem-data.js'),'utf8');
function preparar(error){
 let gravado;
 const ctx={obterCliente:async()=>({from(t){assert.equal(t,'estudo_diario');return {upsert(row,opts){assert.equal(opts.onConflict,'aluna,data');gravado=row;return {select(){return {single:async()=>({data:error?null:row,error})};}};}};}}),dataBr:()=> '31/10/2026'};
 vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('  async function salvarEstudoDiario('),src.indexOf('  async function excluirEstudoDiario(')),ctx);return {ctx,get:()=>gravado};
}
test('salva estudo na fonte dos analíticos com aluna, data e horários únicos',async()=>{
 const {ctx,get}=preparar();const r=await ctx.salvarEstudoDiario({aluna:'Aluna Teste',dataIso:'2026-10-31',horarios:['14:00 às 14:30','14:00 às 14:30']});assert.equal(r.aluna,'Aluna Teste');assert.equal(r.data,'31/10/2026');assert.equal(r.horarios.length,1);assert.equal(get().horarios.length,1);
});
test('erro de permissão ou configuração não confirma estudo salvo',async()=>{
 for(const code of ['42501','42P10','PGRST205'])await assert.rejects(preparar({code}).ctx.salvarEstudoDiario({aluna:'A',dataIso:'2026-10-31',horarios:['14:00 às 15:00']}),new RegExp(code));
});
