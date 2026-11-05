(function () {
  const normal = v => String(v || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLowerCase().replace(/\s+/g,' ');
  function dataIso(v) {
    const texto=String(v||'').trim(),br=texto.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    const iso=br?`${br[3]}-${br[2]}-${br[1]}`:texto.slice(0,10);
    if(!/^\d{4}-\d{2}-\d{2}$/.test(iso))return '';
    const d=new Date(iso+'T12:00:00Z');
    return Number.isFinite(d.getTime())&&d.toISOString().slice(0,10)===iso?iso:'';
  }
  function calcular(historico,{inicio,fim,alunas}) {
    const nomes=new Set(alunas), chamadas=new Map(), grupos=new Map();
    const registros=[...historico].filter(r=>nomes.has(r.Aluna)&&dataIso(r.Data)&&dataIso(r.Data)<=fim).sort((a,b)=>Number(a.id||0)-Number(b.id||0));
    for(const r of registros)if(r.Tipo==='Chamada')chamadas.set(JSON.stringify([r.Aluna,dataIso(r.Data)]),normal(r.Status));
    for(const r of registros){
      const dia=dataIso(r.Data);
      if(new Date(dia+'T12:00:00Z').getUTCDay()!==6||chamadas.get(JSON.stringify([r.Aluna,dia]))!=='presente')continue;
      const disciplina=({pratica:'Prática',teoria:'Teoria',solfejo:'Solfejo','solfejo melodico':'Solfejo Melódico',canto:'Solfejo Melódico'})[normal(String(r.Tipo||'').replace(/^Analise_/,''))];
      if(!disciplina)continue;
      const texto=String(r.Licao_Atual||'').trim(),p=texto.indexOf(':');
      let material=p>=0?texto.slice(0,p).trim():'Material não informado';
      const licao=p>=0?texto.slice(p+1).trim():texto;
      if(!licao)continue;
      if(/^meu piano e divertido(?: 1)?$/.test(normal(material)))material='Meu piano é divertido 1';
      const chave=JSON.stringify([r.Aluna,disciplina,normal(material)]);
      if(!grupos.has(chave))grupos.set(chave,{aluna:r.Aluna,disciplina,material,dias:new Map()});
      const g=grupos.get(chave);if(!g.dias.has(dia))g.dias.set(dia,new Map());
      g.dias.get(dia).set(normal(licao),{licao,registro:r});
    }
    const resultado=[];
    for(const g of grupos.values()){
      let sequencias=new Map();
      for(const [dia,itens] of [...g.dias].sort(([a],[b])=>a.localeCompare(b))){
        const proximas=new Map();
        for(const [chave,{licao,registro:r}] of itens){
          const status=normal(r.Status),obs=normal(r.Observacao),dif=normal(Array.isArray(r.Dificuldades)?r.Dificuldades.join(';'):r.Dificuldades);
          const concluiu=['resolvido','passou','realizada - sem pendencia','realizadas - sem pendencia'].includes(status)
            || /correcao da licao:\s*(?:passou|resolvido)\s*—/.test(obs)
            || (dif.includes('nao apresentou dificuldades')&&!dif.replace(/[\[\]"']/g,'').split(/[;,]/).some(d=>d.trim()&&!d.includes('nao apresentou dificuldades')));
          if(concluiu)continue;
          const anterior=sequencias.get(chave);
          proximas.set(chave,{licao,datas:[...(anterior?.datas||[]),dia]});
        }
        sequencias=proximas;
      }
      for(const seq of sequencias.values())if(seq.datas.length>=3&&seq.datas.at(-1)>=inicio)resultado.push({aluna:g.aluna,disciplina:g.disciplina,material:g.material,licao:seq.licao,inicio:seq.datas[0],ultima:seq.datas.at(-1),sabados:seq.datas.length,datas:seq.datas});
    }
    return resultado.sort((a,b)=>a.disciplina.localeCompare(b.disciplina)||a.aluna.localeCompare(b.aluna));
  }
  window.AlertasLicoes={calcular};
})();
