/* Relatório por aluna: filtros aplicados antes da apresentação e exportação. */
(function () {
  const data = v => { const s=String(v||'').trim(); if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0,10); const m=s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/); return m ? m[3]+'-'+m[2].padStart(2,'0')+'-'+m[1].padStart(2,'0') : ''; };
  const normal = v => String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLowerCase();
  const ordem = (a,b) => data(a.Data).localeCompare(data(b.Data)) || Number(a.id||0)-Number(b.id||0);
  function construir(dados, {inicio,fim,turma=''}) {
    if(!inicio || !fim || !Number.isFinite(Date.parse(inicio)) || !Number.isFinite(Date.parse(fim)) || inicio>fim) throw new Error('Informe um período válido, com início anterior ou igual ao fim.');
    const noPeriodo = d => d && d>=inicio && d<=fim;
    return dados.alunas.filter(a=>a.ativo!==false && (!turma || a.turma===turma)).map(aluna=>{
      const historico=dados.historico.filter(r=>r.Aluna===aluna.nome).slice().sort(ordem);
      const registros=historico.filter(r=>noPeriodo(data(r.Data)));
      const chamadas=new Map();
      registros.filter(r=>r.Tipo==='Chamada').forEach(r=>chamadas.set(data(r.Data),r));
      const frequencia={presentes:0,faltas:0,justificadas:0,desconhecidas:0};
      for(const r of chamadas.values()) {const status=normal(r.Status);if(status==='presente')frequencia.presentes++;else if(['ausente','falta'].includes(status))frequencia.faltas++;else if(['justificada','falta justificada'].includes(status))frequencia.justificadas++;else frequencia.desconhecidas++;}
      const estudos=(dados.estudos||[]).filter(e=>e.aluna===aluna.nome && noPeriodo(data(e.data||e.Data)));
      const diasEstudo=new Set(estudos.filter(e=>Array.isArray(e.horarios)&&e.horarios.some(h=>String(h||'').trim())).map(e=>data(e.data||e.Data))).size;
      const notas=(dados.notas||[]).filter(n=>n.aluna===aluna.nome).map(n=>({...n,avaliacao:(dados.avaliacoes||[]).find(a=>String(a.id)===String(n.avaliacao_id))}));
      const metodos=[]; const inicios=new Map();
      historico.filter(r=>String(r.Tipo||'').startsWith('Material_') && data(r.Data)<=fim).forEach(r=>{
        const chave=r.Tipo+'|'+normal(r.Licao_Atual), status=normal(r.Status);
        if(status==='em andamento') { if(!inicios.has(chave)) inicios.set(chave,data(r.Data)); }
        if(status==='concluido') {
          const comeco=inicios.get(chave)||null;
          if(noPeriodo(data(r.Data))) metodos.push({material:r.Licao_Atual,disciplina:r.Tipo.replace('Material_',''),inicio:comeco,fim:data(r.Data),dias:comeco?Math.round((Date.parse(data(r.Data))-Date.parse(comeco))/86400000):null});
          inicios.delete(chave);
        }
      });
      return {aluna,registros,chamadas:[...chamadas.values()],frequencia,estudos,diasEstudo,diasPeriodo:Math.round((Date.parse(fim)-Date.parse(inicio))/86400000)+1,notas:notas.filter(n=>noPeriodo(data(n.avaliacao?.data_avaliacao))),notasSemData:notas.filter(n=>!data(n.avaliacao?.data_avaliacao)).length,metodos};
    });
  }
  function html(itens,{escapeHtml:e,classificacao,disciplinaAnalise,dificuldades,inicio,fim}) {
    const br=v=>data(v)?data(v).split('-').reverse().join('/'):'Data não informada';
    const p=v=>'<p>'+e(v)+'</p>';
    if(!itens.length)return '<div class="empty">Nenhuma aluna ativa encontrada para esta turma.</div>';
    return '<div data-exportacao class="scale-actions"><button type="button" class="secondary-action" data-expandir-alunas>Abrir todas</button><button type="button" class="secondary-action" data-recolher-alunas>Recolher todas</button></div><h3>Relatório geral das alunas</h3>'+p(br(inicio)+' a '+br(fim)+' · '+itens.length+' aluna(s)')+itens.map(item=>{
      const {aluna,registros,frequencia:f}=item;
      const aulas=registros.filter(r=>disciplinaAnalise(r.Tipo));
      const disciplinas=[...new Set(['Prática','Teoria','Solfejo','Solfejo Melódico',...aulas.map(r=>disciplinaAnalise(r.Tipo))])];
      const desempenho='<h4>Quadro de desempenho individual</h4><div class="table-wrap"><table class="scale-table"><thead><tr><th>Disciplina</th><th>Desempenho</th><th>Registros de aula</th></tr></thead><tbody>'+disciplinas.map(d=>{const rs=aulas.filter(r=>disciplinaAnalise(r.Tipo)===d),c=classificacao(rs);return '<tr><th>'+e(d)+'</th><td>'+e(c.icone+' '+c.nome+(c.nota>0?' · '+c.nota+'%':c.nome==='Bronze'?' · Em desenvolvimento':''))+'</td><td>'+rs.length+'</td></tr>';}).join('')+'</tbody></table></div>'+p('Mesmos critérios do quadro de desempenho: registros sem dificuldades. Campo vazio não comprova evolução.');
      const evolucoes=aulas.filter(r=>{const ds=dificuldades(r.Dificuldades);return ds.some(d=>/não apresentou dificuldade/i.test(d)) && !ds.some(d=>!/não apresentou dificuldade/i.test(d));});
      const evolucao='<h4>Evoluções registradas</h4>'+(evolucoes.length?evolucoes.map(r=>p(br(r.Data)+' · '+disciplinaAnalise(r.Tipo)+' · '+(r.Licao_Atual||'Conteúdo não informado')+' · Não apresentou dificuldades · '+(r.Instrutora||'Autoria não informada'))).join(''):p('Sem marcação explícita de evolução no período.'));
      const metodos='<h4>Conclusão dos métodos</h4>'+(item.metodos.length?item.metodos.map(m=>p(m.disciplina+' · '+m.material+' · Concluído em '+br(m.fim)+(m.inicio?' · Início registrado: '+br(m.inicio)+' · '+m.dias+' dias corridos até concluir':' · Tempo de conclusão indisponível: início não registrado.'))).join(''):p('Nenhuma conclusão de método registrada neste período.'))+p('O tempo considera início e conclusão explícitos do método, mesmo quando o início foi anterior ao período. Trocar de lição ou de método não comprova conclusão.');
      const boletim='<h4>Boletim do período</h4>'+(item.notas.length?item.notas.map(n=>p(br(n.avaliacao.data_avaliacao)+' · '+(n.avaliacao.titulo||'Avaliação')+' · '+n.disciplina+' · Nota: '+(n.nota??'Não informada'))).join(''):p('Sem notas de avaliações datadas neste período.'))+(item.notasSemData?p(item.notasSemData+' nota(s) sem data de avaliação não incluída(s) no recorte.'): '');
      const registrosHtml='<h4>Registros completos: conteúdos, dificuldades e lições de casa</h4>'+(registros.length?registros.map(r=>'<article class="report-record"><h4>'+e(br(r.Data)+' · '+(disciplinaAnalise(r.Tipo)||r.Tipo||'Registro'))+'</h4>'+p('Responsável: '+(r.Instrutora||r.Secretaria||'Não informada'))+(r.Licao_Atual?p('Material / conteúdo trabalhado: '+r.Licao_Atual):'')+(r.Licao_Casa?p('Lição de casa: '+r.Licao_Casa):'')+(r.Status?p('Situação: '+r.Status):'')+(dificuldades(r.Dificuldades).length?p('Dificuldades / avaliação: '+dificuldades(r.Dificuldades).join(' · ')):'')+(r.Observacao?'<p class="report-note">'+e(r.Observacao).replace(/\n/g,'<br>')+'</p>':'')+'</article>').join(''):p('Sem registros no período.'));
      const estudos='<h4>Estudos informados em casa</h4>'+p(item.diasEstudo+' de '+item.diasPeriodo+' dias · '+item.estudos.length+' lançamento(s). Vários horários no mesmo dia contam um dia de estudo.')+(item.estudos.map(s=>p(br(s.data||s.Data)+' · '+(Array.isArray(s.horarios)?s.horarios.join(' · '):'Horários não informados'))).join(''))+p('Dias sem registro não comprovam ausência de estudo.');
      return '<details class="student-report general-student" data-relatorio-aluna><summary class="student-report-heading"><h3>'+e(aluna.nome)+'</h3>'+p((aluna.turma||'Sem turma')+(aluna.comum?' · '+aluna.comum:''))+p(f.presentes+' presenças · '+f.faltas+' faltas · '+f.justificadas+' faltas justificadas')+(f.desconhecidas?p(f.desconhecidas+' chamada(s) com situação não reconhecida.'):'')+'<span class="general-toggle" data-exportacao>Ver ou recolher informações</span></summary>'+desempenho+estudos+boletim+evolucao+metodos+registrosHtml+'</details>';
    }).join('');
  }
  window.RelatorioGeral={construir,html};
})();
