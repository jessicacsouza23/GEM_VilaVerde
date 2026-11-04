(function () {
  const esc = s => String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function nomeMaterial(valor) {
    const nome = String(valor || '').trim();
    const chave = nome.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ');
    return /^meu piano e divertido(?:\s+1)?$/.test(chave) ? 'Meu piano é divertido 1' : nome;
  }
  function normalizarRegistro(r) {
    const registro = {...r};
    if (registro.Tipo === 'Material_Prática') registro.Licao_Atual = nomeMaterial(registro.Licao_Atual);
    if (registro.Tipo === 'Analise_Prática') {
      const texto = String(registro.Licao_Atual || ''), pos = texto.indexOf(':');
      if (pos >= 0) registro.Licao_Atual = nomeMaterial(texto.slice(0,pos)) + texto.slice(pos);
    }
    if (String(registro.Tipo || '').startsWith('Casa_Metodo_')) registro.Tipo = 'Casa_Metodo_' + nomeMaterial(registro.Tipo.slice(12));
    return registro;
  }
  function catalogo(historico) {
    const itens = new Map();
    for (const r of historico.map(normalizarRegistro).sort((a,b) => Number(a.id) - Number(b.id))) {
      const nome = r.Tipo === 'Material_Prática' ? r.Licao_Atual : r.Tipo === 'Analise_Prática' ? String(r.Licao_Atual || '').split(':')[0].trim() : String(r.Tipo || '').startsWith('Casa_Metodo_') ? r.Tipo.slice(12) : ['Casa_Apostila','Casa_Apostila_Prof'].includes(r.Tipo) ? 'Apostila' : '';
      if (!nome) continue;
      if (!itens.has(nome)) itens.set(nome, {nome, concluido:false});
      if (r.Tipo === 'Material_Prática') itens.set(nome, {nome, concluido:r.Status === 'Concluído', data:r.Data, professora:r.Instrutora});
    }
    return [...itens.values()];
  }
  async function montar({area, opcoes, historico, adicionar, linhaCasa, conectarCasas, salvarEstado}) {
    const container = area.querySelector('#materiais-pratica');
    const casas = area.querySelector('#licoes-casa-pratica');
    const adicionarBotao = area.querySelector('#adicionar-material-pratica');
    const existentes = [...container.querySelectorAll('.practice-material-card')];
    opcoes = [...new Set(opcoes.map(nomeMaterial))];
    const registros = catalogo(historico);
    const grupos = new Map();
    const topo = document.createElement('section');
    topo.className = 'materials-picker';
    topo.innerHTML = '<h4>Materiais da aluna</h4><p>Escolha um material por vez e salve o registro dele. Ao trocar, o preenchimento fica guardado enquanto esta tela estiver aberta. Os registros já salvos são preservados.</p><div data-escolhas></div><div class="material-add"><label>Adicionar material<select data-novo><option value="">Escolha na biblioteca</option>' + opcoes.map(m => '<option>' + esc(m) + '</option>').join('') + '</select></label><button type="button" class="secondary-action" data-incluir>＋ Adicionar material</button></div><p data-feedback role="status"></p><details data-concluidos><summary>Métodos concluídos</summary><div></div></details>';
    container.before(topo);
    adicionarBotao.hidden = true;
    casas.hidden = true;
    const feedback = topo.querySelector('[data-feedback]');
    function abrir(grupo) {
      for (const g of grupos.values()) g.bloco.open = g === grupo;
    }
    function resumo(g) {
      const textos = [...g.bloco.querySelectorAll('[data-pratica-conteudo]')].map(c => c.value.trim()).filter(Boolean);
      const tarefas = [...g.bloco.querySelectorAll('[data-casa-conteudo]')].map(c => c.value.trim()).filter(Boolean);
      g.resumo.textContent = (g.check.checked ? 'Hoje: ' + (textos.join('; ') || 'preencher conteúdo') : 'Não trabalhado hoje') + ' · Para casa: ' + (tarefas.join('; ') || 'sem nova lição');
    }
    async function incluir(nome, selecionado, estado = {}) {
      if (grupos.has(nome)) {const g=grupos.get(nome);g.check.checked=true;g.check.dispatchEvent(new Event('change'));return g;}
      const label=document.createElement('label');label.className='material-choice';
      const check=document.createElement('input');check.type='radio';check.name='material-em-edicao';check.checked=selecionado;
      label.append(check,document.createTextNode(nome));topo.querySelector('[data-escolhas]').append(label);
      const bloco=document.createElement('details');bloco.className='material-workspace';bloco.dataset.material=nome;
      bloco.innerHTML='<summary><strong>'+esc(nome)+'</strong><span data-resumo></span></summary><div data-aula></div><section class="material-homework"><h4>Para a próxima aula</h4><p>Deixe vazio para não passar nova lição deste material.</p><div data-tarefas></div><button type="button" class="secondary-action" data-mais-casa>＋ Outra lição de casa</button></section><button type="button" class="secondary-action" data-estado></button>';
      container.append(bloco);
      const g={nome,check,label,bloco,resumo:bloco.querySelector('[data-resumo]'),estado};grupos.set(nome,g);
      let cards=existentes.filter(c=>c.querySelector('[data-pratica-material]').value===nome);
      if(!cards.length){await adicionar({material:nome});cards=[container.lastElementChild];}
      for(const card of cards){bloco.querySelector('[data-aula]').append(card);card.querySelector('[data-pratica-material]').disabled=true;card.querySelector('.remover-material').hidden=true;card.querySelector('[data-pratica-conteudo]').required=true;}
      let rows=[...casas.querySelectorAll('[data-casa-item]')].filter(r=>r.querySelector('[data-casa-material]').value===nome);
      function anexar(row){bloco.querySelector('[data-tarefas]').append(row);row.querySelector('[data-casa-material]').disabled=true;conectarCasas(bloco);}
      if(!rows.length){const host=document.createElement('div');host.innerHTML=linhaCasa({material:nome});rows=[host.firstElementChild];}
      rows.forEach(anexar);
      bloco.querySelector('[data-mais-casa]').onclick=()=>{const host=document.createElement('div');host.innerHTML=linhaCasa({material:nome});anexar(host.firstElementChild);};
      const atualizar=()=>{for(const outro of grupos.values()){outro.bloco.querySelectorAll('.practice-material-card,[data-casa-item]').forEach(el=>el.dataset.ignorarMaterial=outro.check.checked?'false':'true');outro.bloco.hidden=!outro.check.checked;resumo(outro);}if(check.checked)abrir(g);};
      check.onchange=atualizar;bloco.addEventListener('input',()=>resumo(g));bloco.addEventListener('change',()=>resumo(g));
      bloco.addEventListener('toggle',()=>{if(bloco.open)for(const outro of grupos.values())if(outro!==g)outro.bloco.open=false;});
      const estadoBotao=bloco.querySelector('[data-estado]');
      function mostrarEstado(){estadoBotao.textContent=g.estado.concluido?'Reativar método':'Concluir método';}
      estadoBotao.onclick=async()=>{
        if(!confirm(g.estado.concluido?'Reativar '+nome+'?':'Concluir '+nome+'? Salve primeiro o registro desta aula. O histórico será preservado.'))return;
        estadoBotao.disabled=true;
        try{await salvarEstado(nome,!g.estado.concluido);g.estado.concluido=!g.estado.concluido;mostrarEstado();feedback.textContent=nome+(g.estado.concluido?' concluído.':' reativado.');if(g.estado.concluido){check.checked=false;atualizar();}atualizarConcluidos();}
        catch(e){feedback.textContent=e.message;}finally{estadoBotao.disabled=false;}
      };
      mostrarEstado();atualizar();return g;
    }
    function atualizarConcluidos(){
      const lista=topo.querySelector('[data-concluidos] > div');lista.replaceChildren();
      for(const g of grupos.values()){
        g.label.hidden=g.estado.concluido;
        if(!g.estado.concluido)continue;
        const b=document.createElement('button');b.type='button';b.className='secondary-action';b.textContent=g.nome+(g.estado.data?' · '+g.estado.data:'')+(g.estado.professora?' · '+g.estado.professora:'')+' — Reativar';b.onclick=()=>g.bloco.querySelector('[data-estado]').click();lista.append(b);
      }
      if(!lista.children.length)lista.textContent='Nenhum método concluído.';
    }
    for(const card of existentes){const nome=card.querySelector('[data-pratica-material]').value;if(nome&&!registros.some(r=>r.nome===nome))registros.push({nome});if(!nome)card.remove();}
    if(!registros.length)registros.push({nome:'Apostila'});
    for(const r of registros){if(!opcoes.includes(r.nome))opcoes.push(r.nome);await incluir(r.nome,existentes.some(c=>c.querySelector('[data-pratica-material]').value===r.nome),r);}
    atualizarConcluidos();
    topo.querySelector('[data-incluir]').onclick=async()=>{
      const nome=topo.querySelector('[data-novo]').value;if(!nome){feedback.textContent='Escolha o material para adicionar.';return;}
      const botao=topo.querySelector('[data-incluir]');botao.disabled=true;
      try{await salvarEstado(nome,false);const g=await incluir(nome,true);g.estado.concluido=false;g.label.hidden=false;atualizarConcluidos();feedback.textContent=nome+' adicionado aos materiais da aluna.';}
      catch(e){feedback.textContent=e.message;}finally{botao.disabled=false;}
    };
    area.querySelector('#salvar-registro-aula').textContent='Salvar registro deste material';
    area.querySelector('#salvar-registro-aula').addEventListener('click', event => {
      const selecionados=[...grupos.values()].filter(g=>g.check.checked);
      if(!selecionados.length){feedback.textContent='Marque pelo menos um material trabalhado hoje.';event.stopImmediatePropagation();return;}
      for(const g of selecionados){
        const vazio=[...g.bloco.querySelectorAll('[data-pratica-conteudo]')].find(c=>!c.value.trim());
        if(vazio){abrir(g);feedback.textContent=g.nome+': informe o conteúdo trabalhado hoje.';vazio.focus();vazio.reportValidity();event.stopImmediatePropagation();return;}
        if(g.nome==='Apostila')for(const campo of g.bloco.querySelectorAll('[data-pratica-conteudo]')){
          const texto=campo.value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
          const pagina=/\b(?:paginas?|pags?|p)\.?\s*[:\-]?\s*[1-9]\d*\b/.test(texto);
          const licao=/\b(?:licao|licoes|exercicio|exercicios|atividades?)\s*[:\-]?\s*\S+/.test(texto);
          if(!pagina||!licao){abrir(g);feedback.textContent='Apostila: informe '+(!pagina?'a página':'as lições ou exercícios')+'. Ex.: página 18, lições 1 e 2.';campo.focus();event.stopImmediatePropagation();return;}
        }
      }
    }, true);
  }
  window.GemMateriais={catalogo,montar,nomeMaterial,normalizarRegistro};
})();
