-- Ponte segura para a nova interface do GEM.
-- Esta função não devolve senhas nem permite listar professoras/alunas.
-- Ela só devolve o perfil da conta quando usuário e senha correspondem.

create or replace function public.validar_acesso_gem_pessoas(
  p_login text,
  p_senha text
)
returns table (perfil text, nome text)
language plpgsql
security definer
set search_path = public
as $$
begin
  return query
    select 'professora'::text, p.nome::text
    from public.professoras p
    where lower(trim(coalesce(p.login, ''))) = lower(trim(coalesce(p_login, '')))
      and p.senha = p_senha
      and coalesce(p.ativo, true) = true
    limit 1;

  if found then return; end if;

  return query
    select 'aluna'::text, a.nome::text
    from public.alunas a
    where lower(trim(coalesce(a.login, ''))) = lower(trim(coalesce(p_login, '')))
      and a.senha = p_senha
      and coalesce(a.ativo, true) = true
    limit 1;
end;
$$;

revoke all on function public.validar_acesso_gem_pessoas(text, text) from public;
grant execute on function public.validar_acesso_gem_pessoas(text, text) to anon, authenticated;
