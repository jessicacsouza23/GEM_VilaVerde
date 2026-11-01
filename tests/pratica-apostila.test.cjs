const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const src = fs.readFileSync(require.resolve('../js/gem-data.js'), 'utf8');
function validar(materiais) {
  const inicio = src.indexOf('  async function salvarRegistrosPratica(');
  const fim = src.indexOf('    const banco = await obterCliente();', inicio);
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(src.slice(inicio, fim) + '\n}', ctx);
  return ctx.salvarRegistrosPratica({ materiais });
}
test('apostila exige página e lições antes de acessar o banco, mesmo com outro material válido', async () => {
  for (const conteudo of ['', 'lição 2', '18', 'página 18', 'página 18, lições']) {
    await assert.rejects(validar([{ material: 'Volume 1', conteudo: 'lição 1' }, { material: 'Apostila', conteudo }]), /Informe/);
  }
});
test('aceita página com lições, exercícios e exercícios detalhados', async () => {
  for (const conteudo of ['Página 18, lições 1 e 2', 'Pág. 20, exercício 4', 'Páginas 25 e 30, atividades de ritmo']) {
    await validar([{ material: 'Apostila', conteudo }]);
  }
  await validar([{ material: 'Apostila', conteudo: 'p. 18', exercicios: [{ exercicio: '1' }] }]);
});
test('outros métodos não passam a exigir página', async () => {
  await validar([{ material: 'Volume 1', conteudo: 'lição 4' }]);
});
