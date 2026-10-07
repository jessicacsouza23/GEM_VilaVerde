-- As inscrições ficam na base principal: um mesmo navegador pode receber
-- lembretes de mais de um GEM sem misturar as contas ou as notificações.
alter table public.push_subscriptions
  add column if not exists gem_slug text not null default 'vila-verde';

alter table public.notificacoes_enviadas
  add column if not exists gem_slug text not null default 'vila-verde';

-- A inscrição Web Push é identificada pelo aparelho. A chave composta permite
-- que a mesma aluna use esse aparelho em unidades diferentes, se necessário.
alter table public.push_subscriptions
  drop constraint if exists push_subscriptions_endpoint_key;

drop index if exists public.push_subscriptions_endpoint_key;

create unique index if not exists push_subscriptions_gem_endpoint_unico
  on public.push_subscriptions (gem_slug, endpoint);

create index if not exists push_subscriptions_gem_ativo_idx
  on public.push_subscriptions (gem_slug, ativo);

create index if not exists notificacoes_enviadas_gem_idx
  on public.notificacoes_enviadas (gem_slug, created_at desc);
