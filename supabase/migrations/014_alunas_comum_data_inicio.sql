-- Execute em cada base pedagógica de GEM, inclusive a principal.
-- Campos opcionais: não inventa informações para cadastros antigos.
begin;
alter table public.alunas add column if not exists comum text;
alter table public.alunas add column if not exists data_inicio date;
comment on column public.alunas.comum is 'Comum/congregação informada no cadastro da aluna.';
comment on column public.alunas.data_inicio is 'Data de início da aluna no GEM.';
notify pgrst, 'reload schema';
commit;
