(function(){
  const normal=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLowerCase();
  function sabado(agora=new Date()) {
    const partes=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Sao_Paulo',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(agora);
    const v=t=>partes.find(p=>p.type===t).value;
    const d=new Date(v('year')+'-'+v('month')+'-'+v('day')+'T12:00:00Z');
    d.setUTCDate(d.getUTCDate()+(6-d.getUTCDay()+7)%7);
    return d.toISOString().slice(0,10);
  }
  function aulas(escala,{nome,papel,atividades=[]}) {
    const horarios=[...new Set(escala.flatMap(l=>Object.keys(l).filter(k=>!['Aluna','_detalhes'].includes(k))))].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
    const grupos=new Map();
    for(const linha of escala){
      if(papel==='Aluna' && normal(linha.Aluna)!==normal(nome))continue;
      horarios.forEach((bloco,indice)=>{
        const valor=String(linha[bloco]||'');if(!valor)return;
        const d=linha._detalhes?.[bloco]||{},sala=d.sala||valor.split('|')[0].trim();
        const tipo=d.tipo||'Disciplina não informada';
        const praticaEditada=d.atividade_secretaria && d.responsavel_papel==='Professora' && /^(pratica|pratica\s*\+\s*solfejo|solfejo\s*\+\s*pratica)$/.test(normal(tipo));
        const componentes=praticaEditada?['Solfejo','Prática']:d.atividade_secretaria?[tipo]:d.componentes?.length?d.componentes:/pratica.*solfejo|solfejo.*pratica/.test(normal(tipo))?['Solfejo','Prática']:[tipo];
        const tempos=d.horarios_componentes||{};
        const calculados=window.RodizioEngine?.horariosComponentes?.(bloco,componentes,atividades)||{};
        for(const disciplina of componentes){
          const responsavel=d.atividade_secretaria?(d.responsavel||'Secretarias — a definir'):(d.professoras_componentes?.[disciplina]||valor.split('|').slice(1).join('|').trim()||'A definir');
          if(papel==='Professora' && ((d.atividade_secretaria&&d.responsavel_papel!=='Professora')||normal(responsavel)!==normal(nome)))continue;
          const horario=tempos[disciplina]||calculados[disciplina]||bloco;
          const turma=String(d.turma||'Turma não informada');
          const individual=d.atividade_secretaria ? true : typeof d.individual==='boolean' ? d.individual : /pratica.*solfejo|solfejo.*pratica/.test(normal(tipo)) || normal(tipo)==='pratica';
          const chave=[bloco,disciplina,sala,responsavel,horario,turma,individual].join('|');
          if(!grupos.has(chave))grupos.set(chave,{numero:indice+1,bloco,horario,disciplina,sala,responsavel,turma,individual,papelResponsavel:d.atividade_secretaria?d.responsavel_papel:'Professora',alunas:[]});
          const item=grupos.get(chave);if(!item.alunas.includes(linha.Aluna))item.alunas.push(linha.Aluna);
        }
      });
    }
    return [...grupos.values()].sort((a,b)=>a.numero-b.numero||a.horario.localeCompare(b.horario));
  }
  window.ProximasAulas={sabado,aulas};
})();
