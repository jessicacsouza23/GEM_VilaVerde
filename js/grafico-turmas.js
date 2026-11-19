(function(){
  const normal=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLowerCase();
  const iso=v=>{const s=String(v||'').trim(),m=s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);return m?m[3]+'-'+m[2]+'-'+m[1]:s.slice(0,10);};
  const disciplinas=['Teoria','Solfejo','Prática','Solfejo Melódico'];
  // Os registros antigos usavam MSA para Solfejo e Canto para Solfejo
  // Melódico. As equivalências são intencionalmente fechadas: nunca usamos
  // "começa com Solfejo", pois isso juntaria duas disciplinas distintas.
  function disciplinaDoRegistro(tipo){
    const nome=normal(tipo).replace(/^analise[\s_-]*/, '');
    if(['pratica'].includes(nome))return 'Prática';
    if(['teoria'].includes(nome))return 'Teoria';
    if(['solfejo','msa','solfejo individual','solfejo em grupo'].includes(nome))return 'Solfejo';
    if(['canto','solfejo melodico','solfejo melodico individual'].includes(nome))return 'Solfejo Melódico';
    return null;
  }
  function calcular(alunas,historico,referencia,inicioEscolhido){
    const fim=iso(referencia),dia=new Date(fim+'T12:00:00Z');
    if(!/^\d{4}-\d{2}-\d{2}$/.test(fim)||!Number.isFinite(dia.getTime())||dia.toISOString().slice(0,10)!==fim)throw new Error('Informe uma data final válida.');
    dia.setUTCDate(dia.getUTCDate()-29);const inicio=inicioEscolhido===undefined?dia.toISOString().slice(0,10):iso(inicioEscolhido);
    const primeiro=new Date(inicio+'T12:00:00Z');
    if(!/^\d{4}-\d{2}-\d{2}$/.test(inicio)||!Number.isFinite(primeiro.getTime())||primeiro.toISOString().slice(0,10)!==inicio||inicio>fim)throw new Error('Informe uma data inicial válida, anterior ou igual à final.');
    const ativas=alunas.filter(a=>a.ativo!==false),porNome=new Map(ativas.map(a=>[a.nome,a]));
    const turmas=[...new Set(ativas.map(a=>a.turma||'Sem turma'))].sort((a,b)=>a.localeCompare(b,'pt-BR',{numeric:true}));
    const resultados=new Map();
    for(const r of historico){
      const d=iso(r.Data),aluna=porNome.get(r.Aluna);if(!aluna||d<inicio||d>fim)continue;
      const disciplina=disciplinaDoRegistro(r.Tipo);if(!disciplina)continue;
      let ds=r.Dificuldades;if(typeof ds==='string'){try{ds=JSON.parse(ds);}catch(_){ds=ds.split(/[,;]+/);}}
      ds=(Array.isArray(ds)?ds:[]).map(normal).filter(d=>d&&!/^(null|nan|\[\])$/.test(d));
      const positivo=ds.length>0&&ds.every(d=>/^nao apresentou dificuldades?$/.test(d));
      const chave=JSON.stringify([r.Aluna,disciplina]),v=resultados.get(chave)||{total:0,positivos:0};v.total++;if(positivo)v.positivos++;resultados.set(chave,v);
    }
    return {inicio,fim,turmas,disciplinas:disciplinas.map(disciplina=>({disciplina,valores:turmas.map(turma=>{
      const itens=ativas.filter(a=>(a.turma||'Sem turma')===turma).map(a=>resultados.get(JSON.stringify([a.nome,disciplina]))).filter(Boolean);
      return {turma,alunas:itens.length,percentual:itens.length?itens.reduce((s,v)=>s+v.positivos/v.total*100,0)/itens.length:null};
    })}))};
  }
  function html(alunas,historico,referencia,esc,inicio){
    const dados=calcular(alunas,historico,referencia,inicio),cores=['#24aeb5','#edb34f','#8196ba','#b77ab0','#6ba674','#c77e58'];
    const br=d=>d.split('-').reverse().join('/');
    return '<section class="turmas-chart"><h3>Avaliação dos principais pontos</h3><p>Registros de aulas sem dificuldades — média simples das alunas em cada turma.</p><div class="analytics-filters"><label>Data inicial<input type="date" data-grafico-inicio value="'+dados.inicio+'"></label><label>Data final<input type="date" data-grafico-fim value="'+dados.fim+'"></label><button type="button" class="primary-action" data-grafico-aplicar>Aplicar período</button></div><p data-grafico-feedback role="status"></p><p class="hint">'+br(dados.inicio)+' a '+br(dados.fim)+' · Cadastro atual das turmas.</p>'+(dados.turmas.length?dados.disciplinas.map(d=>'<div class="turmas-chart-group"><h4>'+esc(d.disciplina)+'</h4><div>'+d.valores.map((v,i)=>'<div class="turmas-chart-row"><span>'+esc(v.turma)+'</span><div class="turmas-chart-track" role="img" aria-label="'+esc(v.turma+': '+(v.percentual===null?'Sem dados':v.percentual.toFixed(1)+'%'))+'"><span style="width:'+(v.percentual||0)+'%;background:'+cores[i%cores.length]+'"></span></div><strong>'+(v.percentual===null?'Sem dados':v.percentual.toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1})+'%')+'</strong></div>').join('')+'</div></div>').join(''):'<p>Nenhuma aluna ativa cadastrada.</p>')+'<div class="turmas-chart-legend">'+dados.turmas.map((t,i)=>'<span><i style="background:'+cores[i%cores.length]+'"></i>'+esc(t)+'</span>').join('')+'</div><p class="hint">Somente a marcação “Não apresentou dificuldades”, sem outras dificuldades juntas, conta como positiva. Avaliações em branco não contam como positivas. Alunas sem registros na disciplina ficam fora da média.</p></section>';
  }
  function conectar(destino,carregar,esc){
    const secao=destino.querySelector('.turmas-chart');if(!secao)return;
    const botao=secao.querySelector('[data-grafico-aplicar]');
    botao.onclick=async()=>{
      const inicio=secao.querySelector('[data-grafico-inicio]').value,fim=secao.querySelector('[data-grafico-fim]').value,retorno=secao.querySelector('[data-grafico-feedback]');
      try{calcular([],[],fim,inicio);}catch(e){retorno.textContent=e.message;return;}
      const campos=secao.querySelectorAll('input,button');campos.forEach(c=>c.disabled=true);retorno.textContent='Atualizando gráfico…';
      try{
        const dados=await carregar();if(!secao.isConnected)return;
        secao.outerHTML=html(dados.alunas,dados.historico,fim,esc,inicio);conectar(destino,carregar,esc);
        destino.querySelector('[data-grafico-feedback]').textContent='Gráfico atualizado para o período escolhido.';
      }catch(e){retorno.textContent='Não foi possível atualizar o gráfico: '+e.message;}
      finally{campos.forEach(c=>c.disabled=false);}
    };
  }
  window.GraficoTurmas={calcular,html,conectar,disciplinaDoRegistro};
})();
