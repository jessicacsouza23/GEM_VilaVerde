# Estudos com RLS ativo

O navegador usa `/api/estudos` com a sessão assinada HttpOnly emitida no login.
O servidor valida papel, origem, GEM e cadastro ativo da aluna. O nome da
aluna nas gravações vem da sessão. Professoras e Secretaria podem consultar
os estudos da própria unidade; essa rota não permite que alterem os estudos.
Nenhuma chave administrativa deve ser inserida no JavaScript público.

## Vila Verde

Na Vercel, configure `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` e
`SESSION_SECRET` (as mesmas variáveis da sessão já existente). Publique e
saia/entre novamente no aplicativo. Não desative o RLS e não crie políticas
públicas para contornar o bloqueio. Não é necessário alterar os registros.

## GEMs com Supabase próprio

Configure no servidor a variável privada `GEM_ESTUDOS_BASES` como objeto JSON:
`{"slug-do-gem":{"url":"https://projeto.supabase.co","serviceRoleKey":"CHAVE_PRIVADA_DA_UNIDADE"}}`.
Use a service role da unidade, nunca a chave do principal para outra base.
O servidor confere que a unidade está ativa e que sua URL coincide com o
cadastro central. Sem configuração, mostra erro e nunca usa a base principal.
Não cole chaves reais em commits, prints ou conversas.

## Verificação após publicar

1. Aluna: salvar estudo, recarregar, conferir horários e excluir um registro de teste.
2. Professora/Secretaria: atualizar Analítico e visão geral e conferir o mesmo dia.
3. Uma falha de sessão/conexão deve mostrar erro, não “não estudou”.
4. As permissões dos bancos externos devem ser revisadas separadamente caso
   ainda possuam políticas legadas de acesso público; esta mudança não altera policies.
