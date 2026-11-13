const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(require.resolve('../js/proximas-aulas.js'),'utf8'),ctx);const api=ctx.window.ProximasAulas;
test('semana aponta para sábado e mantém escala até meia-noite de São Paulo',()=>{
 assert.equal(api.sabado(new Date('2026-11-12T15:00:00Z')),'2026-11-14');
 assert.equal(api.sabado(new Date('2026-11-15T02:59:59Z')),'2026-11-14');
 assert.equal(api.sabado(new Date('2026-11-15T03:00:00Z')),'2026-11-21');
});
const h1='08:50 - 09:35 (Aula 1)',h2='09:40 - 10:25 (Aula 2)';
const escala=['A','B'].map(Aluna=>({Aluna,[h1]:'SALA 1 | Solfejo: Ana · Prática: Ana Paula',[h2]:'SALA 8 | Ana',_detalhes:{[h1]:{tipo:'Prática + Solfejo',componentes:['Solfejo','Prática'],professoras_componentes:{Solfejo:'Ana','Prática':'Ana Paula'},horarios_componentes:{Solfejo:'08:50 - 09:05',Prática:'09:05 - 09:35'}},[h2]:{tipo:'Teoria'}}}));
test('aluna vê apenas suas aulas, com disciplina, professora e horário específico',()=>{const a=api.aulas(escala,{nome:'A',papel:'Aluna'});assert.equal(a.length,3);assert.equal(a[1].responsavel,'Ana Paula');assert.equal(a[1].horario,'09:05 - 09:35');assert.ok(a.every(i=>i.alunas.length===1&&i.alunas[0]==='A'));assert.equal(a[2].numero,2);});
test('professora não recebe aulas de homônima parcial e coletiva reúne alunas',()=>{const a=api.aulas(escala,{nome:'Ana',papel:'Professora'});assert.equal(a.length,2);assert.equal(a[1].alunas.length,2);assert.ok(a.every(i=>i.disciplina!=='Prática'));});
test('encaminhamento editado vai somente para a professora escolhida',()=>{const e=[{Aluna:'A',[h1]:'SALA 4 | Bia',_detalhes:{[h1]:{atividade_secretaria:true,tipo:'Prática',responsavel_papel:'Professora',responsavel:'Bia',sala:'SALA 4'}}}];assert.equal(api.aulas(e,{nome:'Bia',papel:'Professora'}).length,1);e[0]._detalhes[h1].responsavel_papel='Secretaria';assert.equal(api.aulas(e,{nome:'Bia',papel:'Professora'}).length,0);assert.equal(api.aulas(e,{nome:'A',papel:'Aluna'}).length,1);});
