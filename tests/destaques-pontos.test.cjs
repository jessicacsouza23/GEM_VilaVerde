const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const s=fs.readFileSync(require.resolve('../app.js'),'utf8'),ctx={escapeHtml:String};vm.createContext(ctx);vm.runInContext(s.slice(s.indexOf('function destaquesGemMarkup('),s.indexOf('function conferenciaRegistrosMarkup(')),ctx);
function render(dificuldades,estudos=[]){return ctx.destaquesGemMarkup([{nome:'Ana'}],{historico:[{Aluna:'Ana',Data:'18/11/2026',Tipo:'Chamada',Status:'Presente'},{Aluna:'Ana',Data:'18/11/2026',Tipo:'Analise_Prática',Dificuldades:dificuldades}],estudos},'2026-11-18');}
test('somente marcação explícita positiva; dificuldades retiram um ponto e branco soma um ponto',()=>{
 assert.match(render(['Não apresentou dificuldades']),/6 pontos/);
 assert.match(render([]),/4 pontos/);
 assert.match(render(['Ritmo','Leitura']),/2 pontos/);
 assert.match(render(['Não apresentou dificuldades','Ritmo']),/2 pontos/);
 assert.match(render(JSON.stringify(['Não apresentou dificuldades'])),/6 pontos/);
 assert.match(render('Não apresentou dificuldades'),/6 pontos/);
});
test('estudo vale quatro por dia distinto, com horário preenchido',()=>{
 const estudos=[{aluna:'Ana',data:'18/11/2026',horarios:['10h']},{aluna:'Ana',data:'2026-11-18',horarios:['15h']},{aluna:'Ana',data:'2026-11-17',horarios:['']}];
 assert.match(render([],estudos),/8 pontos/);
});

test('falta desconta dois e justificada desconta um',()=>{
 for(const [status,pontos] of [['Ausente',1],['Justificada',2]]){
 const html=ctx.destaquesGemMarkup([{nome:'Ana'}],{historico:[{Aluna:'Ana',Data:'18/11/2026',Tipo:'Chamada',Status:status},{Aluna:'Ana',Data:'18/11/2026',Tipo:'Analise_Prática',Dificuldades:['Não apresentou dificuldades']}]},'2026-11-18');
 assert.ok(html.includes(pontos+' pontos'));
 }
});
