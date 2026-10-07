-- Logins das Secretarias das unidades criadas pela conta Master.
-- Execute esta migration somente na base principal da plataforma (a que
-- contém as tabelas gems e plataforma_usuarios), nunca nas bases isoladas.

create extension if not exists pgcrypto;

create table if not exists public.gem_secretarias (
  id uuid primary key default gen_random_uuid(),
  gem_id uuid not null references public.gems(id) on delete cascade,
  nome text not null,
  login text not null,
  senha_hash text not null,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists gem_secretarias_login_unico
  on public.gem_secretarias (gem_id, lower(login));

alter table public.gem_secretarias enable row level security;

drop policy if exists "master gerencia secretarias dos gems" on public.gem_secretarias;
create policy "master gerencia secretarias dos gems" on public.gem_secretarias
  for all to authenticated
  using (public.eh_master_plataforma())
  with check (public.eh_master_plataforma());

-- A função é a única via de escrita da interface Master. A senha chega pelo
-- HTTPS, é transformada em hash bcrypt no banco e nunca é devolvida.
create or replace function public.salvar_secretaria_gem(
  p_id uuid,
  p_gem_id uuid,
  p_nome text,
  p_login text,
  p_senha text default '',
  p_ativo boolean default true
)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_nome text := trim(coalesce(p_nome, ''));
  v_login text := lower(trim(coalesce(p_login, '')));
begin
  if not public.eh_master_plataforma() then
    raise exception 'Apenas a conta Master pode gerenciar Secretarias.' using errcode = '42501';
  end if;
  if p_gem_id is null or v_nome = '' or v_login = '' then
    raise exception 'Informe GEM, nome e usuário da Secretaria.';
  end if;
  if p_id is null then
    if length(coalesce(p_senha, '')) < 6 then
      raise exception 'A senha inicial deve ter pelo menos 6 caracteres.';
    end if;
    insert into public.gem_secretarias (gem_id, nome, login, senha_hash, ativo)
    values (p_gem_id, v_nome, v_login, crypt(p_senha, gen_salt('bf')), coalesce(p_ativo, true));
  else
    update public.gem_secretarias
    set gem_id = p_gem_id,
        nome = v_nome,
        login = v_login,
        ativo = coalesce(p_ativo, true),
        senha_hash = case when coalesce(p_senha, '') = '' then senha_hash else crypt(p_senha, gen_salt('bf')) end,
        updated_at = now()
    where id = p_id;
    if not found then raise exception 'Secretaria não encontrada.'; end if;
  end if;
end;
$$;

revoke all on function public.salvar_secretaria_gem(uuid, uuid, text, text, text, boolean) from public;
grant execute on function public.salvar_secretaria_gem(uuid, uuid, text, text, text, boolean) to authenticated;

-- Verificação sem expor senha ou hash: usada somente no login do GEM.
create or replace function public.validar_acesso_secretaria_gem(
  p_slug text,
  p_login text,
  p_senha text
)
returns table (perfil text, nome text)
language sql
security definer
set search_path = public
as $$
  select 'secretaria'::text, s.nome
  from public.gem_secretarias s
  join public.gems g on g.id = s.gem_id
  where g.ativo = true
    and g.slug = lower(trim(coalesce(p_slug, '')))
    and s.ativo = true
    and lower(s.login) = lower(trim(coalesce(p_login, '')))
    and s.senha_hash = crypt(coalesce(p_senha, ''), s.senha_hash)
  limit 1;
$$;

revoke all on function public.validar_acesso_secretaria_gem(text, text, text) from public;
grant execute on function public.validar_acesso_secretaria_gem(text, text, text) to anon, authenticated;

-- A base pedagógica do GEM recebe somente os nomes dessas contas para listas
-- de responsáveis e relatórios; logins e senhas não são expostos.
create or replace function public.listar_secretarias_gem_publicas(p_slug text)
returns table (nome text, login text)
language sql
security definer
set search_path = public
as $$
  select s.nome, s.login
  from public.gem_secretarias s
  join public.gems g on g.id = s.gem_id
  where g.ativo = true
    and g.slug = lower(trim(coalesce(p_slug, '')))
    and s.ativo = true
  order by s.nome;
$$;

revoke all on function public.listar_secretarias_gem_publicas(text) from public;
grant execute on function public.listar_secretarias_gem_publicas(text) to anon, authenticated;
