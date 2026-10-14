-- SOMENTE LEITURA. Executar no SQL Editor do principal e de cada GEM.
-- Não retorna nomes de pessoas, senhas, hashes, chaves ou conteúdo pedagógico.
-- Enviar apenas os resultados desta consulta para preparar a migração de acesso.
select 'tabela' as tipo, n.nspname || '.' || c.relname as objeto,
  jsonb_build_object('rls', c.relrowsecurity,
    'anon_select', has_table_privilege('anon', c.oid, 'SELECT'),
    'anon_insert', has_table_privilege('anon', c.oid, 'INSERT'),
    'anon_update', has_table_privilege('anon', c.oid, 'UPDATE'),
    'anon_delete', has_table_privilege('anon', c.oid, 'DELETE')) as detalhes
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname in ('public', 'storage') and c.relkind = 'r'
union all
select 'politica', schemaname || '.' || tablename || ':' || policyname,
  jsonb_build_object('roles', roles, 'acao', cmd,
    'leitura_irrestrita', coalesce(qual in ('true', '(true)'), false),
    'escrita_irrestrita', coalesce(with_check in ('true', '(true)'), false))
from pg_policies where schemaname in ('public', 'storage')
union all
select 'coluna', table_schema || '.' || table_name || '.' || column_name,
  jsonb_build_object('tipo', data_type, 'nullable', is_nullable)
from information_schema.columns
where table_schema = 'public' and table_name in
  ('alunas','professoras','secretarias','gem_secretarias','plataforma_usuarios','gem_acessos','gems')
union all
select 'funcao', n.nspname || '.' || p.proname || '(' || pg_get_function_identity_arguments(p.oid) || ')',
  jsonb_build_object('security_definer', p.prosecdef,
    'anon_execute', has_function_privilege('anon', p.oid, 'EXECUTE'))
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public' and p.prokind = 'f'
order by tipo, objeto;
