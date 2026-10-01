-- Correção segura para a primeira conta Master quando o usuário do Supabase
-- Auth foi criado antes da migration 002 ou quando o convite não foi aceito.
-- Não altera professoras, alunas, Secretaria nem qualquer dado pedagógico.

insert into public.plataforma_usuarios (nome, email, papel, ativo, status_convite)
values ('master', 'jessicavitorioit@gmail.com', 'master', true, 'pendente')
on conflict (email) do update
set nome = excluded.nome,
    papel = 'master',
    ativo = true,
    updated_at = now();

update public.plataforma_usuarios as plataforma
set auth_user_id = usuario.id,
    status_convite = 'ativo',
    ativo = true,
    updated_at = now()
from auth.users as usuario
where lower(plataforma.email) = lower(usuario.email)
  and lower(plataforma.email) = 'jessicavitorioit@gmail.com'
  and plataforma.papel = 'master';

-- Conferência: deve retornar status_convite = ativo e um auth_user_id preenchido.
select nome, email, papel, ativo, status_convite, auth_user_id
from public.plataforma_usuarios
where lower(email) = 'jessicavitorioit@gmail.com';
