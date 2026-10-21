const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const fonte = fs.readFileSync(require.resolve('../js/gem-data.js'), 'utf8');
const funcao = fonte.slice(fonte.indexOf('  async function dadosRodizio('), fonte.indexOf('  async function dadosFolgas('));
function ambiente(falhar = false) {
  const paginas = [];
  const ctx = { dataBr: () => '24/10/2026', obterCliente: async () => ({ from(tabela) {
    let inicio, fim, unico = false;
    return {
      select() { return this; }, order() { return this; }, eq() { return this; },
      maybeSingle() { unico = true; return this; },
      range(a, b) { inicio = a; fim = b; paginas.push([a, b]); return this; },
      then(resolve) {
        if (tabela === 'calendario' && !unico) {
          if (falhar) return Promise.resolve({ error: { message: 'Falha simulada' } }).then(resolve);
          return Promise.resolve({ data: Array.from({ length: 1203 }, (_, id) => ({ id, escala: [] })).slice(inicio, fim + 1) }).then(resolve);
        }
        return Promise.resolve({ data: unico ? null : [] }).then(resolve);
      }
    };
  } }) };
  vm.createContext(ctx); vm.runInContext(funcao, ctx);
  return { carregar: ctx.dadosRodizio, paginas };
}
test('histórico de rodízios é carregado em todas as páginas', async () => {
  const { carregar, paginas } = ambiente();
  const r = await carregar('2026-10-24');
  assert.equal(r.escalasAnteriores.length, 1203);
  assert.deepEqual(paginas, [[0, 499], [500, 999], [1000, 1499]]);
});
test('erro do histórico não gera escala fingindo não haver sábados anteriores', async () => {
  await assert.rejects(ambiente(true).carregar('2026-10-24'), /histórico de rodízios/);
});
