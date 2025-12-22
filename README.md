# 🚀 Prosolution API — SaaS de Automação Inteligente

A **Prosolution API** é uma plataforma **SaaS backend-first**, desenvolvida com **FastAPI**, focada em **segurança, automação e escalabilidade**, simulando um produto real pronto para mercado.

Este projeto foi pensado **além do CRUD**, com visão de arquitetura, autenticação moderna, controle de usuários, planos e deploy em produção.

---

## 🧠 Visão do Projeto

O objetivo da Prosolution é servir como **base sólida para um SaaS profissional**, incluindo:

* Autenticação real
* Segurança por IP
* Controle de usuários e administradores
* Estrutura de monetização
* Código limpo e organizado
* Deploy funcional em cloud (Render)

---

## 🔐 Funcionalidades Implementadas

### ✅ Autenticação & Segurança

* Login real com **PostgreSQL**
* Senhas criptografadas com **bcrypt**
* Autenticação via **JWT**
* Sessão baseada em token
* Proteção de rotas autenticadas
* Redirecionamento automático após login

### 🚫 Bloqueio de VPN / Proxy

* Validação de IP do cliente
* Bloqueio de acessos via VPN ou Proxy
* Estrutura pronta para integração com APIs anti-fraude

### 👥 Usuários & Admin

* Usuários comuns
* Usuários administradores
* Controle de permissões
* Plano associado ao usuário (free / pro / enterprise)

### 💳 Monetização (estrutura pronta)

* Base de planos no banco
* Controle de acesso por plano
* Preparado para Stripe / Mercado Pago

---

## 🖥️ Interface

* Tela de login moderna
* Dashboard autenticado
* UI estilo terminal / hacker
* Renderização dinâmica com dados do usuário (JWT)

---

## 🛠️ Stack Tecnológica

* **Python 3.13**
* **FastAPI**
* **PostgreSQL**
* **JWT (python-jose)**
* **Passlib + Bcrypt**
* **Jinja2**
* **Uvicorn**
* **APScheduler**
* **HTML + CSS**
* **Deploy: Render**

---

## 📂 Estrutura do Projeto

```
app/
├── auth/          # Autenticação, JWT e segurança
├── dashboard/     # Rotas protegidas e dashboard
├── database/      # PostgreSQL e repositórios
├── scheduler/     # Automação e jobs
├── utils/         # VPN / Proxy block
├── main.py        # Entry point
static/
templates/
requirements.txt
README.md
```

---

## 🚀 Rodando Localmente

```bash
git clone https://github.com/Eduardo09e32y4rhf/Api-prosolution.git
cd Api-prosolution
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse:

```
http://localhost:8000
```

---

## 🌍 Deploy

Aplicação publicada na **Render**, com deploy automático via GitHub.

---

## 👨‍💻 Sobre o Desenvolvedor

**José Eduardo da Silva**
🎓 Formado em **Análise e Desenvolvimento de Sistemas**
💻 Backend Developer — APIs, Automação e Segurança

Experiência prática com:

* FastAPI
* Arquitetura backend
* Autenticação JWT
* Banco de dados
* Deploy em produção

Este projeto demonstra **capacidade técnica + visão de produto**, indo além de exemplos básicos.

🔗 GitHub: [https://github.com/Eduardo09e32y4rhf](https://github.com/Eduardo09e32y4rhf)

---

## ⭐ Conclusão

A **Prosolution API** é uma base real para um SaaS moderno, pronta para evolução com:

* Pagamentos reais
* Multi-tenant
* Logs e métricas
* Escala horizontal
* Painel administrativo completo

> Código limpo, funcional e com visão de mercado.
