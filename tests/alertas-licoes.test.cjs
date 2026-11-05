const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const ctx={window:{}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(require.resolve('../js/alertas-licoes.js'),'utf8'),ctx);
const filtro={inicio:'2026-10-01',fim:'2026-10-31',alunas:['A']};
function aula(dia,licao='MSA: 12',tipo='Analise_Solfejo',presenca='Presente') {return [{id:dia*10,Aluna:'A',Data:`${String(dia).padStart(2,'0')}/10/2026`,Tipo:'Chamada',Status:presenca},{id:dia*10+1,Aluna:'A',Data:`${String(dia).padStart(2,'0')}/10/2026`,Tipo:tipo,Licao_Atual:licao,Status:'Realizada - com dificuldades',Dificuldades:['Dificuldade rítmica']}];}
const calc=h=>ctx.window.AlertasLicoes.calcular(h,filtro);
test('alerta em três sábados distintos e traz começo real, mesmo anterior ao filtro',()=>{
 const h=[...aula(3),...aula(10),...aula(17)];h.push({...h[5],id:999});
 const r=calc(h);assert.equal(r.length,1);assert.equal(r[0].sabados,3);assert.equal(r[0].inicio,'2026-10-03');assert.equal(r[0].licao,'12');
 assert.equal(ctx.window.AlertasLicoes.calcular(h,{...filtro,inicio:'2026-10-17'})[0].inicio,'2026-10-03');
 assert.equal(calc(h.slice(0,4)).length,0);
});
test('não conta faltas, justificativas, dias sem chamada ou fora do sábado',()=>{
 const h=[...aula(3),...aula(10,'MSA: 12','Analise_Solfejo','Justificada'),...aula(17,'MSA: 12','Analise_Solfejo','Ausente'),...aula(24),...aula(25),aula(31)[1]];
 assert.equal(calc(h).length,0);
});
test('nova lição e conclusão encerram o alerta sem misturar materiais ou disciplinas',()=>{
 const h=[...aula(3),...aula(10),...aula(17)];
 assert.equal(calc([...h,...aula(24,'MSA: 13')]).length,0);
 for(const patch of [{Status:'Realizada - sem pendência'},{Dificuldades:['Não apresentou dificuldades']},{Observacao:'Correção da lição: Resolvido — 12'}]){
  const nova=aula(24);Object.assign(nova[1],patch);assert.equal(calc([...h,...nova]).length,0);
 }
 assert.equal(calc([...aula(3),...aula(10,'MSA: 12','Analise_Solfejo Melódico'),...aula(17)]).length,0);
 assert.equal(calc([...aula(3),...aula(10,'Outro: 12'),...aula(17)]).length,0);
});
test('mantém separadas as alunas e respeita última correção da chamada',()=>{
 const h=[...aula(3),...aula(10),...aula(17)];
 h.push({id:999,Aluna:'A',Tipo:'Chamada',Data:'17/10/2026',Status:'Justificada'});
 assert.equal(calc(h).length,0);
 assert.equal(ctx.window.AlertasLicoes.calcular([...aula(3),...aula(10),...aula(17)],{...filtro,alunas:['B']}).length,0);
});
