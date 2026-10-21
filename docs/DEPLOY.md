# Deploy do ambiente de homologação

Guia para colocar a Prosolution no ar em `https://homolog.seudominio.com.br` com Docker Compose.
A pilha sobe cinco serviços:

| Serviço  | Função |
|----------|--------|
| `caddy`  | Proxy reverso com **HTTPS automático** (Let's Encrypt) e cabeçalhos de segurança |
| `web`    | Aplicação FastAPI; aplica as migrações ao iniciar |
| `worker` | Publica os posts agendados |
| `db`     | PostgreSQL 16 |
| `backup` | `pg_dump` diário em `./backups`, com retenção configurável |

---

## 1. Servidor

- VPS com **Ubuntu 24.04**, **2 GB de RAM** e 1 vCPU já bastam para homologação (qualquer provedor: Hetzner, DigitalOcean, Contabo, Hostinger, AWS Lightsail...).
- Acesso SSH por chave (desative login por senha).

```bash
# No servidor, como root
apt update && apt upgrade -y
ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw allow 443/udp && ufw enable

# Docker oficial
curl -fsSL https://get.docker.com | sh

# Usuário de deploy
adduser --disabled-password --gecos "" deploy
usermod -aG docker deploy
```

## 2. Domínio

No painel de DNS do seu domínio, crie um registro **A**:

| Tipo | Nome      | Valor            |
|------|-----------|------------------|
| A    | `homolog` | IP público da VPS |

Confira com `dig +short homolog.seudominio.com.br` antes de seguir: o Caddy só consegue emitir o certificado depois que o DNS propagar.

## 3. Código e configuração

```bash
su - deploy
git clone https://github.com/Eduardo09e32y4rhf/Api-prosolution.git
cd Api-prosolution
cp .env.example .env
nano .env
```

Preencha no mínimo:

| Variável | Valor |
|----------|-------|
| `ENVIRONMENT` | `staging` |
| `DOMAIN` | `homolog.seudominio.com.br` |
| `SECRET_KEY` | `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ENCRYPTION_KEY` | `docker run --rm python:3.11-slim sh -c "pip -q install cryptography && python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"` |
| `POSTGRES_PASSWORD` | Senha forte **só com letras e números** (vai dentro de uma URL) |
| `COMPANY_*`, `CONTACT_EMAIL`, `PRIVACY_EMAIL` | Dados reais da empresa: aparecem nos Termos e na Política de Privacidade |
| `SMTP_*` | Veja a seção 6 |
| `SENTRY_DSN` | Veja a seção 7 |
| `ASAAS_*` | Em homologação use o **sandbox** (`https://sandbox.asaas.com/api/v3`) |
| `INSTAGRAM_REDIRECT_URI` | `https://homolog.seudominio.com.br/dashboard/instagram/callback` |

> Guarde `SECRET_KEY` e `ENCRYPTION_KEY` num gerenciador de senhas. Perder a `ENCRYPTION_KEY` obriga todos os usuários a reconectar o Instagram.

## 4. Subir

```bash
docker compose up -d --build
docker compose ps          # todos "running"/"healthy"
docker compose logs -f web # migrações + Uvicorn iniciado
```

Teste:

```bash
curl https://homolog.seudominio.com.br/health
# {"status":"ok","database":"ok"}
```

Abra no navegador e faça o roteiro da seção 9.

## 5. Atualizar para uma nova versão

```bash
cd ~/Api-prosolution
git pull
docker compose up -d --build   # o web roda as migrações novas ao subir
```

Para voltar uma versão: `git checkout <commit anterior> && docker compose up -d --build`. Se a versão nova tinha migração, restaure o backup feito antes da atualização (seção 8).

## 6. E-mail transacional (Brevo ou Resend)

1. Crie a conta no [Brevo](https://www.brevo.com) ou no [Resend](https://resend.com).
2. **Autentique o domínio** no painel do provedor: ele mostra os registros **SPF**, **DKIM** e **DMARC** para criar no DNS. Sem isso, os e-mails caem no spam.
3. Pegue as credenciais SMTP e coloque no `.env`:

| Provedor | `SMTP_HOST` | `SMTP_PORT` | `SMTP_USER` | `SMTP_PASSWORD` |
|----------|-------------|-------------|-------------|-----------------|
| Brevo    | `smtp-relay.brevo.com` | `587` | login SMTP do painel | chave SMTP |
| Resend   | `smtp.resend.com` | `587` | `resend` | API key |

4. `SMTP_FROM` precisa usar o domínio autenticado, por exemplo `Prosolution <no-reply@seudominio.com.br>`.
5. Teste:

```bash
docker compose exec web python -m app.core.email seu-email@exemplo.com
```

## 7. Monitoramento de erros (Sentry)

1. Crie uma conta em [sentry.io](https://sentry.io) e um projeto **Python → FastAPI**.
2. Copie o **DSN** (Settings → Projects → Client Keys) para `SENTRY_DSN` no `.env`.
3. `docker compose up -d` para recarregar. Web e worker aparecem separados pela tag `component`.
4. O SDK está configurado para **não enviar** e-mails, IPs, cookies nem corpo das requisições (LGPD).
5. Configure um alerta por e-mail para "new issue".

Recomendado também: um monitor de uptime gratuito (UptimeRobot, Better Stack) apontando para `https://homolog.seudominio.com.br/health`.

## 8. Backups

- O serviço `backup` gera `./backups/prosolution-AAAAMMDD-HHMMSS.dump` todo dia às `BACKUP_TIME` (UTC) e apaga os mais antigos que `BACKUP_RETENTION_DAYS`.
- Backup manual antes de uma atualização:

```bash
docker compose run --rm backup --once
```

- **Cópia fora do servidor (obrigatório):** um backup que mora só na VPS some junto com ela. Use o `rclone` para enviar a pasta para um armazenamento de objetos (Cloudflare R2, Backblaze B2, S3):

```bash
# crontab -e do usuário deploy (07:00 UTC, depois do backup)
0 7 * * * rclone copy ~/Api-prosolution/backups remoto:prosolution-backups --max-age 48h
```

- **Restaurar** (substitui o banco atual):

```bash
./scripts/restore.sh backups/prosolution-AAAAMMDD-HHMMSS.dump
```

Teste uma restauração pelo menos uma vez: backup que nunca foi restaurado não é backup.

## 9. Roteiro de verificação

- [ ] `https://homolog...` abre com cadeado; `http://` redireciona para `https://`
- [ ] `/health` responde `{"status":"ok","database":"ok"}`
- [ ] `/termos`, `/privacidade` e `/exclusao-de-dados` abrem com os dados reais da empresa
- [ ] Cadastro, login e logout funcionam
- [ ] "Esqueci minha senha" envia o e-mail e o link redefine a senha
- [ ] Gerar post (com ou sem `OPENAI_API_KEY`) cria um rascunho
- [ ] `docker compose logs backup` mostra o primeiro backup gerado
- [ ] Um erro forçado aparece no Sentry
- [ ] Monitor de uptime configurado
