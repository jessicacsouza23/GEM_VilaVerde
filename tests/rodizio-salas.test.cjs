const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ctx = { window: {} }; vm.createContext(ctx);
const fonte = fs.readFileSync(require.resolve('../js/rodizio-engine.js'), 'utf8');
vm.runInContext(fonte.replace('window.RodizioEngine = {', 'window.RodizioEngine = { estabilizarSalas,'), ctx);
const engine = ctx.window.RodizioEngine;
const entrada = () => ({ data: '17/10/2026', professoras: ['Ana', 'Bia', 'Clara'], turmasReais: { 'Turma 1': ['A1', 'A2'], 'Turma 2': ['B1', 'B2'] }, modelo: { configuracao: {
  blocos: [{ inicio: '08:00', fim: '08:45' }, { inicio: '09:00', fim: '09:45' }],
  salas: [{ Sala: 'SALA 1', Uso: 'Individual' }, { Sala: 'SALA 2', Uso: 'Individual' }],
  atividades: [{ Atividade: 'Teoria', Formato: 'Turma', 'Sala sugerida': 'SALA 8' }, { Atividade: 'Prática', Formato: 'Individual', 'Duração (min)': 45 }],
  turmas: [{ Turma: 'Turma 1' }, { Turma: 'Turma 2' }],
  professoras_habilitadas: { Teoria: ['Clara'], 'Prática': ['Ana', 'Bia'] }
} } });
function conferir(escala) {
  const ocupacao = new Map();
  const salasPorProfessora = new Map();
  for (const linha of escala) for (const [hora, detalhe] of Object.entries(linha._detalhes)) {
    if (!detalhe.individual) continue;
    const [sala] = linha[hora].split('|');
    const chave = `${hora}|${sala}`;
    assert.ok(!ocupacao.has(chave), 'Duas alunas na mesma sala e horário');
    ocupacao.set(chave, linha.Aluna);
    const professora = linha[hora].split('|')[1].trim();
    if (salasPorProfessora.has(professora)) assert.equal(sala, salasPorProfessora.get(professora));
    salasPorProfessora.set(professora, sala);
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
test('trocas sucessivas preservam quem continua na Prática, sem exigir sala vitalícia', () => {
  const mapa = {};
  [['A','B'], ['B','C'], ['A','C']].forEach((profs, i) => profs.forEach((prof, j) => {
    mapa[`${i}-${j}`] = { [`h${i}`]: `SALA ${j+1} | ${prof}`, _detalhes: { [`h${i}`]: { individual: true } } };
  }));
  assert.equal(engine.estabilizarSalas(mapa, ['h0','h1','h2'], ['SALA 1','SALA 2']), true);
  assert.equal(mapa['1-0'].h1, 'SALA 2 | B');
  assert.equal(mapa['1-1'].h1, 'SALA 1 | C');
  assert.equal(mapa['2-1'].h2, 'SALA 1 | C');
  assert.equal(mapa['2-0'].h2, 'SALA 2 | A');
});
test('professoras alternam entre coletiva e individual em horários diferentes', () => {
  const dados = entrada();
  dados.modelo.configuracao.professoras_habilitadas = { Teoria: ['Ana', 'Bia', 'Clara'], 'Prática': ['Ana', 'Bia', 'Clara'] };
  const resultado = engine.gerar({ ...dados, coletivas: { Teoria: { 'Turma 1': 'Ana', 'Turma 2': 'Clara' } } });
  assert.equal(resultado.erros.length, 0, resultado.erros.join('\n'));
  const porHora = new Map();
  for (const linha of resultado.escala) for (const [hora, detalhe] of Object.entries(linha._detalhes)) {
    if (!porHora.has(hora)) porHora.set(hora, new Map());
    const [sala, nome] = linha[hora].split('|').map(v => v.trim());
    porHora.get(hora).set(nome, sala);
    if (!detalhe.individual) assert.equal(sala, 'SALA 8');
  }
  const [primeiro, segundo] = [...porHora.keys()].sort().map(h => porHora.get(h));
  assert.equal(primeiro.get('Ana'), 'SALA 8');
  assert.equal(segundo.get('Clara'), 'SALA 8');
  assert.equal(segundo.get('Ana'), primeiro.get('Clara'), 'Ana ocupa a sala que Clara liberou');
  assert.equal(segundo.get('Bia'), primeiro.get('Bia'), 'Bia continua na mesma sala');
  for (const nome of ['Ana', 'Clara']) {
    const tipos = new Set();
    for (const linha of resultado.escala) for (const [hora, detalhe] of Object.entries(linha._detalhes)) {
      if (linha[hora].endsWith(`| ${nome}`)) tipos.add(detalhe.individual);
    }
    assert.ok(tipos.has(true) && tipos.has(false), `${nome} deve participar da coletiva e do individual`);
  }
});

test('duas coletivas trocam professoras sem deslocar as demais salas práticas', () => {
  const mapa = {};
  const adicionar = (hora, aluna, sala, professora, individual, tipo = 'Prática') => {
    const linha = mapa[aluna] ||= { Aluna: aluna, _detalhes: {} };
    linha[hora] = `${sala} | ${professora}`;
    linha._detalhes[hora] = { individual, tipo };
  };
  // Ordem embaralhada e sala vaga: a substituição deve seguir a coletiva,
  // não escolher simplesmente a primeira sala disponível.
  adicionar('h0', 'a', 'SALA 3', 'Ana', true);
  adicionar('h0', 'b', 'SALA 2', 'Bia', true);
  adicionar('h0', 'c', 'SALA 4', 'Cris', true);
  adicionar('h0', 't', 'SALA 8', 'Dora', false, 'Teoria');
  adicionar('h0', 's', 'SALA 9', 'Eva', false, 'Solfejo');
  adicionar('h1', 'a', 'SALA 1', 'Eva', true);
  adicionar('h1', 'b', 'SALA 3', 'Dora', true);
  adicionar('h1', 'c', 'SALA 2', 'Cris', true);
  adicionar('h1', 't', 'SALA 8', 'Ana', false, 'Teoria');
  adicionar('h1', 's', 'SALA 9', 'Bia', false, 'Solfejo');
  assert.equal(engine.estabilizarSalas(mapa, ['h0', 'h1'], ['SALA 1', 'SALA 2', 'SALA 3', 'SALA 4']), true);
  assert.equal(mapa.a.h1, 'SALA 2 | Eva');
  assert.equal(mapa.b.h1, 'SALA 3 | Dora');
  assert.equal(mapa.c.h1, 'SALA 4 | Cris');
  assert.equal(mapa.t.h1, 'SALA 8 | Ana');
  assert.equal(mapa.s.h1, 'SALA 9 | Bia');
});

test('falha de capacidade não aplica alterações parciais', () => {
  const mapa = [
    { h0: 'SALA 1 | Ana', h1: 'SALA 2 | Ana', _detalhes: { h0: { individual: true }, h1: { individual: true } } },
    { h1: 'SALA 1 | Bia', _detalhes: { h1: { individual: true } } }
  ];
  const antes = JSON.stringify(mapa);
  assert.equal(engine.estabilizarSalas(mapa, ['h0', 'h1'], ['SALA 1']), false);
  assert.equal(JSON.stringify(mapa), antes);
});

test('cadeia entre coletivas leva à sala prática liberada', () => {
  const mapa = [
    { h0: 'SALA 2 | Ana', h1: 'SALA 8 | Ana', _detalhes: { h0: { individual: true }, h1: { individual: false } } },
    { h0: 'SALA 8 | Bia', h1: 'SALA 9 | Bia', _detalhes: { h0: { individual: false }, h1: { individual: false } } },
    { h0: 'SALA 9 | Clara', h1: 'SALA 1 | Clara', _detalhes: { h0: { individual: false }, h1: { individual: true } } }
  ];
  assert.equal(engine.estabilizarSalas(mapa, ['h0', 'h1'], ['SALA 1', 'SALA 2']), true);
  assert.equal(mapa[2].h1, 'SALA 2 | Clara');
  assert.equal(mapa[0].h1, 'SALA 8 | Ana');
  assert.equal(mapa[1].h1, 'SALA 9 | Bia');
});

test('saída antecipada libera sala sem deslocar quem permanece', () => {
  const dados = entrada();
  dados.professoras.push('Dora');
  dados.modelo.configuracao.professoras_habilitadas['Prática'].push('Dora');
  const r = engine.gerar({ ...dados, saidas: { Ana: '08:00 - 08:45 (Bloco 1)' } });
  assert.equal(r.erros.length, 0, r.erros.join('\n'));
  const salas = {};
  for (const linha of r.escala) for (const [hora, detalhe] of Object.entries(linha._detalhes)) {
    if (!detalhe.individual) continue;
    const [sala, nome] = linha[hora].split('|').map(v => v.trim());
    (salas[hora] ||= {})[nome] = sala;
  }
  const [primeiro, segundo] = Object.keys(salas).sort().map(h => salas[h]);
  assert.ok(primeiro.Ana);
  assert.equal(segundo.Ana, undefined);
  assert.equal(segundo.Bia, primeiro.Bia);
  assert.equal(segundo.Dora, primeiro.Ana);
});

test('folgas e escolha incompatível entre coletiva e fixa no mesmo horário não são ignoradas', () => {
  const folga = engine.gerar({ ...entrada(), folgas: ['Ana'] });
  assert.equal(folga.escala, null); assert.ok(folga.erros.length);
  const conflito = entrada();
  conflito.modelo.configuracao.professoras_habilitadas['Prática'].push('Clara');
  const r = engine.gerar({ ...conflito, usarFixas: true, fixas: { a1: 'Clara' }, coletivas: { Teoria: { 'Turma 2': 'Clara' } } });
  assert.equal(r.escala, null); assert.ok(r.erros.length);
});
