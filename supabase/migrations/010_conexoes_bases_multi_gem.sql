-- Conexão de cada unidade a uma base Supabase própria.
-- Não move nem altera os dados do GEM Vila Verde: ele continua usando as
-- variáveis padrão da Vercel e o app.py no projeto atual.

alter table public.gems
  add column if not exists supabase_url text,
  add column if not exists supabase_anon_key text,
  add column if not exists perfil_schema text not null default 'gem-pwa-v1';

alter table public.gems
  drop constraint if exists gems_perfil_schema_check;

alter table public.gems
  add constraint gems_perfil_schema_check
  check (perfil_schema in ('gem-pwa-v1'));

comment on column public.gems.supabase_url is
  'URL pública do projeto Supabase isolado da unidade. Não é segredo.';
comment on column public.gems.supabase_anon_key is
  'Chave anon pública do projeto isolado. A proteção dos dados depende das RLS do projeto da unidade.';

-- O endereço e a anon key já são públicos em qualquer aplicativo Supabase.
-- Esta política permite que /?gem=slug encontre somente a configuração da
-- unidade ativa antes de exibir o login. Dados pedagógicos não existem nesta
-- tabela e continuam protegidos nas bases de cada GEM.
drop policy if exists "leitura publica da conexao de gem ativa" on public.gems;
create policy "leitura publica da conexao de gem ativa" on public.gems
  for select to anon, authenticated
  using (ativo = true);
