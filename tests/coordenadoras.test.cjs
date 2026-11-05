const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync(require.resolve('../js/gem-data.js'),'utf8');
function preparar(){
 const registros=[{id:1,professora:'Ana',inicio:'2026-11-01',fim:'2026-12-31'}];
 const ctx={normalizar:n=>String(n).trim().toUpperCase(),dadosCoordenacoesProfessoras:async()=>registros,obterCliente:async()=>({from:()=>({insert:r=>({select:async()=>{const row={...r,id:registros.length+1};registros.push(row);return {data:[row]};}})})})};
 vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('  async function definirCoordenadoraProfessora('),src.indexOf('  async function salvarPessoa(')),ctx);return {ctx,registros};
}
test('acrescenta coordenadora no mesmo período preservando a anterior e o acesso de ambas',async()=>{
 const {ctx,registros}=preparar();const anterior=JSON.stringify(registros[0]);
 await ctx.definirCoordenadoraProfessora({professora:'Bia',inicio:'2026-11-01',fim:'2026-12-31',periodo:'Bimestre'});
 assert.equal(registros.length,2);assert.equal(JSON.stringify(registros[0]),anterior);
 assert.equal(await ctx.professoraEhCoordenadora('Ana','2026-11-05'),true);assert.equal(await ctx.professoraEhCoordenadora('Bia','2026-11-05'),true);
 assert.equal(await ctx.professoraEhCoordenadora('Bia','2027-01-01'),false);
});
test('impede sobreposição da mesma professora e permite período posterior',async()=>{
 const {ctx,registros}=preparar();
 await assert.rejects(ctx.definirCoordenadoraProfessora({professora:' ana ',inicio:'2026-12-01',fim:'2027-01-01'}),/já possui/);
 assert.equal(registros.length,1);
 await ctx.definirCoordenadoraProfessora({professora:'Ana',inicio:'2027-01-01',fim:'2027-02-28'});assert.equal(registros.length,2);
});
