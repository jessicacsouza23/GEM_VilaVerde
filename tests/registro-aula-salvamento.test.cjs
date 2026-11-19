const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require.resolve('../js/gem-data.js'),'utf8');
for(const tipo of ['Teoria','Solfejo','Solfejo Melódico'])test('salva '+tipo+' com avaliação individual e sem nova tarefa',async()=>{
 const salvos=[];const banco={from(){const q={select(){return q},eq(){return q},order(){return q},in(){return q},update(){return q},delete(){return q},insert(r){salvos.push(r);return q},then(ok){return Promise.resolve({data:[],error:null}).then(ok)}};return q}};
 const ctx={obterCliente:async()=>banco,dataBr:()=> '21/11/2026',normalizar:s=>String(s).toUpperCase()};vm.createContext(ctx);vm.runInContext(source.slice(source.indexOf('  async function salvarRegistroAula('),source.indexOf('  async function salvarRegistrosPratica(')),ctx);
 await ctx.salvarRegistroAula({dataIso:'2026-11-21',instrutora:'Professora',tipo,alunas:['Ana','Bia'],material:'Apostila',conteudo:'',registrosPorAluna:{Ana:{dificuldades:['Dificuldade rítmica'],observacao:'Retomar'},Bia:{dificuldades:['Não apresentou dificuldades']}},licaoCasa:''});
 assert.equal(salvos.length,2);assert.equal(salvos[0].Tipo,'Analise_'+tipo);assert.equal(salvos[0].Status,'Realizada - com dificuldades');assert.equal(salvos[1].Status,'Realizada - sem pendência');assert.equal(salvos[0].Observacao,'Retomar');
});
