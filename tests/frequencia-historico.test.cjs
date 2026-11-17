const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const s=fs.readFileSync(require.resolve('../js/gem-data.js'),'utf8'),ctx={};vm.createContext(ctx);vm.runInContext(s.slice(s.indexOf('  function consolidarChamadas('),s.indexOf('  const configLocal')),ctx);
test('uma chamada por aluna e dia, independente da ordem e formato da data, preservando demais registros',()=>{
 const rs=[{id:10,Aluna:'Ana',Data:'2026-11-07',Tipo:'Chamada',Status:'Falta justificada'},{id:2,Aluna:'Ana',Data:'07/11/2026',Tipo:'Chamada',Status:'Presente'},{id:3,Aluna:'Bia',Data:'07/11/2026',Tipo:'Chamada',Status:'falta'},{id:4,Aluna:'Ana',Data:'07/11/2026',Tipo:'Analise_Prática'}];
 const antes=JSON.stringify(rs);for(const dados of [rs,[...rs].reverse()]){const r=ctx.consolidarChamadas(dados);assert.equal(r.length,3);assert.equal(r.find(x=>x.id===10).Status,'Justificada');assert.equal(r.find(x=>x.id===3).Status,'Ausente');assert.ok(r.some(x=>x.id===4));}assert.equal(JSON.stringify(rs),antes);
});
test('histórico da aluna lê todas as páginas e propaga erro sem retornar totais parciais',async()=>{
 const itens=Array.from({length:1101},(_,id)=>({id}));let falha=false;
 const banco={from(){const q={select(){return q},eq(){return q},order(){return q},async range(a,b){return falha&&a===500?{error:{message:'erro'}}:{data:itens.slice(a,b+1)}}};return q}};
 assert.equal((await ctx.lerHistoricoCompleto(banco,'Ana')).data.length,1101);falha=true;assert.equal((await ctx.lerHistoricoCompleto(banco,'Ana')).data,null);
});
