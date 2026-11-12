const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../app.js'),'utf8');
const start=source.indexOf('function muralRodizio(');
const end=source.indexOf('\nfunction ',start+1);
const ctx={state:{gem:'Teste'},escapeHtml:s=>String(s)};
vm.createContext(ctx);vm.runInContext(source.slice(start,end),ctx);
test('professora atribuída aparece no horário normal, inclusive junto com outra aluna',()=>{
 const hora='10:30 - 11:15 (Aula 3)';
 const escala=[{Aluna:'Emilly',[hora]:'SALA 4 | Patrícia',_detalhes:{[hora]:{atividade_secretaria:true,responsavel_papel:'Professora',responsavel:'Patrícia',tipo:'Prática',turma:'Turma 1',sala:'SALA 4'}}},{Aluna:'Outra aluna',[hora]:'SALA 4 | Patrícia',_detalhes:{[hora]:{individual:true,turma:'Turma 1'}}}];
 const antes=JSON.stringify(escala),html=ctx.muralRodizio(escala,'14/11/2026');
 assert.ok(html.includes('Emilly + Outra aluna'));
 assert.ok(html.includes(hora));
 assert.ok(!html.includes('Atividades complementares'));
 assert.equal(JSON.stringify(escala),antes);
});
test('atendimento da secretaria continua no quadro separado',()=>{
 const html=ctx.muralRodizio([{Aluna:'Aluna',h:'Local | Secretarias',_detalhes:{h:{atividade_secretaria:true,responsavel_papel:'Secretaria',tipo:'Atividade'}}}],'14/11/2026');
 assert.ok(html.includes('Atividades complementares'));
});
