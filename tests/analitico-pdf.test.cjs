const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ctx={window:{}};vm.createContext(ctx);
vm.runInContext(fs.readFileSync(require.resolve('../js/analitico-pdf.js'),'utf8'),ctx);
const api=ctx.window.AnaliticoPDF;
class PDF {
 constructor(){this.pages=[[]];this.p=0;}
 setFont(){} setFontSize(){} setTextColor(){} setDrawColor(){} setFillColor(){} rect(){} line(){} circle(){}
 splitTextToSize(s){return s.match(/.{1,75}/g)||[''];}
 text(s,x,y){this.pages[this.p].push({s,y});}
 addPage(){this.pages.push([]);this.p++;} setPage(n){this.p=n-1;} getNumberOfPages(){return this.pages.length;}
}
test('relatório longo preserva informações e conclusão, sem cortar texto',()=>{
 const pdf=api.gerar({gem:'GEM Teste',filtros:'Solfejo Melódico - outubro',blocos:Array.from({length:80},(_,i)=>({titulo:`Registro ${i}`,texto:'Conteúdo e observação pedagógica. '.repeat(10)})),conclusao:'CONCLUSAO FINAL'},PDF);
 assert.ok(pdf.pages.length>3);
 const texto=pdf.pages.flat().map(l=>l.s).join(' ');
 assert.ok(texto.includes('Registro 79'));assert.ok(texto.includes('CONCLUSAO FINAL'));
 assert.ok(pdf.pages.flat().every(l=>l.y<=289 && l.y>=16));
});
test('conclusão não inventa progresso, separa disciplinas e não transforma ausência de dados em diagnóstico',()=>{
 assert.match(api.conclusao([],'prontuario'),/Não há registros/);
 const resultado=api.conclusao([{Tipo:'Analise_Solfejo',Dificuldades:['Leitura rítmica']},{Tipo:'Analise_Solfejo Melódico',Dificuldades:['Afinação']},{Tipo:'Chamada',Aluna:'A',Data:'10/10/2026',Status:'Justificada'}],'quadro');
 assert.match(resultado,/Solfejo: Leitura/);assert.match(resultado,/Solfejo Melódico: Afinação/);
 assert.match(resultado,/incluindo justificadas/);assert.match(resultado,/resumo é coletivo/);
 assert.match(api.conclusao([],'boletim'),/Isoladamente/);
});
