-- Observação pedagógica interna por nota de avaliação.
-- Nunca deve ser apresentada no boletim destinado à aluna.
alter table public.avaliacao_notas
  add column if not exists observacao text;

comment on column public.avaliacao_notas.observacao is
  'Registro pedagógico interno da professora. Visível somente no Analítico e nos relatórios da equipe.';
