const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(require.resolve('../js/rodizio-engine.js'), 'utf8'), ctx);
const engine = ctx.window.RodizioEngine;
function entrada(quantidade = 7) {
  return { data: '17/10/2026', professoras: ['Ana', 'Bia'], turmasReais: { 'Turma 1': Array.from({length: quantidade}, (_, i) => `Aluna ${i}`) }, modelo: {configuracao: {
    blocos: [{inicio: '08:00', fim: '08:45'}],
    salas: Array.from({length: 7}, (_, i) => ({Sala: `SALA ${i+1}`, Uso:'Individual'})),
    atividades: [{Atividade: 'Prática', Formato: 'Individual', 'Duração (min)': 45}],
    turmas: [{Turma: 'Turma 1'}], professoras_habilitadas: {'Prática': ['Ana', 'Bia']}
  }}};
}
const extras = escala => escala.flatMap(l => Object.values(l._detalhes)).filter(d => d.atividade_secretaria);
test('cinco sem professora seguem para Secretaria sem perder as duas aulas disponíveis', () => {
  const r = engine.gerar(entrada());
  assert.equal(r.erros.length, 0, r.erros.join('\n'));
  assert.equal(r.escala.length, 7); assert.equal(extras(r.escala).length, 5);
  assert.ok(extras(r.escala).every(d => d.responsavel_papel === 'Secretaria' && d.turma === 'Turma 1'));
});
test('só gera complementares quando há falta de professoras', () => {
  assert.equal(extras(engine.gerar(entrada(2)).escala).length, 0);
  const r = engine.gerar({...entrada(), folgas: ['Ana', 'Bia']});
  assert.equal(r.erros.length, 0); assert.equal(extras(r.escala).length, 7);
});
test('edição preserva turma e direcionamento, inclusive após regenerar e serializar', () => {
  const r = engine.gerar(entrada());
  const i = r.escala.findIndex(l => extras([l]).length);
  const hora = Object.keys(r.escala[i]._detalhes)[0];
  engine.editarAtividadeComplementar(r.escala, i, hora, {atividade:'Leitura em dupla', sala:'SALA 1', papel:'Professora', responsavel:'Ana'});
  const salva = JSON.parse(JSON.stringify(r.escala));
  const nova = engine.gerar(entrada()).escala;
  engine.preservarAtividadesComplementares(nova, salva);
  assert.equal(nova[i][hora], 'SALA 1 | Ana');
  assert.equal(nova[i]._detalhes[hora].tipo, 'Leitura em dupla');
  assert.equal(nova[i]._detalhes[hora].turma, 'Turma 1');
  assert.notEqual(nova[i]._detalhes[hora], salva[i]._detalhes[hora]);
  assert.throws(() => engine.editarAtividadeComplementar(nova, i, hora, {atividade:'', sala:'Sala', papel:'Secretaria'}));
});
test('agenda encaminha somente à professora escolhida, permitindo atendimento compartilhado', async () => {
  const escala = ['Ana', 'Ana Paula', 'Ana'].map((nome, i) => ({Aluna:`Aluna ${i}`, h:`SALA 1 | ${nome}`, _detalhes:{h:{atividade_secretaria:true, tipo:'Leitura', sala:'SALA 1', responsavel:nome, responsavel_papel:i === 2 ? 'Secretaria':'Professora'}}}));
  escala.push({Aluna:'Regular', h:'SALA 1 | Ana', _detalhes:{h:{individual:true, tipo:'Prática'}}});
  const source = fs.readFileSync(require.resolve('../js/gem-data.js'), 'utf8');
  const start = source.indexOf('  async function agendaProfessora(');
  const end = source.indexOf('  async function salvarRegistroAula(', start);
  const sandbox = {window:{}, normalizar:s => String(s).toUpperCase(), dataBr:s=>s, tipoDaAula:(_,d)=>d.tipo,
    obterCliente: async () => ({from: table => ({select: () => table === 'calendario' ? {eq:()=>({maybeSingle:async()=>({data:{escala}})})} : Promise.resolve({data:[]})})})};
  vm.createContext(sandbox); vm.runInContext(source.slice(start,end), sandbox);
  const agenda = await sandbox.agendaProfessora('Ana', '2026-10-17');
  assert.equal(agenda.length, 2);
  assert.deepEqual(Array.from(agenda, a=>a.alunas[0]), ['Aluna 0','Regular']);
});
