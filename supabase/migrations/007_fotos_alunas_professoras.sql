-- Buckets usados pelo Streamlit e pelo PWA para as fotos de perfil.
-- IF NOT EXISTS preserva as fotos que já foram enviadas pelo app.py.
insert into storage.buckets (id, name, public)
values ('fotos_alunas', 'fotos_alunas', false)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('fotos_professoras', 'fotos_professoras', false)
on conflict (id) do nothing;

drop policy if exists "fotos alunas acesso legado pwa" on storage.objects;
create policy "fotos alunas acesso legado pwa" on storage.objects
  for all to anon, authenticated
  using (bucket_id = 'fotos_alunas')
  with check (bucket_id = 'fotos_alunas');

drop policy if exists "fotos professoras acesso legado pwa" on storage.objects;
create policy "fotos professoras acesso legado pwa" on storage.objects
  for all to anon, authenticated
  using (bucket_id = 'fotos_professoras')
  with check (bucket_id = 'fotos_professoras');
