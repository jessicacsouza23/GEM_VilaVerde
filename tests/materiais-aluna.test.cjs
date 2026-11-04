const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(require.resolve('../js/materiais-aluna.js'),'utf8'),ctx);
test('nomes antigos de Meu Piano se agrupam no volume 1, sem misturar volume 2',()=>{
 const h=[{id:1,Tipo:'Analise_Prática',Licao_Atual:'Meu Piano é Divertido: 12'},{id:2,Tipo:'Casa_Metodo_Meu piano é divertido 1'},{id:3,Tipo:'Material_Prática',Licao_Atual:'Meu Piano é Divertido',Status:'Concluído'}];
 const itens=ctx.window.GemMateriais.catalogo(h);assert.equal(itens.length,1);assert.equal(itens[0].nome,'Meu piano é divertido 1');assert.equal(itens[0].concluido,true);
 assert.equal(ctx.window.GemMateriais.nomeMaterial('Meu piano é divertido 2'),'Meu piano é divertido 2');
 assert.equal(ctx.window.GemMateriais.normalizarRegistro(h[0]).Licao_Atual,'Meu piano é divertido 1: 12');
 assert.equal(h[0].Licao_Atual,'Meu Piano é Divertido: 12');
});
test('materiais concluídos não são reativados por análise e podem ser retomados explicitamente',()=>{
 const h=[{id:1,Tipo:'Analise_Prática',Licao_Atual:'Volume 1: lição 2'},{id:2,Tipo:'Material_Prática',Licao_Atual:'Volume 1',Status:'Concluído',Data:'03/11/2026',Instrutora:'Professora'},{id:3,Tipo:'Analise_Prática',Licao_Atual:'Volume 1: última lição'},{id:4,Tipo:'Casa_Metodo_Meu Piano é Divertido'}];
 const itens=ctx.window.GemMateriais.catalogo(h);assert.equal(itens.length,2);assert.equal(itens[0].concluido,true);assert.equal(itens[1].nome,'Meu piano é divertido 1');
 h.push({id:5,Tipo:'Material_Prática',Licao_Atual:'Volume 1',Status:'Em andamento'});assert.equal(ctx.window.GemMateriais.catalogo(h)[0].concluido,false);
});
