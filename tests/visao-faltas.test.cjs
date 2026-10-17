const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const fonte = fs.readFileSync(require.resolve('../app.js'), 'utf8');
const ctx = {}; vm.createContext(ctx);
vm.runInContext(fonte.slice(fonte.indexOf('function resumoFaltasVisaoGeral('), fonte.indexOf('function eResolvida(')), ctx);
test('faltas somam ausências e justificadas uma vez por aluna e dia', () => {
  const chamada = (id, Aluna, Status, Data = '17/10/2026') => ({ id, Aluna, Status, Data, Tipo: 'Chamada' });
  const r = ctx.resumoFaltasVisaoGeral([
    chamada(1, 'Ana', 'Ausente'), chamada(2, 'Ana', 'Justificada'),
    chamada(3, 'Bia', 'Ausente'), chamada(4, 'Clara', 'Ausente'), chamada(5, 'Clara', 'Presente'),
    chamada(6, 'Ana', 'Ausente', '10/10/2026'),
    { ...chamada(7, 'Bia', 'Ausente'), Tipo: 'Analise_Pratica' }
  ]);
  assert.equal(r.total, 3); assert.equal(r.justificadas, 1); assert.equal(r.ausentes, 2);
});
test('histórico vazio apresenta zero faltas', () => {
  assert.equal(ctx.resumoFaltasVisaoGeral([]).total, 0);
});
