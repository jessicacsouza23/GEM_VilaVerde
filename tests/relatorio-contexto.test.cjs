const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ctx = { window: {} }; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(require.resolve('../js/relatorio-contexto.js'), 'utf8'), ctx);
const calcular = ctx.window.RelatorioContexto.paraAluna;
const registro = (id, Data, Tipo, Status = 'Pendente', Aluna = 'Ana') => ({ id, Data, Tipo, Status, Aluna, Licao_Atual: 'Página 10', Dificuldades: ['Dificuldade rítmica'] });
test('ausente e justificada trazem só a última aula anterior, sem alterar chamada', () => {
  const historico = [registro(1, '26/09/2026', 'Analise_Pratica'), registro(2, '03/10/2026', 'Analise_Pratica'),
    registro(3, '03/10/2026', 'Analise_Solfejo'), registro(4, '10/10/2026', 'Chamada', 'Ausente'),
    registro(5, '17/10/2026', 'Analise_Pratica'), registro(6, '03/10/2026', 'Analise_Teoria', '', 'Bia')];
  const antes = JSON.stringify(historico);
  for (const presenca of ['Ausente', 'Justificada']) {
    const r = calcular(historico, 'Ana', '10/10/2026', presenca);
    assert.deepEqual(Array.from(r.ultimaAula, i => i.id), [2, 3]);
    assert.equal(r.ultimaAula[0].Licao_Atual, 'Página 10');
    assert.equal(r.ultimaAula[0].Dificuldades[0], 'Dificuldade rítmica');
  }
  assert.equal(JSON.stringify(historico), antes);
  assert.equal(calcular(historico, 'Ana', '10/10/2026', 'Presente'), null);
  assert.equal(calcular(historico, 'Ana', '10/10/2026', 'Ainda não registrada'), null);
});
test('pendências excluem resolvidas e futuras, mantendo apostilas antigas e últimos métodos', () => {
  const historico = [registro(1, '26/09/2026', 'Casa_Metodo_Volume1'), registro(2, '03/10/2026', 'Casa_Metodo_Volume1'),
    registro(3, '03/10/2026', 'Casa_Metodo_Volume2'), registro(4, '19/09/2026', 'Casa_Apostila', 'Não resolvido'),
    registro(5, '26/09/2026', 'Casa_Apostila', 'Resolvido com pendências'), registro(6, '03/10/2026', 'Casa_Apostila', 'Resolvido'),
    registro(7, '17/10/2026', 'Casa_Apostila'), registro(8, '26/09/2026', 'Casa_MSA'), registro(9, '03/10/2026', 'Casa_MSA', 'Resolvido'),
    registro(10, '26/09/2026', 'Casa_Canto'), registro(11, '03/10/2026', 'Casa_Canto')];
  const r = calcular(historico, 'Ana', '10/10/2026', 'Ausente');
  assert.deepEqual(Array.from(r.pendentes, i => i.id), [2, 3, 4, 5, 11]);
  assert.equal(r.ultimaAula.length, 0);
});
test('datas atravessam meses e anos sem comparação textual em formato brasileiro', () => {
  const r = calcular([registro(1, '27/12/2025', 'Analise_Teoria'), registro(2, '03/01/2026', 'Analise_Teoria')], 'Ana', '10/01/2026', 'Ausente');
  assert.equal(r.ultimaAula[0].id, 2);
});
