const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../app.js'), 'utf8');
const ctx = {}; vm.createContext(ctx); vm.runInContext(source.slice(0, source.indexOf('const navByRole')), ctx);
const casa = (Tipo, Aluna = 'A', Licao_Casa = 'Página 12') => ({Tipo, Aluna, Licao_Casa, Status:'Pendente'});
test('sugere lição correspondente nas quatro disciplinas sem misturar métodos', () => {
  for (const [disciplina,material,tipo] of [['Prática','Volume 1','Casa_Metodo_Volume 1'],['Prática','Apostila','Casa_Apostila'],['Teoria','Apostila','Casa_Apostila_Teoria_Prof'],['Teoria','Folha avulsa','Casa_Teoria'],['Solfejo','MSA','Casa_MSA'],['Solfejo Melódico','Canto','Casa_Canto']]) {
    assert.equal(ctx.sugerirConteudoPendente([casa(tipo)],disciplina,material,['A']), 'Página 12');
    assert.equal(ctx.sugerirConteudoPendente([casa(tipo)],disciplina,'Outro método',['A']), '');
  }
});
test('lição resolvida mais recente não ressuscita pendência antiga', () => {
  assert.equal(ctx.sugerirConteudoPendente([{...casa('Casa_MSA'),Status:'Resolvido'},casa('Casa_MSA')],'Solfejo','MSA',['A']), '');
});
test('turma só preenche referência comum entre todas as selecionadas', () => {
  const h = [casa('Casa_MSA'),casa('Casa_MSA','B','Página 20')];
  assert.equal(ctx.sugerirConteudoPendente(h,'Solfejo','MSA',['A','B']), '');
  assert.equal(ctx.sugerirConteudoPendente(h,'Solfejo','MSA',['B']), 'Página 20');
  assert.equal(ctx.sugerirConteudoPendente(h,'Solfejo','MSA',['C']), '');
});
test('material livre corresponde ao material da última aula', () => {
  assert.equal(ctx.sugerirConteudoPendente([casa('Casa_Canto'),{Aluna:'A',Tipo:'Analise_Solfejo Melódico',Licao_Atual:'Bona: exercício 1'}],'Solfejo Melódico','Bona',['A']), 'Página 12');
});
function campo(value = '') { return {value, handlers:{},addEventListener(e,f){this.handlers[e]=f;}}; }
test('última aula sem lição impede recuperar tarefa antiga em cada disciplina', () => {
  for (const [disciplina,material,tipo] of [['Solfejo Melódico','Canto','Casa_Canto'],['Solfejo','MSA','Casa_MSA'],['Teoria','Apostila','Casa_Apostila_Teoria'],['Prática','Volume 1','Casa_Metodo_Volume 1']]) {
    const aula = {Aluna:'A',Tipo:`Analise_${disciplina}`,Data:'03/10/2026',Licao_Atual:`${material}: 437`};
    const antiga = {...casa(tipo),Data:'26/09/2026'};
    assert.equal(ctx.sugerirConteudoPendente([aula,antiga],disciplina,material,['A']), '');
    const nova = {...casa(tipo),Data:'2026-10-03'};
    assert.equal(ctx.sugerirConteudoPendente([nova,aula,antiga],disciplina,material,['A']), 'Página 12');
    assert.equal(ctx.sugerirConteudoPendente([{...nova,Licao_Casa:''},aula,antiga],disciplina,material,['A']), '');
  }
});
test('aula de outra disciplina não invalida tarefa e virada de ano respeita datas', () => {
  const antiga = {...casa('Casa_Canto'),Data:'31/12/2025'};
  const aula = {Aluna:'A',Tipo:'Analise_Solfejo',Data:'01/01/2026',Licao_Atual:'MSA: 1'};
  assert.equal(ctx.sugerirConteudoPendente([aula,antiga],'Solfejo Melódico','Canto',['A']), 'Página 12');
  aula.Tipo = 'Analise_Solfejo Melódico';
  assert.equal(ctx.sugerirConteudoPendente([aula,antiga],'Solfejo Melódico','Canto',['A']), '');
});
test('atualiza sugestão ao trocar método e preserva conteúdo digitado ou salvo', () => {
  const m = campo('A'), c = campo();
  ctx.conectarSugestaoConteudo(m,c,v => `Lição ${v}`);
  assert.equal(c.value,'Lição A'); m.value='B'; m.handlers.change(); assert.equal(c.value,'Lição B');
  c.value='Minha adaptação'; c.handlers.input(); m.value='C'; m.handlers.change(); assert.equal(c.value,'Minha adaptação');
  const salvo = campo('Registro salvo'); ctx.conectarSugestaoConteudo(m,salvo,()=> 'Outra'); assert.equal(salvo.value,'Registro salvo');
});
