const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
test('vários materiais, correção e todas as tarefas persistem por aluna e disciplina', async () => {
  const tabelas = {historico_geral: [{id:1, Aluna:'A', Data:'24/10/2026', Tipo:'Casa_Apostila', Licao_Casa:'página 18, lição 1', Status:'Pendente'}], exercicios_registro:[]};
  let id=10;
  const banco = {from(tabela) {
    let op='select', payload, filtros=[];
    const q = {select(){return q;}, eq(k,v){filtros.push(r=>r[k]===v);return q;}, order(){return q;}, limit(){return q;},
      insert(v){op='insert';payload=v;return q;}, update(v){op='update';payload=v;return q;}, delete(){op='delete';return q;},
      then(resolve,reject){try {
        const encontrados=tabelas[tabela].filter(r=>filtros.every(f=>f(r)));
        if(op==='delete') tabelas[tabela]=tabelas[tabela].filter(r=>!encontrados.includes(r));
        if(op==='update') encontrados.forEach(r=>Object.assign(r,payload));
        if(op==='insert') for(const r of (Array.isArray(payload)?payload:[payload]))tabelas[tabela].push({...r,id:id++});
        return Promise.resolve({data:encontrados,error:null}).then(resolve,reject);
      }catch(e){return Promise.reject(e).then(resolve,reject);}}
    };return q;
  }};
  const src=fs.readFileSync(require.resolve('../js/gem-data.js'),'utf8');
  const ctx={obterCliente:async()=>banco,dataBr:()=> '31/10/2026'};
  vm.createContext(ctx);vm.runInContext(src.slice(src.indexOf('  async function salvarRegistrosPratica('),src.indexOf('  async function exerciciosDaAula(')),ctx);
  const materiais=[{material:'Apostila',conteudo:'página 18, lição 1',licaoPendenteId:1,licaoPendenteTexto:'página 18, lição 1',resultadoLicao:'Resolvido',observacaoCorrecao:'Fez corretamente'},
    {material:'Volume 1',conteudo:'lição 2',exercicios:[{exercicio:'2',dificuldades:['Ritmo']}]},
    {material:'Volume 1',conteudo:'lição 3',exercicios:[{exercicio:'3',dificuldades:[]}]}];
  const licoesCasa=[{material:'Apostila',licaoCasa:'página 20, lição 1'},{material:'Volume 1',licaoCasa:'lição 4'},{material:'Volume 1',licaoCasa:'lição 5'}];
  await ctx.salvarRegistrosPratica({dataIso:'2026-10-31',aluna:'A',instrutora:'Professora',materiais,licoesCasa});
  const analises=tabelas.historico_geral.filter(r=>r.Tipo==='Analise_Prática');
  assert.equal(analises.length,3);
  assert.match(analises[0].Observacao,/Correção da lição: Resolvido/);
  assert.match(analises[0].Observacao,/Fez corretamente/);
  assert.equal(tabelas.historico_geral[0].Status,'Resolvido');
  assert.equal(tabelas.exercicios_registro.length,2);
  assert.equal(tabelas.historico_geral.filter(r=>r.Data==='31/10/2026'&&r.Tipo.startsWith('Casa_')).length,3);
  assert.ok(tabelas.historico_geral.every(r=>r.Aluna==='A'));
  materiais[0].resultadoLicao='';
  await ctx.salvarRegistrosPratica({dataIso:'2026-10-31',aluna:'A',instrutora:'Professora',materiais,licoesCasa});
  assert.match(tabelas.historico_geral.find(r=>r.Tipo==='Analise_Prática'&&r.Licao_Atual.startsWith('Apostila:')).Observacao,/Correção da lição: Resolvido/);
  await ctx.salvarRegistrosPratica({dataIso:'2026-10-31',aluna:'A',instrutora:'Professora',materiais:[materiais[0]],licoesCasa:[licoesCasa[0]],preservarOutrosMateriais:true});
  assert.equal(tabelas.historico_geral.filter(r=>r.Tipo==='Analise_Prática').length,3);
  assert.equal(tabelas.historico_geral.filter(r=>r.Tipo==='Casa_Metodo_Volume 1').length,2);
  assert.equal(tabelas.exercicios_registro.filter(r=>r.material==='Volume 1').length,2);
});
