-- Perfil visual da Coordenação do Vila Verde. Não altera professoras, alunas
-- ou a logo que já existe no Streamlit; o novo app apenas ganha uma foto
-- configurável para substituir a letra do avatar.
create table if not exists public.secretaria_perfil (
  id integer primary key check (id = 1),
  nome_exibicao text not null default 'Coordenação',
  foto_path text,
  updated_at timestamptz not null default now()
);

insert into public.secretaria_perfil (id, nome_exibicao)
values (1, 'Coordenação') on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('fotos_secretaria_gem', 'fotos_secretaria_gem', false)
on conflict (id) do nothing;

alter table public.secretaria_perfil enable row level security;
drop policy if exists "perfil secretaria acesso legado" on public.secretaria_perfil;
create policy "perfil secretaria acesso legado" on public.secretaria_perfil
  for all to anon, authenticated using (true) with check (true);

drop policy if exists "foto secretaria acesso legado" on storage.objects;
create policy "foto secretaria acesso legado" on storage.objects
  for all to anon, authenticated
  using (bucket_id = 'fotos_secretaria_gem')
  with check (bucket_id = 'fotos_secretaria_gem');
