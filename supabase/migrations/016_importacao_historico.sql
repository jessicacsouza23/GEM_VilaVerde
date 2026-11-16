-- Executar no Supabase do GEM que receberá os registros antigos.
begin;
alter table public.historico_geral add column if not exists importacao_chave text;
create unique index if not exists historico_importacao_chave_unique on public.historico_geral(importacao_chave) where importacao_chave is not null;
notify pgrst, 'reload schema';
commit;
