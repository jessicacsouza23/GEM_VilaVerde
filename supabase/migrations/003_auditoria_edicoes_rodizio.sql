-- Mantém um histórico de correções realizadas pela Secretaria no novo app.
-- A tabela calendario continua sendo o retrato que professoras e alunas leem;
-- esta tabela apenas preserva a versão anterior antes de uma edição.
create table if not exists public.calendario_edicoes (
  id uuid primary key default gen_random_uuid(),
  data_escala text not null,
  escala_anterior jsonb not null default '[]'::jsonb,
  escala_nova jsonb not null default '[]'::jsonb,
  motivo text,
  editado_em timestamptz not null default now()
);

create index if not exists calendario_edicoes_data_idx on public.calendario_edicoes(data_escala, editado_em desc);

alter table public.calendario_edicoes enable row level security;

-- Mantém o mesmo modelo de permissões das tabelas legadas: a Secretaria que
-- já pode gravar calendario poderá registrar a auditoria. Caso o projeto use
-- uma política específica, ajuste esta policy para a função de acesso local.
drop policy if exists "secretaria registra auditoria de rodizio" on public.calendario_edicoes;
create policy "secretaria registra auditoria de rodizio" on public.calendario_edicoes
  for all to anon, authenticated using (true) with check (true);
