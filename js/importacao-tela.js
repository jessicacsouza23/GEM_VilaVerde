(function(){
async function montar(destino){
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const api=window.ImportacaoHistorico;
 destino.innerHTML='<h3>Importar registros antigos</h3><p>Envie uma planilha por vez. Datas permitidas: de 01/01/2025 até hoje. Solfejo antigo entra como Solfejo; lições para casa ficam apenas no histórico. A chamada importa somente presenças e justificativas explícitas.</p><label>Planilha do Forms (.xlsx)<input type="file" accept=".xlsx" data-arquivo></label><label>Aba da planilha<select data-aba></select></label><button type="button" class="secondary-action" data-ler>Carregar prévia</button><p role="status" data-retorno></p><div data-revisao></div>';
 const q=s=>destino.querySelector(s),feedback=q('[data-retorno]');let workbook,arquivo,itens=[],base,mapeamento={},pagina=0,ocupado=false;
 q('[data-arquivo]').onchange=async()=>{
   workbook=null;q('[data-revisao]').innerHTML='';q('[data-aba]').innerHTML='';
   try{arquivo=q('[data-arquivo]').files[0];if(!arquivo)return;if(arquivo.size>20*1024*1024)throw new Error('Use um arquivo de até 20 MB.');if(!window.XLSX)throw new Error('A ferramenta de Excel não carregou. Atualize a página.');workbook=window.XLSX.read(await arquivo.arrayBuffer(),{type:'array',cellDates:false});q('[data-aba]').innerHTML=workbook.SheetNames.map(n=>'<option>'+esc(n)+'</option>').join('');feedback.textContent='Arquivo lido. Clique em Carregar prévia.';}catch(e){feedback.textContent=e.message;}
 };
 q('[data-aba]').onchange=()=>{q('[data-revisao]').innerHTML='';};
 q('[data-ler]').onclick=async()=>{
   if(ocupado)return;ocupado=true;q('[data-ler]').disabled=true;
   try{if(!workbook)throw new Error('Selecione uma planilha primeiro.');feedback.textContent='Conferindo planilha e histórico do GEM...';base=await window.GemData.dadosImportacaoHistorico();const aba=q('[data-aba]').value;
     const linhas=window.XLSX.utils.sheet_to_json(workbook.Sheets[aba],{header:1,raw:true,defval:''});
     const resultado=api.ler(linhas,arquivo.name,aba);itens=resultado.itens;
     for(const item of itens)item.chave=await api.chave(item);
     mapeamento={};for(const nome of new Set(itens.map(i=>i.nome))){const matches=base.alunas.filter(a=>api.norm(a.nome)===api.norm(nome));mapeamento[nome]=matches.length===1?matches[0].nome:'';}
     pagina=0;feedback.textContent='Modelo reconhecido: '+resultado.modelo+'. '+itens.length+' registros encontrados. Confira os vínculos, datas e conteúdos.';desenhar();
   }catch(e){feedback.textContent=e.message;}finally{ocupado=false;q('[data-ler]').disabled=false;}
 };
 function desenhar(){
  const r=q('[data-revisao]');r.innerHTML='<details open><summary>1. Vincular nomes da planilha às alunas cadastradas</summary><p>Nomes diferentes precisam ser escolhidos manualmente. Alunas inativas também podem receber histórico antigo.</p><div data-vinculos></div></details><h4>2. Conferir registros</h4><p>Desmarque os registros que não deseja importar. Datas fora de sábado são sinalizadas para conferência. Campos vazios são preservados, sem presumir que não houve dificuldades.</p><div data-resumo></div><div class="table-wrap"><table class="scale-table"><thead><tr><th>Importar</th><th>Origem / aluna</th><th>Data da aula</th><th>Registro completo</th><th>Conferência</th></tr></thead><tbody data-linhas></tbody></table></div><div class="scale-actions"><button type="button" data-anterior>Anterior</button><span data-pagina></span><button type="button" data-proxima>Próxima</button></div><label class="checkbox-line"><input type="checkbox" data-confirmar>Revisei os registros selecionados e os vínculos das alunas.</label><button type="button" class="primary-action" data-salvar>Importar selecionados válidos</button>';
  const nomes=Object.keys(mapeamento);q('[data-vinculos]').innerHTML=nomes.map((nome,i)=>'<label>'+esc(nome||'Nome ausente na planilha')+'<select data-vinculo="'+i+'"><option value="">Escolha a aluna</option>'+base.alunas.map(a=>'<option value="'+esc(a.nome)+'" '+(a.nome===mapeamento[nome]?'selected':'')+'>'+esc(a.nome)+(a.ativo===false?' (inativa)':'')+'</option>').join('')+'</select></label>').join('');
  r.querySelectorAll('[data-vinculo]').forEach(el=>el.onchange=()=>{mapeamento[nomes[Number(el.dataset.vinculo)]]=el.value;atualizar();});
  q('[data-anterior]').onclick=()=>{pagina--;atualizar();};q('[data-proxima]').onclick=()=>{pagina++;atualizar();};
  q('[data-salvar]').onclick=async()=>{
   if(ocupado)return;
   if(!q('[data-confirmar]').checked){feedback.textContent='Marque a confirmação após revisar a prévia.';return;}
   const validos=api.preparar(itens,mapeamento,base.historico).filter(p=>!p.erro&&!p.item.excluir).map(p=>p.item);
   if(!validos.length){feedback.textContent='Não há registros válidos selecionados.';return;}
   ocupado=true;destino.querySelectorAll('button,input,select').forEach(c=>c.disabled=true);
   try{const n=await window.GemData.importarHistoricoAntigo(validos,mapeamento);feedback.textContent=n+' registros importados com sucesso. Eles já estão disponíveis no histórico e relatórios.';base=await window.GemData.dadosImportacaoHistorico();}
   catch(e){feedback.textContent=e.message;}
   finally{ocupado=false;destino.querySelectorAll('button,input,select').forEach(c=>c.disabled=false);atualizar();}
  };
  atualizar();
 }
 function atualizar(){
  q('[data-confirmar]').checked=false;
  const preparados=api.preparar(itens,mapeamento,base.historico),validos=preparados.filter(p=>!p.erro&&!p.item.excluir).length;
  q('[data-resumo]').textContent=validos+' selecionados válidos · '+preparados.filter(p=>p.erro).length+' com pendência ou duplicidade · '+itens.filter(i=>i.excluir).length+' desmarcados.';
  const total=Math.max(1,Math.ceil(itens.length/40));pagina=Math.min(Math.max(0,pagina),total-1);q('[data-pagina]').textContent='Página '+(pagina+1)+' de '+total;q('[data-anterior]').disabled=pagina===0;q('[data-proxima]').disabled=pagina===total-1;
  q('[data-linhas]').innerHTML=preparados.slice(pagina*40,pagina*40+40).map((p,j)=>{const i=pagina*40+j,x=p.item;return '<tr><td><input aria-label="Selecionar registro" type="checkbox" data-usar="'+i+'" '+(!x.excluir?'checked':'')+'></td><td>Linha '+x.linha+'<br>'+esc(x.nome)+'<br><strong>'+esc(p.registro.Aluna||'Vínculo pendente')+'</strong></td><td><input aria-label="Data da aula" type="date" min="2025-01-01" data-data="'+i+'" value="'+esc(x.data)+'"><small>Original: '+esc(x.dataOriginal||'vazia')+'</small></td><td>'+esc(x.tipo)+' · '+esc(x.instrutora)+'<details><summary>Ver conteúdo</summary><p style="white-space:pre-wrap">'+esc([x.conteudo,x.casa&&'Para casa na época: '+x.casa,x.dificuldades.join(' · '),x.obs,x.status].filter(Boolean).join('\n'))+'</p></details></td><td>'+esc(p.erro||((new Date(x.data+'T12:00:00Z')).getUTCDay()!==6?'Data fora de sábado: confira antes de importar.':'Pronto para importar'))+'</td></tr>';}).join('');
  q('[data-linhas]').querySelectorAll('[data-usar]').forEach(el=>el.onchange=()=>{itens[el.dataset.usar].excluir=!el.checked;atualizar();});
  q('[data-linhas]').querySelectorAll('[data-data]').forEach(el=>el.onchange=()=>{const item=itens[el.dataset.data];for(const outro of itens)if(outro.original===item.original)outro.data=el.value;atualizar();});
 }
}
window.ImportacaoTela={montar};
})();
