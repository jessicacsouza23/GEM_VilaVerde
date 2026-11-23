-- Boletins: duas professoras podem avaliar a mesma disciplina e a Secretaria
-- decide quando cada avaliação fica visível para as alunas.
alter table public.avaliacao_responsaveis
  add column if not exists professora_2 text;

-- Alguns bancos antigos tinham uma validação de disciplina anterior ao
-- Solfejo Melódico. Ela impede inclusive salvar as responsáveis da tela.
-- Substituímos somente checks que validam a coluna disciplina nesta tabela.
do $$
declare regra record;
begin
  for regra in
    select conname
    from pg_constraint
    where conrelid = 'public.avaliacao_responsaveis'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) ilike '%disciplina%'
  loop
    execute format('alter table public.avaliacao_responsaveis drop constraint %I', regra.conname);
  end loop;
end $$;

alter table public.avaliacao_responsaveis
  add constraint avaliacao_responsaveis_disciplina_check
  check (disciplina in ('Prática', 'Teoria', 'Solfejo', 'Solfejo Melódico'));

alter table public.avaliacoes
  add column if not exists boletim_liberado boolean not null default false,
  add column if not exists boletim_liberado_em timestamptz,
  add column if not exists boletim_liberado_por text;

-- Cada professora responsável conserva a própria nota. O boletim apresenta
-- a média das notas lançadas para a disciplina naquela avaliação.
alter table public.avaliacao_notas
  drop constraint if exists avaliacao_notas_avaliacao_id_aluna_disciplina_key;

create unique index if not exists avaliacao_notas_por_professora_unica
  on public.avaliacao_notas (avaliacao_id, aluna, disciplina, professora);
