-- Boletins: duas professoras podem avaliar a mesma disciplina e a Secretaria
-- decide quando cada avaliação fica visível para as alunas.
alter table public.avaliacao_responsaveis
  add column if not exists professora_2 text;

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
