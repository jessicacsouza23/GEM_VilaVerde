const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const src = fs.readFileSync(require.resolve('../app.js'), 'utf8');
const ctx = {};
vm.createContext(ctx);
vm.runInContext(src.slice(0, src.indexOf('// Preenche somente')), ctx);
test('mantém orientações específicas de preenchimento', () => {
  const message = 'Informe a página da Apostila de Prática. Ex.: página 18, lições 1 e 2.';
  assert.equal(ctx.mensagemErro({message}), message);
});
test('explica falhas conhecidas e preserva salvamento parcial sem exibir detalhes privados', () => {
  for (const [code, esperado] of [['42501', /permissão/], ['23505', /Já existe/], ['42P01', /migrations/], ['23502', /campo obrigatório/], ['PGRST301', /sessão/]]) {
    const texto = ctx.mensagemErro({message: 'A aula foi salva, mas não foi possível salvar a lição.', cause: {code, message: 'detalhe privado'}});
    assert.match(texto, esperado);
    assert.match(texto, /A aula foi salva/);
    assert.doesNotMatch(texto, /detalhe privado/);
  }
});
test('conexão e causa desconhecida orientam conferir salvamento antes de repetir', () => {
  assert.match(ctx.mensagemErro(new Error('Failed to fetch')), /Confira a internet/);
  assert.match(ctx.mensagemErro({}), /não informou o motivo/);
  assert.match(ctx.mensagemErro(new Error('Não foi possível salvar.')), /não detalhou a causa/);
});
