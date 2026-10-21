# 🚀 Prosolution IA — SaaS de Automação de Conteúdo com IA

A **Prosolution IA** é uma plataforma SaaS em **FastAPI** que gera posts para Instagram com IA a partir do perfil da empresa e da marca, agenda e publica automaticamente via Graph API da Meta, e cobra a assinatura PRO via **PIX (Asaas)**.

![Dashboard Oficial](docs/assets/dashboard_preview.png)

---

## ✨ Funcionalidades

* **Gerador de posts com IA** (OpenAI via LangChain) usando segmento, público, tom de voz, palavras proibidas e CTA da marca. Sem `OPENAI_API_KEY` roda em modo simulado.
* **Editor de posts**: edição da legenda (limites de 2.200 caracteres e 30 hashtags do Instagram), pré-visualização, upload de imagem e agendamento em uma única tela.
* **Imagens no padrão do Instagram**: aceita JPEG/PNG de até 8 MB, converte para JPEG, recorta pelo centro o que passar da faixa de proporção 4:5 a 1.91:1, reduz para 1440 px e remove os metadados (GPS). Armazenamento local ou S3/Cloudflare R2.
* **Calendário de agendamento** (FullCalendar), com o horário do usuário convertido para UTC.
* **Publicação automática no Instagram** por um **worker separado**, com OAuth da Meta (token de longa duração).
* **Assinatura PRO com data de expiração**: cada pagamento PIX confirmado soma `PRO_PLAN_DAYS` dias; estorno cancela; o plano expira sozinho.

## 🔒 Segurança

* Senhas com **bcrypt**; sessão em **JWT** num cookie `HttpOnly` + `Secure` + `SameSite=Lax`.
* **CSRF** em todos os formulários (double submit cookie).
* **Rate limit** (slowapi) em login, cadastro e recuperação de senha.
* **Recuperação de senha por e-mail** (SMTP): o link expira e deixa de valer depois que a senha muda. A resposta é a mesma exista ou não o e-mail.
* **Uploads seguros**: a imagem é decodificada de verdade (extensão e Content-Type são ignorados), há proteção contra "bombas de descompressão", limite de tamanho (413) já na entrada da requisição e os nomes dos arquivos são aleatórios.
* **Webhook do Asaas autenticado** pelo header `asaas-access-token`; sem token configurado, todos os webhooks são recusados. Só pagamentos gerados pela própria aplicação liberam o plano.
* **Tokens do Instagram criptografados** no banco (Fernet).
* OAuth do Instagram com parâmetro `state`.
* `SECRET_KEY` e `ENCRYPTION_KEY` obrigatórias, sem valores padrão; nenhuma chave no código.
* Erros monitorados no **Sentry** sem enviar dados pessoais.

---

## 🛠️ Stack

* **Python 3.11+**, **FastAPI**, **Uvicorn**
* **SQLAlchemy 2 (async)** + **Alembic** — SQLite em desenvolvimento, **PostgreSQL** em produção
* **APScheduler** (worker), **httpx**, **LangChain + OpenAI**
* **Jinja2** + HTML/CSS
* **pytest**, **ruff**, **mypy**, **GitHub Actions**

## 📂 Estrutura

```text
app/
├── ai/engine.py        # Prompt e geração de posts com IA
├── auth/routes.py      # Cadastro, login, logout, recuperação de senha
├── core/               # Configuração, CSRF, rate limit, e-mail, criptografia, fuso horário, Sentry
├── dashboard/routes.py # Telas do painel (conteúdo, calendário, Instagram, assinatura, configurações)
├── dashboard/posts.py  # Editor de posts: legenda, imagem, agendamento, exclusão
├── database/           # Modelos, sessão assíncrona e repositórios
├── instagram/service.py# OAuth e publicação na Graph API
├── legal/routes.py     # Termos, Política de Privacidade e Exclusão de Dados
├── payments/           # Asaas (cobrança), webhook e regras da assinatura
├── security.py         # Hash de senha, JWT e dependência get_current_user
├── worker.py           # Processo que publica os posts agendados
└── main.py             # Aplicação FastAPI
alembic/                # Migrações do banco
templates/ static/      # Frontend
tests/                  # Testes (pytest + httpx.AsyncClient)
deploy/Caddyfile        # Proxy HTTPS
scripts/                # backup.sh e restore.sh do Postgres
```

---

## 🚀 Rodando localmente

```bash
git clone https://github.com/Eduardo09e32y4rhf/Api-prosolution.git
cd Api-prosolution

python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements-dev.txt
cp .env.example .env            # preencha SECRET_KEY e ENCRYPTION_KEY (comandos no próprio arquivo)

alembic upgrade head
uvicorn app.main:app --port 3000 --reload

# Em outro terminal, para publicar os posts agendados:
python -m app.worker
```

Acesse **http://localhost:3000**.

> Em desenvolvimento, sem `SMTP_HOST`, o e-mail de recuperação de senha aparece no log do servidor.

## 🐳 Rodando com Docker (homologação / produção)

```bash
cp .env.example .env   # preencha DOMAIN, SECRET_KEY, ENCRYPTION_KEY, POSTGRES_PASSWORD e as integrações
docker compose up -d --build
```

| Serviço  | Função |
|----------|--------|
| `caddy`  | HTTPS automático (Let's Encrypt) e cabeçalhos de segurança na frente da aplicação |
| `web`    | Aplica as migrações e serve a aplicação (porta interna 3000) |
| `worker` | Publica os posts agendados (várias instâncias são seguras graças ao `FOR UPDATE SKIP LOCKED`) |
| `db`     | PostgreSQL 16 com volume persistente |
| `backup` | `pg_dump` diário em `./backups` com retenção |

Passo a passo completo (servidor, DNS, e-mail, Sentry, backups e restauração): **[docs/DEPLOY.md](docs/DEPLOY.md)**.

## 📋 Documentos

* [docs/ROADMAP.md](docs/ROADMAP.md): plano de 8 semanas até o lançamento
* [docs/DEPLOY.md](docs/DEPLOY.md): como colocar a homologação no ar
* [docs/CREDENCIAMENTO.md](docs/CREDENCIAMENTO.md): verificação da empresa na Meta e conta de produção no Asaas
* Páginas legais públicas: `/termos`, `/privacidade`, `/exclusao-de-dados`

## 💳 Configurando o Asaas

1. Defina `ASAAS_API_KEY` (e `ASAAS_BASE_URL` de produção quando sair do sandbox).
2. No painel do Asaas, crie o webhook de cobranças apontando para `https://SEU_DOMINIO/api/asaas/webhook`.
3. Gere um token de autenticação no webhook e coloque o mesmo valor em `ASAAS_WEBHOOK_TOKEN`.

## 🧪 Qualidade

```bash
ruff check . && ruff format --check .
mypy
alembic upgrade head && alembic check
pytest
# contra Postgres, incluindo concorrência do worker e backup real:
TEST_DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost/prosolution_test pytest
```

O GitHub Actions roda tudo isso em cada push na `main` e em cada pull request.

---

## 👨‍💻 Autor & Manutenção

**José Eduardo da Silva**
🎓 Análise e Desenvolvimento de Sistemas
💻 Backend Developer & AI Architect
🔗 [GitHub: @Eduardo09e32y4rhf](https://github.com/Eduardo09e32y4rhf)
