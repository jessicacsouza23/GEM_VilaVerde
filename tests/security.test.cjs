const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
function carregar(arquivo, extras = {}) {
  const ctx = { module: { exports: {} }, require, Buffer, URL, URLSearchParams, AbortSignal, process: { env: { SESSION_SECRET: 's'.repeat(64), SUPABASE_URL: 'https://principal.supabase.co', SUPABASE_SERVICE_ROLE_KEY: 'test-only' } }, ...extras };
  vm.createContext(ctx); vm.runInContext(fs.readFileSync(require.resolve(arquivo), 'utf8'), ctx);
  return ctx;
}
test('sessões adulteradas, unicode, formato inválido e expiradas são recusadas', () => {
  const ctx = carregar('../api/r2-auth.js'), auth = ctx.module.exports;
  const token = auth.criarSessao({ nome: 'Ana', perfil: 'Aluna' });
  const request = cookie => ({ headers: { cookie: `gem_r2_session=${cookie}` } });
  assert.equal(auth.sessao(request(token)).nome, 'Ana');
  for (const valor of ['', '.', token + '.extra', token.slice(0, -1), 'abc.' + 'é'.repeat(43), 'a'.repeat(5000), 'abc.' + 'x'.repeat(43)]) assert.equal(auth.sessao(request(valor)), null);
  const assinar = dados => { const p = Buffer.from(JSON.stringify(dados)).toString('base64url'); return p + '.' + crypto.createHmac('sha256', ctx.process.env.SESSION_SECRET).update(p).digest('base64url'); };
  for (const dados of [{ nome: 'Ana', perfil: 'Aluna', exp: 1 }, { nome: 'Ana', perfil: 'root', exp: Math.floor(Date.now()/1000)+100 }, { nome: 'Ana', perfil: 'Aluna', gem: '../outro', exp: Math.floor(Date.now()/1000)+100 }]) assert.equal(auth.sessao(request(assinar(dados))), null);
  assert.equal(auth.origemPermitida({ headers: { host: 'gem.test', origin: 'https://gem.test' } }), true);
  assert.equal(auth.origemPermitida({ headers: { host: 'gem.test', origin: 'https://outro.test' } }), false);
  assert.equal(auth.origemPermitida({ headers: { 'sec-fetch-site': 'cross-site' } }), false);
});
test('fotos: propriedade, papéis, unidade e falha fechada', async () => {
  let falhar = false, consultas = 0;
  const ctx = carregar('../lib/photo-access.js', { fetch: async url => {
    consultas++;
    if (falhar) return { ok: false };
    const u = new URL(url);
    if (u.pathname.endsWith('/gems')) return { ok: true, json: async () => [{ supabase_url: 'https://unidade.supabase.co', supabase_anon_key: 'test-anon' }] };
    const nome = u.searchParams.get('nome');
    return { ok: true, json: async () => nome && nome !== 'eq.Ana' ? [] : [{ foto_path: u.searchParams.get('foto_path').slice(3) }] };
  } });
  const { podeLerFoto } = ctx.module.exports;
  const ana = { nome: 'Ana', perfil: 'Aluna', gem: 'vila-verde' };
  const key = 'gems/vila-verde/fotos_alunas/a.jpg';
  assert.equal(await podeLerFoto(ana, key), true);
  assert.equal(await podeLerFoto({ ...ana, nome: 'Bia' }, key), false);
  assert.equal(await podeLerFoto(ana, 'gems/outro/fotos_alunas/a.jpg'), false);
  assert.equal(await podeLerFoto(ana, 'gems/vila-verde/fotos_professoras/a.jpg'), false);
  assert.equal(await podeLerFoto({ ...ana, perfil: 'Professora' }, key), true);
  assert.equal(await podeLerFoto({ ...ana, perfil: 'Master' }, key), false);
  assert.equal(await podeLerFoto({ ...ana, perfil: 'Secretaria' }, key), true);
  assert.equal(await podeLerFoto(ana, 'fotos_alunas/a.jpg'), true);
  assert.equal(await podeLerFoto({ ...ana, gem: 'outro' }, 'gems/outro/fotos_alunas/a.jpg'), true);
  assert.equal(await podeLerFoto(ana, 'gems/vila-verde/fotos_alunas/../a.jpg'), false);
  falhar = true;
  await assert.rejects(podeLerFoto(ana, key));
  assert.ok(consultas > 0);
});
test('proxy e download verificam permissão antes de consultar R2', async () => {
  for (const file of ['r2-file', 'r2-download-url']) {
    let aws = 0;
    const ctx = carregar(`../api/${file}.js`, { require: nome => ({
      '@aws-sdk/client-s3': { GetObjectCommand: class {} },
      '@aws-sdk/s3-request-presigner': { getSignedUrl: async () => { aws++; } },
      './r2-auth': { configurado: () => true, sessaoComR2: () => ({ nome: 'Ana', perfil: 'Aluna', gem: 'vila-verde' }) },
      '../lib/photo-access': { podeLerFoto: async () => false },
      './r2-client': { clienteR2: () => ({ send: async () => { aws++; } }), bucket: () => 'test' }
    })[nome] });
    const resposta = { headers: {}, setHeader(k,v) { this.headers[k]=v; }, status(s) { this.code=s; return this; }, json() {} };
    await ctx.module.exports({ method: 'GET', query: { key: 'r2:gems/vila-verde/fotos_alunas/a.jpg' } }, resposta);
    assert.equal(resposta.code, 403); assert.equal(aws, 0); assert.match(resposta.headers['Cache-Control'], /no-store/);
  }
});
test('service worker não recupera API/foto privada de cache', async () => {
  const eventos = {}, requisicoes = [];
  const ctx = { URL, self: { location: { origin: 'https://gem.test', href: 'https://gem.test/service-worker.js' }, addEventListener: (nome, fn) => { eventos[nome]=fn; } },
    fetch: async (req, opcoes) => { requisicoes.push(opcoes); return 'rede'; }, caches: { match() { throw new Error('Não pode acessar cache privado'); } } };
  vm.createContext(ctx); vm.runInContext(fs.readFileSync(require.resolve('../service-worker.js'), 'utf8'), ctx);
  for (const url of ['https://gem.test/api/r2-file?key=a', 'https://x.supabase.co/storage/v1/object/sign/foto', 'https://x.supabase.co/rest/v1/alunas']) {
    let promise; eventos.fetch({ request: { method: 'GET', url }, respondWith(p) { promise=p; } });
    assert.equal(await promise, 'rede');
    assert.equal(requisicoes.at(-1).cache, 'no-store');
  }
});
