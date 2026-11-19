(function(){
  const disciplinas=['Prática','Teoria','Solfejo','Solfejo Melódico'];
  const normal=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLowerCase();
  const iso=v=>{const s=String(v||'').trim(),m=s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);return m?m[3]+'-'+m[2]+'-'+m[1]:s.slice(0,10);};
  const br=v=>v?iso(v).split('-').reverse().join('/'):'Não informada';
  const percentual=v=>v===null?'Sem dados':v.toLocaleString('pt-BR',{minimumFractionDigits:1,maximumFractionDigits:1})+'%';
  const media=vs=>{const v=vs.filter(x=>x!==null&&Number.isFinite(x));return v.length?v.reduce((s,x)=>s+x,0)/v.length:null;};
  const disciplina=r=>({'pratica':'Prática','teoria':'Teoria','solfejo':'Solfejo','canto':'Solfejo Melódico','solfejo melodico':'Solfejo Melódico'})[normal(String(r.Tipo||'').replace(/^Analise_/,''))];
  function dificuldades(v){if(typeof v==='string'){try{v=JSON.parse(v);}catch(_){v=v.split(/[,;]+/);}}return (Array.isArray(v)?v:[]).map(x=>String(x||'').trim()).filter(x=>x&&!/^(null|nan|\[\])$/i.test(x));}
  const positiva=r=>{const d=dificuldades(r.Dificuldades);return d.length>0&&d.every(v=>/^nao apresentou dificuldades?$/.test(normal(v)));};
  function recorrencias(registros){const mapa=new Map();for(const r of registros)for(const d of new Set(dificuldades(r.Dificuldades).filter(d=>!/^nao apresentou dificuldades?$/.test(normal(d))))){const k=normal(d),v=mapa.get(k)||{nome:d,quantidade:0};v.quantidade++;mapa.set(k,v);}return [...mapa.values()].sort((a,b)=>b.quantidade-a.quantidade||a.nome.localeCompare(b.nome,'pt-BR'));}
  function permanencia(inicio,fim){
    if(!inicio)return 'Ingresso não informado';const a=iso(inicio),b=iso(fim);if(a>b)return 'Ingresso posterior ao período';
    const entrada=new Date(a+'T12:00:00Z'),final=new Date(b+'T12:00:00Z');if(!Number.isFinite(entrada.getTime())||!Number.isFinite(final.getTime()))return 'Ingresso não informado';
    let meses=(final.getUTCFullYear()-entrada.getUTCFullYear())*12+final.getUTCMonth()-entrada.getUTCMonth();
    const marco=n=>{const d=new Date(Date.UTC(entrada.getUTCFullYear(),entrada.getUTCMonth()+n,1,12));const ultimo=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)).getUTCDate();d.setUTCDate(Math.min(entrada.getUTCDate(),ultimo));return d;};
    if(marco(meses)>final)meses--;const dias=Math.round((final-marco(meses))/86400000),anos=Math.floor(meses/12),resto=meses%12;
    return [anos?anos+' ano(s)':'',resto?resto+' mês(es)':'',dias||(!anos&&!resto)?dias+' dia(s)':''].filter(Boolean).join(' ')+' no GEM';
  }
  function construir(dados,{inicio,fim,turma='',gem='GEM Musical'}){
    // Reutiliza os mesmos recortes e chamadas consolidadas do relatório geral.
    const itens=window.RelatorioGeral.construir(dados,{inicio,fim,turma});
    const alunas=itens.map(item=>{
      const aulas=item.registros.filter(r=>disciplina(r));
      const desempenho=disciplinas.map(d=>{const rs=aulas.filter(r=>disciplina(r)===d);return {disciplina:d,total:rs.length,positivos:rs.filter(positiva).length,percentual:rs.length?rs.filter(positiva).length/rs.length*100:null};});
      const f=item.frequencia,total=f.presentes+f.faltas+f.justificadas;
      const ultimos=new Map();aulas.filter(r=>disciplina(r)==='Prática').forEach(r=>{const material=String(r.Licao_Atual||'').split(':')[0]||'Material';ultimos.set(material,r);});
      const pontosFortes=desempenho.filter(d=>d.percentual!==null&&d.percentual>0).sort((a,b)=>b.percentual-a.percentual);
      return {...item,aulas,desempenho,frequenciaPercentual:total?f.presentes/total*100:null,aproveitamento:media(desempenho.map(d=>d.percentual)),dificuldades:recorrencias(aulas),ultimasPraticas:[...ultimos.values()],pontosFortes,tempo:permanencia(item.aluna.data_inicio,fim)};
    }).sort((a,b)=>(a.aluna.turma||'Sem turma').localeCompare(b.aluna.turma||'Sem turma','pt-BR',{numeric:true})||a.aluna.nome.localeCompare(b.aluna.nome,'pt-BR'));
    const turmas=[...new Set(alunas.map(a=>a.aluna.turma||'Sem turma'))].map(nome=>{const grupo=alunas.filter(a=>(a.aluna.turma||'Sem turma')===nome);return {nome,alunas:grupo,frequencia:media(grupo.map(a=>a.frequenciaPercentual)),aproveitamento:media(grupo.map(a=>a.aproveitamento)),dificuldades:recorrencias(grupo.flatMap(a=>a.aulas)),desempenho:disciplinas.map(d=>({disciplina:d,percentual:media(grupo.map(a=>a.desempenho.find(x=>x.disciplina===d).percentual))}))};});
    const alertas=window.AlertasLicoes.calcular(dados.historico,{inicio,fim,alunas:alunas.map(a=>a.aluna.nome)});
    return {gem,inicio,fim,turma,alunas,turmas,alertas,dificuldades:recorrencias(alunas.flatMap(a=>a.aulas)),diasChamados:new Set(alunas.flatMap(a=>a.chamadas.map(r=>iso(r.Data)))).size};
  }
  function textoAluna(a,modelo){
    const f=a.frequencia,alertas=modelo.alertas.filter(r=>r.aluna===a.aluna.nome);
    return [
      {titulo:'CADASTRO',texto:(a.aluna.comum||'Comum não informada')+' | Ingresso: '+br(a.aluna.data_inicio)+' | '+a.tempo},
      {titulo:'FREQUÊNCIA E ESTUDO',texto:'Presenças: '+f.presentes+' | Faltas: '+f.faltas+' | Justificadas: '+f.justificadas+' | Frequência: '+percentual(a.frequenciaPercentual)+'\nAproveitamento: '+percentual(a.aproveitamento)+' | Estudo em casa: '+a.diasEstudo+' de '+a.diasPeriodo+' dias'+(a.chamadas.some(r=>r.falta_inferida)?'\nInclui faltas inferidas das chamadas antigas.':'')},
      {titulo:'DESEMPENHO POR DISCIPLINA',texto:a.desempenho.map(d=>d.disciplina+': '+percentual(d.percentual)+' ('+d.positivos+'/'+d.total+' registros)').join('\n')},
      {titulo:'EVOLUÇÃO / PRÁTICA',texto:(a.ultimasPraticas.length?a.ultimasPraticas.map(r=>br(r.Data)+' | '+r.Licao_Atual+' | '+(r.Status||'Sem resultado')).join('\n'):'Sem registro de Prática no período.')+(a.metodos.length?'\nMétodos concluídos: '+a.metodos.map(m=>m.material+' em '+br(m.fim)+(m.dias!==null?' ('+m.dias+' dias desde o início registrado)':'')).join('; '):'')},
      {titulo:'PONTO FORTE',texto:a.pontosFortes.length?a.pontosFortes.filter(d=>d.percentual===a.pontosFortes[0].percentual).map(d=>d.disciplina+': '+percentual(d.percentual)+' de registros sem dificuldades').join('; '):'Sem marcação positiva suficiente para indicar destaque.'},
      {titulo:'PONTOS DE ATENÇÃO',texto:a.dificuldades.length?a.dificuldades.slice(0,3).map(d=>d.nome+' ('+d.quantidade+' registros)').join('; '):'Sem dificuldades marcadas no período.'},
      {titulo:'LIÇÕES REPETIDAS',texto:alertas.length?alertas.map(r=>r.disciplina+' | '+r.material+': '+r.licao+' | '+r.sabados+' sábados, desde '+br(r.inicio)).join('\n'):'Sem alerta de repetição.'},
      {titulo:'OBSERVAÇÕES REGISTRADAS',texto:a.aulas.filter(r=>r.Observacao).map(r=>br(r.Data)+' | '+disciplina(r)+' | '+(r.Instrutora||'Autoria não informada')+': '+r.Observacao).join('\n')||'Sem observações.'},
      {titulo:'BOLETIM',texto:a.notas.map(n=>br(n.avaliacao.data_avaliacao)+' | '+(n.avaliacao.titulo||'Avaliação')+' | '+n.disciplina+': '+n.nota).join('\n')||'Sem notas datadas no período.'}
    ];
  }
  function preview(m,e){return '<div class="meeting-preview"><header><p>REUNIÃO PEDAGÓGICA</p><h2>'+e(m.gem)+'</h2><p>'+br(m.inicio)+' a '+br(m.fim)+' · '+m.alunas.length+' alunas · '+m.turmas.length+' turmas</p></header>'+m.turmas.map(t=>'<details open><summary>'+e(t.nome)+' · '+t.alunas.length+' alunas · Frequência '+percentual(t.frequencia)+'</summary><div class="meeting-cards">'+t.alunas.map(a=>'<article><h3>'+e(a.aluna.nome)+'</h3>'+textoAluna(a,m).map(b=>'<h4>'+b.titulo+'</h4><p>'+e(b.texto).replace(/\n/g,'<br>')+'</p>').join('')+'</article>').join('')+'</div></details>').join('')+'</div>';}
  function gerarPdf(m,notas,JsPDF,fotos={}){
    const pdf=new JsPDF({orientation:'landscape',unit:'mm',format:[297,167],compress:true});
    const W=297,H=167,navy=[13,25,47],pink=[237,24,113],teal=[27,150,161];let paginaAtual=0;
    const clean=v=>String(v??'').replace(/[\u2010-\u2015]/g,'-').replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu,'').replace(/\u2022/g,' | ');
    const font=(bold=false,size=10,color=navy)=>{pdf.setFont('helvetica',bold?'bold':'normal');pdf.setFontSize(size);pdf.setTextColor(...color);};
    function pagina(titulo,sub=''){if(paginaAtual++)pdf.addPage([W,H],'landscape');pdf.setFillColor(245,247,250);pdf.rect(0,0,W,H,'F');pdf.setFillColor(...navy);pdf.rect(0,0,W,27,'F');pdf.setFillColor(...pink);pdf.rect(9,6,1.5,15,'F');font(true,17,[255,255,255]);pdf.text(clean(titulo),15,14);font(false,9,[220,227,240]);pdf.text(clean(sub),15,22);font(false,8,[100,112,130]);pdf.text(clean(m.gem+' | '+br(m.inicio)+' a '+br(m.fim)),10,162);pdf.text(String(paginaAtual),285,162);}
    function paragrafos(titulo,linhas){pagina(titulo);let y=38;for(const linha of linhas){font(false,11);for(const l of pdf.splitTextToSize(clean(linha),275)){if(y>149){pagina(titulo+' - continuação');y=38;}pdf.text(l,11,y);y+=5.5;}y+=5;}}
    function tabela(titulo,cabecalho,linhas){pagina(titulo);let y=35;const largura=275/cabecalho.length;
      const head=()=>{pdf.setFillColor(...navy);pdf.rect(11,y,275,9,'F');font(true,9,[255,255,255]);cabecalho.forEach((v,i)=>pdf.text(clean(v),14+i*largura,y+6));y+=12;};head();
      for(const row of linhas){font(false,10);const texts=row.map(v=>pdf.splitTextToSize(clean(v),largura-7)),altura=Math.max(...texts.map(t=>t.length))*4.5+5;if(y+altura>151){pagina(titulo+' - continuação');y=35;head();}pdf.setFillColor(255,255,255);pdf.rect(11,y-3,275,altura,'F');font(false,10);texts.forEach((ls,i)=>ls.forEach((l,j)=>pdf.text(l,14+i*largura,y+j*4.5)));y+=altura;}
    }
    pagina('APRESENTAÇÃO PEDAGÓGICA',m.gem);
    font(true,36,navy);pdf.text('GEM | '+m.fim.slice(0,4),15,58);font(true,22,pink);pdf.text('REUNIÃO PEDAGÓGICA',15,77);font(false,15);pdf.text(br(m.inicio)+' a '+br(m.fim),15,94);pdf.text(m.alunas.length+' alunas | '+m.turmas.length+' turmas',15,108);font(false,12);pdf.text('Evolução individual | Frequência | Disciplinas | Dificuldades | Tempo no GEM',15,125);
    paragrafos('CRITÉRIOS DE LEITURA',['Dados do GEM no período selecionado; turmas e situação ativa conforme o cadastro atual.','Aulas sem dificuldades: somente marcação explícita “Não apresentou dificuldades”, sem dificuldades contraditórias. Campo vazio não é positivo. Média simples das alunas com registros.','Frequência: presenças divididas pelas chamadas conhecidas. Faltas justificadas também representam ausência. Sem chamada não se presume falta, exceto a regra identificada para chamadas antigas importadas.','Aproveitamento: média das disciplinas com registros. Estudo em casa: dias distintos informados. Conteúdo alcançado não comprova aprovação. Data de ingresso ausente não é inventada.','Conclusões e encaminhamentos inseridos pela coordenação são identificados e devem ser revisados antes de compartilhar.']);
    const cores=[[36,174,181],[237,179,79],[129,150,186],[183,122,176],[107,166,116]];
    for(let offset=0;offset<m.turmas.length;offset+=4){const ts=m.turmas.slice(offset,offset+4);pagina('AVALIAÇÃO DOS PRINCIPAIS PONTOS','Registros sem dificuldades - média simples das alunas de cada turma');let y=37;for(const d of disciplinas){font(true,11);pdf.text(d,11,y+4);ts.forEach((t,i)=>{const v=t.desempenho.find(x=>x.disciplina===d).percentual;pdf.setFillColor(226,232,239);pdf.rect(72,y+i*5.5,178,3,'F');pdf.setFillColor(...cores[(offset+i)%cores.length]);if(v>0)pdf.rect(72,y+i*5.5,178*v/100,3,'F');font(false,9);pdf.text(percentual(v),255,y+i*5.5+3);});y+=28;}ts.forEach((t,i)=>{font(false,9,cores[(offset+i)%cores.length]);pdf.text(clean(t.nome),15+i*68,151);});}
    tabela('CADASTRO / TEMPO DE PERMANÊNCIA',['Aluna','Turma / Comum','Ingresso','Tempo no GEM'],m.alunas.map(a=>[a.aluna.nome,(a.aluna.turma||'Sem turma')+' / '+(a.aluna.comum||'Não informada'),br(a.aluna.data_inicio),a.tempo]));
    tabela('FREQUÊNCIA POR TURMA',['Turma','Alunas','Frequência média','Aproveitamento'],m.turmas.map(t=>[t.nome,t.alunas.length,percentual(t.frequencia),percentual(t.aproveitamento)]));
    tabela('ACOMPANHAMENTO DA FREQUÊNCIA',['Aluna','Presenças','Faltas','Justificadas'],[...m.alunas].sort((a,b)=>(b.frequencia.faltas+b.frequencia.justificadas)-(a.frequencia.faltas+a.frequencia.justificadas)).map(a=>[a.aluna.nome,a.frequencia.presentes,a.frequencia.faltas,a.frequencia.justificadas]));
    tabela('LEITURA GERAL PEDAGÓGICA',['Dificuldades mais frequentes','Ocorrências nos registros'],m.dificuldades.length?m.dificuldades.map(d=>[d.nome,d.quantidade]):[['Sem dificuldades marcadas','—']]);
    for(const turma of m.turmas){
      pagina(turma.nome.toUpperCase(),turma.alunas.length+' alunas');font(true,26);pdf.text('Frequência média: '+percentual(turma.frequencia),15,62);pdf.text('Aproveitamento: '+percentual(turma.aproveitamento),15,87);
      for(let i=0;i<turma.alunas.length;i+=3){const grupo=turma.alunas.slice(i,i+3);
        const filas=grupo.map(a=>textoAluna(a,m).flatMap(b=>{font(true,9);const tit=pdf.splitTextToSize(clean(b.titulo),80).map(t=>({texto:t,bold:true}));font(false,9);return [...tit,...pdf.splitTextToSize(clean(b.texto),80).map(t=>({texto:t})),{texto:''}];}));
        let continua=false;
        do{pagina(turma.nome.toUpperCase()+' | SÍNTESE DAS ALUNAS'+(continua?' - continuação':''));grupo.forEach((a,j)=>{const x=10+j*94;pdf.setFillColor(255,255,255);pdf.roundedRect(x,32,89,121,4,4,'F');font(true,11);const ns=pdf.splitTextToSize(clean(a.aluna.nome),fotos[a.aluna.nome]?65:81);let y=39;ns.forEach(n=>{pdf.text(n,x+4,y);y+=5;});if(fotos[a.aluna.nome]){try{pdf.addImage(fotos[a.aluna.nome],'JPEG',x+70,34,15,15);}catch(_){}}
          pdf.setDrawColor(...pink);pdf.line(x,y+1,x+89,y+1);y+=7;
          while(filas[j].length&&y<149){if(filas[j][0].bold&&y+8.6>=149)break;const l=filas[j].shift();font(Boolean(l.bold),9,l.bold?teal:navy);pdf.text(l.texto,x+4,y);y+=4.3;}
        });continua=true;}while(filas.some(f=>f.length));
      }
      const melhor=[...turma.desempenho].filter(d=>d.percentual!==null).sort((a,b)=>b.percentual-a.percentual)[0];
      paragrafos(turma.nome.toUpperCase()+' | LEITURA PEDAGÓGICA',['PONTO FORTE: '+(melhor&&melhor.percentual>0?melhor.disciplina+' com '+percentual(melhor.percentual)+' de registros positivos em média.':'Sem evidência positiva suficiente no período.'),'PRINCIPAL ALERTA: '+(turma.dificuldades.slice(0,3).map(d=>d.nome+' ('+d.quantidade+')').join('; ')||'Sem dificuldades marcadas.'),'PRÓXIMO PASSO - COORDENAÇÃO: '+(notas.turmas?.[turma.nome]||'A definir durante a reunião.')]);
    }
    paragrafos('LIÇÕES REPETIDAS - REVISAR',m.alertas.length?m.alertas.map(a=>a.aluna+' | '+a.disciplina+' | '+a.material+': '+a.licao+' | '+a.sabados+' sábados com presença, desde '+br(a.inicio)):['Nenhuma lição atingiu o critério no período.']);
    paragrafos('PRIORIDADES PARA O PRÓXIMO CICLO',[notas.prioridades||'Definir objetivos por turma a partir das dificuldades e pendências apresentadas.']);
    const notasProvas=m.alunas.flatMap(a=>a.notas.map(n=>[a.aluna.nome,br(n.avaliacao.data_avaliacao),n.disciplina,(n.avaliacao.titulo||'Avaliação')+' | Nota: '+n.nota]));
    tabela('AVALIAÇÕES DO PERÍODO',['Aluna','Data','Disciplina','Avaliação / Nota'],notasProvas.length?notasProvas:[['Sem notas datadas no período','','','']]);
    paragrafos('ENCAMINHAMENTOS DA REUNIÃO',[notas.encaminhamentos||'A registrar pela coordenação.']);
    return pdf;
  }
  async function montar(destino,{gem,carregar,autorizar,esc}){
    if(!await autorizar())throw new Error('Acesso disponível para Secretaria e professoras coordenadoras no período de coordenação.');
    const hoje=new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Sao_Paulo'}).format(new Date());
    destino.innerHTML='<section class="intro-card"><h2>Reunião pedagógica</h2><p>Relatório em formato de apresentação, com dados do período e sínteses por turma e aluna.</p></section><section class="panel"><div class="analytics-filters"><label>Data inicial<input type="date" data-reuniao-inicio value="'+hoje.slice(0,4)+'-01-01"></label><label>Data final<input type="date" data-reuniao-fim value="'+hoje+'"></label><label>Turma<select data-reuniao-turma><option value="">Todas as turmas</option></select></label><button type="button" class="primary-action" data-reuniao-gerar>Gerar relatório</button></div><p data-reuniao-status role="status"></p><div data-reuniao-editor></div><div data-reuniao-previa></div></section>';
    let dados=null,rascunho={turmas:{},prioridades:'',encaminhamentos:''};
    const retorno=destino.querySelector('[data-reuniao-status]'),botao=destino.querySelector('[data-reuniao-gerar]');
    const lerNotas=()=>{
      for(const el of destino.querySelectorAll('[data-reuniao-nota-turma]'))rascunho.turmas[el.dataset.reuniaoNotaTurma]=el.value;
      for(const nome of ['prioridades','encaminhamentos']){const el=destino.querySelector('[data-reuniao-'+nome+']');if(el)rascunho[nome]=el.value;}
      return rascunho;
    };
    botao.disabled=true;
    try{
      dados=await carregar();if(!destino.isConnected)return;
      const turmas=[...new Set(dados.alunas.filter(a=>a.ativo!==false).map(a=>a.turma).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pt-BR',{numeric:true}));
      destino.querySelector('[data-reuniao-turma]').innerHTML+=turmas.map(t=>'<option value="'+esc(t)+'">'+esc(t)+'</option>').join('');
    }catch(e){retorno.textContent='Não foi possível carregar os dados: '+e.message;return;}
    finally{botao.disabled=false;}
    botao.onclick=async()=>{
      botao.disabled=true;retorno.textContent='Preparando relatório…';
      try{
        if(!await autorizar())throw new Error('A coordenação não está ativa para este acesso.');
        if(dados.erroBoletim)throw new Error('Não foi possível carregar todas as notas: '+dados.erroBoletim);
        const filtros={gem,inicio:destino.querySelector('[data-reuniao-inicio]').value,fim:destino.querySelector('[data-reuniao-fim]').value,turma:destino.querySelector('[data-reuniao-turma]').value};
        window.GraficoTurmas.calcular([],[],filtros.fim,filtros.inicio);
        const modelo=construir(dados,filtros);lerNotas();
        if(!modelo.alunas.length)throw new Error('Nenhuma aluna ativa encontrada nesse filtro.');
        const editor=destino.querySelector('[data-reuniao-editor]');
        editor.innerHTML='<h3>Conclusões da coordenação</h3><p class="hint">Estes textos entram no PDF. Ficam nesta tela enquanto ela estiver aberta; não são gravados no cadastro das alunas.</p>'+modelo.turmas.map(t=>'<label>Próximo passo — '+esc(t.nome)+'<textarea data-reuniao-nota-turma="'+esc(t.nome)+'" placeholder="Objetivos e ações combinados">'+esc(rascunho.turmas[t.nome]||'')+'</textarea></label>').join('')+'<label>Prioridades para o próximo ciclo<textarea data-reuniao-prioridades>'+esc(rascunho.prioridades)+'</textarea></label><label>Encaminhamentos e observações da reunião<textarea data-reuniao-encaminhamentos>'+esc(rascunho.encaminhamentos)+'</textarea></label><label class="checkbox-line"><input type="checkbox" data-reuniao-fotos checked> Incluir fotos de perfil disponíveis</label><button type="button" class="primary-action" data-reuniao-pdf>Baixar PDF da reunião</button><p data-reuniao-download role="status"></p>';
        destino.querySelector('[data-reuniao-previa]').innerHTML=preview(modelo,esc);
        retorno.textContent='Relatório gerado: '+br(modelo.inicio)+' a '+br(modelo.fim)+'. Revise os dados e as conclusões antes de baixar.';
        editor.querySelector('[data-reuniao-pdf]').onclick=async()=>{
          const baixar=editor.querySelector('[data-reuniao-pdf]'),msg=editor.querySelector('[data-reuniao-download]');baixar.disabled=true;msg.textContent='Gerando PDF…';
          try{
            if(!await autorizar())throw new Error('Acesso de coordenação não está mais ativo.');
            if(!window.jspdf?.jsPDF)throw new Error('A ferramenta de PDF ainda está carregando. Tente novamente.');
            const notas=JSON.parse(JSON.stringify(lerNotas())),fotos={};let falhasFotos=0;
            if(editor.querySelector('[data-reuniao-fotos]').checked){
              try{
                const perfis=await window.GemData.fotosPessoas();
                for(const a of modelo.alunas){const url=perfis.aluna?.[a.aluna.nome];if(!url)continue;
                  try{const resposta=await fetch(url,{credentials:'same-origin'});if(!resposta.ok)throw new Error('Foto indisponível');const bmp=await createImageBitmap(await resposta.blob());const canvas=document.createElement('canvas');canvas.width=canvas.height=150;const ctx=canvas.getContext('2d');ctx.fillStyle='#fff';ctx.fillRect(0,0,150,150);const lado=Math.min(bmp.width,bmp.height);ctx.drawImage(bmp,(bmp.width-lado)/2,(bmp.height-lado)/2,lado,lado,0,0,150,150);bmp.close();fotos[a.aluna.nome]=canvas.toDataURL('image/jpeg',.85);}catch(_){falhasFotos++;}
                }
                if(perfis.erros?.length)falhasFotos+=perfis.erros.length;
              }catch(_){falhasFotos++;}
            }
            const pdf=gerarPdf(modelo,notas,window.jspdf.jsPDF,fotos);pdf.save('Reuniao_pedagogica_'+modelo.inicio+'_'+modelo.fim+'.pdf');
            msg.textContent='PDF gerado. Download iniciado.'+(falhasFotos?' Algumas fotos não puderam ser incluídas; os dados foram preservados.':'');
          }catch(e){msg.textContent='Não foi possível gerar o PDF: '+e.message;}finally{baixar.disabled=false;}
        };
      }catch(e){retorno.textContent=e.message;}finally{botao.disabled=false;}
    };
    destino.querySelectorAll('[data-reuniao-inicio],[data-reuniao-fim],[data-reuniao-turma]').forEach(el=>el.addEventListener('change',()=>{const pdf=destino.querySelector('[data-reuniao-pdf]');if(pdf)pdf.disabled=true;retorno.textContent='Filtros alterados. Clique em Gerar relatório para aplicar antes de baixar.';}));
    await botao.onclick();
  }
  window.ReuniaoPedagogica={construir,gerarPdf,preview,textoAluna,permanencia,montar};
})();
