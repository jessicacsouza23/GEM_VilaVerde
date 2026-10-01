# Publicação do aplicativo no Vercel

O Streamlit continua independente. Não exclua nem altere `app.py` para publicar
esta pasta.

## Configuração única

1. No Vercel, importe o mesmo repositório Git do GEM.
2. Em **Root Directory**, selecione `./` quando o repositório aberto for o
   próprio `GEM_VilaVerde`. Não selecione a pasta-pai `site_telemais`.
3. Em **Environment Variables**, cadastre para Production e Preview:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
4. Clique em **Deploy**.

Depois disso, todo push para o Git publica uma versão nova do aplicativo. O
Vercel fornece um endereço HTTPS; nele, o botão **Instalar aplicativo** ficará
disponível em aparelhos compatíveis.

## Importante

- Use a URL e a chave pública `anon` do Supabase.
- Nunca coloque `SUPABASE_SERVICE_ROLE_KEY` no navegador, em `index.html` ou
  em arquivos `js/`. Ela somente poderá existir como **Secret** na Vercel,
  usada pelas funções de servidor.
- As migrations do Supabase são uma configuração separada, executada uma única
  vez no SQL Editor ou por uma futura automação de deploy.
- Antes do primeiro deploy completo, execute as migrations 001 a 007 listadas
  no `README.md`. A 005 é opcional se os lembretes push não forem usados.

## Notificações no celular

Depois de executar `supabase/migrations/005_notificacoes_push.sql`, cadastre
também como **Secret** na Vercel (Production):

- `SUPABASE_SERVICE_ROLE_KEY` — usada apenas pelas rotas `/api/`, nunca é
  enviada ao celular.
- `PUSH_VAPID_PUBLIC_KEY` e `PUSH_VAPID_PRIVATE_KEY` — par de chaves Web Push.
- `PUSH_CONTACT_EMAIL` — e-mail de contato técnico.
- `CRON_SECRET` — senha longa usada pelo agendamento diário.

As chaves VAPID podem ser geradas uma vez no computador com:

```powershell
npx web-push generate-vapid-keys
```

O botão **Ativar lembretes** aparece depois do login. O cron da Vercel roda às
08:00 (horário de Brasília): lembra as alunas de estudar e avisa professoras
quando há aulas recentes sem registro. No iPhone, as notificações funcionam
depois de instalar o site como aplicativo pela opção “Adicionar à Tela de
Início”.
