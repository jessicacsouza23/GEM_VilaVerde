const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../js/gem-data.js'),'utf8');
function preparar(falha=false){
 const rows=[{Data:'31/10/2026',Tipo:'Chamada',Aluna:'A',Status:'Presente',Observacao:''}];
 const banco={from(){let modo='ler',campos,filtros={};const q={select(){return q;},eq(k,v){filtros[k]=v;return q;},update(c){modo='update';campos=c;return q;},insert(c){modo='insert';campos=c;return q;},then(resolve,reject){let data=rows.filter(r=>Object.entries(filtros).every(([k,v])=>r[k]===v));if(modo!=='ler'&&falha)return Promise.resolve({error:{message:'falha'}}).then(resolve,reject);if(modo==='update')data.forEach(r=>Object.assign(r,campos));if(modo==='insert'){rows.push({...campos});data=[rows.at(-1)];}return Promise.resolve({data}).then(resolve,reject);}};return q;}};
 const ctx={obterCliente:async()=>banco,dataBr:()=> '31/10/2026'};vm.createContext(ctx);vm.runInContext(source.slice(source.indexOf('  async function salvarChamada('),source.indexOf('  window.GemData =')),ctx);return {ctx,rows};
}
test('salva justificada e motivo, permite corrigir e confirma totais',async()=>{
 const {ctx,rows}=preparar();const resumo=await ctx.salvarChamada('2026-10-31',[{aluna:'A',status:'Justificada',observacao:'Motivo teste'},{aluna:'B',status:'Ausente'}]);
 assert.equal(resumo.justificadas,1);assert.equal(resumo.ausentes,1);assert.equal(rows[0].Observacao,'Motivo teste');
 await ctx.salvarChamada('2026-10-31',[{aluna:'A',status:'Presente'}]);assert.equal(rows.length,2);assert.equal(rows[0].Status,'Presente');
});
test('falha não apaga chamada anterior e não informa sucesso',async()=>{
 const {ctx,rows}=preparar(true);await assert.rejects(ctx.salvarChamada('2026-10-31',[{aluna:'A',status:'Justificada'}]),/0 de 1/);assert.equal(rows[0].Status,'Presente');
});
test('chamada vazia ou status inválido não apaga dados',async()=>{
 const {ctx,rows}=preparar();await assert.rejects(ctx.salvarChamada('2026-10-31',[]));await assert.rejects(ctx.salvarChamada('2026-10-31',[{aluna:'A',status:'Outro'}]));assert.equal(rows.length,1);
});
