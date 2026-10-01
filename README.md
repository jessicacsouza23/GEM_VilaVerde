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
8. `008_exercicios_registro_pratica.sql` — garante os exercícios separados por
   método no Registro de Prática.

### Conta Master inicial

Depois das migrations 001 e 002, crie a conta em **Authentication → Users →
Add user → Create new user**:

- e-mail: `jessicavitorioit@gmail.com`
- nome no cadastro da plataforma: `master`
- escolha uma senha e marque **Auto Confirm User**.

Em seguida execute a migration 006. A conta poderá entrar pelo mesmo login do
aplicativo, sem escolher “entrar como”.

## Vários GEMs

A plataforma já possui as tabelas de Master, GEMs e acessos. O Vila Verde
continua no banco legado atual para não interromper o Streamlit.

Antes de cadastrar um GEM novo para uso real, é preciso decidir sua base:

- **banco Supabase próprio** para o novo GEM; ou
- uma futura migração das tabelas pedagógicas para multi-GEM com `gem_id` e
  políticas de isolamento.

Criar somente o nome de outro GEM não deve ser entendido como uma cópia pronta
do Vila Verde: os dados pedagógicos, usuários e arquivos precisam da base
isolada escolhida para aquela unidade.

## Publicação no Vercel

Veja [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md). O Root Directory é `./` quando este
repositório é o próprio `GEM_VilaVerde`.

## Instalação no celular

Depois da publicação em HTTPS:

- Android/Chrome: use **Instalar aplicativo**;
- iPhone/Safari: **Compartilhar → Adicionar à Tela de Início**.

O aplicativo instalado recebe as fotos em cache local para evitar baixar a
mesma imagem do Supabase repetidamente.
