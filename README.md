# GEM Vila Verde — nova interface

Esta pasta é a migração paralela do GEM para uma interface web instalável no
celular (PWA). O Streamlit e o banco atual permanecem intactos enquanto cada
parte é reproduzida e conferida.

## O que já existe nesta primeira etapa

- Estrutura de aplicativo responsiva para celular e computador.
- Login visual e perfis de Secretaria, Professora e Aluna.
- Navegação preparada para os mesmos módulos do sistema atual.
- Mural de rodízio em colunas, preservando a leitura visual de salas, horários,
  professoras e turmas.
- `manifest.webmanifest` e service worker: quando publicado em HTTPS, o sistema
  poderá ser instalado na tela inicial do celular.
- Botão de instalação que aparece automaticamente em navegadores compatíveis.

## Segurança e banco

As credenciais do Supabase **não** ficam neste repositório. O arquivo
`js/supabase-config.example.js` é só um modelo de configuração. A próxima etapa
é criar a autenticação protegida (sem consultar senhas pelo navegador) e então
ligar cada tela ao mesmo Supabase usado pelo Streamlit.

## Preparado para vários GEMs

A nova aplicação será uma plataforma multi-GEM desde o primeiro login real:

- um **login mestre** cria, ativa ou desativa cada GEM e define a Secretaria
  principal daquele GEM;
- Secretaria, professoras e alunas entram somente no GEM a que pertencem;
- cada registro (turmas, pessoas, rodízio, chamadas, relatórios, arquivos e
  notas) será filtrado pelo identificador do GEM;
- as políticas de segurança do Supabase bloquearão o acesso de um GEM aos dados
  de qualquer outro, mesmo se alguém tentar acessar a API diretamente.

O GEM Vila Verde será cadastrado como o primeiro GEM e os dados já existentes
continuarão vinculados somente a ele. GEMs novos começam vazios e independentes.

No login, ninguém escolhe “entrar como”. A conta informa automaticamente se a
pessoa é Master, Secretaria, Professora ou Aluna e a encaminha ao painel certo.
Se uma mesma pessoa participar de mais de um GEM, ela escolhe o GEM **depois**
de autenticar; a conta Master vai diretamente para a administração da plataforma.

### Conta Master inicial

A primeira conta Master não nasce sozinha nem é uma Secretaria. Ela é criada
uma única vez, em uma etapa protegida de implantação, com nome, usuário/e-mail
e senha definidos pela administradora da plataforma. Depois disso, somente uma
conta Master poderá criar outro Master ou cadastrar um novo GEM.

A conta Master administra cadastro, status e responsáveis dos GEMs, mas não
entra automaticamente nos dados pedagógicos de uma unidade. Qualquer acesso de
suporte/auditoria a uma unidade deverá ser concedido explicitamente e ficará
registrado.

### Logos, fotos e arquivos separados

Todo arquivo será salvo com o identificador do GEM na sua própria pasta:

- `gems/{gem_id}/logo/` — logo e identidade visual do GEM;
- `gems/{gem_id}/alunas/{aluna_id}/perfil/` — foto de perfil da aluna;
- `gems/{gem_id}/professoras/{professora_id}/perfil/` — foto da professora;
- `gems/{gem_id}/documentos/` — documentos, apostilas e arquivos daquele GEM.

As permissões de armazenamento seguirão a mesma regra do banco: uma aluna,
professora ou Secretaria só poderá abrir arquivos da própria unidade. No painel
da Secretaria, a marca exibida será sempre a logo do GEM; nos painéis pessoais,
as fotos de perfil continuarão aparecendo conforme o acesso atual.

## Ordem da migração

1. Fundação multi-GEM, login mestre e sessão segura.
2. Perfil e documentos das alunas.
3. Agenda, chamada e registros das professoras.
4. Secretaria: cadastros, boletim, relatórios e documentos.
5. Planejamento e rodízio — conferido lado a lado com o Streamlit antes de se
   tornar oficial.

Nenhum dado histórico será migrado ou alterado: a nova interface consulta as
mesmas tabelas e os mesmos documentos já existentes.

### Primeiro passo de login

Antes de testar Professoras e Alunas, execute no SQL Editor do Supabase a
migration `supabase/migrations/001_validar_login_professoras_alunas.sql` desta
pasta. Ela adiciona somente uma função de validação: não altera alunas,
professoras, senhas nem registros existentes.

Em seguida, execute `supabase/migrations/002_fundacao_multi_gem_master.sql`.
Ela cadastra `GEM Vila Verde` como a primeira unidade e deixa a conta Master
`jessicavitorioit@gmail.com` pronta para receber o convite seguro de criação de
senha. Ainda não altera as tabelas pedagógicas nem os arquivos atuais.

### Criar a senha da conta Master

No Supabase, abra **Authentication → Users → Add user → Create new user**.
Informe o e-mail `jessicavitorioit@gmail.com`, escolha a senha e marque
**Auto Confirm User**. Assim não depende do limite de e-mails de convite.

Em seguida, execute `supabase/migrations/006_reparar_vinculo_master.sql` no
SQL Editor. Ela conecta essa conta de autenticação ao cadastro Master já criado
na migration 002. No resultado final, `status_convite` deve aparecer como
`ativo` e `auth_user_id` deve estar preenchido. Só então entre pelo aplicativo
com o e-mail e a senha definidos no Supabase Auth.

## Instalação no celular

Depois da publicação em HTTPS, Android/Chrome mostrará o botão **Instalar
aplicativo**. No iPhone/Safari, use **Compartilhar → Adicionar à Tela de
Início**. A instalação cria um ícone do GEM e abre sem a barra normal do
navegador.
