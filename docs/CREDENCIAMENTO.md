# Credenciamento: Meta (Instagram) e Asaas

Estes processos dependem de documentos da empresa e de análise humana de terceiros, por isso precisam começar
na **semana 1**: são eles que definem a data de lançamento, não o código.

**Pré-requisitos para os dois:**

- [ ] CNPJ ativo e o **Cartão CNPJ** em PDF
- [ ] Domínio próprio com e-mail no domínio (ex.: `contato@seudominio.com.br`)
- [ ] Homologação no ar com HTTPS (veja [DEPLOY.md](DEPLOY.md))
- [ ] Páginas públicas no ar com os dados reais da empresa (variáveis `COMPANY_*` no `.env`):
  - `https://SEU_DOMINIO/termos`
  - `https://SEU_DOMINIO/privacidade`
  - `https://SEU_DOMINIO/exclusao-de-dados`

> Os textos dessas páginas são um modelo inicial. Peça para um advogado revisar antes do lançamento público.

---

## Meta: app de produção e verificação da empresa

### 1. Portfólio empresarial
1. Acesse [business.facebook.com](https://business.facebook.com) e crie um **portfólio empresarial** com a razão social exatamente como está no Cartão CNPJ.
2. Em **Configurações → Informações da empresa**, preencha endereço, telefone e site.

### 2. Verificar o domínio
1. **Configurações → Segurança da marca → Domínios → Adicionar**.
2. Escolha a verificação por **registro TXT no DNS** e crie o registro no painel do seu domínio.
3. Clique em **Verificar** (o DNS pode levar algumas horas para propagar).

### 3. Verificação da empresa (Business Verification)
1. **Configurações → Central de segurança → Verificação da empresa → Iniciar verificação**.
2. Envie o Cartão CNPJ e um comprovante de endereço ou telefone em nome da empresa (conta de luz, telefone ou extrato).
3. Escolha como receber o código de confirmação (e-mail no domínio, telefone ou verificação de domínio).
4. A análise costuma levar de alguns dias a algumas semanas. Sem ela, o app não consegue **acesso avançado** às permissões do Instagram.

### 4. Criar o app
1. Em [developers.facebook.com/apps](https://developers.facebook.com/apps), **Criar app**, tipo **Empresa**, vinculado ao portfólio do passo 1.
2. Adicione o produto **Login do Facebook para Empresas** e o caso de uso de **API do Instagram** (publicação de conteúdo).
3. **Configurações do app → Básico**, preencha:
   - Domínios do app: `seudominio.com.br`
   - URL da Política de Privacidade: `https://SEU_DOMINIO/privacidade`
   - URL dos Termos de Serviço: `https://SEU_DOMINIO/termos`
   - URL das instruções de exclusão de dados: `https://SEU_DOMINIO/exclusao-de-dados`
   - Ícone 1024×1024, categoria (**Negócios e páginas**) e e-mail de contato
4. **Login do Facebook → Configurações → URIs de redirecionamento do OAuth válidos**:
   `https://SEU_DOMINIO/dashboard/instagram/callback`
5. Copie **ID do app** e **Chave secreta** para `INSTAGRAM_APP_ID` e `INSTAGRAM_APP_SECRET` no `.env`, e
   `INSTAGRAM_REDIRECT_URI` com a URL do passo 4.

### 5. Testar antes da aprovação
Enquanto o app não passa pela revisão, só funciona com pessoas que têm função nele:
**Funções do app → Testadores → Adicionar**. Cada testador aceita o convite em
[developers.facebook.com/requests](https://developers.facebook.com/requests) e precisa ter uma conta Instagram
**profissional** vinculada a uma Página do Facebook.

### 6. Revisão do app (semana 4)
Permissões a solicitar: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
A Meta pede um vídeo de tela mostrando o fluxo completo (login → conectar Instagram → agendar → post publicado) e
uma justificativa de uso para cada permissão. Isso fica para a semana 4, mas já deixe o app criado e a empresa verificada.

---

## Asaas: conta de produção

> Homologação usa o **sandbox** ([sandbox.asaas.com](https://sandbox.asaas.com)), uma conta separada e gratuita, sem documentos.
> A conta de produção só é usada no lançamento, mas a aprovação leva dias, então peça agora.

### 1. Abrir a conta
1. Cadastre-se em [asaas.com](https://www.asaas.com) como **Pessoa Jurídica** com o CNPJ.
2. Envie a documentação pedida no painel, normalmente:
   - Contrato social ou Certificado MEI/CCMEI
   - Documento com foto do sócio administrador (RG ou CNH)
   - Selfie do sócio segurando o documento
   - Comprovante de endereço da empresa
3. Aguarde a aprovação, que é avisada por e-mail.

### 2. Integração (repita no sandbox agora e na produção no lançamento)
1. **Integrações → Chave de API → Gerar**. Copie para `ASAAS_API_KEY` (a chave é mostrada uma vez só).
2. `ASAAS_BASE_URL`:
   - sandbox: `https://sandbox.asaas.com/api/v3`
   - produção: `https://api.asaas.com/v3`
3. **Integrações → Webhooks → Adicionar**:
   - URL: `https://SEU_DOMINIO/api/asaas/webhook`
   - Versão da API: v3, envio **sequencial**
   - **Token de autenticação**: gere um valor aleatório (`python3 -c "import secrets; print(secrets.token_urlsafe(32))"`) e coloque o mesmo valor em `ASAAS_WEBHOOK_TOKEN`
   - Eventos: **Cobranças** (`PAYMENT_CONFIRMED`, `PAYMENT_RECEIVED`, `PAYMENT_OVERDUE`, `PAYMENT_REFUNDED`, `PAYMENT_DELETED`)
4. No sandbox, gere uma cobrança pela tela de assinatura e use **Confirmar pagamento** no painel do Asaas:
   o plano PRO deve aparecer ativo com data de expiração.

---

## Checklist da semana 1

- [ ] Portfólio empresarial criado na Meta
- [ ] Domínio verificado na Meta
- [ ] Verificação da empresa **enviada**
- [ ] App da Meta criado, com as URLs legais e de redirecionamento preenchidas
- [ ] Conta Asaas de produção **solicitada**, com documentos enviados
- [ ] Conta sandbox do Asaas configurada na homologação, com webhook testado
