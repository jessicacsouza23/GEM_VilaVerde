const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(require.resolve('../js/rodizio-engine.js'), 'utf8').replace('window.RodizioEngine = {', 'window.RodizioEngine = { atribuirCustos, cicloSalas,'), ctx);
const engine = ctx.window.RodizioEngine;
test('atribuição conjunta evita repetição da última aluna e respeita restrições', () => {
  assert.deepEqual(Array.from(engine.atribuirCustos([[0, 0, 10], [0, 10, 0], [0, 10, 10]])), [1, 2, 0]);
  assert.deepEqual(Array.from(engine.atribuirCustos([[Infinity, 0], [0, Infinity]])), [1, 0]);
  assert.equal(engine.atribuirCustos([[0], [0]]), null);
  assert.equal(engine.atribuirCustos([[Infinity, Infinity]]), null);
});
test('ciclo de salas reinicia após passar por todas', () => {
  assert.deepEqual(Array.from(engine.cicloSalas(['1', '2', '3', '1'], ['1', '2', '3'])), ['1']);
  assert.equal(engine.cicloSalas(['1', '2', '3'], ['1', '2', '3']).size, 0);
});
test('seis sábados completam duas rodas sem travar salas nem repetir professora antes da hora', () => {
  const modelo = { configuracao: {
    blocos: [{ inicio: '08:00', fim: '08:45' }],
    salas: ['1', '2', '3'].map(n => ({ Sala: 'SALA ' + n, Uso: 'Individual' })),
    atividades: [{ Atividade: 'Prática', Formato: 'Individual', 'Duração (min)': 45 }], turmas: [{ Turma: 'Turma 1' }]
  } };
  const historico = [];
  for (const data of ['05/09/2026', '12/09/2026', '19/09/2026', '26/09/2026', '03/10/2026', '10/10/2026']) {
    const antes = JSON.stringify(historico);
    const r = engine.gerar({ modelo, data, turmasReais: { 'Turma 1': ['A', 'B', 'C'] }, professoras: ['P1', 'P2', 'P3'], escalasAnteriores: historico });
    assert.equal(r.erros.length, 0);
    assert.equal(JSON.stringify(historico), antes);
    historico.push({ id: data, escala: r.escala });
  }
  for (const aluna of ['A', 'B', 'C']) {
    const valores = historico.map(d => Object.entries(d.escala.find(l => l.Aluna === aluna)).find(([h]) => h.includes('08:00'))[1].split('|').map(s => s.trim()));
    for (const inicio of [0, 3]) {
      assert.equal(new Set(valores.slice(inicio, inicio + 3).map(v => v[0])).size, 3);
      assert.equal(new Set(valores.slice(inicio, inicio + 3).map(v => v[1])).size, 3);
    }
    for (let i = 1; i < valores.length; i++) {
      assert.notEqual(valores[i][0], valores[i - 1][0]);
      assert.notEqual(valores[i][1], valores[i - 1][1]);
    }
  }
});
