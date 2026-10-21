# Roadmap: lançamento em 8 semanas

**Objetivo:** MVP vendável. Uma empresa real se cadastra, gera posts com IA, sobe uma imagem, agenda,
publica no próprio Instagram e paga o plano PRO.

| Semana | Tema | Pronto quando | Status |
|--------|------|---------------|--------|
| 1 | Fundação: limpeza, CI, homologação (HTTPS, backup, Sentry), e-mail, páginas legais, pedidos à Meta e ao Asaas | Site no ar em HTTPS, CI verde, pedidos enviados | Código pronto; deploy e credenciamentos dependem do responsável (ver [DEPLOY.md](DEPLOY.md) e [CREDENCIAMENTO.md](CREDENCIAMENTO.md)) |
| 2 | Upload de imagem (R2/S3), validação no padrão do Instagram, pré-visualização e edição da legenda | Usuário agenda com foto do computador, sem URL | Código pronto e testado; falta criar o bucket R2 (ver [DEPLOY.md](DEPLOY.md), seção 7.1) |
| 3 | Limites do plano grátis, CPF/CNPJ, assinatura recorrente do Asaas, e-mails de cobrança | Conta grátis bate o limite, assina no sandbox e é liberada | — |
| 4 | Renovação do token da Meta, status do container, novas tentativas, aviso de falha; envio do App Review | Post agendado publica sozinho; revisão submetida | — |
| 5 | Confirmação de e-mail, troca de senha, exclusão de conta (LGPD), callback de exclusão da Meta, landing page honesta | Conta criada, confirmada e excluída de ponta a ponta | — |
| 6 | Testes E2E (Playwright), revisão de segurança, rate limit com Redis, painel admin mínimo | CI cobre os fluxos principais | — |
| 7 | Beta fechado com 5 a 10 empresas | 5 empresas publicando posts reais | — |
| 8 | Lançamento: Asaas e Meta em produção | Cliente desconhecido assina e publica sozinho | — |

## Proposta de planos (a confirmar)

| | Grátis | PRO (R$ 97/mês) |
|---|---|---|
| Posts gerados por IA | 10 por mês | Ilimitado (teto anti-abuso de 300) |
| Agendamento e publicação automática | 3 por mês | Ilimitado (teto anti-abuso de 300) |
| Contas de Instagram | 1 | 1 |

## Fora do escopo do MVP

Reels e vídeos, carrossel, geração de imagem por IA, outras redes, métricas de engajamento, previsão de
tendências, várias contas ou usuários por empresa, app de celular.

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Meta demora ou recusa a revisão | Começar na semana 1; beta com testadores; reenviar com ajustes |
| Asaas demora a aprovar a conta de produção | Documentação enviada na semana 1 |
| Custo da OpenAI acima do previsto | Limite do plano grátis e `gpt-4o-mini` |
| Uma pessoa só desenvolvendo | Semanas 6 e 7 servem de folga |
