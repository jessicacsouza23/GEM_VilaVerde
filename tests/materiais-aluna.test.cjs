const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(require.resolve('../js/materiais-aluna.js'),'utf8'),ctx);
test('materiais concluídos não são reativados por análise e podem ser retomados explicitamente',()=>{
 const h=[{id:1,Tipo:'Analise_Prática',Licao_Atual:'Volume 1: lição 2'},{id:2,Tipo:'Material_Prática',Licao_Atual:'Volume 1',Status:'Concluído',Data:'03/11/2026',Instrutora:'Professora'},{id:3,Tipo:'Analise_Prática',Licao_Atual:'Volume 1: última lição'},{id:4,Tipo:'Casa_Metodo_Meu Piano é Divertido'}];
 const itens=ctx.window.GemMateriais.catalogo(h);assert.equal(itens.length,2);assert.equal(itens[0].concluido,true);assert.equal(itens[1].nome,'Meu Piano é Divertido');
 h.push({id:5,Tipo:'Material_Prática',Licao_Atual:'Volume 1',Status:'Em andamento'});assert.equal(ctx.window.GemMateriais.catalogo(h)[0].concluido,false);
});
