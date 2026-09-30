-- Fundação da plataforma multi-GEM.
-- É segura para executar junto ao sistema atual: cria tabelas novas e não
-- move, apaga ou reescreve os dados já existentes do Vila Verde.

create extension if not exists pgcrypto;

create table if not exists public.gems (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  slug text not null unique,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- O primeiro GEM preserva o acervo existente. Os registros atuais serão
-- vinculados a ele na migração de dados, nunca copiados para outro GEM.
insert into public.gems (nome, slug)
values ('GEM Vila Verde', 'vila-verde')
on conflict (slug) do nothing;

-- Contas da plataforma. Uma conta Master não pertence a um GEM específico.
-- auth_user_id é preenchido quando o convite do Supabase Auth for aceito.
create table if not exists public.plataforma_usuarios (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid unique references auth.users(id) on delete cascade,
  nome text not null,
  email text not null unique,
  papel text not null check (papel in ('master')),
  ativo boolean not null default true,
  status_convite text not null default 'pendente'
    check (status_convite in ('pendente', 'ativo', 'bloqueado')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Primeira administradora da plataforma. A senha não é salva aqui: ela será
-- definida no convite do Supabase Auth.
insert into public.plataforma_usuarios (nome, email, papel, status_convite)
values ('master', 'jessicavitorioit@gmail.com', 'master', 'pendente')
on conflict (email) do update
set nome = excluded.nome,
    papel = 'master',
    ativo = true;

-- Quando o convite for criado no Supabase Auth, a conta Master é vinculada
-- automaticamente pelo e-mail. Nenhuma senha é copiada para esta tabela.
create or replace function public.vincular_master_ao_auth()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  update public.plataforma_usuarios
  set auth_user_id = new.id,
      status_convite = 'ativo',
      updated_at = now()
  where lower(email) = lower(coalesce(new.email, ''))
    and papel = 'master'
    and auth_user_id is null;
  return new;
end;
$$;

drop trigger if exists ao_criar_usuario_auth_vincular_master on auth.users;
create trigger ao_criar_usuario_auth_vincular_master
  after insert on auth.users
  for each row execute procedure public.vincular_master_ao_auth();

-- Vínculos de quem atua dentro de cada GEM. No futuro uma mesma pessoa poderá
-- ter acessos distintos em mais de uma unidade, sem misturar seus dados.
create table if not exists public.gem_acessos (
  id uuid primary key default gen_random_uuid(),
  gem_id uuid not null references public.gems(id) on delete cascade,
  auth_user_id uuid not null references auth.users(id) on delete cascade,
  papel text not null check (papel in ('secretaria', 'professora', 'aluna')),
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  unique (gem_id, auth_user_id)
);

create index if not exists gem_acessos_usuario_idx on public.gem_acessos(auth_user_id);
create index if not exists gem_acessos_gem_idx on public.gem_acessos(gem_id);

-- Catálogo de arquivos do novo app. O caminho físico seguirá o padrão
-- gems/{gem_id}/..., mantendo logos, fotos e documentos isolados.
create table if not exists public.gem_arquivos (
  id uuid primary key default gen_random_uuid(),
  gem_id uuid not null references public.gems(id) on delete cascade,
  categoria text not null check (categoria in ('logo', 'foto_aluna', 'foto_professora', 'documento')),
  caminho text not null,
  dono_id uuid,
  created_at timestamptz not null default now(),
  unique (gem_id, caminho)
);

alter table public.gems enable row level security;
alter table public.plataforma_usuarios enable row level security;
alter table public.gem_acessos enable row level security;
alter table public.gem_arquivos enable row level security;

create or replace function public.eh_master_plataforma()
returns boolean
language sql stable security definer set search_path = public
as $$
  select exists (
    select 1 from public.plataforma_usuarios
    where auth_user_id = auth.uid()
      and papel = 'master'
      and ativo = true
      and status_convite = 'ativo'
  );
$$;

drop policy if exists "master gerencia gems" on public.gems;
create policy "master gerencia gems" on public.gems
  for all to authenticated
  using (public.eh_master_plataforma())
  with check (public.eh_master_plataforma());

drop policy if exists "master gerencia plataforma" on public.plataforma_usuarios;
create policy "master gerencia plataforma" on public.plataforma_usuarios
  for all to authenticated
  using (public.eh_master_plataforma() or auth_user_id = auth.uid())
  with check (public.eh_master_plataforma());

drop policy if exists "master gerencia acessos" on public.gem_acessos;
create policy "master gerencia acessos" on public.gem_acessos
  for all to authenticated
  using (public.eh_master_plataforma())
  with check (public.eh_master_plataforma());

drop policy if exists "master gerencia arquivos" on public.gem_arquivos;
create policy "master gerencia arquivos" on public.gem_arquivos
  for all to authenticated
  using (public.eh_master_plataforma())
  with check (public.eh_master_plataforma());
