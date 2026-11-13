-- Execute no Supabase do GEM que possui a restrição antiga.
-- Amplia somente a lista de disciplinas; preserva documentos e permissões.
begin;

alter table public.gabaritos
  drop constraint if exists gabaritos_disciplina_check;

alter table public.gabaritos
  add constraint gabaritos_disciplina_check
  check (disciplina in ('Prática', 'Teoria', 'Solfejo', 'Solfejo Melódico'));

notify pgrst, 'reload schema';
commit;
