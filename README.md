# GEM Vila Verde — aplicativo web/PWA

Esta pasta contém o aplicativo publicado no Vercel. Ele consulta o mesmo
Supabase do GEM e mantém o `app.py`/Streamlit como sistema de reserva: nada
nele deve ser removido para publicar o aplicativo novo.

## Funcionalidades já ligadas ao banco do GEM

- Login de Secretaria, Professora, Aluna e Master.
- Rodízio: modelos, turmas, professoras por turma, folgas, saídas antecipadas,
  professoras fixas, rotação manual, edição posterior, histórico e imagem.
- Chamada com fotos e presença selecionada por padrão.
- Registro de aula por disciplina, dificuldades, observações e lições.
- Correção de lições pela Secretaria e pelas professoras.
- Relatório diário com download em PDF, Analítico e quadro de desempenho.
- Cadastros, desativação, senha, fotos de alunas/professoras e perfil da
  Coordenação.
- Documentos, provas, professoras responsáveis, notas e mensagens.
- Aplicativo instalável e notificações push opcionais.

## Execute no Supabase, nesta ordem

No **SQL Editor**, abra e execute cada arquivo abaixo. Eles são incrementais e
preservam tabelas, histórico e o funcionamento do Streamlit.

1. `001_validar_login_professoras_alunas.sql` — login de professoras e alunas.
2. `002_fundacao_multi_gem_master.sql` — base da plataforma e conta Master.
3. `003_auditoria_edicoes_rodizio.sql` — histórico das correções de rodízio.
4. `004_perfil_secretaria_e_marca.sql` — logo e perfil da Coordenação.
5. `005_notificacoes_push.sql` — necessário somente para lembretes no celular.
6. `006_reparar_vinculo_master.sql` — conecta a conta Master ao Supabase Auth.
7. `007_fotos_alunas_professoras.sql` — garante os buckets usados pelas fotos.
8. `008_exercicios_registro_pratica.sql` — registra os exercícios e dificuldades da Prática.
9. `009_professora_coordenadora.sql` — define a professora coordenadora por período e libera Folgas no login dela.
10. `010_conexoes_bases_multi_gem.sql` — vincula uma base Supabase exclusiva a cada novo GEM.

### Conta Master inicial

Depois das migrations 001 e 002, crie a conta em **Authentication → Users →
Add user → Create new user**:

- e-mail: `jessicavitorioit@gmail.com`
- nome no cadastro da plataforma: `master`
- escolha uma senha e marque **Auto Confirm User**.

Em seguida execute a migration 006. A conta poderá entrar pelo mesmo login do
aplicativo, sem escolher “entrar como”.

## Vários GEMs

O Vila Verde continua na base atual, sem mexer no Streamlit. Para uma unidade
nova, a Master cria primeiro um projeto Supabase **separado**. No SQL Editor
desse projeto novo, execute primeiro `supabase/migrations/012_base_pedagogica_novo_gem.sql`
e depois `supabase/migrations/001_validar_login_professoras_alunas.sql`. A
primeira cria todas as tabelas pedagógicas vazias; a segunda ativa o login de
professoras e alunas. Depois, no login Master do Vila Verde, informe no cadastro
do GEM novo:

- nome e identificador;
- URL do projeto Supabase novo;
- chave pública `anon` desse projeto.

O sistema gera um link como `https://seu-app.vercel.app/?gem=gem-central`.
Esse endereço abre o aplicativo conectado somente à base daquela unidade. A
chave `anon` é pública por definição do Supabase; as políticas RLS da base de
cada GEM continuam sendo responsáveis pela proteção dos dados.

O perfil atual suportado é `gem-pwa-v1`. Não é necessário copiar os dados do
Vila Verde: a migration 012 já prepara o mesmo esquema funcional, vazio, para
a nova unidade. Uma unidade com tabelas totalmente diferentes precisa de um
perfil/adaptador próprio antes de ser ativada.

As integrações de servidor já configuradas para o Vila Verde (R2, IA e
notificações push) permanecem isoladas nele. O núcleo pedagógico do PWA usa a
base exclusiva do novo GEM; para ativar essas integrações em outra unidade é
necessário configurar as credenciais próprias dela na Vercel.

## Publicação no Vercel

Veja [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md). O Root Directory é `./` quando este
repositório é o próprio `GEM_VilaVerde`.

## Instalação no celular

Depois da publicação em HTTPS:

- Android/Chrome: use **Instalar aplicativo**;
- iPhone/Safari: **Compartilhar → Adicionar à Tela de Início**.

O aplicativo instalado recebe as fotos em cache local para evitar baixar a
mesma imagem do Supabase repetidamente.
