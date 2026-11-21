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
 const itens=ctx.window.GemMateriais.catalogo(h);const volume=itens.find(item=>item.nome==='Volume 1');assert.equal(volume.concluido,true);assert.equal(volume.nome,'Volume 1');
 h.push({id:5,Tipo:'Material_Prática',Licao_Atual:'Volume 1',Status:'Em andamento'});assert.equal(ctx.window.GemMateriais.catalogo(h).find(item=>item.nome==='Volume 1').concluido,false);
});
test('somente materiais vinculados à aluna viram opções, nunca lições ou análises',()=>{
 const h=[
  {id:1,Tipo:'Analise_Prática',Licao_Atual:'Exercício 5 e 6'},
  {id:2,Tipo:'Analise_Prática',Licao_Atual:'17'},
  {id:3,Tipo:'Analise_Prática',Licao_Atual:'Páginas 10 e 11 corrigidas'},
  {id:4,Tipo:'Analise_Prática',Licao_Atual:'Volume 1: exercícios 5 e 6'},
  {id:5,Tipo:'Casa_Metodo_Meu Piano é Divertido 1'},
  {id:6,Tipo:'Material_Prática',Licao_Atual:'Volume 1',Status:'Em andamento'}
 ];
 const nomes=Array.from(ctx.window.GemMateriais.catalogo(h),item=>item.nome);
 assert.deepEqual(nomes,['Volume 1','Meu piano é divertido 1']);
});
test('recupera materiais legítimos do histórico anterior ao vínculo Material_Prática',()=>{
 const h=[
  {id:1,Tipo:'Analise_Prática',Licao_Atual:'Meu Piano é Divertido: lição 8'},
  {id:2,Tipo:'Casa_Metodo_Volume 1',Licao_Casa:'lição 3'},
  {id:3,Tipo:'Analise_Prática',Licao_Atual:'Páginas 10 e 11 corrigidas'}
 ];
 const nomes=Array.from(ctx.window.GemMateriais.catalogo(h,['Meu piano é divertido 1','Volume 1']),item=>item.nome);
 assert.deepEqual(nomes,['Meu piano é divertido 1','Volume 1']);
});
