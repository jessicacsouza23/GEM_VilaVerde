(function(){
const norm=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
const texto=v=>String(v??'').trim();
function dataISO(v){
 if(typeof v==='number'&&Number.isFinite(v)){const d=new Date(Date.UTC(1899,11,30)+Math.floor(v)*86400000);return Number.isFinite(d.getTime())?d.toISOString().slice(0,10):'';}
 let s=texto(v),m=s.match(/^(\d{4})-(\d{2})-(\d{2})/);
 if(!m){const b=s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);if(b)m=[s,b[3],b[2],b[1]];}
 if(!m)return '';s=m[1]+'-'+m[2]+'-'+m[3];
 const d=new Date(s+'T12:00:00Z');return Number.isFinite(d.getTime())&&d.toISOString().slice(0,10)===s?s:'';
}
const hoje=()=>new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Sao_Paulo'}).format(new Date());
const validaData=d=>Boolean(dataISO(d)&&d>='2025-01-01'&&d<=hoje());
function ler(linhas,arquivo,aba){
 if(!linhas.length)throw new Error('Planilha vazia.');
 const h=linhas[0].map(norm);const tem=n=>h.includes(norm(n));
 const modelo=tem('Alunas presentes')?'presenca':tem('Realizadas - sem pendência')?'correcao':tem('Avaliação de aula')?'teoria':tem('Tipo da Aula')?'semestre':tem('Lição de casa - Volume prática')?'pratica':'';
 if(!modelo)throw new Error('Modelo não reconhecido na aba '+aba+'. Escolha uma aba de respostas do Forms.');
 const saida=[];
 linhas.slice(1).forEach((r,i)=>{
 if(!r.some(v=>texto(v)))return;
 const get=n=>texto(r[h.indexOf(norm(n))]);
 const original=JSON.stringify([modelo,r.map(texto)]);
 const base={arquivo,aba,linha:i+2,modelo,data:dataISO(r[h.indexOf(norm('Data da aula'))]),dataOriginal:dataISO(r[h.indexOf(norm('Data da aula'))])||get('Data da aula'),instrutora:get('Instrutora')||get('Secretária'),carimbo:get('Carimbo de data/hora'),original};
 const nomes=v=>texto(v).split(',').map(texto).filter(Boolean);
 const add=(nomesLista,tipo,conteudo,casa,dificuldades,obs,status='',parte='')=>{
 const ns=[...new Set(nomesLista)];if(!ns.length)ns.push('');
 ns.forEach(nome=>saida.push({...base,nome,tipo,conteudo,casa,dificuldades: texto(dificuldades)?texto(dificuldades).split(/,\s*(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])/).map(texto):[],obs,status,parte,excluir:false}));
 };
 if(modelo==='presenca'){
 add(nomes(get('Alunas presentes')),'Chamada','','','','','Presente','presentes');
 if(get('Faltas justificadas'))add(nomes(get('Faltas justificadas')),'Chamada','','','','','Justificada','justificadas');return;
 }
 if(modelo==='correcao'){
 const cat=get('Categoria');let achou=false;
 for(const campo of ['Realizadas - sem pendência','Realizada - devolvida para refazer','Não realizada'])if(get(campo)){achou=true;add(nomes(get('Aluna')),'Correcao_Historica',cat+': '+get(campo),'','',get('Observações'),campo,campo);}
 if(!achou)add(nomes(get('Aluna')),'Correcao_Historica',cat,'','',get('Observações'),'Resultado não informado','sem-resultado');return;
 }
 if(modelo==='teoria'){
 const ns=['Aluna','Aluna 2','Aluna 3'].flatMap(c=>nomes(get(c)));
 for(const [suf,disc] of [['','Solfejo'],[' 2','Teoria']]){
 const campos=['Lição/Volume','Lição de casa','Dificuldades','Observações'].map(c=>get(c+suf));
 if(campos.some(Boolean))add(ns,'Analise_'+disc,campos[0],campos[1],campos[2],campos[3]+'\nAula realizada em grupo. '+get('Turma'),'','bloco'+suf);
 }
 return;
 }
 const disc=modelo==='pratica'?'Prática':get('Tipo da Aula');
 const casa=modelo==='pratica'?[get('Lição de casa - Volume prática')&&'Método: '+get('Lição de casa - Volume prática'),get('Lição de casa - Apostila')&&'Apostila: '+get('Lição de casa - Apostila')].filter(Boolean).join('\n'):get('Lição de casa');
 add(nomes(get('Aluna')),'Analise_'+disc,get('Lição/Volume'),casa,get('Dificuldades'),get('Observações')||get('Observação'));
 });
 return {modelo,itens:saida};
}
async function chave(item){const bytes=new TextEncoder().encode(item.original+'|'+item.nome+'|'+item.tipo+'|'+item.parte);return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');}
function preparar(itens,mapeamento,historico){
 const keys=new Set(historico.map(r=>r.importacao_chave).filter(Boolean)), vistos=new Set();
 return itens.map(item=>{
 const aluna=mapeamento[item.nome]||'', d=item.data;
 let erro=!validaData(d)?'Confira a data: de 01/01/2025 até hoje.':!aluna?'Vincule a aluna ao cadastro.':!['Chamada','Correcao_Historica','Analise_Prática','Analise_Teoria','Analise_Solfejo'].includes(item.tipo)?'Disciplina não reconhecida.':'';
 const br=d?d.split('-').reverse().join('/'):'';
 if(!erro&&(keys.has(item.chave)||vistos.has(item.chave)))erro='Resposta já importada ou repetida neste arquivo.';
 if(!erro&&historico.some(r=>r.Aluna===aluna&&dataISO(r.Data)===d&&(r.Tipo===item.tipo||r.Tipo===item.tipo.replace('Analise_',''))))erro='Já existe registro da aluna nesta data e disciplina. Confira em Ajustes.';
 if(!erro&&item.tipo==='Chamada'&&itens.some(outro=>outro!==item&&outro.data===d&&(mapeamento[outro.nome]||'')===aluna&&outro.status!==item.status))erro='Presença e justificativa conflitantes para esta data.';
 vistos.add(item.chave);
 const obs=[item.obs,'Importação histórica — '+item.arquivo+' / '+item.aba+' / linha '+item.linha,item.carimbo&&'Resposta do Forms: '+item.carimbo,item.casa&&'Lição para casa na época (somente histórico): '+item.casa].filter(Boolean).join('\n');
 return {item,erro,registro:{Aluna:aluna,Data:br,Tipo:item.tipo,Instrutora:item.instrutora,Licao_Atual:item.conteudo,Licao_Casa:item.casa,Dificuldades:item.dificuldades,Observacao:obs,Status:item.status,importacao_chave:item.chave}};
 });
}
window.ImportacaoHistorico={ler,chave,preparar,dataISO,validaData,norm};
})();
