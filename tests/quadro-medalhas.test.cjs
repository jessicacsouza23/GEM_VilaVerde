const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');const s=fs.readFileSync(require.resolve('../app.js'),'utf8'),ctx={escapeHtml:s=>String(s).replaceAll('<','&lt;')};vm.createContext(ctx);vm.runInContext(s.slice(s.indexOf('function quadroMedalhasMarkup('),s.indexOf('function destaquesGemMarkup(')),ctx);
test('conta medalhas das células e exclui sem registros',()=>{
 const h=ctx.quadroMedalhasMarkup([{'Prática':'Ouro','Teoria':'Sem registros'},{'Prática':'Bronze','Teoria':'Prata'}],['Prática','Teoria'],'2025-01-01','2025-01-31','GEM');
 for(const t of ['Ouro','Prata','Bronze'])assert.ok(h.includes(t+'</span><strong>1</strong>'));
 assert.ok(h.includes('01/01/2025 a 31/01/2025'));assert.ok(h.includes('🥇 0 Ouro'));
});
