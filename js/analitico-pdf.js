/* Exporta os dados da visualização aplicada, sem imprimir ou fotografar a página. */
(function () {
  const limpar = s => String(s ?? '').normalize('NFC').replace(/[\u2010-\u2015]/g, '-').replace(/[●■]/g, '-').replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, '').trim();
  function capturar(elemento) {
    const blocos = [];
    function visitar(no) {
      if (no.nodeType === 3) { if (no.textContent.trim()) blocos.push({texto:no.textContent.trim()}); return; }
      if (no.nodeType !== 1 || no.matches('button, script, style, .hidden, .action-error, [data-exportacao], #pergunta-analitico-ia') || no.hidden) return;
      if (no.matches('.ai-feedback')) {
        const resposta = no.querySelector('.ai-answer');
        if (resposta) blocos.push({titulo:'Análise pedagógica com IA', texto:resposta.innerText});
        return;
      }
      if (no.matches('.bar-chart')) {
        blocos.push({barras:[...no.querySelectorAll('.bar-item')].map(item => ({rotulo:item.querySelector('small').textContent, valor:Number(item.querySelector('strong').textContent)}))}); return;
      }
      if (no.matches('svg')) {
        const pontos = no.querySelector('polyline')?.getAttribute('points');
        if (pontos) blocos.push({linha:pontos.split(/\s+/).map(p=>p.split(',').map(Number)), viewBox:no.getAttribute('viewBox').split(/\s+/).map(Number)});
        return;
      }
      if (no.matches('.comparison-chart')) {
        for (const row of no.querySelectorAll('.comparison-chart-row')) {
          blocos.push({titulo:row.querySelector('strong').textContent, texto:row.querySelector('small').textContent});
          const resumo = row.querySelector('small').textContent;
          blocos.push({barras:[...row.querySelectorAll('div > span')].map((s,i)=>({rotulo:i ? 'Provas (escala percentual)' : 'Rendimento pedagógico (%)',valor:parseFloat(s.style.width)||0,ausente:i ? /Provas\s*[—–-]/.test(resumo) : /Aulas\s*[—–-]/.test(resumo)})).filter(v=>!v.ausente)});
        }
        return;
      }
      if (no.matches('table')) {
        const headers = [...no.querySelectorAll('thead th')].map(c=>c.innerText);
        for (const row of no.querySelectorAll('tbody tr')) {
          const cells = [...row.children].map(c=>c.innerText.replace(/\n/g,' '));
          blocos.push({titulo:cells[0], texto:cells.slice(1).map((v,i)=>`${headers[i+1] || 'Informação'}: ${v}`).join('\n')});
        }
        return;
      }
      if (no.matches('textarea, input')) { if(no.value) blocos.push({texto:no.value}); return; }
      if (no.matches('.feedback-panel > article')) {
        const titulo = no.querySelector('strong')?.textContent;
        if(titulo) blocos.push({titulo});
        for(const filho of no.childNodes) if(filho !== no.querySelector('strong')) visitar(filho);
        return;
      }
      if (no.matches('h1,h2,h3,h4')) { blocos.push({titulo:no.innerText}); return; }
      if (no.matches('.metric,.evolution-list article,.comparison-list article')) { blocos.push({texto:[...no.children].map(c=>c.innerText).join(' | ')}); return; }
      if (no.matches('p,li,.homework-line')) { blocos.push({texto:no.innerText}); return; }
      for (const filho of no.childNodes) visitar(filho);
    }
    visitar(elemento);
    return blocos;
  }
  function conclusao(registros, aba) {
    if (aba === 'boletim') return 'As notas acima devem ser discutidas junto aos critérios de cada avaliação. Isoladamente, não permitem concluir sobre evolução, frequência ou dificuldades. Recomenda-se confrontá-las com os registros de aula antes de definir o próximo foco pedagógico.';
    const aulas = registros.filter(r => /^(Analise_)?(Prática|Teoria|Solfejo|Solfejo Melódico|Canto)$/.test(r.Tipo));
    if (!aulas.length) return 'Não há registros pedagógicos no recorte selecionado suficientes para uma conclusão sobre aprendizagem. Recomenda-se completar os registros e revisar o período antes de definir intervenções. Ausência de registro não significa ausência de estudo ou de dificuldades.';
    const contagem = new Map();
    aulas.forEach(r => {
      let ds = r.Dificuldades;
      if (typeof ds === 'string') { try { ds = JSON.parse(ds); } catch (_) { ds = ds.split(/[,;]+/); } }
      if (!Array.isArray(ds)) return;
      for (const d of ds.filter(d=>d && !/não apresentou dificuldade|não participou/i.test(d))) {
        const chave = `${String(r.Tipo).replace(/^Analise_/, '')}: ${d}`;
        contagem.set(chave,(contagem.get(chave)||0)+1);
      }
    });
    const destaques = [...contagem].sort((a,b)=>b[1]-a[1]).slice(0,3);
    const faltas = registros.filter(r=>r.Tipo==='Chamada' && ['Ausente','Justificada'].includes(r.Status));
    const diasPerdidos = new Set(faltas.map(r=>`${r.Aluna}|${r.Data}`)).size;
    return `Foram considerados ${aulas.length} registros pedagógicos no recorte selecionado. ${destaques.length ? `Os pontos mais registrados foram: ${destaques.map(([d,n])=>`${d} (${n} ocorrência(s))`).join('; ')}. Sugere-se retomar esses conteúdos com exercícios graduais e verificar a resposta nas próximas aulas.` : 'Não foram identificadas dificuldades explícitas nesses registros. Isso não comprova domínio completo; sugere-se consolidar os conteúdos e observar a continuidade.'}${diasPerdidos ? ` Há ${diasPerdidos} registro(s) de falta por aluna/data, incluindo justificadas; convém conferir os conteúdos perdidos e organizar a retomada.` : ''} ${aba === 'quadro' ? 'Este resumo é coletivo e não deve ser aplicado indistintamente a cada aluna.' : 'O planejamento deve considerar o contexto da aluna e os objetivos combinados.'} Esta síntese é automática, não é diagnóstico nem análise de IA, e deve ser revisada pela equipe pedagógica.`;
  }
  function gerar({gem, filtros, blocos, conclusao:final}, JsPDF) {
    const pdf = new JsPDF({unit:'mm',format:'a4',compress:true});
    let y = 20;
    const fonte = (bold=false,size=10) => {pdf.setFont('helvetica',bold?'bold':'normal');pdf.setFontSize(size);pdf.setTextColor(35,45,60);};
    const pagina = () => {pdf.addPage();y=20;};
    const reservar = h => {if(y+h>277) pagina();};
    function escrever(s,bold=false,size=10) {
      fonte(bold,size);
      for(const linha of pdf.splitTextToSize(limpar(s),178)) {reservar(6);fonte(bold,size);pdf.text(linha,16,y);y+=5.5;}
      y+=2;
    }
    escrever('Relatório analítico',true,17); escrever(gem || 'GEM Musical',true,12); escrever(filtros); y+=4;
    for(const b of blocos) {
      if(b.titulo) {reservar(20);escrever(b.titulo,true,12);}
      if(b.texto) escrever(b.texto);
      if(b.barras) {
        const max = Math.max(1,...b.barras.map(v=>v.valor));
        for(const item of b.barras) {
          fonte();const n=pdf.splitTextToSize(limpar(item.rotulo),178).length;
          reservar(n*5.5+13);escrever(`${item.rotulo}: ${item.valor}`);
          pdf.setFillColor(237,239,244);pdf.rect(16,y,178,3,'F');
          pdf.setFillColor(167,100,134);if(item.valor>0)pdf.rect(16,y,178*item.valor/max,3,'F');y+=9;
        }
      }
      if(b.linha?.length) {
        reservar(55);pdf.setDrawColor(220,225,233);
        [0,20,40].forEach(d=>pdf.line(16,y+d,194,y+d));pdf.setDrawColor(87,125,184);
        const pts=b.linha.map(([x,v])=>[16+x/b.viewBox[2]*178,y+v/b.viewBox[3]*40]);
        pts.forEach(([x,v],i)=>{pdf.circle(x,v,0.8,'S');if(i)pdf.line(pts[i-1][0],pts[i-1][1],x,v);});y+=49;
      }
    }
    reservar(25);escrever('Conclusão pedagógica',true,14);escrever(final);
    const total=pdf.getNumberOfPages();
    for(let i=1;i<=total;i++){pdf.setPage(i);fonte(false,8);pdf.text(`Relatório analítico | ${i} / ${total}`,16,289);}
    return pdf;
  }
  window.AnaliticoPDF = {capturar, conclusao, gerar};
})();
