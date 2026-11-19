const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');const c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync(require.resolve('../js/grafico-turmas.js'),'utf8'),c);const api=c.window.GraficoTurmas;
test('média simples por aluna, sem misturar disciplinas ou incluir inativas e registros fora da janela',()=>{
 const alunas=[{nome:'Ana',turma:'Turma 1'},{nome:'Bia',turma:'Turma 1'},{nome:'Sem dados',turma:'Turma 2'},{nome:'Inativa',turma:'Turma 1',ativo:false}];
 const r=(Aluna,Dificuldades,Tipo='Analise_Solfejo',Data='19/11/2026')=>({Aluna,Dificuldades,Tipo,Data});
 const h=[r('Ana',['Não apresentou dificuldades']),r('Ana',['Ritmo']),r('Bia',['Não apresentou dificuldades']),r('Inativa',['Ritmo']),r('Bia',['Ritmo'],'Analise_Solfejo','01/01/2026'),r('Ana',['Não apresentou dificuldades','Ritmo'],'Analise_Canto')];
 const d=api.calcular(alunas,h,'2026-11-19');assert.equal(d.inicio,'2026-10-21');assert.equal(d.disciplinas.find(x=>x.disciplina==='Solfejo').valores[0].percentual,75);assert.equal(d.disciplinas.find(x=>x.disciplina==='Solfejo Melódico').valores[0].percentual,0);assert.equal(d.disciplinas[0].valores[1].percentual,null);
});
test('campo vazio não é positivo e marcação JSON é reconhecida',()=>{
 const d=api.calcular([{nome:'Ana',turma:'1'}],[{Aluna:'Ana',Tipo:'Analise_Prática',Data:'2026-11-19',Dificuldades:[]},{Aluna:'Ana',Tipo:'Analise_Prática',Data:'2026-11-19',Dificuldades:'["Não apresentou dificuldades"]'}],'2026-11-19');assert.equal(d.disciplinas.find(x=>x.disciplina==='Prática').valores[0].percentual,50);
});

test('Solfejo histórico e Solfejo Melódico ficam separados, inclusive MSA e maiúsculas',()=>{
 const alunas=[{nome:'Ana',turma:'1'}];
 const h=[
  {Aluna:'Ana',Tipo:'ANALISE_MSA',Data:'2026-11-19',Dificuldades:['Não apresentou dificuldades']},
  {Aluna:'Ana',Tipo:'Analise_Solfejo',Data:'2026-11-19',Dificuldades:['Ritmo']},
  {Aluna:'Ana',Tipo:'Analise_Solfejo Melódico',Data:'2026-11-19',Dificuldades:['Não apresentou dificuldades']}
 ];
 const d=api.calcular(alunas,h,'2026-11-19');
 assert.equal(d.disciplinas.find(x=>x.disciplina==='Solfejo').valores[0].percentual,50);
 assert.equal(d.disciplinas.find(x=>x.disciplina==='Solfejo Melódico').valores[0].percentual,100);
 assert.equal(api.disciplinaDoRegistro('Analise_Solfejo Melódico'),'Solfejo Melódico');
 assert.equal(api.disciplinaDoRegistro('ANALISE_SOLFEJO'),'Solfejo');
});

test('período escolhido inclui as duas datas e rejeita intervalo inválido',()=>{
 const r=Data=>({Aluna:'Ana',Tipo:'Analise_Teoria',Data,Dificuldades:['Não apresentou dificuldades']});
 const d=api.calcular([{nome:'Ana',turma:'1'}],[r('01/01/2025'),r('31/01/2025'),r('01/02/2025')],'2025-01-31','2025-01-01');assert.equal(d.inicio,'2025-01-01');assert.equal(d.disciplinas[0].valores[0].percentual,100);assert.throws(()=>api.calcular([],[],'2025-01-01','2025-01-31'));assert.throws(()=>api.calcular([],[],'',''));assert.throws(()=>api.calcular([],[],'2025-02-30','2025-01-01'));
});
