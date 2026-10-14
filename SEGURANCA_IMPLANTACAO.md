# Segurança — implantação em etapas

## Estado em 13/10/2026

Esta entrega é uma primeira etapa, NÃO uma certificação de segurança/LGPD.
Não modifica bancos de produção nem migra as contas. As políticas amplas e
as senhas legadas continuam um risco até a migração de autenticação e RLS.
Não cadastrar novos dados sensíveis como se essa etapa tivesse eliminado o risco.

### Proteções de código implementadas

- Cookies com formato/assinatura/perfil/validade inválidos são recusados sem erro de servidor.
- Login/logout/upload recusam origem de navegador incompatível.
- As duas rotas de leitura R2 usam a mesma autorização: aluna lê apenas sua foto
  cadastrada; professora lê sua própria foto e fotos cadastradas de alunas do GEM;
  Secretaria mantém acesso às fotos do seu GEM. Não há permissão global da Master.
- Fotos R2 e sessão têm resposta no-store; URLs diretas expiram em 60 segundos.
- O service worker armazena apenas arquivos públicos da interface. Remove o cache
  antigo de imagens ao ativar. Logout limpa referências locais de fotos.

Limitações: autorizações por dados de cadastro dependem da integridade do banco;
permissões anônimas de escrita ainda precisam ser removidas. Cookies já emitidos
duram até oito horas, não há revogação imediata por conta. URLs antigas assinadas
podem durar até a expiração original. Cache de navegador já existente não pode ser
apagado remotamente de dispositivos desconectados. Leitura de fotos antigas do
Supabase depende das políticas Storage e deve ser incluída na migração.

## Antes da migração do banco

1. Fazer backup recuperável de cada banco e testar a restauração em ambiente separado.
2. Executar `supabase/diagnostico_seguranca.sql` no principal e em cada unidade.
   A consulta é somente leitura e não retorna registros pessoais nem segredos.
3. Informar se `app.py`/Streamlit ainda está em uso. Esse cliente também precisa
   migrar ou deixar de acessar as tabelas; fechar o legado sem isso o interrompe.
4. Com esses resultados, concluir a migração para identidade verificável no banco
   (Supabase Auth), vínculo de conta/unidade/perfil, convites e recuperação de senha.
   Não criar senha padrão compartilhada. Não guardar senhas em texto nas tabelas.
5. Cobrir contas da Secretaria central e GEMs externos; não colocar service_role
   no navegador nem criar proxy genérico que execute consultas arbitrárias.
6. Testar login, cadastro, correção, rodízio, relatórios, fotos e notificações por
   perfil. Testar tentativas diretas de API, acesso cruzado entre GEMs, conta inativa,
   alteração de papel, alteração de fotos e recuperação de senha.
7. Só então substituir TODAS as políticas permissivas, inclusive Storage e RPCs,
   em transação planejada. Criar uma política restritiva não elimina uma permissiva.
8. Remover as senhas legadas após a transição validada. Não reabrir acesso anônimo
   como solução de rollback: corrigir/restaurar a versão segura em ambiente controlado.

## Ações da administradora nos serviços

- Trocar qualquer chave anteriormente exposta e o `SESSION_SECRET` real usado na
  Vercel (não apenas uma variável com nome parecido). Gerar segredo aleatório forte,
  exclusivo, com pelo menos 32 bytes. Não colar segredos no chat, Git ou screenshots.
  A troca do segredo invalida as sessões antigas e exige novo login.
- Revogar as credenciais antigas no provedor; atualizar variáveis e redeploy.
- Ativar MFA nas contas administrativas de GitHub, Vercel, Supabase e Cloudflare.
- Conferir bucket R2 privado, sem domínio/r2.dev público, e token de acesso limitado
  ao bucket necessário. CORS não substitui autenticação.
- Configurar limitação distribuída de tentativas de login no provedor de identidade
  e/ou firewall; contador em memória de função serverless não é proteção suficiente.
- Testar tudo em homologação antes da publicação de produção. Reabrir o PWA online
  para ativar o service worker novo; dispositivos offline não recebem atualizações.

## Privacidade — trabalho organizacional ainda necessário

Definir controlador/responsável por cada GEM, finalidade/base legal de cada uso,
tratamento de menores, aviso de privacidade, canal de direitos, retenção/exclusão,
backups, resposta a incidentes e contratos/transferências com fornecedores.
Revisar quais dados são enviados à IA antes de habilitá-la e restringir relatórios
e busca ativa às pessoas que precisam deles. Validar documentação juridicamente.
Não considerar um botão de aceite como substituto de segurança ou base legal.
