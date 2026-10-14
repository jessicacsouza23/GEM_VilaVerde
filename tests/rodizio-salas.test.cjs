const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ctx = { window: {} }; vm.createContext(ctx);
const fonte = fs.readFileSync(require.resolve('../js/rodizio-engine.js'), 'utf8');
vm.runInContext(fonte.replace('window.RodizioEngine = {', 'window.RodizioEngine = { estabilizarSalas, validarSalasDoSabado,'), ctx);
const engine = ctx.window.RodizioEngine;
const entrada = () => ({ data: '17/10/2026', professoras: ['Ana', 'Bia', 'Clara'], turmasReais: { 'Turma 1': ['A1', 'A2'], 'Turma 2': ['B1', 'B2'] }, modelo: { configuracao: {
  blocos: [{ inicio: '08:00', fim: '08:45' }, { inicio: '09:00', fim: '09:45' }],
  salas: [{ Sala: 'SALA 1', Uso: 'Individual' }, { Sala: 'SALA 2', Uso: 'Individual' }],
  atividades: [{ Atividade: 'Teoria', Formato: 'Turma', 'Sala sugerida': 'SALA 8' }, { Atividade: 'Prática', Formato: 'Individual', 'Duração (min)': 45 }],
  turmas: [{ Turma: 'Turma 1' }, { Turma: 'Turma 2' }],
  professoras_habilitadas: { Teoria: ['Clara'], 'Prática': ['Ana', 'Bia'] }
} } });
function conferir(escala) {
  assert.equal(engine.validarSalasDoSabado(escala).length, 0);
  const ocupacao = new Map();
  for (const linha of escala) for (const [hora, detalhe] of Object.entries(linha._detalhes)) {
    if (!detalhe.individual) continue;
    const [sala] = linha[hora].split('|');
    const chave = `${hora}|${sala}`;
    assert.ok(!ocupacao.has(chave), 'Duas alunas na mesma sala e horário');
    ocupacao.set(chave, linha.Aluna);
  }
}
test('geração mantém salas o sábado inteiro, inclusive professora coletiva', () => {
  const resultado = engine.gerar(entrada());
  assert.equal(resultado.erros.length, 0, resultado.erros.join('\n'));
  conferir(resultado.escala);
});
test('histórico permite rodar salas entre sábados, sem alterar escala anterior', () => {
  const primeiro = engine.gerar(entrada());
  const anterior = JSON.stringify(primeiro.escala);
  const segundo = engine.gerar({ ...entrada(), data: '24/10/2026', escalasAnteriores: [{ id: '17/10/2026', escala: primeiro.escala }] });
  assert.equal(segundo.erros.length, 0); conferir(segundo.escala);
  assert.equal(JSON.stringify(primeiro.escala), anterior);
  const salaAna = escala => escala.flatMap(linha => Object.keys(linha._detalhes).map(h => linha[h])).find(v => v.endsWith('| Ana')).split('|')[0];
  assert.notEqual(salaAna(primeiro.escala), salaAna(segundo.escala));
});
test('estabilização impossível preserva a distribuição original', () => {
  const mapa = {};
  [['A','B'], ['B','C'], ['A','C']].forEach((profs, i) => profs.forEach((prof, j) => {
    mapa[`${i}-${j}`] = { [`h${i}`]: `SALA ${j+1} | ${prof}`, _detalhes: { [`h${i}`]: { individual: true } } };
  }));
  const antes = JSON.stringify(mapa);
  assert.equal(engine.estabilizarSalas(mapa, ['h0','h1','h2'], ['SALA 1','SALA 2'], '17/10/2026'), false);
  assert.equal(JSON.stringify(mapa), antes);
});
test('professoras alternam entre coletiva e individual em horários diferentes', () => {
  const dados = entrada();
  dados.modelo.configuracao.professoras_habilitadas = { Teoria: ['Ana', 'Bia', 'Clara'], 'Prática': ['Ana', 'Bia', 'Clara'] };
  const resultado = engine.gerar({ ...dados, coletivas: { Teoria: { 'Turma 1': 'Ana', 'Turma 2': 'Clara' } } });
  assert.equal(resultado.erros.length, 0, resultado.erros.join('\n'));
  for (const nome of ['Ana', 'Clara']) {
    const tipos = new Set();
    for (const linha of resultado.escala) for (const [hora, detalhe] of Object.entries(linha._detalhes)) {
      if (linha[hora].endsWith(`| ${nome}`)) tipos.add(detalhe.individual);
    }
    assert.ok(tipos.has(true) && tipos.has(false), `${nome} deve participar da coletiva e do individual`);
  }
});

test('folgas e escolha incompatível entre coletiva e fixa no mesmo horário não são ignoradas', () => {
  const folga = engine.gerar({ ...entrada(), folgas: ['Ana'] });
  assert.equal(folga.escala, null); assert.ok(folga.erros.length);
  const conflito = entrada();
  conflito.modelo.configuracao.professoras_habilitadas['Prática'].push('Clara');
  const r = engine.gerar({ ...conflito, usarFixas: true, fixas: { a1: 'Clara' }, coletivas: { Teoria: { 'Turma 2': 'Clara' } } });
  assert.equal(r.escala, null); assert.ok(r.erros.length);
});
