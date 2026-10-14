/* PDF textual: não captura a tela nem reduz cartões para caber na página. */
(function () {
  const texto = valor => String(valor ?? '').normalize('NFC')
    .replace(/[\u2010-\u2015]/g, '-').replace(/\u00a0/g, ' ')
    .replace(/[\p{Extended_Pictographic}\uFE0F\u200D\u2713\u2705]/gu, '').trim();

  function gerar({ gem, data, resumo, alunas }, JsPDF) {
    const pdf = new JsPDF({ orientation: 'p', unit: 'mm', format: 'a4', compress: true });
    const margem = 16, largura = 178, limite = 278, passo = 5;
    let y = 16, alunaAtual = '';
    const estilo = (negrito = false, tamanho = 10) => {
      pdf.setFont('helvetica', negrito ? 'bold' : 'normal');
      pdf.setFontSize(tamanho);
      pdf.setTextColor(35, 45, 60);
    };
    const linhas = (valor) => pdf.splitTextToSize(texto(valor), largura);
    const escrever = (valor, negrito = false, tamanho = 10) => {
      estilo(negrito, tamanho);
      const partes = linhas(valor);
      for (const linha of partes) {
        if (y + passo > limite) {
          novaPagina();
          estilo(negrito, tamanho);
        }
        pdf.text(linha, margem, y);
        y += passo;
      }
      y += 2;
    };
    const cabecalho = () => {
      escrever('Relatório diário', true, 16);
      escrever(`${gem || 'GEM Musical'} | Data: ${data}`, false, 10);
      pdf.setDrawColor(220, 225, 233);
      pdf.line(margem, y, margem + largura, y);
      y += 9;
    };
    const novaPagina = () => {
      pdf.addPage();
      y = 16;
      cabecalho();
      if (alunaAtual) escrever(`${alunaAtual} (continuação)`, true, 11);
    };
    const reservar = (altura) => { if (y + altura > limite) novaPagina(); };
    cabecalho();
    escrever(resumo);
    if (!alunas.length) escrever('Não há escala salva para esta data.');
    for (const aluna of alunas) {
      alunaAtual = '';
      estilo(true, 12);
      reservar(linhas(aluna.nome).length * passo + 28);
      escrever(aluna.nome, true, 12);
      alunaAtual = texto(aluna.nome);
      escrever(`Presença: ${aluna.presenca || 'Ainda não registrada'}`);
      if (aluna.observacaoPresenca) escrever(`Observação da presença: ${aluna.observacaoPresenca}`);
      if (!aluna.registros.length) escrever('Nenhum registro pedagógico lançado ainda para esta aluna.');
      for (const registro of aluna.registros) {
        estilo(true, 11);
        reservar(linhas(registro.titulo).length * passo + 12);
        escrever(registro.titulo, true, 11);
        for (const campo of registro.campos) escrever(campo);
        y += 3;
      }
      y += 5;
    }
    const total = pdf.getNumberOfPages();
    for (let pagina = 1; pagina <= total; pagina++) {
      pdf.setPage(pagina);
      estilo(false, 9);
      pdf.text(`Página ${pagina} de ${total}`, 105, 289, { align: 'center' });
    }
    return pdf;
  }
  window.RelatorioPDF = { gerar };
})();
