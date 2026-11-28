-- Corrige validações antigas que podem bloquear o lançamento de notas válidas
-- (erro PostgreSQL 23514). Aceita as quatro disciplinas e nota de 0 a 10.
do $$
declare regra record;
begin
  for regra in
    select conname
    from pg_constraint
    where conrelid = 'public.avaliacao_notas'::regclass
      and contype = 'c'
      and (
        pg_get_constraintdef(oid) ilike '%disciplina%'
        or pg_get_constraintdef(oid) ilike '%nota%'
      )
  loop
    execute format('alter table public.avaliacao_notas drop constraint %I', regra.conname);
  end loop;
end $$;

alter table public.avaliacao_notas
  add constraint avaliacao_notas_disciplina_check
  check (disciplina in ('Prática', 'Teoria', 'Solfejo', 'Solfejo Melódico'));

alter table public.avaliacao_notas
  add constraint avaliacao_notas_nota_check
  check (nota >= 0 and nota <= 10);

notify pgrst, 'reload schema';
