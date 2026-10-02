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
- Antes do primeiro deploy completo, execute as migrations 001 a 010 listadas
  no `README.md`. A 005 é opcional se os lembretes push não forem usados.

## Fotos no Cloudflare R2 (opcional)

Sem estas variáveis, as fotos continuam no Supabase e o aplicativo não muda.
Para mover **novos envios** de fotos e logo para o R2, crie um bucket privado
como `gem-vila-verde-media`, gere uma chave R2 restrita a esse bucket com
permissão **Object Read & Write** e cadastre, como **Secret** na Vercel:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME` — por exemplo, `gem-vila-verde-media`
- `SESSION_SECRET` — texto aleatório longo para proteger a sessão temporária
  das fotos.
- `SUPABASE_SERVICE_ROLE_KEY` — usada somente pela Vercel para validar o
  login legado antes de emitir essa sessão; nunca vai para o navegador.

No bucket R2, configure CORS permitindo o domínio de produção do Vercel e o
método `PUT`, com o cabeçalho `Content-Type`. Exemplo para o domínio padrão:

```json
[
  {
    "AllowedOrigins": ["https://gem-vila-verde.vercel.app"],
    "AllowedMethods": ["PUT"],
    "AllowedHeaders": ["Content-Type"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 300
  }
]
```

Após publicar, novos envios feitos pela Secretaria passam ao R2. As fotos
antigas permanecem acessíveis no Supabase até uma cópia posterior e conferida;
nada é apagado automaticamente.

## Analítico com IA (opcional)

O botão de resumo pedagógico do Analítico usa a mesma ideia do `app.py`, mas a
chave fica somente no servidor da Vercel. Cadastre como **Secret**:

- `GEMINI_API_KEY` — chave criada no Google AI Studio;
- `SESSION_SECRET` e `SUPABASE_SERVICE_ROLE_KEY` — os mesmos da seção R2,
  usados para confirmar que a pessoa entrou no GEM antes de chamar a IA.

Opcionalmente, defina `GEMINI_MODEL` caso queira escolher um modelo permitido
pela sua chave. Sem ela, o servidor tenta automaticamente um modelo Flash de
texto disponível. O GEM envia apenas o resumo da aluna selecionada (registros,
frequência, lições e notas), nunca fotos, documentos ou senhas.

## Notificações no celular

Depois de executar `supabase/migrations/005_notificacoes_push.sql`, cadastre
também como **Secret** na Vercel (Production):

- `SUPABASE_SERVICE_ROLE_KEY` — usada apenas pelas rotas `/api/`, nunca é
  enviada ao celular.
- `SESSION_SECRET` — senha longa que confirma a conta logada antes de aceitar
  a inscrição do aparelho para receber notificações.
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

## Diagnóstico de login

Se **todos** os perfis (Secretaria, professoras e alunas) exibirem “usuário
ou senha inválidos” ao mesmo tempo, não redefina as senhas: normalmente é a
chave pública `anon` do Supabase que está incorreta na publicação. Confira o
arquivo `js/supabase-config.js`: ele deve conter a URL e a `anonKey` pública
do projeto correto, obtida em **Supabase → Project Settings → API**. Nunca
substitua essa chave por `service_role`; a chave `service_role` fica somente
nas variáveis Secret da Vercel. Após corrigir o arquivo, envie ao Git, aguarde
a implantação e atualize a página do aplicativo.
