const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(require.resolve('../js/relatorio-pdf.js'), 'utf8'), ctx);
class PDF {
  constructor() { this.paginas = [[]]; this.pagina = 0; }
  setFont() {}
  setFontSize(size) { this.size = size; }
  setTextColor() {}
  setDrawColor() {}
  line() {}
  splitTextToSize(value) { return value.match(/.{1,70}/g) || ['']; }
  text(value, x, y) { this.paginas[this.pagina].push({ value, x, y, size: this.size }); }
  addPage() { this.paginas.push([]); this.pagina++; }
  getNumberOfPages() { return this.paginas.length; }
  setPage(n) { this.pagina = n - 1; }
}
test('relatório longo mantém conteúdo, presença e margens sem imagens ou redução', () => {
  const longo = 'Observação da professora: ' + 'Estudar com atenção. '.repeat(700) + 'FIM DA OBSERVAÇÃO';
  const pdf = ctx.window.RelatorioPDF.gerar({ gem: 'GEM Teste', data: '03/10/2026', resumo: 'Resumo', alunas: [
    { nome: 'Júlia', presenca: 'Justificada', observacaoPresenca: 'Motivo registrado', registros: [
      { titulo: 'Prática - Professora: Ana', campos: [longo, 'Situação: pendente'] }
    ] }
  ] }, PDF);
  assert.ok(pdf.paginas.length > 2);
  const tudo = pdf.paginas.flat().map(l => l.value).join('');
  assert.ok(tudo.includes('Presença: Justificada'));
  assert.ok(tudo.includes('Motivo registrado'));
  assert.ok(tudo.includes('FIM DA OBSERVAÇÃO'));
  assert.ok(tudo.includes('Situação: pendente'));
  const corpo = pdf.paginas.flat().filter(l => l.size === 10 && !l.value.includes('GEM Teste | Data:')).map(l => l.value).join('');
  assert.ok(corpo.includes(longo));
  pdf.paginas.forEach((pagina, i) => {
    assert.ok(pagina.some(l => l.value === `Página ${i+1} de ${pdf.paginas.length}`));
    assert.ok(pagina.every(l => l.y >= 16 && l.y <= 289));
    assert.ok(pagina.every(l => l.size >= 9));
    if (i) assert.ok(pagina.some(l => l.value.includes('Júlia (continuação)')));
  });
});
test('relatório vazio continua sendo um PDF válido de uma página', () => {
  const pdf = ctx.window.RelatorioPDF.gerar({ data: '03/10/2026', resumo: '0 alunas', alunas: [] }, PDF);
  assert.equal(pdf.paginas.length, 1);
  assert.ok(pdf.paginas[0].some(l => l.value.includes('Não há escala salva')));
});
