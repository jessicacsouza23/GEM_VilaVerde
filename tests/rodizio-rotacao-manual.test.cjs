const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(require.resolve('../js/rodizio-engine.js'),'utf8'),ctx);
const engine=ctx.window.RodizioEngine;
const entrada=()=>({data:'07/11/2026',professoras:['Ana','Bia','Clara'],turmasReais:{T1:['A'],T2:['B'],T3:['C']},modelo:{configuracao:{
 blocos:[{inicio:'08:00',fim:'08:45'},{inicio:'09:00',fim:'09:45'},{inicio:'10:00',fim:'10:45'}],
 salas:[{Sala:'SALA 1',Uso:'Individual'}],turmas:[{Turma:'T1'},{Turma:'T2'},{Turma:'T3'}],
 atividades:[{Atividade:'Teoria',Formato:'Turma','Sala sugerida':'SALA 8'},{Atividade:'Solfejo Melódico',Formato:'Turma','Sala sugerida':'SALA 9'},{Atividade:'Prática',Formato:'Individual','Duração (min)':45}],
 professoras_habilitadas:{Teoria:['Clara'],'Solfejo Melódico':['Bia'],'Prática':['Ana']}
}},rotacaoTurmas:{T1:['__individual__','Solfejo Melódico','Teoria'],T2:['Teoria','__individual__','Solfejo Melódico'],T3:['Solfejo Melódico','Teoria','__individual__']}});
test('geração segue matriz editada, inclusive ciclo inverso à rotação padrão',()=>{
 const e=entrada(),r=engine.gerar(e);assert.equal(r.erros.length,0,r.erros.join('\n'));
 for(const [i,t] of ['T1','T2','T3'].entries()){
  const linha=r.escala.find(l=>l.Aluna===['A','B','C'][i]);
  for(const [b,detalhe] of Object.values(linha._detalhes).entries())assert.equal(detalhe.tipo,e.rotacaoTurmas[t][b]==='__individual__'?'Prática':e.rotacaoTurmas[t][b]);
 }
});
test('matriz inválida não gera escala: conflitos, campos faltantes e atividade omitida',()=>{
 for(const alterar of [e=>e.rotacaoTurmas.T1[0]='Teoria',e=>e.rotacaoTurmas.T1.pop(),e=>{e.rotacaoTurmas={T1:['Teoria','Teoria','Teoria'],T2:['Solfejo Melódico','Solfejo Melódico','Solfejo Melódico'],T3:['__individual__','__individual__','__individual__']};}]){
  const e=entrada();alterar(e);const r=engine.gerar(e);assert.equal(r.escala,null);assert.ok(r.erros.length);
 }
});
