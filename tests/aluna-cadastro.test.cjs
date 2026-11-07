const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync(require.resolve('../js/gem-data.js'),'utf8');
function ambiente(error){
 let enviado, filtro;
 const query={eq(k,v){filtro=[k,v];return query;},then(resolve){return Promise.resolve({error}).then(resolve);}};
 const ctx={obterCliente:async()=>({from:()=>({insert(d){enviado=d;return query;},update(d){enviado=d;return query;}})})};
 vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('  async function salvarPessoa('),src.indexOf('  async function enviarFotoPessoa(')),ctx);
 return {salvar:ctx.salvarPessoa,get:()=>({enviado,filtro})};
}
test('cadastro e edição preservam comum e data tanto com id quanto com nome legado',async()=>{
 const a=ambiente();await a.salvar('aluna',{nome:'A',comum:' Vila Verde ',data_inicio:'2026-11-07'});
 assert.equal(a.get().enviado.comum,'Vila Verde');assert.equal(a.get().enviado.data_inicio,'2026-11-07');
 await a.salvar('aluna',{comum:'Nova comum',data_inicio:''},null,'A');assert.equal(a.get().enviado.data_inicio,null);assert.equal(a.get().filtro[0],'nome');
 await a.salvar('aluna',{comum:'',data_inicio:'2024-02-29'},'uuid');assert.equal(a.get().enviado.comum,null);assert.equal(a.get().filtro[0],'id');
});
test('data inválida e migration ausente têm mensagens claras e não silenciam os campos',async()=>{
 const a=ambiente();await assert.rejects(a.salvar('aluna',{data_inicio:'2026-02-30'}),/data de início válida/);assert.equal(a.get().enviado,undefined);
 await assert.rejects(ambiente({code:'PGRST204',message:'comum missing'}).salvar('aluna',{comum:'Vila Verde'}),/migration 014/);
});
