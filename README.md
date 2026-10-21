# 🚀 Prosolution IA — SaaS de Automação de Conteúdo com IA

A **Prosolution IA** é uma plataforma SaaS em **FastAPI** que gera posts para Instagram com IA a partir do perfil da empresa e da marca, agenda e publica automaticamente via Graph API da Meta, e cobra a assinatura PRO via **PIX (Asaas)**.

![Dashboard Oficial](docs/assets/dashboard_preview.png)

---

## ✨ Funcionalidades

* **Gerador de posts com IA** (OpenAI via LangChain) usando segmento, público, tom de voz, palavras proibidas e CTA da marca. Sem `OPENAI_API_KEY` roda em modo simulado.
* **Calendário de agendamento** (FullCalendar), com o horário do usuário convertido para UTC.
* **Publicação automática no Instagram** por um **worker separado**, com OAuth da Meta (token de longa duração).
* **Assinatura PRO com data de expiração**: cada pagamento PIX confirmado soma `PRO_PLAN_DAYS` dias; estorno cancela; o plano expira sozinho.

## 🔒 Segurança

* Senhas com **bcrypt**; sessão em **JWT** num cookie `HttpOnly` + `Secure` + `SameSite=Lax`.
* **CSRF** em todos os formulários (double submit cookie).
* **Rate limit** (slowapi) em login, cadastro e recuperação de senha.
* **Recuperação de senha por e-mail** (SMTP): o link expira e deixa de valer depois que a senha muda. A resposta é a mesma exista ou não o e-mail.
* **Webhook do Asaas autenticado** pelo header `asaas-access-token`; sem token configurado, todos os webhooks são recusados. Só pagamentos gerados pela própria aplicação liberam o plano.
* **Tokens do Instagram criptografados** no banco (Fernet).
* OAuth do Instagram com parâmetro `state`.
* `SECRET_KEY` e `ENCRYPTION_KEY` obrigatórias, sem valores padrão; nenhuma chave no código.

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
├── core/               # Configuração, CSRF, rate limit, e-mail, criptografia, fuso horário
├── dashboard/routes.py # Telas do painel (conteúdo, calendário, Instagram, assinatura, configurações)
├── database/           # Modelos, sessão assíncrona e repositórios
├── instagram/service.py# OAuth e publicação na Graph API
├── payments/           # Asaas (cobrança), webhook e regras da assinatura
├── security.py         # Hash de senha, JWT e dependência get_current_user
├── worker.py           # Processo que publica os posts agendados
└── main.py             # Aplicação FastAPI
alembic/                # Migrações do banco
templates/ static/      # Frontend
tests/                  # Testes (pytest + httpx.AsyncClient)
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

## 🐳 Rodando com Docker (produção)

```bash
cp .env.example .env   # preencha SECRET_KEY, ENCRYPTION_KEY, POSTGRES_PASSWORD e as chaves das integrações
docker compose up -d --build
```

Sobe três serviços:

| Serviço  | Função                                                        |
|----------|---------------------------------------------------------------|
| `db`     | PostgreSQL 16 com volume persistente                          |
| `web`    | Aplica as migrações e serve a aplicação na porta 3000         |
| `worker` | Publica os posts agendados (uma instância por vez é suficiente; várias são seguras graças ao `FOR UPDATE SKIP LOCKED`) |

> Use uma `POSTGRES_PASSWORD` sem caracteres especiais de URL (`@`, `:`, `/`), ou codifique-a.
> Coloque um proxy reverso com HTTPS na frente e defina `FORWARDED_ALLOW_IPS` com o IP dele.
> Com mais de um processo web, aponte `RATE_LIMIT_STORAGE_URI` para um Redis.

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
```

O GitHub Actions roda tudo isso em cada push na `main` e em cada pull request.

---

## 👨‍💻 Autor & Manutenção

**José Eduardo da Silva**
🎓 Análise e Desenvolvimento de Sistemas
💻 Backend Developer & AI Architect
🔗 [GitHub: @Eduardo09e32y4rhf](https://github.com/Eduardo09e32y4rhf)
