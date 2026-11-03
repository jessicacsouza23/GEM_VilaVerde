const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const src = fs.readFileSync(require.resolve('../app.js'), 'utf8');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(src.slice(src.indexOf('function resumoEstudoPeriodo('), src.indexOf('async function renderAnalitico(')), ctx);
test('estudo usa todos os dias do filtro, inclusive início e fim, sem repetir datas', () => {
  const dados = ['01/10/2026', '2026-10-01', '31/10/2026', '01/11/2026'].map(data => ({ data, horarios: ['14:00 às 15:00'] }));
  dados.push({data:'02/10/2026', horarios:[]});
  const r = ctx.resumoEstudoPeriodo(dados, '2026-10-01', '2026-10-31');
  assert.equal(r.dias, 2); assert.equal(r.diasPeriodo, 31); assert.equal(r.percentual, 6);
});
test('um lançamento em trinta dias não representa cem por cento', () => {
  const r = ctx.resumoEstudoPeriodo([{data:'01/11/2026',horarios:['14:00']}], '2026-11-01','2026-11-30');
  assert.equal(r.dias,1); assert.equal(r.diasPeriodo,30); assert.equal(r.percentual,3);
  assert.equal(ctx.resumoEstudoPeriodo([], '2026-11-01','2026-11-30').percentual,0);
  assert.equal(ctx.resumoEstudoPeriodo([{data:'01/11/2026',horarios:['14:00']}], '2026-11-01','2026-11-01').percentual,100);
});
