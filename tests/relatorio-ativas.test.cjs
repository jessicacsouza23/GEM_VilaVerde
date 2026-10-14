const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const fonte = fs.readFileSync(require.resolve('../js/gem-data.js'), 'utf8');
const funcao = fonte.slice(fonte.indexOf('  async function dadosVisaoGeral('), fonte.indexOf('  async function dadosPessoas('));
function ambiente(falhar = false) {
  const consultasHistorico = [];
  const ctx = { dataBr: () => '10/10/2026', normalizar: v => String(v || '').trim().toUpperCase(), obterCliente: async () => ({
    from(tabela) {
      let nomes, inicio;
      const query = {
        select() { return this; }, eq() { return this; }, order() { return this; }, maybeSingle() { return this; },
        in(campo, lista) { nomes = lista; consultasHistorico.push(Array.from(lista)); return this; },
        range(a) { inicio = a; return this; },
        then(resolve) {
          if (tabela === 'alunas') return Promise.resolve({ data: [{ nome: 'Ana' }], error: falhar ? {} : null }).then(resolve);
          if (tabela === 'calendario') return Promise.resolve({ data: { escala: [{ Aluna: 'Ana' }, { Aluna: 'Bia' }] } }).then(resolve);
          if (tabela === 'estudo_diario') return Promise.resolve({ data: [{ aluna: 'Ana' }, { aluna: 'Bia' }] }).then(resolve);
          const data = nomes ? nomes.map(Aluna => ({ Aluna, Tipo: 'Analise_Pratica' })) : [
            { Aluna: 'Ana', Tipo: 'Chamada', Status: 'Ausente' }, { Aluna: 'Ana', Tipo: 'Analise_Pratica' },
            { Aluna: 'Bia', Tipo: 'Chamada', Status: 'Justificada' }, { Aluna: 'Bia', Tipo: 'Analise_Pratica' }
          ];
          return Promise.resolve({ data }).then(resolve);
        }
      };
      return query;
    }
  }) };
  vm.createContext(ctx); vm.runInContext(funcao, ctx);
  return { carregar: ctx.dadosVisaoGeral, consultasHistorico };
}
test('relatório exclui desativada de escala, registros, totais e busca de pendências', async () => {
  const { carregar, consultasHistorico } = ambiente();
  const r = await carregar('2026-10-10', { incluirHistoricoAusentes: true, excluirDesativadas: true });
  assert.deepEqual(Array.from(r.alunas), ['Bia']);
  for (const campo of ['escala', 'registros', 'ausentes', 'analises', 'historicoComplementar']) assert.ok(r[campo].every(i => i.Aluna === 'Bia'));
  assert.equal(r.ausentes.length, 1);
  assert.equal(r.analises.length, 1);
  assert.deepEqual(consultasHistorico, [['Bia']]);
  assert.ok(r.estudos.every(i => i.aluna === 'Bia'));
});
test('outros consumidores da visão geral mantêm comportamento anterior', async () => {
  const r = await ambiente().carregar('2026-10-10');
  assert.equal(r.alunas.length, 2);
});
test('erro no cadastro não permite exportar desativadas silenciosamente', async () => {
  await assert.rejects(ambiente(true).carregar('2026-10-10', { excluirDesativadas: true }), /desativadas/);
});
