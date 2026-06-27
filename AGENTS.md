# Job Hunter Agent — Projeto de Agente de Busca de Vagas com Nanobot

## Descrição

Este projeto implementa um assistente pessoal de caça a vagas usando [Nanobot](https://github.com/HKUDS/nanobot).
O agente roda via Telegram, busca vagas em múltiplas plataformas, gera currículos em PDF (HTML+Tailwind+Playwright)
e auxilia em tarefas do processo seletivo (cartas, e-mails, mensagens).

## Arquitetura

```
Telegram → Nanobot Gateway → Agent Loop → Tools (job_scraper, resume_generator, cover_letter)
                                        → Web search/fetch
                                        → File I/O (RESUME.md, templates)
```

### Componentes

| Caminho | Função |
|---------|--------|
| `AGENTS.md` | Instruções para IA coders (este arquivo) |
| `config.json` | Config Nanobot: provider DeepSeek, canal Telegram, web tools |
| `Dockerfile` | Imagem Docker com nanobot + Playwright + Chromium |
| `docker-compose.yml` | Orquestração do gateway + CLI |
| `job_hunter_tools/` | Pacote Python com tools customizadas para Nanobot |
| `templates/` | Templates Jinja2 com Tailwind (pt-br e en) |
| `skills/job-hunter/SKILL.md` | Skill Nanobot com identidade e workflow do agente |
| `RESUME.md` | Currículo do usuário em markdown |
| `JOBS_PLATFORMS.md` | Lista de plataformas de emprego |

## Comandos de Desenvolvimento

```bash
# Construir e rodar
docker compose build
docker compose up -d

# CLI (teste rápido)
docker compose run --rm job-hunter-cli agent -m "Olá"

# Logs
docker compose logs -f

# Parar
docker compose down
```

### Variáveis de Ambiente Necessárias

| Variável | Descrição |
|----------|-----------|
| `DEEPSEEK_API_KEY` | Chave da API DeepSeek |
| `TELEGRAM_TOKEN` | Token do bot Telegram (via @BotFather) |
| `TELEGRAM_ALLOW_FROM` | User ID do Telegram permitido (opcional, default `*`) |

## Tools Customizadas

Cada tool é uma classe Python que estende `nanobot.agent.tools.base.Tool`,
registrada via entry-point `nanobot.tools` no `pyproject.toml`.

- **`job_scraper`**: Busca vagas nas plataformas configuradas. Aceita `query`, `location`, `platforms`.
- **`resume_generator`**: Gera PDF do currículo via Playwright. Aceita `resume_data` (JSON) e `template_lang` (pt-br/en).
- **`cover_letter`**: Gera carta de apresentação (texto ou PDF). Aceita `letter_data` (JSON), `template_lang`, `output_format`.

## Convenções

- Templates Jinja2 em `templates/` com sufixo `.{lang}.html`
- Tool `template_lang` parâmetro: `"pt-br"` ou `"en"`
- RESUME.md é a fonte da verdade do perfil
- JOBS_PLATFORMS.md lista as plataformas ativas
