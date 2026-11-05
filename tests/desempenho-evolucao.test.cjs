const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync(require.resolve('../app.js'),'utf8');
const inicio=src.indexOf('async function renderAnalitico(');
const fonte=src.slice(inicio);
const ctx={};vm.createContext(ctx);
vm.runInContext(fonte.slice(fonte.indexOf('  const dificuldades ='),fonte.indexOf('  const dentroPeriodo ='))+fonte.slice(fonte.indexOf('  const classificacao = (registros)'),fonte.indexOf('  const graficoBarras ='))+'\nthis.classificar=classificacao;',ctx);
test('evolução exige marcação explícita sem dificuldade contraditória',()=>{
 for(const valor of [[],null,'[]',['Dificuldade rítmica'],['Não apresentou dificuldades','Dificuldade rítmica']])assert.equal(ctx.classificar([{Dificuldades:valor}]).evolucao,false);
 for(const valor of [['Não apresentou dificuldades'],'["Não apresentou dificuldades"]']){
  const r=ctx.classificar([{Dificuldades:valor}]);assert.equal(r.evolucao,true);assert.equal(r.nome,'Ouro');assert.equal(r.nota,100);
 }
});
test('mantém critérios das medalhas e reconhece evolução mesmo no bronze',()=>{
 const ruim={Dificuldades:['Dificuldade rítmica']},boa={Dificuldades:['Não apresentou dificuldades']};
 const bronze=ctx.classificar([ruim,ruim,ruim,boa]);assert.equal(bronze.nome,'Bronze');assert.equal(bronze.nota,25);assert.equal(bronze.evolucao,true);
 assert.equal(ctx.classificar([ruim,boa]).nome,'Prata');
 assert.equal(ctx.classificar([ruim]).nota,0);
 assert.equal(ctx.classificar([]).nome,'Sem registros');
});
